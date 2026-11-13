# SPDX-License-Identifier: GPL-3.0-only
"""Extension bitmaps: <appearance>/extensions/<extension-id>/<asset>.png and
<appearance>/revola/<asset>.png for the core's own.

A theme replaces any bitmap asset of an extension, a Settings icon or a canvas
bitmap, with a whole BMap the iPod uses as it would the extension's own: the
28-byte header, then the palette and rows. The compiler encodes a PNG with the
SDK's own encoder, rvt/data/bitmap.py, vendored byte for byte from
revola/tools/bitmap.py: `encode_mask` for a menu bitmap (a 78 x 121 coverage
mask, Mask8, stride 80), `encode_bmap` for any other (Indexed8 with a palette
up to 256 colours, else BGRA8888, rows padded to 4 bytes). The pack stores the
header raw and the rows raw or as one lz stream, at most the rows plus one flag
byte per 8, keyed by the FNV-1a hashes of the extension id and the asset name,
as the core keys them.

Which (id, asset) pairs exist and what size they are comes from the extension
asset catalog, rvt/data/extensions.json for the first-party extensions, plus
any `--extension assets.json` additions; docs/catalog.md.
"""

import json
import re
import struct
from importlib.resources import files
from pathlib import Path

from rvt import bitmaps, lz, rvtfile
from rvt.data import bitmap
from rvt.errors import fail

HEADER = bitmap.HEADER
MASK8, INDEXED8, BGRA8888 = bitmap.MASK8, bitmap.INDEXED8, bitmap.BGRA8888
MENU_WIDTH, MENU_HEIGHT = bitmap.MENU_SIZE
MENU_STRIDE = (MENU_WIDTH + 3) & ~3
MENU_HEADER = HEADER.pack(
    MASK8, 0, MENU_STRIDE, 8, 0, 0, MENU_HEIGHT, MENU_WIDTH, MENU_STRIDE * MENU_HEIGHT
)
FORMAT_NAMES = {MASK8: "mask8", INDEXED8: "indexed8", BGRA8888: "bgra8888"}
# The art box of a Settings icon; the rows below it hold the reflection.
ART_ROWS = 79

if HEADER.size != rvtfile.BMAP_HEADER_BYTES:
    raise ValueError("rvt/data/rvt.h and rvt/data/bitmap.py disagree on the header")

FOLDER = "extensions"
CORE_ID = "revola"
# The core's own bitmaps, owned by the id revola, have their own folder beside
# apple/ and extensions/.
CORE_FOLDER = CORE_ID
ID_PATTERN = re.compile(r"[a-z][a-z0-9_-]{0,31}")
ASSET_PATTERN = re.compile(r"[a-z0-9_-]{1,31}")
PNG_LIMIT = 16 * 1024 * 1024
CATALOG = files("rvt") / "data" / "extensions.json"
RECORD_KEYS = (
    "id",
    "asset",
    "menu",
    "format",
    "width",
    "height",
    "stride",
    "depth",
    "palette_colors",
    "bytes",
    "resident",
)


def owner_hash(identifier: str) -> int:
    return rvtfile.fnv1a(identifier.encode())


def asset_hash(asset: str) -> int:
    return rvtfile.fnv1a(asset.encode())


# The extension asset catalog


def check_record(record: dict, where: str) -> dict:
    """A catalog record with exactly the known keys and plausible values."""
    if not isinstance(record, dict) or tuple(sorted(record)) != tuple(
        sorted(RECORD_KEYS)
    ):
        fail(where, f"expected a record with the keys {', '.join(RECORD_KEYS)}")
    if not isinstance(record["id"], str) or not ID_PATTERN.fullmatch(record["id"]):
        fail(where, f"id must match {ID_PATTERN.pattern}")
    if not isinstance(record["asset"], str) or not ASSET_PATTERN.fullmatch(
        record["asset"]
    ):
        fail(where, f"asset must match {ASSET_PATTERN.pattern}")
    for key in ("menu", "resident"):
        if not isinstance(record[key], bool):
            fail(where, f"{key} is true or false")
    for key in (
        "format",
        "width",
        "height",
        "stride",
        "depth",
        "palette_colors",
        "bytes",
    ):
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            fail(where, f"{key} is a non-negative integer")
    if not record["width"] or not record["height"]:
        fail(where, "width and height are at least 1")
    if record["menu"] and (record["width"], record["height"]) != (
        MENU_WIDTH,
        MENU_HEIGHT,
    ):
        fail(where, f"a menu bitmap is {MENU_WIDTH}x{MENU_HEIGHT}")
    return record


