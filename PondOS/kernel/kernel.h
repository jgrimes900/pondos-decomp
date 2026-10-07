/*
 * PondOS kernel - common definitions.
 *
 * The original kernel was hand-written x86-64 assembly that kept its state at
 * fixed physical addresses.  This reconstruction keeps every address the
 * hardware, the boot sector or a user program can observe (page tables, IDT,
 * GDT/TSS, DMA buffers, virtqueues, the large virtual regions) and turns the
 * rest of the scattered globals into ordinary C variables.  Where the
 * original address of a variable is useful for cross-referencing with the
 * disassembly it is noted next to the declaration as [0xNNNN].
 */
#ifndef PONDOS_KERNEL_H
#define PONDOS_KERNEL_H

typedef unsigned char      u8;
typedef unsigned short     u16;
typedef unsigned int       u32;
typedef unsigned long long u64;
typedef signed char        i8;
typedef short              i16;
typedef int                i32;
typedef long long          i64;
typedef u64                usize;
typedef _Bool              bool;
#define true  1
#define false 0
#define NULL  ((void *)0)

#define NORETURN __attribute__((noreturn))
#define PACKED   __attribute__((packed))
#define UNUSED   __attribute__((unused))

/* ------------------------------------------------------------------------
 * Fixed physical memory map
 * ---------------------------------------------------------------------- */
#define GDT_ADDR          0x1000
#define TSS_ADDR          0x1800
#define E820_COUNT_ADDR   0x1C78      /* dword written by the real-mode code */
#define PML4_ADDR         0x2000
#define BOOT_PT_ADDR      0x5000      /* identity map of 0-2 MiB */
#define IDT_ADDR          0x6000
#define E820_MAP_ADDR     0xF000      /* 24-byte entries */

#define BITMAP_PT_BASE    0x10000     /* 0x10000-0x17FFF: bitmap page tables */

#define MMIO_WINDOW       0x100000    /* 2 pages, remapped on demand */
#define USER_STUB_ADDR    0x108000    /* syscall + entry trampolines */
#define LAPIC_ADDR        0x10A000    /* -> 0xFEE00000 */
#define LAPIC_EOI         (LAPIC_ADDR + 0xB0)
#define LAPIC_SVR         (LAPIC_ADDR + 0xF0)

#define KBD_BUFFER        0x1C3F00    /* 256-byte line buffer */
#define KSTACK_GUARD_LO   0x1C4000
#define KSTACK_TOP        0x1C6000    /* also TSS.rsp0; 0x1C6000 is a guard */

#define BLK_HDR_ADDR      0x1C7900    /* 32 x 24-byte virtio-blk headers */
#define BLK_DONE_ADDR     0x1C7C00    /* completion stack, 16-byte entries */
#define BLK_REQ_ADDR      0x1C8C00    /* 128 x 0x28-byte requests */
#define BLK_VQ_ADDR       0x1CA000    /* request virtqueue */
#define BLK_NOTIFY_PAGE   0x1CB000

#define NET_TXBUF_ADDR    0x1CC000    /* 64 x 0x5F6 */
#define NET_RXBUF_ADDR    0x1E4000    /* 64 x 0x5F6 */
#define NET_TXQ_ADDR      0x1FC000
#define NET_RXQ_ADDR      0x1FD000
#define NET_RX_NOTIFY_PAGE 0x1FE000
#define NET_TX_NOTIFY_PAGE 0x1FF000

#define VGA_TEXT          0xB8000

/* Large virtual regions */
#define BITMAP_A          0xFFFF800000000000ULL   /* PML4[256] */
#define BITMAP_B          0xFFFFC00000000000ULL   /* PML4[384] */
#define TCB_BASE          0x8000000000ULL         /* 128 x 512 KiB */
#define TCB_STRIDE        0x80000
#define TCB_COUNT         128
#define TCP_HASH_ADDR     0x8004000000ULL         /* u16[2048] */
#define TCP_HEAP_ADDR     0x8004001000ULL         /* u16[128] */
#define PCAP_RING         0x9000000000ULL         /* 4 MiB, mapped twice */
#define PCAP_RING_SIZE    0x400000
#define USER_BASE         0x10000000000ULL        /* 1 TiB */
#define USER_LIMIT        0x18000000000ULL
#define USER_STACK_LO     0x10100000000ULL
#define USER_STACK_HI     0x10100100000ULL

