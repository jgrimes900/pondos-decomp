; ==================================================================
; justos.inc -- JustOS program interface (reconstructed)
;
; Program file format:
;     +0  db 01h, 0Eh, 14h, 03h   magic checked by the "run" command
;     +4  entry point, reached by "call far 3000:0004"; return with RETF
;
; Programs are loaded at 3000:0000 by the shell's "load" command.
;
; Calling the kernel: store one of the OS_* vector offsets below in the
; word at 2000:000C, then "call far 2000:0009".  Registers in/out are
; those of the kernel routine.  Kernel routines that use kernel
; variables expect DS = 2000h (see Docs/DECOMPILATION.md).
; ==================================================================

KERNEL_SEG		equ 2000h
PROGRAM_SEG		equ 3000h

OS_SYSCALL		equ 0009h	; far-call entry (2000:0009)
OS_SYSCALL_NUM		equ 000Ch	; word: vector to call

OS_PRINT_STRING		equ 0003h	; DS:SI = zero-terminated string
OS_WAIT_FOR_KEY		equ 0006h	; OUT: AX = key
OS_COPY_STRING		equ 000Fh	; SI -> BX (unbounded, see docs)
OS_BYTE_TO_DEC		equ 0012h	; AL -> "nnn" in kernel num buffer
OS_LOAD_FILE		equ 0015h	; load file named in file_struct
OS_DRAW_PICTURE		equ 0018h	; show 320x200x2bpp at load segment
OS_SET_LOAD_OFFSET	equ 001Bh	; BX = offset for next load

OS_FILE_STRUCT_PTR	equ 001Eh	; word: -> file_struct in kernel
OS_VERSION_PTR		equ 0021h	; word: -> version string in kernel

FILE_STRUCT_NAME	equ 00h		; 11-char 8.3 name (e.g. "GF      PIC")
FILE_STRUCT_SEGMENT	equ 0Ch		; word: segment files are loaded to

%macro PROGRAM_HEADER 0
	db 01h, 0Eh, 14h, 03h
%endmacro
