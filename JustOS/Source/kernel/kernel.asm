; ==================================================================
; JustOS kernel  --  reconstructed from KERNEL.BIN (2151 bytes)
; "Version 0.0.106"
;
; Loaded by the boot sector to 2000:0000 and entered there with DL =
; boot drive.  Everything (code, data, buffers) lives in segment 2000h.
;
; Build (byte-identical to the original):
;     nasm -O0 -f bin -o KERNEL.BIN kernel.asm
;
; Comments marked "BUG:" describe behaviour of the original binary that
; is almost certainly unintended.  They are preserved, not fixed, so
; that this source reassembles to the exact original image.
; ==================================================================

	BITS 16
	CPU 386				; movzx, shr r/m,imm8, pusha, fs/gs

	disk_buffer	equ	0867h	; 8 KB scratch space just past the
					; end of the kernel image (root dir
					; and FAT are read here)


; ------------------------------------------------------------------
; System call vectors (offset 0000h)
;
; Programs reach the kernel with a far call to 2000:0009 after storing
; the *offset of one of these vectors* in the word at 2000:000C.  The
; dispatcher then does "call [cs:000Ch]".  Entries are 3 bytes apart;
; the two data slots at 001Eh/0021h are padded to 3 bytes as well.

os_call_vectors:
	jmp near kernel_start		; 0000h
	jmp near os_print_string	; 0003h
	jmp near os_wait_for_key	; 0006h
	jmp near os_syscall		; 0009h  far-call entry point
os_syscall_num:
	dw 0				; 000Ch  vector to call
	db 0
	jmp near os_copy_string		; 000Fh
	jmp near os_byte_to_dec		; 0012h
	jmp near os_load_file		; 0015h
	jmp near os_draw_picture	; 0018h
	jmp near os_set_load_offset	; 001Bh
	dw file_struct			; 001Eh  -> filename / load segment
	db 0
	dw version_string		; 0021h  -> "Version 0.0.106"
	db 0


; ------------------------------------------------------------------
; Entry point

kernel_start:
	cli
	mov ax, 0			; Stack at 0000:FFFF (BUG: odd SP --
	mov ss, ax			; every push is misaligned; harmless
	mov sp, 0FFFFh			; on x86, just slow)
	sti

	cld

	mov ax, 2000h			; All segments = kernel segment
	mov ds, ax
	mov es, ax
	mov fs, ax
	mov gs, ax

	cmp dl, 0			; Keep boot drive number from loader
	je .no_change
	mov [bootdev], dl
.no_change:

	mov ax, 1003h			; Attribute bit 7 = bright background
	mov bx, 0			; instead of blinking
	int 10h

	; Hook IRQ0 (INT 08h) so that it bumps a tick counter.  The old
	; vector is patched straight into the far CALL in timer_isr.
	cli
	xor ax, ax
	mov es, ax
	mov bx, [es:08h*4]
	mov [old_int8_off], bx
	mov bx, [es:08h*4+2]
	mov [old_int8_seg], bx
	mov word [es:08h*4], timer_isr
	mov [es:08h*4+2], cs
	sti

	mov ax, 2000h
	mov es, ax
	jmp near shell_init


; ------------------------------------------------------------------
; INT 08h handler: chain to BIOS, then increment ticks.
; BUG: uses whatever DS is current, so while a program runs with
; DS = 3000h the counter is actually 3000:0866.

timer_isr:
	pushf
	db 9Ah				; call far old_int8_seg:old_int8_off
old_int8_off	dw 0
old_int8_seg	dw 0
	inc byte [ticks]
	iret


; ------------------------------------------------------------------
; Command shell

shell_init:
	mov si, logo
	call os_print_string
	mov si, version_string
	call os_print_string
	call os_print_newline
	call print_prompt

shell_loop:
	mov bl, [cmd_len]		; BX = current length / insert index
	mov bh, 0
	call os_wait_for_key

	cmp al, 13			; Enter?
	jne .not_enter

	cmp bx, 0			; Ignore empty lines
	je shell_loop

	call os_print_newline
	call process_command		; (returns with BX preserved)

