#include "generators/riscv_pipe_ctrl/riscv_pipe_ctrl.hh"

#include "base/trace.hh"
#include "debug/RiscvPipeCtrl.hh"

namespace gem5 {

RiscvPipeCtrl::RiscvPipeCtrl(const RiscvPipeCtrlParams &p)
    : SimObject(p),
      issue_valid_i_reg(false),
      issue_accept_i_reg(false),
      issue_stall_i_reg(false),
      issue_lsu_i_reg(false),
      issue_csr_i_reg(false),
      issue_div_i_reg(false),
      issue_mul_i_reg(false),
      issue_branch_i_reg(false),
      issue_rd_valid_i_reg(false),
      issue_rd_i_reg(0),
      issue_exception_i_reg(0),
      take_interrupt_i_reg(false),
      issue_branch_taken_i_reg(false),
      issue_branch_target_i_reg(0),
      issue_pc_i_reg(0),
      issue_opcode_i_reg(0),
      issue_operand_ra_i_reg(0),
      issue_operand_rb_i_reg(0),
      alu_result_e1_i_reg(0),
      csr_result_write_e1_i_reg(false),
      csr_result_value_e1_i_reg(0),
      csr_result_wdata_e1_i_reg(0),
      csr_result_exception_e1_i_reg(0),
      mem_complete_i_reg(false),
      mem_result_e2_i_reg(0),
      mem_exception_e2_i_reg(0),
      mul_result_e2_i_reg(0),
      div_complete_i_reg(false),
      div_result_i_reg(0),
      squash_e1_e2_i_reg(false),
      squash_wb_i_reg(false),
      load_e1_o_val(false),
      store_e1_o_val(false),
      mul_e1_o_val(false),
      branch_e1_o_val(false),
      rd_e1_o_val(0),
      pc_e1_o_val(0),
      opcode_e1_o_val(0),
      operand_ra_e1_o_val(0),
      operand_rb_e1_o_val(0),
      load_e2_o_val(false),
      mul_e2_o_val(false),
      rd_e2_o_val(0),
      result_e2_o_val(0),
      valid_wb_o_val(false),
      csr_wb_o_val(false),
      rd_wb_o_val(0),
      result_wb_o_val(0),
      pc_wb_o_val(0),
      opcode_wb_o_val(0),
      operand_ra_wb_o_val(0),
      operand_rb_wb_o_val(0),
      exception_wb_o_val(0),
      csr_write_wb_o_val(false),
      csr_waddr_wb_o_val(0),
      csr_wdata_wb_o_val(0),
      stall_o_val(false),
      squash_e1_e2_o_val(false),
      e1_valid_reg(false),
      e1_load_reg(false),
      e1_store_reg(false),
      e1_mul_reg(false),
      e1_branch_reg(false),
      e1_rd_reg(0),
      e1_pc_reg(0),
      e1_opcode_reg(0),
      e1_operand_ra_reg(0),
      e1_operand_rb_reg(0),
      e2_valid_reg(false),
      e2_load_reg(false),
      e2_mul_reg(false),
      e2_rd_reg(0),
      e2_result_reg(0),
      e2_pc_reg(0),
      e2_opcode_reg(0),
      e2_operand_ra_reg(0),
      e2_operand_rb_reg(0),
      e2_exception_reg(0),
      e2_csr_reg(false),
      e2_csr_write_reg(false),
      e2_csr_wdata_reg(0),
      e2_csr_waddr_reg(0)
{
}

// ======================== Set functions for input ports ========================

void
RiscvPipeCtrl::setIssueValidI(bool val)
{
    issue_valid_i_reg = val;
}

void
RiscvPipeCtrl::setIssueAcceptI(bool val)
{
    issue_accept_i_reg = val;
}

void
RiscvPipeCtrl::setIssueStallI(bool val)
{
    issue_stall_i_reg = val;
}

void
RiscvPipeCtrl::setIssueLsuI(bool val)
{
    issue_lsu_i_reg = val;
}

void
RiscvPipeCtrl::setIssueCsrI(bool val)
{
    issue_csr_i_reg = val;
}

void
RiscvPipeCtrl::setIssueDivI(bool val)
{
    issue_div_i_reg = val;
}

void
RiscvPipeCtrl::setIssueMulI(bool val)
{
    issue_mul_i_reg = val;
}

void
RiscvPipeCtrl::setIssueBranchI(bool val)
{
    issue_branch_i_reg = val;
}

void
RiscvPipeCtrl::setIssueRdValidI(bool val)
{
    issue_rd_valid_i_reg = val;
}

void
RiscvPipeCtrl::setIssueRdI(uint8_t val)
{
    issue_rd_i_reg = val;
}

void
RiscvPipeCtrl::setIssueExceptionI(uint8_t val)
{
    issue_exception_i_reg = val;
}

void
RiscvPipeCtrl::setTakeInterruptI(bool val)
{
    take_interrupt_i_reg = val;
}

void
RiscvPipeCtrl::setIssueBranchTakenI(bool val)
{
    issue_branch_taken_i_reg = val;
}

void
RiscvPipeCtrl::setIssueBranchTargetI(uint32_t val)
{
    issue_branch_target_i_reg = val;
}

void
RiscvPipeCtrl::setIssuePcI(uint32_t val)
{
    issue_pc_i_reg = val;
}

void
RiscvPipeCtrl::setIssueOpcodeI(uint32_t val)
{
    issue_opcode_i_reg = val;
}

void
RiscvPipeCtrl::setIssueOperandRaI(uint32_t val)
{
    issue_operand_ra_i_reg = val;
}

void
RiscvPipeCtrl::setIssueOperandRbI(uint32_t val)
{
    issue_operand_rb_i_reg = val;
}

void
RiscvPipeCtrl::setAluResultE1I(uint32_t val)
{
    alu_result_e1_i_reg = val;
}

void
RiscvPipeCtrl::setCsrResultWriteE1I(bool val)
{
    csr_result_write_e1_i_reg = val;
}

void
RiscvPipeCtrl::setCsrResultValueE1I(uint32_t val)
{
    csr_result_value_e1_i_reg = val;
}

void
RiscvPipeCtrl::setCsrResultWdataE1I(uint32_t val)
{
    csr_result_wdata_e1_i_reg = val;
}

void
RiscvPipeCtrl::setCsrResultExceptionE1I(uint8_t val)
{
    csr_result_exception_e1_i_reg = val;
}

void
RiscvPipeCtrl::setMemCompleteI(bool val)
{
    mem_complete_i_reg = val;
}

void
RiscvPipeCtrl::setMemResultE2I(uint32_t val)
{
    mem_result_e2_i_reg = val;
}

void
RiscvPipeCtrl::setMemExceptionE2I(uint8_t val)
{
    mem_exception_e2_i_reg = val;
}

void
RiscvPipeCtrl::setMulResultE2I(uint32_t val)
{
    mul_result_e2_i_reg = val;
}

void
RiscvPipeCtrl::setDivCompleteI(bool val)
{
    div_complete_i_reg = val;
}

void
RiscvPipeCtrl::setDivResultI(uint32_t val)
{
    div_result_i_reg = val;
}

void
RiscvPipeCtrl::setSquashE1E2I(bool val)
{
    squash_e1_e2_i_reg = val;
}

void
RiscvPipeCtrl::setSquashWbI(bool val)
{
    squash_wb_i_reg = val;
}

// ======================== Get functions for output ports ========================

bool
RiscvPipeCtrl::getLoadE1O()
{
    return load_e1_o_val;
}

bool
RiscvPipeCtrl::getStoreE1O()
{
    return store_e1_o_val;
}

bool
RiscvPipeCtrl::getMulE1O()
{
    return mul_e1_o_val;
}

bool
RiscvPipeCtrl::getBranchE1O()
{
    return branch_e1_o_val;
}

uint8_t
RiscvPipeCtrl::getRdE1O()
{
    return rd_e1_o_val;
}

uint32_t
RiscvPipeCtrl::getPcE1O()
{
    return pc_e1_o_val;
}

uint32_t
RiscvPipeCtrl::getOpcodeE1O()
{
    return opcode_e1_o_val;
}

uint32_t
RiscvPipeCtrl::getOperandRaE1O()
{
    return operand_ra_e1_o_val;
}

uint32_t
RiscvPipeCtrl::getOperandRbE1O()
{
    return operand_rb_e1_o_val;
}

bool
RiscvPipeCtrl::getLoadE2O()
{
    return load_e2_o_val;
}

bool
RiscvPipeCtrl::getMulE2O()
{
    return mul_e2_o_val;
}

uint8_t
RiscvPipeCtrl::getRdE2O()
{
    return rd_e2_o_val;
}

uint32_t
RiscvPipeCtrl::getResultE2O()
{
    return result_e2_o_val;
}

bool
RiscvPipeCtrl::getValidWbO()
{
    return valid_wb_o_val;
}

bool
RiscvPipeCtrl::getCsrWbO()
{
    return csr_wb_o_val;
}

uint8_t
RiscvPipeCtrl::getRdWbO()
{
    return rd_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getResultWbO()
{
    return result_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getPcWbO()
{
    return pc_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getOpcodeWbO()
{
    return opcode_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getOperandRaWbO()
{
    return operand_ra_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getOperandRbWbO()
{
    return operand_rb_wb_o_val;
}

uint8_t
RiscvPipeCtrl::getExceptionWbO()
{
    return exception_wb_o_val;
}

bool
RiscvPipeCtrl::getCsrWriteWbO()
{
    return csr_write_wb_o_val;
}

uint16_t
RiscvPipeCtrl::getCsrWaddrWbO()
{
    return csr_waddr_wb_o_val;
}

uint32_t
RiscvPipeCtrl::getCsrWdataWbO()
{
    return csr_wdata_wb_o_val;
}

bool
RiscvPipeCtrl::getStallO()
{
    return stall_o_val;
}

bool
RiscvPipeCtrl::getSquashE1E2O()
{
    return squash_e1_e2_o_val;
}

// ======================== Process function ========================

void
RiscvPipeCtrl::process()
{
    DPRINTF(RiscvPipeCtrl, "Processing pipeline control\n");

    // =====================================================================
    // STEP 1: Drive all outputs from current register values (combinational)
    // =====================================================================

    // -- E1 outputs (driven from E1 pipeline registers) --
    load_e1_o_val = e1_load_reg;
    store_e1_o_val = e1_store_reg;
    mul_e1_o_val = e1_mul_reg;
    branch_e1_o_val = e1_branch_reg;
    rd_e1_o_val = e1_rd_reg;
    pc_e1_o_val = e1_pc_reg;
    opcode_e1_o_val = e1_opcode_reg;
    operand_ra_e1_o_val = e1_operand_ra_reg;
    operand_rb_e1_o_val = e1_operand_rb_reg;

    // -- E2 outputs (driven from E2 pipeline registers) --
    load_e2_o_val = e2_load_reg;
    mul_e2_o_val = e2_mul_reg;
    rd_e2_o_val = e2_rd_reg;
    result_e2_o_val = e2_result_reg;

    // -- WB outputs (driven from E2 pipeline registers) --
    valid_wb_o_val = e2_valid_reg;
    csr_wb_o_val = e2_csr_reg;
    rd_wb_o_val = e2_rd_reg;
    result_wb_o_val = e2_result_reg;
    pc_wb_o_val = e2_pc_reg;
    opcode_wb_o_val = e2_opcode_reg;
    operand_ra_wb_o_val = e2_operand_ra_reg;
    operand_rb_wb_o_val = e2_operand_rb_reg;
    exception_wb_o_val = e2_exception_reg;
    csr_write_wb_o_val = e2_csr_write_reg;
    csr_waddr_wb_o_val = e2_csr_waddr_reg;
    csr_wdata_wb_o_val = e2_csr_wdata_reg;

    // -- Stall output --
    stall_o_val = false;
    // -- Flush output --
    squash_e1_e2_o_val = false;

    // =====================================================================
    // STEP 2: Stall logic
    // =====================================================================
    // Stall conditions:
    // 1. E2 has a load instruction waiting for memory completion
    // 2. External stall from issue stage

    bool stall_load_hazard = false;
    if (e2_load_reg && e2_valid_reg && !mem_complete_i_reg) {
        stall_load_hazard = true;
    }

    stall_o_val = stall_load_hazard || issue_stall_i_reg;

    // =====================================================================
    // STEP 3: Flush logic
    // =====================================================================
    // Generate squash signal for E1->E2 pipeline:
    // - External squash input (e.g., from branch predictor)
    // - Branch is taken (resolved in issue stage)
    // - Interrupt is taken

    bool branch_taken = false;
    if (issue_branch_i_reg && issue_branch_taken_i_reg) {
        branch_taken = true;
    }

    squash_e1_e2_o_val = squash_e1_e2_i_reg || branch_taken
                       || take_interrupt_i_reg;

    // =====================================================================
    // STEP 4: Override E2/WB results with LSU/mul/div results
    // =====================================================================

    // Override with LSU memory result if available
    if (e2_load_reg && e2_valid_reg && mem_complete_i_reg) {
        result_e2_o_val = mem_result_e2_i_reg;
        result_wb_o_val = mem_result_e2_i_reg;
        exception_wb_o_val = mem_exception_e2_i_reg;
    }

    // Override with multiplier result if applicable
    if (e2_mul_reg && e2_valid_reg) {
        result_e2_o_val = mul_result_e2_i_reg;
        result_wb_o_val = mul_result_e2_i_reg;
    }

    // Override with divider result if complete
    if (e2_valid_reg && div_complete_i_reg) {
        result_e2_o_val = div_result_i_reg;
        result_wb_o_val = div_result_i_reg;
    }

    // =====================================================================
    // STEP 5: WB stage - apply writeback squash
    // =====================================================================

    if (squash_wb_i_reg) {
        valid_wb_o_val = false;
        csr_write_wb_o_val = false;
    }

    // =====================================================================
    // STEP 6: Update E2 pipeline registers (from E1 execution results)
    // =====================================================================

    bool nxt_e2_valid;
    bool nxt_e2_load;
    bool nxt_e2_mul;
    uint8_t nxt_e2_rd;
    uint32_t nxt_e2_result;
    uint32_t nxt_e2_pc;
    uint32_t nxt_e2_opcode;
    uint32_t nxt_e2_operand_ra;
    uint32_t nxt_e2_operand_rb;
    uint8_t nxt_e2_exception;
    bool nxt_e2_csr;
    bool nxt_e2_csr_write;
    uint32_t nxt_e2_csr_wdata;
    uint16_t nxt_e2_csr_waddr;

    // Default: bubble (no valid data)
    nxt_e2_valid = false;
    nxt_e2_load = false;
    nxt_e2_mul = false;
    nxt_e2_rd = 0;
    nxt_e2_result = 0;
    nxt_e2_pc = 0;
    nxt_e2_opcode = 0;
    nxt_e2_operand_ra = 0;
    nxt_e2_operand_rb = 0;
    nxt_e2_exception = 0;
    nxt_e2_csr = false;
    nxt_e2_csr_write = false;
    nxt_e2_csr_wdata = 0;
    nxt_e2_csr_waddr = 0;

    // If E1 has valid data and not squashed, move to E2
    if (!squash_e1_e2_o_val && e1_valid_reg) {
        nxt_e2_valid = true;
        nxt_e2_load = e1_load_reg;
        nxt_e2_mul = e1_mul_reg;
        nxt_e2_rd = e1_rd_reg;
        nxt_e2_result = alu_result_e1_i_reg;
        nxt_e2_pc = e1_pc_reg;
        nxt_e2_opcode = e1_opcode_reg;
        nxt_e2_operand_ra = e1_operand_ra_reg;
        nxt_e2_operand_rb = e1_operand_rb_reg;

        // CSR result takes priority over ALU result
        if (csr_result_write_e1_i_reg) {
            nxt_e2_result = csr_result_value_e1_i_reg;
            nxt_e2_csr = true;
            nxt_e2_csr_write = true;
            nxt_e2_csr_wdata = csr_result_wdata_e1_i_reg;
            // CSR address is in bits [31:20] of instruction
            nxt_e2_csr_waddr = (e1_opcode_reg >> 20) & 0xFFF;
            nxt_e2_exception = csr_result_exception_e1_i_reg;
        }
    }

    // =====================================================================
    // STEP 7: Update E1 pipeline registers (from Issue)
    // =====================================================================

    if (!stall_o_val && issue_valid_i_reg) {
        // Capture instruction from issue stage
        e1_load_reg = false;
        e1_store_reg = false;

        // Determine load vs store from opcode
        // RISC-V LOAD opcode = 0x03, STORE opcode = 0x23
        if (issue_lsu_i_reg) {
            uint8_t opcode_bits = issue_opcode_i_reg & 0x7F;
            if (opcode_bits == 0x03) {
                e1_load_reg = true;
            } else if (opcode_bits == 0x23) {
                e1_store_reg = true;
            }
        }

        e1_mul_reg = issue_mul_i_reg;
        e1_branch_reg = issue_branch_i_reg;
        e1_rd_reg = issue_rd_i_reg;
        e1_pc_reg = issue_pc_i_reg;
        e1_opcode_reg = issue_opcode_i_reg;
        e1_operand_ra_reg = issue_operand_ra_i_reg;
        e1_operand_rb_reg = issue_operand_rb_i_reg;
        e1_valid_reg = true;
    } else if (squash_e1_e2_o_val) {
        // Flush E1: clear all E1 registers
        e1_load_reg = false;
        e1_store_reg = false;
        e1_mul_reg = false;
        e1_branch_reg = false;
        e1_rd_reg = 0;
        e1_pc_reg = 0;
        e1_opcode_reg = 0;
        e1_operand_ra_reg = 0;
        e1_operand_rb_reg = 0;
        e1_valid_reg = false;
    }
    // If stalled (stall_o_val true), E1 registers keep their values unchanged

    // =====================================================================
    // STEP 8: Commit E2 pipeline register updates
    // =====================================================================

    e2_valid_reg = nxt_e2_valid;
    e2_load_reg = nxt_e2_load;
    e2_mul_reg = nxt_e2_mul;
    e2_rd_reg = nxt_e2_rd;
    e2_result_reg = nxt_e2_result;
    e2_pc_reg = nxt_e2_pc;
    e2_opcode_reg = nxt_e2_opcode;
    e2_operand_ra_reg = nxt_e2_operand_ra;
    e2_operand_rb_reg = nxt_e2_operand_rb;
    e2_exception_reg = nxt_e2_exception;
    e2_csr_reg = nxt_e2_csr;
    e2_csr_write_reg = nxt_e2_csr_write;
    e2_csr_wdata_reg = nxt_e2_csr_wdata;
    e2_csr_waddr_reg = nxt_e2_csr_waddr;
}

} // namespace gem5