def read_json(path: Path) -> list[dict]:
    """The records of an assets.json, one JSON object per line."""
    records = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            fail(f"{path}:{number}", str(error))
        records.append(check_record(record, f"{path}:{number}"))
    return records


def load_catalog(extensions: list[Path] = ()) -> dict[tuple[str, str], dict]:
    """(id, asset) -> record: the vendored first-party catalog, then every
    `--extension assets.json` in order, a later record for a pair replacing an
    earlier one."""
    records = {}
    sources = [Path(str(CATALOG)), *(Path(p) for p in extensions)]
    for number, path in enumerate(sources):
        if number and path.suffix != ".json":
            fail("--extension", f"{path}: expected an assets.json")
        if number and not path.is_file():
            fail("--extension", f"{path} does not exist")
        for record in read_json(path):
            records[record["id"], record["asset"]] = record
    return records


def known_names(records: dict[tuple[str, str], dict]) -> dict[tuple[int, int], str]:
    """(owner hash, asset hash) -> "id/asset" for the catalog's records."""
    return {
        (owner_hash(identifier), asset_hash(asset)): f"{identifier}/{asset}"
        for identifier, asset in records
    }


def label(asset: dict, names: dict[tuple[int, int], str]) -> str:
    return names.get(
        (asset["owner"], asset["asset"]),
        f"{asset['owner']:#010x}/{asset['asset']:#010x}",
    )


# The theme folder


def find_sources(folder: Path, appearance: str) -> dict[tuple[str, str], Path]:
    """(id, asset) -> PNG path: <appearance>/extensions/<id>/<asset>.png and
    the core's <appearance>/revola/<asset>.png."""
    root = Path(folder).resolve()
    found = {}

    def add(owner: str, directory: Path, where: str) -> None:
        for path in sorted(directory.iterdir()):
            at = f"{where}/{path.name}"
            if path.name.startswith("."):
                continue
            if path.suffix != ".png" or not ASSET_PATTERN.fullmatch(path.stem):
                fail(
                    at,
                    f"expected <asset>.png with the asset matching {ASSET_PATTERN.pattern}",
                )
            found[owner, path.stem] = source_file(path, root, at, PNG_LIMIT)

    core = root / appearance / CORE_FOLDER
    if core.is_dir():
        add(CORE_ID, core, f"{appearance}/{CORE_FOLDER}")
    directory = root / appearance / FOLDER
    if not directory.is_dir():
        return found
    for owner in sorted(directory.iterdir()):
        where = f"{appearance}/{FOLDER}/{owner.name}"
        if owner.name.startswith("."):
            continue
        if not owner.is_dir():
            fail(
                where,
                f"expected a folder named after an extension id ({ID_PATTERN.pattern})",
            )
        if owner.name == CORE_ID:
            fail(
                where,
                f"{CORE_ID} is the core's id; its bitmaps go in "
                f"{appearance}/{CORE_FOLDER}/",
            )
        if not ID_PATTERN.fullmatch(owner.name):
            fail(where, f"expected an extension id matching {ID_PATTERN.pattern}")
        add(owner.name, owner, where)
    return found


def source_file(path: Path, root: Path, where: str, limit: int) -> Path:
    """The resolved path of an art or rule file: a plain file inside the theme
    folder of at most `limit` bytes."""
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        fail(where, "does not exist")
    if not resolved.is_relative_to(root) or not resolved.is_file():
        fail(where, "must be a file inside the theme folder")
    if resolved.stat().st_size > limit:
        fail(where, f"exceeds {limit:,} bytes")
    return resolved


