from m5.params import *
from m5.SimObject import SimObject


class RiscvAlu(SimObject):
    type = 'RiscvAlu'
    cxx_header = "generators/riscv_alu/riscv_alu.hh"
    cxx_class = "gem5::RiscvAlu"