/* Page table entry bits */
#define PTE_P    0x001ULL
#define PTE_W    0x002ULL
#define PTE_U    0x004ULL
#define PTE_PCD  0x010ULL
#define PTE_NX   0x8000000000000000ULL

/* Recursive mapping through PML4[511] */
#define PT_SELF_PML4 0xFFFFFFFFFFFFF000ULL
#define PT_SELF_PDPT 0xFFFFFFFFFFE00000ULL
#define PT_SELF_PD   0xFFFFFFFFC0000000ULL
#define PT_SELF_PT   0xFFFFFF8000000000ULL

#define MMIO8(a)   (*(volatile u8  *)(usize)(a))
#define MMIO16(a)  (*(volatile u16 *)(usize)(a))
#define MMIO32(a)  (*(volatile u32 *)(usize)(a))
#define MMIO64(a)  (*(volatile u64 *)(usize)(a))
#define PTR(a)     ((void *)(usize)(a))

/* ------------------------------------------------------------------------
 * CPU helpers
 * ---------------------------------------------------------------------- */
static inline void outb(u16 p, u8 v)  { __asm__ volatile("outb %0, %1" :: "a"(v), "Nd"(p)); }
static inline void outl(u16 p, u32 v) { __asm__ volatile("outl %0, %1" :: "a"(v), "Nd"(p)); }
static inline u8  inb(u16 p) { u8 v;  __asm__ volatile("inb %1, %0" : "=a"(v) : "Nd"(p)); return v; }
static inline u32 inl(u16 p) { u32 v; __asm__ volatile("inl %1, %0" : "=a"(v) : "Nd"(p)); return v; }
static inline void cli(void) { __asm__ volatile("cli" ::: "memory"); }
static inline void sti(void) { __asm__ volatile("sti" ::: "memory"); }
static inline void hlt(void) { __asm__ volatile("hlt" ::: "memory"); }
static inline void pause(void) { __asm__ volatile("pause" ::: "memory"); }
static inline void invlpg(u64 va) { __asm__ volatile("invlpg (%0)" :: "r"(va) : "memory"); }
static inline u64 read_rflags(void)
{
	u64 f;
	__asm__ volatile("pushfq; popq %0" : "=r"(f) :: "memory");
	return f;
}
/* pushfq; cli ... popfq-style IF restore used all over the original */
static inline u64 irq_save(void) { u64 f = read_rflags(); cli(); return f; }
static inline void irq_restore(u64 f) { if (f & 0x200) sti(); }

static inline u64 rdrand64(void)
{
	u64 v;
	__asm__ volatile("1: rdrand %0; jnc 1b" : "=r"(v) :: "cc");
	return v;
}
static inline u32 rdrand32(void)
{
	u32 v;
	__asm__ volatile("1: rdrand %0; jnc 1b" : "=r"(v) :: "cc");
	return v;
}
static inline u16 rdrand16(void)
{
	u16 v;
	__asm__ volatile("1: rdrand %0; jnc 1b" : "=r"(v) :: "cc");
	return v;
}
static inline u64 rdtsc(void)
{
	u32 lo, hi;
	__asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
	return ((u64)hi << 32) | lo;
}
static inline u64 crc32c_u64(u64 crc, u64 v)
{
	__asm__("crc32q %1, %0" : "+r"(crc) : "rm"(v));
	return crc;
}
static inline u32 crc32c_u32(u32 crc, u32 v)
{
	__asm__("crc32l %1, %0" : "+r"(crc) : "rm"(v));
	return crc;
}
static inline u16 bswap16(u16 v) { return (u16)((v >> 8) | (v << 8)); }
static inline u32 bswap32(u32 v) { return __builtin_bswap32(v); }

