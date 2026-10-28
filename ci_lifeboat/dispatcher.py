"""Fail-closed GitHub Actions hosted-quota fallback dispatcher.

Only trusted, explicitly allowlisted repositories can dispatch a fallback workflow.
The workflow must independently repeat the evidence check before checking out code.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import quote

# Keep this exact message set in sync with examples/ci-lifeboat.yml and tests.
QUOTA_PATTERN = re.compile(
    r"recent account payments have failed|"
    r"spending limit needs to be increased|"
    r"actions minutes (?:quota|limit|exhausted)|"
    r"hosted runner (?:quota|minutes) exhausted",
    re.IGNORECASE,
)
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
NAME_PATTERN = re.compile(r"[A-Za-z0-9_.\-/]+\Z")


@dataclass(frozen=True)
class Repo:
    name: str
    branch: str = "main"
    workflow: str = "ci-lifeboat.yml"
    workflow_name: str = "CI Lifeboat QA"
    allow_public: bool = False


def load_config(path: Path) -> list[Repo]:
    with path.open("rb") as handle:
        payload = tomllib.load(handle)
    entries = payload.get("repositories")
    if not isinstance(entries, list) or not entries:
        raise ValueError("config requires at least one [[repositories]] entry")
    result: list[Repo] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("repository entry must be a table")
        unexpected = set(entry) - {"name", "branch", "workflow", "workflow_name", "allow_public"}
        if unexpected:
            raise ValueError(f"unsupported configuration keys: {sorted(unexpected)}")
        repo = Repo(**entry)
        if not REPO_PATTERN.fullmatch(repo.name):
            raise ValueError("repository name must be owner/repository")
        if not NAME_PATTERN.fullmatch(repo.branch) or ".." in repo.branch or repo.branch.startswith("/"):
            raise ValueError("invalid branch")
        if not NAME_PATTERN.fullmatch(repo.workflow) or "/" in repo.workflow or repo.workflow.startswith("."):
            raise ValueError("workflow must be a filename, not a path")
        if not repo.workflow_name.strip():
            raise ValueError("workflow_name must not be empty")
        if not isinstance(repo.allow_public, bool):
            raise ValueError("allow_public must be a boolean")
        if repo.name in seen:
            raise ValueError(f"duplicate repository {repo.name}")
        result.append(repo)
        seen.add(repo.name)
    return result


def gh(*args: str) -> str:
    response = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=45, check=False
    )
    if response.returncode:
        msg = (response.stderr.strip().splitlines() or ["GitHub request failed"])[-1]
        raise RuntimeError(msg[:250])
    return response.stdout


def api(path: str) -> object:
    return json.loads(gh("api", "-H", "Accept: application/vnd.github+json", path))


def quota_refused(repo: Repo, run_id: int) -> bool:
    data = api(f"repos/{repo.name}/actions/runs/{run_id}/jobs?per_page=100")
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ValueError("invalid jobs response")
    for job in data["jobs"]:
        if job.get("conclusion") != "failure":
            continue
        # Job IDs can be used as check run IDs for GitHub Actions jobs.
        annotations = api(
            f"repos/{repo.name}/check-runs/{job['id']}/annotations?per_page=100"
        )
        if not isinstance(annotations, list):
            raise ValueError("invalid annotations response")
        if any(QUOTA_PATTERN.search(a.get("message") or "") for a in annotations):
            return True
    return False


def inspect(repo: Repo, dispatch: bool) -> str:
    info = api(f"repos/{repo.name}")
    if not isinstance(info, dict) or not isinstance(info.get("private"), bool):
        raise ValueError("cannot determine repository visibility")
    if not info["private"] and not repo.allow_public:
        return f"SKIP {repo.name} public repository not explicitly permitted"

    branch = quote(repo.branch, safe="")
    head = api(f"repos/{repo.name}/branches/{branch}")
    sha = head["commit"]["sha"]
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("invalid branch SHA")
    runs_data = api(f"repos/{repo.name}/actions/runs?head_sha={sha}&per_page=100")
    if not isinstance(runs_data, dict) or not isinstance(runs_data.get("workflow_runs"), list):
        raise ValueError("invalid workflow runs response")
    runs = [
        run for run in runs_data["workflow_runs"]
        if run.get("head_sha") == sha and run.get("head_branch") == repo.branch
    ]
    previous = [
        run for run in runs if run.get("name") == repo.workflow_name
        and run.get("event") == "workflow_dispatch"
    ]
    if previous:
        return f"SKIP {repo.name} {sha[:9]} already dispatched"
    failed = [
        run for run in runs if run.get("conclusion") == "failure"
        and run.get("event") in ("push", "workflow_dispatch")
        and run.get("name") != repo.workflow_name
    ]
    if not any(quota_refused(repo, run["id"]) for run in failed):
        return f"HOSTED_DEFAULT {repo.name} {sha[:9]} no verified quota refusal"
    if not dispatch:
        return f"WOULD_FALLBACK {repo.name} {sha[:9]} verified quota refusal"
    gh("workflow", "run", repo.workflow, "--repo", repo.name, "--ref", repo.branch)
    return f"DISPATCHED {repo.name} {sha[:9]} {repo.workflow}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/ci-lifeboat/config.toml")
    parser.add_argument("--dispatch", action="store_true", help="Dispatch; default is dry-run")
    parser.add_argument("--repo", action="append", help="Only inspect this configured repository")
    args = parser.parse_args(argv)
    try:
        repos = load_config(args.config)
        if args.repo:
            unknown = set(args.repo) - {repo.name for repo in repos}
            if unknown:
                parser.error(f"repositories absent from allowlist: {sorted(unknown)}")
            repos = [repo for repo in repos if repo.name in args.repo]
    except (OSError, ValueError, TypeError) as exc:
        print(f"CONFIG_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = False
    for repo in repos:
        try:
            print(inspect(repo, args.dispatch), flush=True)
        except (RuntimeError, KeyError, ValueError, IndexError, TypeError, subprocess.TimeoutExpired) as exc:
            print(f"ERROR {repo.name}: {str(exc)[:250]}", file=sys.stderr, flush=True)
            errors = True
    return int(errors)


if __name__ == "__main__":
    raise SystemExit(main())
