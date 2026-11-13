# SPDX-License-Identifier: GPL-3.0-only
"""rvt: compile and check theme folders, inspect .rvt files, start a theme,
browse the two catalogs, and with a local firmware preview derived art or
turn a PNG into a recolour rule."""

import argparse
import json
import struct
import sys
from pathlib import Path

from rvt import assets, compiler, inspector, rvtfile, theme
from rvt import catalog as catalog_module
from rvt.bitmaps import tint_kind


def main(argv=None) -> int | None:
    parser = argparse.ArgumentParser(prog="rvt", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    def catalog_option(command):
        command.add_argument(
            "--catalog",
            type=Path,
            default=None,
            help="a catalog other than the built-in",
        )

    def extension_option(command):
        command.add_argument(
            "--extension",
            type=Path,
            action="append",
            default=[],
            metavar="assets.json",
            help="the bitmaps of an extension outside the first-party catalog, as "
            "the SDK's assets.py prints them; repeatable",
        )

    def theme_options(command):
        command.add_argument("folder", type=Path, help="folder with theme.toml")
        catalog_option(command)
        extension_option(command)
        command.add_argument(
            "--allow-reserved",
            action="store_true",
            help="accept the reserved id of the built-in theme",
        )
        command.add_argument(
            "--strict", action="store_true", help="treat warnings as errors"
        )

    build = commands.add_parser("compile", help="theme folder -> <id>.rvt")
    theme_options(build)
    build.add_argument("--out", type=Path, default=Path("dist"))

    check = commands.add_parser("check", help="compile without writing")
    theme_options(check)

    show = commands.add_parser("inspect", help="validate and describe an .rvt")
    show.add_argument("file", type=Path)
    catalog_option(show)
    extension_option(show)
    show.add_argument("--json", action="store_true", help="print the full description")

    new = commands.add_parser("new", help="start a theme folder")
    new.add_argument("id", help="the theme's id, also the folder's name")
    new.add_argument("--name", help="the display name; defaults to the id")

    browse = commands.add_parser(
        "catalog", help="list or show Apple's bitmaps and extension bitmaps"
    )
    browse_commands = browse.add_subparsers(dest="catalog_command", required=True)
    listing = browse_commands.add_parser("list", help="name, size, format, palette")
    listing.add_argument(
        "--extensions",
        action="store_true",
        help="extension bitmaps instead of Apple's bitmaps",
    )
    listing.add_argument("--group", help="name prefix, or an extension id")
    listing.add_argument(
        "--format", dest="fmt", help=", ".join(catalog_module.FORMAT_NAMES.values())
    )
    catalog_option(listing)
    extension_option(listing)
    detail = browse_commands.add_parser(
        "show", help="every field of one Apple bitmap or extension bitmap"
    )
    detail.add_argument("name", help="catalog name, hex id or <id>/<asset>")
    catalog_option(detail)
    extension_option(detail)

    preview = commands.add_parser(
        "preview", help="render the art a theme derives, from a firmware"
    )
    theme_options(preview)
    preview.add_argument(
        "--firmware", type=Path, required=True, help="osos.bin or revola.bin"
    )
    preview.add_argument("--out", type=Path, default=Path("dist"))

    recolor = commands.add_parser(
        "recolor", help="turn <appearance>/apple/<Name>.png into a recolour rule file"
    )
    recolor.add_argument("png", type=Path, help="<theme>/<appearance>/apple/<Name>.png")
    recolor.add_argument(
        "--firmware", type=Path, required=True, help="osos.bin or revola.bin"
    )
    catalog_option(recolor)

    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            print(new_theme(args.id, args.name))
            return None
        catalog = catalog_module.load(args.catalog)
        extensions = assets.load_catalog(getattr(args, "extension", []))
        if args.command == "compile":
            path, build = compiler.write(
                catalog,
                args.folder,
                args.out,
                args.allow_reserved,
                args.strict,
                extensions,
            )
            report(build)
            print(f"Wrote {path}")
        elif args.command == "check":
            build = compiler.compile_theme(
                catalog, args.folder, args.allow_reserved, args.strict, extensions
            )
            report(build)
        elif args.command == "inspect":
            result = inspector.inspect(
                args.file.read_bytes(), catalog, assets.known_names(extensions)
            )
            if args.json:
                print(json.dumps(result, indent=2, default=lambda b: b.hex()))
            else:
                print(inspector.describe(result))
        elif args.command == "catalog":
            if args.catalog_command == "list" and args.extensions:
                for line in extension_list(extensions, args.group, args.fmt):
                    print(line)
            elif args.catalog_command == "list":
                for line in catalog_list(catalog, args.group, args.fmt):
                    print(line)
            elif "/" in args.name:
                print(extension_show(extensions, args.name))
            else:
                print(catalog_show(catalog, args.name))
        elif args.command == "preview":
            for line in render(catalog, extensions, args):
                print(line)
        else:
            print(convert(catalog, args), end="")
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"{error}\n")
    return None


def report(build: compiler.Build) -> None:
    """Notes, warnings and the size table of a compiled theme."""
    for note in build.notes:
        print(note)
    for warning in build.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(compiler.summary(build.inspection, len(build.data)))


