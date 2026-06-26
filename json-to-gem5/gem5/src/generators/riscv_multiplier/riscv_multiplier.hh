#ifndef __GENERATORS_RISCV_MULTIPLIER_RISCV_MULTIPLIER_HH__
#define __GENERATORS_RISCV_MULTIPLIER_RISCV_MULTIPLIER_HH__

#include <cstdint>

#include "params/RiscvMultiplier.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvMultiplier : public SimObject
{
  private:
    // Input port registers
    uint32_t opcode_valid_i_reg;
    uint32_t opcode_invalid_i_reg;
    uint32_t opcode_opcode_i_reg;
    uint32_t opcode_pc_i_reg;
    uint32_t opcode_rd_idx_i_reg;
    uint32_t opcode_ra_idx_i_reg;
    uint32_t opcode_rb_idx_i_reg;
    uint32_t opcode_ra_operand_i_reg;
    uint32_t opcode_rb_operand_i_reg;
    uint32_t hold_i_reg;

    // Output port value
    uint32_t writeback_value_o_val;

    // Internal states for multi-cycle multiplication
    enum MultState {
        MULT_IDLE = 0,
        MULT_COMPUTE = 1,
        MULT_DONE = 2
    };

    // Multiplication operation types
    enum OpType {
        OP_MUL = 0,
        OP_MULH = 1,
        OP_MULHSU = 2,
        OP_MULHU = 3,
        OP_NONE = 4
    };

    // Multiplier state
    MultState mult_state;
    OpType op_type;
    uint32_t multiplicand;
    uint32_t multiplier_val;
    uint64_t partial_product;
    int cycle_count;

    // Decode operation type from funct3 field
    OpType decodeOpType(uint32_t funct3);

    // Compute final result based on operation type and sign correction
    void computeResult();

  public:
    RiscvMultiplier(const RiscvMultiplierParams &p);

    // Set functions for input ports
    void setOpcodeValidI(uint32_t val);
    void setOpcodeInvalidI(uint32_t val);
    void setOpcodeOpcodeI(uint32_t val);
    void setOpcodePcI(uint32_t val);
    void setOpcodeRdIdxI(uint32_t val);
    void setOpcodeRaIdxI(uint32_t val);
    void setOpcodeRbIdxI(uint32_t val);
    void setOpcodeRaOperandI(uint32_t val);
    void setOpcodeRbOperandI(uint32_t val);
    void setHoldI(uint32_t val);

    // Get functions for output ports
    uint32_t getWritebackValueO();

    // Process function called every cycle by parent module
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_MULTIPLIER_RISCV_MULTIPLIER_HH__
