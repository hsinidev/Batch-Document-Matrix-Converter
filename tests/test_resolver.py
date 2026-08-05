import os
import unittest
from src.binary_resolver import PandocBinaryResolver

class TestBinaryResolver(unittest.TestCase):
    
    def test_resolver_initialization(self):
        resolver = PandocBinaryResolver()
        info = resolver.get_info()
        self.assertIn("path", info)
        self.assertIn("tier", info)
        self.assertIn("version", info)

    def test_manual_override_tier(self):
        resolver = PandocBinaryResolver(manual_path="non_existent_pandoc.exe")
        info = resolver.get_info()
        # Non-existent manual path should fall back to standard tiers
        self.assertNotEqual(info["tier"], 5)

if __name__ == "__main__":
    unittest.main()
