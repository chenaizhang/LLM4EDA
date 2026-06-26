from m5.params import *
from m5.SimObject import SimObject

class RiscvTraceSim(SimObject):
    type = 'RiscvTraceSim'
    cxx_header = "generators/riscv_trace_sim/riscv_trace_sim.hh"
    cxx_class = "gem5::RiscvTraceSim"
