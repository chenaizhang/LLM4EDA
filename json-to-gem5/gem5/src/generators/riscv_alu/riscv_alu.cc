#include "generators/riscv_alu/riscv_alu.hh"

namespace gem5 {

RiscvAlu::RiscvAlu(const RiscvAluParams &p)
    : SimObject(p),
      alu_a_i_reg(0),
      alu_b_i_reg(0),
      alu_op_i_reg(0),
      alu_p_o_val(0)
{
}

void
RiscvAlu::setAluA(uint32_t val)
{
    alu_a_i_reg = val;
}

void
RiscvAlu::setAluB(uint32_t val)
{
    alu_b_i_reg = val;
}

void
RiscvAlu::setAluOp(uint8_t val)
{
    alu_op_i_reg = val;
}

uint32_t
RiscvAlu::getAluP()
{
    return alu_p_o_val;
}

void
RiscvAlu::process()
{
    uint32_t result = 0;
    uint8_t op = alu_op_i_reg;

    if (op == ALU_NONE) {
        result = alu_a_i_reg;
    } else if (op == ALU_SHIFTL) {
        // Barrel shifter: 5-stage left shift (1/2/4/8/16)
        uint32_t shamt = alu_b_i_reg & 0x1F;
        uint32_t temp = alu_a_i_reg;
        if ((shamt >> 0) & 1) {
            temp = temp << 1;
        }
        if ((shamt >> 1) & 1) {
            temp = temp << 2;
        }
        if ((shamt >> 2) & 1) {
            temp = temp << 4;
        }
        if ((shamt >> 3) & 1) {
            temp = temp << 8;
        }
        if ((shamt >> 4) & 1) {
            temp = temp << 16;
        }
        result = temp;
    } else if (op == ALU_SHIFTR) {
        // Barrel shifter: 5-stage logical right shift (1/2/4/8/16)
        uint32_t shamt = alu_b_i_reg & 0x1F;
        uint32_t temp = alu_a_i_reg;
        if ((shamt >> 0) & 1) {
            temp = temp >> 1;
        }
        if ((shamt >> 1) & 1) {
            temp = temp >> 2;
        }
        if ((shamt >> 2) & 1) {
            temp = temp >> 4;
        }
        if ((shamt >> 3) & 1) {
            temp = temp >> 8;
        }
        if ((shamt >> 4) & 1) {
            temp = temp >> 16;
        }
        result = temp;
    } else if (op == ALU_SHIFTR_ARITH) {
        // Barrel shifter: 5-stage arithmetic right shift (1/2/4/8/16)
        uint32_t shamt = alu_b_i_reg & 0x1F;
        int32_t temp = static_cast<int32_t>(alu_a_i_reg);
        if ((shamt >> 0) & 1) {
            temp = temp >> 1;
        }
        if ((shamt >> 1) & 1) {
            temp = temp >> 2;
        }
        if ((shamt >> 2) & 1) {
            temp = temp >> 4;
        }
        if ((shamt >> 3) & 1) {
            temp = temp >> 8;
        }
        if ((shamt >> 4) & 1) {
            temp = temp >> 16;
        }
        result = static_cast<uint32_t>(temp);
    } else if (op == ALU_ADD) {
        result = alu_a_i_reg + alu_b_i_reg;
    } else if (op == ALU_SUB) {
        result = alu_a_i_reg - alu_b_i_reg;
    } else if (op == ALU_AND) {
        result = alu_a_i_reg & alu_b_i_reg;
    } else if (op == ALU_OR) {
        result = alu_a_i_reg | alu_b_i_reg;
    } else if (op == ALU_XOR) {
        result = alu_a_i_reg ^ alu_b_i_reg;
    } else if (op == ALU_LESS_THAN) {
        // Unsigned comparison
        if (alu_a_i_reg < alu_b_i_reg) {
            result = 1;
        } else {
            result = 0;
        }
    } else if (op == ALU_LESS_THAN_SIGNED) {
        // Signed comparison
        if (static_cast<int32_t>(alu_a_i_reg) <
            static_cast<int32_t>(alu_b_i_reg)) {
            result = 1;
        } else {
            result = 0;
        }
    } else {
        // Default: passthrough
        result = alu_a_i_reg;
    }

    alu_p_o_val = result;
}

} // namespace gem5
