from m5.params import *
from m5.SimObject import SimObject


class RiscvRegfile(SimObject):
    type = 'RiscvRegfile'
    cxx_header = "generators/riscv_regfile/riscv_regfile.hh"
    cxx_class = "gem5::RiscvRegfile"

    support_regfile_xilinx = Param.Bool(
        False, "Use Xilinx 2R1W primitive"
    )
