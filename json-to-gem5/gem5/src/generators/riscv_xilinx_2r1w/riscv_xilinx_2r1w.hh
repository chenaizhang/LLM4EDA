#ifndef __GENERATORS_RISCV_XILINX_2R1W_HH__
#define __GENERATORS_RISCV_XILINX_2R1W_HH__

#include <cstdint>

#include "params/RiscvXilinx2r1w.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvXilinx2r1w : public SimObject
{
  private:
    // Input registers (latched by set functions)
    uint8_t ra_i_reg;
    uint8_t rb_i_reg;
    uint8_t rd0_i_reg;
    uint32_t rd0_value_i_reg;

    // Output values (read by parent via get functions)
    uint32_t ra_value_o_val;
    uint32_t rb_value_o_val;

    // Memory array: 16 entries, 32 bits each
    uint32_t mem[16];

  public:
    RiscvXilinx2r1w(const RiscvXilinx2r1wParams &params);

    // Input set functions
    void setRaI(uint8_t val);
    void setRbI(uint8_t val);
    void setRd0I(uint8_t val);
    void setRd0ValueI(uint32_t val);

    // Output get functions
    uint32_t getRaValueO();
    uint32_t getRbValueO();

    // Process function - called by parent each clock cycle
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_XILINX_2R1W_HH__
