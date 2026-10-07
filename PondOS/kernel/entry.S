/*
 * PondOS kernel - assembly glue.
 *
 *   - real-mode E820 routine (called by the boot sector at 0x7E00)
 *   - 64-bit entry point
 *   - interrupt stubs that build a struct intr_frame and call into C
 *   - SYSCALL entry/exit and the first SYSRET into the user program
 *   - the user-mode trampolines copied to 0x108000
 */

	.section .text16, "ax"
	.code16
/*
 * Collect the BIOS E820 memory map into 0000:F000 (24-byte entries), keeping
 * only entries whose length is non-zero.  The count goes to [0x1C78].  Any
 * BIOS error or an empty map jumps to the boot sector's halt loop (0x7C36).
 */
	.globl e820_collect
e820_collect:
	mov	$0xF000, %di
	xor	%ebx, %ebx
	mov	%bx, %es
	mov	$0x534D4150, %edx		/* 'SMAP' */
	mov	$0xE820, %eax
	mov	$0x18, %ecx
	int	$0x15
	jc	0x7C36
	movl	$0, 0x1C78
	cmp	$0x14, %ecx
	jb	2f
	mov	8(%di), %eax
	or	12(%di), %eax
	test	%eax, %eax
	je	2f
	add	$0x18, %di
	addl	$1, 0x1C78
2:	mov	$0x534D4150, %edx
	mov	$0xE820, %eax
	mov	$0x18, %ecx
	int	$0x15
	jc	3f
	cmp	$0x14, %ecx
	jb	1f
	mov	8(%di), %eax
	or	12(%di), %eax
	test	%eax, %eax
	je	1f
	add	$0x18, %di
	addl	$1, 0x1C78
1:	test	%ebx, %ebx
	je	3f
	cmp	$-0x18, %di
	jbe	2b
3:	cmpl	$0, 0x1C78
	je	0x7C36
	ret

	.text
	.code64
/*
 * 64-bit entry, jumped to by the boot sector with paging on and CS = 0x08.
 * Unmap the guard pages around the kernel stack (0x1C4000 and 0x1C6000) and
 * switch to it.
 */
	.globl _start64
_start64:
	xor	%eax, %eax
	mov	%rax, 0x5E30			/* PTE of 0x1C6000 */
	invlpg	0x1C6000
	mov	%rax, 0x5E20			/* PTE of 0x1C4000 */
	invlpg	0x1C4000
	mov	$0x1C6000, %esp
	mov	%rsp, %rbp
	call	kmain
4:	hlt
	jmp	4b

/*
 * Interrupt stubs.  Every gate in the IDT uses IST1 (stack top 0x400), as in
 * the original.  Each stub pushes a dummy error code when the CPU does not
 * supply one, then the registers, and calls handler(struct intr_frame *).
 */
	.macro	ISR name, handler, errcode
	.globl	\name
\name:
	.if \errcode == 0
	pushq	$0
	.endif
	pushq	$0
	push	%rax
	push	%rbx
	push	%rcx
	push	%rdx
	push	%rsi
	push	%rdi
	push	%rbp
	push	%r8
	push	%r9
	push	%r10
	push	%r11
	push	%r12
	push	%r13
	push	%r14
	push	%r15
	mov	%rsp, %rdi
	cld
	call	\handler
	pop	%r15
	pop	%r14
	pop	%r13
	pop	%r12
	pop	%r11
	pop	%r10
	pop	%r9
	pop	%r8
	pop	%rbp
	pop	%rdi
	pop	%rsi
	pop	%rdx
	pop	%rcx
	pop	%rbx
	pop	%rax
	add	$16, %rsp
	iretq
	.endm

	/* The default handler is also installed on vectors that push an error
	 * code; like the original it just reports the first two words the CPU
	 * pushed (which land in frame->rip / frame->cs here) and never returns. */
	ISR isr_default,     fault_default,     0
	ISR isr_debug,       fault_debug,       0
	ISR isr_breakpoint,  fault_breakpoint,  0
	ISR isr_gpf,         fault_gpf,         1
	ISR isr_page_fault,  fault_page,        1
	ISR isr_timer,       irq_timer,         0
	ISR isr_keyboard,    irq_keyboard,      0
	ISR isr_irq_master,  irq_master,        0
	ISR isr_irq8,        irq_slave8,        0
	ISR isr_net,         irq_net,           0
	ISR isr_disk,        irq_disk,          0

	/* Vector 0x30: local APIC spurious interrupt, no EOI. */
	.globl	isr_spurious
isr_spurious:
	iretq

/*
 * SYSCALL entry.  RAX = number, RDX = argument, RCX = user RIP.  The kernel
 * stack pointer saved by enter_user() lives in user_kstack; it is swapped with
 * the user RSP on the way in and out.  Interrupts are re-enabled for the
 * duration of the call.  The user program is MSVC code, so besides the SysV
 * callee-saved registers, RSI and RDI must survive as well.
 */
	.globl	syscall_entry
syscall_entry:
	mov	%rcx, %r9
	mov	%rsp, %r8
	mov	user_kstack, %rsp
	mov	%r8, user_kstack
	sti
	pushfq
	push	%r9
	push	%rsi
	push	%rdi
	sub	$8, %rsp
	mov	%eax, %edi
	mov	%rdx, %rsi
	call	syscall_dispatch
	add	$8, %rsp
	pop	%rdi
	pop	%rsi
	pop	%r9
	sti
	pop	%r11
	mov	%r9, %rcx
	mov	%rsp, %r8
	mov	user_kstack, %rsp
	mov	%r8, user_kstack
	sysretq

/* enter_user(entry, stack_top): first transfer to ring 3, via the trampoline
 * at 0x108006 with RAX = program entry point. */
	.globl	enter_user
enter_user:
	mov	%rsp, user_kstack
	mov	%rsi, %rsp
	sti
	pushfq
	pop	%r11
	mov	%rdi, %rax
	mov	$0x108006, %ecx
	sysretq

/*
 * User-mode trampolines, copied to 0x108000 (mapped user, read-only).
 *   0x108000  syscall(num, arg): the function pointer handed to the program
 *   0x108006  entry: call RAX(0x108000) with a 32-byte shadow space, then
 *             SYSCALL 15/2 (idle) when the program returns
 */
	.section .rodata
	.globl	user_stub_start, user_stub_end
user_stub_start:
	mov	%rcx, %rax
	syscall
	ret
	mov	$0x108000, %ecx
	sub	$0x20, %rsp
	call	*%rax
	add	$0x20, %rsp
	mov	$0xF, %eax
	mov	$2, %edx
	syscall
5:	jmp	5b
user_stub_end:
