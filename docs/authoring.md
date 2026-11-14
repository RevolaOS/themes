# Authoring a theme

A theme is a folder compiled on a desktop into one `.rvt` file. It can set colours, name a palette for each accent the listener can pick, choose a few rendering options and replace Apple's bitmaps with same-size art or rules that derive them. The compiler needs the [catalog](catalog.md), not the firmware. The prose in this documentation is British; the keys in `theme.toml` and the rule files are American (`colors`, `recolor`).

## Quickstart

1. `python3 -m rvt new mytheme` (`python3 -m rvt` runs from the repository root, or `rvt` after `pip install .`) writes `mytheme/theme.toml` in the current folder with every role and option as a comment, and empty `mytheme/light/` and `mytheme/dark/`, each with an `apple/`, a `revola/` and an `extensions/` folder.
2. Edit `theme.toml`; drop art into `light/apple/` and `dark/apple/`, named after the [bitmaps](bitmaps.md) it replaces, and [extension bitmaps](#extension-bitmaps) into `light/extensions/<id>/` and `dark/extensions/<id>/`.
3. `python3 -m rvt check mytheme` prints what each rule matched, the warnings and a size table, and writes nothing.
4. `python3 -m rvt compile mytheme` writes `dist/mytheme/mytheme.rvt` and `report.json`; `--strict` makes the warnings errors.
5. Copy `mytheme.rvt` to `/Revola/Themes/` on the iPod. It appears under Settings > Appearance > Theme.

**Try it in the emulator.** With `ipodvm` from the emulator repository (`qemu-ipod-classic/tools/ipodvm`) and `revola/build/revola.bin` built with `python3 tools/build.py firmware` in the `revola` repository,

```sh
ipodvm disk --base <image> \
    --copy dist/mytheme/mytheme.rvt:/Revola/Themes/mytheme.rvt \
    --copy revola/build/revola.bin:/Revola/Firmware/revola.bin
```

makes a disk with the theme on it. The emulator boots the firmware image from the host, not from the disk, so the booted build must also be the `/Revola/Firmware/revola.bin` on the disk: the iPod derives art from that file.

```
mytheme/
  theme.toml
  light/
    apple/          art for the light appearance: a PNG per replaced Apple bitmap, a TOML per derived one
    extensions/     one folder per extension id, with a PNG per bitmap asset it replaces
    revola/         a PNG per bitmap of the RevolaOS core it replaces
  dark/             the same for dark
```

A file directly under `light/` or `dark/` is an error: Apple's bitmaps go in `apple/`, extension bitmaps in `extensions/<id>/`, the core's in `revola/`.

## theme.toml

```toml
schema = 1
id = "mytheme"          # the file's stem; "classic" is the built-in theme
name = "My Theme"       # shown in Settings
author = "..."          # optional, report only
version = "1.0"         # optional, report only

[light]
menu_covers_default = true  # the Menu Covers setting until the listener chooses one

[light.colors]          # any subset of the roles below, "#rrggbb"
accent_fill = "#0071e3"
icon_tint = "#0071e3"   # left out, it follows accent_text

[light.accents]         # one colour per accent, or a table; see Accents
blue = "#007aff"
yellow = { accent = "#ffcc00", on_accent = "#000000" }

[light.rendering]
flat_selection = false
flat_now_playing = false

[light.tint]            # role = [catalog names, globs or id/asset]; see Tint
icon_tint = ["Settings_EQ_*_Image", "Media_*Proxy_Image"]
text = ["StatusBar*_Battery_Image_[3-9]", "StatusBar*_Battery_Image_[12][0-9]"]
darkness_coverage = ["NowPlaying_Blue_Dot_Image"]
solid_coverage = ["Settings_AppleLogo_Image"]

[light.derive]          # rules for derived art; see Derived art
"Settings_Brightness_Image" = { kind = "invert" }

[dark]                  # the same tables; an empty table is Classic dark colours and no art
```

An appearance that is not in the file is not in the theme: the iPod keeps Classic for it, and a listener who turns Dark Mode on with a light-only theme is told the theme has no dark appearance. Declare `[light]`, `[dark]` or both. Unknown keys are rejected; a named capability the format has no room for (`fonts`, `layouts`, `metrics`, `animations`, `sounds`, `strings`, `wallpapers`) is rejected as unsupported.

### Colour roles

Roles you leave out keep their Classic value; `icon_tint` left out follows `accent_text`.

| Role | Light | Dark | What it colours |
|---|---|---|---|
| `background` | `#ffffff` | `#181818` | Native surfaces; labels on light art |
| `text` | `#202020` | `#e8e8e8` | Native text; labels on dark art |
| `accent_fill` | `#236cc5` | `#00a1ff` | Native accent fills; stock progress, dot, star and playback art the theme leaves stock |
| `accent_text` | `#3185d0` | `#00a1ff` | Native accent text, the Search caret |
| `on_accent` | `#ffffff` | `#ffffff` | Selected-row text and tinted icons on the selection bar, the highlighted Search key, the selected calendar day |
| `selection` | `#236cc5` | `#00a1ff` | The list selection bar; stock selection and focus art the theme leaves stock |
| `cover_border` | `#7e8183` | `#383838` | Cover Flow border |
| `icon_tint` | `#3185d0` | `#00a1ff` | Tinted icons: the Settings icons of extensions and the bitmaps `[tint]` lists under it |

Keep `on_accent` readable on both `accent_fill` and `selection`; `report.json` lists the contrast of each text and background pair for Theme Default and every accent, and `rvt check` warns about a pair the theme colours that falls below 4.5:1, once per pair unless an accent changes it.

Labels Apple draws in a fixed colour over art take `text` or `background`, whichever differs more in brightness from the centre pixel of the art behind them, so that art may be light or dark:

| Label | Art |
|---|---|
| Stopwatch and Charging header title | `NowPlaying_StatusBar_Image` |
| Screen Lock and Volume Limit combination digits | `LockScreen_TumblerBgnd_Image` |
| Date and time picker values | `DateTimePicker_Well` |
| Cover Flow album title and artist (track list) | `CoverFlow_Backside_Top_Image` |
| Calendar days of the shown month | `Calendar_Active_Cell` |

Keep `LockScreen_TumblerFocus_Image` and `DateTimePicker_Selection` about as light or dark as the art above them: the focused digit and the selected value use the same colour as the others. Calendar days of the neighbouring months follow the rule against `Calendar_Inactive_Cell`, mixed halfway toward the cell, and weekday names the same against `background`; a cell with a transparent centre counts as `background`. The selected day uses `on_accent` on `Calendar_Hilite_Cell`, and tinted alarm and event markers switch to `on_accent` there too.

The Search letter strip draws its unhighlighted letters in `text` or `background` against the centre pixel of the well art (`OptionBar_*_Well_Center_Image`); the highlighted letter uses `on_accent` on the thumb, so keep it readable on whatever tints the thumb slices. Option bars (the Clock's Add/Edit bar) label their segments the same way; the Now Playing shuffle selector follows a theme only. The text typed into the Search box follows the rule against `System_Input_Field_Middle_Image`, and its caret uses `accent_text`.

Classic keeps the stock colours of every label above.

### Accents

The listener picks an accent in Settings; `blue`, `purple`, `pink`, `red`, `orange`, `green`, `teal`, `yellow` and `graphite` each have a built-in fill and text colour per appearance, Blue being Classic's. An accent's palette starts from that fill (for `accent_fill` and `selection`), that text (for `accent_text` and `icon_tint`) and the appearance's own `on_accent`. In `[light.accents]` an accent is one of:

| Form | Sets |
|---|---|
| `blue = "#007aff"` | `accent_fill`, `accent_text`, `selection` and `icon_tint` to that colour |
| `yellow = { accent = "#ffcc00", on_accent = "#000000" }` | the same four, and `on_accent` |
| `teal = { accent_fill = "...", accent_text = "...", selection = "...", on_accent = "...", icon_tint = "..." }` | any subset of the five palette slots, each named after the role it replaces |

Accents you leave out keep the built-in fill and text; `report.json` names them under `accents_builtin`.

### Menu Covers

`menu_covers_default`, directly in `[light]` or `[dark]`, is the Menu Covers setting the theme applies until the listener chooses one: whether the Main and Music menus show the highlighted row's cover. It defaults to `true`.

### Rendering

| Key | Default | `true` / `false` |
|---|---|---|
| `flat_selection` | `false` | `true`: `selection` throughout the bar. `false`: a gradient ending at `selection`, starting at `selection` lightened 25 % toward white, with a top line lightened 55 % |
| `flat_now_playing` | `false` | `true`: the cover face-on, no reflection; Cover Flow is unchanged. `false`: the tilted cover with its reflection |
| `flat_icons` | `false` | `true`: the Settings icons of [extensions](#extension-bitmaps) the theme does not replace are drawn without their reflection, as a theme that replaces Apple's icons with reflection-free art wants. `false`: they keep it |

Stock blue artwork that marks selection, focus or progress follows the theme when the theme leaves it stock: the option bar thumbs, the active button, picker and calendar highlights, the Settings checkmark, the progress and Genius sliders, new-item dots, rating stars and playback glyphs. The iPod recolours them from the stock pixels with `selection` or `accent_fill`, keeping their shading; replaced art is never recoloured.

The screens RevolaOS draws itself (the Graphic EQ and other editors, text pages, its lists) take the roles too: their greys are mixed from `background` toward `text`, the selected row uses `selection` with `on_accent` text, and accent text uses `accent_text`.

## Art

A file in `light/apple/` or `dark/apple/` stands for the catalog bitmap of the same name: `Settings_About_Band_Image.png` replaces its pixels, `Settings_About_Band_Image.toml` [derives](#derived-art) them on the iPod from the stock bitmap. [Bitmaps](bitmaps.md) lists every name with its size, format and palette. A name the catalog lists more than once must be given as its hex id, `light/apple/0x0DAD012A.png`. Every file in those folders must match a catalog bitmap, and a bitmap is given once per appearance. `[tint]` lists and `[derive]` keys name the catalog bitmap, without the folder.

The art must be the bitmap's exact native size; the compiler converts it to the native format:

| Format | Art |
|---|---|
| Masks (4 and 8) | Opaque grayscale; 4-bit masks round to 16 levels |
| Paletted (0x64, 0x65) | Any RGBA; more colours than the native palette holds are reduced to fit, with a warning naming the bitmap and the counts (also in `report.json` under `palette_reduced`) |
| RGB565 | Opaque |
| BGRA8888 (0x1888) | Any RGBA |

### Tint

`[light.tint]` makes the iPod draw a bitmap in one live colour role, following the picked accent. Each key is a role and lists catalog names, hex ids or globs (`*`, `?`, `[...]`, case-sensitive), or extension bitmaps as `<id>/<asset>` ([below](#extension-bitmaps)); a glob that matches nothing is a warning, a name that is not in the catalog an error, and a bitmap may appear under one role only. The coverage comes from your art when there is a PNG (its alpha channel when it has one, otherwise its gray level; coloured opaque art is rejected) and from the stock bitmap when there is none. Tinted art with more coverage levels than the palette holds is reduced on the coverage alone, so the result is the same whatever colour it is drawn in.

| Format | Needs art | How it is tinted |
|---|---|---|
| Masks | No; without art the stock shape is tinted | At draw time |
| Paletted | No; without art the stock coverage is tinted | The palette entries are rewritten on the iPod, keeping each entry's alpha |
| BGRA8888 | No; without art the stock coverage is tinted | The pixels are rewritten, keeping their alpha |
| RGB565 | Cannot be tinted | |

The `darkness_coverage` list names tinted bitmaps whose coverage is their darkness instead of their alpha, for stock glyphs drawn black on transparent, where the alpha alone has no anti-aliasing. The `solid_coverage` list names tinted bitmaps drawn flat: every coverage level from 150 of 255 up becomes full and the levels below, the anti-aliased rim, stay, for stock masks whose gloss lives in their levels, such as the Apple logo. A bitmap is in one of the two lists at most. Both apply to the stock bitmap only; they are rejected with a PNG. A tinted bitmap cannot also be derived.

### Derived art

A rule describes a bitmap as a change to Apple's stock bitmap. The iPod reads the stock bytes from its firmware and computes the result when the theme is applied, so the theme carries colours and rules, never Apple's pixels. A rule is an entry of `[dark.derive]` whose key is a catalog name, hex id or glob and whose value is a table, or a `.toml` file beside the PNGs, `dark/apple/<CatalogName>.toml`, holding the same table; the file suits a long recolour map. A `[derive]` rule must match at least one bitmap, may not match a bitmap that has a PNG or a `.toml`, and two rules may not match the same bitmap; `rvt check` prints how many bitmaps each rule matched. A rule has a `kind` and that kind's keys:

| `kind` | Keys | Formats | Result |
|---|---|---|---|
| `recolor` | `[map]`: `"#rrggbbaa" = "#rrggbbaa"`, a stock colour and its replacement; keys must be quoted | paletted, BGRA8888, RGB565 | Each palette entry, pixel or RGB565 word equal to a stock colour in the map takes its replacement; the rest stay |
| `alias` | `source`: a catalog name or hex id | any but masks, the same size | The pixels of `source`: its result when the theme replaces or derives it in this appearance, else the stock pixels; re-encoded in this bitmap's format when the layouts differ, so a paletted bitmap must have room for the source's colours |
| `invert` | | any but masks | RGB inverted, alpha kept |
| `relight` | the rule's values, all optional, below | paletted | A light icon on a light square redrawn as grays on a dark one |

Every kind may add `from_other = true` to start from the theme's own PNG for that bitmap in the other appearance instead of the stock bitmap: you draw the art once and the compiler computes the other appearance's pixels from it, with the same arithmetic the iPod uses for the stock art, and stores the result. That PNG must exist and must not be tinted in its own appearance. An alias with `from_other` takes the other appearance's PNG of `source`, which may be left out to name the bitmap itself and reuse its own art unchanged.

```toml
# theme.toml
[dark.derive]
"Clock_*_Image_*" = { kind = "alias", from_other = true }      # every digit reuses its light art
"Settings_Brightness_Image" = { kind = "invert", from_other = true }
"NowPlaying_White_Pause_Image" = { kind = "alias", source = "NowPlaying_Black_Pause_Image" }
"Media_*Proxy_Image" = { kind = "relight" }

# dark/apple/System_ScrollbarCenter_Image.toml
kind = "recolor"
[map]
"#ffffff26" = "#91919126"
"#00000073" = "#7e7e7e73"
```

On RGB565 both colours of a recolour pair are opaque with `r` and `b` multiples of 8 and `g` a multiple of 4. An alias may not point at another alias or at a tinted bitmap; aliases with `from_other` are resolved by the compiler and not counted against the limit on the iPod's aliases.

**Relight.** The rule's keys are `t_zero` and `t_full` (the channel offsets from the row's background at which a pixel counts as no icon and as all icon), `bg_base`, `bg_ref`, `bg_slope`, `bg_lo`, `bg_hi`, `icon_base`, `icon_luma`, `icon_row`, `icon_lo` and `icon_hi`; [File format](format.md#relight) gives the arithmetic. The defaults are Classic's: `t_zero = 3`, `t_full = 14`, `bg_base = 25`, `bg_ref = 216`, `bg_slope = 0.357` (stored as 91/256), `bg_lo = 24`, `bg_hi = 35`, `icon_base = 394.6`, `icon_luma = -1.170`, `icon_row = -1.769`, `icon_lo = 40`, `icon_hi = 160`. Values are stored as 8.8 fixed point, rounded to 1/256, and must satisfy `0 <= t_zero < t_full <= 255`, `0 <= bg_lo <= bg_hi <= icon_lo <= icon_hi <= 255`, `bg_base` and `icon_base` within ±1024, `bg_ref`, `icon_luma` and `icon_row` within ±255 and `bg_slope` within ±16; the bitmap must have at most 3,840 pixels and a palette of at least `icon_hi - bg_lo + 1` entries.

**From a PNG.** With a decrypted firmware at hand,

```sh
python3 -m rvt recolor mytheme/dark/apple/Foo.png --firmware osos.bin
```

writes `dark/apple/Foo.toml` when the PNG is a pure recolour of the stock bitmap, treating small dithering spreads and a few stray pixels as noise, and lists the stock colours it paints in several colours when it is not. Delete the PNG to use the file.

```sh
python3 -m rvt preview mytheme --firmware osos.bin
```

renders every derived bitmap to `dist/mytheme/derived/<appearance>/<CatalogName>.png` and writes `derived.json` with the address, size and CRC-32 of each result, and warns about map colours that match nothing in the stock bitmap. The compiler itself never needs the firmware.

## Extension bitmaps

A RevolaOS extension ships its bitmaps as assets: the 78 x 121 Settings icon of its row, and any picture its own screens draw. The iPod decodes such a bitmap only while it is shown, and a theme that is on supplies its own at that moment, so extension bitmaps change with the theme like Apple's.

A file `light/extensions/<id>/<asset>.png` replaces the asset `<asset>` of the extension `<id>` in the light appearance; `dark/extensions/` the same for dark. `revola` is the core's id: its bitmaps go in `light/revola/<asset>.png` and `dark/revola/<asset>.png`, never under `extensions/`. Which bitmaps exist and how large they are comes from the extension asset [catalog](catalog.md#extension-asset-catalog):

```sh
python3 -m rvt catalog list --extensions                  # id, asset, size, format, palette, menu
python3 -m rvt catalog list --extensions --group appearance
python3 -m rvt catalog show appearance/settings-moon
```

[Extension bitmaps](extension-bitmaps.md) is the same list as a page. The built-in catalog knows the first-party extensions; for another extension pass its `assets.json` (`python3 <sdk>/assets.py manifest.toml file.rvx > assets.json`, which its author ships beside the package) with `--extension`, repeatable, to `check`, `compile` and `inspect`. The compiler checks the names' syntax (an id is `[a-z][a-z0-9_-]{0,31}`, an asset `[a-z0-9_-]{1,31}`) and encodes the art as the extension's own build would:

| Bitmap | Art | Stored as |
|---|---|---|
| Settings icon (`menu` in the catalog) | Exactly 78 x 121; when any pixel is translucent the alpha channel is the coverage, otherwise opaque grayscale whose gray level is the coverage; coloured opaque art is rejected | A Mask8 coverage mask drawn in the icon tint |
| Any other bitmap | Exactly the catalog's width and height, any RGBA | Indexed8 with a palette when the art has at most 256 colours, else BGRA8888; at most 65,536 bytes with its header |

A picture follows the accent when a `[tint]` role lists it as `<id>/<asset>` (`revola/<asset>` for the core's): `icon_tint = ["homebrew/apps"]` reads `extensions/homebrew/apps.png` as coverage like a Settings icon (alpha, else gray level; coloured opaque art is rejected) and the iPod draws it in that role. Such a bitmap needs its PNG in every appearance that lists it, takes its coverage from the art only (no `darkness_coverage` or `solid_coverage`), and cannot be a Settings icon, which the iPod draws in the icon tint already.

An (id, asset) the catalog does not know compiles only as a Settings icon, when the PNG is 78 x 121 coverage, with a warning; any other size is an error that asks for `--extension`. The iPod ignores a bitmap no installed extension asks for. Two bitmaps whose hashed names collide are rejected; a theme carries at most 64 extension bitmaps per appearance.

The art box of a Settings icon is rows 12..62, centred on column 39; the rows from 79 down hold the reflection on the stock icons. An icon with nothing below row 78 while `flat_icons` ([Rendering](#rendering)) is off is a warning: the icons the theme does not replace would keep their reflection next to one without. Light and dark icons are both coverage, so a theme that draws one shape writes the PNG into both folders.

## Limits

| What | Limit |
|---|---|
| `id` | `[a-z0-9][a-z0-9_-]{0,30}`; `classic` is reserved |
| `name` | at most 47 UTF-8 bytes, no control characters |
| Art size | the bitmap's native width and height, nothing else; Settings icons 78 x 121, other extension bitmaps the catalog's size |
| Extension bitmaps | at most 64 per appearance, each at most 65,536 bytes encoded; ids `[a-z][a-z0-9_-]{0,31}`, assets `[a-z0-9_-]{1,31}`, no two with equal hashes; a tinted one is a picture, not a Settings icon |
| Art files | non-interlaced PNG with 8-bit channels or a palette, at most 16 MiB; plain file names inside the folder, no symlinks that leave it |
| `theme.toml`, rule files | at most 256 KiB each |
| Palette per bitmap | the native palette's entries (see [Bitmaps](bitmaps.md)); more colours are reduced with a warning |
| Recolour map | at most 512 pairs, and no more than the bitmap has palette entries or pixels |
| Aliases of stock art | at most 16 per appearance; an alias between differing layouts is re-encoded on the iPod and allowed for bitmaps of at most 3,840 pixels |
| Relight | bitmaps of at most 3,840 pixels; the bounds above |
| Colours | opaque `#rrggbb`; translucent roles are not supported |

## Unsupported

Fonts, layouts, metrics, animations, sounds, strings, wallpapers, new bitmaps, bitmaps of another size, translucent colours and appearances other than light and dark.
