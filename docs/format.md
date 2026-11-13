# File format

A theme is one file, `/Revola/Themes/<id>.rvt`: a header, then an appearance pack for light and one for dark, either optional. [`rvt/data/rvt.h`](../rvt/data/rvt.h) is the contract; the appearance extension vendors it byte for byte and `rvt/rvtfile.py` parses every `RVT_*` value and enum order from it. All integers are little-endian.

## Header

The offsets are the `RVT_HEADER_*` defines.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `"RVT0"` |
| 4 | u16 | Version, `RVT_VERSION` (2); a reader accepts exactly this value |
| 6 | u16 | Header bytes, where the packs begin |
| 8 | 8 | Catalog fingerprint, see [Catalog](catalog.md) |
| 16 | u32 | Appearances present: `RVT_APPEARANCE_LIGHT`, `RVT_APPEARANCE_DARK` |
| 20 | u32 x 4 | Light offset and bytes, dark offset and bytes; 0 when absent |
| 36 | u32 | CRC-32 of the first `RVT_HEADER_BYTES` (128) bytes with this word as zero |
| 40 | 32 | Id, `[a-z0-9][a-z0-9_-]{0,30}`, NUL-padded; the file's stem |
| 72 | 48 | Name, UTF-8, NUL-padded |
| 120 | 8 | Zero, up to `RVT_HEADER_BYTES`; a reader does not check them |

The light pack starts at the header bytes; the dark pack follows it, 4-byte aligned. A pack's bytes count its header and body. A reader places the packs by the header bytes field, never by the constant: a header longer than `RVT_HEADER_BYTES` belongs to a later layout of the same version, and the reader uses the fields it knows and skips the rest. The CRC covers the first 128 bytes only, also when the header bytes field is larger.

## Pack

The offsets are the `RVT_PACK_*` defines.

| Offset | Size | Field |
|---|---|---|
| 0 | u32 | Body bytes, at least `RVT_STYLE_BYTES` |
| 4 | u32 | Record count |
| 8 | u32 | CRC-32 of the body |
| 12 | u32 | Extension bitmap count, at most `RVT_EXTENSION_BITMAPS_MAX` (64) |
| 16 | | Body: the style prefix, the records, then the extension bitmaps |

A pack is at least `RVT_PACK_HEADER_BYTES` (16) plus `RVT_STYLE_BYTES` long.

## Style prefix

`RVT_STYLE_BYTES` (856), at the `RVT_STYLE_*` offsets. Every colour is R, G, B, A with A = 255.

| Offset | Size | Field |
|---|---|---|
| 0 | 8 x 4 | Colour roles in `enum rvt_role` order: background, text, accent fill, accent text, on accent, selection, cover border, icon tint |
| 32 | u32 | Rendering flags: `RVT_FLAG_FLAT_SELECTION`, `RVT_FLAG_MENU_COVERS_OFF`, `RVT_FLAG_FLAT_NOW_PLAYING`, `RVT_FLAG_FLAT_ICONS` |
| 36 | 9 x 5 x 4 | One palette per accent in `enum rvt_accent` order, each in `enum rvt_accent_slot` order: accent fill, accent text, selection, on accent, icon tint; a slot replaces the role of its name while that accent is picked |
| 216 | `RVT_CATALOG_MAX` | One tint byte per catalog index: `RVT_TINT_NONE`, or `RVT_TINT_ROLE` plus an `rvt_role`, or-ed with `RVT_TINT_DARKNESS` when the coverage comes from darkness or with `RVT_TINT_SOLID` when every level from `RVT_SOLID_FLOOR` up is full, never both. A reader packs the roles two per byte, so `RVT_TINT_ROLE + RVT_ROLES` stays at most 16 |

## Records

Records follow in ascending catalog index, each index at most once:

| Size | Field |
|---|---|
| u32 | Catalog index |
| u32 | Kind, `enum rvt_kind` |
| u32 | Payload bytes |
| bytes | Payload, zero-padded to 4 |

