# SPDX-License-Identifier: GPL-3.0-only
"""theme.toml: loading, validation and the resolution of its tables into the
colours, flags, palettes, tints and rules the compiler encodes. docs/authoring.md
describes the file."""

import fnmatch
import re
import tomllib
from pathlib import Path

from rvt import assets, bitmaps, derive, rvtfile, style
from rvt.catalog import Catalog
from rvt.errors import fail

SCHEMA = 1
THEME_KEYS = {"schema", "id", "name", "author", "version", *rvtfile.APPEARANCES}
APPEARANCE_KEYS = {
    "colors",
    "accents",
    "menu_covers_default",
    "rendering",
    "tint",
    "derive",
}
# Rendering keys, each a boolean that is false by default, and the flag true
# sets.
RENDERING = {
    "flat_selection": "flat_selection",
    "flat_now_playing": "flat_now_playing",
    "flat_icons": "flat_icons",
}
# The Menu Covers setting a theme applies until the listener chooses one; off
# sets the flag.
MENU_COVERS_DEFAULT = "menu_covers_default"
# Named so authors get a precise answer instead of "unknown key".
UNSUPPORTED = {
    "fonts": "custom fonts",
    "layouts": "layout overrides",
    "metrics": "metric overrides",
    "animations": "animations",
    "sounds": "sounds",
    "strings": "string overrides",
    "wallpapers": "wallpapers",
}
# The built-in theme; classic.rvt carries its dark art and nothing else may.
RESERVED_IDS = ("classic",)
COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
GLOB_CHARS = set("*?[")
DARKNESS = "darkness_coverage"
SOLID = "solid_coverage"
COVERAGE_LISTS = {DARKNESS: "darkness", SOLID: "solid"}
TEXT_LIMIT = 64
TOML_LIMIT = 256 * 1024


def check_keys(table, allowed, where: str) -> None:
    if not isinstance(table, dict):
        fail(where, "expected a table")
    for key in sorted(table):
        at = f"{where}.{key}" if where else key
        if key in UNSUPPORTED:
            fail(at, f"unsupported capability: {UNSUPPORTED[key]} are not themeable")
        if key not in allowed:
            fail(at, "unknown key")


def color(value, where: str) -> str:
    if not isinstance(value, str) or not COLOR.fullmatch(value):
        fail(where, 'expected "#rrggbb"')
    return value.lower()


def load(folder: Path) -> dict:
    """The validated document; its appearance tables are resolved by the
    functions below."""
    path = Path(folder) / "theme.toml"
    if not path.is_file():
        fail(str(path), "not found")
    if path.stat().st_size > TOML_LIMIT:
        fail(path.name, f"exceeds {TOML_LIMIT:,} bytes")
    try:
        theme = tomllib.loads(path.read_bytes().decode("utf-8"))
    except UnicodeDecodeError:
        fail(path.name, "expected UTF-8")
    except tomllib.TOMLDecodeError as error:
        fail(path.name, f"invalid TOML: {error}")
    check_keys(theme, THEME_KEYS, "")
    for key in ("schema", "id", "name"):
        if key not in theme:
            fail(key, "required")
    if type(theme["schema"]) is not int or theme["schema"] != SCHEMA:
        fail("schema", f"unsupported schema {theme['schema']!r}; expected {SCHEMA}")
    rvtfile.check_id(theme["id"])
    rvtfile.check_name(theme["name"])
    for key in ("author", "version"):
        if key in theme:
            rvtfile.check_text(theme[key], key, TEXT_LIMIT)
    if not any(key in theme for key in rvtfile.APPEARANCES):
        fail("", "declare [light], [dark] or both")
    for key in rvtfile.APPEARANCES:
        if key in theme:
            check_keys(theme[key], APPEARANCE_KEYS, key)
    return theme


# Colours, accents and rendering


