# SPDX-License-Identifier: GPL-3.0-only
"""PNG reading, palette fitting, the native pixel codecs and the lz codec."""

import struct
import unittest
import zlib
from pathlib import Path

import fixtures

from rvt import bitmaps, lz

RVX = Path(__file__).resolve().parents[2] / "revola" / "tools" / "rvx.py"


def chunk(kind, body):
    return (
        struct.pack(">I", len(body))
        + kind
        + body
        + struct.pack(">I", zlib.crc32(kind + body))
    )


def make_png(width, height, depth, color_type, rows, extra=(), idat_parts=1):
    """A PNG from filtered scanlines; `extra` chunks go between IHDR and IDAT
    and the compressed rows are split over idat_parts IDAT chunks."""
    header = struct.pack(">IIBBBBB", width, height, depth, color_type, 0, 0, 0)
    data = zlib.compress(rows)
    size = -(-len(data) // idat_parts)
    parts = [data[i : i + size] for i in range(0, len(data), size)]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + b"".join(chunk(kind, body) for kind, body in extra)
        + b"".join(chunk(b"IDAT", part) for part in parts)
        + chunk(b"IEND", b"")
    )


def filtered(raw_rows, stride, bpp, filter_type):
    """Scanlines of 8-bit samples encoded with one PNG filter."""
    out = bytearray()
    previous = bytes(stride)
    for row in raw_rows:
        out.append(filter_type)
        for x in range(stride):
            a = row[x - bpp] if x >= bpp else 0
            b = previous[x]
            c = previous[x - bpp] if x >= bpp else 0
            predictor = (0, a, b, (a + b) // 2, bitmaps.paeth(a, b, c))[filter_type]
            out.append((row[x] - predictor) & 255)
        previous = row
    return bytes(out)


def packed_indices(indices, depth):
    """One scanline of palette indices packed MSB first, with its filter byte."""
    bits = "".join(f"{i:0{depth}b}" for i in indices)
    bits += "0" * (-len(bits) % 8)
    return b"\0" + int(bits, 2).to_bytes(len(bits) // 8, "big")


class PngTests(unittest.TestCase):
    RGBA = bytes([10, 20, 30, 255, 40, 50, 60, 128, 70, 80, 90, 0, 1, 2, 3, 4])

    def test_palette_depths(self):
        palette = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 9, 9, 9])
        alpha = bytes([255, 128])
        for depth, indices in ((1, [0, 1, 1, 0]), (2, [0, 1, 2, 3]), (4, [3, 2, 1, 0])):
            with self.subTest(depth=depth):
                png = make_png(
                    4,
                    1,
                    depth,
                    3,
                    packed_indices(indices, depth),
                    [(b"PLTE", palette), (b"tRNS", alpha)],
                )
                width, height, rgba = bitmaps.read_png(png)
                self.assertEqual((width, height), (4, 1))
                expected = b"".join(
                    palette[i * 3 : i * 3 + 3] + bytes([alpha[i] if i < 2 else 255])
                    for i in indices
                )
                self.assertEqual(rgba, expected)

    def test_gray_and_rgb_with_transparent_colour(self):
        gray = make_png(3, 1, 8, 0, b"\0\x10\x20\x30", [(b"tRNS", b"\0\x20")])
        self.assertEqual(
            bitmaps.read_png(gray)[2],
            bytes([16, 16, 16, 255, 32, 32, 32, 0, 48, 48, 48, 255]),
        )
        gray_alpha = make_png(2, 1, 8, 4, b"\0\x10\x80\x20\xff")
        self.assertEqual(
            bitmaps.read_png(gray_alpha)[2], bytes([16, 16, 16, 128, 32, 32, 32, 255])
        )
        rgb = make_png(
            2,
            1,
            8,
            2,
            b"\0\x01\x02\x03\x04\x05\x06",
            [(b"tRNS", b"\0\x04\0\x05\0\x06")],
        )
        self.assertEqual(bitmaps.read_png(rgb)[2], bytes([1, 2, 3, 255, 4, 5, 6, 0]))

    def test_filters_and_multiple_idat_chunks(self):
        rows = [self.RGBA[:8], self.RGBA[8:]]
        for filter_type in range(5):
            with self.subTest(filter=filter_type):
                png = make_png(
                    2, 2, 8, 6, filtered(rows, 8, 4, filter_type), idat_parts=3
                )
                self.assertEqual(bitmaps.read_png(png), (2, 2, self.RGBA))

    def test_malformed_png_is_rejected(self):
        good = make_png(2, 2, 8, 6, filtered([self.RGBA[:8], self.RGBA[8:]], 8, 4, 0))
        cases = {
            "not a PNG": good[1:],
            "truncated PNG": good[:-20],
            "truncated PNG ": good[:40],
            "checksum": good[:-5] + bytes([good[-5] ^ 1]) + good[-4:],
            "interlaced": make_png(1, 1, 8, 6, bytes(5))[:28]
            + b"\1"
            + make_png(1, 1, 8, 6, bytes(5))[29:],
            "pixel length": make_png(2, 2, 8, 6, bytes(9)),
            "row filter": make_png(1, 1, 8, 6, b"\5\0\0\0\0"),
            "exceeds palette": make_png(1, 1, 8, 3, b"\0\3", [(b"PLTE", bytes(3))]),
            "16-bit": make_png(1, 1, 16, 6, bytes(9)),
        }
        for name, bad in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                bitmaps.read_png(bad)

    def test_write_png_round_trip(self):
        png = bitmaps.write_png(2, 2, self.RGBA)
        self.assertEqual(bitmaps.read_png(png), (2, 2, self.RGBA))


