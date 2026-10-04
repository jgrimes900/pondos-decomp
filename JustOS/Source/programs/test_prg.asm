; ==================================================================
; TEST_PRG.BIN -- reconstructed (40 bytes)
; Prints "orbus" through the kernel's print-string call.
;
; Build: nasm -O0 -f bin -o TEST_PRG.BIN test_prg.asm
; ==================================================================

	BITS 16
	%include "justos.inc"

	PROGRAM_HEADER

start:
	push ds
	push ax

	mov ax, PROGRAM_SEG		; DS -> our own data
	mov ds, ax
	mov ax, KERNEL_SEG		; ES -> kernel
	mov es, ax

	mov si, message
	mov ax, OS_PRINT_STRING
	mov [es:OS_SYSCALL_NUM], ax
	call KERNEL_SEG:OS_SYSCALL

	pop ax
	pop ds
	retf

message	db "orbus", 0
