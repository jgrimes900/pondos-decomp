; ==================================================================
; IMGVIEW.BIN -- reconstructed (129 bytes)
; Intended to load THEMESS.PIC to segment 4000h and display it.
;
; Build: nasm -O0 -f bin -o IMGVIEW.BIN imgview.asm
;
; BUG (as shipped -- IMGVIEW hangs the machine):
;  * The kernel's file_struct pointer is read with
;    "mov bx, [OS_FILE_STRUCT_PTR]", i.e. from DS = 3000h -- the
;    program's own bytes at 3000:001E (= 2600h) -- instead of from
;    ES = 2000h.  The name goes to 3000:2600 and the 4000h segment to
;    2000:260C, not into the kernel's file_struct.
;  * The kernel calls then run with DS = 3000h, but os_load_file
;    reads its variables through DS.  SecsPerTrack (3000:04ED) is 0,
;    so l2hts divides by zero at 2000:0480 and, since the BIOS INT 0
;    handler returns to the faulting DIV, loops there forever.
;    (Verified in QEMU.)
;  A working version needs [es:...] for the file_struct accesses and
;  DS = 2000h around the kernel calls (or a kernel that sets DS).
; ==================================================================

	BITS 16
	%include "justos.inc"

	PROGRAM_HEADER

start:
	push ds
	push ax
	push bx
	push cx

	mov ax, PROGRAM_SEG
	mov ds, ax
	mov ax, KERNEL_SEG
	mov es, ax

	; Copy the file name into the kernel's file_struct
	mov si, filename
	mov bx, [OS_FILE_STRUCT_PTR]	; BUG: should be [es:...]
	mov cx, 11
	mov ax, OS_COPY_STRING
	mov [es:OS_SYSCALL_NUM], ax
	call KERNEL_SEG:OS_SYSCALL

	; Load it to 4000:0000 instead of over ourselves at 3000:0000
	mov ax, 4000h
	mov bx, [OS_FILE_STRUCT_PTR]	; BUG: same as above
	add bx, FILE_STRUCT_SEGMENT
	mov [es:bx], ax
	call KERNEL_SEG:OS_SYSCALL	; (still OS_COPY_STRING -- harmless
					; repeat of the copy above)

	mov ax, OS_LOAD_FILE
	mov [es:OS_SYSCALL_NUM], ax
	call KERNEL_SEG:OS_SYSCALL

	mov bx, 0
	mov ax, OS_SET_LOAD_OFFSET
	mov [es:OS_SYSCALL_NUM], ax
	call KERNEL_SEG:OS_SYSCALL

	mov ax, OS_DRAW_PICTURE
	mov [es:OS_SYSCALL_NUM], ax
	call KERNEL_SEG:OS_SYSCALL

	; Restore the default load segment
	mov ax, PROGRAM_SEG
	mov bx, [OS_FILE_STRUCT_PTR]
	add bx, FILE_STRUCT_SEGMENT
	mov [es:bx], ax

	pop cx
	pop bx
	pop ax
	pop ds
	retf

filename	db "THEMESS PIC", 0
