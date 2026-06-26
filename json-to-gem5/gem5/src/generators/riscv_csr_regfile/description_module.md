# RiscvCsrRegfile Module Description

## Module Function Overview

riscv_csr_regfile is a RISC-V CSR (Control and Status Register) register file module that implements all CSR register read/write operations. It supports both Machine mode registers (mstatus, mepc, mcause, mtval, mtvec, mie, mip, etc.) and Supervisor mode registers (sstatus, sepc, scause, stval, stvec, satp, etc.). The module handles exception/interrupt save and restore logic, privilege level management, and interrupt delegation.

## Port List

### Input Ports
| Port Name | Width | Direction | Description |
|-----------|-------|-----------|-------------|
| ext_intr_i | 1 | input | External interrupt input |
| timer_intr_i | 1 | input | Timer interrupt input |
| cpu_id_i | 31:0 | input | CPU ID (for mhartid) |
| misa_i | 31:0 | input | MISA register value |
| exception_i | 5:0 | input | Exception encoding (bit5=valid, bit4=interrupt, bits3:0=cause) |
| exception_pc_i | 31:0 | input | Exception PC |
| exception_addr_i | 31:0 | input | Exception address |
| csr_ren_i | 1 | input | CSR read enable |
| csr_raddr_i | 11:0 | input | CSR read address |
| csr_waddr_i | 11:0 | input | CSR write address |
| csr_wdata_i | 31:0 | input | CSR write data |

### Output Ports
| Port Name | Width | Direction | Description |
|-----------|-------|-----------|-------------|
| csr_rdata_o | 31:0 | output | CSR read data |
| csr_branch_o | 1 | output | CSR branch request (exception/interrupt jump) |
| csr_target_o | 31:0 | output | CSR branch target address |
| priv_o | 1:0 | output | Current privilege level |
| status_o | 31:0 | output | Status register (mstatus) value |
| satp_o | 31:0 | output | SATP register value |
| interrupt_o | 31:0 | output | Interrupt pending flags (bitmask) |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| mstatus_init | uint32_t | 0x00001800 | Initial mstatus value |
| priv_init | uint8_t | 3 | Initial privilege level (3=Machine) |
| mtvec_base | uint32_t | 0x80000000 | Base address for mtvec |
| stvec_base | uint32_t | 0x80000000 | Base address for stvec |

## Internal Signals

| Signal | Width | Description |
|--------|-------|-------------|
| mstatus_val | 32 | Machine status register |
| misa_val | 32 | Machine ISA register |
| medeleg_val | 32 | Machine exception delegation |
| mideleg_val | 32 | Machine interrupt delegation |
| mie_val | 32 | Machine interrupt enable |
| mtvec_val | 32 | Machine trap vector base |
| mscratch_val | 32 | Machine scratch |
| mepc_val | 32 | Machine exception PC |
| mcause_val | 32 | Machine cause |
| mtval_val | 32 | Machine trap value |
| mip_val | 32 | Machine interrupt pending |
| mcycle_val | 32 | Machine cycle counter low |
| mcycleh_val | 32 | Machine cycle counter high |
| mtimecmp_val | 32 | Machine time compare |
| mtimecmp_v2_val | 32 | Machine time compare v2 |
| sie_val | 32 | Supervisor interrupt enable |
| stvec_val | 32 | Supervisor trap vector base |
| sscratch_val | 32 | Supervisor scratch |
| sepc_val | 32 | Supervisor exception PC |
| scause_val | 32 | Supervisor cause |
| stval_val | 32 | Supervisor trap value |
| satp_val | 32 | Supervisor address translation |
| priv_lvl | 2 | Current privilege level (0=U, 1=S, 3=M) |
