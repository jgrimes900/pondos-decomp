#!/usr/bin/env python3
"""Minimal FAT12 1.44 MB floppy tool for JustOS (no mtools needed).

    fat12.py list    IMAGE
    fat12.py extract IMAGE OUTDIR
    fat12.py build   IMAGE BOOTSECTOR FILE [FILE ...]

`build` writes a fresh 2880-sector image whose sector 0 is BOOTSECTOR
(BPB included) and stores each FILE in the root directory under its
upper-cased 8.3 name, contiguously, in the order given.
"""
import os
import struct
import sys

SECTOR = 512
TOTAL_SECTORS = 2880
FAT_SECTORS = 9
NUM_FATS = 2
ROOT_ENTRIES = 224
ROOT_LBA = 1 + NUM_FATS * FAT_SECTORS                  # 19
DATA_LBA = ROOT_LBA + ROOT_ENTRIES * 32 // SECTOR      # 33


def _fat_get(fat, n):
    v = fat[n * 3 // 2] | fat[n * 3 // 2 + 1] << 8
    return v >> 4 if n & 1 else v & 0xFFF


def _fat_set(fat, n, val):
    o = n * 3 // 2
    if n & 1:
        fat[o] = (fat[o] & 0x0F) | ((val << 4) & 0xF0)
        fat[o + 1] = (val >> 4) & 0xFF
    else:
        fat[o] = val & 0xFF
        fat[o + 1] = (fat[o + 1] & 0xF0) | ((val >> 8) & 0x0F)


def _entries(img):
    root = img[ROOT_LBA * SECTOR:DATA_LBA * SECTOR]
    fat = img[SECTOR:(1 + FAT_SECTORS) * SECTOR]
    for i in range(0, len(root), 32):
        e = root[i:i + 32]
        if e[0] == 0:
            break
        if e[0] == 0xE5 or e[11] == 0x0F or e[11] & 0x08:
            continue
        name = e[:8].decode('latin-1').rstrip()
        ext = e[8:11].decode('latin-1').rstrip()
        cluster, size = struct.unpack_from('<HI', e, 26)
        data = bytearray()
        while 2 <= cluster < 0xFF8:
            lba = DATA_LBA + cluster - 2
            data += img[lba * SECTOR:(lba + 1) * SECTOR]
            cluster = _fat_get(fat, cluster)
        yield name + ('.' + ext if ext else ''), e[11], bytes(data[:size])


def cmd_list(image):
    img = open(image, 'rb').read()
    for name, attr, data in _entries(img):
        print(f'{name:12} {len(data):8}  attr={attr:02X}')


def cmd_extract(image, outdir):
    img = open(image, 'rb').read()
    os.makedirs(outdir, exist_ok=True)
    for name, attr, data in _entries(img):
        if attr & 0x10:
            continue
        with open(os.path.join(outdir, name), 'wb') as f:
            f.write(data)
        print(name, len(data))


def _83(path):
    base = os.path.basename(path).upper()
    name, _, ext = base.partition('.')
    if not (1 <= len(name) <= 8 and len(ext) <= 3):
        sys.exit(f'{path}: not an 8.3 name')
    return (name.ljust(8) + ext.ljust(3)).encode('ascii')


def cmd_build(image, bootsector, files):
    boot = open(bootsector, 'rb').read()
    if len(boot) != SECTOR or boot[510:] != b'\x55\xAA':
        sys.exit('boot sector must be 512 bytes ending in 55 AA')
    img = bytearray(TOTAL_SECTORS * SECTOR)
    img[:SECTOR] = boot
    fat = bytearray(FAT_SECTORS * SECTOR)
    _fat_set(fat, 0, 0xFF0)
    _fat_set(fat, 1, 0xFFF)
    root = bytearray(ROOT_ENTRIES * 32)
    cluster = 2
    for i, path in enumerate(files):
        data = open(path, 'rb').read()
        count = max(1, -(-len(data) // SECTOR))
        first = cluster
        for c in range(first, first + count):
            _fat_set(fat, c, c + 1 if c < first + count - 1 else 0xFFF)
        lba = DATA_LBA + first - 2
        img[lba * SECTOR:lba * SECTOR + len(data)] = data
        root[i * 32:i * 32 + 32] = (_83(path) + bytes([0x20]) + bytes(14)
                                    + struct.pack('<HI', first, len(data)))
        cluster += count
    for n in range(NUM_FATS):
        o = (1 + n * FAT_SECTORS) * SECTOR
        img[o:o + len(fat)] = fat
    img[ROOT_LBA * SECTOR:DATA_LBA * SECTOR] = root
    open(image, 'wb').write(img)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'list':
        cmd_list(a[1])
    elif len(a) == 3 and a[0] == 'extract':
        cmd_extract(a[1], a[2])
    elif len(a) >= 3 and a[0] == 'build':
        cmd_build(a[1], a[2], a[3:])
    else:
        sys.exit(__doc__)
