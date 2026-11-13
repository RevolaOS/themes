# Extension bitmaps

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

| Id | Asset | Size | Format | Palette | Menu |
|---|---|---|---|---|---|
| `appearance` | `settings-accent` | 78x121 | mask8 | - | yes |
| `appearance` | `settings-appearance` | 78x121 | mask8 | - | yes |
| `appearance` | `settings-covers` | 78x121 | mask8 | - | yes |
| `appearance` | `settings-moon` | 78x121 | mask8 | - | yes |
| `appearance` | `settings-theme` | 78x121 | mask8 | - | yes |
| `channels` | `settings-channels` | 78x121 | mask8 | - | yes |
| `compressor` | `settings-compressor` | 78x121 | mask8 | - | yes |
| `crossfeed` | `settings-crossfeed` | 78x121 | mask8 | - | yes |
| `equalizer` | `settings-eq` | 78x121 | mask8 | - | yes |
| `revola` | `extensions` | 78x121 | mask8 | - | yes |
