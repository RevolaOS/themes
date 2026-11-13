#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write docs/extension-bitmaps.md: the bitmaps of the first-party extensions
a theme can replace, from the vendored extension asset catalog
rvt/data/extensions.json."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rvt import assets  # noqa: E402

PAGE = ROOT / "docs" / "extension-bitmaps.md"
HEAD = """# Extension bitmaps

The bitmaps of the first-party extensions, which a theme replaces with
`<appearance>/extensions/<id>/<asset>.png`, or `<appearance>/revola/<asset>.png`
for the core's own, as [Authoring](authoring.md#extension-bitmaps) describes.
Id is the extension's id, Asset the asset's name in its manifest; the compiler
keys the art by both. Size is width x height in pixels, which the art must
match; Format the native format the extension ships; Palette its palette
entries, none for masks and BGRA; Menu says whether it is a Settings icon, a
78 x 121 coverage mask drawn in the icon tint. The core's assets are owned by
the id `revola`.

The same list is `rvt catalog list --extensions`; `rvt catalog show <id>/<asset>`
prints every field of one bitmap. The catalog and how it is regenerated are in
[Catalog](catalog.md#extension-asset-catalog).

Regenerate this page with `python3 tools/extension_bitmaps_doc.py`.
"""


def page(records: dict[tuple[str, str], dict]) -> str:
    lines = [
        HEAD,
        "| Id | Asset | Size | Format | Palette | Menu |",
        "|---|---|---|---|---|---|",
    ]
    for (identifier, asset), record in sorted(records.items()):
        fmt = assets.FORMAT_NAMES.get(record["format"], f"{record['format']:#x}")
        lines.append(
            f"| `{identifier}` | `{asset}` | {record['width']}x{record['height']} | "
            f"{fmt} | {record['palette_colors'] or '-'} | "
            f"{'yes' if record['menu'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def current() -> str:
    """The page as the generator writes it today."""
    return page(assets.load_catalog())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=PAGE)
    args = parser.parse_args(argv)
    args.out.write_text(current())
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
