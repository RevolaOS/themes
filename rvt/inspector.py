# SPDX-License-Identifier: GPL-3.0-only
"""Validate an .rvt and describe it, against the catalog when one is given."""

from rvt import assets, bitmaps, derive, lz, rvtfile, style
from rvt.catalog import Catalog
from rvt.errors import fail


def inspect_pack(
    body: bytes,
    count: int,
    bitmap_count: int,
    catalog: Catalog | None,
    where: str,
    names: dict | None = None,
) -> dict:
    """Decoded style, records and extension bitmaps of one pack after checking
    every record. A pixels record's `payload` is the bitmap's bytes from its
    data offset, decoded for the lz kind when the catalog gives the size; an
    extension bitmap's `bmap` is its decoded whole BMap. Messages name the
    bitmap when there is a catalog, else its index; extension bitmaps are
    named from `names` ((owner hash, asset hash) -> "id/asset") when it knows
    them."""
    if catalog is not None and (
        len(body) > catalog.max_body() + rvtfile.EXTENSION_TABLE_MAX_BYTES
    ):
        fail(where, "pack exceeds the catalog maximum")
    try:
        decoded = style.decode(body[: rvtfile.STYLE_BYTES])
    except ValueError as error:
        fail(where, str(error))
    entries = catalog.assets if catalog is not None else None

    def label(index):
        if entries is not None and index < len(entries):
            return entries[index]["name"]
        return f"bitmap {index}"

    records = []
    at = rvtfile.STYLE_BYTES
    previous = -1
    for _ in range(count):
        if at + rvtfile.RECORD_BYTES > len(body):
            fail(where, "truncated record header")
        offset = at
        index, word, length = rvtfile.RECORD.unpack_from(body, at)
        if index <= previous:
            fail(where, "records must be sorted by unique catalog index")
        previous = index
        if word >= len(rvtfile.KINDS):
            fail(where, f"{label(index)} has unknown record kind {word:#x}")
        kind = rvtfile.KINDS[word]
        info = None
        if entries is not None:
            if index >= len(entries):
                fail(where, f"catalog index {index} is outside the catalog")
            info = entries[index]
            if kind == "pixels" and length != catalog.payload_bytes(index):
                fail(where, f"{label(index)} does not match the native bitmap")
        at += rvtfile.RECORD_BYTES
        end = at + length
        if (not length and kind != "invert") or rvtfile.align(end) > len(body):
            fail(where, "truncated record payload")
        payload = body[at:end]
        record = {"index": index, "kind": kind, "bytes": length, "offset": offset}
        if kind in rvtfile.PIXEL_KINDS:
            if kind == "pixels_lz" and info is not None:
                try:
                    payload = lz.lz_decode(payload, catalog.payload_bytes(index))
                except ValueError as error:
                    fail(where, f"{label(index)}: {error}")
            if info is not None and not bitmaps.palette_indices_fit(info, payload):
                fail(where, f"{label(index)} has an invalid palette index")
            record["payload"] = payload
        else:
            spec = derive.decode(kind, payload, f"{where} {label(index)}")
            record["spec"] = spec
            if info is not None:
                check_derived(kind, spec, index, catalog, f"{where} {label(index)}")
        if any(body[end : rvtfile.align(end)]):
            fail(where, "record padding must be zero")
        records.append(record)
        at = rvtfile.align(end)
    if catalog is not None and at > catalog.max_body():
        fail(where, "records exceed the catalog maximum")
    decoded["extension_bitmaps"], at = assets.decode_table(
        body, at, bitmap_count, where
    )
    for found in decoded["extension_bitmaps"]:
        found["name"] = assets.label(found, names or {})
    if at != len(body):
        fail(where, "trailing bytes after the last extension bitmap")
    by_index = {record["index"]: record for record in records}
    derive.check_aliases(
        {r["index"]: r["spec"] for r in records if r["kind"] == "alias"},
        decoded["tinted"],
        label,
        lambda index: where if index is None else f"{where} alias {label(index)}",
    )
    for index, (role, coverage) in decoded["tinted"].items():
        record = by_index.get(index)
        if record is not None and record["kind"] not in rvtfile.PIXEL_KINDS:
            fail(where, f"tinted {label(index)} has a derived record")
        if record is not None and coverage != "alpha":
            fail(where, f"tinted {label(index)} takes its coverage from stock art")
        if entries is None:
            continue
        if index >= len(entries):
            fail(where, f"tinted catalog index {index} is outside the catalog")
        if bitmaps.tint_kind(entries[index]["format"]) is None:
            fail(where, f"tinted {label(index)} has no palette or coverage")
    if entries is not None:
        for record in records:
            record["name"] = entries[record["index"]]["name"]
        decoded["tinted"] = {
            index: {"name": entries[index]["name"], "role": role, "coverage": coverage}
            for index, (role, coverage) in decoded["tinted"].items()
        }
    else:
        decoded["tinted"] = {
            index: {"role": role, "coverage": coverage}
            for index, (role, coverage) in decoded["tinted"].items()
        }
    decoded["records"] = records
    decoded["bytes"] = len(body)
    return decoded