def source_path(appearance: str, identifier: str, asset: str) -> str:
    """Where the PNG of (id, asset) sits in the theme, for messages; without
    an appearance, the path below it."""
    folder = CORE_FOLDER if identifier == CORE_ID else f"{FOLDER}/{identifier}"
    return "/".join(part for part in (appearance, folder, f"{asset}.png") if part)


# Encoding


def encode(path: Path, where: str, record: dict | None) -> bytes:
    """The whole BMap of a PNG: the SDK's menu rule for a catalog record with
    `menu`, else its picture rule at the record's size. Without a record a
    78 x 121 coverage PNG is a menu bitmap; anything else needs the catalog."""
    try:
        width, height, rgba = bitmaps.read_png(path.read_bytes())
    except ValueError as error:
        fail(where, str(error))
    if record is None and (width, height) != (MENU_WIDTH, MENU_HEIGHT):
        fail(
            where,
            f"{width}x{height} is not a menu bitmap and the asset is not in the "
            "extension asset catalog; pass --extension assets.json of the extension",
        )
    menu = record is None or record["menu"]
    if not menu and (width, height) != (record["width"], record["height"]):
        fail(
            where,
            f"expected {record['width']}x{record['height']}, got {width}x{height}",
        )
    try:
        encoder = bitmap.encode_mask if menu else bitmap.encode_bmap
        data = encoder(width, height, rgba)
    except ValueError as error:
        fail(where, str(error))
    if len(data) > rvtfile.EXTENSION_BITMAP_MAX_BYTES:
        fail(
            where,
            f"{len(data):,} bytes exceed {rvtfile.EXTENSION_BITMAP_MAX_BYTES:,}",
        )
    return data


def is_menu(bmap: bytes) -> bool:
    """True when the header is the menu header the pane slot accepts."""
    return bmap[: HEADER.size] == MENU_HEADER


def has_reflection(bmap: bytes) -> bool:
    """True when a menu bitmap's rows below the art box carry anything."""
    return any(bmap[HEADER.size + ART_ROWS * MENU_STRIDE :])


def check_collisions(names: list[tuple[str, str]]) -> None:
    """Two (id, asset) pairs of a theme whose hashes agree would stand for one
    bitmap on the iPod."""
    seen: dict[tuple[int, int], tuple[str, str]] = {}
    for identifier, asset in names:
        key = (owner_hash(identifier), asset_hash(asset))
        other = seen.setdefault(key, (identifier, asset))
        if other != (identifier, asset):
            fail(
                source_path("", identifier, asset),
                f"its hashes collide with {source_path('', *other)}; rename one",
            )


# The table in the pack

KIND_NAMES = {value: name for name, value in rvtfile.EXTENSION_KINDS.items()}


def encode_table(
    bmaps: dict[tuple[str, str], bytes],
) -> tuple[bytes, int, dict[str, int]]:
    """The extension bitmap table of (id, asset) -> whole BMap, ascending by
    the hashes, the header raw and the rows as an lz stream when that is
    smaller; its bytes, its count and the count per kind name."""
    if len(bmaps) > rvtfile.EXTENSION_BITMAPS_MAX:
        fail(
            FOLDER,
            f"{len(bmaps)} extension bitmaps exceed {rvtfile.EXTENSION_BITMAPS_MAX}",
        )
    table = bytearray()
    counts: dict[str, int] = {}
    ordered = sorted(
        bmaps.items(), key=lambda item: (owner_hash(item[0][0]), asset_hash(item[0][1]))
    )
    for (identifier, asset), bmap in ordered:
        header, rows = bmap[: HEADER.size], bmap[HEADER.size :]
        name, data = "bitmap", rows
        packed = lz.lz_encode(rows)
        if len(packed) < len(rows):
            name, data = "bitmap_lz", packed
        counts[name] = counts.get(name, 0) + 1
        table += rvtfile.EXTENSION_BITMAP.pack(
            owner_hash(identifier),
            asset_hash(asset),
            rvtfile.EXTENSION_KINDS[name],
            HEADER.size + len(data),
        )
        table += header + data
        table += bytes(-len(table) % 4)
    return bytes(table), len(bmaps), counts


