#ifndef __GENERATORS_RISCV_LSU_RISCV_LSU_HH__
#define __GENERATORS_RISCV_LSU_RISCV_LSU_HH__

#include <cstdint>

#include "params/RiscvLsu.hh"
#include "sim/sim_object.hh"

namespace gem5 {

class RiscvLsu : public SimObject
{
  private:
    // FIFO entry for pending memory requests
    struct LsuRequest {
        uint32_t opcode;
        uint32_t pc;
        uint32_t rd_idx;
        uint32_t addr;
        uint32_t store_data;
        bool is_load;
        uint32_t funct3;
        uint32_t tag;
    };

    // Exception codes (RISC-V style)
    static const uint32_t EXC_LOAD_ADDR_MISALIGN = 4;
    static const uint32_t EXC_STORE_ADDR_MISALIGN = 6;
    static const uint32_t EXC_LOAD_ACCESS_FAULT = 5;
    static const uint32_t EXC_STORE_ACCESS_FAULT = 7;
    static const uint32_t EXC_LOAD_PAGE_FAULT = 13;
    static const uint32_t EXC_STORE_PAGE_FAULT = 15;

    // LSU state
    enum LsuState {
        STATE_IDLE = 0,
        STATE_ACCEPT = 1,
        STATE_WAIT_RESP = 2
    };

    // Internal state registers
    int lsu_state;
    uint32_t req_tag_counter;

    // Pending request info
    LsuRequest pending_req;
    bool have_pending;
    bool request_accepted;

    // FIFO buffers
    LsuRequest *fifo;
    int fifo_capacity;
    int fifo_head;
    int fifo_tail;
    int fifo_count;

    // Input port registers
    uint32_t opcode_valid_i_reg;
    uint32_t opcode_invalid_i_reg;
    uint32_t opcode_opcode_i_reg;
    uint32_t opcode_pc_i_reg;
    uint32_t opcode_rd_idx_i_reg;
    uint32_t opcode_ra_idx_i_reg;
    uint32_t opcode_rb_idx_i_reg;
    uint32_t opcode_ra_operand_i_reg;
    uint32_t opcode_rb_operand_i_reg;
    uint32_t mem_data_rd_i_reg;
    uint32_t mem_accept_i_reg;
    uint32_t mem_ack_i_reg;
    uint32_t mem_error_i_reg;
    uint32_t mem_resp_tag_i_reg;
    uint32_t mem_load_fault_i_reg;
    uint32_t mem_store_fault_i_reg;

    // Output port values
    uint32_t mem_addr_o_val;
    uint32_t mem_data_wr_o_val;
    uint32_t mem_rd_o_val;
    uint32_t mem_wr_o_val;
    uint32_t mem_cacheable_o_val;
    uint32_t mem_req_tag_o_val;
    uint32_t mem_invalidate_o_val;
    uint32_t mem_writeback_o_val;
    uint32_t mem_flush_o_val;
    uint32_t writeback_valid_o_val;
    uint32_t writeback_value_o_val;
    uint32_t writeback_exception_o_val;
    uint32_t stall_o_val;

    // Helper functions
    uint32_t extractImmediate(uint32_t opcode, bool is_load);
    uint32_t getFunct3(uint32_t opcode);
    bool isLoadOpcode(uint32_t opcode);
    bool isStoreOpcode(uint32_t opcode);
    bool checkAlignment(uint32_t addr, uint32_t funct3);
    uint32_t extractLoadData(uint32_t data, uint32_t funct3);
    uint32_t prepareStoreData(uint32_t data, uint32_t funct3);
    uint32_t getMisalignException(bool is_load);
    uint32_t getFaultException(bool is_load);

    void pushFifo(const LsuRequest &req);
    bool popFifo(LsuRequest &req);
    bool isFifoEmpty();
    bool isFifoFull();

    void issueRequest(const LsuRequest &req);
    void processResponse();
    void setDefaultOutputs();

  public:
    RiscvLsu(const RiscvLsuParams &params);
    ~RiscvLsu();

    // Input port set functions
    void setOpcodeValidI(uint32_t val);
    void setOpcodeInvalidI(uint32_t val);
    void setOpcodeOpcodeI(uint32_t val);
    void setOpcodePcI(uint32_t val);
    void setOpcodeRdIdxI(uint32_t val);
    void setOpcodeRaIdxI(uint32_t val);
    void setOpcodeRbIdxI(uint32_t val);
    void setOpcodeRaOperandI(uint32_t val);
    void setOpcodeRbOperandI(uint32_t val);
    void setMemDataRdI(uint32_t val);
    void setMemAcceptI(uint32_t val);
    void setMemAckI(uint32_t val);
    void setMemErrorI(uint32_t val);
    void setMemRespTagI(uint32_t val);
    void setMemLoadFaultI(uint32_t val);
    void setMemStoreFaultI(uint32_t val);

    // Output port get functions
    uint32_t getMemAddrO();
    uint32_t getMemDataWrO();
    uint32_t getMemRdO();
    uint32_t getMemWrO();
    uint32_t getMemCacheableO();
    uint32_t getMemReqTagO();
    uint32_t getMemInvalidateO();
    uint32_t getMemWritebackO();
    uint32_t getMemFlushO();
    uint32_t getWritebackValidO();
    uint32_t getWritebackValueO();
    uint32_t getWritebackExceptionO();
    uint32_t getStallO();

    // Main process function called by parent each cycle
    void process();

    // Reset the LSU to initial state
    void reset();
};

} // namespace gem5

#endif // __GENERATORS_RISCV_LSU_RISCV_LSU_HH__