void *memcpy(void *d, const void *s, usize n);
void *memset(void *d, int c, usize n);

/* ------------------------------------------------------------------------
 * Interrupt / syscall frames (built by entry.S)
 * ---------------------------------------------------------------------- */
struct intr_frame {
	u64 r15, r14, r13, r12, r11, r10, r9, r8;
	u64 rbp, rdi, rsi, rdx, rcx, rbx, rax;
	u64 vector, error;
	u64 rip, cs, rflags, rsp, ss;
};

/* ------------------------------------------------------------------------
 * Module interfaces
 * ---------------------------------------------------------------------- */

/* time.c / interrupts.c */
u64  now_ms(void);                       /* qword [0x1C0C] */
static inline u32 now_ms32(void) { return (u32)now_ms(); }
void interrupts_init(void);
NORETURN void system_idle(void);
NORETURN void reboot(void);

/* console.c */
extern u32 cursor_pos;                   /* [0x1C00] */
void set_cursor(u16 pos);
void puts(const char *s);
void putc(char c);
void newline(void);
void print_u64(u64 v);
void print_u64_nl(u64 v);
char *utoa_back(u64 v, char *end);

/* shell.c */
void keyboard_poll(bool from_irq, struct intr_frame *f);
void dump_regs(struct intr_frame *f);

/* mem.c */
bool mem_init(void);
u64  page_alloc(bool keep_in_a);
bool map_page(u64 va, u64 flags);
u64  page_query(u64 va);
bool user_buffer_ok(u64 p, i32 len);

/* pci.c */
u32  pci_addr(u8 bus, u8 dev, u8 fn, u8 reg);
u32  pci_read(u32 addr);
void pci_write(u32 addr, u32 val);
u64  pci_read_bar(u32 addr);
void pci_scan(void);
extern u32 net_pci;                      /* [0x1C28] */
extern u32 blk_pci;                      /* [0x1CD0] */

/* virtio.c */
struct virtio_caps {
	u32 found;          /* 1 common, 2 notify, 4 msix, 8 device */
	u64 common;
	u64 notify;
	u32 notify_mult;
	u64 device;
};
u64  mmio_map(u64 phys);
void mmio_unmap(void);
void virtio_find_caps(u32 cfg, u32 msix_vector, struct virtio_caps *c);

/* blk.c */
extern u64 disk_sectors;                 /* [0x1CD8] */
extern u8  disk_allow_low_writes;        /* byte [0x1D14] */
bool blk_init(void);
void blk_requests_init(void);
u32  blk_request(u32 type, u64 sector, u64 buf, u32 count, u64 tag);
u32  blk_sync(u32 type, u64 sector, u64 buf, u32 count);
void blk_complete(void);
void blk_poll_completion(u64 *out);

/* net.c */
extern u8  my_mac[8];                    /* [0x1C30] (6 bytes + 2 zero) */
extern u32 net_has_mac_feature;          /* [0x1CB8] */
extern volatile u64 rx_packet_count;     /* [0x1C38] */
extern u32 my_ip;                        /* [0x1C4C] network order */
extern u64 gateway_mac;                  /* [0x1C70] 48 bits */
bool net_init(void);
void net_tx_reclaim(void);
void net_tx_wait_free(void);
u16  net_tx_free_count(void);
u16  tx_alloc(void);
u8  *tx_buffer(u16 idx);
void tx_send(u16 idx, u32 len);
void net_rx(u8 *pkt, u32 len);
void net_irq(void);

