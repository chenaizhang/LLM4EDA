from m5.params import *
from m5.SimObject import SimObject

class RiscvPipeCtrl(SimObject):
    type = 'RiscvPipeCtrl'
    cxx_header = "generators/riscv_pipe_ctrl/riscv_pipe_ctrl.hh"
    cxx_class = "gem5::RiscvPipeCtrl"
