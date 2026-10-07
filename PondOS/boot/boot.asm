; PondOS boot sector
;
; Loaded by the BIOS at 0000:7C00 with DL = boot drive. It:
;   1. reads the kernel (KERNEL_SECTORS sectors from LBA 1) to 0000:7E00 with
;      INT 13h/AH=42h,
;   2. enables A20, sets 80x25 text mode and homes the cursor,
;   3. checks CPUID for long mode (halts if absent),
;   4. builds the GDT at 0x1000 and the boot page tables at 0x2000-0x5FFF,
;   5. calls the kernel's real-mode E820 routine at 0x7E00,
;   6. switches straight from real mode to long mode and jumps to the
;      kernel's 64-bit entry point (KERNEL_ENTRY).
;
; Assembled with -DORIGINAL this file reproduces the original boot sector
; byte for byte.  Without it, the sector count comes from the C kernel build.
;
; Physical memory set up here:
;   0x1000  GDT   08 kernel code64, 10 kernel data, 18 user data (DPL3),
;                 20 user code64 (DPL3), 28 TSS (base 0x1800, limit 0x68)
;   0x1C00  kernel globals area (zeroed, 0x118 bytes)
;   0x2000  PML4  [0] -> 0x3000, [511] -> 0x2000 (recursive mapping)
;   0x3000  PDPT  [0] -> 0x4000
;   0x4000  PD    [0] -> 0x5000
;   0x5000  PT    identity map of 0-2 MiB, supervisor RW; pages 7..14
;                 (0x7000-0xEFFF, the kernel image) user read-only;
;                 0x10A000 -> local APIC at 0xFEE00000 (uncached)

%ifndef KERNEL_SECTORS
%define KERNEL_SECTORS 0x33
%endif
%ifndef KERNEL_ENTRY
%define KERNEL_ENTRY 0x7E8C
%endif

	bits 16
	org 0x7C00

start:
	cli
	cld
	mov ah, 0x42			; extended read, DS:SI -> DAP
	mov si, dap
	int 0x13
	mov sp, 0x800
	mov ax, 0x2401			; enable A20
	int 0x15
	mov ah, 0			; 80x25 colour text
	mov al, 3
	int 0x10
	mov ah, 2			; cursor to 0,0
	mov bh, 0
	mov dh, 0
	mov dl, 0
	int 0x10

	mov eax, 0x80000001		; long mode supported?
	cpuid
	and edx, 1 << 29
	cmp edx, byte 0
	jnz .have_lm
.halt:
	hlt
	jmp short .halt

.have_lm:
	mov di, 0x1C00			; kernel globals
	mov ecx, 0x46
	xor eax, eax
	rep stosd
	mov di, 0x1000			; GDT
	mov cx, 0x200
	xor eax, eax
	rep stosd
	mov eax, 0xFFFF
	mov [0x1008], eax		; 08: kernel code, 64-bit
	mov dword [0x100C], 0x00AF9A00
	mov [0x1010], eax		; 10: kernel data
	mov dword [0x1014], 0x00CF9200
	mov [0x1020], eax		; 20: user code, 64-bit, DPL 3
	mov dword [0x1024], 0x00AFFA00
	mov [0x1018], eax		; 18: user data, DPL 3
	mov dword [0x101C], 0x00CFF200
	mov dword [0x1028], 0x18000068	; 28: TSS, base 0x1800, limit 0x68
	mov dword [0x102C], 0x00008900
	xor eax, eax
	mov [0x1030], eax
	mov [0x1034], eax

	call 0x7E00			; kernel: collect the E820 memory map

	mov di, 0x2000			; page tables
	mov ecx, 0x1000
	xor eax, eax
	rep stosd
	mov dword [0x2FF8], 0x2003	; PML4[511] = PML4 (recursive)
	mov dword [0x2000], 0x3007
	mov dword [0x3000], 0x4007
	mov dword [0x4000], 0x5007
	mov di, 0x5000			; identity map 0-2 MiB
	mov bx, 0x6000
	mov eax, 3
.pt:
	mov [di], eax
	add di, byte 8
	add eax, 0x1000
	cmp di, bx
	jnz .pt
	mov di, 0x5038			; pages 7..14 user, read-only
	mov bx, 0x5070
	mov eax, 0x7001
.upt:
	mov [di], eax
	add di, byte 8
	add eax, 0x1000
	cmp di, bx
	jng .upt
	mov dword [0x5850], 0xFEE00013	; 0x10A000 -> local APIC

	mov al, 0xFF			; mask both PICs
	out 0xA1, al
	out 0x21, al
	a32 mov dword [esp - 4], 0	; empty IDT
	a32 mov dword [esp - 8], 0
	a32 lidt [esp - 8]
	mov eax, cr4			; PAE | PGE
	or eax, 0xA0
	mov cr4, eax
	mov eax, 0x2000
	mov cr3, eax
	mov ecx, 0xC0000080		; EFER: LME | SCE | NXE
	rdmsr
	or eax, 0x901
	wrmsr
	mov eax, cr0			; PG | WP | PE
	or eax, 0x80010001
	mov cr0, eax
	a32 mov word [esp - 0xA], 0x37
	a32 mov dword [esp - 8], 0x1000
	a32 mov dword [esp - 4], 0
	a32 lgdt [esp - 0xA]
	jmp 0x08:long_mode

	bits 64
long_mode:
	mov ax, 0x10
	mov ds, eax
	mov ss, eax
	mov es, eax
	mov fs, eax
	mov gs, eax
	mov ebp, esp
	jmp KERNEL_ENTRY

dap:					; INT 13h disk address packet
	db 0x10, 0
	dw KERNEL_SECTORS
	dw 0x7E00, 0x0000		; buffer 0000:7E00
	dq 1				; starting LBA

	; Partition table: one active entry of type 0xDA covering sector 1.
	times 0x1BE - ($ - $$) db 0
	db 0x80, 0x00, 0x02, 0x00, 0xDA, 0x00, 0x03, 0x00
	dd 1, 1
	times 510 - ($ - $$) db 0
	dw 0xAA55
