#include "generators/riscv_core/riscv_core.hh"

#include "base/trace.hh"
#include "debug/DUT.hh"
#include "debug/TestGenerator.hh"

namespace gem5 {

// ==================== Constructor ====================
RiscvCore::RiscvCore(const RiscvCoreParams &params)
    : SimObject(params),
      // SimObject submodule references (from params)
      u_fetch(*params.fetch),
      u_issue(*params.issue),
      u_exec(*params.exec),
      u_lsu(*params.lsu),
      u_csr(*params.csr),
      u_mul(*params.mul),
      u_div(*params.div),
      u_mmu(*params.mmu),
      // Non-SimObject submodules (created manually)
      u_decoder(),
      u_decode(params.extra_decode_stage ? 1 : 0, &u_decoder),
      // Core parameters
      support_muldiv(params.support_muldiv),
      support_super(params.support_super),
      support_mmu(params.support_mmu),
      support_load_bypass(params.support_load_bypass),
      support_mul_bypass(params.support_mul_bypass),
      support_regfile_xilinx(params.support_regfile_xilinx),
      extra_decode_stage(params.extra_decode_stage ? 1 : 0),
      mem_cache_addr_min(params.mem_cache_addr_min),
      mem_cache_addr_max(params.mem_cache_addr_max),
      // External input registers (init to 0)
      rst_i_reg(0),
      mem_d_accept_i_reg(0),
      mem_d_ack_i_reg(0),
      mem_d_error_i_reg(0),
      mem_i_accept_i_reg(0),
      mem_i_valid_i_reg(0),
      mem_i_error_i_reg(0),
      intr_i_reg(0),
      // External output values (init to 0)
      mem_d_rd_o_val(0),
      mem_d_cacheable_o_val(0),
      mem_d_invalidate_o_val(0),
      mem_d_writeback_o_val(0),
      mem_d_flush_o_val(0),
      mem_i_rd_o_val(0),
      mem_i_flush_o_val(0),
      mem_i_invalidate_o_val(0),
      // Event
      coreEvent([this]() { processEvent(); }, name())
{
    DPRINTF(DUT, "Created RiscvCore (extra_decode_stage=%d, "
            "support_muldiv=%d, support_mmu=%d)\n",
            params.extra_decode_stage, params.support_muldiv,
            params.support_mmu);

    // Schedule the first event
    if (!coreEvent.scheduled()) {
        schedule(coreEvent, curTick());
    }
}

// ==================== External Input Set Functions ====================

void
RiscvCore::setRstI(uint32_t val)
{
    rst_i_reg = val & 0x1;
}

void
RiscvCore::setMemDAcceptI(uint32_t val)
{
    mem_d_accept_i_reg = val & 0x1;
}

void
RiscvCore::setMemDAckI(uint32_t val)
{
    mem_d_ack_i_reg = val & 0x1;
}

void
RiscvCore::setMemDErrorI(uint32_t val)
{
    mem_d_error_i_reg = val & 0x1;
}

void
RiscvCore::setMemIAcceptI(uint32_t val)
{
    mem_i_accept_i_reg = val & 0x1;
}

void
RiscvCore::setMemIValidI(uint32_t val)
{
    mem_i_valid_i_reg = val & 0x1;
}

void
RiscvCore::setMemIErrorI(uint32_t val)
{
    mem_i_error_i_reg = val & 0x1;
}

void
RiscvCore::setIntrI(uint32_t val)
{
    intr_i_reg = val & 0x1;
}

// ==================== External Output Get Functions ====================

uint32_t
RiscvCore::getMemDRdO()
{
    return mem_d_rd_o_val;
}

uint32_t
RiscvCore::getMemDCacheableO()
{
    return mem_d_cacheable_o_val;
}

uint32_t
RiscvCore::getMemDInvalidateO()
{
    return mem_d_invalidate_o_val;
}

uint32_t
RiscvCore::getMemDWritebackO()
{
    return mem_d_writeback_o_val;
}

uint32_t
RiscvCore::getMemDFlushO()
{
    return mem_d_flush_o_val;
}

uint32_t
RiscvCore::getMemIRdO()
{
    return mem_i_rd_o_val;
}

uint32_t
RiscvCore::getMemIFlushO()
{
    return mem_i_flush_o_val;
}

uint32_t
RiscvCore::getMemIInvalidateO()
{
    return mem_i_invalidate_o_val;
}

// ==================== Reset Helper ====================

void
RiscvCore::resetCore()
{
    // Zero out all external output values
    mem_d_rd_o_val = 0;
    mem_d_cacheable_o_val = 0;
    mem_d_invalidate_o_val = 0;
    mem_d_writeback_o_val = 0;
    mem_d_flush_o_val = 0;
    mem_i_rd_o_val = 0;
    mem_i_flush_o_val = 0;
    mem_i_invalidate_o_val = 0;

    DPRINTF(DUT, "RiscvCore reset\n");
}

// ==================== Main Process (called each cycle) ====================

void
RiscvCore::processEvent()
{
    // ---- Handle reset ----
    if (rst_i_reg) {
        resetCore();
        if (!coreEvent.scheduled()) {
            schedule(coreEvent, curTick() + 1);
        }
        return;
    }

    // ================================================================
    // Phase 1: Set external memory response inputs to MMU
    // ================================================================
    // Instruction-side memory response
    u_mmu.setFetchOutAcceptI(mem_i_accept_i_reg ? true : false);
    u_mmu.setFetchOutValidI(mem_i_valid_i_reg ? true : false);
    u_mmu.setFetchOutErrorI(mem_i_error_i_reg ? true : false);
    // No external instruction data port; MMU will read zeros if no valid data

    // Data-side memory response
    u_mmu.setLsuOutAcceptI(mem_d_accept_i_reg ? true : false);
    u_mmu.setLsuOutAckI(mem_d_ack_i_reg ? true : false);
    u_mmu.setLsuOutErrorI(mem_d_error_i_reg ? true : false);

    // ================================================================
    // Phase 2: Set CSR->MMU control inputs (from previous cycle CSR output)
    // ================================================================
    u_mmu.setPrivDI(u_csr.getMmuPrivDO());
    u_mmu.setSumI(u_csr.getMmuSumO());
    u_mmu.setMxrI(u_csr.getMmuMxrO());
    u_mmu.setFlushI(u_csr.getMmuFlushO());
    u_mmu.setSatpI(u_csr.getMmuSatpO());

    // ================================================================
    // Phase 3: Set Fetch icache inputs (from previous cycle MMU output)
    // ================================================================
    u_fetch.setIcacheAcceptI(u_mmu.getFetchInAcceptO() ? 1 : 0);
    u_fetch.setIcacheValidI(u_mmu.getFetchInValidO() ? 1 : 0);
    u_fetch.setIcacheErrorI(u_mmu.getFetchInErrorO() ? 1 : 0);
    u_fetch.setIcacheInstI(u_mmu.getFetchInInstO());
    u_fetch.setIcachePageFaultI(u_mmu.getFetchInFaultO() ? 1 : 0);

    // ================================================================
    // Phase 4: Set Fetch control inputs
    // ================================================================
    // Decode back-pressure (previous cycle decode output -> fetch accept)
    u_fetch.setFetchAcceptI(u_decode.getFetchInAcceptO());

    // Branch redirect from Issue (previous cycle issue output)
    u_fetch.setBranchRequestI(u_issue.getBranchRequestO());
    u_fetch.setBranchPcI(u_issue.getBranchPcO());
    u_fetch.setBranchPrivI(u_issue.getBranchPrivO());

    // Fetch invalidate (branch taken or interrupt taken)
    uint32_t fetch_invalidate = 0;
    if (u_issue.getBranchRequestO() || u_csr.getTakeInterruptO()) {
        fetch_invalidate = 1;
    }
    u_fetch.setFetchInvalidateI(fetch_invalidate);

    // ================================================================
    // Phase 5: Process Fetch
    // ================================================================
    u_fetch.process();

    // ================================================================
    // Phase 6: Set Decode inputs from Fetch outputs
    // ================================================================
    u_decode.setFetchInValidI(u_fetch.getFetchValidO());
    u_decode.setFetchInInstrI(u_fetch.getFetchInstrO());
    u_decode.setFetchInPcI(u_fetch.getFetchPcO());
    u_decode.setFetchInFaultFetchI(u_fetch.getFetchFaultFetchO());
    u_decode.setFetchInFaultPageI(u_fetch.getFetchFaultPageO());
    u_decode.setSquashDecodeI(u_fetch.getSquashDecodeO());

    // Issue back-pressure to Decode
    u_decode.setFetchOutAcceptI(u_issue.getFetchAcceptO());

    // ================================================================
    // Phase 7: Process Decode (includes decoder combinational logic)
    // ================================================================
    u_decode.process();

    // ================================================================
    // Phase 8: Set Issue inputs from Decode outputs
    // ================================================================
    u_issue.setFetchValidI(u_decode.getFetchOutValidO());
    u_issue.setFetchInstrI(u_decode.getFetchOutInstrO());
    u_issue.setFetchPcI(u_decode.getFetchOutPcO());
    u_issue.setFetchFaultFetchI(u_decode.getFetchOutFaultFetchO());
    u_issue.setFetchFaultPageI(u_decode.getFetchOutFaultPageO());
    u_issue.setFetchInstrExecI(u_decode.getFetchOutInstrExecO());
    u_issue.setFetchInstrLsuI(u_decode.getFetchOutInstrLsuO());
    u_issue.setFetchInstrBranchI(u_decode.getFetchOutInstrBranchO());
    u_issue.setFetchInstrMulI(u_decode.getFetchOutInstrMulO());
    u_issue.setFetchInstrDivI(u_decode.getFetchOutInstrDivO());
    u_issue.setFetchInstrCsrI(u_decode.getFetchOutInstrCsrO());
    u_issue.setFetchInstrRdValidI(u_decode.getFetchOutInstrRdValidO());
    u_issue.setFetchInstrInvalidI(u_decode.getFetchOutInstrInvalidO());

    // ================================================================
    // Phase 9: Set Issue branch feedback inputs (from previous cycle)
    // ================================================================
    // Branch feedback from Exec
    u_issue.setBranchExecRequestI(u_exec.getBranchRequest());
    u_issue.setBranchExecIsTakenI(u_exec.getBranchIsTaken());
    u_issue.setBranchExecIsNotTakenI(u_exec.getBranchIsNotTaken());
    u_issue.setBranchExecSourceI(u_exec.getBranchSource());
    u_issue.setBranchExecIsCallI(u_exec.getBranchIsCall());
    u_issue.setBranchExecIsRetI(u_exec.getBranchIsRet());
    u_issue.setBranchExecIsJmpI(u_exec.getBranchIsJmp());
    u_issue.setBranchExecPcI(u_exec.getBranchPc());
    u_issue.setBranchDExecRequestI(u_exec.getBranchDRequest());
    u_issue.setBranchDExecPcI(u_exec.getBranchDPc());
    u_issue.setBranchDExecPrivI(u_exec.getBranchDPriv());

    // Branch feedback from CSR
    u_issue.setBranchCsrRequestI(u_csr.getBranchCsrRequestO());
    u_issue.setBranchCsrPcI(u_csr.getBranchCsrPcO());
    u_issue.setBranchCsrPrivI(u_csr.getBranchCsrPrivO());

    // ================================================================
    // Phase 10: Set Issue writeback inputs (from previous cycle)
    // ================================================================
    u_issue.setWritebackExecValueI(u_exec.getWritebackValue());
    u_issue.setWritebackMemValidI(u_lsu.getWritebackValidO());
    u_issue.setWritebackMemValueI(u_lsu.getWritebackValueO());
    u_issue.setWritebackMemExceptionI(u_lsu.getWritebackExceptionO());
    u_issue.setWritebackMulValueI(u_mul.getWritebackValueO());
    u_issue.setWritebackDivValidI(u_div.getWritebackValidO());
    u_issue.setWritebackDivValueI(u_div.getWritebackValueO());

    // ================================================================
    // Phase 11: Set Issue CSR result inputs (from previous cycle)
    // ================================================================
    u_issue.setCsrResultE1ValueI(u_csr.getCsrResultE1ValueO());
    u_issue.setCsrResultE1WriteI(u_csr.getCsrResultE1WriteO());
    u_issue.setCsrResultE1WdataI(u_csr.getCsrResultE1WdataO());
    u_issue.setCsrResultE1ExceptionI(u_csr.getCsrResultE1ExceptionO());

    // ================================================================
    // Phase 12: Set Issue control inputs
    // ================================================================
    u_issue.setLsuStallI(u_lsu.getStallO());
    u_issue.setTakeInterruptI(u_csr.getTakeInterruptO());

    // ================================================================
    // Phase 13: Process Issue
    // ================================================================
    u_issue.process();

    // ================================================================
    // Phase 14: Set Exec inputs from Issue outputs
    // ================================================================
    u_exec.setOpcodeValid(u_issue.getExecOpcodeValidO());
    u_exec.setOpcodeOpcode(u_issue.getOpcodeOpcodeO());
    u_exec.setOpcodePc(u_issue.getOpcodePcO());
    u_exec.setOpcodeInvalid(u_issue.getOpcodeInvalidO());
    u_exec.setOpcodeRdIdx(u_issue.getOpcodeRdIdxO());
    u_exec.setOpcodeRaIdx(u_issue.getOpcodeRaIdxO());
    u_exec.setOpcodeRbIdx(u_issue.getOpcodeRbIdxO());
    u_exec.setOpcodeRaOperand(u_issue.getOpcodeRaOperandO());
    u_exec.setOpcodeRbOperand(u_issue.getOpcodeRbOperandO());
    u_exec.setHold(u_issue.getExecHoldO());

    // ================================================================
    // Phase 15: Process Exec
    // ================================================================
    u_exec.process();

    // ================================================================
    // Phase 16: Set LSU inputs from Issue outputs + MMU responses
    // ================================================================
    u_lsu.setOpcodeValidI(u_issue.getLsuOpcodeValidO());
    u_lsu.setOpcodeInvalidI(u_issue.getLsuOpcodeInvalidO());
    u_lsu.setOpcodeOpcodeI(u_issue.getLsuOpcodeOpcodeO());
    u_lsu.setOpcodePcI(u_issue.getLsuOpcodePcO());
    u_lsu.setOpcodeRdIdxI(u_issue.getLsuOpcodeRdIdxO());
    u_lsu.setOpcodeRaIdxI(u_issue.getLsuOpcodeRaIdxO());
    u_lsu.setOpcodeRbIdxI(u_issue.getLsuOpcodeRbIdxO());
    u_lsu.setOpcodeRaOperandI(u_issue.getLsuOpcodeRaOperandO());
    u_lsu.setOpcodeRbOperandI(u_issue.getLsuOpcodeRbOperandO());

    // Memory response from MMU (data side)
    u_lsu.setMemDataRdI(u_mmu.getLsuInDataRdO());
    u_lsu.setMemAcceptI(u_mmu.getLsuInAcceptO() ? 1 : 0);
    u_lsu.setMemAckI(u_mmu.getLsuInAckO() ? 1 : 0);
    u_lsu.setMemErrorI(u_mmu.getLsuInErrorO() ? 1 : 0);
    u_lsu.setMemRespTagI(u_mmu.getLsuInRespTagO());
    u_lsu.setMemLoadFaultI(u_mmu.getLsuInLoadFaultO() ? 1 : 0);
    u_lsu.setMemStoreFaultI(u_mmu.getLsuInStoreFaultO() ? 1 : 0);

    // ================================================================
    // Phase 17: Process LSU
    // ================================================================
    u_lsu.process();

    // ================================================================
    // Phase 18: Set CSR inputs from Issue outputs
    // ================================================================
    u_csr.setOpcodeValidI(u_issue.getCsrOpcodeValidO());
    u_csr.setOpcodeOpcodeI(u_issue.getCsrOpcodeOpcodeO());
    u_csr.setOpcodePcI(u_issue.getCsrOpcodePcO());
    u_csr.setOpcodeInvalidI(u_issue.getCsrOpcodeInvalidO());
    u_csr.setOpcodeRdIdxI(u_issue.getCsrOpcodeRdIdxO());
    u_csr.setOpcodeRaIdxI(u_issue.getCsrOpcodeRaIdxO());
    u_csr.setOpcodeRbIdxI(u_issue.getCsrOpcodeRbIdxO());
    u_csr.setOpcodeRaOperandI(u_issue.getCsrOpcodeRaOperandO());
    u_csr.setOpcodeRbOperandI(u_issue.getCsrOpcodeRbOperandO());

    // CSR writeback from Issue
    u_csr.setCsrWritebackWriteI(u_issue.getCsrWritebackWriteO());
    u_csr.setCsrWritebackWaddrI(u_issue.getCsrWritebackWaddrO());
    u_csr.setCsrWritebackWdataI(u_issue.getCsrWritebackWdataO());
    u_csr.setCsrWritebackExceptionI(u_issue.getCsrWritebackExceptionO());
    u_csr.setCsrWritebackExceptionPcI(u_issue.getCsrWritebackExceptionPcO());
    u_csr.setCsrWritebackExceptionAddrI(
        u_issue.getCsrWritebackExceptionAddrO());

    // CSR control inputs
    u_csr.setIntrI(intr_i_reg);
    u_csr.setInterruptInhibitI(u_issue.getInterruptInhibitO());

    // ================================================================
    // Phase 19: Process CSR
    // ================================================================
    u_csr.process();

    // ================================================================
    // Phase 20: Set Multiplier inputs from Issue outputs
    // ================================================================
    u_mul.setOpcodeValidI(u_issue.getMulOpcodeValidO());
    u_mul.setOpcodeInvalidI(u_issue.getMulOpcodeInvalidO());
    u_mul.setOpcodeOpcodeI(u_issue.getMulOpcodeOpcodeO());
    u_mul.setOpcodePcI(u_issue.getMulOpcodePcO());
    u_mul.setOpcodeRdIdxI(u_issue.getMulOpcodeRdIdxO());
    u_mul.setOpcodeRaIdxI(u_issue.getMulOpcodeRaIdxO());
    u_mul.setOpcodeRbIdxI(u_issue.getMulOpcodeRbIdxO());
    u_mul.setOpcodeRaOperandI(u_issue.getMulOpcodeRaOperandO());
    u_mul.setOpcodeRbOperandI(u_issue.getMulOpcodeRbOperandO());
    u_mul.setHoldI(u_issue.getMulHoldO());

    // ================================================================
    // Phase 21: Process Multiplier
    // ================================================================
    u_mul.process();

    // ================================================================
    // Phase 22: Set Divider inputs from Issue outputs
    // ================================================================
    u_div.setOpcodeValidI(u_issue.getDivOpcodeValidO());
    u_div.setOpcodeInvalidI(u_issue.getOpcodeInvalidO());
    u_div.setOpcodeOpcodeI(u_issue.getOpcodeOpcodeO());
    u_div.setOpcodePcI(u_issue.getOpcodePcO());
    u_div.setOpcodeRdIdxI(u_issue.getOpcodeRdIdxO());
    u_div.setOpcodeRaIdxI(u_issue.getOpcodeRaIdxO());
    u_div.setOpcodeRbIdxI(u_issue.getOpcodeRbIdxO());
    u_div.setOpcodeRaOperandI(u_issue.getOpcodeRaOperandO());
    u_div.setOpcodeRbOperandI(u_issue.getOpcodeRbOperandO());

    // ================================================================
    // Phase 23: Process Divider
    // ================================================================
    u_div.process();

    // ================================================================
    // Phase 24: Connect Fetch icache outputs to MMU fetch_in inputs
    // ================================================================
    u_mmu.setFetchInRdI(u_fetch.getIcacheRdO() ? true : false);
    u_mmu.setFetchInFlushI(u_fetch.getIcacheFlushO() ? true : false);
    u_mmu.setFetchInInvalidateI(
        u_fetch.getIcacheInvalidateO() ? true : false);
    u_mmu.setFetchInPcI(u_fetch.getIcachePcO());
    u_mmu.setFetchInPrivI(u_fetch.getIcachePrivO());

    // ================================================================
    // Phase 25: Connect LSU mem outputs to MMU lsu_in inputs
    // ================================================================
    u_mmu.setLsuInAddrI(u_lsu.getMemAddrO());
    u_mmu.setLsuInDataWrI(u_lsu.getMemDataWrO());
    u_mmu.setLsuInRdI(u_lsu.getMemRdO() ? true : false);
    u_mmu.setLsuInWrI(u_lsu.getMemWrO() ? true : false);
    u_mmu.setLsuInCacheableI(u_lsu.getMemCacheableO() ? true : false);
    u_mmu.setLsuInReqTagI(u_lsu.getMemReqTagO());
    u_mmu.setLsuInInvalidateI(u_lsu.getMemInvalidateO() ? true : false);
    u_mmu.setLsuInWritebackI(u_lsu.getMemWritebackO() ? true : false);
    u_mmu.setLsuInFlushI(u_lsu.getMemFlushO() ? true : false);

    // ================================================================
    // Phase 26: Process MMU (translation, TLB, external interface)
    // ================================================================
    u_mmu.process();

    // ================================================================
    // Phase 27: Read external memory interface outputs from MMU
    // ================================================================
    // Instruction memory outputs
    mem_i_rd_o_val = u_mmu.getFetchOutRdO() ? 1 : 0;
    mem_i_flush_o_val = u_mmu.getFetchOutFlushO() ? 1 : 0;
    mem_i_invalidate_o_val = u_mmu.getFetchOutInvalidateO() ? 1 : 0;

    // Data memory outputs
    mem_d_rd_o_val = u_mmu.getLsuOutRdO() ? 1 : 0;
    mem_d_cacheable_o_val = u_mmu.getLsuOutCacheableO() ? 1 : 0;
    mem_d_invalidate_o_val = u_mmu.getLsuOutInvalidateO() ? 1 : 0;
    mem_d_writeback_o_val = u_mmu.getLsuOutWritebackO() ? 1 : 0;
    mem_d_flush_o_val = u_mmu.getLsuOutFlushO() ? 1 : 0;

    // ================================================================
    // Phase 28: Schedule next cycle
    // ================================================================
    if (!coreEvent.scheduled()) {
        schedule(coreEvent, curTick() + 1);
    }

    DPRINTF(DUT, "RiscvCore cycle %lu\n", curTick());
}

} // namespace gem5
