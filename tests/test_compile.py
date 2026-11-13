# SPDX-License-Identifier: GPL-3.0-only
"""Compiling theme folders, the inspector and the rejection cases."""

import contextlib
import io
import json
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

import fixtures
from fixtures import rgba_png

from rvt import cli, inspector, lz, rvtfile, style
from rvt.compiler import compile_theme, write

THEME = 'schema = 1\nid = "test"\nname = "Test"\n'


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "src"
        self.root.mkdir()
        self.catalog = fixtures.catalog()
        rgba = bytes([10, 20, 30, 50, 40, 50, 60, 70]) * 2
        self.art = {
            "alpha": rgba_png(4, 1, rgba),
            "beta": rgba_png(3, 1, bytes(range(12))),
            # Coverage art: an alpha ramp over a colour, and an opaque gray ramp.
            "alpha-ramp": rgba_png(
                4, 1, b"".join(bytes((200, 10, 10, a)) for a in (0, 85, 170, 255))
            ),
            "gray-ramp": rgba_png(
                4, 1, b"".join(bytes((v, v, v, 255)) for v in (0, 86, 170, 255))
            ),
            "alpha-ramp3": rgba_png(
                3, 1, b"".join(bytes((200, 10, 10, a)) for a in (0, 128, 255))
            ),
            "color": rgba_png(4, 1, bytes([200, 10, 10, 255]) * 4),
            "rgb": rgba_png(4, 1, bytes([255, 0, 0, 255, 0, 255, 0, 255]) * 2),
        }

    def tearDown(self):
        self.directory.cleanup()

    def theme(self, toml=THEME, **files):
        """Write theme.toml and art given as "light/apple/Alpha" -> fixture name."""
        (self.root / "theme.toml").write_text(toml)
        for appearance in ("light", "dark"):
            if (self.root / appearance).is_dir():
                shutil.rmtree(self.root / appearance)
        for path, art in files.items():
            if path.endswith(".toml"):
                target = self.root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(art)
                continue
            target = self.root / f"{path}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.art[art])
        return self.root

    def compile(self, toml=THEME, catalog=None, **files):
        self.theme(toml, **files)
        self.build = compile_theme(catalog or self.catalog, self.root)
        return self.build.data, self.build.report

    def rejects(self, pattern, toml=THEME, catalog=None, **files):
        with self.assertRaisesRegex(ValueError, pattern):
            self.compile(toml, catalog, **files)

    def test_mask_paletted_and_rgb565_records(self):
        toml = (
            THEME
            + '[light.colors]\nicon_tint = "#112233"\n[light.tint]\nicon_tint = ["Delta"]\n[dark]\n'
        )
        data, report = self.compile(
            toml,
            **{
                "light/apple/Alpha": "alpha",
                "light/apple/Delta": "gray-ramp",
                "light/apple/Zeta": "rgb",
            },
        )
        result = inspector.inspect(data, self.catalog)
        self.assertEqual(sorted(result["appearances"]), ["dark", "light"])
        light = result["appearances"]["light"]
        self.assertEqual([r["index"] for r in light["records"]], [0, 3, 5])
        self.assertEqual(
            light["tinted"],
            {3: {"name": "Delta", "role": "icon_tint", "coverage": "alpha"}},
        )
        self.assertEqual(light["colors"]["icon_tint"], "#112233")
        body, count, bitmap_count = rvtfile.decode_file(data)["packs"]["light"]
        self.assertEqual((count, bitmap_count), (3, 0))
        at = style.STYLE_BYTES
        self.assertEqual(rvtfile.RECORD.unpack_from(body, at), (0, 0, 12))
        at += 12
        self.assertEqual(
            body[at : at + 12], bytes([30, 20, 10, 50, 60, 50, 40, 70, 0, 1, 0, 1])
        )
        at += 12
        self.assertEqual(rvtfile.RECORD.unpack_from(body, at), (3, 0, 4))
        at += 12
        self.assertEqual(body[at : at + 4], bytes([0, 86, 170, 255]))
        at += 4
        # Two repeated words compress to 7 bytes, so Zeta is an lz record.
        self.assertEqual(rvtfile.RECORD.unpack_from(body, at), (5, 5, 7))
        at += 12
        words = struct.pack("<4H", 0xF800, 0x07E0, 0xF800, 0x07E0)
        self.assertEqual(lz.lz_decode(body[at : at + 7], 8), words)
        self.assertEqual(light["records"][2]["payload"], words)
        self.assertEqual(light["records"][2]["bytes"], 7)
        self.assertEqual(len(body), at + 8)
        self.assertEqual(
            report["appearances"]["light"]["records"], {"pixels": 2, "pixels_lz": 1}
        )
        self.assertEqual(report["appearances"]["light"]["bytes"], len(body))
        dark = result["appearances"]["dark"]
        self.assertEqual(dark["colors"], style.COLOR_DEFAULTS["dark"])
        self.assertEqual(
            (dark["records"], dark["tinted"], dark["rendering"]), ([], {}, 0)
        )
        self.assertEqual(sorted(report), ["appearances", "id", "name"])
        self.assertEqual(
            sorted(report["appearances"]["light"]),
            [
                "accents_builtin",
                "bytes",
                "contrast",
                "extension_bitmaps",
                "palette_reduced",
                "records",
            ],
        )
        self.assertEqual(len(report["appearances"]["light"]["accents_builtin"]), 9)
        self.assertTrue(report["appearances"]["light"]["contrast"])

    def test_tinted_palette_and_bgra_art_and_palette_reduction(self):
        toml = (
            THEME
            + '[dark.colors]\nicon_tint = "#112233"\n[dark.tint]\nicon_tint = ["Alpha"]\nselection = ["0x20"]\ntext = ["Epsilon"]\n'
        )
        data, _ = self.compile(
            toml,
            **{
                "dark/apple/Alpha": "alpha-ramp",
                "dark/apple/0x20": "alpha-ramp3",
                "dark/apple/Epsilon": "alpha-ramp",
            },
        )
        pack = inspector.inspect(data, self.catalog)["appearances"]["dark"]
        self.assertEqual(
            {i: t["role"] for i, t in pack["tinted"].items()},
            {0: "icon_tint", 1: "selection", 4: "text"},
        )
        payloads = {r["name"]: r["payload"] for r in pack["records"]}
        # Paletted: transparent reserved, then the tint with the mean coverage
        # of the levels the palette cannot hold.
        self.assertEqual(
            payloads["Alpha"][:8], bytes([0, 0, 0, 0, 0x33, 0x22, 0x11, 170])
        )
        self.assertEqual(
            payloads["Beta"],
            bytes([0, 0, 0, 0, 0x33, 0x22, 0x11, 128, 0x33, 0x22, 0x11, 255]),
        )
        self.assertEqual(payloads["Epsilon"], bytes([0x05, 0xAF]))  # 4-bit gray steps
        self.assertEqual(
            self.build.warnings,
            ["dark/apple/Alpha.png: 4 colours reduced to the 2 of its palette"],
        )
        self.assertEqual(
            self.build.report["appearances"]["dark"]["palette_reduced"],
            [{"name": "Alpha", "colors": 4, "palette": 2}],
        )
        # A tinted mask without art sets the role and writes no record.
        data, _ = self.compile(THEME + '[light.tint]\nicon_tint = ["Delta"]\n')
        pack = inspector.inspect(data, self.catalog)["appearances"]["light"]
        self.assertEqual((list(pack["tinted"]), pack["records"]), ([3], []))

    def test_output_is_deterministic_and_accepted_without_catalog(self):
        first, _ = self.compile(THEME + "[light]\n", **{"light/apple/Alpha": "alpha"})
        second, _ = self.compile(THEME + "[light]\n", **{"light/apple/Alpha": "alpha"})
        self.assertEqual(first, second)
        self.assertEqual(inspector.inspect(first)["id"], "test")
        self.assertEqual(self.build.warnings, [])

    def test_style_tables(self):
        toml = THEME + (
            '[dark.colors]\naccent_fill = "#ABCDEF"\n'
            '[dark.accents.teal]\nselection = "#006666"\n'
            "[dark]\nmenu_covers_default = false\n"
            "[dark.rendering]\nflat_selection = true\nflat_now_playing = true\n"
        )
        data, report = self.compile(toml)
        pack = inspector.inspect(data, self.catalog)["appearances"]["dark"]
        self.assertEqual(pack["colors"]["accent_fill"], "#abcdef")
        self.assertEqual(pack["rendering"], 7)
        self.assertEqual(pack["accents"]["teal"]["selection"], "#006666")
        self.assertEqual(pack["accents"]["teal"]["on_accent"], "#ffffff")
        self.assertEqual(pack["colors"]["icon_tint"], "#00a1ff")
        builtin = report["appearances"]["dark"]["accents_builtin"]
        self.assertNotIn("teal", builtin)
        self.assertIn("yellow", builtin)

    def test_invalid_toml_and_art_are_rejected(self):
        cases = {
            "schema: unsupported schema 2": THEME.replace("schema = 1", "schema = 2"),
            r"^id: expected": THEME.replace('"test"', '"Test"'),
            "reserved for the built-in theme": THEME.replace('"test"', '"classic"')
            + "[light]\n",
            "exceeds 47": THEME.replace('"Test"', '"' + "x" * 48 + '"'),
            r"declare \[light\]": THEME,
            "extra: unknown key": THEME + "extra = 1\n[light]\n",
            "fonts: unsupported capability": THEME + "[light.fonts]\n",
            "light.colours: unknown key": THEME + "[light.colours]\n",
            "light.colors.accent: unknown key": THEME
            + '[light.colors]\naccent = "#000000"\n',
            'light.colors.text: expected "#rrggbb"': THEME
            + '[light.colors]\ntext = "#fff"\n',
            "light.accents.cyan: unknown key": THEME + "[light.accents.cyan]\n",
            "light.rendering.selection: unknown key": THEME
            + '[light.rendering]\nselection = "rounded"\n',
            "light.menu_covers_default: expected true or false": THEME
            + '[light]\nmenu_covers_default = "on"\n',
            "light.tint.well: expected one of": THEME
            + '[light.tint]\nwell = ["Delta"]\n',
            "Zeta cannot be tinted": THEME + '[light.tint]\ntext = ["Zeta"]\n',
            "light.tint.text: Delta is already tinted text": THEME
            + '[light.tint]\ntext = ["Delta", "0x40"]\n',
            "invalid TOML": THEME + "[light]\n[light]\n",
            "author: expected a non-empty string": THEME + 'author = ""\n[light]\n',
        }
        for pattern, toml in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, toml)
        light = THEME + "[light]\n"
        self.rejects(
            "light/apple/Nope.png: 'Nope' is not a catalog bitmap name",
            light,
            **{"light/apple/Nope": "alpha"},
        )
        self.rejects(
            "duplicate replacement for Alpha",
            light,
            **{"light/apple/Alpha": "alpha", "light/apple/0x10": "alpha"},
        )
        self.rejects(
            "light/apple/Alpha.png: expected 4x1, got 3x1",
            light,
            **{"light/apple/Alpha": "beta"},
        )
        self.rejects(
            "light/apple/Zeta.png: native RGB565 requires opaque",
            light,
            **{"light/apple/Zeta": "alpha-ramp"},
        )
        self.rejects(
            "ambiguous",
            light,
            fixtures.catalog(duplicate_name=True),
            **{"light/apple/Beta": "beta"},
        )
        self.rejects(
            "grayscale or carry alpha coverage",
            light + '[light.tint]\nicon_tint = ["Delta"]\n',
            **{"light/apple/Delta": "color"},
        )
        self.rejects(
            r"dark: has art but theme.toml declares no \[dark\]",
            light,
            **{"dark/apple/Alpha": "alpha"},
        )
        # An empty folder, as `rvt new` leaves one, is not art.
        self.theme(light)
        (self.root / "dark" / "apple").mkdir(parents=True)
        (self.root / "dark" / "extensions").mkdir()
        compile_theme(self.catalog, self.root)

        def rejects_file(pattern, prepare):
            self.theme(light)
            (self.root / "light" / "apple").mkdir(parents=True)
            prepare(self.root / "light" / "apple")
            with self.assertRaisesRegex(ValueError, pattern):
                compile_theme(self.catalog, self.root)

        outside = self.root.parent / "Alpha.png"
        outside.write_bytes(self.art["alpha"])
        rejects_file(
            "light/apple/notes.txt: expected <CatalogName>.png",
            lambda folder: (folder / "notes.txt").write_text("x"),
        )
        rejects_file(
            "light/apple/Alpha.png: must be a file inside the theme folder",
            lambda folder: (folder / "Alpha.png").symlink_to(outside),
        )
        rejects_file(
            "light/apple/Alpha.png: must be a file inside the theme folder",
            lambda folder: (folder / "Alpha.png").mkdir(),
        )

    def test_reserved_id_with_permission_carries_art_only(self):
        classic = THEME.replace('"test"', '"classic"')
        self.theme(classic + "[dark]\n")
        build = compile_theme(self.catalog, self.root, allow_reserved=True)
        self.assertEqual(inspector.inspect(build.data, self.catalog)["id"], "classic")
        for table in (
            "[dark.rendering]\nflat_icons = true\n",
            "[dark]\nmenu_covers_default = false\n",
            '[dark.tint]\ntext = ["Delta"]\n',
        ):
            self.theme(classic + table)
            with self.assertRaisesRegex(ValueError, "dark: the built-in theme carries"):
                compile_theme(self.catalog, self.root, allow_reserved=True)

    def test_inspector_checks_packs_against_the_catalog(self):
        data, _ = self.compile(
            THEME + "[light]\n", **{"light/apple/Delta": "gray-ramp"}
        )
        header = rvtfile.decode_file(data)
        body, count, _ = header["packs"]["light"]

        def rebuilt(body, count=count, fingerprint=header["fingerprint"]):
            return rvtfile.encode_file(
                fingerprint, "test", "Test", {"light": (bytes(body), count, 0)}
            )

        def tinted(index, value=1):
            data = bytearray(body)
            data[style.TINT_OFFSET + index] = value
            return rebuilt(data)

        cases = {
            "no palette or coverage": tinted(5),
            "Epsilon has unknown record kind 0x7": rebuilt(
                body[: style.STYLE_BYTES]
                + rvtfile.RECORD.pack(4, 7, 4)
                + body[style.STYLE_BYTES + 12 :]
            ),
            "outside the catalog": tinted(11),
            "catalog fingerprint": rebuilt(body, fingerprint=bytes(8)),
            "truncated record header": rebuilt(body[: style.STYLE_BYTES + 4]),
            "trailing bytes": rebuilt(body + bytes(4)),
            "truncated record payload": rebuilt(
                body + rvtfile.RECORD.pack(4, 0, 2), count=2
            ),
            "sorted by unique": rebuilt(body + body[style.STYLE_BYTES :], count=2),
            "catalog index 90 is outside": rebuilt(
                body[: style.STYLE_BYTES]
                + rvtfile.RECORD.pack(90, 0, 4)
                + body[style.STYLE_BYTES + 12 :]
            ),
            "does not match the native bitmap": rebuilt(
                body[: style.STYLE_BYTES]
                + rvtfile.RECORD.pack(3, 0, 5)
                + body[style.STYLE_BYTES + 12 :]
            ),
            "catalog maximum": rebuilt(
                body + bytes(rvtfile.EXTENSION_TABLE_MAX_BYTES + 1024), count=0
            ),
        }
        for pattern, bad in cases.items():
            with self.subTest(pattern), self.assertRaisesRegex(ValueError, pattern):
                inspector.inspect(bad, self.catalog)
        data, _ = self.compile(THEME + "[light]\n", **{"light/apple/Alpha": "alpha"})
        body = bytearray(rvtfile.decode_file(data)["packs"]["light"][0])
        body[-1] = 7
        with self.assertRaisesRegex(ValueError, "invalid palette index"):
            inspector.inspect(rebuilt(body, 1), self.catalog)
        body[-1] = 1
        padded = (
            body[: style.STYLE_BYTES]
            + rvtfile.RECORD.pack(0, 0, 10)
            + body[style.STYLE_BYTES + 12 :]
        )
        with self.assertRaisesRegex(ValueError, "padding must be zero"):
            inspector.inspect(rebuilt(padded, 1))
        payload = bytes(body[style.STYLE_BYTES + 12 :])
        stream = lz.lz_encode(payload + payload)

        def lz_record(stream, size=None):
            return rebuilt(
                body[: style.STYLE_BYTES]
                + rvtfile.RECORD.pack(0, 5, size if size is not None else len(stream))
                + stream
                + bytes(-len(stream) % 4),
                1,
            )

        with self.assertRaisesRegex(ValueError, "Alpha: lz stream continues"):
            inspector.inspect(lz_record(stream), self.catalog)
        with self.assertRaisesRegex(ValueError, "Alpha: lz match outside"):
            inspector.inspect(lz_record(bytes([1, 0, 5, 0])), self.catalog)
        with self.assertRaisesRegex(ValueError, "Alpha: lz stream ends early"):
            inspector.inspect(lz_record(lz.lz_encode(payload)[:-1]), self.catalog)
        with self.assertRaisesRegex(ValueError, "Alpha: lz stream continues"):
            inspector.inspect(lz_record(lz.lz_encode(payload) + b"\0"), self.catalog)
        good = lz_record(lz.lz_encode(payload))
        record = inspector.inspect(good, self.catalog)["appearances"]["light"][
            "records"
        ][0]
        self.assertEqual((record["kind"], record["payload"]), ("pixels_lz", payload))
        # Without a catalog the stream stays as stored.
        record = inspector.inspect(good)["appearances"]["light"]["records"][0]
        self.assertEqual(record["payload"], lz.lz_encode(payload))

    def test_cli_writes_after_validation_and_leaves_failures_untouched(self):
        out = Path(self.directory.name) / "out"
        catalog_path = Path(self.directory.name) / "catalog.json"
        catalog_path.write_text(json.dumps(fixtures.catalog_document()))
        self.theme(THEME + "[light]\n", **{"light/apple/Alpha": "alpha"})
        args = [
            "compile",
            str(self.root),
            "--out",
            str(out),
            "--catalog",
            str(catalog_path),
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(args)
        self.assertEqual(sorted(os.listdir(out / "test")), ["report.json", "test.rvt"])
        before = (out / "test" / "test.rvt").read_bytes()
        report = json.loads((out / "test" / "report.json").read_text())
        self.assertEqual(list(report["appearances"]), ["light"])
        (self.root / "theme.toml").write_text(THEME + "[light.fonts]\n")
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            cli.main(args)
        self.assertEqual((out / "test" / "test.rvt").read_bytes(), before)
        truncated = self.art["alpha"][:-10]
        (self.root / "theme.toml").write_text(THEME + "[light]\n")
        (self.root / "light" / "apple" / "Alpha.png").write_bytes(truncated)
        with (
            self.assertRaises(SystemExit),
            contextlib.redirect_stderr(io.StringIO()) as err,
        ):
            cli.main(args)
        self.assertIn("light/apple/Alpha.png: truncated PNG", err.getvalue())
        (self.root / "light" / "apple" / "Alpha.png").write_bytes(self.art["alpha"])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            cli.main(
                [
                    "inspect",
                    str(out / "test" / "test.rvt"),
                    "--catalog",
                    str(catalog_path),
                ]
            )
        self.assertIn("1 records: 1 pixels; 0 tinted", output.getvalue())
        self.assertIn("0 extension bitmaps", output.getvalue())

    def test_write_returns_the_rvt_path(self):
        self.theme(THEME + "[dark]\n")
        path, build = write(
            self.catalog, self.root, Path(self.directory.name) / "build"
        )
        self.assertEqual(path.name, "test.rvt")
        self.assertEqual(build.report["id"], "test")
        self.assertTrue(path.with_name("report.json").is_file())


if __name__ == "__main__":
    unittest.main()
