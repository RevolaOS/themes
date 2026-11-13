# SPDX-License-Identifier: GPL-3.0-only
"""Derived art: derivation files, record payloads, the reference arithmetic
applied to fixture bitmaps, rules resolved from the other appearance, and the
firmware helpers against a synthetic image."""

import shutil
import struct
import tempfile
import unittest
from pathlib import Path

import fixtures
from fixtures import rgba_png

from rvt import bitmaps, derive, firmware, inspector
from rvt import rvtfile as format
from rvt.compiler import compile_theme

THEME = 'schema = 1\nid = "test"\nname = "Test"\n'

ETA, THETA, IOTA, KAPPA, LAMBDA = 6, 7, 8, 9, 10
NARROW = 'kind = "relight"\nbg_lo = 24\nbg_hi = 26\nicon_lo = 30\nicon_hi = 31\n'


class DeriveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "src"
        self.root.mkdir()
        self.catalog = fixtures.catalog()
        self.image = fixtures.firmware_image()
        self.firmware = firmware.Firmware(self.image_path(), self.catalog)

    def tearDown(self):
        self.directory.cleanup()

    def image_path(self):
        path = Path(self.directory.name) / "osos.bin"
        path.write_bytes(self.image)
        return path

    def theme(self, toml=THEME, **files):
        (self.root / "theme.toml").write_text(toml)
        for appearance in ("light", "dark"):
            if (self.root / appearance).is_dir():
                shutil.rmtree(self.root / appearance)
        for path, content in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content)

    def compile(self, toml=THEME, **files):
        self.theme(toml, **files)
        self.build = compile_theme(self.catalog, self.root)
        return self.build.data, self.build.report

    def rejects(self, pattern, toml=THEME, **files):
        with self.assertRaisesRegex(ValueError, pattern):
            self.compile(toml, **files)

    def records(self, data, appearance="dark"):
        return inspector.inspect(data, self.catalog)["appearances"][appearance][
            "records"
        ]

    def stock(self, index):
        return fixtures.BITMAPS[index]

    # Files and payloads

    def test_recolor_file_sorts_pairs_and_encodes_them(self):
        toml = 'kind = "recolor"\n[map]\n"#000000ff" = "#ffffffff"\n"#ffffffff" = "#000000ff"\n'
        data, _ = self.compile(THEME + "[dark]\n", **{"dark/apple/Eta.toml": toml})
        (record,) = self.records(data)
        self.assertEqual(record["kind"], "recolor")
        self.assertEqual(
            record["spec"],
            [
                (b"\0\0\0\xff", b"\xff\xff\xff\xff"),
                (b"\xff\xff\xff\xff", b"\0\0\0\xff"),
            ],
        )
        body = format.decode_file(data)["packs"]["dark"][0]
        at = format.STYLE_BYTES
        self.assertEqual(format.RECORD.unpack_from(body, at), (ETA, 1, 4 + 16))
        self.assertEqual(body[at + 12 : at + 16], struct.pack("<I", 2))

    def test_recolor_rejections(self):
        cases = {
            "expected kind = 'recolor'": 'kind = "paint"\n',
            "dark/apple/Eta.toml.from: unknown key": 'kind = "recolor"\nfrom = "x"\n[map]\n"#000000ff" = "#ffffffff"\n',
            'expected "#rrggbbaa"': 'kind = "recolor"\n[map]\n"#000000" = "#ffffffff"\n',
            "maps a colour to itself": 'kind = "recolor"\n[map]\n"#000000ff" = "#000000ff"\n',
            "is a mask": None,
            "more colour pairs than Eta has entries": 'kind = "recolor"\n[map]\n'
            + "".join(f'"#0000{i:02x}ff" = "#ffffffff"\n' for i in range(6)),
        }
        for pattern, toml in cases.items():
            with self.subTest(pattern):
                if toml is None:
                    self.rejects(
                        pattern,
                        THEME + "[dark]\n",
                        **{
                            "dark/apple/Delta.toml": 'kind = "recolor"\n[map]\n"#000000ff" = "#ffffffff"\n'
                        },
                    )
                else:
                    self.rejects(
                        pattern, THEME + "[dark]\n", **{"dark/apple/Eta.toml": toml}
                    )
        self.rejects(
            "RGB565 needs opaque colours",
            THEME + "[dark]\n",
            **{
                "dark/apple/Kappa.toml": 'kind = "recolor"\n[map]\n"#ffffffff" = "#182029ff"\n'
            },
        )
        self.rejects(
            "duplicate replacement for Eta",
            THEME + "[dark]\n",
            **{
                "dark/apple/Eta.toml": 'kind = "invert"\n',
                "dark/apple/Eta.png": rgba_png(4, 2, bytes(32)),
            },
        )

    def test_alias_invert_and_relight_files(self):
        data, report = self.compile(
            THEME + "[dark]\n",
            **{
                "dark/apple/Theta.toml": 'kind = "alias"\nsource = "Eta"\n',
                "dark/apple/Kappa.toml": 'kind = "alias"\nsource = "Iota"\n',
                "dark/apple/Lambda.toml": 'kind = "invert"\n',
                "dark/apple/Iota.toml": NARROW,
            },
        )
        kinds = {r["index"]: r["kind"] for r in self.records(data)}
        self.assertEqual(
            kinds, {THETA: "alias", KAPPA: "alias", LAMBDA: "invert", IOTA: "relight"}
        )
        self.assertEqual(
            report["appearances"]["dark"]["records"],
            {"alias": 2, "invert": 1, "relight": 1},
        )
        body = format.decode_file(data)["packs"]["dark"][0]
        self.assertEqual(
            format.RECORD.unpack_from(body, format.STYLE_BYTES), (THETA, 2, 4)
        )
        self.assertEqual(
            struct.unpack_from("<I", body, format.STYLE_BYTES + 12)[0], ETA
        )
        words = [r for r in self.records(data) if r["kind"] == "relight"][0]["spec"]
        self.assertEqual(words[format.RELIGHT_FIELDS.index("bg_lo")], 24 * 256)
        self.assertEqual(
            words[format.RELIGHT_FIELDS.index("bg_slope")], round(10 / 28 * 256)
        )

    def test_alias_invert_and_relight_rejections(self):
        dark = THEME + "[dark]\n"
        cases = {
            "Eta cannot alias itself without from_other": {
                "dark/apple/Eta.toml": 'kind = "alias"\nsource = "Eta"\n'
            },
            "does not fit": {
                "dark/apple/Eta.toml": 'kind = "alias"\nsource = "Alpha"\n'
            },
            "same size and no mask": {
                "dark/apple/Eta.toml": 'kind = "alias"\nsource = "Delta"\n'
            },
            "dark/apple/Eta.toml.source: Theta is an alias itself": {
                "dark/apple/Eta.toml": 'kind = "alias"\nsource = "Theta"\n',
                "dark/apple/Theta.toml": 'kind = "alias"\nsource = "Eta"\n',
            },
            "dark/apple/Eta.toml.from: unknown key": {
                "dark/apple/Eta.toml": 'kind = "alias"\nfrom = "Theta"\n'
            },
            "Delta is a mask; tint it": {"dark/apple/Delta.toml": 'kind = "invert"\n'},
            "relight needs a paletted bitmap; Beta": {
                "dark/apple/Beta.toml": 'kind = "relight"\n'
            },
            "needs 137 palette entries, Iota has 8": {
                "dark/apple/Iota.toml": 'kind = "relight"\n'
            },
            "expected 0 <= t_zero < t_full <= 255": {
                "dark/apple/Iota.toml": NARROW + "t_zero = 14\n"
            },
            "dark/apple/Iota.toml: expected 0 <= t_zero < t_full": {
                "dark/apple/Iota.toml": NARROW + "t_full = 256\n"
            },
            "dark/apple/Iota.toml.bg_base: expected -1024 to 1024": {
                "dark/apple/Iota.toml": NARROW + "bg_base = 1024.5\n"
            },
            "dark/apple/Iota.toml.icon_luma: expected -255 to 255": {
                "dark/apple/Iota.toml": NARROW + "icon_luma = -256\n"
            },
            "dark/apple/Iota.toml.bg_slope: expected -16 to 16": {
                "dark/apple/Iota.toml": NARROW + "bg_slope = 16.01\n"
            },
            "dark/apple/Iota.toml.t_full: expected a number": {
                "dark/apple/Iota.toml": NARROW + 't_full = "wide"\n'
            },
            "dark/apple/Iota.toml.gain: unknown key": {
                "dark/apple/Iota.toml": NARROW + "gain = 2\n"
            },
        }
        for pattern, files in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, dark, **files)
        self.rejects(
            "dark/apple/Eta.toml.source: Theta is tinted",
            dark + '[dark.tint]\ntext = ["Theta"]\n',
            **{"dark/apple/Eta.toml": 'kind = "alias"\nsource = "Theta"\n'},
        )
        self.rejects(
            "Eta is derived by dark/apple/Eta.toml; a tint",
            dark + '[dark.tint]\ntext = ["Eta"]\n',
            **{"dark/apple/Eta.toml": 'kind = "invert"\n'},
        )
        self.rejects(
            "coverage needs stock art; remove dark/apple/Eta.png",
            dark + '[dark.tint]\ntext = ["Eta"]\ndarkness_coverage = ["Eta"]\n',
            **{"dark/apple/Eta.png": rgba_png(4, 2, bytes(32))},
        )
        edge = NARROW + "bg_base = 1024\nbg_slope = -16\nicon_row = 255\n"
        self.compile(dark, **{"dark/apple/Iota.toml": edge})

    def test_stock_alias_between_layouts_is_capped_like_the_ipod(self):
        document = fixtures.catalog_document()
        document["bitmaps"] += [
            fixtures.entry(
                0xC0,
                0x20000,
                fixtures.bgra_colors((fixtures.WHITE,) * 64 * 64, 64, 64),
                "Mu",
            ),
            fixtures.entry(
                0xD0, 0x30000, fixtures.rgb565_words((0xFFFF,) * 64 * 64, 64, 64), "Nu"
            ),
        ]
        mu, nu = document["bitmaps"][11], document["bitmaps"][12]
        with self.assertRaisesRegex(ValueError, "at most 3840 pixels"):
            derive.check_alias(mu, nu, "x")
        # The compiler does the re-encoding for from_other.
        derive.check_alias(mu, nu, "x", from_other=True)

    def test_stock_coverage_tints_need_no_art(self):
        data, _ = self.compile(
            THEME + '[dark.tint]\ntext = ["Eta"]\naccent_fill = ["Lambda"]\n'
            'darkness_coverage = ["Lambda"]\n'
        )
        tinted = inspector.inspect(data, self.catalog)["appearances"]["dark"]["tinted"]
        self.assertEqual(
            tinted[ETA], {"name": "Eta", "role": "text", "coverage": "alpha"}
        )
        self.assertEqual(tinted[LAMBDA]["coverage"], "darkness")
        self.assertEqual(self.records(data), [])

    # Reference arithmetic on fixture bitmaps

    def test_apply_recolor_swaps_without_chaining(self):
        info = self.catalog.assets[ETA]
        pairs = [
            (bytes(fixtures.BLACK), bytes(fixtures.WHITE)),
            (bytes(fixtures.WHITE), bytes(fixtures.BLACK)),
        ]
        out = derive.apply_recolor(
            info, self.stock(ETA), sorted(pairs, key=lambda p: derive.key(p[0]))
        )
        pixels = bitmaps.decode_pixels(info, out[info["data_offset"] :])
        self.assertEqual(pixels[:4], bytes(fixtures.BLACK))
        self.assertEqual(pixels[12:16], bytes(fixtures.WHITE))
        self.assertEqual(pixels[16:20], bytes((0, 0, 255, 128)))
        kappa = self.catalog.assets[KAPPA]
        out = derive.apply_recolor(
            kappa, self.stock(KAPPA), [(b"\xf8\xfc\xf8\xff", b"\x00\x00\xf8\xff")]
        )
        self.assertEqual(
            struct.unpack_from("<H", out, kappa["pixels_offset"])[0], 0x001F
        )
        self.assertEqual(
            struct.unpack_from("<H", out, kappa["pixels_offset"] + 2)[0], 0
        )

    def test_apply_invert_keeps_alpha_and_clear_pixels(self):
        info = self.catalog.assets[LAMBDA]
        out = derive.apply_invert(info, self.stock(LAMBDA))
        pixels = bitmaps.decode_pixels(info, out[info["data_offset"] :])
        self.assertEqual(pixels[:4], bytes((0, 0, 0, 255)))
        self.assertEqual(pixels[4:8], bytes(4))
        self.assertEqual(pixels[12:16], bytes((245, 235, 225, 200)))
        kappa = self.catalog.assets[KAPPA]
        out = derive.apply_invert(kappa, self.stock(KAPPA))
        self.assertEqual(struct.unpack_from("<H", out, kappa["pixels_offset"])[0], 0)

    def test_apply_relight_rebuilds_the_palette(self):
        info = self.catalog.assets[IOTA]
        words = derive.relight_words(
            {"bg_lo": 24, "bg_hi": 26, "icon_lo": 30, "icon_hi": 31}, "x"
        )
        self.assertEqual(derive.relight_levels(words), 8)
        out = derive.apply_relight(info, self.stock(IOTA), words)
        start = info["data_offset"]
        self.assertEqual(
            out[start : start + 8], bytes((26, 26, 26, 255, 31, 31, 31, 255))
        )
        self.assertEqual(out[start + 8 : start + 32], bytes(24))
        rows = out[info["pixels_offset"] :]
        indices = [
            struct.unpack_from("<H", rows, y * info["stride"] + 2 * x)[0]
            for y in range(3)
            for x in range(4)
        ]
        self.assertEqual(indices, [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
        t = derive.relight_coverage(words, info, self.stock(IOTA))
        self.assertEqual(t[3], 0)  # the shadow touches no icon pixel
        self.assertEqual(t[5], 255)

    def test_apply_alias_copies_or_reencodes(self):
        eta, theta, iota, kappa = (
            self.catalog.assets[i] for i in (ETA, THETA, IOTA, KAPPA)
        )
        out = derive.apply_alias(theta, self.stock(THETA), eta, self.stock(ETA))
        self.assertEqual(
            out[theta["data_offset"] :], self.stock(ETA)[eta["data_offset"] :]
        )
        out = derive.apply_alias(kappa, self.stock(KAPPA), iota, self.stock(IOTA))
        word = struct.unpack_from("<H", out, kappa["pixels_offset"])[0]
        self.assertEqual(bitmaps.unpack_565(word), (240, 244, 240))
        out = derive.apply_alias(eta, self.stock(ETA), theta, self.stock(THETA))
        self.assertEqual(
            out[eta["data_offset"] :], self.stock(THETA)[theta["data_offset"] :]
        )
        crowded = bytearray(self.stock(IOTA))
        crowded[iota["pixels_offset"] + 2 * 11] = 5  # a sixth colour
        with self.assertRaisesRegex(ValueError, "more colours than Mu's palette holds"):
            derive.apply_alias(
                dict(iota, name="Mu", palette_colors=5),
                self.stock(IOTA),
                iota,
                bytes(crowded),
            )

    def test_apply_pack_orders_aliases_last(self):
        records = [
            (THETA, "alias", ETA),
            (ETA, "invert", None),
        ]
        results = derive.apply_pack(self.catalog, self.stock, records)
        self.assertEqual(results[THETA], results[ETA])
        self.assertNotEqual(results[ETA], self.stock(ETA))

    # Rules resolved from the other appearance

    def test_from_other_becomes_pixels_computed_from_the_other_png(self):
        art = rgba_png(4, 2, bytes((10, 20, 30, 255)) * 8)
        data, report = self.compile(
            THEME + "[light]\n[dark]\n",
            **{
                "light/apple/Eta.png": art,
                "dark/apple/Eta.toml": 'kind = "invert"\nfrom_other = true\n',
            },
        )
        result = inspector.inspect(data, self.catalog)
        (light,) = result["appearances"]["light"]["records"]
        (dark,) = result["appearances"]["dark"]["records"]
        self.assertIn(dark["kind"], format.PIXEL_KINDS)
        info = self.catalog.assets[ETA]
        expected = derive.apply_invert(
            info, bytes(info["data_offset"]) + light["payload"]
        )
        self.assertEqual(dark["payload"], expected[info["data_offset"] :])
        self.assertEqual(
            self.build.resolved, {"light": {}, "dark": {"Eta": dark["payload"]}}
        )
        pixels = bitmaps.decode_pixels(info, dark["payload"])
        self.assertEqual(pixels[:4], bytes((245, 235, 225, 255)))
        self.assertEqual(report["appearances"]["dark"]["records"], {dark["kind"]: 1})
        rendered, warnings = firmware.render(self.catalog, self.firmware, data)
        self.assertEqual(warnings, [])
        self.assertEqual(rendered["dark"]["Eta"]["kind"], dark["kind"])

    def test_from_other_alias_copies_or_reencodes(self):
        art = rgba_png(4, 2, bytes((10, 20, 30, 255)) * 8)
        data, _ = self.compile(
            THEME + "[light]\n[dark]\n",
            **{
                "light/apple/Eta.png": art,
                "light/apple/Iota.png": rgba_png(4, 3, bytes((8, 4, 8, 255)) * 12),
                "dark/apple/Eta.toml": 'kind = "alias"\nfrom_other = true\n',
                "dark/apple/Theta.toml": 'kind = "alias"\nsource = "Eta"\nfrom_other = true\n',
                "dark/apple/Kappa.toml": 'kind = "alias"\nsource = "Iota"\nfrom_other = true\n',
            },
        )
        light = {r["name"]: r for r in self.records(data, "light")}
        dark = {r["name"]: r for r in self.records(data)}
        self.assertEqual(dark["Eta"]["payload"], light["Eta"]["payload"])
        self.assertEqual(dark["Theta"]["payload"], light["Eta"]["payload"])
        word = struct.unpack_from("<H", dark["Kappa"]["payload"])[0]
        self.assertEqual(bitmaps.unpack_565(word), (8, 4, 8))
        self.assertEqual(sorted(self.build.resolved["dark"]), ["Eta", "Kappa", "Theta"])

    def test_from_other_rejections(self):
        both = THEME + "[light]\n[dark]\n"
        cases = {
            "Eta is tinted in light/apple/": (
                THEME + '[light.tint]\ntext = ["Eta"]\n[dark]\n',
                {
                    "light/apple/Eta.png": rgba_png(4, 2, bytes((9, 9, 9, 255)) * 8),
                    "dark/apple/Eta.toml": 'kind = "alias"\nfrom_other = true\n',
                },
            ),
            "cannot alias itself without from_other": (
                both,
                {"dark/apple/Eta.toml": 'kind = "alias"\nsource = "Eta"\n'},
            ),
            "dark/apple/Eta.toml.source: expected a catalog name": (
                both,
                {"dark/apple/Eta.toml": 'kind = "alias"\n'},
            ),
            "more colours than Iota's palette holds": (
                both,
                {
                    "light/apple/Kappa.png": rgba_png(
                        4, 3, b"".join(bytes((8 * i, 0, 0, 255)) for i in range(12))
                    ),
                    "dark/apple/Iota.toml": 'kind = "alias"\nsource = "Kappa"\nfrom_other = true\n',
                },
            ),
        }
        for pattern, (toml, files) in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, toml, **files)

    # Firmware helpers

    def test_firmware_checks_and_converts(self):
        self.assertEqual(self.firmware.bitmap(ETA), self.stock(ETA))
        broken = bytearray(self.image)
        broken[self.catalog.assets[ETA]["offset"] + 40] ^= 1
        bad = Path(self.directory.name) / "bad.bin"
        bad.write_bytes(broken)
        with self.assertRaisesRegex(ValueError, "Eta at 0x10600 does not carry"):
            firmware.Firmware(bad, self.catalog).bitmap(ETA)
        info = self.catalog.assets[ETA]
        pairs = [(bytes(fixtures.GRAY), bytes((1, 2, 3, 255)))]
        recoloured = derive.apply_recolor(info, self.stock(ETA), pairs)
        png = bitmaps.write_png(
            4, 2, bitmaps.decode_pixels(info, recoloured[info["data_offset"] :])
        )
        found, notes = firmware.to_recolor(self.catalog, self.firmware, ETA, png)
        self.assertEqual((found, notes), (pairs, []))
        self.assertIn('"#c8c8c8ff" = "#010203ff"', firmware.recolor_text(found))
        mixed = bytearray(
            bitmaps.decode_pixels(info, self.stock(ETA)[info["data_offset"] :])
        )
        mixed[0:4] = bytes((0, 0, 0, 255))  # one of the two white pixels turns black
        with self.assertRaisesRegex(ValueError, "not a pure recolour: 1 stock colours"):
            firmware.to_recolor(
                self.catalog, self.firmware, ETA, bitmaps.write_png(4, 2, bytes(mixed))
            )
        data, _ = self.compile(
            THEME + "[dark]\n",
            **{
                "dark/apple/Eta.toml": 'kind = "recolor"\n[map]\n"#010203ff" = "#ffffffff"\n'
            },
        )
        _, warnings = firmware.render(self.catalog, self.firmware, data)
        self.assertEqual(
            warnings,
            ["dark/apple/Eta.toml: 1 of 1 pairs match no stock colour: #010203ff"],
        )


if __name__ == "__main__":
    unittest.main()