| Kind | Payload | The iPod writes |
|---|---|---|
| `pixels` | The native bytes from `data_offset` to the end: palette and rows | them in place |
| `pixels_lz` | The same bytes as an lz stream; the payload bytes are the stream's size | them in place while decoding |
| `recolor` | u32 count, then count × (`from` RGBA, `to` RGBA), strictly ascending by `from` as a little-endian u32, no `from` equal to its `to`; count 1..`RVT_RECOLOR_MAX` | each palette entry, BGRA8888 pixel or RGB565 word equal to a `from` as its `to` |
| `alias` | u32 source catalog index | the source's bytes after its header when the layouts are equal, else its pixels re-encoded in this bitmap's format; after every other record of the pack |
| `invert` | none | RGB inverted, alpha kept |
| `relight` | `RVT_RELIGHT_WORDS` × i32, 8.8 fixed point, `enum rvt_relight` order | grays per [Relight](#relight) below, a palette of the distinct grays in ascending order with zeros after it, and the rows re-indexed |

The two pixel kinds replace the stock bytes; every other kind is computed from them, so the iPod restores a bitmap from its firmware before deriving it. The compiler writes `pixels_lz` whenever the stream is smaller than the raw bytes and `pixels` otherwise.

**lz stream.** The bit layout is the RevolaOS core's, defined in `revola/core/loader/rvx.h` and summarised in `rvt.h`: groups of a flag byte and up to 8 items, bit 0 first; a clear bit is a literal byte; a set bit is a two-byte match `LLLLDDDD DDDDDDDD` copying L + 3 bytes from D + 1 bytes back in the output, L = 15 adding the following bytes to the length while they are 255 and the first that is not. Matches copy from the output itself, so a decoder needs no window buffer. The stream carries no length: a decoder stops when it has produced the bitmap's bytes (its catalog size minus `data_offset`) and the stream must end exactly at the record's end; a stream that ends early, runs past the output or copies from before the output's start makes the record invalid. The palette-index check and the pack CRC apply to the stored bytes as read, so a reader can decode straight into the bitmap.

A tint byte on a paletted or BGRA8888 catalog bitmap without a record tints the stock bitmap, with the coverage its `RVT_TINT_DARKNESS` or `RVT_TINT_SOLID` bit names; with a pixel record the coverage is the record's alpha; a tint byte on a derived bitmap is invalid. A tint byte on a mask bitmap needs no record and leaves the stock levels alone unless it carries `RVT_TINT_SOLID`, which rewrites them (a 4-bit level counts as level x 17); RGB565 bitmaps take no tint. `recolor` on RGB565 uses opaque, 5-6-5-exact colours; `invert` and `alias` are not for masks; `relight` needs a paletted bitmap of at most `RVT_SCRATCH_PIXELS` pixels with a palette of at least `icon_hi − bg_lo + 1` entries. At most `RVT_ALIASES_MAX` aliases per pack; an alias source is neither an alias nor tinted. An alias between equal layouts is a byte copy; between differing layouts the source's pixels are re-encoded, which the iPod does for bitmaps of at most `RVT_SCRATCH_PIXELS` pixels, and an alias into a paletted bitmap fails on the iPod when the source has more distinct colours than the palette holds, and the stock bitmap stays.

## Relight

Every word is 8.8 fixed point; `luma = (77 r + 150 g + 29 b) >> 8`. The iPod accepts `0 <= t_zero < t_full <= 255`, `0 <= bg_lo <= bg_hi <= icon_lo <= icon_hi <= 255`, `|bg_base|` and `|icon_base|` at most 1024, `|bg_ref|`, `|icon_luma|` and `|icon_row|` at most 255 and `|bg_slope|` at most 16, all in pixel units before the 8.8 scaling, and rejects the record otherwise.

For each row, the stock pixel in column 0 is the background `bg`. A pixel's offset `o` is its largest channel difference from `bg`; `t = clamp((o - t_zero) / (t_full - t_zero), 0, 1)` says how much of the pixel is icon, and a pixel with `0 < t < 1` and no 8-neighbour at `t = 1` is a drop shadow and takes `t = 0`. The row's background gray is `bg_dark = clamp(bg_base + (luma(bg) - bg_ref) * bg_slope, bg_lo, bg_hi)`; the pixel's icon gray is `icon_dark = clamp(icon_base + icon_luma * luma(c) + icon_row * y, icon_lo, icon_hi)`; the result is `bg_dark + (icon_dark - bg_dark) * t`, rounded, opaque. The palette becomes the distinct grays in ascending order with zeros after them, and the rows are re-indexed. `rvt.derive` is the reference arithmetic; the iPod's division must match it byte for byte.

Art a theme derives from its own PNG in the other appearance (`from_other` in [Authoring](authoring.md)) is computed by the compiler and stored as a pixel record; the file never refers from one pack into the other.

## Extension bitmaps

After the pack's last record come its extension bitmaps, the bitmaps of RevolaOS extensions the theme replaces ([Authoring](authoring.md#extension-bitmaps)), ascending by owner then asset, each pair at most once, at most `RVT_EXTENSION_BITMAPS_MAX` (64) per pack, each `RVT_EXTENSION_BITMAP_BYTES` (20) of header:

| Size | Field |
|---|---|
| u32 | Owner: FNV-1a of the extension id; the core's own bitmaps are owned by the hash of `revola` |
| u32 | Asset: FNV-1a of the asset name |
| u32 | Kind, `enum rvt_extension_kind`: `RVT_EXTENSION_BITMAP` (1) the bitmap raw, `RVT_EXTENSION_BITMAP_LZ` (2) the bitmap as one lz stream |
| u32 | Stored bytes: the payload's length |
| u32 | Decoded bytes: the bitmap's length |
| bytes | Payload, zero-padded to 4 |

A bitmap is the whole BMap as the iPod decodes it: the `RVT_BMAP_HEADER_BYTES` (28) header (format, reserved, stride, depth, the bounds top, left, bottom, right, payload bytes), then the header's payload bytes of palette and rows. The payload is that bitmap raw, stored equal to decoded, or one lz stream decoding to exactly the decoded bytes and no longer than them plus one flag byte per 8, so the core can size the bitmap's block and run its own lz decoder without looking inside the stream. The decoded bytes are at most `RVT_EXTENSION_BITMAP_MAX_BYTES` (65,536) and equal the header plus its payload bytes; a reader checks the header the way the core does (bounds in order and within 16 bits, depth at most 32, a row of pixels within the stride, an Indexed8 palette of at most 256 entries within the payload and the rows within what is left) and rejects the bitmap otherwise. A Settings icon is a bitmap whose header is the menu header: Mask8 (8), stride 80, depth 8, bounds 0, 0, 121, 78, 9,680 payload bytes. The lz kind carries the same lz stream as `pixels_lz`; the hashes are the ones the core keys extension ids and asset names with (`revola/tools/rvx.py`, `fnv1a`); the compiler writes lz when the stream is smaller, and the pack CRC covers the extension bitmaps with the records.
