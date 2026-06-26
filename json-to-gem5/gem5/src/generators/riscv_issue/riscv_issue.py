from m5.params import *
from m5.SimObject import SimObject


class RiscvIssue(SimObject):
    type = 'RiscvIssue'
    cxx_header = "generators/riscv_issue/riscv_issue.hh"
    cxx_class = "gem5::RiscvIssue"

    regfile = Param.RiscvRegfile("Register file instance")
    xilinx_2r1w = Param.RiscvXilinx2r1w(
        "Optional Xilinx 2R1W primitive"
    )
    support_dual_issue = Param.Bool(
        False, "Support dual issue"
    )
