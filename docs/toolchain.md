# The compiler

`rvt` is a Python package without dependencies; Python 3.11 or later runs it from the repository root as `python3 -m rvt`, and `pip install .` installs it as the command `rvt` (`pip install -e .[dev]` adds Ruff). The two catalogs and the format header ship inside the package, so no command needs the firmware except `preview` and `recolor`.

## Commands

| Command | Does |
|---|---|
| `rvt new <id> [--name NAME]` | Writes `<id>/theme.toml` with every role and option as a comment, and the empty `apple/`, `revola/` and `extensions/` folders of `<id>/light/` and `<id>/dark/` |
| `rvt check <folder>` | Compiles without writing; prints what each derive rule matched, the warnings and a size table per appearance |
| `rvt compile <folder> [--out DIR]` | The same, then writes `<out>/<id>/<id>.rvt` and `report.json`; `--out` defaults to `dist` |
| `rvt inspect <file> [--json]` | Validates an `.rvt` against the catalog and describes it; extension bitmaps are named from the extension asset catalog, by their hashes when it does not know them |
| `rvt catalog list [--group PREFIX] [--format FMT]` | One line per Apple bitmap: name, size, format, palette entries, tintable |
| `rvt catalog list --extensions [--group ID] [--format FMT]` | One line per extension bitmap: id, asset, size, format, palette entries, menu or bitmap |
| `rvt catalog show <Name>` | Every catalog field of one Apple bitmap, by name or hex id |
| `rvt catalog show <id>/<asset>` | Every catalog field of one extension bitmap, and its two hashes |
| `rvt preview <folder> --firmware FILE` | Renders every derived bitmap of a theme from a decrypted `osos.bin` or the booted `revola.bin` to `dist/<id>/derived/` |
| `rvt recolor <png> --firmware FILE` | Turns `<theme>/<appearance>/apple/<Name>.png` into a `recolor` rule file when the PNG is a pure recolour of the stock bitmap |

`--strict` on `check`, `compile` and `preview` turns warnings into errors. `--catalog FILE` on every command but `new` uses a catalog other than the built-in one. `--extension assets.json`, repeatable on `check`, `compile`, `preview`, `inspect` and `catalog`, adds the bitmaps of an extension that is not in the built-in extension asset catalog, the file the SDK's `assets.py` prints for a built package ([Catalog](catalog.md#extension-asset-catalog)). `--allow-reserved` accepts the id `classic`, which only the built-in theme carries.

Warnings name a bitmap whose PNG has more colours than its native palette (reduced to fit; the count and the palette size are in `report.json` under `palette_reduced`), a text and background pair the theme colours that falls below 4.5:1 (once per pair, and once per accent for the pairs an accent changes), a tint glob that matches no bitmap, a Settings icon with nothing below its art box while `flat_icons` is off, and an extension bitmap the extension asset catalog does not list (compiled as a Settings icon).

`report.json` has the theme's id, name, author and version and, per appearance, the contrast of every text and background pair for Theme Default and each accent (`contrast`), the accents that use the built-in colours (`accents_builtin`), the record count per kind (`records`), the extension bitmap count per kind (`extension_bitmaps`), the palette reductions (`palette_reduced`) and the appearance's bytes. It is written with sorted keys and is the same for the same input.

## Layout

| Path | Contents |
|---|---|
| `rvt/rvtfile.py` | The `.rvt` header and packs; every constant parsed from `rvt/data/rvt.h` |
| `rvt/data/rvt.h` | The file format, vendored byte for byte by the Appearance extension |
| `rvt/data/` | The vendored contracts: the format header, the two catalogs and the SDK's bitmap encoder |
| `rvt/data/osos-2.0.5.json` | The [catalog](catalog.md) of Apple's bitmaps |
| `rvt/data/extensions.json` | The [extension asset catalog](catalog.md#extension-asset-catalog): the bitmaps of the first-party extensions |
| `rvt/data/bitmap.py` | The SDK's bitmap encoder, vendored byte for byte from `revola/tools/bitmap.py`; extension bitmaps are encoded with it |
| `rvt/catalog.py` | Catalog loading, lookup, the fingerprint |
| `rvt/theme.py` | `theme.toml`: validation and the resolution of colours, accents, tints and rules |
| `rvt/bitmaps.py` | PNG reading, palette fitting, the native pixel formats |
| `rvt/style.py` | The colours, rendering, accent palettes and tint bytes of an appearance; the Classic colours and the built-in accents |
| `rvt/derive.py` | Derivation rules, record payloads and the reference arithmetic of the iPod's derivations |
| `rvt/lz.py` | The core's lz codec |
| `rvt/assets.py` | Extension bitmaps: the `extensions/` and `revola/` folders, encoding with the SDK's encoder, the extension asset catalog and its `--extension` additions, the hashes and the table in the pack |
| `rvt/errors.py` | `fail`, the one error every check raises |
| `rvt/compiler.py`, `rvt/inspector.py` | Folder to bytes, bytes to a checked description |
| `rvt/firmware.py` | Stock bitmaps from a local firmware for `preview` and `recolor` |
| `rvt/cli.py` | The commands |
| `tests/` | Host tests against a synthetic catalog; a few compare against the sibling `extensions` and `revola` checkouts when present |
| `tools/catalog.py` | Catalog generation, see [Catalog](catalog.md) |
| `tools/bitmaps_doc.py` | Writes [Bitmaps](bitmaps.md) from the catalog |
| `tools/extensions_catalog.py` | Writes `rvt/data/extensions.json` from the extensions build's `dist/assets.json`, see [Catalog](catalog.md#extension-asset-catalog) |
| `tools/extension_bitmaps_doc.py` | Writes [Extension bitmaps](extension-bitmaps.md) from `rvt/data/extensions.json` |
| `themes/` | The first-party themes; `themes/flat/render.py` draws Flat's art and Settings icons, `themes/classic/batteries.py` Classic dark's idle battery frames |

## Tests

```sh
python3 -m unittest discover -s tests
ruff check . && ruff format --check .
```

The CI workflow runs both on Python 3.11 and 3.12 with the `revola` and `extensions` repositories checked out beside this one, so the tests that compare vendored files with their sources run there; without the siblings those tests skip. It then compiles Classic with `--strict` and Flat as it is.