def resolve_style(appearance: str, table: dict) -> tuple[tuple, dict, list[str]]:
    """(colors, flags, palettes) of an appearance, its report, and warnings
    about text and background pairs the theme itself colours that fall below
    style.CONTRAST_MINIMUM; a pair no accent changes is warned about once.
    icon_tint left out follows accent_text."""
    where = appearance
    colors = table.get("colors", {})
    check_keys(colors, set(style.ROLES), f"{where}.colors")
    resolved = dict(style.COLOR_DEFAULTS[appearance])
    for role, value in colors.items():
        resolved[role] = color(value, f"{where}.colors.{role}")
    if "icon_tint" not in colors:
        resolved["icon_tint"] = resolved["accent_text"]

    overrides = table.get("accents", {})
    check_keys(overrides, set(style.ACCENTS), f"{where}.accents")
    palettes = {
        name: accent_palette(name, appearance, resolved, overrides.get(name), where)
        for name in style.ACCENTS
    }

    flags = 0
    covers = table.get(MENU_COVERS_DEFAULT, True)
    if not isinstance(covers, bool):
        fail(f"{where}.{MENU_COVERS_DEFAULT}", "expected true or false")
    if not covers:
        flags |= rvtfile.FLAGS["menu_covers_off"]
    rendering = table.get("rendering", {})
    if not isinstance(rendering, dict):
        fail(f"{where}.rendering", "expected a table")
    for key in sorted(rendering):
        at = f"{where}.rendering.{key}"
        if key not in RENDERING:
            fail(at, "unknown key")
        if not isinstance(rendering[key], bool):
            fail(at, "expected true or false")
        if rendering[key]:
            flags |= rvtfile.FLAGS[RENDERING[key]]

    report = {
        "contrast": style.contrast_report(resolved, palettes),
        "accents_builtin": [name for name in style.ACCENTS if name not in overrides],
    }
    warnings = []
    for pair in report["contrast"]:
        sides = {pair["foreground"], pair["background"]}
        if pair["accent"] != style.THEME_DEFAULT and not sides & set(
            style.ACCENT_SLOTS
        ):
            continue
        owned = pair["accent"] in overrides or any(
            pair[side] in colors for side in ("foreground", "background")
        )
        if owned and not pair["passes"]:
            warnings.append(
                f"{where}: {pair['foreground']} on {pair['background']} is "
                f"{pair['ratio']}:1 with accent {pair['accent']}; "
                f"{style.CONTRAST_MINIMUM}:1 is the minimum"
            )
    return (resolved, flags, palettes), report, warnings


def accent_palette(name, appearance, colors, override, where) -> dict:
    """One accent's palette: the built-in fill and text with the appearance's
    on_accent, then the override: one colour for fill, text, selection and
    icon tint, a table with `accent` and optionally `on_accent`, or a table of
    the five palette slots."""
    palette = style.accent_palette(name, appearance, colors)
    at = f"{where}.accents.{name}"
    if override is None:
        return palette
    if isinstance(override, str):
        override = {"accent": override}
    if not isinstance(override, dict):
        fail(at, 'expected "#rrggbb" or a table')
    if "accent" in override:
        check_keys(override, {"accent", "on_accent"}, at)
        one = color(override["accent"], f"{at}.accent")
        palette.update(accent_fill=one, accent_text=one, selection=one, icon_tint=one)
        if "on_accent" in override:
            palette["on_accent"] = color(override["on_accent"], f"{at}.on_accent")
        return palette
    check_keys(override, set(style.ACCENT_SLOTS), at)
    for slot, value in override.items():
        palette[slot] = color(value, f"{at}.{slot}")
    return palette


# Tints and rules


def is_glob(pattern: str) -> bool:
    return bool(GLOB_CHARS & set(pattern))


def matching(pattern: str, catalog: Catalog, where: str) -> list[int]:
    """Catalog indices a name, hex id or glob stands for; a name that is not
    in the catalog is an error, a glob may match nothing."""
    if not isinstance(pattern, str):
        fail(where, "expected a catalog name, hex id or glob")
    if not is_glob(pattern):
        return [catalog.resolve(pattern, where)]
    return [
        index
        for index, asset in enumerate(catalog.assets)
        if fnmatch.fnmatchcase(asset["name"], pattern)
    ]


