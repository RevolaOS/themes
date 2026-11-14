# SPDX-License-Identifier: GPL-3.0-only
"""Extension bitmaps: the folders, the SDK's encoding rules, the extension
asset catalog and its additions, the table in the pack, the inspector's checks,
the catalog commands and the generated docs page."""

import contextlib
import io
import json
import os
import random
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

import fixtures
from fixtures import rgba_png

from rvt import assets, cli, inspector, lz, rvtfile
from rvt.compiler import compile_theme
from tools import extension_bitmaps_doc, extensions_catalog

ROOT = Path(__file__).resolve().parents[1]
THEME = 'schema = 1\nid = "test"\nname = "Test"\n'
FLAT = (
    THEME
    + "[light.rendering]\nflat_icons = true\n[dark.rendering]\nflat_icons = true\n"
)
W, H = assets.MENU_WIDTH, assets.MENU_HEIGHT
MENU_BYTES = assets.HEADER.size + assets.MENU_STRIDE * H
# Two asset names with the same FNV-1a hash.
COLLIDING = ("7yzlaa", "e6apaa")
MOON = ("appearance", "settings-moon")
MOON_PNG = "light/extensions/appearance/settings-moon.png"


def icon_png(rows=range(12, 63), alpha=True, color=(0, 0, 0)):
    """A 78x121 icon whose pixels in `rows` are fully covered: by alpha over
    `color`, or as opaque white on black."""
    pixels = bytearray()
    for y in range(H):
        for _ in range(W):
            on = y in rows
            if alpha:
                pixels += bytes((*color, 255 if on else 0))
            else:
                pixels += bytes((255, 255, 255, 255) if on else (0, 0, 0, 255))
    return rgba_png(W, H, bytes(pixels))


def picture_png(width, height, colors):
    """A PNG cycling through `colors`, RGBA tuples."""
    pixels = b"".join(bytes(colors[i % len(colors)]) for i in range(width * height))
    return rgba_png(width, height, pixels)


def rainbow(count):
    return [(i & 255, i >> 8 & 255, 7, 255) for i in range(count)]


