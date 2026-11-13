# SPDX-License-Identifier: GPL-3.0-only
"""PNG reading and the native BMap pixel formats a theme can replace.

A BMap is a 28-byte header (format, stride, depth, bounds, payload bytes), for
paletted formats a 32-bit colour count and the palette as B, G, R, A, then the
rows, each padded to the stride. The 32-bit format stores B, G, R, A too. A theme record carries everything after the
header (and after the colour count, which never changes), so a replacement is
the same size as the original and the device copies it in place.
"""

import struct
import zlib
from collections import Counter

MASK4, MASK8 = 4, 8
INDEXED8, INDEXED16 = 0x64, 0x65
RGB565 = 0x565
BGRA8888 = 0x1888
MASK_FORMATS = (MASK4, MASK8)
PALETTE_FORMATS = (INDEXED8, INDEXED16)
BGRA_FORMATS = (BGRA8888,)
DEPTHS = {MASK4: 4, MASK8: 8, INDEXED8: 8, INDEXED16: 16, RGB565: 16, BGRA8888: 32}


def paeth(a, b, c):
    p = a + b - c
    return min((a, b, c), key=lambda value: abs(p - value))


def read_png(data: bytes) -> tuple[int, int, bytes]:
    """Width, height and RGBA bytes of a PNG."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    chunks = {}
    offset = 8
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated PNG")
        size, kind = struct.unpack_from(">I4s", data, offset)
        if offset + 12 + size > len(data):
            raise ValueError("truncated PNG")
        body = data[offset + 8 : offset + 8 + size]
        crc = struct.unpack_from(">I", data, offset + 8 + size)[0]
        if zlib.crc32(kind + body) != crc:
            raise ValueError("PNG chunk checksum mismatch")
        chunks.setdefault(kind, bytearray()).extend(body)
        offset += size + 12
    if b"IEND" not in chunks or len(chunks.get(b"IHDR", b"")) != 13:
        raise ValueError("truncated PNG")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[b"IHDR"]
    )
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if (
        not width
        or not height
        or not (depth == 8 or color == 3 and depth in (1, 2, 4))
        or channels is None
        or any((compression, filtering, interlace))
    ):
        raise ValueError("export a non-interlaced PNG with 8-bit channels or a palette")
    try:
        raw = zlib.decompress(chunks.get(b"IDAT", b""))
    except zlib.error:
        raise ValueError("truncated PNG") from None
    stride = (width * channels * depth + 7) // 8
    filter_bytes = max(1, (channels * depth + 7) // 8)
    if len(raw) != (stride + 1) * height:
        raise ValueError("PNG pixel length does not match its dimensions")
    palette = chunks.get(b"PLTE", b"")
    alpha = chunks.get(b"tRNS", b"")
    transparent = (
        tuple(struct.unpack(">" + "H" * channels, alpha))
        if alpha and color in (0, 2)
        else None
    )
    previous = bytearray(stride)
    pixels = bytearray()
    for y in range(height):
        start = y * (stride + 1)
        filter_type = raw[start]
        if filter_type > 4:
            raise ValueError("unknown PNG row filter")
        row = bytearray(raw[start + 1 : start + 1 + stride])
        for x in range(stride):
            a = row[x - filter_bytes] if x >= filter_bytes else 0
            b = previous[x]
            c = previous[x - filter_bytes] if x >= filter_bytes else 0
            predictor = (0, a, b, (a + b) // 2, paeth(a, b, c))[filter_type]
            row[x] = (row[x] + predictor) & 255
        for x in range(width):
            p = tuple(row[x * channels : (x + 1) * channels])
            if color == 3:
                bit = x * depth
                index = (row[bit // 8] >> (8 - depth - bit % 8)) & ((1 << depth) - 1)
                if index * 3 + 3 > len(palette):
                    raise ValueError("PNG pixel exceeds palette")
                rgba = (
                    *palette[index * 3 : index * 3 + 3],
                    alpha[index] if index < len(alpha) else 255,
                )
            elif color in (0, 4):
                rgba = (
                    p[0],
                    p[0],
                    p[0],
                    p[1] if color == 4 else 0 if p == transparent else 255,
                )
            else:
                rgba = p if color == 6 else (*p, 0 if p == transparent else 255)
            pixels.extend(rgba)
        previous = row
    return width, height, bytes(pixels)


def describe(resource_id: int, offset: int, data: bytes, name: str = "") -> dict:
    """Catalog entry of a native BMap from its bytes."""
    if len(data) < 28:
        raise ValueError(f"{resource_id:#x}: truncated bitmap")
    fmt, _, stride, depth = struct.unpack_from("<4H", data)
    height, width = struct.unpack_from("<II", data, 16)
    start = 28 if struct.unpack_from("<I", data, 24)[0] == len(data) - 28 else 32
    if len(data) < start:
        raise ValueError(f"{resource_id:#x}: truncated bitmap")
    if struct.unpack_from("<I", data, start - 4)[0] != len(data) - start:
        raise ValueError(f"{resource_id:#x}: invalid bitmap length")
    if fmt not in DEPTHS or depth != DEPTHS[fmt] or not width or not height:
        raise ValueError(f"{resource_id:#x}: unsupported native bitmap format")
    colors = struct.unpack_from("<I", data, start)[0] if fmt in PALETTE_FORMATS else 0
    pixels = start + 4 + colors * 4 if colors else start
    if (colors and colors > 1 << depth) or stride < (width * depth + 7) // 8:
        raise ValueError(f"{resource_id:#x}: invalid palette or stride")
    if pixels + stride * height != len(data):
        raise ValueError(f"{resource_id:#x}: invalid pixel storage")
    return {
        "id": resource_id,
        "name": name,
        "offset": offset,
        "bytes": len(data),
        "format": fmt,
        "depth": depth,
        "width": width,
        "height": height,
        "stride": stride,
        "data_offset": start + (4 if colors else 0),
        "pixels_offset": pixels,
        "palette_colors": colors,
        "crc32": zlib.crc32(data),
    }


def tint_kind(fmt: int) -> str | None:
    """How a format takes a tint: masks at draw time, palettes and BGRA8888
    pixels by rewriting their colours on the device; RGB565 has neither palette
    nor alpha."""
    if fmt in MASK_FORMATS:
        return "mask"
    if fmt in PALETTE_FORMATS:
        return "palette"
    if fmt in BGRA_FORMATS:
        return "bgra"
    return None


def encode_pixels(info: dict, width: int, height: int, rgba: bytes) -> bytes:
    """Record payload of a catalog bitmap from RGBA pixels of its native size.
    4-bit masks round to the 16 gray levels the format stores."""
    if (width, height) != (info["width"], info["height"]):
        raise ValueError(
            f"expected {info['width']}x{info['height']}, got {width}x{height}"
        )
    colors = [rgba[i : i + 4] for i in range(0, len(rgba), 4)]
    if len(colors) != width * height:
        raise ValueError("invalid PNG pixel count")
    result = bytearray(info["bytes"] - info["data_offset"])
    fmt, stride = info["format"], info["stride"]
    start = info["pixels_offset"] - info["data_offset"]
    capacity = info["palette_colors"]
    if capacity:
        unique = list(dict.fromkeys(colors))
        if len(unique) > capacity:
            raise ValueError(
                f"{len(unique)} colours exceed the {capacity} of its palette"
            )
        lookup = {color: index for index, color in enumerate(unique)}
        for index, (red, green, blue, alpha) in enumerate(unique):
            result[index * 4 : index * 4 + 4] = bytes((blue, green, red, alpha))
        for y in range(height):
            for x in range(width):
                at = start + y * stride + x * (info["depth"] // 8)
                index = lookup[colors[y * width + x]]
                if fmt == INDEXED8:
                    result[at] = index
                else:
                    struct.pack_into("<H", result, at, index)
        return bytes(result)
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = colors[y * width + x]
            at = start + y * stride + x * (info["depth"] // 8)
            if fmt == BGRA8888:
                result[at : at + 4] = bytes((blue, green, red, alpha))
            elif fmt == RGB565:
                if alpha != 255:
                    raise ValueError("native RGB565 requires opaque pixels")
                struct.pack_into(
                    "<H", result, at, (red >> 3) << 11 | (green >> 2) << 5 | blue >> 3
                )
            else:
                if red != green or green != blue or alpha != 255:
                    raise ValueError("native grayscale requires opaque gray levels")
                if fmt == MASK8:
                    result[at] = red
                else:
                    at = start + y * stride + x // 2
                    shift = 4 if x % 2 == 0 else 0
                    result[at] = (result[at] & ~(15 << shift)) | (
                        round(red / 17) << shift
                    )
    return bytes(result)


def palette_indices_fit(info: dict, payload: bytes) -> bool:
    """True when every pixel of a paletted record payload indexes its palette."""
    capacity = info["palette_colors"]
    if not capacity:
        return True
    start = info["pixels_offset"] - info["data_offset"]
    width = info["depth"] // 8
    for y in range(info["height"]):
        for x in range(info["width"]):
            at = start + y * info["stride"] + x * width
            if int.from_bytes(payload[at : at + width], "little") >= capacity:
                return False
    return True


def decode_pixels(info: dict, payload: bytes) -> bytes:
    """RGBA pixels of a catalog bitmap from its record payload, the inverse of
    encode_pixels. RGB565 channels expand with zero low bits."""
    fmt, stride = info["format"], info["stride"]
    width, height = info["width"], info["height"]
    start = info["pixels_offset"] - info["data_offset"]
    palette = []
    for i in range(info["palette_colors"]):
        blue, green, red, alpha = payload[i * 4 : i * 4 + 4]
        palette.append(bytes((red, green, blue, alpha)))
    out = bytearray()
    for y in range(height):
        row = start + y * stride
        for x in range(width):
            if fmt == INDEXED8:
                out += palette[payload[row + x]]
            elif fmt == INDEXED16:
                out += palette[struct.unpack_from("<H", payload, row + 2 * x)[0]]
            elif fmt == BGRA8888:
                blue, green, red, alpha = payload[row + 4 * x : row + 4 * x + 4]
                out += bytes((red, green, blue, alpha))
            elif fmt == RGB565:
                out += bytes(
                    (
                        *unpack_565(struct.unpack_from("<H", payload, row + 2 * x)[0]),
                        255,
                    )
                )
            elif fmt == MASK8:
                out += bytes((payload[row + x],) * 3) + b"\xff"
            else:
                nibble = payload[row + x // 2] >> (4 if x % 2 == 0 else 0) & 15
                out += bytes((nibble * 17,) * 3) + b"\xff"
    return bytes(out)


def write_png(width: int, height: int, rgba: bytes) -> bytes:
    """An RGBA PNG with unfiltered rows."""
    rows = b"".join(
        b"\0" + rgba[y * width * 4 : (y + 1) * width * 4] for y in range(height)
    )

    def chunk(kind, body):
        return (
            struct.pack(">I", len(body))
            + kind
            + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def pack_565(red, green, blue):
    return (red >> 3) << 11 | (green >> 2) << 5 | blue >> 3


def unpack_565(word):
    return (word >> 11) << 3, (word >> 5 & 63) << 2, (word & 31) << 3


def is_565(rgba):
    """True for an opaque colour RGB565 stores exactly."""
    red, green, blue, alpha = rgba
    return alpha == 255 and not (red & 7 or green & 3 or blue & 7)


def coverage(rgba: bytes) -> bytes:
    """Per-pixel coverage of tinted art: the alpha channel when the PNG uses one,
    otherwise the gray level. Coloured, opaque art has no single coverage."""
    alpha = rgba[3::4]
    if any(value != 255 for value in alpha):
        return bytes(alpha)
    if any(
        rgba[i] != rgba[i + 1] or rgba[i + 1] != rgba[i + 2]
        for i in range(0, len(rgba), 4)
    ):
        raise ValueError("tinted art must be grayscale or carry alpha coverage")
    return bytes(rgba[::4])


def gray_pixels(levels: bytes) -> bytes:
    """Opaque gray pixels of a coverage, for a native mask."""
    return b"".join(bytes((value, value, value, 255)) for value in levels)


def distinct(rgba: bytes) -> int:
    """Distinct colours of RGBA pixels."""
    return len({rgba[i : i + 4] for i in range(0, len(rgba), 4)})


def fit_levels(levels: bytes, capacity: int) -> bytes:
    """Coverage reduced to what a palette of `capacity` entries holds, so the
    result does not depend on the colour it is painted in afterwards."""
    return fit_palette(b"".join(bytes((0, 0, 0, level)) for level in levels), capacity)[
        3::4
    ]


def tinted_pixels(levels: bytes, tint: str) -> bytes:
    """Placeholder-coloured pixels whose alpha carries the coverage; the device
    rewrites the palette entries or BGRA8888 pixels with the live role colour."""
    color = bytes.fromhex(tint.removeprefix("#"))
    return b"".join(color + bytes((level,)) if level else bytes(4) for level in levels)


def premultiplied(color):
    return tuple(value * color[3] / 255 for value in color[:3]) + (color[3],)


def fit_palette(rgba: bytes, capacity: int) -> bytes:
    """Weighted median cut in premultiplied RGBA, reserving transparent pixels."""
    pixels = [tuple(rgba[i : i + 4]) for i in range(0, len(rgba), 4)]
    counts = Counter(pixels)
    if len(counts) <= capacity:
        return rgba
    transparent = any(color[3] == 0 for color in counts)
    palette = [(0, 0, 0, 0)] if transparent and capacity > 1 else []
    colors = [color for color in counts if color[3] or not palette]
    points = {color: premultiplied(color) for color in colors}
    boxes = [colors] if colors else []
    while len(boxes) + len(palette) < capacity:
        candidates = []
        for i, box in enumerate(boxes):
            if len(box) < 2:
                continue
            spans = [
                max(points[c][axis] for c in box) - min(points[c][axis] for c in box)
                for axis in range(4)
            ]
            axis = max(range(4), key=spans.__getitem__)
            candidates.append((spans[axis] ** 2 * sum(counts[c] for c in box), i, axis))
        if not candidates:
            break
        _, index, axis = max(candidates)
        box = sorted(boxes.pop(index), key=lambda color: (points[color][axis], color))
        halfway = sum(counts[c] for c in box) / 2
        accumulated = 0
        split = 1
        for split, color in enumerate(box[:-1], 1):
            accumulated += counts[color]
            if accumulated >= halfway:
                break
        boxes.extend((box[:split], box[split:]))
    for box in boxes:
        total = sum(counts[c] for c in box)
        palette.append(
            tuple(
                round(sum(c[axis] * counts[c] for c in box) / total)
                for axis in range(4)
            )
        )
    palette_points = [premultiplied(color) for color in palette]
    mapping = {}
    for color in counts:
        point = premultiplied(color)
        index = min(
            range(len(palette)),
            key=lambda i: sum((a - b) ** 2 for a, b in zip(point, palette_points[i])),
        )
        mapping[color] = bytes(palette[index])
    return b"".join(mapping[color] for color in pixels)
