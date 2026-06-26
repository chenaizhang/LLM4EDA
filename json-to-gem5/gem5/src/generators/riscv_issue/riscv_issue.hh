#ifndef __GENERATORS_RISCV_ISSUE_HH__
#define __GENERATORS_RISCV_ISSUE_HH__

#include <cstdint>

#include "generators/riscv_regfile/riscv_regfile.hh"
#include "generators/riscv_xilinx_2r1w/riscv_xilinx_2r1w.hh"
#include "params/RiscvIssue.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvIssue : public SimObject
{
  private:
    /** Submodule references */
    RiscvRegfile& regfile;
    RiscvXilinx2r1w* xilinx_2r1w;

    /** Parameter: support dual issue */
    bool supportDualIssue;

    // ---- Input registers (latched by set functions) ----

    /** Fetch inputs */
    uint8_t fetch_valid_i_reg;
    uint32_t fetch_instr_i_reg;
    uint32_t fetch_pc_i_reg;
    uint8_t fetch_fault_fetch_i_reg;
    uint8_t fetch_fault_page_i_reg;
    uint8_t fetch_instr_exec_i_reg;
    uint8_t fetch_instr_lsu_i_reg;
    uint8_t fetch_instr_branch_i_reg;
    uint8_t fetch_instr_mul_i_reg;
    uint8_t fetch_instr_div_i_reg;
    uint8_t fetch_instr_csr_i_reg;
    uint8_t fetch_instr_rd_valid_i_reg;
    uint8_t fetch_instr_invalid_i_reg;

    /** Branch inputs */
    uint8_t branch_exec_request_i_reg;
    uint8_t branch_exec_is_taken_i_reg;
    uint8_t branch_exec_is_not_taken_i_reg;
    uint8_t branch_exec_source_i_reg;
    uint8_t branch_exec_is_call_i_reg;
    uint8_t branch_exec_is_ret_i_reg;
    uint8_t branch_exec_is_jmp_i_reg;
    uint32_t branch_exec_pc_i_reg;
    uint8_t branch_d_exec_request_i_reg;
    uint32_t branch_d_exec_pc_i_reg;
    uint8_t branch_d_exec_priv_i_reg;
    uint8_t branch_csr_request_i_reg;
    uint32_t branch_csr_pc_i_reg;
    uint8_t branch_csr_priv_i_reg;

    /** Writeback inputs */
    uint32_t writeback_exec_value_i_reg;
    uint8_t writeback_mem_valid_i_reg;
    uint32_t writeback_mem_value_i_reg;
    uint8_t writeback_mem_exception_i_reg;
    uint32_t writeback_mul_value_i_reg;
    uint8_t writeback_div_valid_i_reg;
    uint32_t writeback_div_value_i_reg;

    /** CSR inputs */
    uint32_t csr_result_e1_value_i_reg;
    uint8_t csr_result_e1_write_i_reg;
    uint32_t csr_result_e1_wdata_i_reg;
    uint8_t csr_result_e1_exception_i_reg;

    /** Control inputs */
    uint8_t lsu_stall_i_reg;
    uint8_t take_interrupt_i_reg;

    // ---- Output values (computed by process, read by get functions) ----

    /** Fetch interface outputs */
    uint8_t fetch_accept_o_val;

    /** Branch outputs */
    uint8_t branch_request_o_val;
    uint32_t branch_pc_o_val;
    uint8_t branch_priv_o_val;

    /** Execution unit valid outputs */
    uint8_t exec_opcode_valid_o_val;
    uint8_t lsu_opcode_valid_o_val;
    uint8_t csr_opcode_valid_o_val;
    uint8_t mul_opcode_valid_o_val;
    uint8_t div_opcode_valid_o_val;

    /** Generic opcode outputs (shared datapath) */
    uint32_t opcode_opcode_o_val;
    uint32_t opcode_pc_o_val;
    uint8_t opcode_invalid_o_val;
    uint8_t opcode_rd_idx_o_val;
    uint8_t opcode_ra_idx_o_val;
    uint8_t opcode_rb_idx_o_val;
    uint32_t opcode_ra_operand_o_val;
    uint32_t opcode_rb_operand_o_val;

    /** LSU opcode outputs */
    uint32_t lsu_opcode_opcode_o_val;
    uint32_t lsu_opcode_pc_o_val;
    uint8_t lsu_opcode_invalid_o_val;
    uint8_t lsu_opcode_rd_idx_o_val;
    uint8_t lsu_opcode_ra_idx_o_val;
    uint8_t lsu_opcode_rb_idx_o_val;
    uint32_t lsu_opcode_ra_operand_o_val;
    uint32_t lsu_opcode_rb_operand_o_val;

    /** MUL opcode outputs */
    uint32_t mul_opcode_opcode_o_val;
    uint32_t mul_opcode_pc_o_val;
    uint8_t mul_opcode_invalid_o_val;
    uint8_t mul_opcode_rd_idx_o_val;
    uint8_t mul_opcode_ra_idx_o_val;
    uint8_t mul_opcode_rb_idx_o_val;
    uint32_t mul_opcode_ra_operand_o_val;
    uint32_t mul_opcode_rb_operand_o_val;

    /** CSR opcode outputs */
    uint32_t csr_opcode_opcode_o_val;
    uint32_t csr_opcode_pc_o_val;
    uint8_t csr_opcode_invalid_o_val;
    uint8_t csr_opcode_rd_idx_o_val;
    uint8_t csr_opcode_ra_idx_o_val;
    uint8_t csr_opcode_rb_idx_o_val;
    uint32_t csr_opcode_ra_operand_o_val;
    uint32_t csr_opcode_rb_operand_o_val;

    /** CSR writeback outputs */
    uint8_t csr_writeback_write_o_val;
    uint16_t csr_writeback_waddr_o_val;
    uint32_t csr_writeback_wdata_o_val;
    uint8_t csr_writeback_exception_o_val;
    uint32_t csr_writeback_exception_pc_o_val;
    uint32_t csr_writeback_exception_addr_o_val;

    /** Pipeline hold outputs */
    uint8_t exec_hold_o_val;
    uint8_t mul_hold_o_val;
    uint8_t interrupt_inhibit_o_val;

    // ---- Internal pipeline state registers ----

    /** In-flight tracking for bypass (destination register index per unit) */
    uint8_t exec_rd_idx_reg;
    uint8_t mem_rd_idx_reg;
    uint8_t mul_rd_idx_reg;
    uint8_t div_rd_idx_reg;

    /** In-flight valid flags */
    uint8_t exec_in_flight_reg;
    uint8_t mem_in_flight_reg;
    uint8_t mul_in_flight_reg;
    uint8_t div_in_flight_reg;

    /** Interrupt handling state */
    uint8_t interrupt_inhibit_reg;

  public:
    RiscvIssue(const RiscvIssueParams &p);

    // ---- Input set functions ----

    /** Fetch input set functions */
    void setFetchValidI(uint8_t val);
    void setFetchInstrI(uint32_t val);
    void setFetchPcI(uint32_t val);
    void setFetchFaultFetchI(uint8_t val);
    void setFetchFaultPageI(uint8_t val);
    void setFetchInstrExecI(uint8_t val);
    void setFetchInstrLsuI(uint8_t val);
    void setFetchInstrBranchI(uint8_t val);
    void setFetchInstrMulI(uint8_t val);
    void setFetchInstrDivI(uint8_t val);
    void setFetchInstrCsrI(uint8_t val);
    void setFetchInstrRdValidI(uint8_t val);
    void setFetchInstrInvalidI(uint8_t val);

    /** Branch input set functions */
    void setBranchExecRequestI(uint8_t val);
    void setBranchExecIsTakenI(uint8_t val);
    void setBranchExecIsNotTakenI(uint8_t val);
    void setBranchExecSourceI(uint8_t val);
    void setBranchExecIsCallI(uint8_t val);
    void setBranchExecIsRetI(uint8_t val);
    void setBranchExecIsJmpI(uint8_t val);
    void setBranchExecPcI(uint32_t val);
    void setBranchDExecRequestI(uint8_t val);
    void setBranchDExecPcI(uint32_t val);
    void setBranchDExecPrivI(uint8_t val);
    void setBranchCsrRequestI(uint8_t val);
    void setBranchCsrPcI(uint32_t val);
    void setBranchCsrPrivI(uint8_t val);

    /** Writeback input set functions */
    void setWritebackExecValueI(uint32_t val);
    void setWritebackMemValidI(uint8_t val);
    void setWritebackMemValueI(uint32_t val);
    void setWritebackMemExceptionI(uint8_t val);
    void setWritebackMulValueI(uint32_t val);
    void setWritebackDivValidI(uint8_t val);
    void setWritebackDivValueI(uint32_t val);

    /** CSR input set functions */
    void setCsrResultE1ValueI(uint32_t val);
    void setCsrResultE1WriteI(uint8_t val);
    void setCsrResultE1WdataI(uint32_t val);
    void setCsrResultE1ExceptionI(uint8_t val);

    /** Control input set functions */
    void setLsuStallI(uint8_t val);
    void setTakeInterruptI(uint8_t val);

    // ---- Output get functions ----

    /** Fetch interface get functions */
    uint8_t getFetchAcceptO();

    /** Branch output get functions */
    uint8_t getBranchRequestO();
    uint32_t getBranchPcO();
    uint8_t getBranchPrivO();

    /** Execution unit valid get functions */
    uint8_t getExecOpcodeValidO();
    uint8_t getLsuOpcodeValidO();
    uint8_t getCsrOpcodeValidO();
    uint8_t getMulOpcodeValidO();
    uint8_t getDivOpcodeValidO();

    /** Generic opcode get functions */
    uint32_t getOpcodeOpcodeO();
    uint32_t getOpcodePcO();
    uint8_t getOpcodeInvalidO();
    uint8_t getOpcodeRdIdxO();
    uint8_t getOpcodeRaIdxO();
    uint8_t getOpcodeRbIdxO();
    uint32_t getOpcodeRaOperandO();
    uint32_t getOpcodeRbOperandO();

    /** LSU opcode get functions */
    uint32_t getLsuOpcodeOpcodeO();
    uint32_t getLsuOpcodePcO();
    uint8_t getLsuOpcodeInvalidO();
    uint8_t getLsuOpcodeRdIdxO();
    uint8_t getLsuOpcodeRaIdxO();
    uint8_t getLsuOpcodeRbIdxO();
    uint32_t getLsuOpcodeRaOperandO();
    uint32_t getLsuOpcodeRbOperandO();

    /** MUL opcode get functions */
    uint32_t getMulOpcodeOpcodeO();
    uint32_t getMulOpcodePcO();
    uint8_t getMulOpcodeInvalidO();
    uint8_t getMulOpcodeRdIdxO();
    uint8_t getMulOpcodeRaIdxO();
    uint8_t getMulOpcodeRbIdxO();
    uint32_t getMulOpcodeRaOperandO();
    uint32_t getMulOpcodeRbOperandO();

    /** CSR opcode get functions */
    uint32_t getCsrOpcodeOpcodeO();
    uint32_t getCsrOpcodePcO();
    uint8_t getCsrOpcodeInvalidO();
    uint8_t getCsrOpcodeRdIdxO();
    uint8_t getCsrOpcodeRaIdxO();
    uint8_t getCsrOpcodeRbIdxO();
    uint32_t getCsrOpcodeRaOperandO();
    uint32_t getCsrOpcodeRbOperandO();

    /** CSR writeback get functions */
    uint8_t getCsrWritebackWriteO();
    uint16_t getCsrWritebackWaddrO();
    uint32_t getCsrWritebackWdataO();
    uint8_t getCsrWritebackExceptionO();
    uint32_t getCsrWritebackExceptionPcO();
    uint32_t getCsrWritebackExceptionAddrO();

    /** Pipeline hold get functions */
    uint8_t getExecHoldO();
    uint8_t getMulHoldO();
    uint8_t getInterruptInhibitO();

    /**
     * Process function.
     * Called by parent module each cycle.
     * Performs instruction dispatch, register file access,
     * bypass logic, writeback merging, and branch handling.
     */
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_ISSUE_HH__
