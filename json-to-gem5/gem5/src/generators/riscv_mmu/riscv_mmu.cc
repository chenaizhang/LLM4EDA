/*
 * gem5 simulator
 * Copyright (c) 2024, Jason Lowe-Power
 * All rights reserved.
 */

#include "generators/riscv_mmu/riscv_mmu.hh"

#include <cstdint>

namespace gem5 {

RiscvMmu::RiscvMmu(const RiscvMmuParams &p)
    : SimObject(p),
      tlbVictimIdx(0),
      memCacheAddrMin(p.mem_cache_addr_min),
      memCacheAddrMax(p.mem_cache_addr_max)
{
    // Initialize input port registers
    priv_d_i_reg = 0;
    sum_i_reg = false;
    mxr_i_reg = false;
    flush_i_reg = false;
    satp_i_reg = 0;

    fetch_in_rd_i_reg = false;
    fetch_in_flush_i_reg = false;
    fetch_in_invalidate_i_reg = false;
    fetch_in_pc_i_reg = 0;
    fetch_in_priv_i_reg = 0;

    fetch_out_accept_i_reg = false;
    fetch_out_valid_i_reg = false;
    fetch_out_error_i_reg = false;
    fetch_out_inst_i_reg = 0;

    lsu_in_addr_i_reg = 0;
    lsu_in_data_wr_i_reg = 0;
    lsu_in_rd_i_reg = false;
    lsu_in_wr_i_reg = false;
    lsu_in_cacheable_i_reg = false;
    lsu_in_req_tag_i_reg = 0;
    lsu_in_invalidate_i_reg = false;
    lsu_in_writeback_i_reg = false;
    lsu_in_flush_i_reg = false;

    lsu_out_data_rd_i_reg = 0;
    lsu_out_accept_i_reg = false;
    lsu_out_ack_i_reg = false;
    lsu_out_error_i_reg = false;
    lsu_out_resp_tag_i_reg = 0;

    // Initialize output port values
    fetch_in_accept_o_val = false;
    fetch_in_valid_o_val = false;
    fetch_in_error_o_val = false;
    fetch_in_inst_o_val = 0;
    fetch_out_rd_o_val = false;
    fetch_out_flush_o_val = false;
    fetch_out_invalidate_o_val = false;
    fetch_out_pc_o_val = 0;
    fetch_in_fault_o_val = false;

    lsu_in_data_rd_o_val = 0;
    lsu_in_accept_o_val = false;
    lsu_in_ack_o_val = false;
    lsu_in_error_o_val = false;
    lsu_in_resp_tag_o_val = 0;
    lsu_out_addr_o_val = 0;
    lsu_out_data_wr_o_val = 0;
    lsu_out_rd_o_val = false;
    lsu_out_wr_o_val = false;
    lsu_out_cacheable_o_val = false;
    lsu_out_req_tag_o_val = 0;
    lsu_out_invalidate_o_val = false;
    lsu_out_writeback_o_val = false;
    lsu_out_flush_o_val = false;
    lsu_in_load_fault_o_val = false;
    lsu_in_store_fault_o_val = false;

    // Initialize TLB entries (all invalid)
    for (int i = 0; i < TLB_ENTRIES; i++) {
        tlb[i].valid = false;
        tlb[i].vpn = 0;
        tlb[i].ppn = 0;
        tlb[i].r = false;
        tlb[i].w = false;
        tlb[i].x = false;
        tlb[i].u = false;
    }
}

// ==================== Input port set functions ====================

void
RiscvMmu::setPrivDI(uint8_t val)
{
    priv_d_i_reg = val;
}

void
RiscvMmu::setSumI(bool val)
{
    sum_i_reg = val;
}

void
RiscvMmu::setMxrI(bool val)
{
    mxr_i_reg = val;
}

void
RiscvMmu::setFlushI(bool val)
{
    flush_i_reg = val;
}

void
RiscvMmu::setSatpI(uint32_t val)
{
    satp_i_reg = val;
}

void
RiscvMmu::setFetchInRdI(bool val)
{
    fetch_in_rd_i_reg = val;
}

void
RiscvMmu::setFetchInFlushI(bool val)
{
    fetch_in_flush_i_reg = val;
}

void
RiscvMmu::setFetchInInvalidateI(bool val)
{
    fetch_in_invalidate_i_reg = val;
}

void
RiscvMmu::setFetchInPcI(uint32_t val)
{
    fetch_in_pc_i_reg = val;
}

void
RiscvMmu::setFetchInPrivI(uint8_t val)
{
    fetch_in_priv_i_reg = val;
}

void
RiscvMmu::setFetchOutAcceptI(bool val)
{
    fetch_out_accept_i_reg = val;
}

void
RiscvMmu::setFetchOutValidI(bool val)
{
    fetch_out_valid_i_reg = val;
}

void
RiscvMmu::setFetchOutErrorI(bool val)
{
    fetch_out_error_i_reg = val;
}

void
RiscvMmu::setFetchOutInstI(uint32_t val)
{
    fetch_out_inst_i_reg = val;
}

void
RiscvMmu::setLsuInAddrI(uint32_t val)
{
    lsu_in_addr_i_reg = val;
}

void
RiscvMmu::setLsuInDataWrI(uint32_t val)
{
    lsu_in_data_wr_i_reg = val;
}

void
RiscvMmu::setLsuInRdI(bool val)
{
    lsu_in_rd_i_reg = val;
}

void
RiscvMmu::setLsuInWrI(bool val)
{
    lsu_in_wr_i_reg = val;
}

void
RiscvMmu::setLsuInCacheableI(bool val)
{
    lsu_in_cacheable_i_reg = val;
}

void
RiscvMmu::setLsuInReqTagI(uint32_t val)
{
    lsu_in_req_tag_i_reg = val;
}

void
RiscvMmu::setLsuInInvalidateI(bool val)
{
    lsu_in_invalidate_i_reg = val;
}

void
RiscvMmu::setLsuInWritebackI(bool val)
{
    lsu_in_writeback_i_reg = val;
}

void
RiscvMmu::setLsuInFlushI(bool val)
{
    lsu_in_flush_i_reg = val;
}

void
RiscvMmu::setLsuOutDataRdI(uint32_t val)
{
    lsu_out_data_rd_i_reg = val;
}

void
RiscvMmu::setLsuOutAcceptI(bool val)
{
    lsu_out_accept_i_reg = val;
}

void
RiscvMmu::setLsuOutAckI(bool val)
{
    lsu_out_ack_i_reg = val;
}

void
RiscvMmu::setLsuOutErrorI(bool val)
{
    lsu_out_error_i_reg = val;
}

void
RiscvMmu::setLsuOutRespTagI(uint32_t val)
{
    lsu_out_resp_tag_i_reg = val;
}

// ==================== Output port get functions ====================

bool
RiscvMmu::getFetchInAcceptO()
{
    return fetch_in_accept_o_val;
}

bool
RiscvMmu::getFetchInValidO()
{
    return fetch_in_valid_o_val;
}

bool
RiscvMmu::getFetchInErrorO()
{
    return fetch_in_error_o_val;
}

uint32_t
RiscvMmu::getFetchInInstO()
{
    return fetch_in_inst_o_val;
}

bool
RiscvMmu::getFetchOutRdO()
{
    return fetch_out_rd_o_val;
}

bool
RiscvMmu::getFetchOutFlushO()
{
    return fetch_out_flush_o_val;
}

bool
RiscvMmu::getFetchOutInvalidateO()
{
    return fetch_out_invalidate_o_val;
}

uint32_t
RiscvMmu::getFetchOutPcO()
{
    return fetch_out_pc_o_val;
}

bool
RiscvMmu::getFetchInFaultO()
{
    return fetch_in_fault_o_val;
}

uint32_t
RiscvMmu::getLsuInDataRdO()
{
    return lsu_in_data_rd_o_val;
}

bool
RiscvMmu::getLsuInAcceptO()
{
    return lsu_in_accept_o_val;
}

bool
RiscvMmu::getLsuInAckO()
{
    return lsu_in_ack_o_val;
}

bool
RiscvMmu::getLsuInErrorO()
{
    return lsu_in_error_o_val;
}

uint32_t
RiscvMmu::getLsuInRespTagO()
{
    return lsu_in_resp_tag_o_val;
}

uint32_t
RiscvMmu::getLsuOutAddrO()
{
    return lsu_out_addr_o_val;
}

uint32_t
RiscvMmu::getLsuOutDataWrO()
{
    return lsu_out_data_wr_o_val;
}

bool
RiscvMmu::getLsuOutRdO()
{
    return lsu_out_rd_o_val;
}

bool
RiscvMmu::getLsuOutWrO()
{
    return lsu_out_wr_o_val;
}

bool
RiscvMmu::getLsuOutCacheableO()
{
    return lsu_out_cacheable_o_val;
}

uint32_t
RiscvMmu::getLsuOutReqTagO()
{
    return lsu_out_req_tag_o_val;
}

bool
RiscvMmu::getLsuOutInvalidateO()
{
    return lsu_out_invalidate_o_val;
}

bool
RiscvMmu::getLsuOutWritebackO()
{
    return lsu_out_writeback_o_val;
}

bool
RiscvMmu::getLsuOutFlushO()
{
    return lsu_out_flush_o_val;
}

bool
RiscvMmu::getLsuInLoadFaultO()
{
    return lsu_in_load_fault_o_val;
}

bool
RiscvMmu::getLsuInStoreFaultO()
{
    return lsu_in_store_fault_o_val;
}

// ==================== Private helper methods ====================

bool
RiscvMmu::tlbLookup(uint32_t va, uint32_t &pa, bool &r, bool &w,
                     bool &x, bool &u)
{
    uint32_t vpn = va >> 12;

    for (int i = 0; i < TLB_ENTRIES; i++) {
        if (tlb[i].valid && tlb[i].vpn == vpn) {
            // TLB hit: reconstruct physical address
            pa = (tlb[i].ppn << 12) | (va & 0xFFF);
            r = tlb[i].r;
            w = tlb[i].w;
            x = tlb[i].x;
            u = tlb[i].u;
            return true;
        }
    }

    return false;
}

void
RiscvMmu::tlbInsert(uint32_t va, uint32_t pa, bool r, bool w,
                     bool x, bool u)
{
    tlb[tlbVictimIdx].valid = true;
    tlb[tlbVictimIdx].vpn = va >> 12;
    tlb[tlbVictimIdx].ppn = pa >> 12;
    tlb[tlbVictimIdx].r = r;
    tlb[tlbVictimIdx].w = w;
    tlb[tlbVictimIdx].x = x;
    tlb[tlbVictimIdx].u = u;

    // Round-robin replacement
    tlbVictimIdx = (tlbVictimIdx + 1) % TLB_ENTRIES;
}

void
RiscvMmu::tlbFlush()
{
    for (int i = 0; i < TLB_ENTRIES; i++) {
        tlb[i].valid = false;
    }
}

bool
RiscvMmu::walkPageTable(uint32_t va, uint32_t &pa, bool &r, bool &w,
                         bool &x, bool &u, bool &fault)
{
    // SV32 two-level page table walk.
    //
    // This implementation cannot access physical memory to read PTEs.
    // A complete implementation would use a memory port to read:
    //   - Level-1 PTE from (satp.ppn << 12) | (va[31:22] << 2)
    //   - Level-0 PTE from (pte1.ppn << 12) | (va[21:12] << 2)
    //
    // Without memory access, the walk always faults.
    // The TLB must be populated by other means (e.g., hardware page
    // table walker or preloaded entries) for successful translation.
    fault = true;
    return false;
}

bool
RiscvMmu::checkPermission(bool pte_r, bool pte_w, bool pte_x,
                           bool pte_u, bool is_fetch, bool is_store,
                           uint8_t priv, bool sum, bool mxr)
{
    // M-mode (3): full access, no permission checks
    if (priv == 3) {
        return true;
    }

    // S-mode (1) / U-mode (0): check user/supervisor page access
    if (priv == 1) {
        // S-mode: can access supervisor pages always;
        // user pages only when SUM is set
        if (pte_u && !sum) {
            return false;
        }
    } else {
        // U-mode: can only access user pages
        if (!pte_u) {
            return false;
        }
    }

    // Check specific access type against PTE permissions
    if (is_fetch) {
        // Instruction fetch requires execute permission
        return pte_x;
    } else if (is_store) {
        // Store requires write permission
        return pte_w;
    } else {
        // Load requires read permission, or MXR makes execute readable
        return pte_r || (mxr && pte_x);
    }
}

bool
RiscvMmu::isCacheable(uint32_t addr)
{
    return (addr >= memCacheAddrMin) && (addr <= memCacheAddrMax);
}

// ==================== Main process ====================

void
RiscvMmu::process()
{
    // ---- Reset all output values to default ----
    fetch_in_accept_o_val = false;
    fetch_in_valid_o_val = false;
    fetch_in_error_o_val = false;
    fetch_in_inst_o_val = 0;
    fetch_out_rd_o_val = false;
    fetch_out_flush_o_val = false;
    fetch_out_invalidate_o_val = false;
    fetch_out_pc_o_val = 0;
    fetch_in_fault_o_val = false;

    lsu_in_data_rd_o_val = 0;
    lsu_in_accept_o_val = false;
    lsu_in_ack_o_val = false;
    lsu_in_error_o_val = false;
    lsu_in_resp_tag_o_val = 0;
    lsu_out_addr_o_val = 0;
    lsu_out_data_wr_o_val = 0;
    lsu_out_rd_o_val = false;
    lsu_out_wr_o_val = false;
    lsu_out_cacheable_o_val = false;
    lsu_out_req_tag_o_val = 0;
    lsu_out_invalidate_o_val = false;
    lsu_out_writeback_o_val = false;
    lsu_out_flush_o_val = false;
    lsu_in_load_fault_o_val = false;
    lsu_in_store_fault_o_val = false;

    // ---- TLB flush ----
    if (flush_i_reg) {
        tlbFlush();
    }

    // ---- Fetch path ----
    // Forward flush/invalidate control signals to icache
    if (fetch_in_flush_i_reg) {
        fetch_out_flush_o_val = true;
    }
    if (fetch_in_invalidate_i_reg) {
        fetch_out_invalidate_o_val = true;
    }

    // Handle fetch request from core
    if (fetch_in_rd_i_reg) {
        uint32_t pa = 0;
        bool pte_r = false;
        bool pte_w = false;
        bool pte_x = false;
        bool pte_u = false;
        bool hit = tlbLookup(fetch_in_pc_i_reg, pa,
                             pte_r, pte_w, pte_x, pte_u);
        bool fault = false;

        if (!hit) {
            // TLB miss: attempt page table walk
            hit = walkPageTable(fetch_in_pc_i_reg, pa,
                                pte_r, pte_w, pte_x, pte_u, fault);
            if (hit) {
                tlbInsert(fetch_in_pc_i_reg, pa,
                          pte_r, pte_w, pte_x, pte_u);
            }
        }

        if (hit) {
            // Check instruction fetch permission
            bool permOk = checkPermission(pte_r, pte_w, pte_x,
                                          pte_u, true, false,
                                          fetch_in_priv_i_reg,
                                          sum_i_reg, mxr_i_reg);
            if (permOk && fetch_out_accept_i_reg) {
                // Permission OK and icache ready: send translated request
                fetch_out_rd_o_val = true;
                fetch_out_pc_o_val = pa;
                fetch_in_accept_o_val = true;
            } else if (!permOk) {
                fetch_in_fault_o_val = true;
            }
        } else if (fault) {
            fetch_in_fault_o_val = true;
        }
    }

    // Handle icache response (forward data back to core)
    if (fetch_out_valid_i_reg) {
        fetch_in_valid_o_val = true;
        fetch_in_inst_o_val = fetch_out_inst_i_reg;
        fetch_in_error_o_val = fetch_out_error_i_reg;
    }

    // ---- LSU / Data path ----
    // Forward flush/invalidate/writeback control signals to dcache
    if (lsu_in_flush_i_reg) {
        lsu_out_flush_o_val = true;
    }
    if (lsu_in_invalidate_i_reg) {
        lsu_out_invalidate_o_val = true;
    }
    if (lsu_in_writeback_i_reg) {
        lsu_out_writeback_o_val = true;
    }

    // Handle LSU request from core
    bool lsuIsLoad = lsu_in_rd_i_reg;
    bool lsuIsStore = lsu_in_wr_i_reg;

    if (lsuIsLoad || lsuIsStore) {
        uint32_t pa = 0;
        bool pte_r = false;
        bool pte_w = false;
        bool pte_x = false;
        bool pte_u = false;
        bool hit = tlbLookup(lsu_in_addr_i_reg, pa,
                             pte_r, pte_w, pte_x, pte_u);
        bool fault = false;

        if (!hit) {
            hit = walkPageTable(lsu_in_addr_i_reg, pa,
                                pte_r, pte_w, pte_x, pte_u, fault);
            if (hit) {
                tlbInsert(lsu_in_addr_i_reg, pa,
                          pte_r, pte_w, pte_x, pte_u);
            }
        }

        if (hit) {
            bool permOk = checkPermission(pte_r, pte_w, pte_x,
                                          pte_u, false, lsuIsStore,
                                          priv_d_i_reg,
                                          sum_i_reg, mxr_i_reg);
            if (permOk && lsu_out_accept_i_reg) {
                // Permission OK and dcache ready: send translated request
                lsu_out_addr_o_val = pa;
                lsu_out_data_wr_o_val = lsu_in_data_wr_i_reg;
                lsu_out_rd_o_val = lsuIsLoad;
                lsu_out_wr_o_val = lsuIsStore;
                lsu_out_cacheable_o_val = isCacheable(pa);
                lsu_out_req_tag_o_val = lsu_in_req_tag_i_reg;
                lsu_in_accept_o_val = true;
            } else if (!permOk) {
                if (lsuIsLoad) {
                    lsu_in_load_fault_o_val = true;
                }
                if (lsuIsStore) {
                    lsu_in_store_fault_o_val = true;
                }
            }
        } else if (fault) {
            if (lsuIsLoad) {
                lsu_in_load_fault_o_val = true;
            }
            if (lsuIsStore) {
                lsu_in_store_fault_o_val = true;
            }
        }
    }

    // Handle dcache response (forward data back to core)
    if (lsu_out_ack_i_reg) {
        lsu_in_ack_o_val = true;
        lsu_in_data_rd_o_val = lsu_out_data_rd_i_reg;
        lsu_in_error_o_val = lsu_out_error_i_reg;
        lsu_in_resp_tag_o_val = lsu_out_resp_tag_i_reg;
    }
}

} // namespace gem5