class PaletteTests(unittest.TestCase):
    def test_fit_palette_reserves_transparent_and_keeps_fitting_art(self):
        rgba = b"".join(bytes((v, v, v, 255)) for v in range(16)) + bytes(4)
        self.assertEqual(bitmaps.fit_palette(rgba, 17), rgba)
        fitted = bitmaps.fit_palette(rgba, 4)
        colors = {fitted[i : i + 4] for i in range(0, len(fitted), 4)}
        self.assertEqual(len(colors), 4)
        self.assertIn(bytes(4), colors)
        self.assertEqual(fitted[-4:], bytes(4))
        self.assertEqual(bitmaps.distinct(rgba), 17)

    def test_fit_levels_reduces_coverage_alone(self):
        levels = bytes(range(0, 256, 5))
        fitted = bitmaps.fit_levels(levels, 8)
        self.assertEqual(len(set(fitted)), 8)
        self.assertEqual(fitted[0], 0)
        self.assertEqual(
            bitmaps.fit_levels(bytes([0, 100, 200]), 3), bytes([0, 100, 200])
        )
        # The tint colour does not change which levels survive.
        for tint in ("#ff0000", "#00ff00"):
            tinted = bitmaps.tinted_pixels(fitted, tint)
            self.assertEqual(tinted[3::4], fitted)