def extension_key(pattern: str, where: str) -> tuple[str, str] | None:
    """(id, asset) when a tint entry names an extension bitmap as `id/asset`
    (the core's as `revola/asset`); None for a catalog name, hex id or glob,
    which never contain a slash."""
    if not isinstance(pattern, str) or "/" not in pattern:
        return None
    identifier, _, asset = pattern.partition("/")
    if not assets.ID_PATTERN.fullmatch(
        identifier
    ) or not assets.ASSET_PATTERN.fullmatch(asset):
        fail(where, f"{pattern!r} is not an extension bitmap <id>/<asset>")
    return identifier, asset


def resolve_tints(
    table: dict, appearance: str, catalog: Catalog
) -> tuple[dict[int, tuple[str, str]], dict[tuple[str, str], str], list[str]]:
    """Catalog index -> (role, coverage) and extension (id, asset) -> role from
    [<appearance>.tint], and warnings about globs that match nothing: role =
    [names or globs] per role, a `darkness_coverage` list naming tinted bitmaps
    whose coverage is their darkness and a `solid_coverage` list naming those
    whose coverage is full from the floor up. An extension bitmap is named
    `id/asset` and takes its coverage from its PNG's alpha only."""
    where = f"{appearance}.tint"
    tints = table.get("tint", {})
    if not isinstance(tints, dict):
        fail(where, "expected a table")
    tinted: dict[int, tuple[str, str]] = {}
    extensions: dict[tuple[str, str], str] = {}
    warnings: list[str] = []
    for role, patterns in tints.items():
        at = f"{where}.{role}"
        if role not in COVERAGE_LISTS and role not in style.ROLES:
            fail(at, f"expected one of {', '.join((*style.ROLES, *COVERAGE_LISTS))}")
        if not isinstance(patterns, list):
            fail(at, "expected a list of catalog names, hex ids or globs")
        for pattern in patterns:
            key = extension_key(pattern, at)
            if key is not None:
                if role in COVERAGE_LISTS:
                    fail(at, f"{pattern} takes its coverage from its PNG's alpha")
                if key in extensions:
                    fail(at, f"{pattern} is already tinted {extensions[key]}")
                extensions[key] = role
                continue
            found = matching(pattern, catalog, at)
            if not found:
                warnings.append(f"{at}: {pattern!r} matches no catalog bitmap")
            if role in COVERAGE_LISTS:
                continue
            for index in found:
                info = catalog.assets[index]
                if index in tinted:
                    fail(at, f"{info['name']} is already tinted {tinted[index][0]}")
                if bitmaps.tint_kind(info["format"]) is None:
                    fail(
                        at,
                        f"{info['name']} cannot be tinted: it has no palette or coverage",
                    )
                tinted[index] = (role, "alpha")
    for key, coverage in COVERAGE_LISTS.items():
        at = f"{where}.{key}"
        for pattern in tints.get(key, []):
            for index in matching(pattern, catalog, at):
                name = catalog.assets[index]["name"]
                if index not in tinted:
                    fail(at, f"{name} has no tint role")
                if tinted[index][1] == coverage:
                    fail(at, f"{name} is listed twice")
                if tinted[index][1] != "alpha":
                    fail(
                        at, f"{name} already takes its coverage from {tinted[index][1]}"
                    )
                tinted[index] = (tinted[index][0], coverage)
    return tinted, extensions, warnings


