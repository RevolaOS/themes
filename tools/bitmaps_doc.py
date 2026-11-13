#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write docs/bitmaps.md, the catalog as a page: every bitmap a theme can
replace, grouped by name prefix, with its size, format, palette size and
whether it can be tinted. The "Appears" column is written by hand; the
generator keeps what the committed page says."""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rvt import bitmaps, catalog  # noqa: E402

PAGE = ROOT / "docs" / "bitmaps.md"
# Prefixes with fewer bitmaps than this share the Other group.
GROUP_MINIMUM = 4
OTHER = "Other"
ROW = re.compile(r"\| `([^`]+)` \| [^|]* \| [^|]* \| [^|]* \| [^|]* \| ([^|]*) \|")
HEAD = """# Bitmaps

Every bitmap of Apple's 2.0.5 firmware a theme can replace, from the
[catalog](catalog.md) `rvt/data/osos-2.0.5.json`, grouped by the part of the
name before the first underscore (`No_Content` counts as one). Size is width x height in pixels; Palette is
the native palette's entries, none for masks, RGB565 and BGRA8888; Tintable
says whether `[<appearance>.tint]` may name it (masks, paletted and BGRA8888
bitmaps yes, RGB565 no). Appears says where the iPod draws it and is filled in by hand.

Regenerate with `python3 tools/bitmaps_doc.py`; the Appears column survives.
"""


def group_of(name: str) -> str:
    """The name's first word; a leading No_ belongs to the next word."""
    parts = name.split("_", 2)
    if parts[0] == "No" and len(parts) > 1:
        return "_".join(parts[:2])
    return parts[0]


def natural(name: str) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def groups(assets: list) -> dict[str, list]:
    """Prefix -> bitmaps, small prefixes merged into Other, Other last."""
    by_prefix: dict[str, list] = {}
    for asset in assets:
        by_prefix.setdefault(group_of(asset["name"]), []).append(asset)
    result = {}
    other = []
    for prefix in sorted(by_prefix):
        if len(by_prefix[prefix]) < GROUP_MINIMUM:
            other += by_prefix[prefix]
        else:
            result[prefix] = by_prefix[prefix]
    if other:
        result[OTHER] = other
    return result


def appears_from(text: str) -> dict[str, str]:
    """Name -> the Appears cell of an existing page."""
    return {name: cell.strip() for name, cell in ROW.findall(text)}


def page(assets: list, appears: dict[str, str]) -> str:
    lines = [HEAD]
    for group, members in groups(assets).items():
        lines += [
            f"## {group}",
            "",
            "| Name | Size | Format | Palette | Tintable | Appears |",
            "|---|---|---|---|---|---|",
        ]
        for asset in sorted(members, key=lambda a: natural(a["name"])):
            palette = asset["palette_colors"] or "-"
            tintable = "yes" if bitmaps.tint_kind(asset["format"]) else "no"
            lines.append(
                f"| `{asset['name']}` | {asset['width']}x{asset['height']} | "
                f"{catalog.FORMAT_NAMES[asset['format']]} | {palette} | {tintable} | "
                f"{appears.get(asset['name'], '')} |"
            )
        lines.append("")
    return "\n".join(lines)


def current(path: Path = PAGE) -> str:
    """The page as the generator writes it today."""
    assets = catalog.load(None).assets
    existing = appears_from(path.read_text()) if path.is_file() else {}
    return page(assets, existing)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=PAGE)
    args = parser.parse_args(argv)
    args.out.write_text(current(args.out))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
