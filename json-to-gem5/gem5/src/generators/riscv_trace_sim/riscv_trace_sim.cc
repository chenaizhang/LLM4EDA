#include "generators/riscv_trace_sim/riscv_trace_sim.hh"

#include "base/trace.hh"
#include "debug/RiscvTraceSim.hh"

namespace gem5 {

RiscvTraceSim::RiscvTraceSim(const RiscvTraceSimParams &p)
    : SimObject(p),
      valid_i_reg(0),
      pc_i_reg(0),
      opcode_i_reg(0),
      trace_count(0)
{
}

void
RiscvTraceSim::setValidI(uint32_t val)
{
    valid_i_reg = val;
}

void
RiscvTraceSim::setPcI(uint32_t val)
{
    pc_i_reg = val;
}

void
RiscvTraceSim::setOpcodeI(uint32_t val)
{
    opcode_i_reg = val;
}

void
RiscvTraceSim::process()
{
    if (valid_i_reg) {
        DPRINTF(RiscvTraceSim,
                "Trace: pc=0x%08x opcode=0x%08x count=%lu\n",
                pc_i_reg, opcode_i_reg, trace_count);
        trace_count++;
    }
}

} // namespace gem5
