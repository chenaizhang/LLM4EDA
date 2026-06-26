from m5.params import *
from m5.SimObject import SimObject


class RiscvMultiplier(SimObject):
    type = 'RiscvMultiplier'
    cxx_header = "generators/riscv_multiplier/riscv_multiplier.hh"
    cxx_class = "gem5::RiscvMultiplier"
