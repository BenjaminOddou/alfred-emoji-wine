"""Minimal pure-Python PNG reader/writer, enough to pad the bundled icons.

Supports non-interlaced 8-bit PNGs (grayscale, RGB, palette, +alpha variants).
"""

from __future__ import annotations

import struct
import zlib

_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _chunks(data: bytes):
    pos = len(_SIGNATURE)
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> list:
    stride = width * bpp
    rows: list = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        kind = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for i in range(stride):
            left = line[i - bpp] if i >= bpp else 0
            up = prev[i]
            if kind == 1:
                line[i] = (line[i] + left) & 255
            elif kind == 2:
                line[i] = (line[i] + up) & 255
            elif kind == 3:
                line[i] = (line[i] + ((left + up) >> 1)) & 255
            elif kind == 4:
                upleft = prev[i - bpp] if i >= bpp else 0
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else upleft)
                line[i] = (line[i] + pred) & 255
        rows.append(line)
        prev = line
    return rows


def read_rgba(data: bytes) -> tuple:
    """Decode a PNG into (width, height, rows of RGBA bytes)."""
    if not data.startswith(_SIGNATURE):
        raise ValueError("not a PNG file")
    idat, palette, trns = b"", b"", b""
    width = height = depth = ctype = interlace = 0
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
    if depth != 8 or interlace or ctype not in _CHANNELS:
        raise ValueError("unsupported PNG (need 8-bit, non-interlaced)")
    channels = _CHANNELS[ctype]
    rows = _unfilter(zlib.decompress(idat), width, height, channels)
    out = []
    for row in rows:
        rgba = bytearray()
        for x in range(width):
            px = row[x * channels:(x + 1) * channels]
            if ctype == 6:
                rgba += px
            elif ctype == 2:
                rgba += px + b"\xff"
            elif ctype == 0:
                rgba += bytes((px[0], px[0], px[0], 255))
            elif ctype == 4:
                rgba += bytes((px[0], px[0], px[0], px[1]))
            else:  # palette
                idx = px[0]
                alpha = trns[idx] if idx < len(trns) else 255
                rgba += palette[idx * 3:idx * 3 + 3] + bytes((alpha,))
        out.append(bytes(rgba))
    return width, height, out


def write_rgba(width: int, height: int, rows: list) -> bytes:
    """Encode RGBA rows as a PNG."""

    def chunk(kind: bytes, body: bytes) -> bytes:
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc)

    raw = b"".join(b"\x00" + row for row in rows)
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        _SIGNATURE
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def pad_png(data: bytes, padding: int) -> bytes:
    """Return the PNG surrounded by `padding` transparent pixels in total (split evenly)."""
    width, height, rows = read_rgba(data)
    left = top = padding // 2
    new_w, new_h = width + padding, height + padding
    blank = bytes(4 * new_w)
    pad_left = bytes(4 * left)
    pad_right = bytes(4 * (new_w - width - left))
    padded = [blank] * top
    padded += [pad_left + row + pad_right for row in rows]
    padded += [blank] * (new_h - height - top)
    return write_rgba(new_w, new_h, padded)
