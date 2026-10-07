/*
 * CPU setup, interrupt descriptor table, the millisecond clock and the
 * exception handlers.
 */
#include "kernel.h"

/*
 * Clock: a 32.32 fixed-point millisecond counter extended to 128 bits
 * ([0x1C08] low qword, [0x1C10] high qword).  The PIT runs at
 * 1193182 / 10000 = 119.318 Hz, i.e. 8.38095 ms per tick, which is
 * 0x8_618602F4 in 32.32 fixed point.
 */
#define PIT_DIVISOR   10000
#define MS_PER_TICK   0x8618602F4ULL

static volatile u64 clock_lo, clock_hi;
static u32 tcp_coarse_last;                      /* [0x1CB0] */

u64 now_ms(void)
{
	/* the qword at [0x1C0C]: bits 32..95 of the 128-bit counter */
	return (clock_lo >> 32) | (clock_hi << 32);
}

void irq_timer(struct intr_frame *f UNUSED)
{
	u64 lo = clock_lo + MS_PER_TICK;
	if (lo < clock_lo)
		clock_hi++;
	clock_lo = lo;

	/* TCP coarse timer, every 200 ms once TCP is up */
	if (tcp_enabled && (i32)(now_ms32() - tcp_coarse_last - 200) > 0) {
		tcp_coarse_last = now_ms32();
		tcp_coarse_timer();
	}
	outb(0x20, 0x20);
}

void irq_keyboard(struct intr_frame *f)
{
	keyboard_poll(true, f);
	outb(0x20, 0x20);
}

/* IRQ 1-7 and 9-15 (vectors 0x22-0x2F): only the master PIC is acknowledged,
 * even for the slave's lines, exactly like the original. */
void irq_master(struct intr_frame *f UNUSED)
{
	outb(0x20, 0x20);
}

void irq_slave8(struct intr_frame *f UNUSED)
{
	outb(0xA0, 0x20);
	outb(0x20, 0x20);
}

void irq_net(struct intr_frame *f UNUSED)
{
	net_irq();
	MMIO32(LAPIC_EOI) = 0;
}

void irq_disk(struct intr_frame *f UNUSED)
{
	blk_complete();
	MMIO32(LAPIC_EOI) = 0;
}

/* ---------------------------------------------------------------------- */

NORETURN void reboot(void)
{
	/* Load CR3 with 0: the next fetch triple-faults and resets the CPU. */
	__asm__ volatile("mov %0, %%cr3" :: "r"(0ULL) : "memory");
	for (;;)
		hlt();
}

/*
 * Final resting state after a fault or when the user program asks for it.
 * With interrupts disabled the keyboard is polled so that the debug shell
 * stays usable; otherwise the CPU just halts and services interrupts.
 */
NORETURN void system_idle(void)
{
	puts("Went to system idle\n");
	if (read_rflags() & 0x200)
		for (;;)
			hlt();
	for (;;) {
		keyboard_poll(false, NULL);
		outb(0x20, 0x20);
		pause(); pause(); pause(); pause();
	}
}

void fault_default(struct intr_frame *f)
{
	puts("Fault Occured\n");
	print_u64_nl(f->rip);       /* first two words of the CPU frame */
	print_u64_nl(f->cs);
	system_idle();
}

void fault_debug(struct intr_frame *f)
{
	u64 flags = read_rflags(), dr6, dr7;   /* the handler's own RFLAGS */
	puts("Debug Fault Occured\n");
	print_u64_nl(f->rip);
	print_u64_nl(f->cs);
	__asm__ volatile("mov %%dr6, %0; mov %%dr7, %1" : "=r"(dr6), "=r"(dr7));
	print_u64_nl(dr6);
	print_u64_nl(dr7);
	print_u64_nl(flags);
	system_idle();
}

void fault_breakpoint(struct intr_frame *f)
{
	puts("Breakpoint Occured\n");
	print_u64_nl(f->rip);
	print_u64_nl(f->cs);
	system_idle();
}

void fault_gpf(struct intr_frame *f)
{
	puts("General Protection Fault\n");
	print_u64_nl(read_rflags());
	print_u64_nl(f->ss);
	print_u64_nl(f->rsp);
	print_u64_nl(f->rflags);
	print_u64_nl(f->cs);
	print_u64_nl(f->rip);
	print_u64_nl(f->error);
	system_idle();
}

