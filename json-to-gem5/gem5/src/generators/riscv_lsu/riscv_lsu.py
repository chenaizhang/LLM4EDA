from m5.params import *
from m5.SimObject import SimObject


class RiscvLsu(SimObject):
    type = 'RiscvLsu'
    cxx_header = "generators/riscv_lsu/riscv_lsu.hh"
    cxx_class = "gem5::RiscvLsu"

    fifo_depth = Param.UInt32(4, "Depth of the memory request FIFO")
