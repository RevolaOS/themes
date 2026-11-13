# SPDX-License-Identifier: GPL-3.0-only
"""The lz codec of the RevolaOS core: the bit layout in revola/core/loader/rvx.h,
which the appearance extension decodes on the iPod. A copy of lz_encode and
lz_decode in revola/tools/rvx.py; tests/test_bitmaps.py pins the stream of a
known input so the two copies cannot drift apart unnoticed.

Groups of a flag byte and up to 8 items, bit 0 first. A clear bit is a literal
byte. A set bit is a match of two bytes, LLLLDDDD DDDDDDDD: it copies L + 3
bytes from D + 1 bytes back in the output; L = 15 adds the following bytes to
the length while they are 255, and the first that is not. The stream carries
no length: a decoder stops when the output is full and the stream must end
there.
"""

from rvt import rvtfile

WINDOW = rvtfile.LZ_WINDOW
MIN_MATCH = rvtfile.LZ_MIN_MATCH
CHAIN = 48  # earlier positions tried per match search


def lz_match(data, i, positions):
    """Longest match for data[i:] among earlier positions in the window."""
    best_length = best_distance = 0
    limit = len(data) - i
    for j in reversed(positions[-CHAIN:]):
        distance = i - j
        if distance > WINDOW:
            break
        length = MIN_MATCH
        while length < limit and data[j + length] == data[i + length]:
            length += 1
        if length > best_length:
            best_length, best_distance = length, distance
            if length == limit:
                break
    return best_length, best_distance


def lz_encode(data):
    """The lz stream for `data`: greedy matching with one step of lookahead."""
    heads = {}
    items = []

    def remember(i):
        if i + MIN_MATCH <= len(data):
            chain = heads.setdefault(data[i : i + MIN_MATCH], [])
            chain.append(i)
            if len(chain) > 2 * CHAIN:
                del chain[:CHAIN]

    def search(i):
        if i + MIN_MATCH > len(data):
            return 0, 0
        return lz_match(data, i, heads.get(data[i : i + MIN_MATCH], []))

    i = 0
    pending = search(0)
    while i < len(data):
        length, distance = pending
        if length:
            remember(i)
            ahead = search(i + 1)
            if ahead[0] > length + 1:
                items.append(bytes((data[i],)))
                i += 1
                pending = ahead
                continue
            extra = length - MIN_MATCH
            nibble = min(extra, 15)
            match = bytes((nibble << 4 | (distance - 1) >> 8, (distance - 1) & 0xFF))
            if nibble == 15:
                extra -= 15
                match += b"\xff" * (extra // 255) + bytes((extra % 255,))
            items.append(match)
            for k in range(i + 1, i + length):
                remember(k)
            i += length
        else:
            items.append(bytes((data[i],)))
            remember(i)
            i += 1
        pending = search(i)
    out = bytearray()
    for group in range(0, len(items), 8):
        chunk = items[group : group + 8]
        out.append(sum(1 << bit for bit, item in enumerate(chunk) if len(item) > 1))
        for item in chunk:
            out += item
    return bytes(out)


def lz_decode(stream, size):
    """`size` bytes decoded from an lz stream, which must end exactly there."""
    out = bytearray()
    at = 0
    try:
        while len(out) < size:
            flags = stream[at]
            at += 1
            for bit in range(8):
                if len(out) == size:
                    break
                if not flags >> bit & 1:
                    out.append(stream[at])
                    at += 1
                    continue
                high, low = stream[at], stream[at + 1]
                at += 2
                length = (high >> 4) + MIN_MATCH
                distance = ((high & 15) << 8 | low) + 1
                if high >> 4 == 15:
                    while True:
                        more = stream[at]
                        at += 1
                        length += more
                        if more != 255:
                            break
                if distance > len(out) or len(out) + length > size:
                    raise ValueError("lz match outside the output")
                for _ in range(length):
                    out.append(out[-distance])
    except IndexError:
        raise ValueError("lz stream ends early") from None
    if at != len(stream):
        raise ValueError("lz stream continues past its output")
    return bytes(out)
