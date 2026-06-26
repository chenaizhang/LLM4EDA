# RiscvCsr Module Description

## Module Function Overview

The riscv_csr module is a RISC-V CSR (Control and Status Register) processing module that handles all CSR instructions including CSRRW, CSRRS, CSRRC, CSRRWI, CSRRSI, CSRRCI, ECALL, EBREAK, ERET, WFI, and FENCE instructions. It manages interrupt handling, exception processing, privilege level switching, and MMU control signal generation (sum, mxr, satp, flush, priv). The module uses the riscv_csr_regfile submodule to store all CSR register state.

## Port List

### Input Ports
| Port Name | Width | Direction | Description |
|-----------|-------|-----------|-------------|
| opcode_valid_i | 1 | input | Opcode valid flag |
| opcode_opcode_i | 31:0 | input | Instruction opcode |
| opcode_pc_i | 31:0 | input | Instruction PC value |
| opcode_invalid_i | 1 | input | Illegal instruction flag |
| opcode_rd_idx_i | 4:0 | input | Destination register index |
| opcode_ra_idx_i | 4:0 | input | Source operand A register index |
| opcode_rb_idx_i | 4:0 | input | Source operand B register index |
| opcode_ra_operand_i | 31:0 | input | Source operand A value |
| opcode_rb_operand_i | 31:0 | input | Source operand B value |
| csr_writeback_write_i | 1 | input | CSR writeback write enable |
| csr_writeback_waddr_i | 11:0 | input | CSR writeback write address |
| csr_writeback_wdata_i | 31:0 | input | CSR writeback write data |
| csr_writeback_exception_i | 5:0 | input | CSR writeback exception type |
| csr_writeback_exception_pc_i | 31:0 | input | CSR writeback exception PC |
| csr_writeback_exception_addr_i | 31:0 | input | CSR writeback exception address |
| cpu_id_i | 31:0 | input | CPU ID |
| reset_vector_i | 31:0 | input | Reset vector base address |
| intr_i | 1 | input | External interrupt signal |
| interrupt_inhibit_i | 1 | input | Interrupt inhibit flag |

### Output Ports
| Port Name | Width | Direction | Description |
|-----------|-------|-----------|-------------|
| csr_result_e1_value_o | 31:0 | output | CSR result value (E1 stage) |
| csr_result_e1_write_o | 1 | output | CSR result write enable (E1 stage) |
| csr_result_e1_wdata_o | 31:0 | output | CSR result write data (E1 stage) |
| csr_result_e1_exception_o | 5:0 | output | CSR result exception type (E1 stage) |
| branch_csr_request_o | 1 | output | CSR branch request |
| branch_csr_pc_o | 31:0 | output | CSR branch target PC |
| branch_csr_priv_o | 1:0 | output | CSR branch target privilege level |
| take_interrupt_o | 1 | output | Interrupt response flag |
| ifence_o | 1 | output | Instruction fence flag |
| mmu_priv_d_o | 1:0 | output | MMU data access privilege level |
| mmu_sum_o | 1 | output | MMU Supervisor User Memory enable |
| mmu_mxr_o | 1 | output | MMU executable-readable flag |
| mmu_flush_o | 1 | output | MMU TLB flush flag |
| mmu_satp_o | 31:0 | output | MMU SATP register value |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| csrfile | RiscvCsrRegfile | (required) | CSR register file submodule |

## Internal Signals

| Signal | Width | Description |
|--------|-------|-------------|
| prev_satp_val | 32 | Previous SATP value for TLB flush detection |

## Submodule

### u_csrfile (riscv_csr_regfile)
CSR register file submodule that stores all CSR register state, including mstatus, misa, mtvec, mepc, mcause, mtval, mie, mip, mscratch, mcycle, mtimecmp, medeleg, mideleg, sepc, stvec, scause, stval, satp, sscratch and other CSR registers.

## Function Description

### 1. CSR Instruction Processing (CSRRW, CSRRS, CSRRC, CSRRWI, CSRRSI, CSRRCI)
Decodes CSR instructions from the opcode. Sets up CSR read address on the regfile for the decode stage. The read data is output as csr_result_e1_value_o. The write data is computed by the pipeline logic between E1 and writeback stages and arrives via csr_writeback_wdata_i.

### 2. Special Instruction Processing
- **ECALL**: Generates synchronous exception with cause code based on current privilege level (8 for U-mode, 9 for S-mode, 11 for M-mode)
- **EBREAK**: Generates breakpoint exception (cause code 3)
- **MRET**: Reads MEPC, restores MIE from MPIE, sets MPP=0, generates branch to return address
- **SRET**: Reads SEPC, restores SIE from SPIE, sets SPP=0, generates branch to return address
- **WFI**: No special action in simplified implementation
- **FENCE**: Sets ifence_o flag

### 3. Interrupt Handling
Forwards external interrupt (intr_i) to regfile submodule. Outputs take_interrupt_o when regfile detects pending interrupts.

### 4. Exception Handling
Writeback stage exception (csr_writeback_exception_i) takes priority over decode stage exceptions. Forwards exception information to regfile for state saving.

### 5. MMU Control Output
Generates MMU signals based on mstatus register state:
- mmu_priv_d_o: Uses MPP when MPRV is set, otherwise uses current privilege level
- mmu_sum_o: From mstatus.SUM (bit 18)
- mmu_mxr_o: From mstatus.MXR (bit 19)
- mmu_satp_o: Direct passthrough from regfile
- mmu_flush_o: Set when satp value changes
