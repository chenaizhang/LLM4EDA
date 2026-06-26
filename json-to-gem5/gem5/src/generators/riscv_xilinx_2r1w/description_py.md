# RiscvXilinx2r1w 参数说明

## Python 类: RiscvXilinx2r1w

```python
class RiscvXilinx2r1w(SimObject):
    type = 'RiscvXilinx2r1w'
    cxx_header = "generators/riscv_xilinx_2r1w/riscv_xilinx_2r1w.hh"
    cxx_class = "gem5::RiscvXilinx2r1w"
```

## 参数列表

该模块为固定配置的存储原语，无运行时参数。

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| (无) | - | - | 模块为固定16x32存储阵列，无需参数配置 |

## 使用示例

```python
from m5.objects import RiscvXilinx2r1w

# 实例化（无参数）
memory = RiscvXilinx2r1w()
```

## 注意事项

- 该模块作为子模块使用，由父模块（如 riscv_regfile）通过 set 函数设置输入、process 函数驱动时钟、get 函数读取输出
- 存储深度固定为 16 个条目，每个条目 32 位
