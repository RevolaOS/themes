# SPDX-License-Identifier: GPL-3.0-only
"""The .rvt header and pack layout against rvt/data/rvt.h."""

import struct
import unittest
import zlib
from pathlib import Path

import fixtures  # noqa: F401  (puts the repository on sys.path)

from rvt import rvtfile as format

EXTENSION_HEADER = (
    Path(__file__).resolve().parents[2] / "extensions" / "appearance" / "rvt.h"
)


class HeaderCopyTests(unittest.TestCase):
    def test_copy_equals_the_extension_header(self):
        if not EXTENSION_HEADER.is_file():
            self.skipTest("extensions repository is not checked out alongside")
        self.assertEqual(format.HEADER_FILE.read_bytes(), EXTENSION_HEADER.read_bytes())

    def test_constants_come_from_the_header(self):
        defines = format.DEFINES
        self.assertEqual(format.MAGIC, b"RVT0")
        self.assertEqual(defines["RVT_MAGIC"], int.from_bytes(b"RVT0", "little"))
        self.assertEqual(
            (format.VERSION, format.HEADER_BYTES, format.PACK_HEADER_BYTES),
            (defines["RVT_VERSION"], defines["RVT_HEADER_BYTES"], 16),
        )
        self.assertEqual(format.ENUMS["rvt_role"][-1], "RVT_ROLES")
        self.assertEqual(len(format.ROLES), 8)
        self.assertEqual(format.ROLES[0], "background")
        self.assertEqual(format.ROLES[-1], "icon_tint")
        self.assertEqual(len(format.ACCENTS), 9)
        self.assertEqual(format.ACCENTS[0], "blue")
        self.assertEqual(
            format.ACCENT_SLOTS,
            ("accent_fill", "accent_text", "selection", "on_accent", "icon_tint"),
        )
        self.assertEqual(
            (
                format.STYLE_COLORS,
                format.STYLE_FLAGS,
                format.STYLE_PALETTES,
                format.STYLE_TINTS,
                format.STYLE_BYTES,
            ),
            (0, 32, 36, 216, 856),
        )
        self.assertEqual(format.STYLE_BYTES, 8 * 4 + 4 + 9 * 5 * 4 + format.CATALOG_MAX)
        self.assertEqual(
            format.HEADER_OFFSETS, (0, 4, 6, 8, 16, 20, 24, 28, 32, 36, 40, 72)
        )
        self.assertEqual(format.PACK_OFFSETS, (0, 4, 8, 12))
        self.assertEqual(
            format.FLAGS,
            {
                "flat_selection": 1,
                "menu_covers_off": 2,
                "flat_now_playing": 4,
                "flat_icons": 8,
            },
        )
        self.assertEqual((format.TINT_NONE, format.TINT_ROLE), (0, 1))
        # The extension packs tint bytes two per byte.
        self.assertLessEqual(format.TINT_ROLE + len(format.ROLES), 16)
        self.assertIn(
            "_Static_assert(RVT_TINT_ROLE + RVT_ROLES <= 16",
            format.HEADER_FILE.read_text(),
        )
        self.assertEqual(
            format.KINDS,
            ("pixels", "recolor", "alias", "invert", "relight", "pixels_lz"),
        )
        self.assertEqual((format.LZ_WINDOW, format.LZ_MIN_MATCH), (4096, 3))
        self.assertNotIn("RVT_KIND_FROM_OTHER", defines)
        self.assertEqual(
            (
                format.EXTENSION_BITMAP_BYTES,
                format.EXTENSION_KINDS,
                format.BMAP_HEADER_BYTES,
                format.EXTENSION_BITMAPS_MAX,
                format.EXTENSION_BITMAP_MAX_BYTES,
            ),
            (20, {"bitmap": 1, "bitmap_lz": 2}, 28, 64, 65536),
        )
        self.assertEqual(format.RELIGHT_FIELDS[:2], ("t_zero", "t_full"))
        self.assertEqual(format.SCRATCH_PIXELS, 3840)
        self.assertEqual(format.VERSION, 2)
        self.assertEqual(format.VALUES["RVT_EXTENSION_KINDS"], 3)
        self.assertEqual(format.VALUES["RVT_KIND_PIXELS_LZ"], 5)
        self.assertEqual(format.fnv1a(b""), 2166136261)
        self.assertEqual(format.fnv1a(b"revola"), 0xF802A4B0)


