# SPDX-License-Identifier: GPL-3.0-only
"""Every form of theme.toml: accents, rendering, tints and derive rules."""

import re
import shutil
import tempfile
import unittest
from pathlib import Path

import fixtures
from fixtures import rgba_png

from rvt import inspector, rvtfile, theme
from rvt.compiler import compile_theme

THEME = 'schema = 1\nid = "test"\nname = "Test"\n'

ART = rgba_png(4, 2, bytes((10, 10, 10, 255)) * 8)


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "src"
        self.root.mkdir()
        self.catalog = fixtures.catalog()

    def tearDown(self):
        self.directory.cleanup()

    def compile(self, toml, **files):
        (self.root / "theme.toml").write_text(THEME + toml)
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
        return compile_theme(self.catalog, self.root)

    def pack(self, build, appearance="light"):
        return inspector.inspect(build.data, self.catalog)["appearances"][appearance]

    def rejects(self, pattern, toml, **files):
        with self.assertRaisesRegex(ValueError, re.escape(pattern)):
            self.compile(toml, **files)

    # Accents

    def test_accent_forms(self):
        build = self.compile(
            '[light.colors]\non_accent = "#111111"\nselection = "#222222"\n'
            'icon_tint = "#333333"\n'
            "[light.accents]\n"
            'blue = "#007AFF"\n'
            'yellow = { accent = "#ffcc00", on_accent = "#000000" }\n'
            'teal = { accent_fill = "#006666" }\n'
        )
        accents = self.pack(build)["accents"]
        self.assertEqual(
            accents["blue"],
            {
                "accent_fill": "#007aff",
                "accent_text": "#007aff",
                "selection": "#007aff",
                "on_accent": "#111111",
                "icon_tint": "#007aff",
            },
        )
        self.assertEqual(accents["yellow"]["on_accent"], "#000000")
        self.assertEqual(accents["yellow"]["selection"], "#ffcc00")
        # The long form and the built-in accents follow the built-in colours for
        # selection and icon tint; only on_accent is the appearance's own.
        self.assertEqual(accents["teal"]["accent_fill"], "#006666")
        self.assertEqual(accents["teal"]["accent_text"], "#007378")
        self.assertEqual(accents["teal"]["selection"], "#007378")
        self.assertEqual(accents["red"]["accent_fill"], "#d02028")
        self.assertEqual(accents["red"]["selection"], "#d02028")
        self.assertEqual(accents["red"]["on_accent"], "#111111")
        self.assertEqual(accents["red"]["icon_tint"], "#d02028")
        self.assertEqual(
            build.report["appearances"]["light"]["accents_builtin"],
            ["purple", "pink", "red", "orange", "green", "graphite"],
        )

    def test_contrast_warns_once_per_pair_the_theme_colours(self):
        build = self.compile(
            '[light.colors]\ntext = "#777777"\non_accent = "#dddddd"\n'
            '[light.accents]\nblue = "#007aff"\n'
        )
        about_text = [w for w in build.warnings if w.startswith("light: text on")]
        self.assertEqual(len(about_text), 1)
        self.assertIn("with accent Theme Default", about_text[0])
        # on_accent is an accent role, so its pairs are warned about per accent.
        on_accent = [w for w in build.warnings if w.startswith("light: on_accent")]
        accents = {w.split("with accent ")[1].split(";")[0] for w in on_accent}
        self.assertTrue({"Theme Default", "blue"} <= accents)

    def test_accent_rejections(self):
        cases = {
            'light.accents.blue: expected "#rrggbb" or a table': "blue = 1\n",
            "light.accents.blue.accent_fill: unknown key": 'blue = { accent = "#000000", accent_fill = "#000000" }\n',
            'light.accents.blue.accent: expected "#rrggbb"': 'blue = { accent = "blue" }\n',
            "light.accents.blue.fill: unknown key": 'blue = { fill = "#000000" }\n',
            "light.accents.cyan: unknown key": 'cyan = "#000000"\n',
        }
        for pattern, line in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, "[light.accents]\n" + line)

    # Rendering

    def test_rendering_booleans_and_the_menu_covers_default(self):
        build = self.compile(
            "[light]\nmenu_covers_default = false\n"
            "[light.rendering]\nflat_selection = true\nflat_now_playing = true\n"
            "[dark]\nmenu_covers_default = true\n"
        )
        self.assertEqual(self.pack(build)["rendering"], 7)
        self.assertEqual(self.pack(build, "dark")["rendering"], 0)
        cases = {
            "light.menu_covers_default: expected true or false": 'menu_covers_default = "off"\n',
            "light.rendering.flat_selection: expected true or false": "[light.rendering]\nflat_selection = 1\n",
            "light.rendering.covers: unknown key": "[light.rendering]\ncovers = true\n",
            "light.rendering.menu_covers: unknown key": "[light.rendering]\nmenu_covers = true\n",
        }
        for pattern, line in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, "[light]\n" + line)

    # Tints

    def test_grouped_tints_with_globs_and_darkness(self):
        build = self.compile(
            "[light.tint]\n"
            'icon_tint = ["[BET]*", "Alpha", "0xb0"]\n'
            'text = ["Delta", "Nope_*"]\n'
            'darkness_coverage = ["Lambda", "[BT]?eta"]\n'
        )
        tinted = self.pack(build)["tinted"]
        self.assertEqual(
            {t["name"]: (t["role"], t["coverage"]) for t in tinted.values()},
            {
                "Alpha": ("icon_tint", "alpha"),
                "Beta": ("icon_tint", "alpha"),
                "Epsilon": ("icon_tint", "alpha"),
                "Eta": ("icon_tint", "alpha"),
                "Theta": ("icon_tint", "darkness"),
                "Lambda": ("icon_tint", "darkness"),
                "Delta": ("text", "alpha"),
            },
        )
        self.assertEqual(
            build.warnings, ["light.tint.text: 'Nope_*' matches no catalog bitmap"]
        )

    def test_tint_rejections(self):
        cases = {
            "light.tint.text: expected a list of catalog names": 'text = "Beta"\n',
            "light.tint.well: expected one of": 'well = ["Alpha"]\n',
            "light.tint.text: Eta is already tinted icon_tint": 'icon_tint = ["Eta"]\ntext = ["[ET]*"]\n',
            "light.tint.darkness_coverage: Alpha has no tint role": 'darkness_coverage = ["Alpha"]\n',
            "light.tint.darkness: expected one of": 'darkness = ["Alpha"]\n',
            "light.tint.icon_tint: 'Nope' is not a catalog bitmap name": 'icon_tint = ["Nope"]\n',
            "light.tint.icon_tint: Zeta cannot be tinted": 'icon_tint = ["Zeta"]\n',
            "light.tint.icon_tint: expected a catalog name": "icon_tint = [1]\n",
        }
        for pattern, lines in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, "[light.tint]\n" + lines)

    def test_icon_tint_follows_accent_text_unless_set(self):
        build = self.compile('[light.colors]\nicon_tint = "#123456"\n')
        self.assertEqual(self.pack(build)["colors"]["icon_tint"], "#123456")
        build = self.compile('[light.colors]\naccent_text = "#654321"\n')
        self.assertEqual(self.pack(build)["colors"]["icon_tint"], "#654321")
        self.rejects("light.icon_tint: unknown key", 'light.icon_tint = "#123456"\n')

    # Derive rules

    def test_glob_rules(self):
        build = self.compile(
            "[light]\n[dark.derive]\n"
            '"*[eE]ta" = { kind = "alias", from_other = true }\n'
            '"Lambda" = { kind = "invert" }\n'
            '"Kappa" = { kind = "alias", source = "Iota" }\n',
            **{
                "light/apple/Beta.png": rgba_png(3, 1, bytes(12)),
                "light/apple/Zeta.png": rgba_png(4, 1, bytes([8, 4, 8, 255]) * 4),
                "light/apple/Eta.png": ART,
                "light/apple/Theta.png": ART,
            },
        )
        records = self.pack(build, "dark")["records"]
        self.assertEqual(
            {
                r["name"]: "pixels" if r["kind"] in rvtfile.PIXEL_KINDS else r["kind"]
                for r in records
            },
            {
                "Beta": "pixels",
                "Zeta": "pixels",
                "Eta": "pixels",
                "Theta": "pixels",
                "Lambda": "invert",
                "Kappa": "alias",
            },
        )
        self.assertEqual(
            sorted(build.resolved["dark"]), ["Beta", "Eta", "Theta", "Zeta"]
        )
        self.assertEqual(
            build.notes,
            [
                "dark.derive.'*[eE]ta' matches 4 bitmaps",
                "dark.derive.'Lambda' matches 1 bitmap",
                "dark.derive.'Kappa' matches 1 bitmap",
            ],
        )
        counts = build.report["appearances"]["dark"]["records"]
        self.assertEqual((counts.get("alias"), counts.get("invert")), (1, 1))
        self.assertEqual(sum(counts.get(k, 0) for k in rvtfile.PIXEL_KINDS), 4)

    def test_rule_rejections(self):
        both = "[light]\n[dark.derive]\n"
        cases = {
            "dark.derive.'Nope_*': matches no catalog bitmap": (
                both + '"Nope_*" = { kind = "invert" }\n',
                {},
            ),
            "dark.derive.'Nope': 'Nope' is not a catalog bitmap name": (
                both + '"Nope" = { kind = "invert" }\n',
                {},
            ),
            "dark.derive.'E*': matches Eta, which has Eta.png": (
                both + '"E*" = { kind = "invert" }\n',
                {"dark/apple/Eta.png": ART},
            ),
            "dark.derive.'Eta': matches Eta, which has Eta.toml": (
                both + '"Eta" = { kind = "invert" }\n',
                {"dark/apple/Eta.toml": 'kind = "invert"\n'},
            ),
            "dark.derive.'*ta': matches Eta, which 'Eta' matches too": (
                both + '"Eta" = { kind = "invert" }\n"*ta" = { kind = "invert" }\n',
                {},
            ),
            "dark.derive.'Eta'.from_other: expected true or false": (
                both + '"Eta" = { kind = "invert", from_other = "light" }\n',
                {},
            ),
            "dark.derive.'Eta': expected a table": (both + '"Eta" = "invert"\n', {}),
            "dark.derive: expected a table of rules": (
                "[light]\n[dark]\nderive = 1\n",
                {},
            ),
            "dark.derive.'Eta'.from_other: Eta has no art in light/apple/": (
                both + '"Eta" = { kind = "invert", from_other = true }\n',
                {},
            ),
            "dark.derive.'Eta'.from_other: Eta is tinted in light/apple/": (
                both.replace("[light]\n", '[light.tint]\ntext = ["Eta"]\n')
                + '"Eta" = { kind = "alias", from_other = true }\n',
                {"light/apple/Eta.png": ART},
            ),
            "dark.tint.Eta: Eta is derived by dark.derive": (
                '[light]\n[dark.tint]\ntext = ["Eta"]\n[dark.derive]\n'
                '"Eta" = { kind = "invert" }\n',
                {},
            ),
        }
        for pattern, (toml, files) in cases.items():
            with self.subTest(pattern):
                self.rejects(pattern, toml, **files)

    def test_template_compiles(self):
        text = theme.template("mine", "Mine")
        (self.root / "theme.toml").write_text(text)
        build = compile_theme(self.catalog, self.root)
        self.assertEqual(sorted(self.pack(build)), sorted(self.pack(build, "dark")))
        self.assertEqual(build.warnings, [])
        for key in (
            "background",
            "cover_border",
            "icon_tint",
            "flat_selection",
            "menu_covers_default",
            "darkness_coverage",
        ):
            self.assertIn(key, text)
        for appearance in rvtfile.APPEARANCES:
            for table in ("colors", "accents", "rendering", "tint", "derive"):
                self.assertIn(f"[{appearance}.{table}]", text)


if __name__ == "__main__":
    unittest.main()
