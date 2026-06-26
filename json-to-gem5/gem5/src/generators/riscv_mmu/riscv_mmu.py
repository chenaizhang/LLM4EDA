from m5.params import *
from m5.SimObject import SimObject


class RiscvMmu(SimObject):
    type = 'RiscvMmu'
    cxx_header = "generators/riscv_mmu/riscv_mmu.hh"
    cxx_class = "gem5::RiscvMmu"

    mem_cache_addr_min = Param.UInt32(
        0x80000000, "Minimum address of cacheable region"
    )
    mem_cache_addr_max = Param.UInt32(
        0x8FFFFFFF, "Maximum address of cacheable region"
    )