def record(identifier, asset, width, height, menu=False, fmt=None, colors=0):
    if menu:
        fmt, colors, stride, depth = assets.MASK8, 0, assets.MENU_STRIDE, 8
    else:
        fmt = assets.INDEXED8 if fmt is None else fmt
        depth = 8 if fmt == assets.INDEXED8 else 32
        stride = (width * depth // 8 + 3) & ~3
    return {
        "id": identifier,
        "asset": asset,
        "menu": menu,
        "format": fmt,
        "width": width,
        "height": height,
        "stride": stride,
        "depth": depth,
        "palette_colors": colors,
        "bytes": assets.HEADER.size
        + (4 + 4 * colors if colors else 0)
        + stride * height,
        "preload": "optional" if menu else "never",
    }


def table(*entries):
    """An extension bitmap table from (owner, asset, kind, payload[, decoded
    [, stored]]); decoded defaults to a Settings icon, stored to the payload."""
    data = b""
    for owner, name, kind, payload, *rest in entries:
        decoded = rest[0] if rest else MENU_BYTES
        stored = rest[1] if len(rest) > 1 else len(payload)
        data += rvtfile.EXTENSION_BITMAP.pack(owner, name, kind, stored, decoded)
        data += payload + bytes(-len(data + payload) % 4)
    return data


class EncodingTests(unittest.TestCase):
    def test_encoder_is_the_sdk_copy(self):
        sdk = ROOT.parent / "revola" / "tools" / "bitmap.py"
        if not sdk.is_file():
            self.skipTest("revola repository is not checked out alongside")
        self.assertEqual(
            (ROOT / "rvt" / "data" / "bitmap.py").read_bytes(), sdk.read_bytes()
        )

    def test_hashes_match_the_core(self):
        self.assertEqual(assets.owner_hash("revola"), 0xF802A4B0)
        self.assertEqual(rvtfile.fnv1a(COLLIDING[0].encode()), 0x2C91828D)
        self.assertEqual(
            rvtfile.fnv1a(COLLIDING[0].encode()), rvtfile.fnv1a(COLLIDING[1].encode())
        )

    def test_mask_follows_encode_mask(self):
        translucent = b"".join(bytes((9, 9, 9, a)) for a in (0, 128, 255)) * (
            W * H // 3
        )
        bmap = assets.bitmap.encode_mask(W, H, translucent)
        self.assertEqual(len(bmap), MENU_BYTES)
        self.assertEqual(bmap[:28], assets.MENU_HEADER)
        self.assertEqual(
            assets.HEADER.unpack(bmap[:28]), (8, 0, 80, 8, 0, 0, 121, 78, 9680)
        )
        self.assertTrue(assets.is_menu(bmap))
        self.assertEqual(bmap[28:31], bytes((0, 128, 255)))
        self.assertEqual(bmap[28 + 78 : 28 + 80], bytes(2))
        gray = b"".join(bytes((v, v, v, 255)) for v in (0, 7, 200)) * (W * H // 3)
        self.assertEqual(
            assets.bitmap.encode_mask(W, H, gray)[28:31], bytes((0, 7, 200))
        )
        # Opaque art with an alpha hole uses alpha even where it is grayscale.
        mixed = bytearray(gray)
        mixed[3] = 0
        self.assertEqual(
            assets.bitmap.encode_mask(W, H, bytes(mixed))[28:31], bytes((0, 255, 255))
        )
        with self.assertRaisesRegex(ValueError, "a menu bitmap is coverage"):
            assets.bitmap.encode_mask(W, H, bytes((200, 10, 10, 255)) * (W * H))
        with self.assertRaisesRegex(ValueError, "a menu bitmap is 78 x 121, not 4 x 1"):
            assets.bitmap.encode_mask(4, 1, bytes(16))

    def test_picture_follows_encode_bmap(self):
        # Five pixels of three colours: Indexed8, a palette of three, stride 8.
        colors = [(1, 2, 3, 255), (4, 5, 6, 128), (1, 2, 3, 255), (7, 8, 9, 0)]
        rgba = b"".join(bytes(c) for c in colors) + bytes((4, 5, 6, 128))
        bmap = assets.bitmap.encode_bmap(5, 1, rgba)
        fmt, _, stride, depth, top, left, bottom, right, payload = assets.HEADER.unpack(
            bmap[:28]
        )
        self.assertEqual(
            (fmt, stride, depth, top, left, bottom, right), (0x64, 8, 8, 0, 0, 1, 5)
        )
        self.assertEqual(payload, 4 + 12 + 8)
        self.assertEqual(len(bmap), 28 + payload)
        self.assertEqual(struct.unpack_from("<I", bmap, 28)[0], 3)
        self.assertEqual(bmap[32:44], bytes((3, 2, 1, 255, 6, 5, 4, 128, 9, 8, 7, 0)))
        self.assertEqual(bmap[44:52], bytes((0, 1, 0, 2, 1, 0, 0, 0)))
        self.assertFalse(assets.is_menu(bmap))
        self.assertTrue(assets.header_sane(bmap))
        # More than 256 colours: BGRA8888, four bytes per pixel.
        many = b"".join(bytes(c) for c in rainbow(257))
        bmap = assets.bitmap.encode_bmap(257, 1, many)
        self.assertEqual(assets.HEADER.unpack(bmap[:28])[:4], (0x1888, 0, 1028, 32))
        self.assertEqual(bmap[28:32], bytes((7, 0, 0, 255)))
        self.assertEqual(len(bmap), 28 + 1028)
        self.assertTrue(assets.header_sane(bmap))
        self.assertEqual(
            assets.describe(bmap),
            {
                "width": 257,
                "height": 1,
                "format": "bgra8888",
                "palette": 0,
                "menu": False,
            },
        )

    def test_bitmap_matches_the_catalog_record(self):
        with tempfile.TemporaryDirectory() as name:
            png = Path(name) / "a.png"
            # Unknown asset: a 78x121 coverage PNG is a menu bitmap.
            png.write_bytes(icon_png())
            self.assertTrue(assets.is_menu(assets.encode(png, "x", None)))
            # Unknown asset of another size: the catalog is needed.
            png.write_bytes(rgba_png(4, 1, bytes(16)))
            with self.assertRaises(ValueError) as caught:
                assets.encode(png, "x", None)
            self.assertEqual(
                str(caught.exception),
                "x: 4x1 is not a menu bitmap and the asset is not in the extension "
                "asset catalog; pass --extension assets.json of the extension",
            )
            # A record says the size and whether it is a menu bitmap.
            bmap = assets.encode(png, "x", record("e", "a", 4, 1))
            self.assertEqual(assets.describe(bmap)["format"], "indexed8")
            with self.assertRaises(ValueError) as caught:
                assets.encode(png, "x", record("e", "a", 5, 2))
            self.assertEqual(str(caught.exception), "x: expected 5x2, got 4x1")
            with self.assertRaisesRegex(ValueError, "x: a menu bitmap is 78 x 121"):
                assets.encode(png, "x", record("e", "a", 78, 121, menu=True))
            png.write_bytes(icon_png())
            self.assertTrue(
                assets.is_menu(
                    assets.encode(png, "x", record("e", "a", 78, 121, menu=True))
                )
            )
            # A menu-sized PNG of a picture asset is a picture.
            bmap = assets.encode(png, "x", record("e", "a", 78, 121))
            self.assertFalse(assets.is_menu(bmap))
            self.assertEqual(assets.describe(bmap)["format"], "indexed8")
            # The cap: 200x100 in BGRA is 80,028 bytes.
            png.write_bytes(picture_png(200, 100, rainbow(300)))
            with self.assertRaisesRegex(ValueError, "x: 80,028 bytes exceed 65,536"):
                assets.encode(png, "x", record("e", "a", 200, 100))
            png.write_bytes(icon_png()[:-20])
            with self.assertRaisesRegex(ValueError, "x: truncated PNG"):
                assets.encode(png, "x", None)

    def test_table_is_sorted_by_hash_and_compressed_when_smaller(self):
        flat = assets.MENU_HEADER + bytes(assets.MENU_STRIDE * H)
        # Rows that compress badly stay raw.
        noisy = assets.MENU_HEADER + random.Random(1).randbytes(assets.MENU_STRIDE * H)
        data, count, counts = assets.encode_table(
            {("revola", "extensions"): flat, MOON: noisy}
        )
        self.assertEqual(count, 2)
        self.assertEqual(counts, {"bitmap": 1, "bitmap_lz": 1})
        found, end = assets.decode_table(data, 0, 2, "light")
        self.assertEqual(end, len(data))
        self.assertEqual(
            [(a["owner"], a["asset"]) for a in found],
            sorted(
                [
                    (assets.owner_hash("revola"), assets.asset_hash("extensions")),
                    (assets.owner_hash(*MOON[:1]), assets.asset_hash(MOON[1])),
                ]
            ),
        )
        names = assets.known_names(assets.load_catalog())
        by_name = {assets.label(a, names): a for a in found}
        self.assertEqual(by_name["revola/extensions"]["kind"], "bitmap_lz")
        self.assertEqual(by_name["revola/extensions"]["bmap"], flat)
        self.assertEqual(by_name["appearance/settings-moon"]["kind"], "bitmap")
        self.assertEqual(by_name["appearance/settings-moon"]["bmap"], noisy)
        self.assertEqual(by_name["appearance/settings-moon"]["bytes"], MENU_BYTES)
        self.assertEqual(
            {k: by_name["revola/extensions"][k] for k in ("width", "height", "format")},
            {"width": 78, "height": 121, "format": "mask8"},
        )
        self.assertEqual(
            assets.label({"owner": 1, "asset": 2}, {}), "0x00000001/0x00000002"
        )
        self.assertEqual(by_name["revola/extensions"]["decoded"], MENU_BYTES)
        self.assertLess(by_name["revola/extensions"]["bytes"], MENU_BYTES)
        too_many = {("a", f"x{i}"): flat for i in range(65)}
        with self.assertRaisesRegex(ValueError, "65 extension bitmaps exceed 64"):
            assets.encode_table(too_many)

    def test_header_sanity_follows_core_bitmap_whole(self):
        def header(fmt=8, stride=80, depth=8, bounds=(0, 0, 121, 78), payload=9680):
            return assets.HEADER.pack(fmt, 0, stride, depth, *bounds, payload)

        rows = bytes(9680)
        self.assertTrue(assets.header_sane(header() + rows))
        bad = {
            "bottom above top": header(bounds=(121, 0, 0, 78)),
            "right left of left": header(bounds=(0, 78, 121, 0)),
            "pixels wider than the stride": header(stride=76),
            "depth over 32": header(depth=64, stride=80 * 8),
            "rows past the payload": header(payload=9679),
            "palette count past 256": header(fmt=0x64, payload=9680)
            + struct.pack("<I", 300),
            "palette past the payload": header(fmt=0x64, payload=9680)
            + struct.pack("<I", 256),
            "payload too short for a count": header(fmt=0x64, payload=3),
        }
        for name, data in bad.items():
            with self.subTest(name):
                self.assertFalse(assets.header_sane(data.ljust(28 + 9680, b"\0")))
        # An Indexed8 header whose palette and rows fit.
        indexed = header(fmt=0x64, stride=4, bounds=(0, 0, 1, 4), payload=4 + 8 + 4)
        self.assertTrue(assets.header_sane(indexed + struct.pack("<I", 2) + bytes(12)))

    def test_decode_rejections(self):
        flat = assets.MENU_HEADER + bytes(9680)
        stream = lz.lz_encode(flat)
        raw, packed = (
            rvtfile.EXTENSION_KINDS["bitmap"],
            rvtfile.EXTENSION_KINDS["bitmap_lz"],
        )
        good = table((1, 1, packed, stream), (1, 2, raw, flat))
        self.assertEqual(len(assets.decode_table(good, 0, 2, "p")[0]), 2)
        # An lz stream whose length is not a multiple of 4, so it is padded.
        unaligned = next(
            lz.lz_encode(assets.MENU_HEADER + bytes((i,)) + bytes(9679))
            for i in range(1, 9)
            if len(lz.lz_encode(assets.MENU_HEADER + bytes((i,)) + bytes(9679))) % 4
        )
        over_cap = assets.HEADER.pack(0x1888, 0, 256, 32, 0, 0, 256, 64, 65536)
        wide = assets.HEADER.pack(8, 0, 76, 8, 0, 0, 121, 78, 9680)
        cases = {
            "65 extension bitmaps exceed": (good, 65),
            "truncated extension bitmap header": (
                table((1, 1, packed, stream)) + bytes(8),
                2,
            ),
            "sorted by unique owner": (table((1, 2, raw, flat)) + good, 3),
            "unknown kind 0x3": (table((1, 1, 3, flat)), 1),
            "decoded size smaller than a header": (
                table((1, 1, raw, assets.MENU_HEADER, 28)),
                1,
            ),
            "truncated payload": (table((1, 1, raw, flat, MENU_BYTES, 9712)), 1),
            "raw payload is not its decoded size": (
                table((1, 1, raw, flat[:-4])),
                1,
            ),
            "lz stream continues": (table((1, 1, packed, stream + b"\0")), 1),
            "lz stream ends early": (table((1, 1, packed, stream[:-1])), 1),
            "lz stream longer than its bitmap allows": (
                table((1, 1, packed, bytes(9708 + 1214 + 1))),
                1,
            ),
            "65,564 bytes exceed 65,536": (
                table((1, 1, raw, over_cap + bytes(65536), 65564)),
                1,
            ),
            "header does not describe its bytes": (
                table((1, 1, raw, wide + bytes(9680))),
                1,
            ),
            "header does not describe its bytes$": (
                table((1, 1, raw, flat + bytes(4), MENU_BYTES + 4)),
                1,
            ),
            "padding must be zero": (
                table(
                    (
                        1,
                        1,
                        packed,
                        unaligned + bytes(-len(unaligned) % 4 - 1) + b"\1",
                        MENU_BYTES,
                        len(unaligned),
                    )
                ),
                1,
            ),
        }
        for pattern, (body, count) in cases.items():
            with self.subTest(pattern), self.assertRaisesRegex(ValueError, pattern):
                assets.decode_table(body, 0, count, "p")


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_vendored_catalog(self):
        records = assets.load_catalog()
        self.assertIn(("revola", "extensions"), records)
        self.assertEqual(records["revola", "extensions"]["bytes"], MENU_BYTES)
        text = Path(str(assets.CATALOG)).read_text()
        lines = text.splitlines()
        self.assertEqual(len(lines), len(records))
        self.assertEqual(
            lines,
            sorted(
                lines,
                key=lambda line: (json.loads(line)["id"], json.loads(line)["asset"]),
            ),
        )
        self.assertEqual(
            [json.dumps(json.loads(line), sort_keys=True) for line in lines], lines
        )

    def test_json_additions_and_rejections(self):
        path = self.root / "assets.json"
        path.write_text(
            json.dumps(record("third", "logo", 4, 1))
            + "\n\n"
            + json.dumps(record("revola", "extensions", 78, 121, menu=True))
            + "\n"
        )
        records = assets.load_catalog([path])
        self.assertEqual(records["third", "logo"]["width"], 4)
        self.assertIn(MOON, records)
        bad = {
            "expected a record with the keys": {"id": "x"},
            "id must match": {**record("Third", "a", 1, 1)},
            "asset must match": {**record("third", "A", 1, 1)},
            "menu is true or false": {**record("third", "a", 1, 1), "menu": 1},
            "width is a non-negative integer": {
                **record("third", "a", 1, 1),
                "width": -1,
            },
            "width and height are at least 1": {**record("third", "a", 0, 1)},
            "a menu bitmap is 78x121": {**record("third", "a", 4, 1), "menu": True},
        }
        for pattern, document in bad.items():
            path.write_text(json.dumps(document) + "\n")
            with (
                self.subTest(pattern),
                self.assertRaisesRegex(ValueError, f"{path}:1: {pattern}"),
            ):
                assets.load_catalog([path])
        path.write_text("{\n")
        with self.assertRaisesRegex(ValueError, f"{path}:1: "):
            assets.load_catalog([path])
        with self.assertRaisesRegex(
            ValueError, "--extension: .*missing.json does not exist"
        ):
            assets.load_catalog([self.root / "missing.json"])
        (self.root / "x.txt").write_text("")
        with self.assertRaisesRegex(ValueError, "expected an assets.json"):
            assets.load_catalog([self.root / "x.txt"])


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "src"
        self.root.mkdir()
        self.catalog = fixtures.catalog()

    def tearDown(self):
        self.directory.cleanup()

    def theme(self, toml=THEME + "[light]\n", extensions=None, **files):
        (self.root / "theme.toml").write_text(toml)
        for appearance in ("light", "dark"):
            if (self.root / appearance).is_dir():
                shutil.rmtree(self.root / appearance)
        for path, data in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return compile_theme(self.catalog, self.root, extensions=extensions)

    def rejects(self, pattern, toml=THEME + "[light]\n", extensions=None, **files):
        with self.assertRaisesRegex(ValueError, pattern):
            self.theme(toml, extensions, **files)

    def test_bitmaps_land_in_the_pack(self):
        build = self.theme(
            FLAT,
            **{
                MOON_PNG: icon_png(),
                "light/revola/extensions.png": icon_png(alpha=False),
                "dark/extensions/appearance/settings-moon.png": icon_png(),
            },
        )
        self.assertEqual(build.warnings, [])
        light = build.inspection["appearances"]["light"]
        found = light["extension_bitmaps"]
        self.assertEqual(
            [a["name"] for a in found],
            ["appearance/settings-moon", "revola/extensions"],
        )
        self.assertTrue(all(a["kind"] == "bitmap_lz" for a in found))
        self.assertEqual(found[0]["bmap"][:28], assets.MENU_HEADER)
        self.assertEqual(
            found[0]["bmap"][28 + 12 * 80 : 28 + 12 * 80 + 78], b"\xff" * 78
        )
        self.assertEqual(found[0]["bmap"][28 : 28 + 80], bytes(80))
        self.assertEqual(
            len(build.inspection["appearances"]["dark"]["extension_bitmaps"]), 1
        )
        self.assertEqual(
            build.report["appearances"]["light"]["extension_bitmaps"], {"bitmap_lz": 2}
        )
        _, count, bitmap_count = rvtfile.decode_file(build.data)["packs"]["light"]
        self.assertEqual((count, bitmap_count), (0, 2))
        # Without names the inspector shows the hashes.
        plain = inspector.inspect(build.data)["appearances"]["light"][
            "extension_bitmaps"
        ]
        self.assertEqual(plain[1]["name"], "0xf802a4b0/0x161194cb")
        self.assertIn(
            "2 extension bitmaps: appearance/settings-moon 78x121 mask8, "
            "revola/extensions 78x121 mask8",
            inspector.describe(build.inspection),
        )

    def test_picture_assets_follow_their_record(self):
        extensions = {
            **assets.load_catalog(),
            ("third", "logo"): record("third", "logo", 4, 1),
            ("third", "big"): record("third", "big", 257, 1),
        }
        build = self.theme(
            THEME + "[light]\n",
            extensions,
            **{
                "light/extensions/third/logo.png": rgba_png(4, 1, bytes(range(16))),
                "light/extensions/third/big.png": picture_png(257, 1, rainbow(257)),
            },
        )
        self.assertEqual(build.warnings, [])
        found = {
            a["name"]: a
            for a in build.inspection["appearances"]["light"]["extension_bitmaps"]
        }
        self.assertEqual(
            (found["third/logo"]["format"], found["third/logo"]["palette"]),
            ("indexed8", 4),
        )
        self.assertEqual(found["third/big"]["format"], "bgra8888")
        self.rejects(
            "light/extensions/third/logo.png: expected 4x1, got 5x1",
            THEME + "[light]\n",
            extensions,
            **{"light/extensions/third/logo.png": rgba_png(5, 1, bytes(20))},
        )

    def test_unknown_asset_compiles_only_as_a_settings_icon(self):
        build = self.theme(
            FLAT,
            **{
                "light/extensions/third-party/settings-x.png": icon_png(),
                MOON_PNG: icon_png(),
            },
        )
        self.assertEqual(
            build.warnings,
            [
                "light/extensions/third-party/settings-x.png: not in the extension "
                "asset catalog, compiled as a Settings icon; docs/extension-bitmaps.md "
                "lists the first-party bitmaps, --extension adds others"
            ],
        )
        self.assertEqual(
            len(build.inspection["appearances"]["light"]["extension_bitmaps"]), 2
        )
        self.rejects(
            r"light/extensions/third-party/logo.png: 4x1 is not a menu bitmap and the "
            r"asset is not in the extension asset catalog; pass --extension",
            **{"light/extensions/third-party/logo.png": rgba_png(4, 1, bytes(16))},
        )

    def test_art_outside_its_folder_is_rejected(self):
        self.rejects(
            r"light/extensions/revola: revola is the core's id; its bitmaps go in "
            r"light/revola/",
            **{"light/extensions/revola/extensions.png": icon_png()},
        )
        self.rejects(
            r"light/stray.png: catalog art goes in light/apple/, extension bitmaps "
            r"in light/extensions/<extension-id>/, the core's in light/revola/",
            **{"light/stray.png": icon_png()},
        )
        self.rejects(
            r"dark: has art but theme.toml declares no \[dark\]",
            **{"dark/revola/extensions.png": icon_png()},
        )
        self.rejects(
            "light/revola/Extensions.png: expected <asset>.png",
            **{"light/revola/Extensions.png": icon_png()},
        )

    def test_reflection_warning_follows_flat_icons_for_menu_bitmaps(self):
        files = {MOON_PNG: icon_png()}
        build = self.theme(**files)
        self.assertEqual(
            build.warnings,
            [
                f"{MOON_PNG}: no reflection below the art; draw one or set "
                "flat_icons = true in [light.rendering]"
            ],
        )
        build = self.theme(THEME + "[light.rendering]\nflat_icons = true\n", **files)
        self.assertEqual(build.warnings, [])
        reflected = icon_png(rows=list(range(12, 63)) + [100])
        build = self.theme(**{MOON_PNG: reflected})
        self.assertEqual(build.warnings, [])
        extensions = {("third", "logo"): record("third", "logo", 4, 1)}
        build = self.theme(
            THEME + "[light]\n",
            extensions,
            **{"light/extensions/third/logo.png": rgba_png(4, 1, bytes(16))},
        )
        self.assertEqual(build.warnings, [])

    def test_bad_names_and_colliding_hashes_are_rejected(self):
        cases = {
            "light/extensions/Appearance: expected an extension id": {
                "light/extensions/Appearance/settings-moon.png": icon_png()
            },
            "light/extensions/1st: expected an extension id": {
                "light/extensions/1st/x.png": icon_png()
            },
            "light/extensions/" + "a" * 33 + ": expected an extension id": {
                "light/extensions/" + "a" * 33 + "/x.png": icon_png()
            },
            "light/extensions/stray.png: expected a folder named after an extension id": {
                "light/extensions/stray.png": icon_png()
            },
            "light/extensions/appearance/Settings-Moon.png: expected <asset>.png": {
                "light/extensions/appearance/Settings-Moon.png": icon_png()
            },
            "light/extensions/appearance/settings-moon.toml: expected <asset>.png": {
                "light/extensions/appearance/settings-moon.toml": b"x"
            },
            "light/extensions/appearance/" + "a" * 32 + ".png: expected <asset>.png": {
                "light/extensions/appearance/" + "a" * 32 + ".png": icon_png()
            },
            f"{MOON_PNG}: a menu bitmap is 78 x 121, not 4 x 1": {
                MOON_PNG: rgba_png(4, 1, bytes(16))
            },
            f"{MOON_PNG}: a menu bitmap is coverage": {
                MOON_PNG: rgba_png(W, H, bytes((200, 10, 10, 255)) * (W * H))
            },
            f"{MOON_PNG}: truncated PNG": {MOON_PNG: icon_png()[:-20]},
            "extensions/appearance/e6apaa.png: its hashes collide with "
            "extensions/appearance/7yzlaa.png": {
                f"light/extensions/appearance/{COLLIDING[0]}.png": icon_png(),
                f"dark/extensions/appearance/{COLLIDING[1]}.png": icon_png(),
            },
        }
        for pattern, files in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, THEME + "[light]\n[dark]\n", **files)
        # The same name in both appearances is two bitmaps, not a collision.
        build = self.theme(
            THEME + "[light]\n[dark]\n",
            **{MOON_PNG: icon_png(), MOON_PNG.replace("light", "dark"): icon_png()},
        )
        self.assertEqual(
            len(build.inspection["appearances"]["dark"]["extension_bitmaps"]), 1
        )
        self.theme(THEME + "[light]\n[dark]\n")
        (self.root / "light" / "extensions" / "appearance").mkdir(parents=True)
        outside = self.root.parent / "settings-moon.png"
        outside.write_bytes(icon_png())
        (self.root / MOON_PNG).symlink_to(outside)
        with self.assertRaisesRegex(ValueError, f"{MOON_PNG}: must be a file inside"):
            compile_theme(self.catalog, self.root)

    def test_more_than_the_cap_of_extension_bitmaps_is_rejected(self):
        files = {
            f"light/extensions/appearance/icon-{i:02}.png": icon_png()
            for i in range(65)
        }
        self.rejects("65 extension bitmaps exceed 64", THEME + "[light]\n", **files)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.catalog = self.root / "catalog.json"
        self.catalog.write_text(json.dumps(fixtures.catalog_document()))
        self.previous = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.previous)
        self.directory.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        status = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                cli.main([str(a) for a in args])
            except SystemExit as exit_:
                status = exit_.code
        return status, out.getvalue(), err.getvalue()

    def test_catalog_list_and_show(self):
        status, out, _ = self.run_cli("catalog", "list", "--extensions")
        self.assertEqual(status, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "appearance settings-accent 78x121 mask8 0 menu")
        self.assertEqual(len(lines), len(assets.load_catalog()))
        _, out, _ = self.run_cli("catalog", "list", "--extensions", "--group", "revola")
        self.assertEqual(
            out,
            "revola extensions 78x121 mask8 0 menu\n"
            "revola info 78x121 mask8 0 menu\n"
            "revola optimize 78x121 mask8 0 menu\n",
        )
        _, out, _ = self.run_cli(
            "catalog", "list", "--extensions", "--format", "indexed8"
        )
        self.assertEqual(out, "")
        status, _, err = self.run_cli(
            "catalog", "list", "--extensions", "--format", "gif"
        )
        self.assertEqual(status, 1)
        self.assertIn("--format: expected one of mask8, indexed8, bgra8888", err)
        _, out, _ = self.run_cli("catalog", "show", "revola/extensions")
        self.assertIn("id revola\nasset extensions\nmenu true\nformat 0x8\n", out)
        self.assertIn(
            "format_name mask8\nowner_hash 0xf802a4b0\nasset_hash 0x161194cb", out
        )
        status, _, err = self.run_cli("catalog", "show", "nope/x")
        self.assertEqual(status, 1)
        self.assertIn("'nope/x' is not in the extension asset catalog", err)
        addition = self.root / "assets.json"
        addition.write_text(json.dumps(record("third", "logo", 4, 1)) + "\n")
        _, out, _ = self.run_cli(
            "catalog",
            "list",
            "--extensions",
            "--group",
            "third",
            "--extension",
            addition,
        )
        self.assertEqual(out, "third logo 4x1 indexed8 0 bitmap\n")
        _, out, _ = self.run_cli(
            "catalog", "show", "third/logo", "--extension", addition
        )
        self.assertIn("menu false\n", out)

    def test_compile_and_inspect_with_an_extension(self):
        folder = self.root / "src"
        png = folder / "light" / "extensions" / "third" / "logo.png"
        png.parent.mkdir(parents=True)
        png.write_bytes(rgba_png(4, 1, bytes(range(16))))
        (folder / "theme.toml").write_text(THEME + "[light]\n")
        status, _, err = self.run_cli("check", folder, "--catalog", self.catalog)
        self.assertEqual(status, 1)
        self.assertIn("pass --extension", err)
        addition = self.root / "assets.json"
        addition.write_text(json.dumps(record("third", "logo", 4, 1)) + "\n")
        status, out, err = self.run_cli(
            "compile", folder, "--catalog", self.catalog, "--extension", addition
        )
        self.assertEqual((status, err), (0, ""))
        self.assertIn("1 extension bitmaps", out)
        rvt = self.root / "dist" / "test" / "test.rvt"
        _, out, _ = self.run_cli("inspect", rvt, "--catalog", self.catalog)
        self.assertIn("1 extension bitmaps: 0x", out)
        _, out, _ = self.run_cli(
            "inspect", rvt, "--catalog", self.catalog, "--extension", addition
        )
        self.assertIn("1 extension bitmaps: third/logo 4x1 indexed8", out)
        _, out, _ = self.run_cli(
            "inspect", rvt, "--catalog", self.catalog, "--extension", addition, "--json"
        )
        self.assertEqual(
            json.loads(out)["appearances"]["light"]["extension_bitmaps"][0]["palette"],
            4,
        )