def resolve_rules(
    table: dict, appearance: str, catalog: Catalog, sources: dict
) -> tuple[dict[int, derive.Rule], dict[int, str], list[str]]:
    """Catalog index -> Rule from [<appearance>.derive], index -> the rule's
    pattern, and one note per rule saying how many bitmaps it matched. A rule
    matches by name, hex id or glob; it may not match nothing, a bitmap in
    `sources` (one with a PNG or a per-file TOML) or a bitmap of another
    rule."""
    where = f"{appearance}.derive"
    rules = table.get("derive", {})
    if not isinstance(rules, dict):
        fail(where, "expected a table of rules")
    resolved: dict[int, derive.Rule] = {}
    owner: dict[int, str] = {}
    notes = []
    for pattern, spec in rules.items():
        at = f"{where}.{pattern!r}"
        found = matching(pattern, catalog, at)
        if not found:
            fail(at, "matches no catalog bitmap")
        for index in found:
            name = catalog.assets[index]["name"]
            if index in sources:
                fail(at, f"matches {name}, which has {sources[index][1].name}")
            if index in owner:
                fail(at, f"matches {name}, which {owner[index]!r} matches too")
            owner[index] = pattern
        for index in found:
            resolved[index] = derive.rule(spec, index, catalog, at)
        notes.append(
            f"{at} matches {len(found)} bitmap{'s' if len(found) != 1 else ''}"
        )
    return resolved, owner, notes


# rvt new


def template(identifier: str, name: str) -> str:
    """A theme.toml with every role and option present as a comment."""
    out = [
        "schema = 1",
        f'id = "{identifier}"',
        f'name = "{name}"',
        '# author = ""',
        '# version = "1.0"',
        "",
        "# Art goes beside this file: <appearance>/apple/<CatalogName>.png or",
        "# .toml for Apple's bitmaps, <appearance>/extensions/<extension-id>/",
        "# <asset>.png for the bitmaps of extensions (rvt catalog list",
        "# --extensions), <appearance>/revola/<asset>.png for the core's own.",
    ]
    for appearance in rvtfile.APPEARANCES:
        defaults = style.COLOR_DEFAULTS[appearance]
        out += [
            "",
            f"# {appearance.capitalize()} appearance; drop the table to leave it out.",
            f"[{appearance}]",
            f"# {MENU_COVERS_DEFAULT} = true  # Menu Covers until the listener chooses",
            "",
            "# Roles left out keep the Classic colours shown.",
            f"[{appearance}.colors]",
        ]
        out += [
            f'# {role} = "{value}"'
            + ("  # left out, it follows accent_text" if role == "icon_tint" else "")
            for role, value in defaults.items()
        ]
        out += [
            "",
            "# Accents the listener can pick. One colour fills accent_fill,",
            "# accent_text, selection and icon_tint; on_accent comes from the",
            "# colours above. Accents left out use the built-in fill and text.",
            f"[{appearance}.accents]",
        ]
        for accent in style.ACCENTS:
            fill, _ = style.accent_builtin(accent, appearance)
            out.append(f'# {accent} = "{fill}"')
        out += [
            '# yellow = { accent = "#ffcc00", on_accent = "#000000" }',
            "",
            f"[{appearance}.rendering]",
            "# flat_selection = false   # true: the selection bar is one flat colour",
            "# flat_now_playing = false # true: face-on cover art, no reflection",
            "# flat_icons = false       # true: extension icons this theme does not",
            "#                          # replace lose their reflection",
            "",
            "# Bitmaps the iPod draws in one live colour, by role; globs allowed.",
            f"[{appearance}.tint]",
        ]
        out += [f"# {role} = []" for role in style.ROLES]
        out += [
            f"# {DARKNESS} = []   # coverage from darkness, stock art only",
            f"# {SOLID} = []      # coverage full from the floor up, stock art only",
            "",
            "# Rules that derive bitmaps from the stock art or, with",
            "# from_other = true, from this theme's own PNG in the other appearance.",
            f"[{appearance}.derive]",
            '# "Settings_Brightness_Image" = { kind = "invert" }',
            '# "Clock_*_Image_*" = { kind = "alias", from_other = true }',
        ]
    return "\n".join(out) + "\n"
