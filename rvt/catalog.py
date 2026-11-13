# SPDX-License-Identifier: GPL-3.0-only
"""The bitmap catalog: every BMap of the pinned Apple firmware that a theme can
replace, by index. A pack's records and tint bytes index into this list, so a
theme is tied to the catalog it was compiled against by the fingerprint."""

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import TypedDict

from rvt import bitmaps, rvtfile

SCHEMA = 1


class Entry(TypedDict):
    """One catalog bitmap; docs/catalog.md describes the fields."""

    id: int
    name: str
    offset: int
    address: int
    bytes: int
    format: int
    depth: int
    width: int
    height: int
    stride: int
    data_offset: int
    pixels_offset: int
    palette_colors: int
    crc32: int


ENTRY_KEYS = tuple(Entry.__annotations__)
DEFAULT = files("rvt") / "data" / "osos-2.0.5.json"
FORMAT_NAMES = {
    bitmaps.MASK4: "mask4",
    bitmaps.MASK8: "mask8",
    bitmaps.INDEXED8: "indexed8",
    bitmaps.INDEXED16: "indexed16",
    bitmaps.RGB565: "rgb565",
    bitmaps.BGRA8888: "bgra8888",
}


def address(offset: int, runtime_base: int, runtime_file_offset: int) -> int:
    """Where a bitmap at a file offset lives: Apple loads osos.bin at
    runtime_base with the file's first runtime_file_offset bytes stripped."""
    return runtime_base + offset - runtime_file_offset


def canonical(entries: list[Entry]) -> bytes:
    return json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()


def fingerprint(entries: list[Entry]) -> bytes:
    """The first FINGERPRINT_BYTES of the SHA-256 of the canonical entry list."""
    return hashlib.sha256(canonical(entries)).digest()[: rvtfile.FINGERPRINT_BYTES]


def is_hex_id(reference: str) -> bool:
    return (
        reference[:2].lower() == "0x"
        and 1 <= len(reference) - 2 <= 8
        and all(c in "0123456789abcdefABCDEF" for c in reference[2:])
    )


class Catalog:
    assets: list[Entry]

    def __init__(self, document: dict):
        if not isinstance(document, dict) or document.get("schema") != SCHEMA:
            raise ValueError(f"catalog: expected schema {SCHEMA}")
        entries = document.get("bitmaps")
        if not isinstance(entries, list) or not entries:
            raise ValueError("catalog: expected a non-empty bitmap list")
        if len(entries) > rvtfile.CATALOG_MAX:
            raise ValueError(f"catalog: more than {rvtfile.CATALOG_MAX} bitmaps")
        self.assets = entries
        self.firmware = document.get("firmware", {})
        runtime = (document.get("runtime_base"), document.get("runtime_file_offset"))
        if not all(isinstance(value, int) for value in runtime):
            raise ValueError("catalog: expected runtime_base and runtime_file_offset")
        self.runtime_base, self.runtime_file_offset = runtime
        self.by_id: dict[int, int] = {}
        self.by_name: dict[str, list[int]] = {}
        for index, asset in enumerate(entries):
            if tuple(sorted(asset)) != tuple(sorted(ENTRY_KEYS)):
                raise ValueError(f"catalog: bitmap {index} has unexpected keys")
            if asset["address"] != address(asset["offset"], *runtime):
                raise ValueError(f"catalog: bitmap {asset['id']:#010x} address")
            if asset["id"] in self.by_id:
                raise ValueError(f"catalog: duplicate bitmap id {asset['id']:#010x}")
            self.by_id[asset["id"]] = index
            self.by_name.setdefault(asset["name"], []).append(index)
        self.fingerprint = fingerprint(entries)
        stored = document.get("fingerprint")
        if stored is not None and stored != self.fingerprint.hex():
            raise ValueError("catalog: stored fingerprint does not match the bitmaps")

    def resolve(self, reference: str, where: str) -> int:
        """Index of a bitmap named by catalog name or hex id."""
        if is_hex_id(reference):
            value = int(reference, 16)
            if value not in self.by_id:
                raise ValueError(f"{where}: {value:#010x} is not a catalog bitmap")
            return self.by_id[value]
        matches = self.by_name.get(reference)
        if not matches:
            raise ValueError(f"{where}: {reference!r} is not a catalog bitmap name")
        if len(matches) > 1:
            ids = ", ".join(f"{self.assets[i]['id']:#010x}" for i in matches)
            raise ValueError(f"{where}: {reference!r} is ambiguous; use one of {ids}")
        return matches[0]

    def payload_bytes(self, index: int) -> int:
        asset = self.assets[index]
        return asset["bytes"] - asset["data_offset"]

    def max_body(self) -> int:
        """Largest valid body: the style prefix plus one record per bitmap."""
        return rvtfile.STYLE_BYTES + sum(
            rvtfile.RECORD_BYTES + payload_max(asset) for asset in self.assets
        )


def entries(info: Entry) -> int:
    """Colour slots a recolour can touch: palette entries or pixels."""
    return info["palette_colors"] or info["width"] * info["height"]


def payload_max(info: Entry) -> int:
    """The largest padded payload any record kind allows for a bitmap."""
    pixels = info["bytes"] - info["data_offset"]
    pairs = min(rvtfile.RECOLOR_MAX, entries(info))
    return max(
        rvtfile.align(pixels),
        rvtfile.align(4 + pairs * rvtfile.PAIR.size),
        rvtfile.RELIGHT_BYTES,
    )


def load(path: Path | None = None) -> Catalog:
    source = DEFAULT if path is None else Path(path)
    return Catalog(json.loads(source.read_text()))
