#ifndef __GENERATORS_RISCV_CORE_HH__
#define __GENERATORS_RISCV_CORE_HH__

#include <cstdint>

#include "params/RiscvCore.hh"
#include "sim/sim_object.hh"

#include "generators/riscv_fetch/riscv_fetch.hh"
#include "generators/riscv_decode/riscv_decode.hh"
#include "generators/riscv_decoder/riscv_decoder.hh"
#include "generators/riscv_issue/riscv_issue.hh"
#include "generators/riscv_exec/riscv_exec.hh"
#include "generators/riscv_lsu/riscv_lsu.hh"
#include "generators/riscv_csr/riscv_csr.hh"
#include "generators/riscv_multiplier/riscv_multiplier.hh"
#include "generators/riscv_divider/riscv_divider.hh"
#include "generators/riscv_mmu/riscv_mmu.hh"

namespace gem5 {

class RiscvCore : public SimObject
{
  private:
    // ---- Submodule references ----
    RiscvFetch &u_fetch;
    RiscvDecoder u_decoder;
    RiscvDecode u_decode;
    RiscvIssue &u_issue;
    RiscvExec &u_exec;
    RiscvLsu &u_lsu;
    RiscvCsr &u_csr;
    RiscvMultiplier &u_mul;
    RiscvDivider &u_div;
    RiscvMmu &u_mmu;

    // ---- Core parameters ----
    bool support_muldiv;
    bool support_super;
    bool support_mmu;
    bool support_load_bypass;
    bool support_mul_bypass;
    bool support_regfile_xilinx;
    uint32_t extra_decode_stage;
    uint32_t mem_cache_addr_min;
    uint32_t mem_cache_addr_max;

    // ---- External input registers (set by testbench) ----
    uint32_t rst_i_reg;
    uint32_t mem_d_accept_i_reg;
    uint32_t mem_d_ack_i_reg;
    uint32_t mem_d_error_i_reg;
    uint32_t mem_i_accept_i_reg;
    uint32_t mem_i_valid_i_reg;
    uint32_t mem_i_error_i_reg;
    uint32_t intr_i_reg;

    // ---- External output values (read by testbench) ----
    uint32_t mem_d_rd_o_val;
    uint32_t mem_d_cacheable_o_val;
    uint32_t mem_d_invalidate_o_val;
    uint32_t mem_d_writeback_o_val;
    uint32_t mem_d_flush_o_val;
    uint32_t mem_i_rd_o_val;
    uint32_t mem_i_flush_o_val;
    uint32_t mem_i_invalidate_o_val;

    // ---- Event ----
    EventFunctionWrapper coreEvent;

    // ---- Internal helper ----
    void resetCore();

  public:
    RiscvCore(const RiscvCoreParams &p);

    // ---- External input set functions ----
    void setRstI(uint32_t val);
    void setMemDAcceptI(uint32_t val);
    void setMemDAckI(uint32_t val);
    void setMemDErrorI(uint32_t val);
    void setMemIAcceptI(uint32_t val);
    void setMemIValidI(uint32_t val);
    void setMemIErrorI(uint32_t val);
    void setIntrI(uint32_t val);

    // ---- External output get functions ----
    uint32_t getMemDRdO();
    uint32_t getMemDCacheableO();
    uint32_t getMemDInvalidateO();
    uint32_t getMemDWritebackO();
    uint32_t getMemDFlushO();
    uint32_t getMemIRdO();
    uint32_t getMemIFlushO();
    uint32_t getMemIInvalidateO();

    // ---- Core process (called each cycle by event) ----
    void processEvent();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_CORE_HH__
