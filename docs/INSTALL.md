# Installation guide

[← README](../README.md) · [For coding agents](../AGENTS.md)

**Before starting:** CI Lifeboat **does not install or register GitHub's runner**. You configure a standard official GitHub Actions self-hosted runner separately. The fallback workflow runs project code, so its isolation and allowed workload are security decisions.

## Prerequisites

- Python 3.11+ and `pipx` (or another isolated Python package installer).
- GitHub CLI `gh` authenticated with **minimal** repository/actions/checks read permissions and permission to dispatch the intended workflow. Prefer a dedicated limited-privilege credential over your personal broad-scope token.
- A private, owned repository with a **protected** `main` branch and existing GitHub-hosted CI.
- An isolated, preferably ephemeral, self-hosted runner that has been registered with GitHub and can reach GitHub over outbound HTTPS. Its workflow environment needs Linux, `curl`, `jq`, `make`, and the repo's QA tools.
- GitHub runner groups restricting **repository + exact workflow + trusted branch** (or equally strong repo-specific controls).

The included workflow defaults to branch `main` and self-hosted runner label `ci-lifeboat`. Treat other branch names as a deliberate customization: change both the controller config **and** the independent workflow guard.

## 1. Review first (no changes to the runner)

Clone and inspect the docs and both workflow files. Identify the private repository, its real CI commands and the smallest source-level QA target that can safely run without deployment credentials.

Run offline tests:

```sh
python3 -m unittest discover -s tests -v
```

## 2. Install the controller

```sh
pipx install .
mkdir -p ~/.config/ci-lifeboat
cp examples/config.toml ~/.config/ci-lifeboat/config.toml
chmod 600 ~/.config/ci-lifeboat/config.toml
```

Edit the config with only your approved repository names. The example is intentionally non-functional until you replace the placeholder.

## 3. Register and restrict the official GitHub runner

Follow GitHub's current [self-hosted runner instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).

- Register the runner for the appropriate repository/organization. Keep registration tokens out of shells logs and source control.
- Use a dedicated runner group or repo-scoped runner. Limit it to the exact repository and fallback workflow. Allow only trusted protected branch execution.
- Provide an isolated runtime; **no host Docker socket, personal files, production tokens, or broadly privileged cloud credentials**.
- Use a unique runner label, and set the matching `runs-on` in the workflow template.
- Do **not** grant public fork PR workflows access. The public CI Lifeboat repository itself should continue to use GitHub-hosted runners.

The controller does **not** configure or audit these GitHub settings.

## 4. Install a limited fallback QA recipe

Copy [examples/ci-lifeboat.yml](../examples/ci-lifeboat.yml) to the approved repository's `.github/workflows/ci-lifeboat.yml` on protected `main`.

Create a `ci-fallback` Makefile target in that repository, with an explicitly reviewed subset of **secret-free**, source-level checks. The example workflow intentionally fails if the target is missing. Do not replace it with an unconditional success or deployment command. Keep existing hosted CI and protected release requirements unchanged.

Check that the fallback workflow re-verifies quota evidence **before code checkout** and has only `contents: read`, `actions: read`, `checks: read` permissions.

## 5. Verify safely (no dispatch)

```sh
gh auth status
ci-lifeboat
ci-lifeboat --repo your-org/your-private-repo
```

Expected results include `HOSTED_DEFAULT`, `SKIP`, or `WOULD_FALLBACK` (if the current SHA has genuine matching evidence). None dispatch anything without `--dispatch`.

**Only after verifying runner-group security and obtaining approval** may you run `ci-lifeboat --dispatch`. That command is not an installation test: if real qualifying evidence exists, it will schedule a job. Do not fabricate quota failures in a production repo.

## 6. Optional timer

Install `systemd/ci-lifeboat.service` and `systemd/ci-lifeboat.timer` under `~/.config/systemd/user/`. Review the `ExecStart` binary path and the credentials available to the systemd user. Then, **after explicit approval**:

```sh
systemctl --user daemon-reload
systemctl --user enable --now ci-lifeboat.timer
systemctl --user status ci-lifeboat.timer
journalctl --user -u ci-lifeboat.service -n 50 --no-pager
```

To pause automatic dispatch, run `systemctl --user disable --now ci-lifeboat.timer`. Already queued or running GitHub jobs are not cancelled by stopping the timer.

## Configuration

Set `~/.config/ci-lifeboat/config.toml` based on [examples/config.toml](../examples/config.toml).

| Key | Default | Description |
| --- | --- | --- |
| `name` | Required | Exact repository `owner/name` allowlist |
| `branch` | `main` | Trusted protected branch |
| `workflow` | `ci-lifeboat.yml` | Allowed dispatch workflow filename |
| `workflow_name` | `CI Lifeboat QA` | Used for deduplication |
| `allow_public` | `false` | High-risk public opt-in; **not recommended** for personal machines |

Configuration is intentionally stored outside the source repository. Do not commit private repository names, tokens or host-specific config to the public repo.

## Limitations and sign-off

- This is **polling**, not automatic GitHub Actions job rerouting.
- Only explicit quota/billing-refusal check annotations for the exact current commit qualify.
- The controller is currently limited to GitHub's first 100 returned matching workflow runs and first 100 jobs/annotations per queried result. It is **not** exhaustive across pagination.
- The runner workflow provides **limited QA**, not complete hosted CI equivalence.
- Record who approved the runner group, verified the isolation, reviewed the QA target and observed a real hosted quota failure or a controlled equivalent on an isolated test repo.
- If GitHub-hosted CI is unavailable because of billing, keep public-source CI on hosted runners and report that it is **blocked**, not passing.

For operations and architecture details, see [Architecture](ARCHITECTURE.md), [Security](../SECURITY.md) and [Release checklist](../RELEASE.md).
