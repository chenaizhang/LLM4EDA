from m5.params import *
from m5.SimObject import SimObject
from m5.proxy import Parent


class RiscvCsr(SimObject):
    type = 'RiscvCsr'
    cxx_header = "generators/riscv_csr/riscv_csr.hh"
    cxx_class = "gem5::RiscvCsr"

    csrfile = Param.RiscvCsrRegfile(Parent.any, "CSR register file submodule")
