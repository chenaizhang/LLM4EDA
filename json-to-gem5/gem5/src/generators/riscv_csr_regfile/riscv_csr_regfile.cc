#include "generators/riscv_csr_regfile/riscv_csr_regfile.hh"

#include "base/trace.hh"
#include "debug/DUT.hh"
#include "debug/TestGenerator.hh"

namespace gem5 {

// ==================== Constructor ====================
RiscvCsrRegfile::RiscvCsrRegfile(const RiscvCsrRegfileParams &params) :
    SimObject(params),
    // Machine mode CSR initial values
    mstatus_val(params.mstatus_init),
    misa_val(0),
    medeleg_val(0),
    mideleg_val(0),
    mie_val(0),
    mtvec_val(params.mtvec_base),
    mscratch_val(0),
    mepc_val(0),
    mcause_val(0),
    mtval_val(0),
    mip_val(0),
    mcycle_val(0),
    mcycleh_val(0),
    mtimecmp_val(0xFFFFFFFF),
    mtimecmp_v2_val(0xFFFFFFFF),
    // Supervisor mode CSR initial values
    sstatus_val(0),
    sie_val(0),
    stvec_val(params.stvec_base),
    sscratch_val(0),
    sepc_val(0),
    scause_val(0),
    stval_val(0),
    satp_val(0),
    // Privilege level
    priv_lvl(params.priv_init),
    // Input registers
    ext_intr_i_reg(0),
    timer_intr_i_reg(0),
    cpu_id_i_reg(0),
    misa_i_reg(0),
    exception_i_reg(0),
    exception_pc_i_reg(0),
    exception_addr_i_reg(0),
    csr_ren_i_reg(0),
    csr_raddr_i_reg(0),
    csr_waddr_i_reg(0),
    csr_wdata_i_reg(0),
    // Output values
    csr_rdata_o_val(0),
    csr_branch_o_val(false),
    csr_target_o_val(0),
    priv_o_val(params.priv_init),
    status_o_val(params.mstatus_init),
    satp_o_val(0),
    interrupt_o_val(0)
{
    DPRINTF(DUT, "Created RiscvCsrRegfile\n");
}

// ==================== Input Set Functions ====================
void
RiscvCsrRegfile::setExtIntrI(uint32_t val)
{
    ext_intr_i_reg = val & 0x1;
}

void
RiscvCsrRegfile::setTimerIntrI(uint32_t val)
{
    timer_intr_i_reg = val & 0x1;
}

void
RiscvCsrRegfile::setCpuIdI(uint32_t val)
{
    cpu_id_i_reg = val;
}

void
RiscvCsrRegfile::setMisaI(uint32_t val)
{
    misa_i_reg = val;
}

void
RiscvCsrRegfile::setExceptionI(uint32_t val)
{
    exception_i_reg = val & 0x3F;  // 6 bits
}

void
RiscvCsrRegfile::setExceptionPcI(uint32_t val)
{
    exception_pc_i_reg = val;
}

void
RiscvCsrRegfile::setExceptionAddrI(uint32_t val)
{
    exception_addr_i_reg = val;
}

void
RiscvCsrRegfile::setCsrRenI(uint32_t val)
{
    csr_ren_i_reg = val & 0x1;
}

void
RiscvCsrRegfile::setCsrRaddrI(uint32_t val)
{
    csr_raddr_i_reg = val & 0xFFF;  // 12 bits
}

void
RiscvCsrRegfile::setCsrWaddrI(uint32_t val)
{
    csr_waddr_i_reg = val & 0xFFF;  // 12 bits
}

void
RiscvCsrRegfile::setCsrWdataI(uint32_t val)
{
    csr_wdata_i_reg = val;
}

// ==================== Output Get Functions ====================
uint32_t
RiscvCsrRegfile::getCsrRdataO()
{
    return csr_rdata_o_val;
}

bool
RiscvCsrRegfile::getCsrBranchO()
{
    return csr_branch_o_val;
}

uint32_t
RiscvCsrRegfile::getCsrTargetO()
{
    return csr_target_o_val;
}

uint32_t
RiscvCsrRegfile::getPrivO()
{
    return priv_o_val;
}

uint32_t
RiscvCsrRegfile::getStatusO()
{
    return status_o_val;
}

uint32_t
RiscvCsrRegfile::getSatpO()
{
    return satp_o_val;
}

uint32_t
RiscvCsrRegfile::getInterruptO()
{
    return interrupt_o_val;
}

// ==================== Private Helper: getSstatusFromMstatus ====================
uint32_t
RiscvCsrRegfile::getSstatusFromMstatus() const
{
    // sstatus is a subset of mstatus: only SIE, SPIE, SPP, UIE, UPIE, FS,
    // XS, MXR, SUM bits
    return mstatus_val & CSR_SSTATUS_MASK;
}

// ==================== Private Helper: setSstatusFromValue ====================
void
RiscvCsrRegfile::setSstatusFromValue(uint32_t value)
{
    // Write only the sstatus-relevant bits to mstatus
    uint32_t masked = value & CSR_SSTATUS_MASK;
    mstatus_val = (mstatus_val & ~CSR_SSTATUS_MASK) | masked;
}

// ==================== Private Helper: csrRead ====================
uint32_t
RiscvCsrRegfile::csrRead(uint32_t addr)
{
    // Machine mode registers
    if (addr == CSR_MSTATUS) {
        return mstatus_val;
    } else if (addr == CSR_MISA) {
        return misa_val;
    } else if (addr == CSR_MEDELEG) {
        return medeleg_val;
    } else if (addr == CSR_MIDELEG) {
        return mideleg_val;
    } else if (addr == CSR_MIE) {
        return mie_val;
    } else if (addr == CSR_MTVEC) {
        return mtvec_val;
    } else if (addr == CSR_MSCRATCH) {
        return mscratch_val;
    } else if (addr == CSR_MEPC) {
        return mepc_val;
    } else if (addr == CSR_MCAUSE) {
        return mcause_val;
    } else if (addr == CSR_MTVAL) {
        return mtval_val;
    } else if (addr == CSR_MIP) {
        return mip_val;
    } else if (addr == CSR_MCYCLE) {
        return mcycle_val;
    } else if (addr == CSR_MCYCLEH) {
        return mcycleh_val;
    } else if (addr == CSR_MTIMECMP) {
        return mtimecmp_val;
    } else if (addr == CSR_MTIMECMP_V2) {
        return mtimecmp_v2_val;

    // Supervisor mode registers
    } else if (addr == CSR_SSTATUS) {
        return getSstatusFromMstatus();
    } else if (addr == CSR_SIE) {
        return sie_val;
    } else if (addr == CSR_STVEC) {
        return stvec_val;
    } else if (addr == CSR_SSCRATCH) {
        return sscratch_val;
    } else if (addr == CSR_SEPC) {
        return sepc_val;
    } else if (addr == CSR_SCAUSE) {
        return scause_val;
    } else if (addr == CSR_STVAL) {
        return stval_val;
    } else if (addr == CSR_SATP) {
        return satp_val;

    // Unknown CSR address: read as 0
    } else {
        return 0;
    }
}

// ==================== Private Helper: csrWrite ====================
void
RiscvCsrRegfile::csrWrite(uint32_t addr, uint32_t data)
{
    // Machine mode registers
    if (addr == CSR_MSTATUS) {
        mstatus_val = (mstatus_val & ~CSR_MSTATUS_MASK) |
                      (data & CSR_MSTATUS_MASK);
    } else if (addr == CSR_MISA) {
        // misa is read-only
    } else if (addr == CSR_MEDELEG) {
        medeleg_val = (medeleg_val & ~CSR_MEDELEG_MASK) |
                      (data & CSR_MEDELEG_MASK);
    } else if (addr == CSR_MIDELEG) {
        mideleg_val = (mideleg_val & ~CSR_MIDELEG_MASK) |
                      (data & CSR_MIDELEG_MASK);
    } else if (addr == CSR_MIE) {
        mie_val = (mie_val & ~CSR_MIE_MASK) |
                  (data & CSR_MIE_MASK);
    } else if (addr == CSR_MTVEC) {
        mtvec_val = (mtvec_val & ~CSR_MTVEC_MASK) |
                    (data & CSR_MTVEC_MASK);
    } else if (addr == CSR_MSCRATCH) {
        mscratch_val = (mscratch_val & ~CSR_MSCRATCH_MASK) |
                       (data & CSR_MSCRATCH_MASK);
    } else if (addr == CSR_MEPC) {
        mepc_val = (mepc_val & ~CSR_MEPC_MASK) |
                   (data & CSR_MEPC_MASK);
    } else if (addr == CSR_MCAUSE) {
        mcause_val = (mcause_val & ~CSR_MCAUSE_MASK) |
                     (data & CSR_MCAUSE_MASK);
    } else if (addr == CSR_MTVAL) {
        mtval_val = (mtval_val & ~CSR_MTVAL_MASK) |
                    (data & CSR_MTVAL_MASK);
    } else if (addr == CSR_MIP) {
        // mip is read-only (set by hardware)
    } else if (addr == CSR_MCYCLE) {
        mcycle_val = data;
    } else if (addr == CSR_MCYCLEH) {
        mcycleh_val = data;
    } else if (addr == CSR_MTIMECMP) {
        mtimecmp_val = data;
    } else if (addr == CSR_MTIMECMP_V2) {
        mtimecmp_v2_val = data;

    // Supervisor mode registers
    } else if (addr == CSR_SSTATUS) {
        setSstatusFromValue(data);
    } else if (addr == CSR_SIE) {
        sie_val = (sie_val & ~CSR_SIE_MASK) |
                  (data & CSR_SIE_MASK);
    } else if (addr == CSR_STVEC) {
        stvec_val = (stvec_val & ~CSR_STVEC_MASK) |
                    (data & CSR_STVEC_MASK);
    } else if (addr == CSR_SSCRATCH) {
        sscratch_val = (sscratch_val & ~CSR_SSCRATCH_MASK) |
                       (data & CSR_SSCRATCH_MASK);
    } else if (addr == CSR_SEPC) {
        sepc_val = (sepc_val & ~CSR_SEPC_MASK) |
                   (data & CSR_SEPC_MASK);
    } else if (addr == CSR_SCAUSE) {
        scause_val = (scause_val & ~CSR_SCAUSE_MASK) |
                     (data & CSR_SCAUSE_MASK);
    } else if (addr == CSR_STVAL) {
        stval_val = (stval_val & ~CSR_STVAL_MASK) |
                    (data & CSR_STVAL_MASK);
    } else if (addr == CSR_SATP) {
        satp_val = (satp_val & ~CSR_SATP_MASK) |
                   (data & CSR_SATP_MASK);

    // Unknown CSR address: write ignored
    } else {
        // Do nothing
    }
}

// ==================== Private Helper: updateMip ====================
void
RiscvCsrRegfile::updateMip()
{
    // Clear all external/timer interrupt bits in mip
    mip_val = mip_val & ~(MIP_MEIP | MIP_MTIP);

    // Set MEIP from external interrupt input
    if (ext_intr_i_reg != 0) {
        mip_val = mip_val | MIP_MEIP;
    }

    // Set MTIP from timer interrupt input
    if (timer_intr_i_reg != 0) {
        mip_val = mip_val | MIP_MTIP;
    }
}

// ==================== Private Helper: handleException ====================
void
RiscvCsrRegfile::handleException()
{
    // exception_i (5:0):
    //   bit 5 = valid (1 = exception/interrupt pending)
    //   bit 4 = interrupt flag (1 = interrupt, 0 = exception)
    //   bits 3:0 = cause code
    uint32_t exception_valid = (exception_i_reg >> 5) & 0x1;
    if (exception_valid == 0) {
        return;
    }

    uint32_t is_interrupt = (exception_i_reg >> 4) & 0x1;
    uint32_t cause_code = exception_i_reg & 0xF;

    // Determine if this is delegatable to supervisor mode
    bool delegate_to_s = false;
    if (priv_lvl == PRIV_SUPERVISOR || priv_lvl == PRIV_USER) {
        if (is_interrupt != 0) {
            // Check mideleg
            delegate_to_s = ((mideleg_val >> cause_code) & 0x1) != 0;
        } else {
            // Check medeleg
            delegate_to_s = ((medeleg_val >> cause_code) & 0x1) != 0;
        }
    }

    if (delegate_to_s) {
        // Handle in Supervisor mode
        sepc_val = exception_pc_i_reg & CSR_SEPC_MASK;
        // Build scause: interrupt flag + cause code
        if (is_interrupt != 0) {
            scause_val = MCAUSE_INTERRUPT | cause_code;
        } else {
            scause_val = cause_code;
        }
        stval_val = exception_addr_i_reg;

        // Save previous privilege in SPP (mstatus bit 8)
        // SPP = priv_lvl bit 0 (1 for S-mode, 0 for U-mode)
        if ((priv_lvl & 0x1) != 0) {
            mstatus_val = mstatus_val | (1 << 8);  // SPP = 1
        } else {
            mstatus_val = mstatus_val & ~(1 << 8);  // SPP = 0
        }

        // Save SIE in SPIE (mstatus bit 3)
        uint32_t current_sie = (mstatus_val >> 0) & 0x1;
        if (current_sie != 0) {
            mstatus_val = mstatus_val | (1 << 3);  // SPIE = 1
        } else {
            mstatus_val = mstatus_val & ~(1 << 3);  // SPIE = 0
        }

        // Disable SIE
        mstatus_val = mstatus_val & ~(1 << 0);  // SIE = 0

        // Enter Supervisor mode
        priv_lvl = PRIV_SUPERVISOR;

        // Branch to stvec
        csr_branch_o_val = true;
        csr_target_o_val = stvec_val & 0xFFFFFFFC;
    } else {
        // Handle in Machine mode
        mepc_val = exception_pc_i_reg & CSR_MEPC_MASK;
        // Build mcause: interrupt flag + cause code
        if (is_interrupt != 0) {
            mcause_val = MCAUSE_INTERRUPT | cause_code;
        } else {
            mcause_val = cause_code;
        }
        mtval_val = exception_addr_i_reg;

        // Save previous privilege in MPP (mstatus bits 6:5)
        mstatus_val = (mstatus_val & ~0x60) | ((priv_lvl & 0x3) << 5);

        // Save MIE in MPIE (mstatus bit 7)
        uint32_t current_mie = (mstatus_val >> 1) & 0x1;
        if (current_mie != 0) {
            mstatus_val = mstatus_val | (1 << 7);  // MPIE = 1
        } else {
            mstatus_val = mstatus_val & ~(1 << 7);  // MPIE = 0
        }

        // Disable MIE
        mstatus_val = mstatus_val & ~(1 << 1);  // MIE = 0

        // Enter Machine mode
        priv_lvl = PRIV_MACHINE;

        // Branch to mtvec
        csr_branch_o_val = true;
        csr_target_o_val = mtvec_val & 0xFFFFFFFC;
    }
}

// ==================== Private Helper: checkInterrupts ====================
void
RiscvCsrRegfile::checkInterrupts()
{
    // Compute pending and enabled interrupts
    uint32_t pending = mip_val & mie_val;

    // Build interrupt_o: all pending interrupts (raw mip & mie)
    interrupt_o_val = pending;

    // Check if any interrupt can be taken based on privilege and MIE/SIE
    bool take_interrupt = false;

    // In Machine mode, need MIE=1 to take interrupts
    // In Supervisor mode, need SIE=1 to take interrupts
    // In User mode, need SIE=1 (delegated) or MIE=1 (non-delegated)
    if (priv_lvl == PRIV_MACHINE) {
        uint32_t mie = (mstatus_val >> 1) & 0x1;
        if (mie != 0 && pending != 0) {
            take_interrupt = true;
        }
    } else {
        uint32_t sie = mstatus_val & 0x1;
        if (sie != 0 && pending != 0) {
            // Check if any interrupt not delegated to S-mode
            // Actually, in S or U mode, non-delegated interrupts (machine
            // level) are taken regardless of SIE, they are "always on" at
            // machine level. But delegated ones (S-level) need SIE=1.
            // For simplicity, if we're not in M-mode and SIE=1, take any
            // pending interrupt.
            take_interrupt = true;
        }

        // Even when SIE=0, machine-level interrupts (MEI, MSI, MTI) are
        // always taken
        uint32_t m_level_intr = pending & (MIP_MEIP | MIP_MSIP | MIP_MTIP);
        if (m_level_intr != 0) {
            take_interrupt = true;
        }
    }

    if (take_interrupt) {
        // Find highest priority pending interrupt
        // Priority: MEI > MSI > MTI > SEI > SSI > STI (machine then
        // supervisor)
        uint32_t cause_code = 0;
        bool is_interrupt = true;

        if ((pending & MIP_MEIP) != 0) {
            cause_code = 11;
        } else if ((pending & MIP_MSIP) != 0) {
            cause_code = 3;
        } else if ((pending & MIP_MTIP) != 0) {
            cause_code = 7;
        } else if ((pending & MIP_SEIP) != 0) {
            cause_code = 9;
        } else if ((pending & MIP_SSIP) != 0) {
            cause_code = 1;
        } else if ((pending & MIP_STIP) != 0) {
            cause_code = 5;
        } else {
            // No recognized interrupt pending
            return;
        }

        // Determine target mode (machine or supervisor)
        bool delegate_to_s = false;
        if (priv_lvl == PRIV_SUPERVISOR || priv_lvl == PRIV_USER) {
            delegate_to_s = ((mideleg_val >> cause_code) & 0x1) != 0;
        }

        if (delegate_to_s) {
            // Delegate to S-mode
            sepc_val = exception_pc_i_reg & CSR_SEPC_MASK;
            scause_val = MCAUSE_INTERRUPT | cause_code;
            stval_val = 0;

            // Save SPP and SPIE
            if ((priv_lvl & 0x1) != 0) {
                mstatus_val = mstatus_val | (1 << 8);
            } else {
                mstatus_val = mstatus_val & ~(1 << 8);
            }

            uint32_t current_sie = mstatus_val & 0x1;
            if (current_sie != 0) {
                mstatus_val = mstatus_val | (1 << 3);
            } else {
                mstatus_val = mstatus_val & ~(1 << 3);
            }

            // Disable SIE
            mstatus_val = mstatus_val & ~(1 << 0);

            priv_lvl = PRIV_SUPERVISOR;
            csr_branch_o_val = true;
            csr_target_o_val = stvec_val & 0xFFFFFFFC;
        } else {
            // Handle in M-mode
            mepc_val = exception_pc_i_reg & CSR_MEPC_MASK;
            mcause_val = MCAUSE_INTERRUPT | cause_code;
            mtval_val = 0;

            // Save MPP and MPIE
            mstatus_val = (mstatus_val & ~0x60) | ((priv_lvl & 0x3) << 5);

            uint32_t current_mie = (mstatus_val >> 1) & 0x1;
            if (current_mie != 0) {
                mstatus_val = mstatus_val | (1 << 7);
            } else {
                mstatus_val = mstatus_val & ~(1 << 7);
            }

            // Disable MIE
            mstatus_val = mstatus_val & ~(1 << 1);

            priv_lvl = PRIV_MACHINE;
            csr_branch_o_val = true;
            csr_target_o_val = mtvec_val & 0xFFFFFFFC;
        }
    }
}

// ==================== Process Function ====================
void
RiscvCsrRegfile::process()
{
    // Clear branch output at start of each cycle
    csr_branch_o_val = false;

    // Step 1: Update misa from input
    misa_val = misa_i_reg;

    // Step 2: Update mip from external interrupt lines
    updateMip();

    // Step 3: Increment cycle counter
    mcycle_val = mcycle_val + 1;
    if (mcycle_val == 0) {
        // mcycle wrapped; increment mcycleh
        mcycleh_val = mcycleh_val + 1;
    }

    // Step 4: Handle exception (if exception_i is valid)
    // Exception handling has priority over normal CSR writes
    handleException();

    // Step 5: Handle CSR write (only if no exception was taken)
    if (csr_branch_o_val == false) {
        // Normal CSR write operation
        // CSR write happens when csr_waddr_i != 0 or similar
        // For RISC-V, CSRRW/CSRRS/CSRRC instructions specify the address,
        // and a write occurs regardless of the address value. We use the
        // write enable signal implicitly: if the instruction specifies a
        // write, the address will be non-zero for most cases, but actually
        // CSR writes can target address 0 in some cases.
        // The description states csr_waddr_i is the write address.
        // We'll write whenever csr_waddr_i is a valid CSR address.
        if (csr_waddr_i_reg != 0) {
            csrWrite(csr_waddr_i_reg, csr_wdata_i_reg);
        }
    }

    // Step 6: Handle CSR read
    if (csr_ren_i_reg != 0) {
        csr_rdata_o_val = csrRead(csr_raddr_i_reg);
    } else {
        csr_rdata_o_val = 0;
    }

    // Step 7: Check for interrupt requests
    checkInterrupts();

    // Step 8: Set output values
    priv_o_val = priv_lvl;
    status_o_val = mstatus_val;
    satp_o_val = satp_val;
}

} // namespace gem5