struct pkt {               /* replaces the original's "push offsets on the caller's stack" trick */
	u8 *buf;
	u32 ip_off;
	u32 l4_off;
	u32 len;
};
u32  eth_header(u8 *b, u32 off, u64 dst_mac, u16 ethertype);
u32  ip_header(u8 *b, u32 off, u8 proto, u32 dst);
void ip_finish(u8 *ip, u16 total);
u32  udp_header(u8 *b, u32 off, u16 sport, u16 dport);
u32  tcp_header(u8 *b, u32 off, u16 sport, u16 dport, u16 win, u32 seq, u32 ack, u8 flags);
u16  csum_partial(const u8 *b, u32 len, u64 sum);
void udp_begin(struct pkt *p, u16 txidx, u16 sport, u16 dport, u32 dst);
u32  udp_finish(struct pkt *p, u32 dst);
void tcp_begin(struct pkt *p, u16 txidx, u8 flags, u16 sport, u16 dport,
               u16 win, u32 dst, u32 seq, u32 ack);
u32  tcp_finish(struct pkt *p, u32 dst);
u64  arp_resolve(u32 ip, bool *ok);
extern volatile u32 arp_state;           /* [0x1CC0] */
extern u32 arp_ip;                       /* [0x1CC4] */
extern u64 arp_mac;                      /* [0x1CC8] */

/* dhcp.c */
extern volatile u32 dhcp_state;          /* [0x1C50] */
extern u32 dhcp_xid;                     /* [0x1C54] */
extern u64 dhcp_offer_time;              /* [0x1C58] */
extern u64 dhcp_lease_ms;                /* [0x1C60] */
extern u32 dhcp_server;                  /* [0x1C68] */
extern u32 dhcp_offer_ip;                /* [0x1C6C] */
extern u32 dhcp_router;                  /* [0x1CBC] */
bool dhcp_configure(void);
void dhcp_rx(const u8 *bootp, i32 len, u32 src_ip);

/* dns.c */
extern volatile u32 dns_state;           /* [0x1C90] */
extern u32 dns_addr;                     /* [0x1C94] */
extern u64 dns_ttl_ms;                   /* [0x1C98] */
void dns_query(const char *name);
void dns_rx(u8 *msg, i32 len);

/* pcap.c */
extern u32 pcap_state;                   /* [0x1D0C] */
void pcap_capture(const u8 *pkt, u32 len);
void pcap_flush(void);

/* tcp.c */
extern u32 tcp_enabled;                  /* [0x1CB4] */
extern u32 tcp_listen_cfg;               /* [0x1CF4] */
extern u32 tcp_free_head;                /* [0x1CA0] */
extern u32 tcp_sendq_head;               /* [0x1CA4] */
bool tcp_init(void);
void tcp_coarse_timer(void);
void tcp_send_pending(void);
void tcp_input(u8 *th, u32 seglen, u32 hdrlen, u32 seglen_edi,
               u32 src_ip, u32 dst_ip, u16 sport, u16 dport);
u32  tcp_sys_connect(u32 ip, u32 ports);
void tcp_sys_close(u32 idx);
void tcp_free(u32 idx);
i32  tcp_sys_send(u32 idx, u64 buf, i32 len);
u64  tcp_sys_recv(u32 idx, u64 buf, i32 len);
void tcp_sys_abort(u32 idx);
void tcp_sys_reconnect(u32 idx, u32 ip, u32 ports);
u64  tcp_poll_notify(void);
void tcp_shell_list(void);

/* loader.c */
bool load_user_program(void);
extern u64 user_kstack;                  /* [0x1CF8] */

/* syscall.c */
u64  syscall_dispatch(u32 num, u64 arg);

/* entry.S */
extern char user_stub_start[], user_stub_end[];
NORETURN void enter_user(u64 entry, u64 stack_top);
extern void isr_default(void), isr_irq_master(void), isr_irq8(void),
	isr_debug(void), isr_breakpoint(void), isr_gpf(void), isr_page_fault(void),
	isr_timer(void), isr_keyboard(void), isr_spurious(void), isr_net(void),
	isr_disk(void), syscall_entry(void);

#endif
