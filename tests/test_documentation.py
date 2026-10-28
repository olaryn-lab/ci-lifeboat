"""Offline documentation regression tests for native Mermaid diagrams."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_and_architecture_use_native_mermaid(self):
        source = (ROOT / "docs/architecture.mmd").read_text(encoding="utf-8").strip()
        self.assertTrue(source.startswith("flowchart TD"))
        self.assertEqual(source.count('["'), 7)
        for doc in ("README.md", "docs/ARCHITECTURE.md"):
            with self.subTest(doc=doc):
                content = (ROOT / doc).read_text(encoding="utf-8")
                self.assertIn(f"```mermaid\n{source}\n```", content)
                self.assertNotIn("architecture.png", content)
                self.assertNotIn("architecture.svg", content)
                self.assertNotIn("architecture.dot", content)

    def test_source_and_agent_documentation_exist(self):
        for name in (
            "AGENTS.md",
            "docs/INSTALL.md",
            "docs/ARCHITECTURE.md",
            "docs/architecture.mmd",
            "RELEASE.md",
            "SECURITY.md",
        ):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file())


    def test_readme_local_links_resolve(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", readme)
        for link in links:
            if link.startswith(("https://", "http://", "#")):
                continue
            relative = link.split("#", 1)[0]
            with self.subTest(link=link):
                self.assertTrue((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
