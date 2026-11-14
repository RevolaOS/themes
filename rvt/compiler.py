# SPDX-License-Identifier: GPL-3.0-only
"""Compile a theme folder (theme.toml, light/, dark/) into <id>.rvt.

An appearance folder holds `apple/`, a PNG or TOML per catalog bitmap,
`extensions/<id>/<asset>.png`, the bitmap assets of extensions, and
`revola/<asset>.png`, the core's own.

Everything is checked and built in memory, the result is read back through the
inspector, and only then are <id>.rvt and report.json written.
"""

import json
import re
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from rvt import assets, bitmaps, derive, inspector, lz, rvtfile, style, theme
from rvt.catalog import Catalog, Entry
from rvt.derive import Rule
from rvt.errors import fail

FILE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._ -]{0,127}")
APPLE = "apple"
FOLDERS = (APPLE, assets.CORE_FOLDER, assets.FOLDER)


@dataclass
class Build:
    """A compiled theme: the file, the report, the inspector's description of
    the file, the warnings `rvt check` prints and `--strict` rejects, the
    notes about rule matches, and the payloads the compiler derived from the
    other appearance (appearance -> name -> bytes from the bitmap's data
    offset), which themes/flat/render.py --check compares its art against."""

    data: bytes
    report: dict
    inspection: dict
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    resolved: dict[str, dict[str, bytes]] = field(default_factory=dict)


def check_layout(folder: Path, appearance: str) -> None:
    """An appearance folder holds only apple/, revola/ and extensions/."""
    directory = Path(folder) / appearance
    if not directory.is_dir():
        return
    for path in sorted(directory.iterdir()):
        if path.name.startswith(".") or (path.is_dir() and path.name in FOLDERS):
            continue
        fail(
            f"{appearance}/{path.name}",
            f"catalog art goes in {appearance}/{APPLE}/, extension bitmaps in "
            f"{appearance}/{assets.FOLDER}/<extension-id>/, the core's in "
            f"{appearance}/{assets.CORE_FOLDER}/",
        )


def has_art(folder: Path, appearance: str) -> bool:
    return any(
        path.is_file() and not path.name.startswith(".")
        for path in (Path(folder) / appearance).rglob("*")
    )


def find_sources(folder: Path, appearance: str, catalog: Catalog) -> dict:
    """Catalog index -> ("png" | "toml", path) for every file in the
    appearance's apple/ folder: a PNG replaces the bitmap, a TOML derives it."""
    root = Path(folder).resolve()
    directory = root / appearance / APPLE
    found = {}
    if not directory.is_dir():
        return found
    for path in sorted(directory.iterdir()):
        where = f"{appearance}/{APPLE}/{path.name}"
        if path.name.startswith("."):
            continue
        if path.suffix not in (".png", ".toml") or not FILE_NAME.fullmatch(path.name):
            fail(where, "expected <CatalogName>.png, <CatalogName>.toml or 0x<id>.png")
        limit = assets.PNG_LIMIT if path.suffix == ".png" else theme.TOML_LIMIT
        resolved = assets.source_file(path, root, where, limit)
        index = catalog.resolve(path.stem, where)
        if index in found:
            fail(where, f"duplicate replacement for {catalog.assets[index]['name']}")
        found[index] = (path.suffix[1:], resolved)
    return found


