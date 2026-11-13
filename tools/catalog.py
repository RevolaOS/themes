#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write rvt/data/osos-2.0.5.json from a RepriseOS firmware/bitmaps.json.

Entries marked "source": "payload" are RepriseOS's own glyphs, not Apple's,
and are dropped. TODO: walk the resource index of osos.bin directly instead
of converting bitmaps.json.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rvt import catalog  # noqa: E402

FIRMWARE = {
    "file": "osos.bin",
    "version": "2.0.5",
    "bytes": 10634496,
    "sha256": "660eb6ff5f498bb1a75e85f1f9921bf0c753525a8bca9b4fa47ed260e5ad0f1e",
}
# Apple loads osos.bin at RUNTIME_BASE with the file's first
# RUNTIME_FILE_OFFSET bytes stripped (OSOS_RUNTIME_FILE_OFFSET in the core).
RUNTIME_BASE = 0x08000000
RUNTIME_FILE_OFFSET = 0xB798


def convert(document):
    if document.get("schema") != 1 or document.get("input") != {
        "bytes": FIRMWARE["bytes"],
        "sha256": FIRMWARE["sha256"],
    }:
        raise ValueError("expected bitmaps.json for the pinned 2.0.5 osos.bin")
    entries = []
    for asset in document["bitmaps"]:
        if asset.get("source") == "payload":
            continue
        entry = {key: asset[key] for key in catalog.ENTRY_KEYS if key != "address"}
        entry["address"] = catalog.address(
            entry["offset"], RUNTIME_BASE, RUNTIME_FILE_OFFSET
        )
        entries.append(entry)
    return {
        "schema": catalog.SCHEMA,
        "firmware": FIRMWARE,
        "runtime_base": RUNTIME_BASE,
        "runtime_file_offset": RUNTIME_FILE_OFFSET,
        "fingerprint": catalog.fingerprint(entries).hex(),
        "bitmaps": entries,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("bitmaps", type=Path, help="RepriseOS firmware/bitmaps.json")
    parser.add_argument("--out", type=Path, default=Path(str(catalog.DEFAULT)))
    args = parser.parse_args(argv)
    try:
        document = convert(json.loads(args.bitmaps.read_text()))
        catalog.Catalog(document)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    args.out.write_text(json.dumps(document, indent=1) + "\n")
    print(f"{len(document['bitmaps'])} bitmaps, fingerprint {document['fingerprint']}")


if __name__ == "__main__":
    main()
