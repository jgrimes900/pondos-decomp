/*
 * Physical memory and page tables.
 *
 * Free physical pages (only those at or above 2 MiB) are tracked by two
 * bitmaps, one bit per 4 KiB page:
 *   B at 0xFFFFC00000000000: the page is free
 *   A at 0xFFFF800000000000: the page is free or owned by user mappings
 *                            (allocations for kernel addresses clear it too)
 * Pages are never freed.  Page tables are edited through the recursive
 * PML4[511] slot.
 */
#include "kernel.h"

struct e820 {               /* after normalisation: base, end, usable */
	i64 base;
	i64 len;            /* becomes the end address */
	u32 type;           /* becomes 1 = usable, 0 = not */
	u32 ext;
};

static u32 bitmap_hint;     /* [0x1C7C] byte offset where the last page came from */
static u32 bitmap_bytes;    /* [0x1C80] bytes of bitmap currently mapped */

/*
 * Allocate a physical page from bitmap B.  When keep_in_a is false the page
 * is also removed from bitmap A.  Returns 0 when memory is exhausted.
 * The scan starts at the hint and does not wrap around.
 */
u64 page_alloc(bool keep_in_a)
{
	volatile u64 *b = PTR(BITMAP_B), *a = PTR(BITMAP_A);
	for (u32 off = bitmap_hint; off != bitmap_bytes; off += 8) {
		u64 w = b[off / 8];
		if (!w)
			continue;
		bitmap_hint = off;
		u32 bit = __builtin_ctzll(w);
		b[off / 8] = w & ~(1ULL << bit);
		if (!keep_in_a)
			a[off / 8] &= ~(1ULL << bit);
		return ((u64)off * 8 + bit) << 12;
	}
	return 0;
}

static inline bool is_user_va(u64 va)
{
	return va >= USER_BASE && va < USER_LIMIT;
}

/*
 * Map one page at 'va' with the given flags (P/W/U/PCD/NX), allocating the
 * intermediate tables and the frame as needed.  A page that is already
 * mapped keeps its frame.  When P is requested the page is zeroed; a
 * read-only page is zeroed through a writable mapping first.
 * Fails if memory runs out or a user mapping would go through a supervisor
 * table.
 */
bool map_page(u64 va, u64 flags)
{
	const bool user = is_user_va(va);
	const u64 leaf_flags = flags & 0x800000000000001FULL;
	const u64 dir_flags = (flags & 7) | PTE_W;
	u64 page = va & ~0xFFFULL;

	/* table entry addresses for PML4, PDPT, PD and PT via the recursive slot */
	volatile u64 *ent[4] = {
		PTR(((page >> 36) & ~7ULL) | PT_SELF_PML4),
		PTR(((page >> 27) & ~7ULL) | PT_SELF_PDPT),
		PTR(((page >> 18) & ~7ULL) | PT_SELF_PD),
		PTR(((page >> 9)  & ~7ULL) | PT_SELF_PT),
	};

	for (int lvl = 0; lvl < 3; lvl++) {
		bool fresh = false, changed;
		u64 e = *ent[lvl];
		if (!(e & PTE_P)) {
			e = page_alloc(user);
			if (!e)
				return false;
			fresh = true;
		}
		if ((dir_flags & PTE_U) && (e & PTE_P) && !(e & PTE_U))
			return false;
		changed = fresh || (e & 0xFFF) != dir_flags;
		*ent[lvl] = e | dir_flags;
		if (changed)
			invlpg((u64)ent[lvl + 1]);
		if (fresh)
			memset((void *)((u64)ent[lvl + 1] & ~0xFFFULL), 0, 0x1000);
	}

	u64 e = *ent[3];
	if (!(e & PTE_P)) {
		e = page_alloc(user);
		if (!e)
			return false;
	}
	if ((dir_flags & PTE_U) && (e & PTE_P) && !(e & PTE_U))
		return false;
	u64 frame = e & ~0xFFFULL;
	u64 final = leaf_flags | frame;
	*ent[3] = frame | leaf_flags | PTE_W;
	invlpg(page);
	if (final & PTE_P) {
		memset(PTR(page), 0, 0x1000);
		if (!(final & PTE_W)) {
			*ent[3] = final;
			invlpg(page);
		}
	}
	return true;
}

/*
 * Look up 'va'.  Returns the frame address ORed with the P/W/U bits common
 * to all four levels, or 0 if the page is not mapped.
 */
