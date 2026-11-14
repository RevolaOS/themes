# SPDX-License-Identifier: GPL-3.0-only
"""The .rvt file: header and appearance packs.

Every constant comes from rvt/data/rvt.h, which the appearance extension
vendors byte for byte, so the two sides cannot drift apart.
"""

import ast
import re
import struct
import zlib
from importlib.resources import files

HEADER_FILE = files("rvt") / "data" / "rvt.h"

ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,30}")


def _evaluate(node, names):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, names)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, ast.BinOp):
        left, right = _evaluate(node.left, names), _evaluate(node.right, names)
        operators = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.LShift: lambda: left << right,
            ast.BitOr: lambda: left | right,
        }
        return operators[type(node.op)]()
    raise ValueError(f"unsupported expression in rvt.h: {ast.dump(node)}")


def parse(text: str) -> tuple[dict[str, int], dict[str, list[str]], dict[str, int]]:
    """Defines (name -> int), enums (name -> ordered member names) and enum
    member values (member -> int) of rvt.h.

    Enum members count from zero, or from the integer a member is given; a
    define may use them, so the enums are read first."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    enums = {}
    names = {}
    for name, body in re.findall(r"enum\s+(\w+)\s*\{(.*?)\}\s*;", text, re.S):
        members = []
        value = 0
        for item in body.split(","):
            if not item.strip():
                continue
            match = re.fullmatch(r"\s*(RVT_\w+)\s*(?:=\s*(\d+)\s*)?", item)
            if not match:
                raise ValueError(f"enum {name} has a member this parser cannot read")
            member, given = match.groups()
            if given is not None:
                value = int(given)
            members.append(member)
            names[member] = value
            value += 1
        enums[name] = members
    defines = {}
    for name, value in re.findall(r"^#define[ \t]+(RVT_\w+)[ \t]+(.+)$", text, re.M):
        expression = re.sub(r"\b(0[xX][0-9a-fA-F]+|\d+)[uU]?\b", r"\1", value)
        defines[name] = _evaluate(ast.parse(expression, mode="eval"), names)
        names[name] = defines[name]
    values = {member: names[member] for members in enums.values() for member in members}
    return defines, enums, values


DEFINES, ENUMS, VALUES = parse(HEADER_FILE.read_text())


def _names(enum, prefix):
    """Lower-case member names without the prefix; the last member is the count."""
    members = ENUMS[enum][:-1]
    return tuple(m.removeprefix(prefix).lower() for m in members)


def _values(enum, prefix):
    """Lower-case member name -> value, for enums that do not count from zero."""
    return {m.removeprefix(prefix).lower(): VALUES[m] for m in ENUMS[enum][:-1]}


MAGIC = DEFINES["RVT_MAGIC"].to_bytes(4, "little")
VERSION = DEFINES["RVT_VERSION"]
HEADER_BYTES = DEFINES["RVT_HEADER_BYTES"]
FINGERPRINT_BYTES = DEFINES["RVT_FINGERPRINT_BYTES"]
ID_BYTES = DEFINES["RVT_ID_BYTES"]
NAME_BYTES = DEFINES["RVT_NAME_BYTES"]
PACK_HEADER_BYTES = DEFINES["RVT_PACK_HEADER_BYTES"]
APPEARANCES = {
    "light": DEFINES["RVT_APPEARANCE_LIGHT"],
    "dark": DEFINES["RVT_APPEARANCE_DARK"],
}
FLAGS = {
    "flat_selection": DEFINES["RVT_FLAG_FLAT_SELECTION"],
    "menu_covers_off": DEFINES["RVT_FLAG_MENU_COVERS_OFF"],
    "flat_now_playing": DEFINES["RVT_FLAG_FLAT_NOW_PLAYING"],
    "flat_icons": DEFINES["RVT_FLAG_FLAT_ICONS"],
}
TINT_NONE = DEFINES["RVT_TINT_NONE"]
TINT_ROLE = DEFINES["RVT_TINT_ROLE"]
TINT_DARKNESS = DEFINES["RVT_TINT_DARKNESS"]
TINT_SOLID = DEFINES["RVT_TINT_SOLID"]
SOLID_FLOOR = DEFINES["RVT_SOLID_FLOOR"]
CATALOG_MAX = DEFINES["RVT_CATALOG_MAX"]
STYLE_COLORS = DEFINES["RVT_STYLE_COLORS"]
STYLE_FLAGS = DEFINES["RVT_STYLE_FLAGS"]
STYLE_PALETTES = DEFINES["RVT_STYLE_PALETTES"]
STYLE_TINTS = DEFINES["RVT_STYLE_TINTS"]
STYLE_BYTES = DEFINES["RVT_STYLE_BYTES"]
RECORD_BYTES = DEFINES["RVT_RECORD_BYTES"]
RELIGHT_BYTES = DEFINES["RVT_RELIGHT_BYTES"]
SCRATCH_BYTES = DEFINES["RVT_SCRATCH_BYTES"]
RECOLOR_MAX = DEFINES["RVT_RECOLOR_MAX"]
SCRATCH_PIXELS = DEFINES["RVT_SCRATCH_PIXELS"]
ALIASES_MAX = DEFINES["RVT_ALIASES_MAX"]
EXTENSION_BITMAP_BYTES = DEFINES["RVT_EXTENSION_BITMAP_BYTES"]
# Extension bitmap kinds, name -> the kind word.
EXTENSION_KINDS = _values("rvt_extension_kind", "RVT_EXTENSION_")
BMAP_HEADER_BYTES = DEFINES["RVT_BMAP_HEADER_BYTES"]
EXTENSION_BITMAPS_MAX = DEFINES["RVT_EXTENSION_BITMAPS_MAX"]
EXTENSION_BITMAP_MAX_BYTES = DEFINES["RVT_EXTENSION_BITMAP_MAX_BYTES"]
# The largest extension bitmap table: every bitmap at the cap, padded.
EXTENSION_TABLE_MAX_BYTES = EXTENSION_BITMAPS_MAX * (
    EXTENSION_BITMAP_BYTES + EXTENSION_BITMAP_MAX_BYTES
)
# A Settings icon's rows: Mask8, stride 80, 121 rows.
MENU_ROWS_BYTES = 80 * 121
ROLES = _names("rvt_role", "RVT_ROLE_")
ACCENTS = _names("rvt_accent", "RVT_ACCENT_")
ACCENT_SLOTS = _names("rvt_accent_slot", "RVT_SLOT_")
KINDS = _names("rvt_kind", "RVT_KIND_")
PIXEL_KINDS = ("pixels", "pixels_lz")
LZ_WINDOW = DEFINES["RVT_LZ_WINDOW"]
LZ_MIN_MATCH = DEFINES["RVT_LZ_MIN_MATCH"]
RELIGHT_FIELDS = _names("rvt_relight", "RVT_RELIGHT_")

# The header fields in RVT_HEADER_* order; the rest up to HEADER_BYTES is zero.
HEADER = struct.Struct(f"<4sHH{FINGERPRINT_BYTES}sIIIIII{ID_BYTES}s{NAME_BYTES}s")
HEADER_OFFSETS = (
    DEFINES["RVT_HEADER_MAGIC"],
    DEFINES["RVT_HEADER_VERSION"],
    DEFINES["RVT_HEADER_HEADER_BYTES"],
    DEFINES["RVT_HEADER_FINGERPRINT"],
    DEFINES["RVT_HEADER_APPEARANCES"],
    DEFINES["RVT_HEADER_LIGHT_OFFSET"],
    DEFINES["RVT_HEADER_LIGHT_BYTES"],
    DEFINES["RVT_HEADER_DARK_OFFSET"],
    DEFINES["RVT_HEADER_DARK_BYTES"],
    DEFINES["RVT_HEADER_CRC"],
    DEFINES["RVT_HEADER_ID"],
    DEFINES["RVT_HEADER_NAME"],
)
CRC_OFFSET = DEFINES["RVT_HEADER_CRC"]
# A pack header in RVT_PACK_* order: body bytes, record count, body CRC,
# extension bitmap count.
PACK = struct.Struct("<IIII")
PACK_OFFSETS = (
    DEFINES["RVT_PACK_BODY_BYTES"],
    DEFINES["RVT_PACK_RECORDS"],
    DEFINES["RVT_PACK_CRC"],
    DEFINES["RVT_PACK_EXTENSION_BITMAPS"],
)
# A record: catalog index, kind, payload bytes.
RECORD = struct.Struct("<III")
# An extension bitmap: owner hash, asset hash, kind, stored bytes, decoded
# bytes, tint byte (TINT_NONE or TINT_ROLE plus a role, no coverage bits).
EXTENSION_BITMAP = struct.Struct("<IIIIII")
PAIR = struct.Struct("<4s4s")
RELIGHT = struct.Struct(f"<{len(RELIGHT_FIELDS)}i")


def _field_offsets(layout: struct.Struct) -> tuple[int, ...]:
    """Where each field of a little-endian layout starts; a counted `s` is
    one field, a counted number is that many."""
    offsets = []
    at = 0
    for count, code in re.findall(r"(\d*)([a-zA-Z])", layout.format):
        fields = [count + code] if code == "s" else [code] * int(count or 1)
        for field in fields:
            offsets.append(at)
            at += struct.calcsize(field)
    return tuple(offsets)


if (
    MAGIC != b"RVT0"
    or HEADER.size > HEADER_BYTES
    or _field_offsets(HEADER) != HEADER_OFFSETS
    or PACK.size != PACK_HEADER_BYTES
    or _field_offsets(PACK) != PACK_OFFSETS
    or RECORD.size != RECORD_BYTES
    or EXTENSION_BITMAP.size != EXTENSION_BITMAP_BYTES
    or EXTENSION_KINDS != {"bitmap": 1, "bitmap_lz": 2}
    or BMAP_HEADER_BYTES != 28
    or EXTENSION_BITMAP_MAX_BYTES < BMAP_HEADER_BYTES + MENU_ROWS_BYTES
    or STYLE_COLORS != 0
    or STYLE_FLAGS != len(ROLES) * 4
    or STYLE_PALETTES != STYLE_FLAGS + 4
    or STYLE_TINTS != STYLE_PALETTES + len(ACCENTS) * len(ACCENT_SLOTS) * 4
    or STYLE_BYTES != STYLE_TINTS + CATALOG_MAX
    or RELIGHT.size != RELIGHT_BYTES
    or KINDS != ("pixels", "recolor", "alias", "invert", "relight", "pixels_lz")
    or LZ_WINDOW != 4096
    or LZ_MIN_MATCH != 3
    or TINT_ROLE + len(ROLES) > 16
    or TINT_DARKNESS < 16
    or TINT_SOLID < 16
    or TINT_DARKNESS & TINT_SOLID
    or not 0 < SOLID_FLOOR <= 255
    or RECOLOR_MAX * PAIR.size > SCRATCH_BYTES
    or SCRATCH_PIXELS + 256 > SCRATCH_BYTES
):
    raise ValueError("rvt/data/rvt.h does not match the layout this module encodes")


def align(size: int) -> int:
    return size + -size % 4


def check_id(value: str, where: str = "id") -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{where}: expected [a-z0-9][a-z0-9_-]{{0,30}}")
    return value


def check_text(value: str, where: str, limit: int) -> str:
    """A non-empty string without control characters of at most `limit`
    UTF-8 bytes."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where}: expected a non-empty string")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(f"{where}: control characters are not allowed")
    if len(value.encode()) > limit:
        raise ValueError(f"{where}: exceeds {limit} UTF-8 bytes")
    return value


