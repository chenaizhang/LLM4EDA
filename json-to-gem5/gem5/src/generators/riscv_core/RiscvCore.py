from m5.params import *
from m5.SimObject import SimObject


class RiscvCore(SimObject):
    type = "RiscvCore"
    cxx_header = "generators/riscv_core/riscv_core.hh"
    cxx_class = "gem5::RiscvCore"

    # ---- Submodule references ----
    fetch = Param.RiscvFetch("Fetch unit")
    issue = Param.RiscvIssue("Issue unit")
    exec = Param.RiscvExec("Execute unit")
    lsu = Param.RiscvLsu("Load store unit")
    csr = Param.RiscvCsr("CSR unit")
    mul = Param.RiscvMultiplier("Multiplier")
    div = Param.RiscvDivider("Divider")
    mmu = Param.RiscvMmu("MMU")

    # ---- Core parameters ----
    support_muldiv = Param.Bool(
        True, "Support MUL/DIV extensions"
    )
    support_super = Param.Bool(
        False, "Support Supervisor mode"
    )
    support_mmu = Param.Bool(
        False, "Support MMU"
    )
    support_load_bypass = Param.Bool(
        True, "Support load bypass"
    )
    support_mul_bypass = Param.Bool(
        True, "Support multiplier bypass"
    )
    support_regfile_xilinx = Param.Bool(
        False, "Use Xilinx register file primitive"
    )
    extra_decode_stage = Param.Bool(
        False, "Insert extra decode pipeline stage"
    )
    mem_cache_addr_min = Param.UInt32(
        0x80000000, "Minimum address of cacheable region"
    )
    mem_cache_addr_max = Param.UInt32(
        0x8FFFFFFF, "Maximum address of cacheable region"
    )
