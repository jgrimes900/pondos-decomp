/*
 * PS/2 keyboard input and the built-in debug shell.
 *
 * Typed characters are echoed and collected into a 256-byte line buffer at
 * 0x1C3F00; Enter runs the line as a command.  Esc reboots.
 *
 * Commands (first character):
 *   P            page-fault test: write to the unmapped address 1 << 44
 *   S            reboot
 *   D            print the interrupted RIP and dump registers
 *   R<s> addr    read 1/2/8 bytes (s = '1','2','8'; anything else: 4)
 *   W<s> addr v  write 1/2/4/8 bytes
 *   T            list the TCP control block free list
 *   N            packet capture: start, then stop and write a pcap to disk
 *   H a b c      write c sectors from memory address b to disk sector a
 */
#include "kernel.h"

/* Scancode set 1 -> ASCII.  Left Shift (0x2A) produces a space. */
static const char keymap[128] =
	"\0\0" "1234567890-=" "\b\t" "QWERTYUIOP[]" "\n\0"
	"ASDFGHJKL;'`" " " "\\ZXCVBNM,./" "\0\0\0" " ";

static u32 line_len;        /* [0x1D00] */
static u32 last_scancode;   /* [0x1D10] */

void dump_regs(struct intr_frame *f)
{
	static const struct intr_frame zero;
	if (!f)
		f = (struct intr_frame *)&zero;
	const u64 v[16] = { f->rax, f->rbx, f->rcx, f->rdx, f->rsi, f->rdi,
	                    f->rsp, f->rbp, f->r8, f->r9, f->r10, f->r11,
	                    f->r12, f->r13, f->r14, f->r15 };
	for (int i = 0; i < 16; i += 2) {
		print_u64(v[i]);
		puts(" ");
		print_u64_nl(v[i + 1]);
	}
}

static void skip_ws(const u8 **p, u32 *n)
{
	/* The original also compared against "\r", "\n", "\v", "\f" written as
	 * two-character constants ('\\r' etc.), which a single byte can never
	 * equal, so only space and tab are actually skipped. */
	while (*n && (**p == ' ' || **p == '\t')) {
		(*p)++;
		(*n)--;
	}
}

static u64 parse_uint(const u8 **p, u32 *n)
{
	u64 v = 0;
	while (*n && **p >= '0' && **p <= '9') {
		v = v * 10 + (**p - '0');
		(*p)++;
		(*n)--;
	}
	return v;
}

static bool readable(u64 a)  { return page_query(a) & PTE_P; }

static int writable(u64 a)
{
	u64 q = page_query(a);
	if (!(q & PTE_P))
		return 0;
	return (q & PTE_W) ? 1 : -1;
}

static void cmd_read(u8 size, u64 a)
{
	switch (size) {
	case '1':
		if (!readable(a))
			break;
		print_u64_nl(*(volatile u8 *)a);
		return;
	case '2':
		if (!readable(a) || !readable(a + 1))
			break;
		print_u64_nl(*(volatile u16 *)a);
		return;
	case '8':
		if (!readable(a) || !readable(a + 7))
			break;
		print_u64_nl(*(volatile u64 *)a);
		return;
	default:
		if (!readable(a) || !readable(a + 3))
			break;
		print_u64_nl(*(volatile u32 *)a);
		return;
	}
	puts("Page Not Present\n");
}

static void cmd_write(u8 size, u64 a, u64 v)
{
	u32 last = size == '1' ? 0 : size == '2' ? 1 : size == '8' ? 7 : 3;
	int w = writable(a);
	if (w > 0 && last)
		w = writable(a + last);
	if (w == 0) {
		puts("Page Not Present\n");
		return;
	}
	if (w < 0) {
		puts("Page Not Writable\n");
		return;
	}
	switch (size) {
	case '1': *(volatile u8 *)a = v;  break;
	case '2': *(volatile u16 *)a = v; break;
	case '8': *(volatile u64 *)a = v; break;
	default:  *(volatile u32 *)a = v; break;
	}
}

static void shell_command(const u8 *p, u32 n, struct intr_frame *f)
{
	if (!n)
		return;
	u8 c = *p++;
	n--;

	switch (c) {
	case 'P':
		line_len = 0;
		*(volatile u8 *)(1ULL << 44) = 0;
		return;
	case 'S':
		reboot();
	case 'D':
		print_u64_nl(f ? f->rip : 0);
		dump_regs(f);
		return;
	case 'R': {
		if (!n)
			return;
		u8 size = *p++;
		n--;
		skip_ws(&p, &n);
		cmd_read(size, parse_uint(&p, &n));
		return;
	}
	case 'W': {
		if (!n)
			return;
		u8 size = *p++;
		n--;
		skip_ws(&p, &n);
		u64 a = parse_uint(&p, &n);
		skip_ws(&p, &n);
		cmd_write(size, a, parse_uint(&p, &n));
		return;
	}
	case 'T':
		tcp_shell_list();
		return;
	case 'N':
		if (pcap_state != 2) {
			if (pcap_state == 0)
				pcap_state = 1;
			else
				pcap_flush();
		}
		print_u64_nl(pcap_state);
		return;
	case 'H': {
		skip_ws(&p, &n);
		u64 sector = parse_uint(&p, &n);
		skip_ws(&p, &n);
		u64 buf = parse_uint(&p, &n);
		skip_ws(&p, &n);
		u64 count = parse_uint(&p, &n);
		print_u64_nl(blk_sync(1, sector, buf, count));
		return;
	}
	case '\n':
		return;
	default:
		puts("Unknown Command\n");
	}
}

/*
 * Read one scancode from port 0x60.  When polling (no IRQ) a repeat of the
 * previous scancode is ignored, since it is just the same byte read again.
 */
void keyboard_poll(bool from_irq, struct intr_frame *f)
{
	u32 sc = inb(0x60);
	if (!from_irq && sc == last_scancode)
		return;
	last_scancode = sc;
	if (sc & 0x80)
		return;                 /* key release */

	char ch = keymap[sc];
	if (!ch) {
		if (sc == 1)            /* Esc */
			reboot();
		return;
	}
	if (ch == '\b') {
		i32 pos = (i32)cursor_pos - 1;
		if (pos < 0)
			pos = 0x7CF;
		((volatile u16 *)PTR(VGA_TEXT))[pos] = 0x0720;
		cursor_pos = pos;
		set_cursor(pos);
		if (line_len)
			line_len--;
		return;
	}

	putc(ch);
	u8 *line = PTR(KBD_BUFFER);
	if (line_len == 0x100) {
		line_len = 0;           /* overflow: drop the line */
		return;
	}
	line[line_len++] = ch;
	if (ch == '\n') {
		shell_command(line, line_len, f);
		line_len = 0;
	}
}
