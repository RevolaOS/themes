#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Snap Classic's own PNG, the background, to the palette of the bitmap it
replaces, with the compiler's palette fitting, so the committed art is what the iPod shows and the compiler has
nothing to reduce.

    python3 themes/classic/fit.py [--preview DIR]

--preview writes each PNG before and after, scaled up, under DIR.
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from rvt import bitmaps, catalog  # noqa: E402

SCALE = 8


def fit(path: Path, entry: dict) -> tuple[int, int]:
    """Rewrite the PNG with at most the bitmap's palette entries; returns the
    colour counts before and after."""
    width, height, rgba = bitmaps.read_png(path.read_bytes())
    before = bitmaps.distinct(rgba)
    capacity = entry["palette_colors"]
    if capacity and before > capacity:
        rgba = bitmaps.fit_palette(rgba, capacity)
        path.write_bytes(bitmaps.write_png(width, height, rgba))
    return before, bitmaps.distinct(rgba)


def preview(path: Path, folder: Path, suffix: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "magick",
            str(path),
            "-filter",
            "point",
            "-resize",
            f"{SCALE * 100}%",
            str(folder / f"{path.stem}-{suffix}.png"),
        ],
        check=True,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--preview", type=Path, help="write before/after PNGs here")
    args = parser.parse_args(argv)
    entries = catalog.load(None)
    for path in sorted((HERE / "dark" / "apple").glob("*.png")):
        entry = entries.assets[entries.resolve(path.stem, path.name)]
        if args.preview:
            preview(path, args.preview, "before")
        before, after = fit(path, entry)
        if args.preview:
            preview(path, args.preview, "after")
        print(
            f"{path.name}: {before} -> {after} colours (palette {entry['palette_colors']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
