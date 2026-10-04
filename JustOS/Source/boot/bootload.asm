; ==================================================================
; JustOS boot sector  --  reconstructed from sector 0 of JustOS.img
;
; This is (instruction for instruction) the MikeOS 4.x FAT12 boot
; loader with JustOS' own BPB labels and messages.  It finds
; KERNEL.BIN in the root directory, loads it to 2000:0000 and jumps
; there with DL = boot drive.
;
; Build (byte-identical to the original):
;     nasm -O0 -f bin -o bootload.bin bootload.asm
; ==================================================================

	BITS 16
	CPU 386

	jmp short bootloader_start
	nop


; ------------------------------------------------------------------
; BIOS Parameter Block (1.44 MB floppy)

OEMLabel		db "JUSTBOOT"
BytesPerSector		dw 512
SectorsPerCluster	db 1
ReservedForBoot		dw 1
NumberOfFats		db 2
RootDirEntries		dw 224
LogicalSectors		dw 2880
MediumByte		db 0F0h
SectorsPerFat		dw 9
SectorsPerTrack		dw 18
Sides			dw 2
HiddenSectors		dd 0
LargeSectors		dd 0
DriveNo			dw 0
Signature		db 41
VolumeID		dd 00000000h
VolumeLabel		db "JUSTOS     "
FileSystem		db "FAT12   "


; ------------------------------------------------------------------

bootloader_start:
	mov ax, 07C0h			; 4 KB stack above the 8 KB buffer
	add ax, 544
	cli
	mov ss, ax
	mov sp, 4096
	sti

	mov ax, 07C0h
	mov ds, ax

	cmp dl, 0			; Ask the BIOS for the real geometry
	je no_change			; unless booting from drive 0
	mov [bootdev], dl
	mov ah, 8
	int 13h
	jc near fatal_disk_error
	and cx, 3Fh
	mov [SectorsPerTrack], cx
	movzx dx, dh
	add dx, 1
	mov [Sides], dx

no_change:
	mov eax, 0			; (needed by some old BIOSes)


; Read the root directory (LBA 19, 14 sectors) into the buffer

	mov ax, 19
	call l2hts

	mov si, buffer
	mov bx, ds
	mov es, bx
	mov bx, si

	mov ah, 2
	mov al, 14

	pusha

read_root_dir:
	popa
	pusha

	stc
	int 13h
	jnc search_dir
	call reset_floppy
	jnc read_root_dir

	jmp near reboot

search_dir:
	popa

	mov ax, ds
	mov es, ax
	mov di, buffer

	mov cx, word [RootDirEntries]
	mov ax, 0

next_root_entry:
	xchg cx, dx

	mov si, kern_filename
	mov cx, 11
	rep cmpsb
	je found_file_to_load

	add ax, 32

	mov di, buffer
	add di, ax

	xchg dx, cx
	loop next_root_entry

	mov si, file_not_found
	call print_string
	jmp near reboot


found_file_to_load:
	mov ax, word [es:di+0Fh]	; First cluster
	mov word [cluster], ax

	mov ax, 1			; Read the FAT
	call l2hts

	mov di, buffer
	mov bx, di

	mov ah, 2
	mov al, 9

	pusha

read_fat:
	popa
	pusha

	stc
	int 13h
	jnc read_fat_ok
	call reset_floppy
	jnc read_fat

fatal_disk_error:
	mov si, disk_error
	call print_string
	jmp near reboot


read_fat_ok:
	popa

	mov ax, 2000h			; Kernel goes to 2000:0000
	mov es, ax
	mov bx, 0

	mov ah, 2
	mov al, 1

	push ax

load_file_sector:
	mov ax, word [cluster]
	add ax, 31

	call l2hts

	mov ax, 2000h
	mov es, ax
	mov bx, word [pointer]

	pop ax
	push ax

	stc
	int 13h

	jnc calculate_next_cluster

	call reset_floppy
	jmp near load_file_sector


calculate_next_cluster:
	mov ax, [cluster]
	mov dx, 0
	mov bx, 3
	mul bx
	mov bx, 2
	div bx
	mov si, buffer
	add si, ax
	mov ax, word [ds:si]

	or dx, dx
	jz even

odd:
	shr ax, 4
	jmp short next_cluster_cont

even:
	and ax, 0FFFh

next_cluster_cont:
	mov word [cluster], ax

	cmp ax, 0FF8h
	jae end

	add word [pointer], 512
	jmp near load_file_sector


end:
	pop ax
	mov dl, byte [bootdev]

	jmp 2000h:0000h


; ------------------------------------------------------------------

reboot:
	mov ax, 0
	int 16h
	mov ax, 0
	int 19h


print_string:
	pusha

	mov ah, 0Eh

.repeat:
	lodsb
	cmp al, 0
	je .done
	int 10h
	jmp short .repeat

.done:
	popa
	ret


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


l2hts:
	push bx
	push ax

	mov bx, ax

	mov dx, 0
	div word [SectorsPerTrack]
	add dl, 01h
	mov cl, dl
	mov ax, bx

	mov dx, 0
	div word [SectorsPerTrack]
	mov dx, 0
	div word [Sides]
	mov dh, dl
	mov ch, al

	pop ax
	pop bx

	mov dl, byte [bootdev]

	ret


; ------------------------------------------------------------------

	kern_filename	db "KERNEL  BIN"

	disk_error	db "Floppy error! Press any key...", 0
	file_not_found	db "KERNEL.BIN not found!", 0

	bootdev		db 0
	cluster		dw 0
	pointer		dw 0


	times 510-($-$$) db 0
	dw 0AA55h


buffer:					; 8 KB disk buffer at 07C0:0200