def pixel_payload(
    info: Entry, path: Path, where: str, tint: bool, icon: str
) -> tuple[bytes, int | None]:
    """The native payload of a PNG replacement, and the number of distinct
    colours (coverage levels for tinted art) when it exceeded the palette and
    was reduced. Tinted art is stored in `icon`, the placeholder the iPod
    rewrites."""
    kind = bitmaps.tint_kind(info["format"]) if tint else None
    capacity = info["palette_colors"]
    reduced = None
    try:
        width, height, rgba = bitmaps.read_png(path.read_bytes())
        if kind == "mask":
            rgba = bitmaps.gray_pixels(bitmaps.coverage(rgba))
        elif kind:
            levels = bitmaps.coverage(rgba)
            if capacity and len(set(levels)) > capacity:
                reduced = len(set(levels))
                levels = bitmaps.fit_levels(levels, capacity)
            rgba = bitmaps.tinted_pixels(levels, icon)
        elif capacity and bitmaps.distinct(rgba) > capacity:
            reduced = bitmaps.distinct(rgba)
            rgba = bitmaps.fit_palette(rgba, capacity)
        payload = bitmaps.encode_pixels(info, width, height, rgba)
    except (KeyError, ValueError, zlib.error, struct.error) as error:
        fail(where, str(error) or type(error).__name__)
    if len(payload) != info["bytes"] - info["data_offset"]:
        fail(where, "native encoding changed the bitmap size")
    return payload, reduced


