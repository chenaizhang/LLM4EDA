#ifndef __GENERATORS_RISCV_CSR_REGFILE_HH__
#define __GENERATORS_RISCV_CSR_REGFILE_HH__

#include "params/RiscvCsrRegfile.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvCsrRegfile : public SimObject
{
  private:
    // ==================== CSR Address Constants ====================
    // Machine mode registers
    static const uint32_t CSR_MSTATUS    = 0x300;
    static const uint32_t CSR_MISA       = 0x301;
    static const uint32_t CSR_MEDELEG    = 0x302;
    static const uint32_t CSR_MIDELEG    = 0x303;
    static const uint32_t CSR_MIE        = 0x304;
    static const uint32_t CSR_MTVEC      = 0x305;
    static const uint32_t CSR_MSCRATCH   = 0x340;
    static const uint32_t CSR_MEPC       = 0x341;
    static const uint32_t CSR_MCAUSE     = 0x342;
    static const uint32_t CSR_MTVAL      = 0x343;
    static const uint32_t CSR_MIP        = 0x344;
    static const uint32_t CSR_MCYCLE     = 0xB00;
    static const uint32_t CSR_MCYCLEH    = 0xB80;
    static const uint32_t CSR_MTIMECMP   = 0x7C0;
    static const uint32_t CSR_MTIMECMP_V2 = 0x7C1;

    // Supervisor mode registers
    static const uint32_t CSR_SSTATUS    = 0x100;
    static const uint32_t CSR_SIE        = 0x104;
    static const uint32_t CSR_STVEC      = 0x105;
    static const uint32_t CSR_SSCRATCH   = 0x140;
    static const uint32_t CSR_SEPC       = 0x141;
    static const uint32_t CSR_SCAUSE     = 0x142;
    static const uint32_t CSR_STVAL      = 0x143;
    static const uint32_t CSR_SATP       = 0x180;

    // ==================== CSR Mask Constants ====================
    // mstatus writable bits (RV32): SIE, MIE, SPIE, MPP[1:0], MPIE, SPP,
    // FS[1:0], XS[1:0], MXR, SUM, TVM, TW, TSR
    static const uint32_t CSR_MSTATUS_MASK  = 0x00FF88FF;
    // misa is read-only
    static const uint32_t CSR_MISA_MASK     = 0x00000000;
    static const uint32_t CSR_MEDELEG_MASK  = 0x0000FFFF;
    static const uint32_t CSR_MIDELEG_MASK  = 0x00000AAA;
    static const uint32_t CSR_MIE_MASK      = 0x00000AAA;
    static const uint32_t CSR_MTVEC_MASK    = 0xFFFFFFFD;
    static const uint32_t CSR_MSCRATCH_MASK = 0xFFFFFFFF;
    static const uint32_t CSR_MEPC_MASK     = 0xFFFFFFFC;
    static const uint32_t CSR_MCAUSE_MASK   = 0x8000001F;
    static const uint32_t CSR_MTVAL_MASK    = 0xFFFFFFFF;
    // mip is read-only (set by hardware)
    static const uint32_t CSR_MIP_MASK      = 0x00000000;
    static const uint32_t CSR_MCYCLE_MASK   = 0xFFFFFFFF;
    static const uint32_t CSR_MCYCLEH_MASK  = 0xFFFFFFFF;
    static const uint32_t CSR_MTIMECMP_MASK    = 0xFFFFFFFF;
    static const uint32_t CSR_MTIMECMP_V2_MASK = 0xFFFFFFFF;

    // sstatus is a subset of mstatus
    static const uint32_t CSR_SSTATUS_MASK  = 0x0000010D;
    static const uint32_t CSR_SIE_MASK      = 0x00000222;
    static const uint32_t CSR_STVEC_MASK    = 0xFFFFFFFD;
    static const uint32_t CSR_SSCRATCH_MASK = 0xFFFFFFFF;
    static const uint32_t CSR_SEPC_MASK     = 0xFFFFFFFC;
    static const uint32_t CSR_SCAUSE_MASK   = 0x8000001F;
    static const uint32_t CSR_STVAL_MASK    = 0xFFFFFFFF;
    static const uint32_t CSR_SATP_MASK     = 0xFFFFFFFF;

    // ==================== mip/mie bit positions ====================
    static const uint32_t MIP_SSIP  = (1 << 1);
    static const uint32_t MIP_MSIP  = (1 << 3);
    static const uint32_t MIP_STIP  = (1 << 5);
    static const uint32_t MIP_MTIP  = (1 << 7);
    static const uint32_t MIP_SEIP  = (1 << 9);
    static const uint32_t MIP_MEIP  = (1 << 11);

    // ==================== Privilege Levels ====================
    static const uint32_t PRIV_USER       = 0;
    static const uint32_t PRIV_SUPERVISOR = 1;
    static const uint32_t PRIV_MACHINE    = 3;

    // ==================== mcause bit definitions ====================
    // bit 31: interrupt flag
    static const uint32_t MCAUSE_INTERRUPT = (1 << 31);

    // ==================== CSR Register State ====================
    // Machine mode
    uint32_t mstatus_val;
    uint32_t misa_val;
    uint32_t medeleg_val;
    uint32_t mideleg_val;
    uint32_t mie_val;
    uint32_t mtvec_val;
    uint32_t mscratch_val;
    uint32_t mepc_val;
    uint32_t mcause_val;
    uint32_t mtval_val;
    uint32_t mip_val;
    uint32_t mcycle_val;
    uint32_t mcycleh_val;
    uint32_t mtimecmp_val;
    uint32_t mtimecmp_v2_val;

    // Supervisor mode
    uint32_t sstatus_val;
    uint32_t sie_val;
    uint32_t stvec_val;
    uint32_t sscratch_val;
    uint32_t sepc_val;
    uint32_t scause_val;
    uint32_t stval_val;
    uint32_t satp_val;

    // Current privilege level
    uint32_t priv_lvl;

    // ==================== Input Port Registers ====================
    uint32_t ext_intr_i_reg;
    uint32_t timer_intr_i_reg;
    uint32_t cpu_id_i_reg;
    uint32_t misa_i_reg;
    uint32_t exception_i_reg;
    uint32_t exception_pc_i_reg;
    uint32_t exception_addr_i_reg;
    uint32_t csr_ren_i_reg;
    uint32_t csr_raddr_i_reg;
    uint32_t csr_waddr_i_reg;
    uint32_t csr_wdata_i_reg;

    // ==================== Output Port Values ====================
    uint32_t csr_rdata_o_val;
    bool     csr_branch_o_val;
    uint32_t csr_target_o_val;
    uint32_t priv_o_val;
    uint32_t status_o_val;
    uint32_t satp_o_val;
    uint32_t interrupt_o_val;

    // ==================== Private Helper Functions ====================
    /** Read CSR register by address. */
    uint32_t csrRead(uint32_t addr);

    /** Write CSR register by address with masking. */
    void csrWrite(uint32_t addr, uint32_t data);

    /** Handle incoming exception/interrupt from exception_i signal. */
    void handleException();

    /** Update mip based on external interrupt inputs. */
    void updateMip();

    /** Check for pending interrupts and set csr_branch_o if needed. */
    void checkInterrupts();

    /** Extract sstatus fields from mstatus. */
    uint32_t getSstatusFromMstatus() const;

    /** Write sstatus fields into mstatus. */
    void setSstatusFromValue(uint32_t value);

  public:
    RiscvCsrRegfile(const RiscvCsrRegfileParams &p);

    // ==================== Input Set Functions ====================
    void setExtIntrI(uint32_t val);
    void setTimerIntrI(uint32_t val);
    void setCpuIdI(uint32_t val);
    void setMisaI(uint32_t val);
    void setExceptionI(uint32_t val);
    void setExceptionPcI(uint32_t val);
    void setExceptionAddrI(uint32_t val);
    void setCsrRenI(uint32_t val);
    void setCsrRaddrI(uint32_t val);
    void setCsrWaddrI(uint32_t val);
    void setCsrWdataI(uint32_t val);

    // ==================== Output Get Functions ====================
    uint32_t getCsrRdataO();
    bool     getCsrBranchO();
    uint32_t getCsrTargetO();
    uint32_t getPrivO();
    uint32_t getStatusO();
    uint32_t getSatpO();
    uint32_t getInterruptO();

    // ==================== Process Function ====================
    /** Called by parent (riscv_csr) every cycle. */
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_CSR_REGFILE_HH__
