#include "generators/riscv_lsu/riscv_lsu.hh"

#include <cassert>
#include <cstring>

namespace gem5 {

// RISC-V opcode bits [6:0]
static const uint32_t OPCODE_LOAD  = 0x03;
static const uint32_t OPCODE_STORE = 0x23;

// funct3 values for loads
static const uint32_t FUNCT3_LB  = 0;
static const uint32_t FUNCT3_LH  = 1;
static const uint32_t FUNCT3_LW  = 2;
static const uint32_t FUNCT3_LBU = 4;
static const uint32_t FUNCT3_LHU = 5;

// funct3 values for stores
static const uint32_t FUNCT3_SB = 0;
static const uint32_t FUNCT3_SH = 1;
static const uint32_t FUNCT3_SW = 2;

RiscvLsu::RiscvLsu(const RiscvLsuParams &params)
    : SimObject(params),
      lsu_state(STATE_IDLE),
      req_tag_counter(0),
      have_pending(false),
      request_accepted(false),
      fifo_capacity(params.fifo_depth),
      fifo_head(0),
      fifo_tail(0),
      fifo_count(0),
      opcode_valid_i_reg(0),
      opcode_invalid_i_reg(0),
      opcode_opcode_i_reg(0),
      opcode_pc_i_reg(0),
      opcode_rd_idx_i_reg(0),
      opcode_ra_idx_i_reg(0),
      opcode_rb_idx_i_reg(0),
      opcode_ra_operand_i_reg(0),
      opcode_rb_operand_i_reg(0),
      mem_data_rd_i_reg(0),
      mem_accept_i_reg(0),
      mem_ack_i_reg(0),
      mem_error_i_reg(0),
      mem_resp_tag_i_reg(0),
      mem_load_fault_i_reg(0),
      mem_store_fault_i_reg(0)
{
    fifo = new LsuRequest[fifo_capacity];
    std::memset(fifo, 0, fifo_capacity * sizeof(LsuRequest));
}

RiscvLsu::~RiscvLsu()
{
    delete[] fifo;
}

// ==================== Helper Functions ====================

uint32_t
RiscvLsu::getFunct3(uint32_t opcode)
{
    // funct3 is bits [14:12] of the instruction
    return ((opcode >> 12) & 0x7);
}

bool
RiscvLsu::isLoadOpcode(uint32_t opcode)
{
    // RISC-V LOAD opcode is 0x03 in bits [6:0]
    return ((opcode & 0x7f) == OPCODE_LOAD);
}

bool
RiscvLsu::isStoreOpcode(uint32_t opcode)
{
    // RISC-V STORE opcode is 0x23 in bits [6:0]
    return ((opcode & 0x7f) == OPCODE_STORE);
}

uint32_t
RiscvLsu::extractImmediate(uint32_t opcode, bool is_load)
{
    if (is_load) {
        // I-type: imm[11:0] = instr[31:20]
        uint32_t imm = (opcode >> 20) & 0xfff;
        // Sign extend from 12 bits to 32 bits
        if ((imm >> 11) & 1) {
            imm = imm | 0xfffff000;
        }
        return imm;
    } else {
        // S-type: imm[11:5] = instr[31:25], imm[4:0] = instr[11:7]
        uint32_t imm_hi = (opcode >> 25) & 0x7f;
        uint32_t imm_lo = (opcode >> 7) & 0x1f;
        uint32_t imm = (imm_hi << 5) | imm_lo;
        // Sign extend from 12 bits to 32 bits
        if ((imm >> 11) & 1) {
            imm = imm | 0xfffff000;
        }
        return imm;
    }
}

bool
RiscvLsu::checkAlignment(uint32_t addr, uint32_t funct3)
{
    if (funct3 == FUNCT3_LW || funct3 == FUNCT3_SW) {
        // Word access: must be 4-byte aligned
        return ((addr & 0x3) == 0);
    } else if (funct3 == FUNCT3_LH || funct3 == FUNCT3_LHU ||
               funct3 == FUNCT3_SH) {
        // Halfword access: must be 2-byte aligned
        return ((addr & 0x1) == 0);
    } else {
        // Byte access: always aligned
        return true;
    }
}

uint32_t
RiscvLsu::extractLoadData(uint32_t data, uint32_t funct3)
{
    if (funct3 == FUNCT3_LB) {
        // LB: load byte, sign extend
        uint32_t byte_val = data & 0xff;
        if ((byte_val >> 7) & 1) {
            byte_val = byte_val | 0xffffff00;
        }
        return byte_val;
    } else if (funct3 == FUNCT3_LH) {
        // LH: load halfword, sign extend
        uint32_t half_val = data & 0xffff;
        if ((half_val >> 15) & 1) {
            half_val = half_val | 0xffff0000;
        }
        return half_val;
    } else if (funct3 == FUNCT3_LW) {
        // LW: load word
        return data;
    } else if (funct3 == FUNCT3_LBU) {
        // LBU: load byte unsigned
        return (data & 0xff);
    } else if (funct3 == FUNCT3_LHU) {
        // LHU: load halfword unsigned
        return (data & 0xffff);
    } else {
        return data;
    }
}

uint32_t
RiscvLsu::prepareStoreData(uint32_t data, uint32_t funct3)
{
    if (funct3 == FUNCT3_SB) {
        // SB: store byte (replicate byte across all 4 byte lanes)
        uint32_t byte_val = data & 0xff;
        return byte_val | (byte_val << 8) | (byte_val << 16)
               | (byte_val << 24);
    } else if (funct3 == FUNCT3_SH) {
        // SH: store halfword (replicate halfword across both word halves)
        uint32_t half_val = data & 0xffff;
        return half_val | (half_val << 16);
    } else {
        // SW: store word
        return data;
    }
}

uint32_t
RiscvLsu::getMisalignException(bool is_load)
{
    if (is_load) {
        return EXC_LOAD_ADDR_MISALIGN;
    } else {
        return EXC_STORE_ADDR_MISALIGN;
    }
}

uint32_t
RiscvLsu::getFaultException(bool is_load)
{
    if (is_load) {
        return EXC_LOAD_ACCESS_FAULT;
    } else {
        return EXC_STORE_ACCESS_FAULT;
    }
}

// ==================== FIFO Functions ====================

void
RiscvLsu::pushFifo(const LsuRequest &req)
{
    if (fifo_count < fifo_capacity) {
        fifo[fifo_tail] = req;
        fifo_tail = (fifo_tail + 1) % fifo_capacity;
        fifo_count++;
    }
}

bool
RiscvLsu::popFifo(LsuRequest &req)
{
    if (fifo_count > 0) {
        req = fifo[fifo_head];
        fifo_head = (fifo_head + 1) % fifo_capacity;
        fifo_count--;
        return true;
    }
    return false;
}

bool
RiscvLsu::isFifoEmpty()
{
    return (fifo_count == 0);
}

bool
RiscvLsu::isFifoFull()
{
    return (fifo_count >= fifo_capacity);
}

// ==================== Set Input Functions ====================

void
RiscvLsu::setOpcodeValidI(uint32_t val)
{
    opcode_valid_i_reg = val & 1;
}

void
RiscvLsu::setOpcodeInvalidI(uint32_t val)
{
    opcode_invalid_i_reg = val & 1;
}

void
RiscvLsu::setOpcodeOpcodeI(uint32_t val)
{
    opcode_opcode_i_reg = val;
}

void
RiscvLsu::setOpcodePcI(uint32_t val)
{
    opcode_pc_i_reg = val;
}

void
RiscvLsu::setOpcodeRdIdxI(uint32_t val)
{
    opcode_rd_idx_i_reg = val & 0x1f;
}

void
RiscvLsu::setOpcodeRaIdxI(uint32_t val)
{
    opcode_ra_idx_i_reg = val & 0x1f;
}

void
RiscvLsu::setOpcodeRbIdxI(uint32_t val)
{
    opcode_rb_idx_i_reg = val & 0x1f;
}

void
RiscvLsu::setOpcodeRaOperandI(uint32_t val)
{
    opcode_ra_operand_i_reg = val;
}

void
RiscvLsu::setOpcodeRbOperandI(uint32_t val)
{
    opcode_rb_operand_i_reg = val;
}

void
RiscvLsu::setMemDataRdI(uint32_t val)
{
    mem_data_rd_i_reg = val;
}

void
RiscvLsu::setMemAcceptI(uint32_t val)
{
    mem_accept_i_reg = val & 1;
}

void
RiscvLsu::setMemAckI(uint32_t val)
{
    mem_ack_i_reg = val & 1;
}

void
RiscvLsu::setMemErrorI(uint32_t val)
{
    mem_error_i_reg = val & 1;
}

void
RiscvLsu::setMemRespTagI(uint32_t val)
{
    mem_resp_tag_i_reg = val;
}

void
RiscvLsu::setMemLoadFaultI(uint32_t val)
{
    mem_load_fault_i_reg = val & 1;
}

void
RiscvLsu::setMemStoreFaultI(uint32_t val)
{
    mem_store_fault_i_reg = val & 1;
}

// ==================== Get Output Functions ====================

uint32_t
RiscvLsu::getMemAddrO()
{
    return mem_addr_o_val;
}

uint32_t
RiscvLsu::getMemDataWrO()
{
    return mem_data_wr_o_val;
}

uint32_t
RiscvLsu::getMemRdO()
{
    return mem_rd_o_val;
}

uint32_t
RiscvLsu::getMemWrO()
{
    return mem_wr_o_val;
}

uint32_t
RiscvLsu::getMemCacheableO()
{
    return mem_cacheable_o_val;
}

uint32_t
RiscvLsu::getMemReqTagO()
{
    return mem_req_tag_o_val;
}

uint32_t
RiscvLsu::getMemInvalidateO()
{
    return mem_invalidate_o_val;
}

uint32_t
RiscvLsu::getMemWritebackO()
{
    return mem_writeback_o_val;
}

uint32_t
RiscvLsu::getMemFlushO()
{
    return mem_flush_o_val;
}

uint32_t
RiscvLsu::getWritebackValidO()
{
    return writeback_valid_o_val;
}

uint32_t
RiscvLsu::getWritebackValueO()
{
    return writeback_value_o_val;
}

uint32_t
RiscvLsu::getWritebackExceptionO()
{
    return writeback_exception_o_val;
}

uint32_t
RiscvLsu::getStallO()
{
    return stall_o_val;
}

// ==================== Core Functions ====================

void
RiscvLsu::setDefaultOutputs()
{
    mem_addr_o_val = 0;
    mem_data_wr_o_val = 0;
    mem_rd_o_val = 0;
    mem_wr_o_val = 0;
    mem_cacheable_o_val = 0;
    mem_req_tag_o_val = 0;
    mem_invalidate_o_val = 0;
    mem_writeback_o_val = 0;
    mem_flush_o_val = 0;
    writeback_valid_o_val = 0;
    writeback_value_o_val = 0;
    writeback_exception_o_val = 0;
    stall_o_val = 0;
}

void
RiscvLsu::issueRequest(const LsuRequest &req)
{
    mem_addr_o_val = req.addr;
    mem_req_tag_o_val = req.tag;
    mem_cacheable_o_val = 1;

    if (req.is_load) {
        mem_rd_o_val = 1;
        mem_wr_o_val = 0;
    } else {
        mem_rd_o_val = 0;
        mem_wr_o_val = 1;
        mem_data_wr_o_val = req.store_data;
    }

    // Store as pending
    pending_req = req;
    have_pending = true;
    request_accepted = false;
    lsu_state = STATE_ACCEPT;
    stall_o_val = 1;
}

void
RiscvLsu::processResponse()
{
    bool has_exception = false;
    uint32_t exception_code = 0;
    uint32_t writeback_data = 0;

    // Check for memory faults
    if (pending_req.is_load && mem_load_fault_i_reg) {
        exception_code = EXC_LOAD_PAGE_FAULT;
        has_exception = true;
    } else if (!pending_req.is_load && mem_store_fault_i_reg) {
        exception_code = EXC_STORE_PAGE_FAULT;
        has_exception = true;
    } else if (mem_error_i_reg) {
        exception_code = getFaultException(pending_req.is_load);
        has_exception = true;
    } else if (pending_req.is_load) {
        // Extract load data based on funct3
        writeback_data = extractLoadData(mem_data_rd_i_reg,
                                         pending_req.funct3);
    }

    if (has_exception) {
        writeback_exception_o_val = exception_code;
    } else {
        writeback_value_o_val = writeback_data;
    }

    writeback_valid_o_val = 1;
    have_pending = false;
    lsu_state = STATE_IDLE;
    stall_o_val = 0;
}

void
RiscvLsu::process()
{
    setDefaultOutputs();

    // ========== State machine ==========

    if (lsu_state == STATE_ACCEPT) {
        // Waiting for memory to accept the request
        if (mem_accept_i_reg) {
            request_accepted = true;
            lsu_state = STATE_WAIT_RESP;

            // Check if response also arrives in the same cycle
            if (mem_ack_i_reg &&
                mem_resp_tag_i_reg == pending_req.tag) {
                processResponse();
            } else {
                stall_o_val = 1;
            }
        } else {
            stall_o_val = 1;
        }
    } else if (lsu_state == STATE_WAIT_RESP) {
        // Waiting for memory response
        stall_o_val = 1;

        if (mem_ack_i_reg &&
            mem_resp_tag_i_reg == pending_req.tag) {
            processResponse();
        }
    } else {
        // STATE_IDLE: Check memory response for any outstanding req
        if (have_pending && mem_ack_i_reg &&
            mem_resp_tag_i_reg == pending_req.tag) {
            processResponse();
        }
    }

    // ========== Accept new request ==========
    // In IDLE state after handling any response,
    // check FIFO for pending requests or accept new one directly

    if (lsu_state == STATE_IDLE && !have_pending) {
        // Try to process next request from FIFO
        LsuRequest next_req;
        bool has_request = false;

        if (!isFifoEmpty()) {
            has_request = popFifo(next_req);
        } else if (opcode_valid_i_reg) {
            // Direct new request
            next_req.opcode = opcode_opcode_i_reg;
            next_req.pc = opcode_pc_i_reg;
            next_req.rd_idx = opcode_rd_idx_i_reg;
            next_req.funct3 = getFunct3(opcode_opcode_i_reg);
            next_req.is_load = isLoadOpcode(opcode_opcode_i_reg);
            next_req.tag = req_tag_counter;

            uint32_t imm = extractImmediate(opcode_opcode_i_reg,
                                            next_req.is_load);
            next_req.addr = opcode_ra_operand_i_reg + imm;
            next_req.store_data = prepareStoreData(
                opcode_rb_operand_i_reg, next_req.funct3);

            has_request = true;
        }

        if (has_request) {
            // Check for alignment error
            if (checkAlignment(next_req.addr, next_req.funct3)) {
                req_tag_counter++;
                issueRequest(next_req);
            } else {
                // Alignment error, writeback exception
                writeback_exception_o_val =
                    getMisalignException(next_req.is_load);
                writeback_valid_o_val = 1;
                stall_o_val = 0;
            }
        }
    }

    // ========== Push new requests to FIFO ==========
    // If we have a valid opcode and we're not processing it directly above
    // (i.e., we're busy or the FIFO already had entries)

    if (opcode_valid_i_reg) {
        bool already_handled = false;

        // Check if this was the request we just handled directly
        if (lsu_state == STATE_IDLE && !have_pending && isFifoEmpty()) {
            already_handled = true;
        }

        if (!already_handled && !isFifoFull()) {
            LsuRequest new_req;
            new_req.opcode = opcode_opcode_i_reg;
            new_req.pc = opcode_pc_i_reg;
            new_req.rd_idx = opcode_rd_idx_i_reg;
            new_req.funct3 = getFunct3(opcode_opcode_i_reg);
            new_req.is_load = isLoadOpcode(opcode_opcode_i_reg);
            new_req.tag = req_tag_counter;

            uint32_t imm = extractImmediate(opcode_opcode_i_reg,
                                            new_req.is_load);
            new_req.addr = opcode_ra_operand_i_reg + imm;
            new_req.store_data = prepareStoreData(
                opcode_rb_operand_i_reg, new_req.funct3);

            if (!checkAlignment(new_req.addr, new_req.funct3)) {
                // Alignment error on FIFO push, writeback directly
                writeback_exception_o_val =
                    getMisalignException(new_req.is_load);
                writeback_valid_o_val = 1;
            } else {
                req_tag_counter++;
                pushFifo(new_req);
            }
        } else if (!already_handled && isFifoFull()) {
            // FIFO full: stall
            stall_o_val = 1;
        }
    }

    // ========== Handle opcode_invalid_i ==========
    if (opcode_invalid_i_reg) {
        // Opcode is illegal, we just forward the exception
        writeback_exception_o_val = 2; // Illegal instruction
        writeback_valid_o_val = 1;
    }
}

void
RiscvLsu::reset()
{
    lsu_state = STATE_IDLE;
    req_tag_counter = 0;
    have_pending = false;
    request_accepted = false;
    fifo_head = 0;
    fifo_tail = 0;
    fifo_count = 0;

    opcode_valid_i_reg = 0;
    opcode_invalid_i_reg = 0;
    opcode_opcode_i_reg = 0;
    opcode_pc_i_reg = 0;
    opcode_rd_idx_i_reg = 0;
    opcode_ra_idx_i_reg = 0;
    opcode_rb_idx_i_reg = 0;
    opcode_ra_operand_i_reg = 0;
    opcode_rb_operand_i_reg = 0;
    mem_data_rd_i_reg = 0;
    mem_accept_i_reg = 0;
    mem_ack_i_reg = 0;
    mem_error_i_reg = 0;
    mem_resp_tag_i_reg = 0;
    mem_load_fault_i_reg = 0;
    mem_store_fault_i_reg = 0;

    setDefaultOutputs();
}

} // namespace gem5
