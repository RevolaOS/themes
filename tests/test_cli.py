# SPDX-License-Identifier: GPL-3.0-only
"""rvt new, check, compile --strict, catalog, and report determinism."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import fixtures
from fixtures import rgba_png

from rvt import cli

THEME = 'schema = 1\nid = "test"\nname = "Test"\n'


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

    def theme(self, toml=THEME, **files):
        folder = self.root / "src"
        folder.mkdir(exist_ok=True)
        (folder / "theme.toml").write_text(toml)
        for path, content in files.items():
            target = folder / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return folder

    def test_new_writes_a_compilable_folder(self):
        status, out, _ = self.run_cli("new", "mine", "--name", "Mine")
        self.assertEqual(status, 0)
        self.assertIn("Wrote mine/theme.toml", out)
        for appearance in ("light", "dark"):
            for sub in ("apple", "revola", "extensions"):
                self.assertTrue((self.root / "mine" / appearance / sub).is_dir())
        status, out, _ = self.run_cli("check", "mine", "--catalog", self.catalog)
        self.assertEqual(status, 0)
        self.assertIn("mine.rvt:", out)
        status, _, err = self.run_cli("new", "mine")
        self.assertEqual((status, err), (1, "mine exists\n"))
        status, _, err = self.run_cli("new", "classic")
        self.assertIn("reserved", err)
        status, _, err = self.run_cli("new", "Bad")
        self.assertIn("id: expected", err)

    def test_check_prints_warnings_and_sizes_without_writing(self):
        rainbow = rgba_png(4, 1, bytes(range(16)))
        folder = self.theme(THEME + "[light]\n", **{"light/apple/Alpha.png": rainbow})
        status, out, err = self.run_cli("check", folder, "--catalog", self.catalog)
        self.assertEqual(status, 0)
        self.assertIn(
            "warning: light/apple/Alpha.png: 4 colours reduced to the 2 of its palette",
            err,
        )
        self.assertIn("light: 1 bitmaps (1 pixels, 0 derived)", out)
        self.assertFalse((self.root / "dist").exists())
        status, _, err = self.run_cli(
            "check", folder, "--catalog", self.catalog, "--strict"
        )
        self.assertEqual(status, 1)
        self.assertIn("1 warnings with --strict", err)
        status, out, err = self.run_cli(
            "compile", folder, "--catalog", self.catalog, "--strict"
        )
        self.assertEqual(status, 1)
        self.assertFalse((self.root / "dist").exists())
        status, out, err = self.run_cli("compile", folder, "--catalog", self.catalog)
        self.assertEqual(status, 0)
        self.assertIn("reduced", err)
        report = json.loads((self.root / "dist/test/report.json").read_text())
        self.assertEqual(
            report["appearances"]["light"]["palette_reduced"],
            [{"name": "Alpha", "colors": 4, "palette": 2}],
        )

    def test_report_and_file_are_deterministic(self):
        folder = self.theme(
            THEME + '[light.tint]\ntext = ["Delta"]\n[dark]\n',
            **{"light/apple/Alpha.png": rgba_png(4, 1, bytes(16))},
        )
        outputs = []
        for out in ("one", "two"):
            self.run_cli("compile", folder, "--catalog", self.catalog, "--out", out)
            outputs.append(
                (
                    (self.root / out / "test/test.rvt").read_bytes(),
                    (self.root / out / "test/report.json").read_text(),
                )
            )
        self.assertEqual(outputs[0], outputs[1])
        report = json.loads(outputs[0][1])
        self.assertEqual(
            sorted(report["appearances"]["light"]),
            [
                "accents_builtin",
                "bytes",
                "contrast",
                "extension_bitmaps",
                "extension_tinted",
                "palette_reduced",
                "records",
            ],
        )

    def test_catalog_list_and_show(self):
        status, out, _ = self.run_cli("catalog", "list", "--catalog", self.catalog)
        self.assertEqual(status, 0)
        self.assertEqual(out.splitlines()[0], "Alpha 4x1 indexed8 2 tintable")
        self.assertEqual(len(out.splitlines()), 11)
        _, out, _ = self.run_cli(
            "catalog", "list", "--catalog", self.catalog, "--group", "Z"
        )
        self.assertEqual(out, "Zeta 4x1 rgb565 0 untintable\n")
        _, out, _ = self.run_cli(
            "catalog", "list", "--catalog", self.catalog, "--format", "mask4"
        )
        self.assertEqual(out, "Epsilon 4x1 mask4 0 tintable\n")
        status, _, err = self.run_cli(
            "catalog", "list", "--catalog", self.catalog, "--format", "gif"
        )
        self.assertEqual(status, 1)
        _, out, _ = self.run_cli("catalog", "show", "Iota", "--catalog", self.catalog)
        self.assertIn("index 8\nid 0x90\nname Iota\n", out)
        self.assertIn("format 0x65\n", out)
        self.assertIn("format_name indexed16", out)
        _, out, _ = self.run_cli("catalog", "show", "0x90", "--catalog", self.catalog)
        self.assertIn("name Iota", out)
        status, _, err = self.run_cli(
            "catalog", "show", "Nope", "--catalog", self.catalog
        )
        self.assertEqual(status, 1)
        self.assertIn("not a catalog bitmap name", err)


if __name__ == "__main__":
    unittest.main()