.clear_buffer:				; Wipe cmd_buffer[len..1]
	mov byte [bx+cmd_buffer], 0	; BUG: [len] is already 0 and [0]
	dec bx				; is never cleared (harmless, as
	cmp bx, 0			; it is overwritten next time)
	jne .clear_buffer

	mov byte [cmd_len], 0
	jmp near shell_loop

.not_enter:
	cmp al, 8			; Backspace?
	jne .store_char

	; BUG: clears [len] (already 0) instead of [len-1], so the erased
	; character stays in the buffer: "abc<BS><Enter>" runs "abc".
	; BUG: no check for an empty line; cmd_len wraps to 255.
	mov byte [bx+cmd_buffer], 0
	dec byte [cmd_len]
	call os_print_backspace
	jmp near shell_loop

.store_char:				; BUG: no length limit (cmd_len is
	mov [bx+cmd_buffer], al		; a byte, so it wraps at 256)
	inc byte [cmd_len]
	mov ah, 0Eh
	int 10h
	jmp near shell_loop


; ------------------------------------------------------------------
; process_command -- look the first word of cmd_buffer up in
; command_table and call its handler.  Each table entry points at a
; zero-terminated command name which is directly followed by the
; handler's code.  On entry to a handler SI points just past the
; character that ended the command word (i.e. at its argument).
;
; BUG: the table holds words but the index is advanced with "inc bx",
;      so every other probe reads a bogus pointer made of two halves
;      of adjacent entries.  It works only because those bogus
;      "names" almost never match.
; BUG: if the typed word is a proper prefix of a command name (e.g.
;      "dra", "t", "1"), the code jumps back to .next_entry *without*
;      advancing BX and loops forever (the shell freezes).

process_command:
	push bx
	mov bx, 0

.next_entry:
	mov si, cmd_buffer
	push bx
	mov bx, [bx+command_table]
	mov [cmd_ptr], bx
	pop bx
	cmp word [cmd_ptr], 0		; End of table?
	je .unknown

.compare:
	lodsb
	cmp al, 0
	je .word_end
	cmp al, ' '
	je .word_end

	push bx
	mov bx, [cmd_ptr]
	mov ah, [bx]
	pop bx
	inc word [cmd_ptr]
	cmp al, ah
	je .compare

	inc bx
	jmp near .next_entry

.word_end:				; Typed word ended; does the name?
	push bx
	mov bx, [cmd_ptr]
	mov ah, [bx]
	pop bx
	cmp ah, 0
	je .found
	jmp near .next_entry		; BUG: see above (no inc bx)

.found:
	inc word [cmd_ptr]		; Skip the name's terminator
	call [cmd_ptr]			; ...and run the code after it
	jmp near .done

.unknown:				; Unknown command: echo it back
	mov si, cmd_buffer
	call os_print_string

.done:
	call os_print_newline
	call print_prompt
	pop bx
	ret

cmd_ptr		dw 0


; ------------------------------------------------------------------
; os_syscall -- far-callable dispatcher at 2000:0009 (via vector)

os_syscall:
	call [cs:os_syscall_num]
	retf


; ------------------------------------------------------------------
; os_print_string -- print zero-terminated string at DS:SI

os_print_string:
	pusha
	mov ah, 0Eh
.repeat:
	lodsb
	cmp al, 0
	je .done
	int 10h
	jmp near .repeat
.done:
	popa
	ret


; ------------------------------------------------------------------
; os_copy_string -- copy zero-terminated string DS:SI to DS:BX
; IN: SI = source, BX = destination, CX = "max length"
; BUG: compares the destination *pointer* BX with CX, which never
;      matches for real buffers, so the copy is effectively unbounded.
;      The terminator is not copied either.

os_copy_string:
	pusha
	mov ah, 0Eh			; (leftover, unused)
.repeat:
	lodsb
	cmp al, 0
	je .done
	mov [bx], al
	inc bx
	cmp bx, cx
	je .done
	jmp near .repeat
.done:
	popa
	ret


; ------------------------------------------------------------------
; os_print_newline -- print LF, CR

os_print_newline:
	pusha
	mov ah, 0Eh
	mov al, 10
	int 10h
	mov al, 13
	int 10h
	popa
	ret


; ------------------------------------------------------------------
; os_print_backspace -- erase the character left of the cursor

