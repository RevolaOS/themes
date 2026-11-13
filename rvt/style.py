# SPDX-License-Identifier: GPL-3.0-only
"""The style prefix of an appearance pack: colour roles, rendering flags, one
palette per named accent and one tint byte per catalog bitmap."""

import struct

from rvt import rvtfile

ROLES = rvtfile.ROLES
ACCENTS = rvtfile.ACCENTS
# The accent palette slots are the TOML keys of the roles they replace.
ACCENT_SLOTS = rvtfile.ACCENT_SLOTS
if any(slot not in ROLES for slot in ACCENT_SLOTS):
    raise ValueError("accent slots do not name roles of rvt.h")
STYLE_BYTES = rvtfile.STYLE_BYTES
FLAGS_OFFSET = rvtfile.STYLE_FLAGS
PALETTE_OFFSET = rvtfile.STYLE_PALETTES
TINT_OFFSET = rvtfile.STYLE_TINTS

ALL_FLAGS = sum(rvtfile.FLAGS.values())
# The lowest contrast of a text and background pair that passes.
CONTRAST_MINIMUM = 4.5

# Classic light and dark.
COLOR_DEFAULTS = {
    key: dict(zip(ROLES, (f"#{value}" for value in values.split())))
    for key, values in {
        "light": "ffffff 202020 236cc5 3185d0 ffffff 236cc5 7e8183 3185d0",
        "dark": "181818 e8e8e8 00a1ff 00a1ff ffffff 00a1ff 383838 00a1ff",
    }.items()
}
# Built-in accents: light fill, light text, dark fill, dark text. Blue is Classic.
ACCENT_BUILTIN = dict(
    zip(
        ACCENTS,
        (
            ("236cc5", "3185d0", "00a1ff", "00a1ff"),
            ("8944ab", "8944ab", "964ebc", "da8fff"),
            ("c41e56", "c41e56", "ce2660", "ff6491"),
            ("d02028", "d02028", "d42830", "ff6961"),
            ("b84800", "b84800", "be4c00", "ff9f0a"),
            ("1e803a", "1e803a", "20863e", "30d158"),
            ("007378", "007378", "00787d", "40d2d7"),
            ("826500", "826500", "846700", "ffd60a"),
            ("5c6066", "5c6066", "64686e", "bec2c8"),
        ),
    )
)


def rgb(color):
    return bytes.fromhex(color.removeprefix("#"))


def accent_builtin(name: str, appearance: str) -> tuple[str, str]:
    """Built-in fill and text of an accent for one appearance."""
    builtin = ACCENT_BUILTIN[name]
    fill, text = builtin[2:] if appearance == "dark" else builtin[:2]
    return "#" + fill, "#" + text


def accent_palette(name: str, appearance: str, colors: dict[str, str]) -> dict:
    """The palette an accent starts from: the built-in fill for accent_fill and
    selection, the built-in text for accent_text and icon_tint, and the
    appearance's own on_accent."""
    fill, text = accent_builtin(name, appearance)
    return dict(zip(ACCENT_SLOTS, (fill, text, fill, colors["on_accent"], text)))


def contrast(first: str, second: str) -> float:
    """WCAG contrast ratio of two #rrggbb colours."""

    def luminance(color):
        linear = [
            v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
            for v in (c / 255 for c in rgb(color))
        ]
        return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))

    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


CONTRAST_PAIRS = (
    ("text", "background"),
    ("accent_text", "background"),
    ("on_accent", "selection"),
    ("on_accent", "accent_fill"),
)


# The accent entry of the theme's own colours, as Settings names it.
THEME_DEFAULT = "Theme Default"


def contrast_report(colors: dict, palettes: dict) -> list[dict]:
    """Contrast of each text/background pair for Theme Default and every accent."""
    report = []
    for name, palette in [(THEME_DEFAULT, {}), *palettes.items()]:
        resolved = colors | palette
        for foreground, background in CONTRAST_PAIRS:
            ratio = contrast(resolved[foreground], resolved[background])
            report.append(
                {
                    "accent": name,
                    "foreground": foreground,
                    "background": background,
                    "ratio": round(ratio, 3),
                    "passes": ratio >= CONTRAST_MINIMUM,
                }
            )
    return report


COVERAGES = ("alpha", "darkness")


def tint_byte(role: str, coverage: str = "alpha") -> int:
    value = rvtfile.TINT_ROLE + ROLES.index(role)
    return value | (rvtfile.TINT_DARKNESS if coverage == "darkness" else 0)


def encode(colors: dict, flags: int, palettes: dict, tinted: dict) -> bytes:
    """The style prefix. tinted maps a catalog index to a tint role or a
    (role, coverage) pair."""
    if flags & ~ALL_FLAGS:
        raise ValueError(f"unknown rendering flags {flags:#x}")
    tints = bytearray(rvtfile.CATALOG_MAX)
    for index, tint in tinted.items():
        if not 0 <= index < rvtfile.CATALOG_MAX:
            raise ValueError(
                f"tinted catalog index {index} exceeds {rvtfile.CATALOG_MAX}"
            )
        role, coverage = tint if isinstance(tint, tuple) else (tint, "alpha")
        tints[index] = tint_byte(role, coverage)
    return (
        b"".join(rgb(colors[role]) + b"\xff" for role in ROLES)
        + struct.pack("<I", flags)
        + b"".join(
            rgb(palettes[name][slot]) + b"\xff"
            for name in ACCENTS
            for slot in ACCENT_SLOTS
        )
        + bytes(tints)
    )


def decode(data: bytes) -> dict:
    """Colours, flags, accent palettes and tinted bitmaps of a prefix."""
    if len(data) != STYLE_BYTES:
        raise ValueError(f"style prefix must be {STYLE_BYTES} bytes")
    if any(data[i] != 255 for i in range(3, TINT_OFFSET, 4) if i != FLAGS_OFFSET + 3):
        raise ValueError("style colours must be opaque")
    flags = struct.unpack_from("<I", data, FLAGS_OFFSET)[0]
    if flags & ~ALL_FLAGS:
        raise ValueError(f"unknown rendering flags {flags:#x}")
    at = PALETTE_OFFSET
    palettes = {}
    for name in ACCENTS:
        palettes[name] = {}
        for slot in ACCENT_SLOTS:
            palettes[name][slot] = "#" + data[at : at + 3].hex()
            at += 4
    tinted = {}
    for index, value in enumerate(data[TINT_OFFSET:]):
        if value == rvtfile.TINT_NONE:
            continue
        coverage = "darkness" if value & rvtfile.TINT_DARKNESS else "alpha"
        value &= ~rvtfile.TINT_DARKNESS
        if rvtfile.TINT_ROLE <= value < rvtfile.TINT_ROLE + len(ROLES):
            tinted[index] = (ROLES[value - rvtfile.TINT_ROLE], coverage)
        else:
            raise ValueError(f"unknown tint byte {value} for bitmap {index}")
    return {
        "colors": {
            role: "#" + data[i * 4 : i * 4 + 3].hex() for i, role in enumerate(ROLES)
        },
        "rendering": flags,
        "accents": palettes,
        "tinted": tinted,
    }
