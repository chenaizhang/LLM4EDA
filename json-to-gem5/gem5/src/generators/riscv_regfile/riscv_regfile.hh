#ifndef __GENERATORS_RISCV_REGFILE_HH__
#define __GENERATORS_RISCV_REGFILE_HH__

#include <cstdint>

#include "params/RiscvRegfile.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvRegfile : public SimObject
{
  private:
    static constexpr int NUM_REGS = 32;

    /** Register file storage */
    uint32_t regs[NUM_REGS];

    /** Input registers */
    uint8_t ra0I;
    uint8_t rb0I;
    uint8_t rd0I;
    uint32_t rd0ValueI;

    /** Output values */
    uint32_t ra0ValueO;
    uint32_t rb0ValueO;

    /** Parameter: use Xilinx 2R1W primitive */
    bool supportRegfileXilinx;

  public:
    RiscvRegfile(const RiscvRegfileParams &p);

    /** Input port set functions */
    void setRa0I(uint8_t val);
    void setRb0I(uint8_t val);
    void setRd0I(uint8_t val);
    void setRd0ValueI(uint32_t val);

    /** Output port get functions */
    uint32_t getRa0ValueO();
    uint32_t getRb0ValueO();

    /**
     * Process function.
     * Called by parent module (riscv_issue) each cycle.
     * Performs read-before-write with RAW forwarding.
     */
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_REGFILE_HH__