void fault_page(struct intr_frame *f)
{
	u64 cr2;
	__asm__ volatile("mov %%cr2, %0" : "=r"(cr2));
	puts("Page Fault\n");
	print_u64_nl(f->rip);
	print_u64_nl(cr2);
	print_u64_nl(f->error);
	dump_regs(f);
	/* if the faulting code is readable, show the 16 bytes at RIP */
	if (page_query(f->rip) & PTE_P) {
		const u64 *code = PTR(f->rip);
		newline();
		print_u64(code[0]);
		puts(" ");
		print_u64_nl(code[1]);
	}
	system_idle();
}

/* ---------------------------------------------------------------------- */

static void set_gate(int vec, void (*handler)(void))
{
	u64 h = (u64)handler;
	volatile u64 *g = PTR(IDT_ADDR + vec * 16);
	/* present, DPL 0, 64-bit interrupt gate, IST 1, selector 0x08 */
	g[0] = (h & 0xFFFF) | (0x08ULL << 16) | (1ULL << 32) | (0x8EULL << 40) |
	       ((h >> 16 & 0xFFFF) << 48);
	g[1] = h >> 32;
}

static void wrmsr(u32 msr, u64 v)
{
	__asm__ volatile("wrmsr" :: "c"(msr), "a"((u32)v), "d"((u32)(v >> 32)));
}

void interrupts_init(void)
{
	/* TSS at 0x1800: RSP0-2 = kernel stack, IST1-7 = 0x400, no I/O bitmap */
	memset(PTR(TSS_ADDR), 0, 0x68);
	MMIO64(TSS_ADDR + 0x04) = KSTACK_TOP;
	MMIO64(TSS_ADDR + 0x0C) = KSTACK_TOP;
	MMIO64(TSS_ADDR + 0x14) = KSTACK_TOP;
	for (int i = 0; i < 7; i++)
		MMIO64(TSS_ADDR + 0x24 + 8 * i) = 0x400;
	MMIO16(TSS_ADDR + 0x66) = 0x68;
	__asm__ volatile("ltr %w0" :: "r"(0x28));

	for (int v = 0; v < 256; v++)
		set_gate(v, isr_default);
	for (int v = 0x20; v < 0x30; v++)
		set_gate(v, v == 0x28 ? isr_irq8 : isr_irq_master);
	set_gate(0x0E, isr_page_fault);
	set_gate(0x0D, isr_gpf);
	set_gate(0x01, isr_debug);
	set_gate(0x03, isr_breakpoint);
	set_gate(0x20, isr_timer);
	set_gate(0x21, isr_keyboard);
	set_gate(0x30, isr_spurious);
	set_gate(0x31, isr_net);
	set_gate(0x32, isr_disk);

	clock_lo = clock_hi = 0;

	/* PIT channel 0, mode 2 */
	outb(0x43, 0x34);
	outb(0x40, PIT_DIVISOR & 0xFF);
	outb(0x40, PIT_DIVISOR >> 8);

	struct PACKED { u16 limit; u64 base; } idtr = { 0x1000, IDT_ADDR };
	__asm__ volatile("lidt %0" :: "m"(idtr));
	sti();

	/* Remap the PICs to 0x20/0x28 and unmask every line */
	outb(0x20, 0x11); outb(0xA0, 0x11);
	outb(0x21, 0x20); outb(0xA1, 0x28);
	outb(0x21, 4);    outb(0xA1, 2);
	outb(0x21, 1);    outb(0xA1, 1);
	outb(0x21, 0);    outb(0xA1, 0);

	/* Local APIC on, spurious vector 0x30 */
	MMIO32(LAPIC_SVR) = 0x130;

	/* SSE and AVX state: CR0.EM off, CR0.MP on, CR4 OSFXSR|OSXMMEXCPT|OSXSAVE,
	 * XCR0 |= SSE|AVX.  The user program is compiled with AVX. */
	u64 cr;
	__asm__ volatile("mov %%cr0, %0" : "=r"(cr));
	cr = (cr & ~4ULL) | 2;
	__asm__ volatile("mov %0, %%cr0" :: "r"(cr));
	__asm__ volatile("mov %%cr4, %0" : "=r"(cr));
	cr |= 0x40600;
	__asm__ volatile("mov %0, %%cr4" :: "r"(cr));
	u32 lo, hi;
	__asm__ volatile("xgetbv" : "=a"(lo), "=d"(hi) : "c"(0));
	lo |= 6;
	__asm__ volatile("xsetbv" :: "a"(lo), "d"(hi), "c"(0));

	/* SYSCALL: kernel CS 0x08, SYSRET base 0x13 (user CS 0x23, SS 0x1B);
	 * IF and DF are cleared on entry. */
	wrmsr(0xC0000081, 0x0013000800000000ULL);
	wrmsr(0xC0000082, (u64)syscall_entry);
	wrmsr(0xC0000084, 0x600);
}
