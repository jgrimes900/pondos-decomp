/*
 * VGA text console: 80x25, light grey on black, no scrolling - output wraps
 * back to the top-left corner after the last cell.
 */
#include "kernel.h"

#define COLS  80
#define CELLS 2000

u32 cursor_pos = 0x50;          /* [0x1C00]: starts on line 2 */

void set_cursor(u16 pos)
{
	outb(0x3D4, 0x0F);
	outb(0x3D5, pos & 0xFF);
	outb(0x3D4, 0x0E);
	outb(0x3D5, pos >> 8);
}

void puts(const char *s)
{
	u64 flags = irq_save();
	volatile u16 *vga = PTR(VGA_TEXT);
	u32 pos = cursor_pos;

	for (; *s; s++) {
		if (*s == '\r')
			continue;
		if (*s == '\n') {
			/* blank to the end of the line (at least one cell) */
			do {
				vga[pos] = 0x0720;
				if (++pos == CELLS)
					pos = 0;
			} while (pos % COLS);
			continue;
		}
		vga[pos] = 0x0700 | (u8)*s;
		if (++pos == CELLS)
			pos = 0;
	}
	set_cursor(pos);
	cursor_pos = pos;
	irq_restore(flags);
}

void putc(char c)
{
	char s[2] = { c, 0 };
	puts(s);
}

void newline(void)
{
	putc('\n');
}

/* Write the decimal digits of v backwards, ending just before 'end'. */
char *utoa_back(u64 v, char *end)
{
	do {
		*--end = '0' + v % 10;
		v /= 10;
	} while (v);
	return end;
}

void print_u64(u64 v)
{
	char buf[32];
	buf[31] = 0;
	puts(utoa_back(v, &buf[31]));
}

void print_u64_nl(u64 v)
{
	u64 flags = irq_save();
	print_u64(v);
	newline();
	irq_restore(flags);
}
