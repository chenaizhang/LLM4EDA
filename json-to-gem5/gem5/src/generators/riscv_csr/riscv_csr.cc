#include "generators/riscv_csr/riscv_csr.hh"

#include "base/trace.hh"
#include "debug/DUT.hh"
#include "debug/TestGenerator.hh"

namespace gem5 {

// ==================== CSR Address Constants ====================
// (matching riscv_csr_regfile internal constants for reference)
static const uint32_t CSR_MSTATUS  = 0x300;
static const uint32_t CSR_SSTATUS  = 0x100;
static const uint32_t CSR_MEPC     = 0x341;
static const uint32_t CSR_SEPC     = 0x141;

// ==================== Constructor ====================
RiscvCsr::RiscvCsr(const RiscvCsrParams &params) :
    SimObject(params),
    // Input port registers
    opcode_valid_i_reg(0),
    opcode_opcode_i_reg(0),
    opcode_pc_i_reg(0),
    opcode_invalid_i_reg(0),
    opcode_rd_idx_i_reg(0),
    opcode_ra_idx_i_reg(0),
    opcode_rb_idx_i_reg(0),
    opcode_ra_operand_i_reg(0),
    opcode_rb_operand_i_reg(0),
    csr_writeback_write_i_reg(0),
    csr_writeback_waddr_i_reg(0),
    csr_writeback_wdata_i_reg(0),
    csr_writeback_exception_i_reg(0),
    csr_writeback_exception_pc_i_reg(0),
    csr_writeback_exception_addr_i_reg(0),
    cpu_id_i_reg(0),
    reset_vector_i_reg(0),
    intr_i_reg(0),
    interrupt_inhibit_i_reg(0),
    // Output port values
    csr_result_e1_value_o_val(0),
    csr_result_e1_write_o_val(0),
    csr_result_e1_wdata_o_val(0),
    csr_result_e1_exception_o_val(0),
    branch_csr_request_o_val(0),
    branch_csr_pc_o_val(0),
    branch_csr_priv_o_val(0),
    take_interrupt_o_val(0),
    ifence_o_val(0),
    mmu_priv_d_o_val(0),
    mmu_sum_o_val(0),
    mmu_mxr_o_val(0),
    mmu_flush_o_val(0),
    mmu_satp_o_val(0),
    // Submodule reference
    csrfile(*params.csrfile),
    // Internal state
    prev_satp_val(0)
{
    DPRINTF(DUT, "Created RiscvCsr\n");
}

// ==================== Input Set Functions ====================

void
RiscvCsr::setOpcodeValidI(uint32_t val)
{
    opcode_valid_i_reg = val & 0x1;
}

void
RiscvCsr::setOpcodeOpcodeI(uint32_t val)
{
    opcode_opcode_i_reg = val;
}

void
RiscvCsr::setOpcodePcI(uint32_t val)
{
    opcode_pc_i_reg = val;
}

void
RiscvCsr::setOpcodeInvalidI(uint32_t val)
{
    opcode_invalid_i_reg = val & 0x1;
}

void
RiscvCsr::setOpcodeRdIdxI(uint32_t val)
{
    opcode_rd_idx_i_reg = val & 0x1F;
}

void
RiscvCsr::setOpcodeRaIdxI(uint32_t val)
{
    opcode_ra_idx_i_reg = val & 0x1F;
}

void
RiscvCsr::setOpcodeRbIdxI(uint32_t val)
{
    opcode_rb_idx_i_reg = val & 0x1F;
}

void
RiscvCsr::setOpcodeRaOperandI(uint32_t val)
{
    opcode_ra_operand_i_reg = val;
}

void
RiscvCsr::setOpcodeRbOperandI(uint32_t val)
{
    opcode_rb_operand_i_reg = val;
}

void
RiscvCsr::setCsrWritebackWriteI(uint32_t val)
{
    csr_writeback_write_i_reg = val & 0x1;
}

void
RiscvCsr::setCsrWritebackWaddrI(uint32_t val)
{
    csr_writeback_waddr_i_reg = val & 0xFFF;
}

void
RiscvCsr::setCsrWritebackWdataI(uint32_t val)
{
    csr_writeback_wdata_i_reg = val;
}

void
RiscvCsr::setCsrWritebackExceptionI(uint32_t val)
{
    csr_writeback_exception_i_reg = val & 0x3F;
}

void
RiscvCsr::setCsrWritebackExceptionPcI(uint32_t val)
{
    csr_writeback_exception_pc_i_reg = val;
}

void
RiscvCsr::setCsrWritebackExceptionAddrI(uint32_t val)
{
    csr_writeback_exception_addr_i_reg = val;
}

void
RiscvCsr::setCpuIdI(uint32_t val)
{
    cpu_id_i_reg = val;
}

void
RiscvCsr::setResetVectorI(uint32_t val)
{
    reset_vector_i_reg = val;
}

void
RiscvCsr::setIntrI(uint32_t val)
{
    intr_i_reg = val & 0x1;
}

void
RiscvCsr::setInterruptInhibitI(uint32_t val)
{
    interrupt_inhibit_i_reg = val & 0x1;
}

// ==================== Output Get Functions ====================

uint32_t
RiscvCsr::getCsrResultE1ValueO()
{
    return csr_result_e1_value_o_val;
}

uint32_t
RiscvCsr::getCsrResultE1WriteO()
{
    return csr_result_e1_write_o_val;
}

uint32_t
RiscvCsr::getCsrResultE1WdataO()
{
    return csr_result_e1_wdata_o_val;
}

uint32_t
RiscvCsr::getCsrResultE1ExceptionO()
{
    return csr_result_e1_exception_o_val;
}

uint32_t
RiscvCsr::getBranchCsrRequestO()
{
    return branch_csr_request_o_val;
}

uint32_t
RiscvCsr::getBranchCsrPcO()
{
    return branch_csr_pc_o_val;
}

uint32_t
RiscvCsr::getBranchCsrPrivO()
{
    return branch_csr_priv_o_val;
}

uint32_t
RiscvCsr::getTakeInterruptO()
{
    return take_interrupt_o_val;
}

uint32_t
RiscvCsr::getIfenceO()
{
    return ifence_o_val;
}

uint32_t
RiscvCsr::getMmuPrivDO()
{
    return mmu_priv_d_o_val;
}

uint32_t
RiscvCsr::getMmuSumO()
{
    return mmu_sum_o_val;
}

uint32_t
RiscvCsr::getMmuMxrO()
{
    return mmu_mxr_o_val;
}

uint32_t
RiscvCsr::getMmuFlushO()
{
    return mmu_flush_o_val;
}

uint32_t
RiscvCsr::getMmuSatpO()
{
    return mmu_satp_o_val;
}

// ==================== Process Function ====================

void
RiscvCsr::process()
{
    // Clear pulse outputs at start of cycle
    csr_result_e1_write_o_val = 0;
    branch_csr_request_o_val = 0;
    ifence_o_val = 0;
    mmu_flush_o_val = 0;
    csr_result_e1_exception_o_val = 0;

    // ==================== Phase 1: Set Default Regfile Inputs ====================

    // Default CSR write from writeback stage
    csrfile.setCsrWaddrI(csr_writeback_waddr_i_reg);
    csrfile.setCsrWdataI(csr_writeback_wdata_i_reg);

    // Default exception setup: writeback stage exception has priority
    bool wb_exception_valid = ((csr_writeback_exception_i_reg >> 5) & 0x1) != 0;
    if (wb_exception_valid) {
        csrfile.setExceptionI(csr_writeback_exception_i_reg);
        csrfile.setExceptionPcI(csr_writeback_exception_pc_i_reg);
        csrfile.setExceptionAddrI(csr_writeback_exception_addr_i_reg);
    } else {
        csrfile.setExceptionI(0);
        csrfile.setExceptionPcI(0);
        csrfile.setExceptionAddrI(0);
    }

    // Default: no CSR read from decode stage
    csrfile.setCsrRenI(0);
    csrfile.setCsrRaddrI(0);

    // ==================== Phase 2: Decode Current Instruction ====================
    bool is_csr_inst = false;
    bool is_eret = false;

    if ((opcode_valid_i_reg != 0) && (opcode_invalid_i_reg == 0)) {
        uint32_t opcode_bits = opcode_opcode_i_reg & 0x7F;

        if (opcode_bits == 0x73) {
            // SYSTEM opcode - CSR instructions and system calls
            uint32_t funct3 = (opcode_opcode_i_reg >> 12) & 0x7;
            uint32_t funct12 = (opcode_opcode_i_reg >> 20) & 0xFFF;

            if ((funct3 >= 1) && (funct3 <= 7)) {
                // CSR instructions: CSRRW(1), CSRRS(2), CSRRC(3),
                // CSRRWI(5), CSRRSI(6), CSRRCI(7)
                is_csr_inst = true;
                uint32_t csr_addr = (opcode_opcode_i_reg >> 20) & 0xFFF;
                csrfile.setCsrRenI(1);
                csrfile.setCsrRaddrI(csr_addr);
                csr_result_e1_write_o_val = 1;

                DPRINTF(DUT, "CSR instruction: addr=0x%03X funct3=%d\n",
                        csr_addr, funct3);
            } else if (funct3 == 0) {
                // SYSTEM sub-instructions (ECALL, EBREAK, ERET, WFI)
                if (funct12 == 0x000) {
                    // ECALL - generate exception based on current privilege
                    if (!wb_exception_valid) {
                        uint32_t current_priv = csrfile.getPrivO();
                        uint32_t cause;
                        if (current_priv == 0) {
                            cause = 8;   // U-mode ECALL
                        } else if (current_priv == 1) {
                            cause = 9;   // S-mode ECALL
                        } else {
                            cause = 11;  // M-mode ECALL
                        }
                        csrfile.setExceptionI((1 << 5) | cause);
                        csrfile.setExceptionPcI(opcode_pc_i_reg);
                        csrfile.setExceptionAddrI(0);
                        DPRINTF(DUT, "ECALL: priv=%d cause=%d\n",
                                current_priv, cause);
                    }
                } else if (funct12 == 0x001) {
                    // EBREAK - generate breakpoint exception
                    if (!wb_exception_valid) {
                        csrfile.setExceptionI((1 << 5) | 3);
                        csrfile.setExceptionPcI(opcode_pc_i_reg);
                        csrfile.setExceptionAddrI(0);
                        DPRINTF(DUT, "EBREAK\n");
                    }
                } else if (funct12 == 0x102) {
                    // SRET - return from supervisor exception
                    is_eret = true;

                    // Read SEPC to get return address
                    csrfile.setCsrRenI(1);
                    csrfile.setCsrRaddrI(CSR_SEPC);

                    // Compute new mstatus for SRET:
                    //   SIE = old SPIE
                    //   SPIE = 1
                    //   SPP = 0
                    // Target privilege = old SPP
                    uint32_t old_status = csrfile.getStatusO();
                    uint32_t old_spie = (old_status >> 5) & 0x1;
                    uint32_t old_spp = (old_status >> 8) & 0x1;

                    uint32_t new_status = old_status;
                    // SIE = old SPIE
                    if (old_spie != 0) {
                        new_status = new_status | (1 << 0);
                    } else {
                        new_status = new_status & ~(1 << 0);
                    }
                    // SPIE = 1
                    new_status = new_status | (1 << 5);
                    // SPP = 0
                    new_status = new_status & ~(1 << 8);

                    // Override CSR write for mstatus update (SRET takes
                    // priority over writeback)
                    csrfile.setCsrWaddrI(CSR_SSTATUS);
                    csrfile.setCsrWdataI(new_status);

                    // Set target privilege from old SPP
                    branch_csr_priv_o_val = old_spp;

                    DPRINTF(DUT, "SRET: old_spp=%d old_spie=%d\n",
                            old_spp, old_spie);
                } else if (funct12 == 0x302) {
                    // MRET - return from machine exception
                    is_eret = true;

                    // Read MEPC to get return address
                    csrfile.setCsrRenI(1);
                    csrfile.setCsrRaddrI(CSR_MEPC);

                    // Compute new mstatus for MRET:
                    //   MIE = old MPIE
                    //   MPIE = 1
                    //   MPP = 0
                    // Target privilege = old MPP
                    uint32_t old_status = csrfile.getStatusO();
                    uint32_t old_mpie = (old_status >> 7) & 0x1;
                    uint32_t old_mpp = (old_status >> 11) & 0x3;

                    uint32_t new_status = old_status;
                    // MIE = old MPIE
                    if (old_mpie != 0) {
                        new_status = new_status | (1 << 3);
                    } else {
                        new_status = new_status & ~(1 << 3);
                    }
                    // MPIE = 1
                    new_status = new_status | (1 << 7);
                    // MPP = 0
                    new_status = new_status & ~(0x3 << 11);

                    // Override CSR write for mstatus update (MRET takes
                    // priority over writeback)
                    csrfile.setCsrWaddrI(CSR_MSTATUS);
                    csrfile.setCsrWdataI(new_status);

                    // Set target privilege from old MPP
                    branch_csr_priv_o_val = old_mpp;

                    DPRINTF(DUT, "MRET: old_mpp=%d old_mpie=%d\n",
                            old_mpp, old_mpie);
                } else if (funct12 == 0x105) {
                    // WFI - wait for interrupt (no special action in
                    // simplified implementation)
                    DPRINTF(DUT, "WFI\n");
                }
            }
        } else if (opcode_bits == 0x0F) {
            // FENCE / FENCE.I instruction
            ifence_o_val = 1;
            DPRINTF(DUT, "FENCE\n");
        }
    }

    // ==================== Phase 3: Set Up Remaining Regfile Inputs ====================

    // External interrupt (masked by interrupt_inhibit_i)
    uint32_t effective_intr = intr_i_reg & (~interrupt_inhibit_i_reg) & 0x1;
    csrfile.setExtIntrI(effective_intr);
    // No timer interrupt from this module (timer is handled externally)
    csrfile.setTimerIntrI(0);
    // CPU ID
    csrfile.setCpuIdI(cpu_id_i_reg);
    // MISA: RV32I (bit 8 = I extension)
    csrfile.setMisaI(0x40000000);

    // ==================== Phase 4: Call Regfile Process ====================

    csrfile.process();

    // ==================== Phase 5: Read Regfile Outputs ====================

    uint32_t csr_rdata = csrfile.getCsrRdataO();
    bool csr_branch = csrfile.getCsrBranchO();
    uint32_t csr_target = csrfile.getCsrTargetO();
    uint32_t priv = csrfile.getPrivO();
    uint32_t status = csrfile.getStatusO();
    uint32_t satp = csrfile.getSatpO();
    uint32_t interrupt = csrfile.getInterruptO();

    // ==================== Phase 6: Generate Module Outputs ====================

    // CSR E1 stage result
    if (is_csr_inst) {
        csr_result_e1_value_o_val = csr_rdata;
        csr_result_e1_wdata_o_val = csr_rdata;
    }

    // Branch outputs
    if (is_eret) {
        // ERET: branch to return address (MEPC or SEPC), priv already set
        branch_csr_request_o_val = 1;
        branch_csr_pc_o_val = csr_rdata;
        ifence_o_val = 1;
    } else if (csr_branch) {
        // Exception/interrupt branch (handled by regfile)
        branch_csr_request_o_val = 1;
        branch_csr_pc_o_val = csr_target;
        branch_csr_priv_o_val = priv;
    }

    // Interrupt output
    if (interrupt != 0) {
        take_interrupt_o_val = 1;
    } else {
        take_interrupt_o_val = 0;
    }

    // MMU signal generation from mstatus:
    //   mstatus.MPRV (bit 17) - use MPP for data accesses when set
    //   mstatus.MPP  (bits 12:11) - machine previous privilege
    //   mstatus.SUM   (bit 18) - Supervisor User Memory enable
    //   mstatus.MXR   (bit 19) - Make eXecutable Readable
    uint32_t mprv = (status >> 17) & 0x1;
    uint32_t mpp = (status >> 11) & 0x3;

    if (mprv != 0) {
        mmu_priv_d_o_val = mpp;
    } else {
        mmu_priv_d_o_val = priv;
    }

    mmu_sum_o_val = (status >> 18) & 0x1;
    mmu_mxr_o_val = (status >> 19) & 0x1;
    mmu_satp_o_val = satp;

    // TLB flush on satp value change
    if (satp != prev_satp_val) {
        mmu_flush_o_val = 1;
        prev_satp_val = satp;
    }

    DPRINTF(DUT, "RiscvCsr: priv=%d satp=0x%08X flush=%d\n",
            priv, satp, mmu_flush_o_val);
}

} // namespace gem5
