import os
import tempfile
import unittest
from src.doc_matrix import DocumentItem, ConversionStatus
from src.binary_resolver import PandocBinaryResolver
from src.converter_engine import DocumentConverterEngine

class TestConverterPipeline(unittest.TestCase):

    def setUp(self):
        self.resolver = PandocBinaryResolver()
        self.resolver.resolve()
        self.engine = DocumentConverterEngine(self.resolver)

    def test_document_item_model(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(b"# Test Markdown Document\n\nSample body content.")
            temp_md = f.name

        try:
            item = DocumentItem(file_path=temp_md, target_format="html")
            self.assertEqual(item.input_format, "md")
            self.assertEqual(item.target_format, "html")
            self.assertEqual(item.status, ConversionStatus.QUEUED)
            
            output_path = item.resolve_output_path()
            self.assertTrue(output_path.endswith(".html"))
        finally:
            if os.path.exists(temp_md):
                os.remove(temp_md)

if __name__ == "__main__":
    unittest.main()