os_print_backspace:
	pusha
	mov ah, 0Eh
	mov al, 8
	int 10h
	mov al, ' '
	int 10h
	mov al, 8
	int 10h
	popa
	ret


; ------------------------------------------------------------------
; os_wait_for_key -- OUT: AX = key (AH = scan code, AL = ASCII)

os_wait_for_key:
	pusha
	mov ax, 0
	mov ah, 10h
	int 16h
	mov [.tmp_key], ax
	popa
	mov ax, [.tmp_key]
	ret

.tmp_key	dw 0


; ------------------------------------------------------------------
; os_byte_to_dec -- convert AL to three ASCII digits in num_buffer

os_byte_to_dec:
	pusha
	push bx

	mov word [num_buffer], '00'
	mov byte [num_buffer+2], '0'

	movzx ax, al

	mov bl, 0			; Hundreds
.hundreds:
	cmp al, 100
	jb .got_hundreds
	sub al, 100
	inc bl
	jmp near .hundreds
.got_hundreds:
	add [num_buffer], bl

	mov bl, 0			; Tens
.tens:
	cmp al, 10
	jb .got_tens
	sub al, 10
	inc bl
	jmp near .tens
.got_tens:
	add [num_buffer+1], bl

	add [num_buffer+2], al		; Units

	pop bx
	popa
	ret


; ------------------------------------------------------------------

print_prompt:
	mov ah, 0Eh
	mov al, '>'
	int 10h
	ret


; ==================================================================
; Shell commands.  Each is "name", 0 followed by its code.
; ==================================================================

; load XXXXXXXXYYY -- load a file (name typed in raw 8.3 directory
; form, e.g. "load TEST_PRGBIN") to [load_segment]:[pointer].
; The argument is assumed to start at cmd_buffer+5.

cmd_load:
	db "load", 0
	mov si, cmd_buffer+5
	mov bx, file_struct
	mov cx, 11
	call os_copy_string
	call os_load_file
	mov bx, 0			; Next load goes to offset 0 again
	call os_set_load_offset
	ret


; testbts -- print the length of the current command line (always
; "007", the length of "testbts" itself, unless followed by text)

cmd_testbts:
	db "testbts", 0
	pusha
	mov al, [cmd_len]
	call os_byte_to_dec
	mov si, num_buffer
	call os_print_string
	popa
	ret


; run -- far-call a program previously loaded at 3000:0000.  The
; program must start with the 4-byte magic and is entered at 3000:0004.
; BUG: registers are popped in the wrong order (AX and BX swap) and
;      ES is left at 3000h on the error path.

cmd_run:
	db "run", 0
	push ax
	push bx
	mov bx, 3000h
	mov es, bx
	mov ax, [es:0]
	cmp ax, [program_magic]
	jne .bad_magic
	mov ax, [es:2]
	cmp ax, [program_magic+2]
	jne .bad_magic
	pop ax
	call 3000h:0004h
	mov bx, 2000h
	mov es, bx
	pop bx
	ret

.bad_magic:
	mov si, msg_no_magic
	call os_print_string
	pop bx
	pop ax
	ret

msg_no_magic	db "Magic Number missing.", 0
program_magic	db 01h, 0Eh, 14h, 03h


; printstr N -- print one of the kernel's strings:
; 1 = version, 2 = logo, 3 = command buffer, 4 = number buffer

cmd_printstr:
	db "printstr", 0
	lodsb
	cmp al, '1'
	je .version
	cmp al, '2'
	je .logo
	cmp al, '3'
	je .buffer
	cmp al, '4'
	je .number
	jmp near .not_found

.version:
	mov si, version_string
	jmp near .print
.logo:
	mov si, logo
	jmp near .print
.buffer:
	mov si, cmd_buffer
	jmp near .print
.number:
	mov si, num_buffer
	jmp near .print
.not_found:
	mov si, msg_no_string
.print:
	call os_print_string
	ret

msg_no_string	db "String with that ID not found.", 0


; 1987 -- easter egg: load GF.PIC, show it, then print "IT'S ME"

cmd_1987:
	db "1987", 0
	push bx
	push cx
	mov si, gf_filename
	mov bx, file_struct
	mov cx, 11
	call os_copy_string
	call os_load_file
	mov bx, 0
	call os_set_load_offset
	call os_draw_picture
	mov si, msg_its_me
	call os_print_string
	pop cx
	pop bx
	ret

