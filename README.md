# themes

First-party themes for RevolaOS, and the compiler that builds a theme folder into one `/Revola/Themes/<id>.rvt` file read by the Appearance extension. A theme sets colours, accents and rendering options and replaces or derives Apple's bitmaps; authoring needs Python and nothing from the iPod, never the firmware.

| Directory | Theme | What it looks like | Appearances |
|---|---|---|---|
| `themes/classic` | Classic | Classic's dark look: the stock art relit, recoloured and inverted on the iPod. Shipped inside the Appearance extension, not installed as a file | dark |
| `themes/flat` | Flat | Flat glyphs from Cupertino Icons and Inter, an iOS palette, nine accents, flat selection bar and face-on cover art | light, dark |

## Build

```sh
python3 -m rvt compile themes/flat          # into dist/flat/flat.rvt
python3 -m rvt inspect dist/flat/flat.rvt
```

`<id>.rvt` is what goes to `/Revola/Themes/<id>.rvt`. Flat's art and `theme.toml` are drawn by `themes/flat/render.py` from Cupertino Icons and Inter with ImageMagick (`--font`, `--text-font`); `render.py --check` confirms the committed files match. The other commands, tests and the layout of the compiler are in [The compiler](docs/toolchain.md).

## Documentation

| Page | Contents |
|---|---|
| [docs/](docs/README.md) | Authoring, the compiler, the file format, the catalogs, the bitmaps |
| [STYLE.md](STYLE.md) | Principles and rules for every file |

## Development

Large language models are used for much of the coding on RevolaOS. Their output is checked in the emulator, its memory use comes from the heap profile, and every release is tested on an iPod before it ships. Contributions written with the same tools are welcome and tested in the same way.

## License

GPL-3.0-only. See COPYING and NOTICE.