def check_name(value: str, where: str = "name") -> str:
    return check_text(value, where, NAME_BYTES - 1)


def fnv1a(data: bytes) -> int:
    """FNV-1a, the hash the core keys extension ids and asset names with."""
    value = 2166136261
    for byte in data:
        value = (value ^ byte) * 16777619 & 0xFFFFFFFF
    return value


def encode_pack(body: bytes, count: int, bitmaps: int = 0) -> bytes:
    """Pack header and body; the body is the style prefix, the padded records
    and the `bitmaps` extension bitmaps after them."""
    if len(body) % 4:
        raise ValueError("pack body is not a multiple of 4 bytes")
    return PACK.pack(len(body), count, zlib.crc32(body), bitmaps) + body


def encode_file(
    fingerprint: bytes,
    identifier: str,
    name: str,
    packs: dict[str, tuple[bytes, int, int]],
) -> bytes:
    """A complete .rvt: packs maps an appearance name to (body, record count,
    extension bitmap count)."""
    if len(fingerprint) != FINGERPRINT_BYTES:
        raise ValueError(f"fingerprint must be {FINGERPRINT_BYTES} bytes")
    check_id(identifier)
    check_name(name)
    if not packs:
        raise ValueError("a theme needs a light or dark appearance")
    mask = 0
    placement = {}
    data = bytearray()
    offset = HEADER_BYTES
    for appearance, bit in APPEARANCES.items():
        if appearance not in packs:
            continue
        pack = encode_pack(*packs[appearance])
        mask |= bit
        placement[appearance] = (offset, len(pack))
        data += pack
        offset += len(pack)
    header = bytearray(HEADER_BYTES)
    HEADER.pack_into(
        header,
        0,
        MAGIC,
        VERSION,
        HEADER_BYTES,
        fingerprint,
        mask,
        *placement.get("light", (0, 0)),
        *placement.get("dark", (0, 0)),
        0,
        identifier.encode("ascii"),
        name.encode(),
    )
    struct.pack_into("<I", header, CRC_OFFSET, zlib.crc32(header))
    return bytes(header) + bytes(data)


