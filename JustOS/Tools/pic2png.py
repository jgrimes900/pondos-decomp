#!/usr/bin/env python3
"""Convert a JustOS .PIC (320x200, 2 bpp, linear, MSB = leftmost pixel,
16000 bytes) to PNG using the CGA mode 4 default palette (black, cyan,
magenta, white) that the kernel's draw routine displays it with.

    pic2png.py INPUT.PIC OUTPUT.png [SCALE]
"""
import struct
import sys
import zlib

WIDTH, HEIGHT = 320, 200
PALETTE = [(0x00, 0x00, 0x00), (0x55, 0xFF, 0xFF),
           (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0xFF)]


def pic_to_png(data, scale=1):
    rows = []
    for y in range(HEIGHT):
        row = bytearray()
        for x in range(WIDTH):
            i = y * WIDTH + x
            b = data[i // 4] if i // 4 < len(data) else 0
            row += bytes(PALETTE[(b >> (6 - 2 * (i % 4))) & 3]) * scale
        rows += [b'\0' + bytes(row)] * scale

    def chunk(tag, body):
        return (struct.pack('>I', len(body)) + tag + body
                + struct.pack('>I', zlib.crc32(tag + body)))

    ihdr = struct.pack('>IIBBBBB', WIDTH * scale, HEIGHT * scale, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(b''.join(rows), 9))
            + chunk(b'IEND', b''))


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    scale = int(sys.argv[3]) if len(sys.argv) == 4 else 1
    with open(sys.argv[1], 'rb') as f:
        png = pic_to_png(f.read(), scale)
    with open(sys.argv[2], 'wb') as f:
        f.write(png)
