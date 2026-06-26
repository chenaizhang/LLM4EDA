#include "generators/riscv_issue/riscv_issue.hh"

namespace gem5 {

RiscvIssue::RiscvIssue(const RiscvIssueParams &params)
    : SimObject(params),
      regfile(*params.regfile),
      xilinx_2r1w(params.xilinx_2r1w),
      supportDualIssue(params.support_dual_issue)
{
    // Initialize all input registers to 0
    fetch_valid_i_reg = 0;
    fetch_instr_i_reg = 0;
    fetch_pc_i_reg = 0;
    fetch_fault_fetch_i_reg = 0;
    fetch_fault_page_i_reg = 0;
    fetch_instr_exec_i_reg = 0;
    fetch_instr_lsu_i_reg = 0;
    fetch_instr_branch_i_reg = 0;
    fetch_instr_mul_i_reg = 0;
    fetch_instr_div_i_reg = 0;
    fetch_instr_csr_i_reg = 0;
    fetch_instr_rd_valid_i_reg = 0;
    fetch_instr_invalid_i_reg = 0;

    branch_exec_request_i_reg = 0;
    branch_exec_is_taken_i_reg = 0;
    branch_exec_is_not_taken_i_reg = 0;
    branch_exec_source_i_reg = 0;
    branch_exec_is_call_i_reg = 0;
    branch_exec_is_ret_i_reg = 0;
    branch_exec_is_jmp_i_reg = 0;
    branch_exec_pc_i_reg = 0;
    branch_d_exec_request_i_reg = 0;
    branch_d_exec_pc_i_reg = 0;
    branch_d_exec_priv_i_reg = 0;
    branch_csr_request_i_reg = 0;
    branch_csr_pc_i_reg = 0;
    branch_csr_priv_i_reg = 0;

    writeback_exec_value_i_reg = 0;
    writeback_mem_valid_i_reg = 0;
    writeback_mem_value_i_reg = 0;
    writeback_mem_exception_i_reg = 0;
    writeback_mul_value_i_reg = 0;
    writeback_div_valid_i_reg = 0;
    writeback_div_value_i_reg = 0;

    csr_result_e1_value_i_reg = 0;
    csr_result_e1_write_i_reg = 0;
    csr_result_e1_wdata_i_reg = 0;
    csr_result_e1_exception_i_reg = 0;

    lsu_stall_i_reg = 0;
    take_interrupt_i_reg = 0;

    // Initialize all output values to 0
    fetch_accept_o_val = 0;

    branch_request_o_val = 0;
    branch_pc_o_val = 0;
    branch_priv_o_val = 0;

    exec_opcode_valid_o_val = 0;
    lsu_opcode_valid_o_val = 0;
    csr_opcode_valid_o_val = 0;
    mul_opcode_valid_o_val = 0;
    div_opcode_valid_o_val = 0;

    opcode_opcode_o_val = 0;
    opcode_pc_o_val = 0;
    opcode_invalid_o_val = 0;
    opcode_rd_idx_o_val = 0;
    opcode_ra_idx_o_val = 0;
    opcode_rb_idx_o_val = 0;
    opcode_ra_operand_o_val = 0;
    opcode_rb_operand_o_val = 0;

    lsu_opcode_opcode_o_val = 0;
    lsu_opcode_pc_o_val = 0;
    lsu_opcode_invalid_o_val = 0;
    lsu_opcode_rd_idx_o_val = 0;
    lsu_opcode_ra_idx_o_val = 0;
    lsu_opcode_rb_idx_o_val = 0;
    lsu_opcode_ra_operand_o_val = 0;
    lsu_opcode_rb_operand_o_val = 0;

    mul_opcode_opcode_o_val = 0;
    mul_opcode_pc_o_val = 0;
    mul_opcode_invalid_o_val = 0;
    mul_opcode_rd_idx_o_val = 0;
    mul_opcode_ra_idx_o_val = 0;
    mul_opcode_rb_idx_o_val = 0;
    mul_opcode_ra_operand_o_val = 0;
    mul_opcode_rb_operand_o_val = 0;

    csr_opcode_opcode_o_val = 0;
    csr_opcode_pc_o_val = 0;
    csr_opcode_invalid_o_val = 0;
    csr_opcode_rd_idx_o_val = 0;
    csr_opcode_ra_idx_o_val = 0;
    csr_opcode_rb_idx_o_val = 0;
    csr_opcode_ra_operand_o_val = 0;
    csr_opcode_rb_operand_o_val = 0;

    csr_writeback_write_o_val = 0;
    csr_writeback_waddr_o_val = 0;
    csr_writeback_wdata_o_val = 0;
    csr_writeback_exception_o_val = 0;
    csr_writeback_exception_pc_o_val = 0;
    csr_writeback_exception_addr_o_val = 0;

    exec_hold_o_val = 0;
    mul_hold_o_val = 0;
    interrupt_inhibit_o_val = 0;

    // Initialize internal pipeline state
    exec_rd_idx_reg = 0;
    mem_rd_idx_reg = 0;
    mul_rd_idx_reg = 0;
    div_rd_idx_reg = 0;

    exec_in_flight_reg = 0;
    mem_in_flight_reg = 0;
    mul_in_flight_reg = 0;
    div_in_flight_reg = 0;

    interrupt_inhibit_reg = 0;
}

// ==================== Input Set Functions ====================

/** Fetch input set functions */
void RiscvIssue::setFetchValidI(uint8_t val) { fetch_valid_i_reg = val; }
void RiscvIssue::setFetchInstrI(uint32_t val) { fetch_instr_i_reg = val; }
void RiscvIssue::setFetchPcI(uint32_t val) { fetch_pc_i_reg = val; }
void RiscvIssue::setFetchFaultFetchI(uint8_t val) { fetch_fault_fetch_i_reg = val; }
void RiscvIssue::setFetchFaultPageI(uint8_t val) { fetch_fault_page_i_reg = val; }
void RiscvIssue::setFetchInstrExecI(uint8_t val) { fetch_instr_exec_i_reg = val; }
void RiscvIssue::setFetchInstrLsuI(uint8_t val) { fetch_instr_lsu_i_reg = val; }
void RiscvIssue::setFetchInstrBranchI(uint8_t val) { fetch_instr_branch_i_reg = val; }
void RiscvIssue::setFetchInstrMulI(uint8_t val) { fetch_instr_mul_i_reg = val; }
void RiscvIssue::setFetchInstrDivI(uint8_t val) { fetch_instr_div_i_reg = val; }
void RiscvIssue::setFetchInstrCsrI(uint8_t val) { fetch_instr_csr_i_reg = val; }
void RiscvIssue::setFetchInstrRdValidI(uint8_t val) { fetch_instr_rd_valid_i_reg = val; }
void RiscvIssue::setFetchInstrInvalidI(uint8_t val) { fetch_instr_invalid_i_reg = val; }

/** Branch input set functions */
void RiscvIssue::setBranchExecRequestI(uint8_t val) { branch_exec_request_i_reg = val; }
void RiscvIssue::setBranchExecIsTakenI(uint8_t val) { branch_exec_is_taken_i_reg = val; }
void RiscvIssue::setBranchExecIsNotTakenI(uint8_t val) { branch_exec_is_not_taken_i_reg = val; }
void RiscvIssue::setBranchExecSourceI(uint8_t val) { branch_exec_source_i_reg = val; }
void RiscvIssue::setBranchExecIsCallI(uint8_t val) { branch_exec_is_call_i_reg = val; }
void RiscvIssue::setBranchExecIsRetI(uint8_t val) { branch_exec_is_ret_i_reg = val; }
void RiscvIssue::setBranchExecIsJmpI(uint8_t val) { branch_exec_is_jmp_i_reg = val; }
void RiscvIssue::setBranchExecPcI(uint32_t val) { branch_exec_pc_i_reg = val; }
void RiscvIssue::setBranchDExecRequestI(uint8_t val) { branch_d_exec_request_i_reg = val; }
void RiscvIssue::setBranchDExecPcI(uint32_t val) { branch_d_exec_pc_i_reg = val; }
void RiscvIssue::setBranchDExecPrivI(uint8_t val) { branch_d_exec_priv_i_reg = val; }
void RiscvIssue::setBranchCsrRequestI(uint8_t val) { branch_csr_request_i_reg = val; }
void RiscvIssue::setBranchCsrPcI(uint32_t val) { branch_csr_pc_i_reg = val; }
void RiscvIssue::setBranchCsrPrivI(uint8_t val) { branch_csr_priv_i_reg = val; }

/** Writeback input set functions */
void RiscvIssue::setWritebackExecValueI(uint32_t val) { writeback_exec_value_i_reg = val; }
void RiscvIssue::setWritebackMemValidI(uint8_t val) { writeback_mem_valid_i_reg = val; }
void RiscvIssue::setWritebackMemValueI(uint32_t val) { writeback_mem_value_i_reg = val; }
void RiscvIssue::setWritebackMemExceptionI(uint8_t val) { writeback_mem_exception_i_reg = val; }
void RiscvIssue::setWritebackMulValueI(uint32_t val) { writeback_mul_value_i_reg = val; }
void RiscvIssue::setWritebackDivValidI(uint8_t val) { writeback_div_valid_i_reg = val; }
void RiscvIssue::setWritebackDivValueI(uint32_t val) { writeback_div_value_i_reg = val; }

/** CSR input set functions */
void RiscvIssue::setCsrResultE1ValueI(uint32_t val) { csr_result_e1_value_i_reg = val; }
void RiscvIssue::setCsrResultE1WriteI(uint8_t val) { csr_result_e1_write_i_reg = val; }
void RiscvIssue::setCsrResultE1WdataI(uint32_t val) { csr_result_e1_wdata_i_reg = val; }
void RiscvIssue::setCsrResultE1ExceptionI(uint8_t val) { csr_result_e1_exception_i_reg = val; }

/** Control input set functions */
void RiscvIssue::setLsuStallI(uint8_t val) { lsu_stall_i_reg = val; }
void RiscvIssue::setTakeInterruptI(uint8_t val) { take_interrupt_i_reg = val; }

// ==================== Output Get Functions ====================

/** Fetch interface get functions */
uint8_t RiscvIssue::getFetchAcceptO() { return fetch_accept_o_val; }

/** Branch output get functions */
uint8_t RiscvIssue::getBranchRequestO() { return branch_request_o_val; }
uint32_t RiscvIssue::getBranchPcO() { return branch_pc_o_val; }
uint8_t RiscvIssue::getBranchPrivO() { return branch_priv_o_val; }

/** Execution unit valid get functions */
uint8_t RiscvIssue::getExecOpcodeValidO() { return exec_opcode_valid_o_val; }
uint8_t RiscvIssue::getLsuOpcodeValidO() { return lsu_opcode_valid_o_val; }
uint8_t RiscvIssue::getCsrOpcodeValidO() { return csr_opcode_valid_o_val; }
uint8_t RiscvIssue::getMulOpcodeValidO() { return mul_opcode_valid_o_val; }
uint8_t RiscvIssue::getDivOpcodeValidO() { return div_opcode_valid_o_val; }

/** Generic opcode get functions */
uint32_t RiscvIssue::getOpcodeOpcodeO() { return opcode_opcode_o_val; }
uint32_t RiscvIssue::getOpcodePcO() { return opcode_pc_o_val; }
uint8_t RiscvIssue::getOpcodeInvalidO() { return opcode_invalid_o_val; }
uint8_t RiscvIssue::getOpcodeRdIdxO() { return opcode_rd_idx_o_val; }
uint8_t RiscvIssue::getOpcodeRaIdxO() { return opcode_ra_idx_o_val; }
uint8_t RiscvIssue::getOpcodeRbIdxO() { return opcode_rb_idx_o_val; }
uint32_t RiscvIssue::getOpcodeRaOperandO() { return opcode_ra_operand_o_val; }
uint32_t RiscvIssue::getOpcodeRbOperandO() { return opcode_rb_operand_o_val; }

/** LSU opcode get functions */
uint32_t RiscvIssue::getLsuOpcodeOpcodeO() { return lsu_opcode_opcode_o_val; }
uint32_t RiscvIssue::getLsuOpcodePcO() { return lsu_opcode_pc_o_val; }
uint8_t RiscvIssue::getLsuOpcodeInvalidO() { return lsu_opcode_invalid_o_val; }
uint8_t RiscvIssue::getLsuOpcodeRdIdxO() { return lsu_opcode_rd_idx_o_val; }
uint8_t RiscvIssue::getLsuOpcodeRaIdxO() { return lsu_opcode_ra_idx_o_val; }
uint8_t RiscvIssue::getLsuOpcodeRbIdxO() { return lsu_opcode_rb_idx_o_val; }
uint32_t RiscvIssue::getLsuOpcodeRaOperandO() { return lsu_opcode_ra_operand_o_val; }
uint32_t RiscvIssue::getLsuOpcodeRbOperandO() { return lsu_opcode_rb_operand_o_val; }

/** MUL opcode get functions */
uint32_t RiscvIssue::getMulOpcodeOpcodeO() { return mul_opcode_opcode_o_val; }
uint32_t RiscvIssue::getMulOpcodePcO() { return mul_opcode_pc_o_val; }
uint8_t RiscvIssue::getMulOpcodeInvalidO() { return mul_opcode_invalid_o_val; }
uint8_t RiscvIssue::getMulOpcodeRdIdxO() { return mul_opcode_rd_idx_o_val; }
uint8_t RiscvIssue::getMulOpcodeRaIdxO() { return mul_opcode_ra_idx_o_val; }
uint8_t RiscvIssue::getMulOpcodeRbIdxO() { return mul_opcode_rb_idx_o_val; }
uint32_t RiscvIssue::getMulOpcodeRaOperandO() { return mul_opcode_ra_operand_o_val; }
uint32_t RiscvIssue::getMulOpcodeRbOperandO() { return mul_opcode_rb_operand_o_val; }

/** CSR opcode get functions */
uint32_t RiscvIssue::getCsrOpcodeOpcodeO() { return csr_opcode_opcode_o_val; }
uint32_t RiscvIssue::getCsrOpcodePcO() { return csr_opcode_pc_o_val; }
uint8_t RiscvIssue::getCsrOpcodeInvalidO() { return csr_opcode_invalid_o_val; }
uint8_t RiscvIssue::getCsrOpcodeRdIdxO() { return csr_opcode_rd_idx_o_val; }
uint8_t RiscvIssue::getCsrOpcodeRaIdxO() { return csr_opcode_ra_idx_o_val; }
uint8_t RiscvIssue::getCsrOpcodeRbIdxO() { return csr_opcode_rb_idx_o_val; }
uint32_t RiscvIssue::getCsrOpcodeRaOperandO() { return csr_opcode_ra_operand_o_val; }
uint32_t RiscvIssue::getCsrOpcodeRbOperandO() { return csr_opcode_rb_operand_o_val; }

/** CSR writeback get functions */
uint8_t RiscvIssue::getCsrWritebackWriteO() { return csr_writeback_write_o_val; }
uint16_t RiscvIssue::getCsrWritebackWaddrO() { return csr_writeback_waddr_o_val; }
uint32_t RiscvIssue::getCsrWritebackWdataO() { return csr_writeback_wdata_o_val; }
uint8_t RiscvIssue::getCsrWritebackExceptionO() { return csr_writeback_exception_o_val; }
uint32_t RiscvIssue::getCsrWritebackExceptionPcO() { return csr_writeback_exception_pc_o_val; }
uint32_t RiscvIssue::getCsrWritebackExceptionAddrO() { return csr_writeback_exception_addr_o_val; }

/** Pipeline hold get functions */
uint8_t RiscvIssue::getExecHoldO() { return exec_hold_o_val; }
uint8_t RiscvIssue::getMulHoldO() { return mul_hold_o_val; }
uint8_t RiscvIssue::getInterruptInhibitO() { return interrupt_inhibit_o_val; }

// ==================== Process Function ====================

void
RiscvIssue::process()
{
    // ---------------------------------------------------------------
    // 1. Handle writeback merging to register file
    //    Priority: exec > mem > mul > div
    // ---------------------------------------------------------------
    uint8_t wb_rd_idx = 0;
    uint32_t wb_value = 0;
    uint8_t wb_valid = 0;

    if (exec_in_flight_reg) {
        // Exec unit always writes back (single-cycle)
        wb_rd_idx = exec_rd_idx_reg;
        wb_value = writeback_exec_value_i_reg;
        wb_valid = 1;
        exec_in_flight_reg = 0;
    } else if (writeback_mem_valid_i_reg) {
        // Mem writeback valid
        wb_rd_idx = mem_rd_idx_reg;
        wb_value = writeback_mem_value_i_reg;
        wb_valid = 1;
        mem_in_flight_reg = 0;
    } else if (mul_in_flight_reg) {
        // Mul writeback (single-cycle or multi-cycle, simplified as always valid)
        wb_rd_idx = mul_rd_idx_reg;
        wb_value = writeback_mul_value_i_reg;
        wb_valid = 1;
        mul_in_flight_reg = 0;
    } else if (writeback_div_valid_i_reg) {
        // Div writeback with valid
        wb_rd_idx = div_rd_idx_reg;
        wb_value = writeback_div_value_i_reg;
        wb_valid = 1;
        div_in_flight_reg = 0;
    }

    // Set regfile write port
    if (wb_valid && wb_rd_idx != 0) {
        regfile.setRd0I(wb_rd_idx);
        regfile.setRd0ValueI(wb_value);
    } else {
        regfile.setRd0I(0);
        regfile.setRd0ValueI(0);
    }

    // ---------------------------------------------------------------
    // 2. Handle branch forwarding
    //    Forward branch results from exec and CSR to Fetch
    // ---------------------------------------------------------------
    uint8_t branch_taken = 0;
    if (branch_exec_request_i_reg) {
        branch_request_o_val = 1;
        branch_pc_o_val = branch_exec_pc_i_reg;
        branch_priv_o_val = branch_exec_source_i_reg & 0x3;
        branch_taken = 1;
    } else if (branch_csr_request_i_reg) {
        branch_request_o_val = 1;
        branch_pc_o_val = branch_csr_pc_i_reg;
        branch_priv_o_val = branch_csr_priv_i_reg;
        branch_taken = 1;
    } else {
        branch_request_o_val = 0;
        branch_pc_o_val = 0;
        branch_priv_o_val = 0;
    }

    // ---------------------------------------------------------------
    // 3. Handle CSR writeback output
    // ---------------------------------------------------------------
    if (csr_result_e1_write_i_reg) {
        csr_writeback_write_o_val = 1;
        csr_writeback_wdata_o_val = csr_result_e1_wdata_i_reg;
        csr_writeback_exception_o_val = csr_result_e1_exception_i_reg;
        csr_writeback_exception_pc_o_val = fetch_pc_i_reg;
        csr_writeback_exception_addr_o_val = csr_result_e1_value_i_reg;
    } else {
        csr_writeback_write_o_val = 0;
        csr_writeback_wdata_o_val = 0;
        csr_writeback_exception_o_val = 0;
        csr_writeback_exception_pc_o_val = 0;
        csr_writeback_exception_addr_o_val = 0;
    }

    // ---------------------------------------------------------------
    // 4. Determine pipeline hold / stall conditions
    // ---------------------------------------------------------------
    // Interrupt inhibit: active while handling interrupt or branch
    if (take_interrupt_i_reg) {
        interrupt_inhibit_reg = 1;
    } else if (branch_taken) {
        interrupt_inhibit_reg = 1;
    } else if (!fetch_valid_i_reg) {
        // Clear inhibit when no new instruction and no interrupt/branch
        interrupt_inhibit_reg = 0;
    }

    // exec_hold_o: set when exec unit is busy (in-flight and not writing back yet)
    exec_hold_o_val = exec_in_flight_reg;

    // mul_hold_o: set when mul unit is busy
    mul_hold_o_val = mul_in_flight_reg;

    // interrupt_inhibit_o
    interrupt_inhibit_o_val = interrupt_inhibit_reg;

    // ---------------------------------------------------------------
    // 5. Determine if we can accept a new instruction
    // ---------------------------------------------------------------
    uint8_t accept_instr = 1;

    // Stall conditions
    if (exec_hold_o_val) {
        accept_instr = 0;
    }
    if (lsu_stall_i_reg) {
        accept_instr = 0;
    }
    if (take_interrupt_i_reg) {
        accept_instr = 0;
    }
    if (interrupt_inhibit_reg) {
        accept_instr = 0;
    }
    if (branch_taken) {
        accept_instr = 0;
    }

    fetch_accept_o_val = accept_instr;

    // ---------------------------------------------------------------
    // 6. Dispatch new instruction (if valid and accepted)
    // ---------------------------------------------------------------

    // Clear all opcode valid signals by default
    exec_opcode_valid_o_val = 0;
    lsu_opcode_valid_o_val = 0;
    csr_opcode_valid_o_val = 0;
    mul_opcode_valid_o_val = 0;
    div_opcode_valid_o_val = 0;

    // Clear output opcode buses
    opcode_opcode_o_val = 0;
    opcode_pc_o_val = 0;
    opcode_invalid_o_val = 0;
    opcode_rd_idx_o_val = 0;
    opcode_ra_idx_o_val = 0;
    opcode_rb_idx_o_val = 0;
    opcode_ra_operand_o_val = 0;
    opcode_rb_operand_o_val = 0;

    lsu_opcode_opcode_o_val = 0;
    lsu_opcode_pc_o_val = 0;
    lsu_opcode_invalid_o_val = 0;
    lsu_opcode_rd_idx_o_val = 0;
    lsu_opcode_ra_idx_o_val = 0;
    lsu_opcode_rb_idx_o_val = 0;
    lsu_opcode_ra_operand_o_val = 0;
    lsu_opcode_rb_operand_o_val = 0;

    mul_opcode_opcode_o_val = 0;
    mul_opcode_pc_o_val = 0;
    mul_opcode_invalid_o_val = 0;
    mul_opcode_rd_idx_o_val = 0;
    mul_opcode_ra_idx_o_val = 0;
    mul_opcode_rb_idx_o_val = 0;
    mul_opcode_ra_operand_o_val = 0;
    mul_opcode_rb_operand_o_val = 0;

    csr_opcode_opcode_o_val = 0;
    csr_opcode_pc_o_val = 0;
    csr_opcode_invalid_o_val = 0;
    csr_opcode_rd_idx_o_val = 0;
    csr_opcode_ra_idx_o_val = 0;
    csr_opcode_rb_idx_o_val = 0;
    csr_opcode_ra_operand_o_val = 0;
    csr_opcode_rb_operand_o_val = 0;

    if (fetch_valid_i_reg && accept_instr) {
        // 6a. Decode instruction fields
        // RISC-V instruction format:
        //   rd:  bits 11:7
        //   rs1: bits 19:15
        //   rs2: bits 24:20
        //   opcode: bits 6:0
        uint32_t instr = fetch_instr_i_reg;
        uint8_t rd = (instr >> 7) & 0x1F;
        uint8_t rs1 = (instr >> 15) & 0x1F;
        uint8_t rs2 = (instr >> 20) & 0x1F;

        // Process fault flags
        uint8_t has_fault = 0;
        if (fetch_fault_fetch_i_reg) {
            has_fault = 1;
        }
        if (fetch_fault_page_i_reg) {
            has_fault = 1;
        }

        // 6b. Read register file
        if (!has_fault) {
            regfile.setRa0I(rs1);
            regfile.setRb0I(rs2);
        } else {
            regfile.setRa0I(0);
            regfile.setRb0I(0);
        }

        // Process regfile (this commits writeback and performs read)
        regfile.process();

        // Read regfile outputs
        uint32_t ra_val = regfile.getRa0ValueO();
        uint32_t rb_val = regfile.getRb0ValueO();

        // 6c. Apply bypass (data forwarding) logic
        // Check if rs1 matches any in-flight writeback destination
        uint32_t ra_operand = ra_val;
        uint32_t rb_operand = rb_val;

        // Bypass from exec writeback (current cycle)
        if (wb_valid && rs1 != 0 && rs1 == wb_rd_idx) {
            ra_operand = wb_value;
        }
        if (wb_valid && rs2 != 0 && rs2 == wb_rd_idx) {
            rb_operand = wb_value;
        }

        // Bypass from mem (check against stored mem_rd_idx before clearing)
        if (writeback_mem_valid_i_reg && rs1 != 0 && rs1 == mem_rd_idx_reg) {
            ra_operand = writeback_mem_value_i_reg;
        }
        if (writeback_mem_valid_i_reg && rs2 != 0 && rs2 == mem_rd_idx_reg) {
            rb_operand = writeback_mem_value_i_reg;
        }

        // Bypass from mul
        if (mul_in_flight_reg && rs1 != 0 && rs1 == mul_rd_idx_reg) {
            ra_operand = writeback_mul_value_i_reg;
        }
        if (mul_in_flight_reg && rs2 != 0 && rs2 == mul_rd_idx_reg) {
            rb_operand = writeback_mul_value_i_reg;
        }

        // Bypass from div
        if (writeback_div_valid_i_reg && rs1 != 0 && rs1 == div_rd_idx_reg) {
            ra_operand = writeback_div_value_i_reg;
        }
        if (writeback_div_valid_i_reg && rs2 != 0 && rs2 == div_rd_idx_reg) {
            rb_operand = writeback_div_value_i_reg;
        }

        // 6d. Set generic opcode outputs
        opcode_opcode_o_val = instr;
        opcode_pc_o_val = fetch_pc_i_reg;
        opcode_invalid_o_val = fetch_instr_invalid_i_reg | has_fault;
        opcode_rd_idx_o_val = rd;
        opcode_ra_idx_o_val = rs1;
        opcode_rb_idx_o_val = rs2;
        opcode_ra_operand_o_val = ra_operand;
        opcode_rb_operand_o_val = rb_operand;

        // 6e. Route instruction to appropriate execution unit
        if (fetch_instr_exec_i_reg) {
            // Dispatch to ALU/exec unit
            exec_opcode_valid_o_val = 1;
            exec_rd_idx_reg = rd;
            exec_in_flight_reg = 1;

        } else if (fetch_instr_lsu_i_reg) {
            // Dispatch to LSU
            lsu_opcode_valid_o_val = 1;
            lsu_opcode_opcode_o_val = instr;
            lsu_opcode_pc_o_val = fetch_pc_i_reg;
            lsu_opcode_invalid_o_val = fetch_instr_invalid_i_reg | has_fault;
            lsu_opcode_rd_idx_o_val = rd;
            lsu_opcode_ra_idx_o_val = rs1;
            lsu_opcode_rb_idx_o_val = rs2;
            lsu_opcode_ra_operand_o_val = ra_operand;
            lsu_opcode_rb_operand_o_val = rb_operand;
            mem_rd_idx_reg = rd;
            mem_in_flight_reg = 1;

        } else if (fetch_instr_csr_i_reg) {
            // Dispatch to CSR unit
            csr_opcode_valid_o_val = 1;
            csr_opcode_opcode_o_val = instr;
            csr_opcode_pc_o_val = fetch_pc_i_reg;
            csr_opcode_invalid_o_val = fetch_instr_invalid_i_reg | has_fault;
            csr_opcode_rd_idx_o_val = rd;
            csr_opcode_ra_idx_o_val = rs1;
            csr_opcode_rb_idx_o_val = rs2;
            csr_opcode_ra_operand_o_val = ra_operand;
            csr_opcode_rb_operand_o_val = rb_operand;

        } else if (fetch_instr_mul_i_reg) {
            // Dispatch to multiplier
            mul_opcode_valid_o_val = 1;
            mul_opcode_opcode_o_val = instr;
            mul_opcode_pc_o_val = fetch_pc_i_reg;
            mul_opcode_invalid_o_val = fetch_instr_invalid_i_reg | has_fault;
            mul_opcode_rd_idx_o_val = rd;
            mul_opcode_ra_idx_o_val = rs1;
            mul_opcode_rb_idx_o_val = rs2;
            mul_opcode_ra_operand_o_val = ra_operand;
            mul_opcode_rb_operand_o_val = rb_operand;
            mul_rd_idx_reg = rd;
            mul_in_flight_reg = 1;

        } else if (fetch_instr_div_i_reg) {
            // Dispatch to divider
            div_opcode_valid_o_val = 1;
            div_rd_idx_reg = rd;
            div_in_flight_reg = 1;
        }
    } else {
        // No dispatch this cycle - still need to process regfile for writeback
        regfile.setRa0I(0);
        regfile.setRb0I(0);
        regfile.process();
    }
}

} // namespace gem5
