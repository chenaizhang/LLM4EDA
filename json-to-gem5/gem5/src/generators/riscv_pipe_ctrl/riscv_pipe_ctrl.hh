#ifndef __GENERATORS_RISCV_PIPE_CTRL_HH__
#define __GENERATORS_RISCV_PIPE_CTRL_HH__

#include "params/RiscvPipeCtrl.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvPipeCtrl : public SimObject
{
  private:
    // ==================== Input port registers ====================
    // Issue stage inputs
    bool issue_valid_i_reg;
    bool issue_accept_i_reg;
    bool issue_stall_i_reg;
    bool issue_lsu_i_reg;
    bool issue_csr_i_reg;
    bool issue_div_i_reg;
    bool issue_mul_i_reg;
    bool issue_branch_i_reg;
    bool issue_rd_valid_i_reg;
    uint8_t issue_rd_i_reg;
    uint8_t issue_exception_i_reg;
    bool take_interrupt_i_reg;
    bool issue_branch_taken_i_reg;
    uint32_t issue_branch_target_i_reg;
    uint32_t issue_pc_i_reg;
    uint32_t issue_opcode_i_reg;
    uint32_t issue_operand_ra_i_reg;
    uint32_t issue_operand_rb_i_reg;

    // E1 execution result inputs
    uint32_t alu_result_e1_i_reg;
    bool csr_result_write_e1_i_reg;
    uint32_t csr_result_value_e1_i_reg;
    uint32_t csr_result_wdata_e1_i_reg;
    uint8_t csr_result_exception_e1_i_reg;

    // E2 result inputs
    bool mem_complete_i_reg;
    uint32_t mem_result_e2_i_reg;
    uint8_t mem_exception_e2_i_reg;
    uint32_t mul_result_e2_i_reg;
    bool div_complete_i_reg;
    uint32_t div_result_i_reg;

    // Flush inputs
    bool squash_e1_e2_i_reg;
    bool squash_wb_i_reg;

    // ==================== Output port registers ====================
    // E1 outputs
    bool load_e1_o_val;
    bool store_e1_o_val;
    bool mul_e1_o_val;
    bool branch_e1_o_val;
    uint8_t rd_e1_o_val;
    uint32_t pc_e1_o_val;
    uint32_t opcode_e1_o_val;
    uint32_t operand_ra_e1_o_val;
    uint32_t operand_rb_e1_o_val;

    // E2 outputs
    bool load_e2_o_val;
    bool mul_e2_o_val;
    uint8_t rd_e2_o_val;
    uint32_t result_e2_o_val;

    // WB outputs
    bool valid_wb_o_val;
    bool csr_wb_o_val;
    uint8_t rd_wb_o_val;
    uint32_t result_wb_o_val;
    uint32_t pc_wb_o_val;
    uint32_t opcode_wb_o_val;
    uint32_t operand_ra_wb_o_val;
    uint32_t operand_rb_wb_o_val;
    uint8_t exception_wb_o_val;
    bool csr_write_wb_o_val;
    uint16_t csr_waddr_wb_o_val;
    uint32_t csr_wdata_wb_o_val;

    // Control outputs
    bool stall_o_val;
    bool squash_e1_e2_o_val;

    // ==================== Pipeline state registers ====================
    // E1 pipeline registers (between Issue and E1)
    bool e1_valid_reg;
    bool e1_load_reg;
    bool e1_store_reg;
    bool e1_mul_reg;
    bool e1_branch_reg;
    uint8_t e1_rd_reg;
    uint32_t e1_pc_reg;
    uint32_t e1_opcode_reg;
    uint32_t e1_operand_ra_reg;
    uint32_t e1_operand_rb_reg;

    // E2 pipeline registers (between E1 and WB)
    bool e2_valid_reg;
    bool e2_load_reg;
    bool e2_mul_reg;
    uint8_t e2_rd_reg;
    uint32_t e2_result_reg;
    uint32_t e2_pc_reg;
    uint32_t e2_opcode_reg;
    uint32_t e2_operand_ra_reg;
    uint32_t e2_operand_rb_reg;
    uint8_t e2_exception_reg;
    bool e2_csr_reg;
    bool e2_csr_write_reg;
    uint32_t e2_csr_wdata_reg;
    uint16_t e2_csr_waddr_reg;

  public:
    RiscvPipeCtrl(const RiscvPipeCtrlParams &p);

    // ==================== Set functions for input ports ====================
    // Issue stage inputs
    void setIssueValidI(bool val);
    void setIssueAcceptI(bool val);
    void setIssueStallI(bool val);
    void setIssueLsuI(bool val);
    void setIssueCsrI(bool val);
    void setIssueDivI(bool val);
    void setIssueMulI(bool val);
    void setIssueBranchI(bool val);
    void setIssueRdValidI(bool val);
    void setIssueRdI(uint8_t val);
    void setIssueExceptionI(uint8_t val);
    void setTakeInterruptI(bool val);
    void setIssueBranchTakenI(bool val);
    void setIssueBranchTargetI(uint32_t val);
    void setIssuePcI(uint32_t val);
    void setIssueOpcodeI(uint32_t val);
    void setIssueOperandRaI(uint32_t val);
    void setIssueOperandRbI(uint32_t val);

    // E1 execution result inputs
    void setAluResultE1I(uint32_t val);
    void setCsrResultWriteE1I(bool val);
    void setCsrResultValueE1I(uint32_t val);
    void setCsrResultWdataE1I(uint32_t val);
    void setCsrResultExceptionE1I(uint8_t val);

    // E2 result inputs
    void setMemCompleteI(bool val);
    void setMemResultE2I(uint32_t val);
    void setMemExceptionE2I(uint8_t val);
    void setMulResultE2I(uint32_t val);
    void setDivCompleteI(bool val);
    void setDivResultI(uint32_t val);

    // Flush inputs
    void setSquashE1E2I(bool val);
    void setSquashWbI(bool val);

    // ==================== Get functions for output ports ====================
    // E1 outputs
    bool getLoadE1O();
    bool getStoreE1O();
    bool getMulE1O();
    bool getBranchE1O();
    uint8_t getRdE1O();
    uint32_t getPcE1O();
    uint32_t getOpcodeE1O();
    uint32_t getOperandRaE1O();
    uint32_t getOperandRbE1O();

    // E2 outputs
    bool getLoadE2O();
    bool getMulE2O();
    uint8_t getRdE2O();
    uint32_t getResultE2O();

    // WB outputs
    bool getValidWbO();
    bool getCsrWbO();
    uint8_t getRdWbO();
    uint32_t getResultWbO();
    uint32_t getPcWbO();
    uint32_t getOpcodeWbO();
    uint32_t getOperandRaWbO();
    uint32_t getOperandRbWbO();
    uint8_t getExceptionWbO();
    bool getCsrWriteWbO();
    uint16_t getCsrWaddrWbO();
    uint32_t getCsrWdataWbO();

    // Control outputs
    bool getStallO();
    bool getSquashE1E2O();

    // ==================== Process function ====================
    // Called by parent module (riscv_issue) each cycle
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_PIPE_CTRL_HH__
