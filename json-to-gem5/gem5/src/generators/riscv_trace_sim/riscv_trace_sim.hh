#ifndef __GENERATORS_RISCV_TRACE_SIM_HH__
#define __GENERATORS_RISCV_TRACE_SIM_HH__

#include "params/RiscvTraceSim.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvTraceSim : public SimObject
{
  private:
    // Input port registers
    uint32_t valid_i_reg;
    uint32_t pc_i_reg;
    uint32_t opcode_i_reg;

    // Internal state: trace entry count
    uint64_t trace_count;

  public:
    RiscvTraceSim(const RiscvTraceSimParams &p);

    // Set functions for input ports
    void setValidI(uint32_t val);
    void setPcI(uint32_t val);
    void setOpcodeI(uint32_t val);

    // Process function - called by parent module each cycle
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_TRACE_SIM_HH__
