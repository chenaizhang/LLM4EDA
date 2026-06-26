#include "generators/riscv_multiplier/riscv_multiplier.hh"

namespace gem5 {

RiscvMultiplier::RiscvMultiplier(const RiscvMultiplierParams &p)
    : SimObject(p),
      opcode_valid_i_reg(0),
      opcode_invalid_i_reg(0),
      opcode_opcode_i_reg(0),
      opcode_pc_i_reg(0),
      opcode_rd_idx_i_reg(0),
      opcode_ra_idx_i_reg(0),
      opcode_rb_idx_i_reg(0),
      opcode_ra_operand_i_reg(0),
      opcode_rb_operand_i_reg(0),
      hold_i_reg(0),
      writeback_value_o_val(0),
      mult_state(MULT_IDLE),
      op_type(OP_NONE),
      multiplicand(0),
      multiplier_val(0),
      partial_product(0),
      cycle_count(0)
{
}

void
RiscvMultiplier::setOpcodeValidI(uint32_t val)
{
    opcode_valid_i_reg = val;
}

void
RiscvMultiplier::setOpcodeInvalidI(uint32_t val)
{
    opcode_invalid_i_reg = val;
}

void
RiscvMultiplier::setOpcodeOpcodeI(uint32_t val)
{
    opcode_opcode_i_reg = val;
}

void
RiscvMultiplier::setOpcodePcI(uint32_t val)
{
    opcode_pc_i_reg = val;
}

void
RiscvMultiplier::setOpcodeRdIdxI(uint32_t val)
{
    opcode_rd_idx_i_reg = val;
}

void
RiscvMultiplier::setOpcodeRaIdxI(uint32_t val)
{
    opcode_ra_idx_i_reg = val;
}

void
RiscvMultiplier::setOpcodeRbIdxI(uint32_t val)
{
    opcode_rb_idx_i_reg = val;
}

void
RiscvMultiplier::setOpcodeRaOperandI(uint32_t val)
{
    opcode_ra_operand_i_reg = val;
}

void
RiscvMultiplier::setOpcodeRbOperandI(uint32_t val)
{
    opcode_rb_operand_i_reg = val;
}

void
RiscvMultiplier::setHoldI(uint32_t val)
{
    hold_i_reg = val;
}

uint32_t
RiscvMultiplier::getWritebackValueO()
{
    return writeback_value_o_val;
}

RiscvMultiplier::OpType
RiscvMultiplier::decodeOpType(uint32_t funct3)
{
    if (funct3 == 0) {
        return OP_MUL;
    } else if (funct3 == 1) {
        return OP_MULH;
    } else if (funct3 == 2) {
        return OP_MULHSU;
    } else if (funct3 == 3) {
        return OP_MULHU;
    } else {
        return OP_NONE;
    }
}

void
RiscvMultiplier::computeResult()
{
    uint32_t result = 0;

    if (op_type == OP_MUL) {
        // MUL: low 32 bits, same for signed and unsigned
        result = (uint32_t)(partial_product & 0xFFFFFFFF);
    } else if (op_type == OP_MULH) {
        // MULH: signed x signed, high 32 bits with sign correction
        uint64_t product = partial_product;
        if (((opcode_ra_operand_i_reg >> 31) & 1) != 0) {
            product -= (uint64_t)opcode_rb_operand_i_reg << 32;
        }
        if (((opcode_rb_operand_i_reg >> 31) & 1) != 0) {
            product -= (uint64_t)opcode_ra_operand_i_reg << 32;
        }
        result = (uint32_t)((product >> 32) & 0xFFFFFFFF);
    } else if (op_type == OP_MULHSU) {
        // MULHSU: signed x unsigned, high 32 bits with sign correction
        uint64_t product = partial_product;
        if (((opcode_ra_operand_i_reg >> 31) & 1) != 0) {
            product -= (uint64_t)opcode_rb_operand_i_reg << 32;
        }
        result = (uint32_t)((product >> 32) & 0xFFFFFFFF);
    } else if (op_type == OP_MULHU) {
        // MULHU: unsigned x unsigned, high 32 bits, no correction needed
        result = (uint32_t)((partial_product >> 32) & 0xFFFFFFFF);
    } else {
        result = 0;
    }

    writeback_value_o_val = result;
}

void
RiscvMultiplier::process()
{
    // Transition from DONE to IDLE at the start of the cycle
    // The output value remains stable until a new operation starts
    if (mult_state == MULT_DONE) {
        mult_state = MULT_IDLE;
    }

    // In IDLE state, check for a new multiplication request
    if (mult_state == MULT_IDLE) {
        if ((opcode_valid_i_reg & 1) != 0 &&
            (hold_i_reg & 1) == 0 &&
            (opcode_invalid_i_reg & 1) == 0) {
            // Decode operation type from funct3 field (bits 14:12)
            uint32_t funct3 = (opcode_opcode_i_reg >> 12) & 0x7;
            op_type = decodeOpType(funct3);

            // Initialize multiplication
            multiplicand = opcode_ra_operand_i_reg;
            multiplier_val = opcode_rb_operand_i_reg;
            partial_product = 0;
            cycle_count = 0;
            mult_state = MULT_COMPUTE;
        }
    }

    // In COMPUTE state, perform one iteration per cycle
    if (mult_state == MULT_COMPUTE && (hold_i_reg & 1) == 0) {
        // Shift-and-add multiplication: one bit per cycle
        if ((multiplier_val & 1) != 0) {
            partial_product += multiplicand;
        }
        multiplicand = multiplicand << 1;
        multiplier_val = multiplier_val >> 1;
        cycle_count++;

        // After 32 iterations, result is ready
        if (cycle_count >= 32) {
            computeResult();
            mult_state = MULT_DONE;
        }
    }
}

} // namespace gem5
