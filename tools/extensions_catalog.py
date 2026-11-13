#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write rvt/data/extensions.json from the `dist/assets.json` the extensions
build writes: every record checked, one per line with sorted keys, ordered by
id then asset so that diffs read."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rvt import assets  # noqa: E402


def convert(source: Path) -> str:
    records = sorted(assets.read_json(source), key=lambda r: (r["id"], r["asset"]))
    seen = set()
    for record in records:
        key = (record["id"], record["asset"])
        if key in seen:
            raise ValueError(f"{source}: {key[0]}/{key[1]} is listed twice")
        seen.add(key)
    return "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("assets", type=Path, help="extensions/dist/assets.json")
    parser.add_argument("--out", type=Path, default=Path(str(assets.CATALOG)))
    args = parser.parse_args(argv)
    try:
        args.out.write_text(convert(args.assets))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
