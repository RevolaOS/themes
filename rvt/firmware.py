# SPDX-License-Identifier: GPL-3.0-only
"""A local firmware image as the source of stock bitmaps: previews of derived
art, and derivation files written from an author's PNG when the PNG is a pure
recolour of the stock bitmap. The compiler and inspector never import this
module."""

import zlib
from collections import defaultdict

from rvt import bitmaps, derive, inspector, rvtfile


class Firmware:
    """Stock bitmaps read at the catalog's offsets; osos.bin or revola.bin."""

    def __init__(self, path, catalog):
        self.data = path.read_bytes()
        self.catalog = catalog
        self.checked = {}

    def bitmap(self, index):
        info = self.catalog.assets[index]
        if index not in self.checked:
            data = self.data[info["offset"] : info["offset"] + info["bytes"]]
            if len(data) != info["bytes"] or zlib.crc32(data) != info["crc32"]:
                raise ValueError(
                    f"firmware: {info['name']} at {info['offset']:#x} does not carry"
                    " the catalog checksum"
                )
            self.checked[index] = data
        return self.checked[index]


def render(catalog, firmware, data):
    """Every record of an .rvt applied to the stock bitmaps, and every tinted
    stock bitmap whose coverage the iPod rewrites (kind `coverage`):
    appearance -> name -> {index, kind, address, bytes, crc32, png}, plus
    warnings about recolour pairs that match no stock colour."""
    result = {}
    warnings = []
    for appearance, pack in inspector.inspect(data, catalog)["appearances"].items():
        records = [
            (
                record["index"],
                record["kind"],
                record["payload"]
                if record["kind"] in rvtfile.PIXEL_KINDS
                else record["spec"],
            )
            for record in pack["records"]
        ]
        derived = derive.apply_pack(catalog, firmware.bitmap, records)
        for index, tint in pack["tinted"].items():
            if index not in derived and tint["coverage"] != "alpha":
                derived[index] = derive.apply_coverage(
                    catalog.assets[index], firmware.bitmap(index), tint["coverage"]
                )
                records.append((index, "coverage", tint["coverage"]))
        result[appearance] = {}
        for index, kind, spec in records:
            info = catalog.assets[index]
            bitmap = derived[index]
            result[appearance][info["name"]] = {
                "index": index,
                "kind": kind,
                "address": info["address"],
                "bytes": info["bytes"],
                "crc32": zlib.crc32(bitmap),
                "png": bitmaps.write_png(
                    info["width"],
                    info["height"],
                    bitmaps.decode_pixels(info, bitmap[info["data_offset"] :]),
                ),
            }
            if kind == "recolor":
                unused = unmatched(info, firmware.bitmap(index), spec)
                if unused:
                    warnings.append(
                        f"{appearance}/apple/{info['name']}.toml: {len(unused)} of "
                        f"{len(spec)} pairs match no stock colour: "
                        + ", ".join(f"#{c.hex()}" for c in unused[:4])
                    )
    return result, warnings


def stock_colors(info, bitmap):
    """The distinct stock colours a recolour can match."""
    pixels = bitmaps.decode_pixels(info, bitmap[info["data_offset"] :])
    if info["palette_colors"]:
        start = info["data_offset"]
        return {
            bytes(
                (
                    bitmap[start + i * 4 + 2],
                    bitmap[start + i * 4 + 1],
                    bitmap[start + i * 4],
                    bitmap[start + i * 4 + 3],
                )
            )
            for i in range(info["palette_colors"])
        }
    return {pixels[i : i + 4] for i in range(0, len(pixels), 4)}


def unmatched(info, bitmap, pairs):
    colors = stock_colors(info, bitmap)
    return [source for source, _ in pairs if source not in colors]


NOISE = 16  # channel levels an editor's dithering may spread one colour over
STRAY_SHARE = 16  # a stray colour covers at most 1/16 of a stock colour's pixels


def quantize_565(color):
    red, green, blue, alpha = color
    return bytes((red & ~7, green & ~3, blue & ~7, alpha))


def distance(first, second):
    """Largest channel difference of two RGBA colours with alpha applied, so
    fully transparent colours are equal whatever their RGB."""

    def visible(color):
        return (*(c * color[3] // 255 for c in color[:3]), color[3])

    return max(abs(a - b) for a, b in zip(visible(first), visible(second)))


def to_recolor(catalog, firmware, index, png):
    """Colour pairs that turn the stock bitmap into the PNG, and notes about
    stray pixels. A stock colour the PNG paints in several colours takes the
    most frequent one when the others are within NOISE of it or cover at most
    1/STRAY_SHARE of its pixels; a wider spread is a ValueError naming the
    colours. Targets of an RGB565 bitmap are rounded to what the format
    stores."""
    info = catalog.assets[index]
    width, height, rgba = bitmaps.read_png(png)
    if (width, height) != (info["width"], info["height"]):
        raise ValueError(
            f"expected {info['width']}x{info['height']}, got {width}x{height}"
        )
    bitmap = firmware.bitmap(index)
    stock = bitmaps.decode_pixels(info, bitmap[info["data_offset"] :])
    targets = defaultdict(lambda: defaultdict(int))
    for i in range(0, len(rgba), 4):
        target = rgba[i : i + 4]
        if derive.is_565(info):
            target = quantize_565(target)
        targets[stock[i : i + 4]][target] += 1
    chosen = {}
    conflicts = []
    notes = []
    for source, counts in targets.items():
        best = max(counts, key=counts.get)
        total = sum(counts.values())
        strays = 0
        for other, count in counts.items():
            if distance(best, other) <= NOISE:
                continue
            if count * STRAY_SHARE <= total:
                strays += count
                continue
            conflicts.append(
                f"#{source.hex()} maps to {len(counts)} colours over {total} pixels"
            )
            break
        if strays:
            notes.append(f"#{source.hex()}: {strays} of {total} pixels ignored")
        chosen[source] = best
    if conflicts:
        raise ValueError(
            f"not a pure recolour: {len(conflicts)} stock colours map to several "
            "colours\n" + "\n".join(sorted(conflicts))
        )
    pairs = sorted(
        ((source, target) for source, target in chosen.items() if source != target),
        key=lambda pair: derive.key(pair[0]),
    )
    derive.check_recolor(pairs, info, info["name"])
    return pairs, notes


def recolor_text(pairs):
    lines = ['kind = "recolor"', "", "[map]"]
    lines += [f'"#{source.hex()}" = "#{target.hex()}"' for source, target in pairs]
    return "\n".join(lines) + "\n"
