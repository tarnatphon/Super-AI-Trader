#!/usr/bin/env python3
"""Generate the Super-AI-Trader app icon with only the Python standard library.

Creates:
  desktop/app.png   — 256x256 source icon (green rounded tile + rising chart)
  desktop/app.ico   — Windows icon (multi-size, PNG-compressed entries)
  desktop/app.icns  — macOS icon (PNG-based entries, works on modern macOS)

Run:  python3 desktop/make_icon.py
No third-party libraries needed.
"""
from __future__ import annotations

import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 256

# Brand colours
GREEN_TOP = (41, 196, 132)
GREEN_BOT = (18, 138, 92)
DARK = (10, 18, 28)
WHITE = (238, 246, 255)


def _new_canvas(size: int):
    return [0] * (size * size * 4)


def _set(px, size, x, y, rgba):
    x = int(round(x)); y = int(round(y))
    if 0 <= x < size and 0 <= y < size:
        r, g, b, a = rgba
        i = (y * size + x) * 4
        # simple over-blend for anti-aliasing
        if a >= 255 or px[i + 3] == 0:
            px[i:i + 4] = [r, g, b, a]
        else:
            ia = a / 255
            px[i] = int(r * ia + px[i] * (1 - ia))
            px[i + 1] = int(g * ia + px[i + 1] * (1 - ia))
            px[i + 2] = int(b * ia + px[i + 2] * (1 - ia))
            px[i + 3] = max(px[i + 3], a)


def _disc(px, size, cx, cy, radius, color):
    r2 = (radius + 1) ** 2
    for yy in range(int(cy - radius - 2), int(cy + radius + 2)):
        for xx in range(int(cx - radius - 2), int(cx + radius + 2)):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if d2 <= radius * radius:
                _set(px, size, xx, yy, color)
            elif d2 <= r2:
                edge = max(0.0, min(1.0, (radius + 1 - (d2 ** 0.5))))
                _set(px, size, xx, yy, (color[0], color[1], color[2], int(255 * edge)))


def _line(px, size, x0, y0, x1, y1, width, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / steps
        _disc(px, size, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, width / 2, color)


def draw(size: int = SIZE) -> bytes:
    px = _new_canvas(size)
    s = size / SIZE
    radius = 58 * s

    # Rounded-square background with vertical gradient.
    for yy in range(size):
        for xx in range(size):
            # rounded corner test
            cx = min(max(xx, radius), size - radius)
            cy = min(max(yy, radius), size - radius)
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= radius * radius:
                t = yy / size
                r = int(GREEN_TOP[0] * (1 - t) + GREEN_BOT[0] * t)
                g = int(GREEN_TOP[1] * (1 - t) + GREEN_BOT[1] * t)
                b = int(GREEN_TOP[2] * (1 - t) + GREEN_BOT[2] * t)
                _set(px, size, xx, yy, (r, g, b, 255))

    # White rising chart line (steady growth) with node dots.
    pts = [(58, 178), (112, 132), (150, 150), (202, 86)]
    pts = [(x * s, y * s) for x, y in pts]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        _line(px, size, x0, y0, x1, y1, 15 * s, (*WHITE, 255))
    for x, y in pts:
        _disc(px, size, x, y, 11 * s, (*DARK, 255))
        _disc(px, size, x, y, 6 * s, (*WHITE, 255))

    # Small shield/check accent in the corner (safety).
    sx, sy = 60 * s, 58 * s
    _disc(px, size, sx, sy, 20 * s, (*WHITE, 235))
    _line(px, size, sx - 8 * s, sy + 1 * s, sx - 2 * s, sy + 7 * s, 5 * s, (*GREEN_BOT, 255))
    _line(px, size, sx - 2 * s, sy + 7 * s, sx + 9 * s, sy - 6 * s, 5 * s, (*GREEN_BOT, 255))

    return bytes(px)


def write_png(path: str, size: int, raw: bytes):
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw_pixel = raw
    # scale raw (SIZE) down to requested size via nearest neighbour
    if size != SIZE:
        scaled = bytearray(size * size * 4)
        for y in range(size):
            for x in range(size):
                sx = min(SIZE - 1, int(x * SIZE / size))
                sy = min(SIZE - 1, int(y * SIZE / size))
                src = (sy * SIZE + sx) * 4
                dst = (y * size + x) * 4
                scaled[dst:dst + 4] = raw_pixel[src:src + 4]
        raw_pixel = bytes(scaled)
    scan = b"".join(b"\x00" + raw_pixel[y * size * 4:(y + 1) * size * 4]
                    for y in range(size))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(scan, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def write_ico(path: str, sizes=(16, 24, 32, 48, 64, 128, 256)):
    blobs = []
    base = draw(SIZE)
    for sz in sizes:
        png_path = path + f".{sz}.png"
        write_png(png_path, sz, base)
        blobs.append((sz, open(png_path, "rb").read()))
        os.remove(png_path)
    header = struct.pack("<HHH", 0, 1, len(blobs))
    entries = b""
    offset = 6 + 16 * len(blobs)
    data = b""
    for sz, blob in blobs:
        wh = 0 if sz >= 256 else sz
        entries += struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(blob), offset)
        data += blob
        offset += len(blob)
    with open(path, "wb") as f:
        f.write(header + entries + data)


def write_icns(path: str, sizes=(32, 64, 128, 256, 512)):
    # ICNS with PNG ('icp5','icp6','ic07','ic08','ic09') entries.
    codes = {32: b"icp5", 64: b"icp6", 128: b"ic07", 256: b"ic08", 512: b"ic09"}
    base = draw(SIZE)
    body = b""
    for sz in sizes:
        tmp = path + f".{sz}.png"
        write_png(tmp, min(sz, SIZE) if sz <= SIZE else SIZE, base)
        blob = open(tmp, "rb").read()
        os.remove(tmp)
        body += codes.get(sz, b"ic08") + struct.pack(">I", len(blob) + 8) + blob
    with open(path, "wb") as f:
        f.write(b"icns" + struct.pack(">I", len(body) + 8) + body)


def main():
    raw = draw(SIZE)
    write_png(os.path.join(HERE, "app.png"), SIZE, raw)
    write_ico(os.path.join(HERE, "app.ico"))
    write_icns(os.path.join(HERE, "app.icns"))
    print("Icons written to desktop/: app.png, app.ico, app.icns")


if __name__ == "__main__":
    main()