class Plan:
    """One appearance before its bytes: style, tints and records as
    index -> Rule, each with the text naming its origin."""

    def __init__(
        self,
        catalog: Catalog,
        folder: Path,
        appearance: str,
        table: dict,
        extensions: dict,
    ):
        self.catalog = catalog
        self.appearance = appearance
        self.warnings: list[str] = []
        self.notes: list[str] = []
        self.reduced: list[dict] = []
        self.resolved: dict[str, bytes] = {}
        check_layout(folder, appearance)
        sources = find_sources(folder, appearance, catalog)
        self.origin = {
            index: f"{appearance}/{APPLE}/{path.name}"
            for index, (_, path) in sources.items()
        }
        (self.colors, self.flags, self.palettes), self.report, warnings = (
            theme.resolve_style(appearance, table)
        )
        self.warnings += warnings
        self.tinted, self.tinted_bitmaps, warnings = theme.resolve_tints(
            table, appearance, catalog
        )
        self.warnings += warnings
        rules, owners, self.notes = theme.resolve_rules(
            table, appearance, catalog, sources
        )
        self.records: dict[int, Rule] = {}
        for index, (source, path) in sorted(sources.items()):
            info = catalog.assets[index]
            where = self.origin[index]
            if source == "png":
                payload, reduced = pixel_payload(
                    info, path, where, index in self.tinted, self.colors["icon_tint"]
                )
                if reduced is not None:
                    self.reduced.append(
                        {
                            "name": info["name"],
                            "colors": reduced,
                            "palette": info["palette_colors"],
                        }
                    )
                    self.warnings.append(
                        f"{where}: {reduced} colours reduced to the "
                        f"{info['palette_colors']} of its palette"
                    )
                self.records[index] = Rule("pixels", payload)
            else:
                self.records[index] = derive.load(path, index, catalog, where)
        for index, rule in rules.items():
            self.origin[index] = f"{appearance}.derive.{owners[index]!r}"
            self.records[index] = rule
        self.check_tints()
        self.bitmaps: dict[tuple[str, str], bytes] = {}
        sources = assets.find_sources(folder, appearance)
        for key, role in self.tinted_bitmaps.items():
            if key not in sources:
                fail(
                    f"{appearance}.tint.{role}",
                    f"{key[0]}/{key[1]} has no {assets.source_path(appearance, *key)}",
                )
        for key, path in sources.items():
            where = assets.source_path(appearance, *key)
            record = extensions.get(key)
            tint = self.tinted_bitmaps.get(key)
            self.bitmaps[key] = assets.encode(
                path, where, record, self.colors["icon_tint"] if tint else None
            )
            if record is None:
                self.warnings.append(
                    f"{where}: not in the extension asset catalog, compiled as a "
                    "Settings icon; docs/extension-bitmaps.md lists the first-party "
                    "bitmaps, --extension adds others"
                )
        if not self.flags & rvtfile.FLAGS["flat_icons"]:
            for key, bmap in self.bitmaps.items():
                if assets.is_menu(bmap) and not assets.has_reflection(bmap):
                    self.warnings.append(
                        f"{assets.source_path(appearance, *key)}: no reflection "
                        "below the art; draw one or set "
                        f"flat_icons = true in [{appearance}.rendering]"
                    )

    def name(self, index: int) -> str:
        return self.catalog.assets[index]["name"]

    def check_tints(self) -> None:
        """A tint needs stock art or a PNG, never a derivation; darkness
        coverage needs the stock art."""
        for index, (_, coverage) in self.tinted.items():
            record = self.records.get(index)
            if record is None:
                continue
            at = f"{self.appearance}.tint.{self.name(index)}"
            if record.kind != "pixels":
                fail(
                    at,
                    f"{self.name(index)} is derived by {self.origin[index]}; "
                    "a tint cannot be combined with a derivation",
                )
            if coverage != "alpha":
                fail(
                    f"{at}.coverage",
                    f"coverage needs stock art; remove {self.origin[index]}",
                )

    def resolve_from_other(self, other: "Plan | None") -> None:
        """Records starting from the theme's own art in the other appearance
        become pixels records computed here, as the iPod would compute them
        from that art. The art must be a PNG the other appearance does not
        tint, since a tinted PNG carries coverage, not colours."""
        for index, rule in sorted(self.records.items()):
            if not rule.from_other:
                continue
            where = f"{self.origin[index]}.from_other"
            if other is None:
                fail(where, "the theme has one appearance")
            target = rule.spec if rule.kind == "alias" else index
            name = self.name(target)
            base = other.records.get(target)
            if base is None:
                fail(where, f"{name} has no art in {other.appearance}/{APPLE}/")
            if base.kind != "pixels" or base.from_other:
                fail(
                    where,
                    f"{name} is derived in {other.appearance}/{APPLE}/; it must be a PNG",
                )
            if target in other.tinted:
                fail(where, f"{name} is tinted in {other.appearance}/{APPLE}/")
            try:
                result = derive.apply_record(
                    self.catalog, self.blank, index, rule.kind, rule.spec, {}, base.spec
                )
            except ValueError as error:
                fail(where, str(error))
            payload = result[self.catalog.assets[index]["data_offset"] :]
            self.records[index] = Rule("pixels", payload)
            self.resolved[self.name(index)] = payload

    def blank(self, index: int) -> bytes:
        """A bitmap of the right size whose header is never read."""
        return bytes(self.catalog.assets[index]["bytes"])

    def check_aliases(self) -> None:
        aliases = {
            index: rule.spec
            for index, rule in self.records.items()
            if rule.kind == "alias"
        }
        derive.check_aliases(
            aliases,
            self.tinted,
            self.name,
            lambda index: (
                self.appearance if index is None else f"{self.origin[index]}.source"
            ),
        )

    def body(self) -> bytes:
        """The pack body: style prefix, records and extension bitmaps, pixels
        and bitmap rows compressed when that is smaller."""
        body = bytearray(style.encode(*self.style_tuple(), self.tinted))
        counts: dict[str, int] = {}
        for index, rule in sorted(self.records.items()):
            kind, payload = rule.kind, derive.encode(rule.kind, rule.spec)
            if kind == "pixels":
                packed = lz.lz_encode(payload)
                if len(packed) < len(payload):
                    kind, payload = "pixels_lz", packed
            counts[kind] = counts.get(kind, 0) + 1
            body += rvtfile.RECORD.pack(index, rvtfile.KINDS.index(kind), len(payload))
            body += payload
            body += bytes(-len(body) % 4)
        if len(body) > self.catalog.max_body():
            fail(self.appearance, "exceeds the largest size the catalog allows")
        table, self.bitmap_count, bitmap_counts = assets.encode_table(
            self.bitmaps, self.tinted_bitmaps
        )
        body += table
        self.report["records"] = dict(sorted(counts.items()))
        self.report["extension_bitmaps"] = dict(sorted(bitmap_counts.items()))
        self.report["extension_tinted"] = {
            f"{identifier}/{asset}": role
            for (identifier, asset), role in sorted(self.tinted_bitmaps.items())
        }
        self.report["palette_reduced"] = self.reduced
        self.report["bytes"] = len(body)
        return bytes(body)

    def style_tuple(self) -> tuple:
        return self.colors, self.flags, self.palettes


