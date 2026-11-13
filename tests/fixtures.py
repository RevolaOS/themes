# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic PNGs, native bitmaps and a six-asset catalog for the tests."""

import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rvt import catalog as catalog_module  # noqa: E402
from rvt.bitmaps import describe  # noqa: E402


def png(width, height, color_type, rows):
    """A PNG from raw scanlines (each prefixed with its filter byte)."""

    def chunk(kind, body):
        return (
            struct.pack(">I", len(body))
            + kind
            + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def rgba_png(width, height, rgba):
    rows = b"".join(
        b"\0" + rgba[y * width * 4 : (y + 1) * width * 4] for y in range(height)
    )
    return png(width, height, 6, rows)


def indexed():
    pixels = bytes([0, 1, 0, 1])
    body = struct.pack("<I", 2) + bytes([3, 2, 1, 255, 6, 5, 4, 127]) + pixels
    return struct.pack("<4H5I", 0x64, 0, 4, 8, 0, 0, 1, 4, len(body)) + body


def bgra(width=3):
    pixels = bytes(4 * width)
    return (
        struct.pack("<4H5I", 0x1888, 0, 4 * width, 32, 0, 0, 1, width, len(pixels))
        + pixels
    )


def mask(fmt=8):
    pixels = bytes(4) if fmt == 8 else bytes(2)
    return (
        struct.pack("<4H5I", fmt, 0, len(pixels), fmt, 0, 0, 1, 4, len(pixels)) + pixels
    )


def rgb565():
    pixels = bytes(8)
    return struct.pack("<4H5I", 0x565, 0, 8, 16, 0, 0, 1, 4, 8) + pixels


def indexed_colors(colors, pixels, width, height, fmt=0x64):
    """A paletted bitmap: colors are RGBA tuples, pixels palette indices."""
    palette = b"".join(bytes((b, g, r, a)) for r, g, b, a in colors)
    size = 1 if fmt == 0x64 else 2
    rows = b"".join(struct.pack("<B" if size == 1 else "<H", index) for index in pixels)
    body = struct.pack("<I", len(colors)) + palette + rows
    return (
        struct.pack(
            "<4H5I", fmt, 0, width * size, 8 * size, 0, 0, height, width, len(body)
        )
        + body
    )


def bgra_colors(colors, width, height):
    pixels = b"".join(bytes((b, g, r, a)) for r, g, b, a in colors)
    return (
        struct.pack("<4H5I", 0x1888, 0, 4 * width, 32, 0, 0, height, width, len(pixels))
        + pixels
    )


def rgb565_words(words, width, height):
    pixels = b"".join(struct.pack("<H", w) for w in words)
    return (
        struct.pack("<4H5I", 0x565, 0, 2 * width, 16, 0, 0, height, width, len(pixels))
        + pixels
    )


# Derivation fixtures. Eta and Theta share a layout; Iota is a 4x3 icon on a
# light square for relight; Kappa is RGB565 the size of Iota; Lambda is
# BGRA8888.
WHITE, GRAY, DARK, BLACK, CLEAR = (
    (255, 255, 255, 255),
    (200, 200, 200, 255),
    (64, 64, 64, 255),
    (0, 0, 0, 255),
    (255, 255, 255, 0),
)
ETA_COLORS = (WHITE, GRAY, DARK, BLACK, (0, 0, 255, 128))
IOTA_COLORS = (
    (240, 244, 247, 255),  # row 0 background
    (230, 235, 240, 255),  # row 1 background
    (220, 226, 234, 255),  # row 2 background
    (200, 208, 216, 255),  # icon
    (236, 240, 244, 255),  # shadow, 4 below row 0's background
    (0, 0, 0, 0),
    (0, 0, 0, 0),
    (0, 0, 0, 0),
)
IOTA_PIXELS = (0, 0, 0, 4, 1, 3, 1, 1, 2, 2, 2, 2)


def eta():
    return indexed_colors(ETA_COLORS, (0, 1, 2, 3, 4, 0, 1, 2), 4, 2)


def theta():
    return indexed_colors(ETA_COLORS, (4, 3, 2, 1, 0, 4, 3, 2), 4, 2)


def iota():
    return indexed_colors(IOTA_COLORS, IOTA_PIXELS, 4, 3, fmt=0x65)


def kappa():
    words = (0xFFFF, 0, 0xF800, 0x07E0, 0x001F, 0xFFFF, 0, 0, 0, 0xFFFF, 0, 0)
    return rgb565_words(words, 4, 3)


def lambda_():
    return bgra_colors((WHITE, (0, 0, 0, 0), DARK, (10, 20, 30, 200)), 2, 2)


def firmware_image():
    """Every fixture bitmap at its catalog offset, for rvt.firmware tests."""
    document = catalog_document()
    size = max(a["offset"] + a["bytes"] for a in document["bitmaps"])
    image = bytearray(size)
    for info, data in zip(document["bitmaps"], BITMAPS):
        image[info["offset"] : info["offset"] + len(data)] = data
    return bytes(image)


RUNTIME_BASE = 0x08000000
RUNTIME_FILE_OFFSET = 0xB798


def entry(resource_id, offset, data, name):
    info = describe(resource_id, offset, data, name)
    info["address"] = catalog_module.address(offset, RUNTIME_BASE, RUNTIME_FILE_OFFSET)
    return info


def catalog_document(duplicate_name=False):
    bitmaps = [
        entry(0x10, 0x10000, indexed(), "Alpha"),
        entry(0x20, 0x10100, bgra(), "Beta"),
        entry(0x30, 0x10200, bgra(1), "Beta" if duplicate_name else "Gamma"),
        entry(0x40, 0x10300, mask(), "Delta"),
        entry(0x50, 0x10400, mask(4), "Epsilon"),
        entry(0x60, 0x10500, rgb565(), "Zeta"),
        entry(0x70, 0x10600, eta(), "Eta"),
        entry(0x80, 0x10700, theta(), "Theta"),
        entry(0x90, 0x10800, iota(), "Iota"),
        entry(0xA0, 0x10900, kappa(), "Kappa"),
        entry(0xB0, 0x10A00, lambda_(), "Lambda"),
    ]
    return {
        "schema": 1,
        "runtime_base": RUNTIME_BASE,
        "runtime_file_offset": RUNTIME_FILE_OFFSET,
        "bitmaps": bitmaps,
    }


BITMAPS = (
    indexed(),
    bgra(),
    bgra(1),
    mask(),
    mask(4),
    rgb565(),
    eta(),
    theta(),
    iota(),
    kappa(),
    lambda_(),
)


def catalog(duplicate_name=False):
    return catalog_module.Catalog(catalog_document(duplicate_name))