gf_filename	db "GF      PIC", 0


; ------------------------------------------------------------------
; draw / os_draw_picture -- show a 320x200, 2 bits-per-pixel picture
; (16000 bytes, linear, MSB = leftmost pixel) stored at
; [load_segment]:0000 in CGA mode 4 (one BIOS call per pixel), wait,
; then return to 80x25 text mode (mode 2).
;
; BUG: the delay was meant to be "ticks + 40h" (~3.5 s) but the
;      brackets were left off, so the *low byte of the address* of
;      `ticks` (66h) is used: it waits until the free-running counter
;      happens to equal 0A6h -- anywhere from 0 to ~14 s.

cmd_draw:
	db "draw", 0
os_draw_picture:
	pusha
	push bx
	push cx
	push dx

	mov word [pic_index], 0

	mov ah, 0			; 320x200x4 graphics
	mov al, 4
	int 10h

	mov cx, 0			; X
	mov dx, 0			; Y
.next_byte:
	mov ax, [load_segment]
	mov es, ax
	mov ah, 0Ch			; BIOS write pixel
	mov bx, [pic_index]
	mov bl, [es:bx]
	mov [pic_byte], bl

	mov al, [pic_byte]		; Pixel 0: bits 7-6
	shr al, 6
	mov bh, 0
	int 10h
	inc cx

	mov al, [pic_byte]		; Pixel 1: bits 5-4
	and al, 30h
	shr al, 4
	int 10h
	inc cx

	mov al, [pic_byte]		; Pixel 2: bits 3-2
	and al, 0Ch
	shr al, 2
	int 10h
	inc cx

	mov al, [pic_byte]		; Pixel 3: bits 1-0
	and al, 03h
	int 10h

	inc word [pic_index]
	inc cx
	cmp cx, 320
	jl .next_byte
	mov cx, 0
	inc dx
	cmp dx, 200
	jl .next_byte

	mov ax, 2000h
	mov es, ax

	mov al, (ticks-$$) & 0FFh	; Original: "mov al, ticks" (BUG)
	add al, 40h
.wait:
	nop
	cmp al, [ticks]
	jne .wait

	mov ah, 0			; Back to 80x25 text
	mov al, 2
	int 10h

	pop dx
	pop cx
	pop bx
	popa
	ret

pic_index	dw 0
pic_byte	db 0

msg_its_me	db "IT'S ME", 0


; ------------------------------------------------------------------
; Command table (word pointers to the "name",0,code blocks above)

command_table:
	dw cmd_testbts
	dw cmd_printstr
	dw cmd_1987
	dw cmd_draw
	dw cmd_load
	dw cmd_run
	dw 0


; ------------------------------------------------------------------
; os_load_file -- load the file named (11-char 8.3 directory form) in
; file_struct from the boot floppy to [load_segment]:[pointer].
; Adapted from the MikeOS boot loader's FAT12 code.
;
; NOTE: all variables are addressed through DS, so this only works
; when called with DS = 2000h.  Called from a program (DS = 3000h)
; SecsPerTrack reads as 0 and l2hts dies on "div" (divide by zero;
; the BIOS INT 0 handler returns to the same DIV, so it hangs).

os_load_file:
	mov ax, 19			; Root directory starts at LBA 19
	call l2hts

	mov si, disk_buffer
	mov bx, ds
	mov es, bx
	mov bx, si

	mov ah, 2			; Read 14 sectors (224 entries)
	mov al, 14

	pusha

.read_root_dir:
	popa
	pusha

	stc
	int 13h
	jnc .search_dir
	call reset_floppy
	jnc .read_root_dir

	popa				; Silent failure
	ret

.search_dir:
	popa

	mov ax, ds
	mov es, ax
	mov di, disk_buffer

	mov cx, word [RootDirEntries]
	mov ax, 0

.next_root_entry:
	xchg cx, dx			; Use DX as loop counter

	mov si, file_struct
	mov cx, 11
	rep cmpsb
	je .found_file

	add ax, 32
	mov di, disk_buffer
	add di, ax

	xchg dx, cx
	loop .next_root_entry

	mov si, msg_file_not_found
	call os_print_string
	ret

