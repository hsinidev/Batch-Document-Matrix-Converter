import unittest
from src.dom_sanitizer import DOMSanitizer

class TestDOMSanitizer(unittest.TestCase):

    def test_strip_inline_styles(self):
        sanitizer = DOMSanitizer({"strip_inline_styles": True, "remove_empty_tags": False})
        raw_html = "<p style='color: red;'>Hello World</p>"
        clean, stats = sanitizer.sanitize_html(raw_html, base_dir=".")
        self.assertNotIn("style=", clean)
        self.assertEqual(stats["styles_stripped"], 1)

    def test_remove_empty_tags(self):
        sanitizer = DOMSanitizer({"remove_empty_tags": True})
        raw_html = "<div><p></p><span>   </span><h1>Header</h1></div>"
        clean, stats = sanitizer.sanitize_html(raw_html, base_dir=".")
        self.assertNotIn("<p></p>", clean)
        self.assertIn("<h1>Header</h1>", clean)
        self.assertGreater(stats["empty_tags_removed"], 0)

    def test_heading_anchors(self):
        sanitizer = DOMSanitizer({"normalize_headings": True})
        raw_html = "<h2>Sample Chapter Title</h2>"
        clean, _ = sanitizer.sanitize_html(raw_html, base_dir=".")
        self.assertIn("id=\"sample-chapter-title\"", clean)

if __name__ == "__main__":
    unittest.main()