def new_theme(identifier: str, name: str | None) -> str:
    """Write <id>/theme.toml with every option as a comment, and the apple/,
    revola/ and extensions/ folders of light/ and dark/."""
    rvtfile.check_id(identifier)
    if identifier in theme.RESERVED_IDS:
        raise ValueError(f"id: {identifier!r} is reserved for the built-in theme")
    name = rvtfile.check_name(name or identifier)
    folder = Path(identifier)
    if folder.exists():
        raise ValueError(f"{folder} exists")
    for appearance in rvtfile.APPEARANCES:
        for sub in compiler.FOLDERS:
            (folder / appearance / sub).mkdir(parents=True)
    (folder / "theme.toml").write_text(theme.template(identifier, name))
    return f"Wrote {folder}/theme.toml and {{light,dark}}/{{{','.join(compiler.FOLDERS)}}}/"


def catalog_list(catalog, group: str | None, fmt: str | None) -> list[str]:
    """name WxH format palette tintable, one line per bitmap."""
    names = catalog_module.FORMAT_NAMES
    if fmt is not None and fmt not in names.values():
        raise ValueError(f"--format: expected one of {', '.join(names.values())}")
    lines = []
    for asset in catalog.assets:
        if group and not asset["name"].startswith(group):
            continue
        if fmt and names[asset["format"]] != fmt:
            continue
        lines.append(
            f"{asset['name']} {asset['width']}x{asset['height']} "
            f"{names[asset['format']]} {asset['palette_colors']} "
            f"{'tintable' if tint_kind(asset['format']) else 'untintable'}"
        )
    return lines


def extension_list(extensions: dict, group: str | None, fmt: str | None) -> list[str]:
    """id asset WxH format palette menu, one line per extension bitmap."""
    names = assets.FORMAT_NAMES
    if fmt is not None and fmt not in names.values():
        raise ValueError(f"--format: expected one of {', '.join(names.values())}")
    lines = []
    for (identifier, asset), record in sorted(extensions.items()):
        if group and identifier != group:
            continue
        name = names.get(record["format"], f"{record['format']:#x}")
        if fmt and name != fmt:
            continue
        lines.append(
            f"{identifier} {asset} {record['width']}x{record['height']} {name} "
            f"{record['palette_colors']} {'menu' if record['menu'] else 'bitmap'}"
        )
    return lines


def extension_show(extensions: dict, reference: str) -> str:
    """Every field of one extension bitmap, named <id>/<asset>."""
    identifier, _, asset = reference.partition("/")
    record = extensions.get((identifier, asset))
    if record is None:
        raise ValueError(
            f"name: {reference!r} is not in the extension asset catalog; "
            "--extension adds an extension's assets.json"
        )
    lines = []
    for key in assets.RECORD_KEYS:
        value = record[key]
        if key == "format":
            value = f"{value:#x}"
        elif isinstance(value, bool):
            value = str(value).lower()
        lines.append(f"{key} {value}")
    lines.append(f"format_name {assets.FORMAT_NAMES.get(record['format'], 'unknown')}")
    lines.append(f"owner_hash {assets.owner_hash(identifier):#010x}")
    lines.append(f"asset_hash {assets.asset_hash(asset):#010x}")
    return "\n".join(lines)


def catalog_show(catalog, reference: str) -> str:
    """Every field of one bitmap; a name listed twice shows both."""
    if catalog_module.is_hex_id(reference):
        indices = [catalog.resolve(reference, "name")]
    else:
        indices = catalog.by_name.get(reference)
        if not indices:
            raise ValueError(f"name: {reference!r} is not a catalog bitmap name")
    blocks = []
    for index in indices:
        asset = catalog.assets[index]
        lines = [f"index {index}"]
        for key, value in asset.items():
            text = f"{value:#x}" if key in ("id", "address", "format") else value
            lines.append(f"{key} {text}")
        lines.append(f"format_name {catalog_module.FORMAT_NAMES[asset['format']]}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def convert(catalog, args) -> str:
    """Write <appearance>/<Name>.toml beside the PNG and return a summary."""
    from rvt import firmware

    png = args.png.resolve()
    appearance = png.parent.parent.name
    if (
        png.parent.name != compiler.APPLE
        or appearance not in rvtfile.APPEARANCES
        or png.suffix != ".png"
    ):
        raise ValueError(
            f"expected <theme>/<appearance>/{compiler.APPLE}/<CatalogName>.png"
        )
    index = catalog.resolve(png.stem, str(args.png))
    pairs, notes = firmware.to_recolor(
        catalog, firmware.Firmware(args.firmware, catalog), index, png.read_bytes()
    )
    target = png.with_suffix(".toml")
    target.write_text(firmware.recolor_text(pairs))
    return "".join(f"{png.name}: {note}\n" for note in notes) + (
        f"Wrote {target} ({len(pairs)} colour pairs); delete {png.name} to use it\n"
    )


def render(catalog, extensions, args) -> list[str]:
    """Previews of every derived bitmap under <out>/<id>/derived/."""
    from rvt import firmware

    build = compiler.compile_theme(
        catalog, args.folder, args.allow_reserved, args.strict, extensions
    )
    result, warnings = firmware.render(
        catalog, firmware.Firmware(args.firmware, catalog), build.data
    )
    root = args.out / build.report["id"] / "derived"
    listing = {}
    for appearance, entries in result.items():
        (root / appearance).mkdir(parents=True, exist_ok=True)
        listing[appearance] = {}
        for name, entry in entries.items():
            (root / appearance / f"{name}.png").write_bytes(entry.pop("png"))
            listing[appearance][name] = entry
    (root / "derived.json").write_text(json.dumps(listing, indent=2) + "\n")
    count = sum(len(entries) for entries in listing.values())
    return [*warnings, f"Wrote {count} previews and derived.json under {root}"]


if __name__ == "__main__":
    sys.exit(main())