class CodecTests(unittest.TestCase):
    def setUp(self):
        self.catalog = fixtures.catalog()

    def round_trip(self, name, rgba):
        info = self.catalog.assets[self.catalog.resolve(name, "x")]
        payload = bitmaps.encode_pixels(info, info["width"], info["height"], rgba)
        self.assertEqual(len(payload), info["bytes"] - info["data_offset"])
        self.assertTrue(bitmaps.palette_indices_fit(info, payload))
        return payload, bitmaps.decode_pixels(info, payload)

    def test_each_format_round_trips(self):
        two = bytes([10, 20, 30, 255, 40, 50, 60, 128]) * 2
        payload, back = self.round_trip("Alpha", two)
        self.assertEqual(back, two)
        self.assertEqual(payload[:8], bytes([30, 20, 10, 255, 60, 50, 40, 128]))
        eight = b"".join(bytes((i, i * 2, i * 3, 255)) for i in range(8)) + bytes(16)
        eight = eight[:32] + eight[:16]
        _, back = self.round_trip("Iota", eight)
        self.assertEqual(back, eight)
        bgra = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        payload, back = self.round_trip("Beta", bgra)
        self.assertEqual(back, bgra)
        self.assertEqual(payload[:4], bytes([3, 2, 1, 4]))
        rgb = bytes([248, 252, 248, 255, 8, 4, 8, 255]) * 2
        payload, back = self.round_trip("Zeta", rgb)
        self.assertEqual(back, rgb)
        self.assertEqual(struct.unpack_from("<H", payload)[0], 0xFFFF)
        gray = b"".join(bytes((v, v, v, 255)) for v in (0, 7, 200, 255))
        _, back = self.round_trip("Delta", gray)
        self.assertEqual(back, gray)

    def test_four_bit_masks_round_to_sixteen_levels(self):
        gray = b"".join(bytes((v, v, v, 255)) for v in (0, 100, 110, 255))
        payload, back = self.round_trip("Epsilon", gray)
        self.assertEqual(payload, bytes([0x06, 0x6F]))
        self.assertEqual(back[::4], bytes((0, 102, 102, 255)))

    def test_encode_rejections(self):
        info = self.catalog.assets[0]
        with self.assertRaisesRegex(ValueError, "expected 4x1"):
            bitmaps.encode_pixels(info, 3, 1, bytes(12))
        with self.assertRaisesRegex(
            ValueError, "4 colours exceed the 2 of its palette"
        ):
            bitmaps.encode_pixels(info, 4, 1, bytes(range(16)))
        zeta = self.catalog.assets[5]
        with self.assertRaisesRegex(ValueError, "opaque"):
            bitmaps.encode_pixels(zeta, 4, 1, bytes(16))
        delta = self.catalog.assets[3]
        with self.assertRaisesRegex(ValueError, "gray"):
            bitmaps.encode_pixels(delta, 4, 1, bytes([1, 2, 3, 255]) * 4)
        with self.assertRaisesRegex(ValueError, "truncated bitmap"):
            bitmaps.describe(1, 0, bytes(16))


class LzTests(unittest.TestCase):
    def test_round_trip(self):
        samples = [
            b"",
            b"a",
            b"abcabcabcabcx",
            bytes(5000),
            bytes(range(256)) * 20,
            b"".join(bytes([i % 7, i % 11]) for i in range(3000)),
        ]
        for data in samples:
            with self.subTest(len(data)):
                stream = lz.lz_encode(data)
                self.assertEqual(lz.lz_decode(stream, len(data)), data)

    def test_known_stream(self):
        # Literals a b c, a match of 9 bytes from 3 back, the literal x.
        self.assertEqual(
            lz.lz_encode(b"abcabcabcabcx"),
            bytes([0x08, 0x61, 0x62, 0x63, 0x60, 0x02, 0x78]),
        )
        # A long match: L = 15 and one more length byte.
        self.assertEqual(lz.lz_encode(bytes(40)), bytes([0x02, 0x00, 0xF0, 0x00, 0x15]))

    def test_decode_rejections(self):
        stream = lz.lz_encode(b"abcabcabcabcx")
        with self.assertRaisesRegex(ValueError, "ends early"):
            lz.lz_decode(stream[:-1], 13)
        with self.assertRaisesRegex(ValueError, "continues past"):
            lz.lz_decode(stream + b"\0", 13)
        with self.assertRaisesRegex(ValueError, "continues past"):
            lz.lz_decode(stream, 12)
        with self.assertRaisesRegex(ValueError, "outside the output"):
            lz.lz_decode(bytes([0x01, 0x00, 0x05]), 4)

    def test_matches_the_rvx_encoder(self):
        if not RVX.is_file():
            self.skipTest("revola repository is not checked out alongside")
        namespace = {}
        source = RVX.read_text()
        start = source.index("WINDOW = ")
        end = source.index("def api_word")
        exec(source[start:end], namespace)  # noqa: S102
        for data in (b"abcabcabcabcx", bytes(range(256)) * 4, bytes(300)):
            self.assertEqual(namespace["lz_encode"](data), lz.lz_encode(data))
        self.assertEqual(
            (namespace["WINDOW"], namespace["MIN_MATCH"], namespace["CHAIN"]),
            (lz.WINDOW, lz.MIN_MATCH, lz.CHAIN),
        )


if __name__ == "__main__":
    unittest.main()
