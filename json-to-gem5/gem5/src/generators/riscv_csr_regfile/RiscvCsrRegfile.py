from m5.SimObject import SimObject
from m5.params import *

class RiscvCsrRegfile(SimObject):
    type = 'RiscvCsrRegfile'
    cxx_header = "generators/riscv_csr_regfile/riscv_csr_regfile.hh"
    cxx_class = "gem5::RiscvCsrRegfile"

    # Initial mstatus value (machine mode, MIE disabled)
    mstatus_init = Param.UInt32(0x00001800, "Initial mstatus value")
    # Initial privilege level: 0=User, 1=Supervisor, 3=Machine
    priv_init = Param.UInt8(3, "Initial privilege level (0=U, 1=S, 3=M)")
    # Base address for mtvec
    mtvec_base = Param.UInt32(0x80000000, "Base address for mtvec")
    # Base address for stvec
    stvec_base = Param.UInt32(0x80000000, "Base address for stvec")