class FileTests(unittest.TestCase):
    fingerprint = bytes(range(8))

    def packs(self):
        return {
            "light": (bytes(format.STYLE_BYTES), 0, 0),
            "dark": (
                bytes(format.STYLE_BYTES) + format.RECORD.pack(1, 28, 3) + b"abc\0",
                1,
                0,
            ),
        }

    def test_header_layout_matches_the_documented_offsets(self):
        data = format.encode_file(self.fingerprint, "my-theme", "Mine", self.packs())
        light = format.PACK_HEADER_BYTES + format.STYLE_BYTES
        dark = light + 16
        self.assertEqual(data[0:4], b"RVT0")
        self.assertEqual(struct.unpack_from("<HH", data, 4), (format.VERSION, 128))
        self.assertEqual(data[8:16], self.fingerprint)
        self.assertEqual(
            struct.unpack_from("<IIIII", data, 16), (3, 128, light, 128 + light, dark)
        )
        sealed = bytearray(data[:128])
        crc = struct.unpack_from("<I", sealed, 36)[0]
        struct.pack_into("<I", sealed, 36, 0)
        self.assertEqual(crc, zlib.crc32(sealed))
        self.assertEqual(data[40:72], b"my-theme".ljust(32, b"\0"))
        self.assertEqual(data[72:120], b"Mine".ljust(48, b"\0"))
        self.assertEqual(data[120:128], bytes(8))
        self.assertEqual(len(data), 128 + light + dark)
        body_bytes, count, crc, assets = struct.unpack_from("<IIII", data, 128 + light)
        self.assertEqual((body_bytes, count, assets), (format.STYLE_BYTES + 16, 1, 0))
        self.assertEqual(crc, zlib.crc32(data[128 + light + 16 :]))
        # The extension bitmap count is the fourth header word and is bounded.
        packs = self.packs()
        packs["light"] = (packs["light"][0], 0, 2)
        data = format.encode_file(self.fingerprint, "x", "X", packs)
        self.assertEqual(struct.unpack_from("<I", data, 128 + 12)[0], 2)
        self.assertEqual(format.decode_file(data)["packs"]["light"], packs["light"])
        packs["light"] = (packs["light"][0], 0, 65)
        with self.assertRaisesRegex(ValueError, "65 extension bitmaps"):
            format.decode_file(format.encode_file(self.fingerprint, "x", "X", packs))

    def test_round_trip(self):
        data = format.encode_file(self.fingerprint, "x", "é" * 23 + "x", self.packs())
        decoded = format.decode_file(data)
        self.assertEqual(decoded["id"], "x")
        self.assertEqual(decoded["name"], "é" * 23 + "x")
        self.assertEqual(decoded["fingerprint"], self.fingerprint)
        self.assertEqual(decoded["packs"], self.packs())
        only_dark = format.encode_file(
            self.fingerprint, "x", "X", {"dark": self.packs()["dark"]}
        )
        self.assertEqual(struct.unpack_from("<IIIII", only_dark, 16)[:3], (2, 0, 0))
        self.assertEqual(list(format.decode_file(only_dark)["packs"]), ["dark"])

    def test_packs_follow_a_larger_header(self):
        data = format.encode_file(self.fingerprint, "x", "X", self.packs())
        header = bytearray(data[:128]) + bytes(8)
        # The bytes after the name are not read.
        header[120] = 1
        struct.pack_into("<H", header, 6, 136)
        struct.pack_into("<I", header, 20, 136)
        light = format.PACK_HEADER_BYTES + format.STYLE_BYTES
        struct.pack_into("<I", header, 28, 136 + light)
        struct.pack_into("<I", header, 36, 0)
        struct.pack_into("<I", header, 36, zlib.crc32(header[:128]))
        larger = bytes(header) + data[128:]
        self.assertEqual(format.decode_file(larger)["packs"], self.packs())
        struct.pack_into("<H", header, 6, 100)
        struct.pack_into("<I", header, 36, 0)
        struct.pack_into("<I", header, 36, zlib.crc32(header[:128]))
        with self.assertRaisesRegex(ValueError, "at least 128 header bytes"):
            format.decode_file(bytes(header) + data[128:])

    def test_rejects_invalid_input(self):
        for identifier in ("", "Test", "-a", "a" * 32, "a b", "é"):
            with self.assertRaisesRegex(ValueError, "^id:"):
                format.encode_file(self.fingerprint, identifier, "X", self.packs())
        with self.assertRaisesRegex(ValueError, "exceeds 47"):
            format.encode_file(self.fingerprint, "x", "n" * 48, self.packs())
        with self.assertRaisesRegex(ValueError, "light or dark"):
            format.encode_file(self.fingerprint, "x", "X", {})
        with self.assertRaisesRegex(ValueError, "multiple of 4"):
            format.encode_pack(bytes(format.STYLE_BYTES + 1), 0)

    def test_rejects_malformed_files(self):
        data = format.encode_file(self.fingerprint, "x", "X", self.packs())

        def resealed(header):
            header = bytearray(header)
            struct.pack_into("<I", header, 36, 0)
            struct.pack_into("<I", header, 36, zlib.crc32(header))
            return bytes(header) + data[128:]

        cases = {
            "bad magic": b"RVT1" + data[4:],
            "newer version": resealed(
                data[:4] + struct.pack("<H", format.VERSION + 1) + data[6:128]
            ),
            "older version": resealed(
                data[:4] + struct.pack("<H", format.VERSION - 1) + data[6:128]
            ),
            "header bytes": resealed(data[:6] + struct.pack("<H", 132) + data[8:128]),
            "CRC": data[:36] + b"\0\0\0\0" + data[40:],
            "appearance bits": resealed(
                data[:16] + struct.pack("<I", 4) + data[20:128]
            ),
            "misplaced": resealed(data[:20] + struct.pack("<I", 132) + data[24:128]),
            "truncated": data[:-4],
            "trailing": data + bytes(4),
            "pack CRC": data[:-1] + bytes([data[-1] ^ 1]),
            "id": resealed(data[:40] + b"Bad\0" + bytes(28) + data[72:128]),
            "name": resealed(data[:72] + b"n" * 48 + data[120:128]),
        }
        for name, bad in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                format.decode_file(bad)


if __name__ == "__main__":
    unittest.main()
