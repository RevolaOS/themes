# SPDX-License-Identifier: GPL-3.0-only
"""Derived art: records the iPod computes from the stock bitmaps, so a theme
carries colours and rules instead of pixels.

The authoring side is a rule with a `kind`: one TOML file per bitmap, or a
glob rule in theme.toml. This module parses rules, checks them against the
catalog, encodes and decodes the record payloads, and holds the reference
arithmetic the appearance extension mirrors, applied here to bitmap bytes for
rules the compiler resolves itself (`from_other`), for tests and for previews.
Nothing here reads the firmware; rvt.firmware supplies stock bytes when a
caller has them.
"""

import re
import struct
import tomllib
from dataclasses import dataclass
from pathlib import Path

from rvt import bitmaps, rvtfile
from rvt.catalog import Catalog, Entry, entries
from rvt.errors import fail

RGBA = re.compile(r"#[0-9A-Fa-f]{8}")
KEYS = {
    "recolor": {"kind", "from_other", "map"},
    "alias": {"kind", "from_other", "source"},
    "invert": {"kind", "from_other"},
    "relight": {"kind", "from_other", *rvtfile.RELIGHT_FIELDS},
}
# Classic dark's relight, fitted to its hand-made proxies.
RELIGHT_DEFAULTS = dict(
    zip(
        rvtfile.RELIGHT_FIELDS,
        (3, 14, 25, 216, 10 / 28, 24, 35, 394.6, -1.170, -1.769, 40, 160),
    )
)
ONE = 256  # 8.8 fixed point
FULL = 255  # coverage scale
# The bounds derive.c accepts, in 8.8 units, so the arithmetic cannot overflow.
LEVEL_MAX = 255 * ONE
assert LEVEL_MAX * FULL < 1 << 24  # the per-pixel products stay in 32 bits with room
BASE_MAX = 1024 * ONE
SLOPE_MAX = 16 * ONE
RELIGHT_BOUNDS = {
    "bg_base": BASE_MAX,
    "bg_ref": LEVEL_MAX,
    "bg_slope": SLOPE_MAX,
    "icon_base": BASE_MAX,
    "icon_luma": LEVEL_MAX,
    "icon_row": LEVEL_MAX,
}


@dataclass(frozen=True)
class Rule:
    """A record before it is encoded: the kind, its spec (a pixels payload,
    recolour pairs, an alias source index, None for invert, relight words) and
    whether it starts from the theme's own art in the other appearance."""

    kind: str
    spec: object
    from_other: bool = False


