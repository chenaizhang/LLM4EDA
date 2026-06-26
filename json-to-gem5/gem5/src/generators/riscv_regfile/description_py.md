## Python 配置文件参数说明

### riscv_regfile.py 参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| support_regfile_xilinx | Param.Bool | False | 是否使用 Xilinx 2R1W 原语实现 |

### 使用示例

在配置脚本中实例化：

```python
from m5.objects import *

root = Root(full_system = False)

# 实例化寄存器文件
root.regfile = RiscvRegfile(support_regfile_xilinx = False)

# 或使用默认参数
root.regfile = RiscvRegfile()
```

作为其他模块的子模块引用：

```python
class RiscvIssue(SimObject):
    type = 'RiscvIssue'
    cxx_header = "generators/riscv_issue/riscv_issue.hh"
    cxx_class = "gem5::RiscvIssue"

    regfile = Param.RiscvRegfile("Register file instance")
```