def _cstring(field, where, encoding):
    end = field.find(b"\0")
    if end < 0:
        raise ValueError(f"{where}: missing NUL terminator")
    if any(field[end:]):
        raise ValueError(f"{where}: bytes after the NUL terminator must be zero")
    try:
        return field[:end].decode(encoding)
    except UnicodeDecodeError:
        raise ValueError(f"{where}: invalid {encoding}") from None


def decode_header(data: bytes) -> dict:
    if len(data) < HEADER_BYTES:
        raise ValueError(f"header: expected {HEADER_BYTES} bytes, got {len(data)}")
    (
        magic,
        version,
        header_bytes,
        fingerprint,
        mask,
        light_offset,
        light_bytes,
        dark_offset,
        dark_bytes,
        crc,
        raw_id,
        raw_name,
    ) = HEADER.unpack_from(data)
    if magic != MAGIC:
        raise ValueError(f"header: bad magic {magic!r}")
    if version != VERSION:
        raise ValueError(f"header: version {version} is not {VERSION}")
    # A larger header is a later layout's; the packs start where it says.
    if header_bytes < HEADER_BYTES or header_bytes % 4 or header_bytes > len(data):
        raise ValueError(f"header: expected at least {HEADER_BYTES} header bytes")
    sealed = bytearray(data[:HEADER_BYTES])
    struct.pack_into("<I", sealed, CRC_OFFSET, 0)
    if zlib.crc32(sealed) != crc:
        raise ValueError("header: CRC-32 mismatch")
    if not mask or mask & ~sum(APPEARANCES.values()):
        raise ValueError(f"header: invalid appearance bits {mask:#x}")
    placement = {
        "light": (light_offset, light_bytes),
        "dark": (dark_offset, dark_bytes),
    }
    expected = header_bytes
    packs = {}
    for appearance, bit in APPEARANCES.items():
        offset, size = placement[appearance]
        if not mask & bit:
            if offset or size:
                raise ValueError(f"header: {appearance} is absent but placed")
            continue
        if offset != expected or size < PACK_HEADER_BYTES:
            raise ValueError(f"header: {appearance} pack is misplaced")
        packs[appearance] = (offset, size)
        expected = align(offset + size)
    if len(data) != expected:
        raise ValueError(f"file: expected {expected} bytes, got {len(data)}")
    return {
        "version": version,
        "fingerprint": bytes(fingerprint),
        "id": check_id(_cstring(raw_id, "header id", "ascii"), "header id"),
        "name": check_name(_cstring(raw_name, "header name", "utf-8"), "header name"),
        "packs": packs,
    }


def decode_pack(data: bytes, offset: int, size: int) -> tuple[bytes, int, int]:
    """(body, record count, extension bitmap count) of the pack at offset,
    after checking its CRC."""
    body_bytes, count, crc, bitmaps = PACK.unpack_from(data, offset)
    if body_bytes != size - PACK_HEADER_BYTES or body_bytes < STYLE_BYTES:
        raise ValueError(f"pack at {offset}: body of {body_bytes} bytes does not fit")
    body = bytes(data[offset + PACK_HEADER_BYTES : offset + size])
    if zlib.crc32(body) != crc:
        raise ValueError(f"pack at {offset}: CRC-32 mismatch")
    if bitmaps > EXTENSION_BITMAPS_MAX:
        raise ValueError(f"pack at {offset}: {bitmaps} extension bitmaps")
    return body, count, bitmaps


def decode_file(data: bytes) -> dict:
    """Header fields plus packs as appearance -> (body, record count, extension
    bitmap count)."""
    header = decode_header(data)
    header["packs"] = {
        appearance: decode_pack(data, offset, size)
        for appearance, (offset, size) in header["packs"].items()
    }
    return header
