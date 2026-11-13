# Catalog

The compiler ships two catalogs: Apple's bitmaps in `rvt/data/osos-2.0.5.json`, and the bitmaps of the first-party extensions in `rvt/data/extensions.json`, the extension asset catalog ([below](#extension-asset-catalog)).

## Apple's bitmaps

`rvt/data/osos-2.0.5.json` lists every `BMap` bitmap of Apple's 2.0.5 firmware that a theme can replace. An appearance's records and tint bytes refer to bitmaps by their index in this list, so the compiler and the appearance extension must agree on it; the fingerprint in every `.rvt` header makes a mismatch a refusal instead of wrong art.

The catalog records names, sizes, offsets and checksums. It never contains pixels.

### Fields

| Field | Contents |
|---|---|
| `schema` | 1 |
| `firmware` | File name, version, byte count and SHA-256 of the decrypted `osos.bin` the offsets refer to |
| `runtime_base`, `runtime_file_offset` | How a file offset becomes an address, below |
| `fingerprint` | The fingerprint of `bitmaps`, below |
| `bitmaps` | The entries, in firmware order |

Each entry:

| Key | Contents |
|---|---|
| `id` | Resource id |
| `name` | Resource name, what `theme.toml` and the art files use |
| `offset` | File offset of the bitmap header in `osos.bin` |
| `address` | Where the bitmap lives at run time |
| `bytes` | Bitmap size including its header |
| `format`, `depth` | Native pixel format and bits per pixel: 4 and 8 are masks, 0x64 and 0x65 are paletted, 0x565 is RGB565, 0x1888 is BGRA8888 |
| `width`, `height`, `stride` | Pixel size and row bytes |
| `data_offset` | Where a theme record starts: after the header and, for paletted formats, the colour count |
| `pixels_offset` | Where the rows start, after any palette |
| `palette_colors` | Palette entries, 0 for formats without one |
| `crc32` | CRC-32 of the whole bitmap, for checking the firmware the theme is applied to |

### Addresses

Apple loads `osos.bin` at `0x08000000` with the file's first `0xb798` bytes stripped (`OSOS_RUNTIME_FILE_OFFSET` in the core), so

```
address = runtime_base + offset - runtime_file_offset
```

### Fingerprint

The first 8 bytes of the SHA-256 of the entry list serialised as JSON with sorted keys and no whitespace. `rvt.catalog.fingerprint` computes it; the catalog file stores it for readers that do not want to.

### Browsing

`rvt catalog list` prints one line per bitmap (`--group` for a name prefix, `--format` for one native format); `rvt catalog show <Name>` prints every field of one bitmap. [Bitmaps](bitmaps.md) is the same list as a page, grouped by name prefix, with a column for where each bitmap appears.

### Regenerating

```sh
python3 tools/catalog.py /path/to/bitmaps.json
```

converts a RepriseOS `firmware/bitmaps.json` for the pinned firmware into `rvt/data/osos-2.0.5.json`, dropping its own glyphs (`"source": "payload"`). The Appearance extension vendors the file; a regenerated catalog changes the fingerprint and every theme must be recompiled. TODO: a resource-index walker over `osos.bin` that needs no RepriseOS file.

## Extension asset catalog

`rvt/data/extensions.json` lists every bitmap of the first-party extensions and of the core, one JSON object per line, sorted by id then asset: what a theme's `extensions/<id>/<asset>.png` or `revola/<asset>.png` must match. The compiler does not need it to key the art (the pack stores hashes of the names) but uses it to check the art's size, to tell a Settings icon from a picture and to name bitmaps in `rvt inspect`. A bitmap that is not in it compiles only as a 78 x 121 Settings icon, with a warning. `--extension assets.json` on `compile`, `check`, `inspect` and `catalog` adds the bitmaps of another extension; its author prints the file from the built package with the SDK's catalog tool:

```sh
python3 <sdk>/assets.py manifest.toml build/<id>.rvx > assets.json
```

A later record for the same id and asset replaces an earlier one.

| Key | Contents |
|---|---|
| `id` | The extension's id; `revola` is the core |
| `asset` | The asset's name in the manifest |
| `menu` | `true` for a Settings icon (`menu = true` in the manifest): a 78 x 121 coverage mask |
| `format`, `depth` | The BMap format word and bits per pixel as the extension ships it: 8 Mask8, 0x64 Indexed8, 0x1888 BGRA8888 |
| `width`, `height`, `stride` | Pixel size and row bytes |
| `palette_colors` | Palette entries, 0 without one |
| `bytes` | The decoded BMap, header included |
| `resident` | Whether the extension keeps it in RAM |

`rvt catalog list --extensions [--group <id>]` prints one line per bitmap; `rvt catalog show <id>/<asset>` every field and the two hashes. [Extension bitmaps](extension-bitmaps.md) is the same list as a page.

### Regenerating

`make` in the `extensions` repository writes `dist/assets.json`, the core's record from the SDK (`assets.json` beside `rvx-pack`) plus `assets.py <manifest.toml> <file.rvx>` for every built extension. Then, in this repository:

```sh
python3 tools/extensions_catalog.py ../extensions/dist/assets.json   # rvt/data/extensions.json, by id then asset
python3 tools/extension_bitmaps_doc.py                                # docs/extension-bitmaps.md
```

The file is pinned like Apple's catalog: it changes when an extension adds, removes or resizes a bitmap asset, and the committed page must equal the generator's output (`tests/test_assets.py`).
