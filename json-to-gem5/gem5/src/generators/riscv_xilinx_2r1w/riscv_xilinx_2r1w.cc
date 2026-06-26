#include "generators/riscv_xilinx_2r1w/riscv_xilinx_2r1w.hh"

namespace gem5 {

RiscvXilinx2r1w::RiscvXilinx2r1w(const RiscvXilinx2r1wParams &params) :
    SimObject(params),
    ra_i_reg(0),
    rb_i_reg(0),
    rd0_i_reg(0),
    rd0_value_i_reg(0),
    ra_value_o_val(0),
    rb_value_o_val(0)
{
    // Initialize all memory entries to zero
    for (int i = 0; i < 16; i++) {
        mem[i] = 0;
    }
}

void
RiscvXilinx2r1w::setRaI(uint8_t val)
{
    ra_i_reg = val;
}

void
RiscvXilinx2r1w::setRbI(uint8_t val)
{
    rb_i_reg = val;
}

void
RiscvXilinx2r1w::setRd0I(uint8_t val)
{
    rd0_i_reg = val;
}

void
RiscvXilinx2r1w::setRd0ValueI(uint32_t val)
{
    rd0_value_i_reg = val;
}

uint32_t
RiscvXilinx2r1w::getRaValueO()
{
    return ra_value_o_val;
}

uint32_t
RiscvXilinx2r1w::getRbValueO()
{
    return rb_value_o_val;
}

void
RiscvXilinx2r1w::process()
{
    // Read ports (asynchronous / combinational - read before write)
    // Mask addresses to 4-bit range
    uint8_t ra = ra_i_reg & 0xF;
    uint8_t rb = rb_i_reg & 0xF;
    ra_value_o_val = mem[ra];
    rb_value_o_val = mem[rb];

    // Write port (synchronous - triggered by clock edge, i.e. process() call)
    uint8_t rd0 = rd0_i_reg & 0xF;
    mem[rd0] = rd0_value_i_reg;
}

} // namespace gem5