def header_sane(bmap: bytes) -> bool:
    """core_bitmap_whole: bounds in order and within 16 bits, depth at most
    32, a row of pixels within the stride, the palette within the payload and
    the rows within what is left."""
    fmt, _, stride, depth, top, left, bottom, right, payload = HEADER.unpack_from(bmap)
    height, width = bottom - top, right - left
    palette = 0
    if fmt == INDEXED8:
        colors = (
            struct.unpack_from("<I", bmap, HEADER.size)[0] if payload >= 4 else 0x10000
        )
        palette = 4 + 4 * colors if colors <= 256 else payload + 1
    return (
        bottom >= top
        and right >= left
        and height <= 0xFFFF
        and width <= 0xFFFF
        and depth <= 32
        and width * depth <= stride * 8
        and palette <= payload
        and height * stride <= payload - palette
    )


def describe(bmap: bytes) -> dict:
    """Size, format name and palette of a BMap, for inspection."""
    fmt, _, _, _, top, left, bottom, right, _ = HEADER.unpack_from(bmap)
    palette = 0
    if fmt == INDEXED8:
        palette = struct.unpack_from("<I", bmap, HEADER.size)[0]
    return {
        "width": right - left,
        "height": bottom - top,
        "format": FORMAT_NAMES.get(fmt, f"{fmt:#x}"),
        "palette": palette,
        "menu": is_menu(bmap),
    }


def decode_table(
    body: bytes, at: int, count: int, where: str
) -> tuple[list[dict], int]:
    """The `count` extension bitmaps starting at `at`, each checked: known
    kind, ascending unique (owner, asset), a payload of the header and the
    rows, raw or as an lz stream no longer than the rows plus a flag byte per
    8 that decodes to exactly the header's payload bytes, within the cap, with
    zero padding. Returns the bitmaps, each with its decoded whole BMap as
    `bmap`, and the offset after the last."""
    if count > rvtfile.EXTENSION_BITMAPS_MAX:
        fail(where, f"{count} extension bitmaps exceed {rvtfile.EXTENSION_BITMAPS_MAX}")
    found = []
    previous = None
    for _ in range(count):
        if at + rvtfile.EXTENSION_BITMAP_BYTES > len(body):
            fail(where, "truncated extension bitmap header")
        owner, asset, kind, length = rvtfile.EXTENSION_BITMAP.unpack_from(body, at)
        name = f"extension bitmap {owner:#010x}/{asset:#010x}"
        if previous is not None and (owner, asset) <= previous:
            fail(where, "extension bitmaps must be sorted by unique owner and asset")
        previous = (owner, asset)
        if kind not in KIND_NAMES:
            fail(where, f"{name} has unknown kind {kind:#x}")
        at += rvtfile.EXTENSION_BITMAP_BYTES
        end = at + length
        if length <= HEADER.size or rvtfile.align(end) > len(body):
            fail(where, f"{name}: truncated payload")
        header = body[at : at + HEADER.size]
        payload_bytes = HEADER.unpack_from(header)[8]
        if HEADER.size + payload_bytes > rvtfile.EXTENSION_BITMAP_MAX_BYTES:
            fail(
                where,
                f"{name}: {HEADER.size + payload_bytes:,} bytes exceed "
                f"{rvtfile.EXTENSION_BITMAP_MAX_BYTES:,}",
            )
        rows = body[at + HEADER.size : end]
        if KIND_NAMES[kind] == "bitmap_lz":
            if len(rows) > payload_bytes + (payload_bytes + 7) // 8:
                fail(where, f"{name}: lz stream longer than its rows allow")
            try:
                rows = lz.lz_decode(rows, payload_bytes)
            except ValueError as error:
                fail(where, f"{name}: {error}")
        elif len(rows) != payload_bytes:
            fail(where, f"{name}: payload bytes do not match its header")
        bmap = header + rows
        if not header_sane(bmap):
            fail(where, f"{name}: bitmap header does not describe its rows")
        if any(body[end : rvtfile.align(end)]):
            fail(where, f"{name}: padding must be zero")
        found.append(
            {
                "owner": owner,
                "asset": asset,
                "kind": KIND_NAMES[kind],
                "bytes": length,
                "bmap": bmap,
                **describe(bmap),
            }
        )
        at = rvtfile.align(end)
    return found, at