class PageTests(unittest.TestCase):
    def test_page_is_the_generator_output(self):
        page = ROOT / "docs" / "extension-bitmaps.md"
        self.assertEqual(page.read_text(), extension_bitmaps_doc.current())

    def test_vendored_catalog_is_the_converter_output(self):
        source = Path(str(assets.CATALOG))
        self.assertEqual(source.read_text(), extensions_catalog.convert(source))
        with tempfile.TemporaryDirectory() as name:
            unsorted = Path(name) / "assets.json"
            unsorted.write_text(
                json.dumps(record("z", "a", 1, 1))
                + "\n"
                + json.dumps(record("a", "b", 1, 1))
                + "\n"
                + json.dumps(record("a", "a", 1, 1))
                + "\n"
            )
            out = Path(name) / "extensions.json"
            with contextlib.redirect_stdout(io.StringIO()):
                extensions_catalog.main([str(unsorted), "--out", str(out)])
            self.assertEqual(
                [json.loads(line)["asset"] for line in out.read_text().splitlines()],
                ["a", "b", "a"],
            )
            unsorted.write_text((json.dumps(record("a", "a", 1, 1)) + "\n") * 2)
            with self.assertRaisesRegex(ValueError, "a/a is listed twice"):
                extensions_catalog.convert(unsorted)

    def test_page_rows(self):
        text = extension_bitmaps_doc.page(
            {
                ("third", "logo"): record("third", "logo", 4, 1, colors=3),
                ("revola", "extensions"): record("revola", "extensions", 78, 121, True),
            }
        )
        self.assertIn("| `revola` | `extensions` | 78x121 | mask8 | - | yes |", text)
        self.assertIn("| `third` | `logo` | 4x1 | indexed8 | 3 | no |", text)
        self.assertLess(text.index("`revola`"), text.index("`third`"))
        with tempfile.TemporaryDirectory() as name:
            out = Path(name) / "page.md"
            with contextlib.redirect_stdout(io.StringIO()):
                extension_bitmaps_doc.main(["--out", str(out)])
            self.assertEqual(out.read_text(), extension_bitmaps_doc.current())


if __name__ == "__main__":
    unittest.main()
