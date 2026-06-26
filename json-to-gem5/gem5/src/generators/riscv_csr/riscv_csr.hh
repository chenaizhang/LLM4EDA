#ifndef __GENERATORS_RISCV_CSR_HH__
#define __GENERATORS_RISCV_CSR_HH__

#include <cstdint>

#include "generators/riscv_csr_regfile/riscv_csr_regfile.hh"
#include "params/RiscvCsr.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvCsr : public SimObject
{
  private:
    // ==================== Input Port Registers ====================
    // opcode bundle (from decode stage)
    uint32_t opcode_valid_i_reg;
    uint32_t opcode_opcode_i_reg;
    uint32_t opcode_pc_i_reg;
    uint32_t opcode_invalid_i_reg;
    uint32_t opcode_rd_idx_i_reg;
    uint32_t opcode_ra_idx_i_reg;
    uint32_t opcode_rb_idx_i_reg;
    uint32_t opcode_ra_operand_i_reg;
    uint32_t opcode_rb_operand_i_reg;

    // CSR writeback (from writeback stage)
    uint32_t csr_writeback_write_i_reg;
    uint32_t csr_writeback_waddr_i_reg;
    uint32_t csr_writeback_wdata_i_reg;
    uint32_t csr_writeback_exception_i_reg;
    uint32_t csr_writeback_exception_pc_i_reg;
    uint32_t csr_writeback_exception_addr_i_reg;

    // Control inputs
    uint32_t cpu_id_i_reg;
    uint32_t reset_vector_i_reg;
    uint32_t intr_i_reg;
    uint32_t interrupt_inhibit_i_reg;

    // ==================== Output Port Values ====================
    uint32_t csr_result_e1_value_o_val;
    uint32_t csr_result_e1_write_o_val;
    uint32_t csr_result_e1_wdata_o_val;
    uint32_t csr_result_e1_exception_o_val;
    uint32_t branch_csr_request_o_val;
    uint32_t branch_csr_pc_o_val;
    uint32_t branch_csr_priv_o_val;
    uint32_t take_interrupt_o_val;
    uint32_t ifence_o_val;
    uint32_t mmu_priv_d_o_val;
    uint32_t mmu_sum_o_val;
    uint32_t mmu_mxr_o_val;
    uint32_t mmu_flush_o_val;
    uint32_t mmu_satp_o_val;

    // ==================== Submodule Reference ====================
    RiscvCsrRegfile &csrfile;

    // ==================== Internal State ====================
    /** Previous SATP value for detecting TLB flush on satp change. */
    uint32_t prev_satp_val;

  public:
    RiscvCsr(const RiscvCsrParams &p);

    // ==================== Input Set Functions ====================
    void setOpcodeValidI(uint32_t val);
    void setOpcodeOpcodeI(uint32_t val);
    void setOpcodePcI(uint32_t val);
    void setOpcodeInvalidI(uint32_t val);
    void setOpcodeRdIdxI(uint32_t val);
    void setOpcodeRaIdxI(uint32_t val);
    void setOpcodeRbIdxI(uint32_t val);
    void setOpcodeRaOperandI(uint32_t val);
    void setOpcodeRbOperandI(uint32_t val);
    void setCsrWritebackWriteI(uint32_t val);
    void setCsrWritebackWaddrI(uint32_t val);
    void setCsrWritebackWdataI(uint32_t val);
    void setCsrWritebackExceptionI(uint32_t val);
    void setCsrWritebackExceptionPcI(uint32_t val);
    void setCsrWritebackExceptionAddrI(uint32_t val);
    void setCpuIdI(uint32_t val);
    void setResetVectorI(uint32_t val);
    void setIntrI(uint32_t val);
    void setInterruptInhibitI(uint32_t val);

    // ==================== Output Get Functions ====================
    uint32_t getCsrResultE1ValueO();
    uint32_t getCsrResultE1WriteO();
    uint32_t getCsrResultE1WdataO();
    uint32_t getCsrResultE1ExceptionO();
    uint32_t getBranchCsrRequestO();
    uint32_t getBranchCsrPcO();
    uint32_t getBranchCsrPrivO();
    uint32_t getTakeInterruptO();
    uint32_t getIfenceO();
    uint32_t getMmuPrivDO();
    uint32_t getMmuSumO();
    uint32_t getMmuMxrO();
    uint32_t getMmuFlushO();
    uint32_t getMmuSatpO();

    // ==================== Process Function ====================
    /** Called by parent module every cycle. */
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_CSR_HH__