u64 page_query(u64 va)
{
	const u64 sh[4] = { 36, 27, 18, 9 };
	const u64 base[4] = { PT_SELF_PML4, PT_SELF_PDPT, PT_SELF_PD, PT_SELF_PT };
	u64 flags = 7, e = 0;
	for (int i = 0; i < 4; i++) {
		e = *(volatile u64 *)(((va >> sh[i]) & ~7ULL) | base[i]);
		if (!(e & PTE_P))
			return 0;
		flags &= e;
	}
	return flags | (e & ~0xFFFULL & ~PTE_NX);
}

/* Every page touched by [p, p+len) must be present and user-accessible. */
bool user_buffer_ok(u64 p, i32 len)
{
	while (len > 0) {
		if ((page_query(p) & 5) != 5)
			return false;
		u64 next = (p + 0x1000) & ~0xFFFULL;
		len += (i32)(p - next);
		p = next;
	}
	return true;
}

/*
 * Normalise the E820 map and build the free-page bitmaps.
 */
bool mem_init(void)
{
	struct e820 *m = PTR(E820_MAP_ADDR);
	u32 n = MMIO32(E820_COUNT_ADDR);

	/* "Sort" by base: each entry is swapped (not shifted) into the slot
	 * after the last entry with a smaller-or-equal base. */
	for (u32 i = 1; i < n; i++) {
		u32 j = i;
		while (m[i].base < m[j - 1].base && --j)
			;
		struct e820 t = m[i];
		m[i] = m[j];
		m[j] = t;
	}

	/* Convert to [base, end) with type 1 = usable, resolving overlaps
	 * between neighbours: same type merges, usable memory loses to the
	 * other type. */
	u32 last = n - 1;
	m[last].type = m[last].type == 1;
	m[last].len += m[last].base;
	for (u32 i = 0; i < last; i++) {
		struct e820 *c = &m[i], *nx = &m[i + 1];
		nx->type = nx->type == 1;
		nx->len += nx->base;
		if (c->len <= nx->base)
			continue;
		if (c->type == nx->type) {
			if (nx->len < c->len)
				nx->len = c->len;
			c->len = nx->base;
		} else if (c->type == 1) {
			c->len = nx->base;
		} else {
			nx->len = c->len;
			nx->type = 0;
			c->len = nx->base;
		}
	}
	for (u32 i = 0; i < n; i++) {
		u64 b = (m[i].base + 0xFFF) & ~0xFFFULL;
		u64 e = m[i].len & ~0xFFFULL;
		if (b >= e)
			b = e = 0;
		m[i].base = b;
		m[i].len = e;
	}

	/* First page of each bitmap: A at phys 0x16000, B at 0x17000, reached
	 * through tables at 0x10000-0x15000. */
	memset(PTR(BITMAP_PT_BASE), 0, 0x8000);
	MMIO32(PML4_ADDR + 256 * 8) = 0x10003;
	MMIO32(0x10000) = 0x11003;
	MMIO32(0x11000) = 0x12003;
	MMIO32(0x12000) = 0x16003;
	invlpg(BITMAP_A);
	MMIO32(PML4_ADDR + 384 * 8) = 0x13003;
	MMIO32(0x13000) = 0x14003;
	MMIO32(0x14000) = 0x15003;
	MMIO32(0x15000) = 0x17003;
	invlpg(BITMAP_B);
	bitmap_bytes = 0x1000;

	volatile u64 *a = PTR(BITMAP_A), *b = PTR(BITMAP_B);
	for (u32 i = 0; i < n; i++) {
		if (!m[i].type || m[i].base == m[i].len)
			continue;
		for (u64 p = m[i].base; p != (u64)m[i].len; p += 0x1000) {
			while (p >= (u64)bitmap_bytes * 0x8000) {
				if (!map_page(BITMAP_B + bitmap_bytes, PTE_NX | PTE_W | PTE_P) ||
				    !map_page(BITMAP_A + bitmap_bytes, PTE_NX | PTE_W | PTE_P)) {
					puts("Memory Alloc For Page Map Failed!\n");
					return false;
				}
				bitmap_bytes += 0x1000;
			}
			if (p >= 0x200000) {
				u64 bit = 1ULL << ((p >> 12) & 63);
				b[p >> 18] |= bit;
				a[p >> 18] |= bit;
			}
		}
	}
	return true;
}