.found_file:
	mov ax, word [es:di+0Fh]	; First cluster (DI is 11 bytes in)
	mov word [cluster], ax

	mov ax, 1			; Read the FAT (LBA 1, 9 sectors)
	call l2hts

	mov di, disk_buffer
	mov bx, di

	mov ah, 2
	mov al, 9

	pusha

.read_fat:
	popa
	pusha

	stc
	int 13h
	jnc .read_fat_ok
	call reset_floppy
	jnc .read_fat

	mov si, msg_disk_error
	call os_print_string
	popa
	ret

.read_fat_ok:
	popa

	mov ax, [load_segment]
	mov es, ax
	mov bx, 0

	mov ah, 2
	mov al, 1

	push ax

.load_file_sector:
	mov ax, word [cluster]		; Cluster -> LBA
	add ax, 31

	call l2hts

	mov ax, [load_segment]
	mov es, ax
	mov bx, word [pointer]

	pop ax
	push ax

	stc
	int 13h

	jnc .calculate_next_cluster

	call reset_floppy
	jmp near .load_file_sector

.calculate_next_cluster:
	mov ax, [cluster]
	mov dx, 0
	mov bx, 3
	mul bx
	mov bx, 2
	div bx				; DX = cluster mod 2
	mov si, disk_buffer
	add si, ax
	mov ax, word [ds:si]

	or dx, dx
	jz .even

.odd:
	shr ax, 4
	jmp short .next_cluster_cont

.even:
	and ax, 0FFFh

.next_cluster_cont:
	mov word [cluster], ax

	cmp ax, 0FF8h
	jae .end

	add word [pointer], 512
	jmp near .load_file_sector

.end:
	pop ax
	ret


; ------------------------------------------------------------------

reset_floppy:
	push ax
	push dx
	mov ax, 0
	mov dl, byte [bootdev]
	stc
	int 13h
	pop dx
	pop ax
	ret


; l2hts -- logical sector in AX -> CH/CL/DH/DL for INT 13h

l2hts:
	push bx
	push ax

	mov bx, ax

	mov dx, 0
	div word [SecsPerTrack]
	add dl, 01h
	mov cl, dl
	mov ax, bx

	mov dx, 0
	div word [SecsPerTrack]
	mov dx, 0
	div word [Sides]
	mov dh, dl
	mov ch, al

	pop ax
	pop bx

	mov dl, byte [bootdev]

	ret


; ------------------------------------------------------------------
; os_set_load_offset -- IN: BX = offset for the next os_load_file

os_set_load_offset:
	mov [pointer], bx
	ret


; ==================================================================
; Data

file_struct:
	times 12 db 0			; +00h  11-char name + terminator
load_segment	dw 3000h		; +0Ch  segment files are loaded to

msg_disk_error		db "Floppy error! Press any key...", 0
msg_file_not_found	db "File not found!", 0

bootdev		db 0
cluster		dw 0
pointer		dw 0

Sides		dw 2
SecsPerTrack	dw 18
RootDirEntries	dw 224

version_string	db "Version 0.0.106", 0

logo:
	db ' ________                 _____    ________     ______      _____', 10, 13
	db '/        \   /\    /\    /     \  /        \   /  __  \    /     \', 10, 13
	db '\___    _/  |  |  |  |  |   ___/  \__    __/  |  /  \  |  |   ___/', 10, 13
	db '    |  |    |  |  |  |   \  \        |  |     | |    | |   \  \', 10, 13
	db '    |  |    |  |  |  |    \  \       |  |     | |    | |    \  \', 10, 13
	db ' __ |  |    |  |  |  |     \  \      |  |     | |    | |     \  \', 10, 13
	db '|  ||  |    |  |__|  |   ___\  \     |  |     | |    | |   ___\  \', 10, 13
	db '|  ||  |    |        |  /       |    |  |     |  \__/  |  /       |', 10, 13
	db ' \____/      \______/   \______/     |__|      \______/   \______/', 10, 13
	db 0

cmd_buffer	times 256 db 0
		db 0
cmd_len		db 0
num_buffer	db "000", 0
ticks		db 0

; disk_buffer (0867h) follows here, outside the file image.
