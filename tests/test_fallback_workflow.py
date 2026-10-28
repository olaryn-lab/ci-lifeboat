"""Safety checks for our own desktop fallback workflow."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SelfHostedWorkflowTests(unittest.TestCase):
    def test_public_repo_fallback_scoped_to_main_and_quota_proof(self):
        workflow = (ROOT / ".github/workflows/desktop-fallback.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("desktop-fallback-trevra", workflow)
        self.assertIn("current_sha", workflow)
        self.assertIn('"$current_sha" != "$GITHUB_SHA"', workflow)
        self.assertIn("spending limit needs to be increased", workflow)
        self.assertIn("No verified hosted quota refusal", workflow)
        self.assertLess(workflow.index("No verified hosted quota refusal"), workflow.index("actions/checkout@"))
        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("docker.sock", workflow)


if __name__ == "__main__":
    unittest.main()
