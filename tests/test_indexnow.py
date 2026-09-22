"""Tests for the standalone IndexNow submission helper."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("submit_indexnow", ROOT / "tools" / "submit_indexnow.py")
INDEXNOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXNOW)


class IndexNowHelper(unittest.TestCase):
    def test_sitemap_urls_are_canonical_and_unique(self):
        urls = INDEXNOW.validate_urls(INDEXNOW.sitemap_urls(ROOT / "docs" / "sitemap.xml"))
        self.assertGreater(len(urls), 100)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith(INDEXNOW.SITE_PREFIX) for url in urls))

    def test_rejects_foreign_urls(self):
        with self.assertRaises(ValueError):
            INDEXNOW.validate_urls(["https://example.com/"])

    def test_discovers_matching_key_file(self):
        with tempfile.TemporaryDirectory() as directory:
            docs = Path(directory)
            (docs / "abcdefgh.txt").write_text("abcdefgh", encoding="utf-8")
            self.assertEqual(INDEXNOW.discover_key_file(docs).name, "abcdefgh.txt")


if __name__ == "__main__":
    unittest.main()
