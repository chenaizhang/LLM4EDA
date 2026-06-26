#ifndef __GENERATORS_RISCV_ALU_HH__
#define __GENERATORS_RISCV_ALU_HH__

#include <cstdint>

#include "params/RiscvAlu.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvAlu : public SimObject
{
  private:
    // Input port registers
    uint32_t alu_a_i_reg;
    uint32_t alu_b_i_reg;
    uint8_t alu_op_i_reg;

    // Output port value
    uint32_t alu_p_o_val;

    // ALU operation codes
    static constexpr uint8_t ALU_NONE = 0x0;
    static constexpr uint8_t ALU_SHIFTL = 0x1;
    static constexpr uint8_t ALU_SHIFTR = 0x2;
    static constexpr uint8_t ALU_SHIFTR_ARITH = 0x3;
    static constexpr uint8_t ALU_ADD = 0x4;
    static constexpr uint8_t ALU_SUB = 0x6;
    static constexpr uint8_t ALU_AND = 0x7;
    static constexpr uint8_t ALU_OR = 0x8;
    static constexpr uint8_t ALU_XOR = 0x9;
    static constexpr uint8_t ALU_LESS_THAN = 0xA;
    static constexpr uint8_t ALU_LESS_THAN_SIGNED = 0xB;

  public:
    RiscvAlu(const RiscvAluParams &p);

    // Set functions for input ports
    void setAluA(uint32_t val);
    void setAluB(uint32_t val);
    void setAluOp(uint8_t val);

    // Get function for output port
    uint32_t getAluP();

    // Process function - combinational logic, called by parent module
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_ALU_HH__
