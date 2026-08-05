import unittest
from src.dublin_core import DublinCoreManager

class TestDublinCoreManager(unittest.TestCase):

    def test_sanitize_metadata(self):
        raw = {"title": "  Sample Title  ", "author": " Jane Doe "}
        clean = DublinCoreManager.sanitize_metadata(raw)
        self.assertEqual(clean["title"], "Sample Title")
        self.assertEqual(clean["author"], "Jane Doe")
        self.assertEqual(clean["language"], "en-US")

    def test_build_pandoc_args(self):
        meta = {
            "title": "Test Transcode Document",
            "author": "Alice Smith",
            "language": "en-US"
        }
        args = DublinCoreManager.build_pandoc_args(meta)
        self.assertIn("--metadata", args)
        self.assertIn("title=Test Transcode Document", args)
        self.assertIn("author=Alice Smith", args)

    def test_yaml_frontmatter_generation(self):
        meta = {"title": "YAML Test", "author": "Bob"}
        yaml_str = DublinCoreManager.build_yaml_frontmatter(meta)
        self.assertTrue(yaml_str.startswith("---"))
        self.assertTrue(yaml_str.endswith("---\n\n"))
        self.assertIn("title: YAML Test", yaml_str)

if __name__ == "__main__":
    unittest.main()
