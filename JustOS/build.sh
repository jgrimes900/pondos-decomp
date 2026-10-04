#!/bin/sh
# Rebuild JustOS from the reconstructed sources and check that every
# binary is byte-identical to the originals in Bin/.
#
#   ./build.sh          assemble into Build/ and verify
#
# Requires: nasm, python3
set -e
cd "$(dirname "$0")"
mkdir -p Build Build/orig

nasm -O0 -f bin -o Build/bootload.bin Source/boot/bootload.asm
nasm -O0 -f bin -o Build/KERNEL.BIN   Source/kernel/kernel.asm
nasm -O0 -f bin -I Source/programs/ -o Build/TEST_PRG.BIN Source/programs/test_prg.asm
nasm -O0 -f bin -I Source/programs/ -o Build/IMGVIEW.BIN  Source/programs/imgview.asm

# Pull the originals out of the shipped floppy images
python3 Tools/fat12.py extract Bin/JustOS.img Build/orig >/dev/null
python3 Tools/fat12.py extract Bin/disk.img   Build/orig >/dev/null
dd if=Bin/JustOS.img of=Build/orig/bootload.bin bs=512 count=1 2>/dev/null

status=0
for f in bootload.bin KERNEL.BIN TEST_PRG.BIN IMGVIEW.BIN; do
	if cmp -s "Build/$f" "Build/orig/$f"; then
		echo "  identical  $f"
	else
		echo "  DIFFERENT  $f"; status=1
	fi
done

# A single bootable floppy with the kernel, programs and pictures
python3 Tools/fat12.py build Build/justos-full.img Build/bootload.bin \
	Build/KERNEL.BIN Build/TEST_PRG.BIN Build/IMGVIEW.BIN \
	Build/orig/GF.PIC Build/orig/THEMESS.PIC
echo "  wrote      Build/justos-full.img"
exit $status
