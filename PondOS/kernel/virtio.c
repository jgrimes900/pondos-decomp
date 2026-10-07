/*
 * Virtio over PCI: capability discovery and a two-page window for reaching
 * device registers that live above the identity-mapped first 2 MiB.
 */
#include "kernel.h"

#define BOOT_PT ((volatile u64 *)PTR(BOOT_PT_ADDR))

/* Map the two pages starting at the page of 'phys' (uncached) at 0x100000
 * and return the virtual address corresponding to 'phys'. */
u64 mmio_map(u64 phys)
{
	u64 pte = (phys & ~0xFFFULL) | PTE_PCD | PTE_W | PTE_P;
	BOOT_PT[0x100] = pte;
	BOOT_PT[0x101] = pte + 0x1000;
	invlpg(MMIO_WINDOW);
	invlpg(MMIO_WINDOW + 0x1000);
	return MMIO_WINDOW + (phys & 0xFFF);
}

/* Restore the identity mapping of 0x100000-0x101FFF. */
void mmio_unmap(void)
{
	BOOT_PT[0x100] = 0x100003;
	BOOT_PT[0x101] = 0x101003;
	invlpg(MMIO_WINDOW);
	invlpg(MMIO_WINDOW + 0x1000);
}

/*
 * Walk the capability list of the PCI function at 'cfg'.  Records the first
 * common-config (type 1), notify (type 2) and device-config (type 4) virtio
 * capabilities, and enables MSI-X with table entry 0 delivering
 * 'msix_vector' to the local APIC.  Stops once all four are found.
 */
void virtio_find_caps(u32 cfg, u32 msix_vector, struct virtio_caps *c)
{
	c->found = 0;
	u32 ptr = pci_read(cfg + 0x34) & 0xFC;

	while (ptr) {
		u32 cap = cfg + ptr;
		u32 hdr = pci_read(cap);
		u32 id = hdr & 0xFF;

		if (id == 0x11 && !(c->found & 4)) {
			/* MSI-X: enable, clear function mask */
			pci_write(cap, (hdr | 0x80000000u) & 0xBFFFFFFFu);
			u32 tbl = pci_read(cap + 4);
			u64 a = pci_read_bar(cfg + 0x10 + (tbl & 7) * 4) + (tbl & ~7u);
			volatile u32 *e = PTR(mmio_map(a));
			e[0] = 0xFEE00000;          /* message address: BSP */
			e[1] = 0;
			e[2] = msix_vector;         /* message data */
			e[3] &= ~1u;                /* unmask */
			c->found |= 4;
		} else if (id == 0x09) {
			u32 type = hdr >> 24;
			u32 bar = pci_read(cap + 4) & 0xFF;
			u32 off = pci_read(cap + 8);
			if (type == 1 && !(c->found & 1)) {
				c->common = pci_read_bar(cfg + 0x10 + bar * 4) + off;
				c->found |= 1;
			} else if (type == 2 && !(c->found & 2)) {
				c->notify = pci_read_bar(cfg + 0x10 + bar * 4) + off;
				c->notify_mult = pci_read(cap + 0x10);
				c->found |= 2;
			} else if (type == 4 && !(c->found & 8)) {
				c->device = pci_read_bar(cfg + 0x10 + bar * 4) + off;
				c->found |= 8;
			}
		}
		if (c->found == 0xF)
			return;
		ptr = (pci_read(cap) >> 8) & 0xFC;
	}
}
