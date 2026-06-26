## Python 配置文件参数说明

### riscv_issue.py 参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| regfile | Param.RiscvRegfile | (必选) | 通用寄存器文件实例 |
| xilinx_2r1w | Param.RiscvXilinx2r1w | None | 可选 Xilinx 2R1W 原语实例 |
| support_dual_issue | Param.Bool | False | 是否支持双发射 |

### 使用示例

在配置脚本中实例化：

```python
from m5.objects import *

root = Root(full_system = False)

# 实例化寄存器文件
root.regfile = RiscvRegfile(support_regfile_xilinx = False)

# 实例化发射单元
root.issue = RiscvIssue(
    regfile = root.regfile,
    support_dual_issue = False
)
```

### 作为顶层模块的子模块引用

```python
class RiscvCore(SimObject):
    type = 'RiscvCore'
    cxx_header = "generators/riscv_core/riscv_core.hh"
    cxx_class = "gem5::RiscvCore"

    issue = Param.RiscvIssue("Issue unit instance")
    regfile = Param.RiscvRegfile("Register file instance")
```
