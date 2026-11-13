#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Draw Classic dark's Now Playing idle battery, the eight 72x40
``NowPlaying_Idle_Battery_<n>_Image`` PNGs, pixel-aligned in the bitmaps'
own palettes: frames 1..7 in two colours (the battery and its fill in one,
the page in the other), frame 0 with a red sliver as a third.

    python3 themes/classic/batteries.py [--preview DIR]

--preview writes each frame scaled up under DIR.
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from rvt import bitmaps  # noqa: E402

WIDTH, HEIGHT = 72, 40
SCALE = 8

PAGE = (255, 255, 255, 255)  # the idle screen keeps its white page in every look
BODY = (18, 18, 18, 255)
LOW = (255, 2, 2, 255)

# Rounded rectangles as (left, top, right, bottom, radius), edges inclusive.
OUTER = (0, 0, 64, 39, 9)
INNER = (2, 2, 62, 37, 7)  # the page inside the 2 px outline
FILL = (4, 4, 60, 35, 5)  # the fill's full extent at level 7
NUB = (62, 13, 69, 26, 2)  # starts under the outline, so only its right end is rounded
LEVELS = 7
LOW_WIDTH = 4


def inside(x, y, box):
    """Whether pixel (x, y) lies in the rounded rectangle, by its centre."""
    left, top, right, bottom, radius = box
    if not (left <= x <= right and top <= y <= bottom):
        return False
    cx = min(max(x + 0.5, left + radius), right + 1 - radius)
    cy = min(max(y + 0.5, top + radius), bottom + 1 - radius)
    return (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= radius * radius


def fill_right(level):
    """The last fill column at a level, 1..7; level 7 reaches FILL's right."""
    left, _, right, _, _ = FILL
    return left + round((right - left + 1) * level / LEVELS) - 1


def frame(level):
    """RGBA bytes of one frame; level 0 draws the red sliver."""
    right = fill_right(level) if level else FILL[0] + LOW_WIDTH - 1
    fill = LOW if level == 0 else BODY
    out = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if inside(x, y, FILL) and x <= right:
                out += bytes(fill)
            elif inside(x, y, NUB) or (inside(x, y, OUTER) and not inside(x, y, INNER)):
                out += bytes(BODY)
            else:
                out += bytes(PAGE)
    return bytes(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--preview", type=Path, help="write scaled PNGs here")
    args = parser.parse_args(argv)
    if args.preview:
        args.preview.mkdir(parents=True, exist_ok=True)
    for level in range(LEVELS + 1):
        path = HERE / "dark" / "apple" / f"NowPlaying_Idle_Battery_{level}_Image.png"
        path.write_bytes(bitmaps.write_png(WIDTH, HEIGHT, frame(level)))
        print(f"{path.name}: fill to column {fill_right(level) if level else '-'}")
        if args.preview:
            subprocess.run(
                [
                    "magick",
                    str(path),
                    "-filter",
                    "point",
                    "-resize",
                    f"{SCALE * 100}%",
                    str(args.preview / f"{path.stem}-after.png"),
                ],
                check=True,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
