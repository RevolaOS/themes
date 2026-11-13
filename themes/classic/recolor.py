#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write Classic dark's generated recolour rule files from the stock colours.

Each bitmap in RULES gets `dark/apple/<Name>.toml` mapping every stock colour
through a tonal curve: two luma anchors joined by a line, clamped between
them, give the output grey; the stock alpha is kept. Colours with a chroma at
or above the rule's threshold (the red of a calendar header, the purple of a
Genius atom) pass through unchanged, so only the greys move. Every colour the
bitmap uses is listed, which is what keeps the iPod's result free of stray
stock pixels; a colour the curve leaves unchanged is left out because the
format forbids identity pairs. RGB565 targets lose the low bits the format
drops. The remaining .toml files in dark/apple/ are hand-written.

    python3 themes/classic/recolor.py --firmware osos.bin [--check]

--check regenerates in memory and reports files that differ, writing nothing.
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from rvt import catalog, derive, firmware  # noqa: E402

# A curve: (stock luma, output grey) at two points; the line through them,
# clamped to the output range. A falling curve inverts a glyph.
SURFACE = ((0x5B, 0x10), (0xFC, 0x2F))  # the recoloured status bar's range
CELL = ((0x90, 0x26), (0xFF, 0x3C))  # a step above the #181818 background
CELL_DIM = ((0x90, 0x20), (0xFF, 0x30))
WELL = ((0x80, 0x3C), (0xFF, 0x6E))  # the Disk Mode empty bar's grey
GLYPH = ((0x00, 0xE8), (0xA0, 0xA0))  # a dark glyph on transparent, inverted
PAGE = ((0x00, 0xD8), (0xFF, 0x2E))  # a dark glyph on an opaque white page
THUMB = ((0x80, 0x80), (0xFF, 0xC8))  # a white thumb that must stay a thumb
TRACK = ((0xAC, 0x33), (0xFC, 0x4A))  # the playing progress track
# The track's translucent rows are its reflection on the floor below; at the
# stock alphas they need a brighter grey than the track to show on dark.
TRACK_REFLECTION = ((0xAC, 0x70), (0xFC, 0x90))
DIM = ((0x80, 0x80), (0xFF, 0xE4))  # light art kept, its white taken off glare
# Relight runs on paletted bitmaps only; the one RGB565 proxy square gets a
# curve that lands on relight's background and icon greys.
SQUARE = ((0xB0, 0x8C), (0xD8, 0x19))

CHROMA = 24  # below this a colour counts as grey; the extension's accent tint agrees
NEUTRAL = 2  # at most this much cast: the battery outline, not its blue-cast body
CAST = 64  # greys with a colour cast still count as grey; saturated dots pass
ALL = 256  # every colour, whatever its chroma
# The status bar battery needs two curves, told apart by colour cast: its
# neutral-grey outline and nub go brighter than the stock #63 so the frame
# shows on the dark bar, its blue-cast empty body goes dark, and the
# translucent white reflection under it is dropped.
BATTERY = object()
BATTERY_OUTLINE = ((0x60, 0x6A), (0xC8, 0x90))
BATTERY_BODY = ((0x54, 0x26), (0xA4, 0x50))

