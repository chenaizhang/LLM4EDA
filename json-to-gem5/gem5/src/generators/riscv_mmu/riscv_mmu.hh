#ifndef __GENERATORS_RISCV_MMU_RISCV_MMU_HH__
#define __GENERATORS_RISCV_MMU_RISCV_MMU_HH__

#include <cstdint>

#include "params/RiscvMmu.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvMmu : public SimObject
{
  private:
    // TLB entry structure
    struct TlbEntry {
        bool valid;
        uint32_t vpn;       // Virtual page number (MSB 20 bits of VA)
        uint32_t ppn;       // Physical page number (MSB 20 bits of PA)
        bool r;             // Readable
        bool w;             // Writable
        bool x;             // Executable
        bool u;             // User-accessible
    };

    // Sv32 page table walk constants
    static constexpr int TLB_ENTRIES = 4;
    static constexpr uint32_t PTE_FLAG_V = 0;
    static constexpr uint32_t PTE_FLAG_R = 1;
    static constexpr uint32_t PTE_FLAG_W = 2;
    static constexpr uint32_t PTE_FLAG_X = 3;
    static constexpr uint32_t PTE_FLAG_U = 4;
    static constexpr uint32_t PTE_FLAG_A = 6;
    static constexpr uint32_t PTE_FLAG_D = 7;

    // ---- Input port registers ----
    uint8_t priv_d_i_reg;               // 2-bit - data access privilege
    bool sum_i_reg;                     // SUM flag
    bool mxr_i_reg;                     // MXR flag
    bool flush_i_reg;                   // TLB flush request
    uint32_t satp_i_reg;                // SATP register value

    // Fetch input (from core)
    bool fetch_in_rd_i_reg;             // Fetch read request
    bool fetch_in_flush_i_reg;          // Fetch flush request
    bool fetch_in_invalidate_i_reg;     // Fetch invalidate request
    uint32_t fetch_in_pc_i_reg;         // Fetch PC
    uint8_t fetch_in_priv_i_reg;        // 2-bit - fetch privilege level

    // Fetch output (from icache)
    bool fetch_out_accept_i_reg;        // Icache accepts
    bool fetch_out_valid_i_reg;         // Icache data valid
    bool fetch_out_error_i_reg;         // Icache error
    uint32_t fetch_out_inst_i_reg;      // Icache instruction data

    // LSU input (from core)
    uint32_t lsu_in_addr_i_reg;         // LSU access address
    uint32_t lsu_in_data_wr_i_reg;      // LSU write data
    bool lsu_in_rd_i_reg;               // LSU read request
    bool lsu_in_wr_i_reg;               // LSU write request
    bool lsu_in_cacheable_i_reg;        // LSU cacheable flag
    uint32_t lsu_in_req_tag_i_reg;      // LSU request tag
    bool lsu_in_invalidate_i_reg;       // LSU invalidate request
    bool lsu_in_writeback_i_reg;        // LSU writeback request
    bool lsu_in_flush_i_reg;            // LSU flush request

    // LSU output (from dcache)
    uint32_t lsu_out_data_rd_i_reg;     // Dcache read data
    bool lsu_out_accept_i_reg;          // Dcache accepts
    bool lsu_out_ack_i_reg;             // Dcache ack
    bool lsu_out_error_i_reg;           // Dcache error
    uint32_t lsu_out_resp_tag_i_reg;    // Dcache response tag

    // ---- Output port values ----
    bool fetch_in_accept_o_val;         // Accept fetch request
    bool fetch_in_valid_o_val;          // Fetch result valid
    bool fetch_in_error_o_val;          // Fetch error
    uint32_t fetch_in_inst_o_val;       // Fetch instruction data
    bool fetch_out_rd_o_val;            // Icache read request
    bool fetch_out_flush_o_val;         // Icache flush
    bool fetch_out_invalidate_o_val;    // Icache invalidate
    uint32_t fetch_out_pc_o_val;        // Icache PC
    bool fetch_in_fault_o_val;          // Fetch page fault

    uint32_t lsu_in_data_rd_o_val;      // LSU read data
    bool lsu_in_accept_o_val;           // LSU request accepted
    bool lsu_in_ack_o_val;              // LSU request acked
    bool lsu_in_error_o_val;            // LSU error
    uint32_t lsu_in_resp_tag_o_val;     // LSU response tag
    uint32_t lsu_out_addr_o_val;        // Dcache address
    uint32_t lsu_out_data_wr_o_val;     // Dcache write data
    bool lsu_out_rd_o_val;              // Dcache read request
    bool lsu_out_wr_o_val;              // Dcache write request
    bool lsu_out_cacheable_o_val;       // Cacheable flag
    uint32_t lsu_out_req_tag_o_val;     // Request tag
    bool lsu_out_invalidate_o_val;      // Invalidate request
    bool lsu_out_writeback_o_val;       // Writeback request
    bool lsu_out_flush_o_val;           // Flush request
    bool lsu_in_load_fault_o_val;       // Load page fault
    bool lsu_in_store_fault_o_val;      // Store page fault

    // ---- Internal state ----
    TlbEntry tlb[TLB_ENTRIES];
    int tlbVictimIdx;

    // Parameters
    uint32_t memCacheAddrMin;
    uint32_t memCacheAddrMax;

    // ---- Private helper methods ----
    bool tlbLookup(uint32_t va, uint32_t &pa, bool &r, bool &w,
                   bool &x, bool &u);
    void tlbInsert(uint32_t va, uint32_t pa, bool r, bool w,
                   bool x, bool u);
    void tlbFlush();
    bool walkPageTable(uint32_t va, uint32_t &pa, bool &r, bool &w,
                       bool &x, bool &u, bool &fault);
    bool checkPermission(bool pte_r, bool pte_w, bool pte_x,
                         bool pte_u, bool is_fetch, bool is_store,
                         uint8_t priv, bool sum, bool mxr);
    bool isCacheable(uint32_t addr);

  public:
    RiscvMmu(const RiscvMmuParams &p);

    // ---- Input port set functions ----
    void setPrivDI(uint8_t val);
    void setSumI(bool val);
    void setMxrI(bool val);
    void setFlushI(bool val);
    void setSatpI(uint32_t val);
    void setFetchInRdI(bool val);
    void setFetchInFlushI(bool val);
    void setFetchInInvalidateI(bool val);
    void setFetchInPcI(uint32_t val);
    void setFetchInPrivI(uint8_t val);
    void setFetchOutAcceptI(bool val);
    void setFetchOutValidI(bool val);
    void setFetchOutErrorI(bool val);
    void setFetchOutInstI(uint32_t val);
    void setLsuInAddrI(uint32_t val);
    void setLsuInDataWrI(uint32_t val);
    void setLsuInRdI(bool val);
    void setLsuInWrI(bool val);
    void setLsuInCacheableI(bool val);
    void setLsuInReqTagI(uint32_t val);
    void setLsuInInvalidateI(bool val);
    void setLsuInWritebackI(bool val);
    void setLsuInFlushI(bool val);
    void setLsuOutDataRdI(uint32_t val);
    void setLsuOutAcceptI(bool val);
    void setLsuOutAckI(bool val);
    void setLsuOutErrorI(bool val);
    void setLsuOutRespTagI(uint32_t val);

    // ---- Output port get functions ----
    bool getFetchInAcceptO();
    bool getFetchInValidO();
    bool getFetchInErrorO();
    uint32_t getFetchInInstO();
    bool getFetchOutRdO();
    bool getFetchOutFlushO();
    bool getFetchOutInvalidateO();
    uint32_t getFetchOutPcO();
    bool getFetchInFaultO();
    uint32_t getLsuInDataRdO();
    bool getLsuInAcceptO();
    bool getLsuInAckO();
    bool getLsuInErrorO();
    uint32_t getLsuInRespTagO();
    uint32_t getLsuOutAddrO();
    uint32_t getLsuOutDataWrO();
    bool getLsuOutRdO();
    bool getLsuOutWrO();
    bool getLsuOutCacheableO();
    uint32_t getLsuOutReqTagO();
    bool getLsuOutInvalidateO();
    bool getLsuOutWritebackO();
    bool getLsuOutFlushO();
    bool getLsuInLoadFaultO();
    bool getLsuInStoreFaultO();

    // ---- Main process (called by parent each cycle) ----
    void process();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_MMU_RISCV_MMU_HH__
