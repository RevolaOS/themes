# SPDX-License-Identifier: GPL-3.0-only
"""Catalog loading, lookup and the fingerprint."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

import fixtures

from rvt import catalog
from rvt import rvtfile as format

ROOT = Path(__file__).resolve().parents[1]
EXTENSION_CATALOG = ROOT.parent / "extensions" / "appearance" / "catalog.json"
sys.path.insert(0, str(ROOT))
from tools import bitmaps_doc  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_fingerprint_is_the_sha256_prefix_of_the_canonical_entries(self):
        entries = fixtures.catalog_document()["bitmaps"]
        canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(
            catalog.fingerprint(entries), hashlib.sha256(canonical).digest()[:8]
        )
        self.assertEqual(len(catalog.fingerprint(entries)), format.FINGERPRINT_BYTES)
        changed = json.loads(json.dumps(entries))
        changed[0]["crc32"] ^= 1
        self.assertNotEqual(catalog.fingerprint(entries), catalog.fingerprint(changed))

    def test_pinned_catalog(self):
        document = json.loads(catalog.DEFAULT.read_text())
        loaded = catalog.Catalog(document)
        self.assertEqual(len(loaded.assets), 599)
        self.assertEqual(loaded.fingerprint.hex(), document["fingerprint"])
        self.assertEqual(document["runtime_file_offset"], 0xB798)
        self.assertEqual(document["runtime_base"], 0x08000000)
        self.assertFalse(any(a["name"].startswith("CFW_") for a in loaded.assets))
        self.assertTrue(all(a["name"] for a in loaded.assets))
        for asset in loaded.assets:
            self.assertEqual(asset["address"], 0x08000000 + asset["offset"] - 0xB798)
        index = loaded.resolve("Background_LightBlue_Image", "x")
        self.assertEqual(loaded.resolve("0x0DAD012D", "x"), index)

    def test_bitmaps_page_is_the_generator_output(self):
        page = ROOT / "docs" / "bitmaps.md"
        self.assertEqual(page.read_text(), bitmaps_doc.current(page))
        appears = bitmaps_doc.appears_from(
            "| `Alpha` | 4x1 | indexed8 | 2 | yes | Settings > About |\n"
        )
        self.assertEqual(appears, {"Alpha": "Settings > About"})
        document = fixtures.catalog_document()["bitmaps"]
        text = bitmaps_doc.page(document, appears)
        self.assertIn("## Other", text)
        self.assertEqual(
            bitmaps_doc.group_of("No_Content_Music_Preview_Image"), "No_Content"
        )
        self.assertEqual(bitmaps_doc.group_of("Notes_Preview_Image"), "Notes")
        self.assertIn("| `Alpha` | 4x1 | indexed8 | 2 | yes | Settings > About |", text)
        self.assertIn("| `Delta` | 4x1 | mask8 | - | yes |  |", text)
        self.assertIn("| `Zeta` | 4x1 | rgb565 | - | no |  |", text)

    def test_extension_vendors_the_same_catalog(self):
        if not EXTENSION_CATALOG.is_file():
            self.skipTest("extensions repository is not checked out alongside")
        self.assertEqual(catalog.DEFAULT.read_bytes(), EXTENSION_CATALOG.read_bytes())

    def test_lookup_and_validation(self):
        loaded = fixtures.catalog()
        self.assertEqual(loaded.resolve("Alpha", "x"), 0)
        self.assertEqual(loaded.resolve("0x20", "x"), 1)
        # The largest payload is a relight's 48 bytes, except Iota (8 palette
        # entries, a 68-byte recolour) and Kappa (12 pixels, 100 bytes).
        self.assertEqual(loaded.max_body(), 856 + 11 * 12 + 9 * 48 + 68 + 100)
        with self.assertRaisesRegex(ValueError, "not a catalog bitmap name"):
            loaded.resolve("Nope", "x")
        with self.assertRaisesRegex(ValueError, "0x00000099 is not a catalog bitmap"):
            loaded.resolve("0x99", "x")
        with self.assertRaisesRegex(ValueError, "ambiguous; use one of 0x00000020"):
            fixtures.catalog(duplicate_name=True).resolve("Beta", "x")
        document = fixtures.catalog_document()
        document["bitmaps"][0]["address"] += 1
        with self.assertRaisesRegex(ValueError, "address"):
            catalog.Catalog(document)
        document = fixtures.catalog_document()
        document["fingerprint"] = "00" * 8
        with self.assertRaisesRegex(ValueError, "stored fingerprint"):
            catalog.Catalog(document)
        document = fixtures.catalog_document()
        document["bitmaps"][1]["id"] = 0x10
        with self.assertRaisesRegex(ValueError, "duplicate bitmap id"):
            catalog.Catalog(document)
        document = fixtures.catalog_document()
        del document["runtime_base"]
        with self.assertRaisesRegex(ValueError, "runtime_base"):
            catalog.Catalog(document)


if __name__ == "__main__":
    unittest.main()