def compile_theme(
    catalog: Catalog,
    folder: Path,
    allow_reserved: bool = False,
    strict: bool = False,
    extensions: dict | None = None,
) -> Build:
    """The .rvt bytes, report, warnings and notes of a theme folder; with
    strict, warnings are errors. `extensions` is the extension asset catalog
    ((id, asset) -> record), the vendored one when None. The built-in theme's
    packs carry art only: no rendering flags, no tints."""
    folder = Path(folder)
    if extensions is None:
        extensions = assets.load_catalog()
    document = theme.load(folder)
    reserved = document["id"] in theme.RESERVED_IDS
    if reserved and not allow_reserved:
        fail("id", f"{document['id']!r} is reserved for the built-in theme")
    for appearance in rvtfile.APPEARANCES:
        if appearance not in document and has_art(folder, appearance):
            fail(appearance, f"has art but theme.toml declares no [{appearance}]")
    plans = {
        appearance: Plan(catalog, folder, appearance, document[appearance], extensions)
        for appearance in rvtfile.APPEARANCES
        if appearance in document
    }
    for appearance, plan in plans.items():
        if reserved and (plan.flags or plan.tinted or plan.tinted_bitmaps):
            fail(appearance, "the built-in theme carries art only: no flags, no tints")
        others = [p for a, p in plans.items() if a != appearance]
        plan.resolve_from_other(others[0] if others else None)
    for plan in plans.values():
        plan.check_aliases()
    assets.check_collisions([key for plan in plans.values() for key in plan.bitmaps])
    packs = {
        a: (plan.body(), len(plan.records), plan.bitmap_count)
        for a, plan in plans.items()
    }
    report = {
        key: document[key]
        for key in ("id", "name", "author", "version")
        if key in document
    }
    report["appearances"] = {a: plan.report for a, plan in plans.items()}
    data = rvtfile.encode_file(
        catalog.fingerprint, document["id"], document["name"], packs
    )
    build = Build(
        data,
        report,
        inspector.inspect(data, catalog, assets.known_names(extensions)),
        [w for plan in plans.values() for w in plan.warnings],
        [n for plan in plans.values() for n in plan.notes],
        {a: plan.resolved for a, plan in plans.items()},
    )
    if strict and build.warnings:
        fail(
            "",
            "\n".join(
                [f"{len(build.warnings)} warnings with --strict:"] + build.warnings
            ),
        )
    return build


def write(
    catalog: Catalog,
    folder: Path,
    out: Path,
    allow_reserved: bool = False,
    strict: bool = False,
    extensions: dict | None = None,
) -> tuple[Path, Build]:
    """Compile and write <out>/<id>/<id>.rvt and report.json."""
    build = compile_theme(catalog, folder, allow_reserved, strict, extensions)
    directory = Path(out) / build.report["id"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{build.report['id']}.rvt"
    path.write_bytes(build.data)
    (directory / "report.json").write_text(
        json.dumps(build.report, indent=2, sort_keys=True) + "\n"
    )
    return path, build


def summary(result: dict, size: int) -> str:
    """One line per appearance for the console, from an inspect() result."""
    lines = [f"{result['id']}.rvt: {size:,} bytes"]
    for appearance, pack in result["appearances"].items():
        counts = inspector.counts(pack["records"])
        pixels = sum(counts.get(kind, 0) for kind in rvtfile.PIXEL_KINDS)
        derived = len(pack["records"]) - pixels
        lines.append(
            f"  {appearance}: {len(pack['records'])} bitmaps "
            f"({pixels} pixels, {derived} derived), "
            f"{len(pack['extension_bitmaps'])} extension bitmaps, "
            f"{pack['bytes']:,} bytes"
        )
    return "\n".join(lines)