def check_derived(kind: str, spec, index: int, catalog: Catalog, where: str) -> None:
    """Catalog checks of a derived record."""
    info = catalog.assets[index]
    if kind == "recolor":
        derive.check_recolor(spec, info, where)
    elif kind == "alias":
        if spec >= len(catalog.assets):
            fail(where, f"alias source {spec} is outside the catalog")
        derive.check_alias(info, catalog.assets[spec], where)
    elif kind == "invert":
        derive.check_invert(info, where)
    else:
        derive.check_relight(spec, info, where)


def inspect(
    data: bytes, catalog: Catalog | None = None, names: dict | None = None
) -> dict:
    """Header fields and one decoded pack per appearance; raises ValueError."""
    header = rvtfile.decode_file(data)
    if catalog is not None and header["fingerprint"] != catalog.fingerprint:
        fail(
            "header",
            f"catalog fingerprint {header['fingerprint'].hex()} is not "
            f"{catalog.fingerprint.hex()}",
        )
    return {
        "id": header["id"],
        "name": header["name"],
        "version": header["version"],
        "fingerprint": header["fingerprint"].hex(),
        "appearances": {
            appearance: inspect_pack(
                body, count, bitmap_count, catalog, appearance, names
            )
            for appearance, (body, count, bitmap_count) in header["packs"].items()
        },
    }


def counts(records: list[dict]) -> dict[str, int]:
    """Records per kind, kinds with none left out, in rvt_kind order."""
    result = {}
    for record in records:
        result[record["kind"]] = result.get(record["kind"], 0) + 1
    return {kind: result[kind] for kind in rvtfile.KINDS if kind in result}


def describe(result: dict) -> str:
    """A readable summary of an inspect() result."""
    lines = [
        f"{result['id']}: {result['name']} (version {result['version']}, "
        f"catalog {result['fingerprint']})"
    ]
    names = {value: key for key, value in rvtfile.FLAGS.items()}
    for appearance, pack in result["appearances"].items():
        flags = [names[bit] for bit in names if pack["rendering"] & bit] or ["none"]
        lines.append(f"{appearance}:")
        for role, value in pack["colors"].items():
            lines.append(f"  {role:13} {value}")
        lines.append(f"  rendering     {', '.join(flags)}")
        kinds = ", ".join(f"{n} {kind}" for kind, n in counts(pack["records"]).items())
        lines.append(
            f"  bitmaps       {len(pack['records'])} records"
            f"{': ' + kinds if kinds else ''}; {len(pack['tinted'])} tinted; "
            f"{pack['bytes']:,} bytes"
        )
        listed = ", ".join(
            f"{asset['name']} {asset['width']}x{asset['height']} {asset['format']}"
            + (f" tinted {asset['tint']}" if asset["tint"] else "")
            for asset in pack["extension_bitmaps"]
        )
        lines.append(
            f"  extensions    {len(pack['extension_bitmaps'])} extension bitmaps"
            f"{': ' + listed if listed else ''}"
        )
    return "\n".join(lines)
