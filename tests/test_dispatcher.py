"""Offline, no-GitHub-network tests for CI Lifeboat."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from ci_lifeboat import dispatcher as runner


SHA = "a" * 40
REPO = runner.Repo("example/private-repo")


class Tests(unittest.TestCase):
    def fake_api(self, path):
        if path == "repos/example/private-repo":
            return {"private": True}
        if path == "repos/example/private-repo/branches/main":
            return {"commit": {"sha": SHA}}
        if "/actions/runs?head_sha=" in path:
            return {"workflow_runs": [
                {"id": 11, "event": "push", "head_sha": SHA, "head_branch": "main",
                 "conclusion": "failure", "name": "CI"}
            ]}
        if "/actions/runs/11/jobs" in path:
            return {"jobs": [{"id": 22, "conclusion": "failure"}]}
        if "/check-runs/22/annotations" in path:
            return [{"message": "The job was not started because recent account payments have failed"}]
        raise AssertionError(path)

    def test_default_dry_run(self):
        with patch.object(runner, "api", side_effect=self.fake_api), patch.object(runner, "gh") as gh:
            self.assertIn("WOULD_FALLBACK", runner.inspect(REPO, False))
            gh.assert_not_called()

    def test_dispatch_with_exact_sha_quota_proof(self):
        with patch.object(runner, "api", side_effect=self.fake_api), patch.object(runner, "gh") as gh:
            self.assertIn("DISPATCHED", runner.inspect(REPO, True))
            gh.assert_called_once_with("workflow", "run", "ci-lifeboat.yml", "--repo", REPO.name, "--ref", "main")

    def test_non_quota_failure_does_not_dispatch(self):
        def fake(path):
            result = self.fake_api(path)
            if "/annotations" in path:
                return [{"message": "Unit tests failed"}]
            return result
        with patch.object(runner, "api", side_effect=fake), patch.object(runner, "gh") as gh:
            self.assertIn("HOSTED_DEFAULT", runner.inspect(REPO, True))
            gh.assert_not_called()

    def test_duplicate_dispatch_does_not_dispatch(self):
        def fake(path):
            result = self.fake_api(path)
            if "/actions/runs?head_sha=" in path:
                result["workflow_runs"].append({
                    "id": 99, "event": "workflow_dispatch", "head_sha": SHA,
                    "head_branch": "main", "conclusion": None, "name": "CI Lifeboat QA"
                })
            return result
        with patch.object(runner, "api", side_effect=fake), patch.object(runner, "gh") as gh:
            self.assertIn("already dispatched", runner.inspect(REPO, True))
            gh.assert_not_called()

    def test_wrong_sha_fails_closed(self):
        def fake(path):
            result = self.fake_api(path)
            if "/actions/runs?head_sha=" in path:
                result["workflow_runs"][0]["head_sha"] = "b" * 40
            return result
        with patch.object(runner, "api", side_effect=fake), patch.object(runner, "gh") as gh:
            self.assertIn("HOSTED_DEFAULT", runner.inspect(REPO, True))
            gh.assert_not_called()

    def test_public_repo_default_deny(self):
        with patch.object(runner, "api", return_value={"private": False}), patch.object(runner, "gh") as gh:
            self.assertIn("public repository not explicitly permitted", runner.inspect(REPO, True))
            gh.assert_not_called()

    def test_api_failure_never_dispatches(self):
        with patch.object(runner, "api", side_effect=RuntimeError("API unavailable")), patch.object(runner, "gh") as gh:
            with self.assertRaises(RuntimeError):
                runner.inspect(REPO, True)
            gh.assert_not_called()

    def test_quota_lexicon(self):
        accepted = [
            "Recent account payments have failed",
            "Spending limit needs to be increased",
            "Actions minutes quota",
            "Actions minutes limit",
            "Actions minutes exhausted",
            "Hosted runner quota exhausted",
            "Hosted runner minutes exhausted",
        ]
        for message in accepted:
            with self.subTest(message=message):
                self.assertIsNotNone(runner.QUOTA_PATTERN.search(message))
        for message in ["Test failure", "Job cancelled", "Hosted runner unavailable"]:
            self.assertIsNone(runner.QUOTA_PATTERN.search(message))

    def test_workflow_lexicon_matches_watcher(self):
        text = (Path(__file__).parents[1] / "examples/ci-lifeboat.yml").read_text()
        for phrase in [
            "recent account payments have failed",
            "spending limit needs to be increased",
            "actions minutes (quota|limit|exhausted)",
            "hosted runner (quota|minutes) exhausted",
        ]:
            self.assertIn(phrase, text)

    def test_config_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text('[[repositories]]\nname = "example/private-repo"\n')
            self.assertEqual(runner.load_config(path), [REPO])
            path.write_text('[[repositories]]\nname = "not-a-repo"\n')
            with self.assertRaises(ValueError):
                runner.load_config(path)

    def test_unknown_repo_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text('[[repositories]]\nname = "example/private-repo"\n')
            with patch.object(runner, "inspect") as inspect:
                with self.assertRaises(SystemExit):
                    runner.main(["--config", str(path), "--repo", "other/repo", "--dispatch"])
                inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
