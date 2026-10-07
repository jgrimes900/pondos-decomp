/*
 * PCI configuration space (mechanism #1) and device discovery.
 */
#include "kernel.h"

u32 net_pci;    /* [0x1C28] config address of the virtio-net function, 0 = none */
u32 blk_pci;    /* [0x1CD0] config address of the virtio-blk function */

u32 pci_addr(u8 bus, u8 dev, u8 fn, u8 reg)
{
	return 0x80000000u | (u32)bus << 16 | (u32)dev << 11 | (u32)fn << 8 | reg;
}

u32 pci_read(u32 addr)
{
	outl(0xCF8, addr);
	return inl(0xCFC);
}

void pci_write(u32 addr, u32 val)
{
	outl(0xCF8, addr);
	outl(0xCFC, val);
}

/* Base address of a BAR, following 64-bit memory BARs into the next slot. */
u64 pci_read_bar(u32 addr)
{
	u64 v = pci_read(addr);
	if (v & 1)
		return v & ~3ULL;                       /* I/O space */
	if ((v & 6) == 4)
		v |= (u64)pci_read(addr + 4) << 32;     /* 64-bit memory */
	return v & ~0xFULL;
}

/*
 * Walk every bus/device/function and remember the first virtio-net
 * (1AF4:1000 transitional or 1AF4:1041 modern) and virtio-blk
 * (1AF4:1001 / 1AF4:1042) function.
 *
 * The multi-function test looks at bit 7 of the *vendor ID's low byte*
 * (offset 0) instead of the header type, so devices of vendors whose ID has
 * that bit set (0x8086, 0x1AF4, ...) get all eight functions probed.
 */
void pci_scan(void)
{
	u32 bus = 0;
	do {
		for (u32 dev = 0; dev < 32; dev++) {
			u32 id0 = pci_read(pci_addr(bus, dev, 0, 0));
			if ((u16)id0 == 0xFFFF)
				continue;
			for (u32 fn = 0; fn < 8; fn++) {
				u32 a = pci_addr(bus, dev, fn, 0);
				u32 id = pci_read(a);
				if ((u16)id != 0xFFFF) {
					(void)pci_read(pci_addr(bus, dev, fn, 8));   /* class, unused */
					id = pci_read(a);
					if ((u16)id == 0x1AF4) {
						u16 did = id >> 16;
						if (did == 0x1000 || did == 0x1041) {
							if (!net_pci) {
								puts("VirtIO Net Device Found\n");
								net_pci = a;
							}
						} else if (did == 0x1001 || did == 0x1042) {
							if (!blk_pci) {
								puts("VirtIO Blk Device Found\n");
								blk_pci = a;
							}
						}
					}
				}
				if (!(id0 & 0x80))
					break;
			}
		}
		bus = (bus + 1) & 0xFF;
	} while (bus);
}
