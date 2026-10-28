"""Offline documentation regression tests (especially GitHub mobile README)."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_renders_image_not_raw_mermaid(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("![CI Lifeboat architecture", readme)
        self.assertIn("](docs/architecture.png)", readme)
        self.assertNotIn(chr(96) * 3 + "mermaid", readme)
        png = (ROOT / "docs/architecture.png").read_bytes()
        self.assertTrue(png.startswith(bytes.fromhex("89504e470d0a1a0a")))

    def test_source_and_agent_documentation_exist(self):
        for name in (
            "AGENTS.md",
            "docs/INSTALL.md",
            "docs/ARCHITECTURE.md",
            "docs/architecture.mmd",
            "docs/architecture.dot",
            "docs/architecture.svg",
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