def to_fixed(value, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(where, "expected a number")
    fixed = round(value * ONE)
    if not -(1 << 31) <= fixed < 1 << 31:
        fail(where, "out of range")
    return fixed


def rgba(value, where: str) -> bytes:
    if not isinstance(value, str) or not RGBA.fullmatch(value):
        fail(where, 'expected "#rrggbbaa"')
    return bytes.fromhex(value[1:])


def key(color: bytes) -> int:
    """A colour as the little-endian u32 the records sort by."""
    return int.from_bytes(color, "little")


def is_mask(info: Entry) -> bool:
    return info["format"] in bitmaps.MASK_FORMATS


def is_565(info: Entry) -> bool:
    return info["format"] == bitmaps.RGB565


def same_layout(first: Entry, second: Entry) -> bool:
    return all(
        first[k] == second[k]
        for k in (
            "format",
            "width",
            "height",
            "stride",
            "bytes",
            "data_offset",
            "pixels_offset",
            "palette_colors",
        )
    )


# Parsing and checks


def load(path: Path, index: int, catalog: Catalog, where: str) -> Rule:
    """The rule of a derivation file, see `rule`."""
    try:
        table = tomllib.loads(path.read_bytes().decode("utf-8"))
    except UnicodeDecodeError:
        fail(where, "expected UTF-8")
    except tomllib.TOMLDecodeError as error:
        fail(where, f"invalid TOML: {error}")
    return rule(table, index, catalog, where)


def rule(table: dict, index: int, catalog: Catalog, where: str) -> Rule:
    """The Rule of a rule table: recolor -> sorted colour pairs, alias ->
    source index, invert -> None, relight -> fixed-point words. from_other
    says the rule starts from the theme's own PNG in the other appearance
    instead of the stock bitmap; an alias may then leave `source` out to
    reuse its own art unchanged."""
    if not isinstance(table, dict):
        fail(where, "expected a table")
    kind = table.get("kind")
    if kind not in KEYS:
        fail(where, f"expected kind = {', '.join(repr(k) for k in KEYS)}")
    for name in sorted(table):
        if name not in KEYS[kind]:
            fail(f"{where}.{name}", "unknown key")
    from_other = table.get("from_other", False)
    if not isinstance(from_other, bool):
        fail(f"{where}.from_other", "expected true or false")
    info = catalog.assets[index]
    if kind == "recolor":
        pairs = read_map(table.get("map"), f"{where}.map")
        check_recolor(pairs, info, where)
        return Rule(kind, pairs, from_other)
    if kind == "alias":
        source = table.get("source")
        if source is None and from_other:
            return Rule(kind, index, True)
        if not isinstance(source, str):
            fail(f"{where}.source", "expected a catalog name or hex id")
        found = catalog.resolve(source, f"{where}.source")
        if found != index or not from_other:
            check_alias(info, catalog.assets[found], f"{where}.source", from_other)
        return Rule(kind, found, from_other)
    if kind == "invert":
        check_invert(info, where)
        return Rule(kind, None, from_other)
    words = relight_words(table, where)
    check_relight(words, info, where)
    return Rule(kind, words, from_other)


def read_map(table, where: str) -> list[tuple[bytes, bytes]]:
    if not isinstance(table, dict) or not table:
        fail(where, 'expected a table of "#rrggbbaa" = "#rrggbbaa"')
    pairs = {}
    for source, target in table.items():
        at = f'{where}."{source}"'
        source, target = rgba(source, at), rgba(target, at)
        if source == target:
            fail(at, "maps a colour to itself")
        if source in pairs:
            fail(at, "duplicate colour")
        pairs[source] = target
    return sorted(pairs.items(), key=lambda pair: key(pair[0]))


def check_recolor(pairs: list, info: Entry, where: str) -> None:
    if is_mask(info):
        fail(where, f"{info['name']} is a mask; it has no colours to recolour")
    if len(pairs) > rvtfile.RECOLOR_MAX:
        fail(where, f"more than {rvtfile.RECOLOR_MAX} colour pairs")
    if len(pairs) > entries(info):
        fail(where, f"more colour pairs than {info['name']} has entries")
    if is_565(info):
        for source, target in pairs:
            for color in (source, target):
                if not bitmaps.is_565(color):
                    fail(
                        f'{where}."#{color.hex()}"',
                        "RGB565 needs opaque colours with r and b multiples of 8"
                        " and g a multiple of 4",
                    )


def describe_layout(info: Entry) -> str:
    return f"{info['name']} ({info['format']:#x} {info['width']}x{info['height']})"


def alias_fits(target: Entry, source: Entry) -> bool:
    """Whether source's pixels can become target's: the same size, neither a
    mask. Equal layouts are copied byte for byte; otherwise the pixels are
    re-encoded, and a paletted target must hold the source's distinct colours,
    which only the iPod can count."""
    return (
        target["id"] != source["id"]
        and not is_mask(target)
        and not is_mask(source)
        and target["width"] == source["width"]
        and target["height"] == source["height"]
    )


def check_alias(
    target: Entry, source: Entry, where: str, from_other: bool = False
) -> None:
    """Of the stock bitmaps; with from_other a bitmap may name itself for its
    own art in the other appearance, and the compiler does the re-encoding
    the iPod otherwise caps at SCRATCH_PIXELS."""
    if target["id"] == source["id"]:
        fail(where, f"{target['name']} cannot alias itself without from_other")
    if not alias_fits(target, source):
        fail(
            where,
            f"{describe_layout(source)} does not fit {describe_layout(target)}: an"
            " alias needs the same size and no mask on either side",
        )
    pixels = target["width"] * target["height"]
    if not from_other and not same_layout(target, source):
        if pixels > rvtfile.SCRATCH_PIXELS:
            fail(
                where,
                f"{describe_layout(source)} must be re-encoded into "
                f"{describe_layout(target)}, which the iPod does for at most "
                f"{rvtfile.SCRATCH_PIXELS} pixels",
            )


def check_aliases(aliases: dict, tinted: dict, names, where) -> None:
    """The pack-wide alias rules: at most ALIASES_MAX, no alias of an alias,
    no tinted source. aliases maps index -> source index; names(index) and
    where(index) give the messages their words."""
    if len(aliases) > rvtfile.ALIASES_MAX:
        fail(where(None), f"more than {rvtfile.ALIASES_MAX} aliases")
    for index, source in aliases.items():
        if source in aliases:
            fail(where(index), f"{names(source)} is an alias itself")
        if source in tinted:
            fail(where(index), f"{names(source)} is tinted")


def check_invert(info: Entry, where: str) -> None:
    if is_mask(info):
        fail(where, f"{info['name']} is a mask; tint it instead")


def relight_words(table: dict, where: str) -> list[int]:
    values = dict(RELIGHT_DEFAULTS)
    for name in rvtfile.RELIGHT_FIELDS:
        if name in table:
            values[name] = table[name]
    return [
        to_fixed(values[name], f"{where}.{name}") for name in rvtfile.RELIGHT_FIELDS
    ]


def relight_levels(words: list[int]) -> int:
    """Palette entries a relight may need: one per gray between bg_lo and icon_hi."""
    w = dict(zip(rvtfile.RELIGHT_FIELDS, words))
    return ((w["icon_hi"] + ONE // 2) >> 8) - (w["bg_lo"] >> 8) + 1


def check_relight(words: list[int], info: Entry, where: str) -> None:
    """The bounds derive.c enforces, so a rule the compiler accepts is one the
    iPod applies."""
    w = dict(zip(rvtfile.RELIGHT_FIELDS, words))
    if not 0 <= w["t_zero"] < w["t_full"] <= LEVEL_MAX:
        fail(where, "expected 0 <= t_zero < t_full <= 255")
    for name, bound in RELIGHT_BOUNDS.items():
        if abs(w[name]) > bound:
            fail(f"{where}.{name}", f"expected -{bound // ONE} to {bound // ONE}")
    if not 0 <= w["bg_lo"] <= w["bg_hi"] <= w["icon_lo"] <= w["icon_hi"] <= LEVEL_MAX:
        fail(where, "expected 0 <= bg_lo <= bg_hi <= icon_lo <= icon_hi <= 255")
    if info["format"] not in bitmaps.PALETTE_FORMATS:
        fail(where, f"relight needs a paletted bitmap; {info['name']} is not")
    if info["width"] * info["height"] > rvtfile.SCRATCH_PIXELS:
        fail(where, f"{info['name']} has more than {rvtfile.SCRATCH_PIXELS} pixels")
    if relight_levels(words) > info["palette_colors"]:
        fail(
            where,
            f"needs {relight_levels(words)} palette entries, "
            f"{info['name']} has {info['palette_colors']}",
        )


# Record payloads


def encode(kind: str, spec) -> bytes:
    if kind in rvtfile.PIXEL_KINDS:
        return spec
    if kind == "recolor":
        return struct.pack("<I", len(spec)) + b"".join(
            rvtfile.PAIR.pack(source, target) for source, target in spec
        )
    if kind == "alias":
        return struct.pack("<I", spec)
    if kind == "invert":
        return b""
    return rvtfile.RELIGHT.pack(*spec)


def decode(kind: str, payload: bytes, where: str) -> object:
    """The spec of a payload after its structural checks; catalog checks are
    the caller's."""
    if kind == "recolor":
        if (
            len(payload) < 4 + rvtfile.PAIR.size
            or (len(payload) - 4) % rvtfile.PAIR.size
        ):
            fail(where, "recolor payload must be a count and whole colour pairs")
        count = struct.unpack_from("<I", payload)[0]
        if count * rvtfile.PAIR.size != len(payload) - 4:
            fail(where, "recolor count does not match the payload")
        pairs = [
            rvtfile.PAIR.unpack_from(payload, 4 + i * rvtfile.PAIR.size)
            for i in range(count)
        ]
        for before, after in zip(pairs, pairs[1:]):
            if key(after[0]) <= key(before[0]):
                fail(where, "recolor pairs must be strictly ascending")
        for source, target in pairs:
            if source == target:
                fail(where, "recolor maps a colour to itself")
        return pairs
    if kind == "alias":
        if len(payload) != 4:
            fail(where, "alias payload must be one index")
        return struct.unpack("<I", payload)[0]
    if kind == "invert":
        if payload:
            fail(where, "invert takes no payload")
        return None
    if kind == "relight":
        if len(payload) != rvtfile.RELIGHT_BYTES:
            fail(where, f"relight payload must be {rvtfile.RELIGHT_BYTES} bytes")
        return list(rvtfile.RELIGHT.unpack(payload))
    fail(where, f"unknown record kind {kind}")


# Reference arithmetic and host application. Every function takes the whole
# native bitmap (header included) and returns a new one.


def luma(red: int, green: int, blue: int) -> int:
    return (77 * red + 150 * green + 29 * blue) >> 8


def tdiv(a: int, b: int) -> int:
    """Division truncating toward zero, as C does."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _palette(info, data):
    start = info["data_offset"]
    return [
        bytearray(data[start + i * 4 : start + i * 4 + 4])
        for i in range(info["palette_colors"])
    ]


def _write_palette(info, data, palette):
    start = info["data_offset"]
    for i, entry in enumerate(palette):
        data[start + i * 4 : start + i * 4 + 4] = entry


def _index(info, data, x, y):
    at = info["pixels_offset"] + y * info["stride"]
    if info["format"] == bitmaps.INDEXED8:
        return data[at + x]
    return struct.unpack_from("<H", data, at + 2 * x)[0]


def _set_index(info, data, x, y, value):
    at = info["pixels_offset"] + y * info["stride"]
    if info["format"] == bitmaps.INDEXED8:
        data[at + x] = value
    else:
        struct.pack_into("<H", data, at + 2 * x, value)


def _each_slot(info, data):
    """Offsets of every colour slot: palette entries, BGRA8888 pixels or RGB565
    words."""
    if info["palette_colors"]:
        return [(info["data_offset"] + i * 4, 4) for i in range(info["palette_colors"])]
    size = 4 if info["format"] == bitmaps.BGRA8888 else 2
    return [
        (info["pixels_offset"] + y * info["stride"] + x * size, size)
        for y in range(info["height"])
        for x in range(info["width"])
    ]


def _slot_rgba(data, at, size):
    if size == 4:
        blue, green, red, alpha = data[at : at + 4]
        return bytes((red, green, blue, alpha))
    word = struct.unpack_from("<H", data, at)[0]
    return bytes((*bitmaps.unpack_565(word), 255))


def _set_slot(data, at, size, color):
    red, green, blue, alpha = color
    if size == 4:
        data[at : at + 4] = bytes((blue, green, red, alpha))
    else:
        struct.pack_into("<H", data, at, bitmaps.pack_565(red, green, blue))


def apply_recolor(info: Entry, data: bytes, pairs: list) -> bytes:
    table = dict(pairs)
    out = bytearray(data)
    for at, size in _each_slot(info, out):
        target = table.get(_slot_rgba(out, at, size))
        if target is not None:
            _set_slot(out, at, size, target)
    return bytes(out)


def apply_invert(info: Entry, data: bytes) -> bytes:
    out = bytearray(data)
    for at, size in _each_slot(info, out):
        if size == 4:
            if info["palette_colors"] or out[at + 3]:
                for i in range(3):
                    out[at + i] ^= 255
        else:
            struct.pack_into(
                "<H", out, at, struct.unpack_from("<H", out, at)[0] ^ 0xFFFF
            )
    return bytes(out)


def relight_coverage(words: list[int], info: Entry, data: bytes) -> bytearray:
    """t per pixel, 0..FULL, after shadow pruning."""
    w = dict(zip(rvtfile.RELIGHT_FIELDS, words))
    palette = _palette(info, data)
    width, height = info["width"], info["height"]
    t = bytearray(width * height)
    for y in range(height):
        bg = palette[_index(info, data, 0, y)]
        for x in range(width):
            c = palette[_index(info, data, x, y)]
            o = max(abs(c[i] - bg[i]) for i in range(3)) * ONE
            if o <= w["t_zero"]:
                value = 0
            elif o >= w["t_full"]:
                value = FULL
            else:
                value = (o - w["t_zero"]) * FULL // (w["t_full"] - w["t_zero"])
            t[y * width + x] = value
    pruned = bytearray(t)
    for y in range(height):
        for x in range(width):
            if not 0 < t[y * width + x] < FULL:
                continue
            solid = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if (dx or dy) and 0 <= nx < width and 0 <= ny < height:
                        solid |= t[ny * width + nx] == FULL
            if not solid:
                pruned[y * width + x] = 0
    return pruned


def relight_gray(words: list[int], c: bytes, bg: bytes, y: int, t: int) -> int:
    """The gray of one pixel: c and bg are BGRA, t is 0..FULL."""
    w = dict(zip(rvtfile.RELIGHT_FIELDS, words))
    bgd = w["bg_base"] + tdiv(
        (luma(bg[2], bg[1], bg[0]) * ONE - w["bg_ref"]) * w["bg_slope"], ONE
    )
    bgd = clamp(bgd, w["bg_lo"], w["bg_hi"])
    icon = w["icon_base"] + w["icon_luma"] * luma(c[2], c[1], c[0]) + w["icon_row"] * y
    icon = clamp(icon, w["icon_lo"], w["icon_hi"])
    mixed = bgd + ((icon - bgd) * t + FULL // 2) // FULL
    return (mixed + ONE // 2) >> 8


def apply_relight(info: Entry, data: bytes, words: list[int]) -> bytes:
    out = bytearray(data)
    palette = _palette(info, out)
    width, height = info["width"], info["height"]
    t = relight_coverage(words, info, out)
    grays = bytearray(width * height)
    for y in range(height):
        bg = palette[_index(info, out, 0, y)]
        for x in range(width):
            c = palette[_index(info, out, x, y)]
            grays[y * width + x] = relight_gray(words, c, bg, y, t[y * width + x])
    levels = sorted(set(grays))
    if len(levels) > info["palette_colors"]:
        raise ValueError("relight produced more grays than the palette holds")
    lookup = {gray: i for i, gray in enumerate(levels)}
    _write_palette(
        info,
        out,
        [bytearray((g, g, g, 255)) for g in levels]
        + [bytearray(4) for _ in range(info["palette_colors"] - len(levels))],
    )
    for y in range(height):
        for x in range(width):
            _set_index(info, out, x, y, lookup[grays[y * width + x]])
    return bytes(out)


def apply_alias(target: Entry, data: bytes, source: Entry, source_data: bytes) -> bytes:
    """Target with the source's pixels: a byte copy for equal layouts, else the
    pixels re-encoded; a paletted target takes the distinct colours in order of
    first appearance and must have room for them."""
    out = bytearray(data)
    if same_layout(target, source):
        start = target["data_offset"]
        out[start:] = source_data[start:]
        return bytes(out)
    pixels = bitmaps.decode_pixels(source, source_data[source["data_offset"] :])
    width, height = target["width"], target["height"]
    palette = {}
    for y in range(height):
        at = target["pixels_offset"] + y * target["stride"]
        for x in range(width):
            i = (y * width + x) * 4
            red, green, blue, alpha = pixels[i : i + 4]
            if target["palette_colors"]:
                color = bytes((blue, green, red, alpha))
                if color not in palette:
                    if len(palette) == target["palette_colors"]:
                        raise ValueError(
                            f"{source['name']} has more colours than "
                            f"{target['name']}'s palette holds"
                        )
                    palette[color] = len(palette)
                _set_index(target, out, x, y, palette[color])
            elif is_565(target):
                word = bitmaps.pack_565(red, green, blue)
                struct.pack_into("<H", out, at + 2 * x, word)
            else:
                out[at + 4 * x : at + 4 * x + 4] = bytes((blue, green, red, alpha))
    if target["palette_colors"]:
        _write_palette(
            target,
            out,
            [bytearray(color) for color in palette]
            + [bytearray(4) for _ in range(target["palette_colors"] - len(palette))],
        )
    return bytes(out)


def apply_record(
    catalog: Catalog,
    stock,
    index: int,
    kind: str,
    spec,
    results: dict[int, bytes],
    base: bytes | None = None,
) -> bytes:
    """One record over stock(index), or over `base`, the other appearance's
    pixels payload of this bitmap (of the source, for an alias). An alias
    without a base reads its source from results when the pack derived or
    replaced it, else from stock."""
    info = catalog.assets[index]
    data = stock(index)
    if base is not None:
        if kind == "alias":
            source = catalog.assets[spec]
            return apply_alias(
                info, data, source, stock(spec)[: source["data_offset"]] + base
            )
        data = data[: info["data_offset"]] + base
    if kind in rvtfile.PIXEL_KINDS:
        return data[: info["data_offset"]] + spec
    if kind == "recolor":
        return apply_recolor(info, data, spec)
    if kind == "invert":
        return apply_invert(info, data)
    if kind == "relight":
        return apply_relight(info, data, spec)
    source_data = results[spec] if spec in results else stock(spec)
    return apply_alias(info, data, catalog.assets[spec], source_data)


def apply_pack(catalog: Catalog, stock, records) -> dict[int, bytes]:
    """Index -> derived bitmap bytes for a pack's records (index, kind, spec),
    in the device's order: everything but aliases ascending, then the aliases.
    stock(index) returns a bitmap's stock bytes."""
    results = {}
    aliases = []
    for index, kind, spec in records:
        if kind == "alias":
            aliases.append((index, spec))
            continue
        results[index] = apply_record(catalog, stock, index, kind, spec, results)
    for index, source in aliases:
        results[index] = apply_record(catalog, stock, index, "alias", source, results)
    return results
