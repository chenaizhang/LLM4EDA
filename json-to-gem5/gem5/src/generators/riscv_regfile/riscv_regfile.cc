#include "generators/riscv_regfile/riscv_regfile.hh"

namespace gem5 {

RiscvRegfile::RiscvRegfile(const RiscvRegfileParams &params)
    : SimObject(params),
      supportRegfileXilinx(params.support_regfile_xilinx)
{
    for (int i = 0; i < NUM_REGS; i++) {
        regs[i] = 0;
    }

    ra0I = 0;
    rb0I = 0;
    rd0I = 0;
    rd0ValueI = 0;
    ra0ValueO = 0;
    rb0ValueO = 0;
}

void
RiscvRegfile::setRa0I(uint8_t val)
{
    ra0I = val;
}

void
RiscvRegfile::setRb0I(uint8_t val)
{
    rb0I = val;
}

void
RiscvRegfile::setRd0I(uint8_t val)
{
    rd0I = val;
}

void
RiscvRegfile::setRd0ValueI(uint32_t val)
{
    rd0ValueI = val;
}

uint32_t
RiscvRegfile::getRa0ValueO()
{
    return ra0ValueO;
}

uint32_t
RiscvRegfile::getRb0ValueO()
{
    return rb0ValueO;
}

void
RiscvRegfile::process()
{
    if (supportRegfileXilinx) {
        // Xilinx primitive path - relies on riscv_xilinx_2r1w submodule
        // Not implemented in standard register array mode
    } else {
        // Standard register array implementation with write-forwarding.
        // Read-before-write: compute read outputs (with forwarding) first,
        // then commit the write.

        // Read port A with forwarding
        if (ra0I == 0) {
            ra0ValueO = 0;
        } else if (rd0I != 0 && ra0I == rd0I) {
            ra0ValueO = rd0ValueI;
        } else {
            ra0ValueO = regs[ra0I];
        }

        // Read port B with forwarding
        if (rb0I == 0) {
            rb0ValueO = 0;
        } else if (rd0I != 0 && rb0I == rd0I) {
            rb0ValueO = rd0ValueI;
        } else {
            rb0ValueO = regs[rb0I];
        }

        // Write (x0 is hardwired to 0, skip write to x0)
        if (rd0I != 0) {
            regs[rd0I] = rd0ValueI;
        }
    }
}

} // namespace gem5
