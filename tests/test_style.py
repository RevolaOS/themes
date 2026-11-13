# SPDX-License-Identifier: GPL-3.0-only
"""Style prefix layout and the Classic defaults."""

import re
import struct
import unittest
from pathlib import Path

import fixtures  # noqa: F401

from rvt import rvtfile as format
from rvt import style

STYLE_C = Path(__file__).resolve().parents[2] / "extensions" / "appearance" / "style.c"


def classic(appearance):
    """Colours, flags and palettes of the Classic appearance."""
    colors = style.COLOR_DEFAULTS[appearance]
    palettes = {
        name: style.accent_palette(name, appearance, colors) for name in style.ACCENTS
    }
    return colors, 0, palettes


class StyleTests(unittest.TestCase):
    def test_prefix_follows_the_header_offsets(self):
        self.assertEqual(style.FLAGS_OFFSET, 32)
        self.assertEqual(style.PALETTE_OFFSET, 36)
        self.assertEqual(style.TINT_OFFSET, 216)
        self.assertEqual(style.STYLE_BYTES, 856)
        colors, flags, palettes = classic("light")
        data = style.encode(
            dict(colors, icon_tint="#ff4477"),
            7,
            palettes,
            {0: "icon_tint", 3: "background", 9: "cover_border"},
        )
        self.assertEqual(len(data), format.STYLE_BYTES)
        self.assertEqual(
            data[:32].hex(),
            "ffffffff202020ff236cc5ff3185d0ffffffffff236cc5ff7e8183ffff4477ff",
        )
        self.assertEqual(struct.unpack_from("<I", data, 32)[0], 7)
        # Blue is the first accent; its light palette is Classic's.
        self.assertEqual(data[36:56].hex(), "236cc5ff3185d0ff236cc5ffffffffff3185d0ff")
        tints = data[216:]
        self.assertEqual((tints[0], tints[3], tints[9]), (8, 1, 7))
        self.assertEqual(sum(tints), 16)

    def test_classic_dark_and_accent_defaults(self):
        colors, flags, palettes = classic("dark")
        data = style.encode(colors, flags, palettes, {})
        self.assertEqual(
            data[:32].hex(),
            "181818ffe8e8e8ff00a1ffff00a1ffffffffffff00a1ffff383838ff00a1ffff",
        )
        self.assertEqual(style.accent_builtin("teal", "dark"), ("#00787d", "#40d2d7"))
        self.assertEqual(
            palettes["teal"],
            {
                "accent_fill": "#00787d",
                "accent_text": "#40d2d7",
                "selection": "#00787d",
                "on_accent": "#ffffff",
                "icon_tint": "#40d2d7",
            },
        )
        self.assertEqual(
            style.accent_palette(
                "teal",
                "dark",
                dict(colors, selection="#101010", on_accent="#000000"),
            ),
            {
                "accent_fill": "#00787d",
                "accent_text": "#40d2d7",
                "selection": "#00787d",
                "on_accent": "#000000",
                "icon_tint": "#40d2d7",
            },
        )

    def test_builtin_accents_equal_the_extension(self):
        if not STYLE_C.is_file():
            self.skipTest("extensions repository is not checked out alongside")
        source = STYLE_C.read_text()
        table = re.search(
            r"accents\[RVT_ACCENTS\]\[2\]\[2\]\[4\] = \{(.*?)\};", source, re.S
        )
        rows = re.findall(r"\{\{(.*?)\}\}", table.group(1), re.S)
        self.assertEqual(len(rows), len(style.ACCENTS))
        for name, row in zip(style.ACCENTS, rows):
            colors = re.findall(r"RGB\((\d+), (\d+), (\d+)\)", row)
            self.assertEqual(
                tuple("".join(f"{int(c):02x}" for c in color) for color in colors),
                style.ACCENT_BUILTIN[name],
                name,
            )

    def test_decode_round_trip_and_rejections(self):
        colors, flags, palettes = classic("light")
        tinted = {5: "text", 639: ("icon_tint", "darkness")}
        decoded = style.decode(style.encode(colors, 5, palettes, tinted))
        self.assertEqual(decoded["colors"], colors)
        self.assertEqual(decoded["rendering"], 5)
        self.assertEqual(decoded["accents"], palettes)
        self.assertEqual(
            decoded["tinted"], {5: ("text", "alpha"), 639: ("icon_tint", "darkness")}
        )
        with self.assertRaisesRegex(ValueError, "exceeds 640"):
            style.encode(colors, 0, palettes, {640: "text"})
        with self.assertRaisesRegex(ValueError, "rendering flags"):
            style.encode(colors, 16, palettes, {})
        data = bytearray(style.encode(colors, 0, palettes, {}))
        data[3] = 0
        with self.assertRaisesRegex(ValueError, "opaque"):
            style.decode(bytes(data))
        data[3] = 255
        data[216] = 9
        with self.assertRaisesRegex(ValueError, "tint byte 9"):
            style.decode(bytes(data))
        data[216] = 8 | format.TINT_DARKNESS
        self.assertEqual(
            style.decode(bytes(data))["tinted"], {0: ("icon_tint", "darkness")}
        )
        self.assertAlmostEqual(style.contrast("#000000", "#ffffff"), 21.0)


if __name__ == "__main__":
    unittest.main()