RULES = {
    "Lozenge_Left_White_Image": (SURFACE, CHROMA),
    "Lozenge_Middle_White_Image": (SURFACE, CHROMA),
    "Lozenge_Right_White_Image": (SURFACE, CHROMA),
    "System_Input_Field_Left_Image": (SURFACE, CHROMA),
    "System_Input_Field_Middle_Image": (SURFACE, CHROMA),
    "System_Input_Field_Right_Image": (SURFACE, CHROMA),
    "OptionBar_White_Well_Center_Image": (SURFACE, CHROMA),
    "OptionBar_White_Well_LeftCap_Image": (SURFACE, CHROMA),
    "OptionBar_White_Well_RightCap_Image": (SURFACE, CHROMA),
    "OptionBar_NowPlaying_Well_Center_Image": (SURFACE, CHROMA),
    "OptionBar_NowPlaying_Well_LeftCap_Image": (SURFACE, CHROMA),
    "OptionBar_NowPlaying_Well_RightCap_Image": (SURFACE, CHROMA),
    "WorldClock_Graybar_Image": (SURFACE, CHROMA),
    "Calendar_Active_Cell": (CELL, ALL),
    "Calendar_Inactive_Cell": (CELL_DIM, ALL),
    "Settings_DateTime_Calendar_Image": (DIM, 96),
    "Genius_Slider_Image": (CELL, CHROMA),
    "NowPlaying_ProgressBar_Active_Background_Image": (TRACK, CHROMA),
    "CapacityView_Detailed_EmptyCenter_Image": (WELL, CHROMA),
    "CapacityView_Detailed_EmptyLeft_Image": (WELL, CHROMA),
    "CapacityView_Detailed_EmptyRight_Image": (WELL, CHROMA),
    "CapacityView_Detailed_Edge_Image": (WELL, CHROMA),
    "Settings_About_Capacity_Fill_Image": (WELL, CHROMA),
    "Settings_About_Capacity_LeftCap_Image": (WELL, CHROMA),
    "Settings_About_Capacity_RightCap_Image": (WELL, CHROMA),
    **{f"StatusBarWhite_Battery_Image_{i}": (BATTERY, CHROMA) for i in range(23)},
    "StatusBarWhite_Battery_Image_Charge": (GLYPH, CHROMA),
    "StatusBarWhite_Battery_Image_Plug": (GLYPH, CHROMA),
    "Media_VideoStatusIcon_Image": (GLYPH, CHROMA),
    "Podcasts_video_solo_Image": (GLYPH, CHROMA),
    "Media_Genius_Refresh_Image": (GLYPH, CHROMA),
    "Media_Genius_Normal_Image": (GLYPH, CAST),
    "Playlist_Genius_Icon": (GLYPH, CAST),
    "Settings_About_Bubble_Deselected_Image": (GLYPH, CHROMA),
    "Media_OTGPlaylist_Image": (PAGE, CHROMA),
    "No_Content_iTunesU_Small_Image": (SQUARE, ALL),
    "OptionBar_NowPlaying_Thumb_Center_Image": (THUMB, CHROMA),
    "OptionBar_NowPlaying_Thumb_LeftCap_Image": (THUMB, CHROMA),
    "OptionBar_NowPlaying_Thumb_RightCap_Image": (THUMB, CHROMA),
}


def gray(curve, level: int) -> int:
    (x0, y0), (x1, y1) = curve
    value = y0 + (level - x0) * (y1 - y0) / (x1 - x0)
    return round(min(max(value, min(y0, y1)), max(y0, y1)))


def target(color: bytes, curve, chroma: int, rgb565: bool) -> bytes | None:
    """The replacement for one stock colour, or None to leave it alone."""
    red, green, blue, alpha = color
    cast = max(red, green, blue) - min(red, green, blue)
    if alpha == 0 or cast >= chroma:
        return None
    luma = derive.luma(red, green, blue)
    if curve is BATTERY:
        if alpha < 255 and luma > 0xC0:
            return bytes(4)
        curve = BATTERY_OUTLINE if cast <= NEUTRAL else BATTERY_BODY
    elif curve is TRACK and alpha < 255:
        curve = TRACK_REFLECTION
    level = gray(curve, luma)
    out = bytes((level, level, level, alpha))
    if rgb565:
        out = firmware.quantize_565(out)
    return None if out == color else out


def pairs(entries, stock, name: str):
    """The sorted colour pairs of one rule file."""
    index = entries.resolve(name, name)
    info = entries.assets[index]
    curve, chroma = RULES[name]
    rgb565 = derive.is_565(info)
    result = []
    for color in firmware.stock_colors(info, stock.bitmap(index)):
        out = target(color, curve, chroma, rgb565)
        if out is not None:
            result.append((color, out))
    result.sort(key=lambda pair: derive.key(pair[0]))
    derive.check_recolor(result, info, name)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--firmware", type=Path, required=True, help="osos.bin")
    parser.add_argument("--check", action="store_true", help="compare, write nothing")
    args = parser.parse_args(argv)
    entries = catalog.load(None)
    stock = firmware.Firmware(args.firmware, entries)
    stale = []
    for name in sorted(RULES):
        path = HERE / "dark" / "apple" / f"{name}.toml"
        rules = pairs(entries, stock, name)
        text = firmware.recolor_text(rules)
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(path.name)
        else:
            path.write_text(text)
            print(f"{path.name}: {len(rules)} colour pairs")
    for name in stale:
        print(f"{name}: differs from the table", file=sys.stderr)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
