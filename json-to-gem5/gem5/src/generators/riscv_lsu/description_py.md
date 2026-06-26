# riscv_lsu.py 参数说明

## SimObject: RiscvLsu

### Python类
```python
class RiscvLsu(SimObject):
    type = 'RiscvLsu'
    cxx_header = "generators/riscv_lsu/riscv_lsu.hh"
    cxx_class = "gem5::RiscvLsu"
    
    fifo_depth = Param.UInt32(4, "Depth of the memory request FIFO")
```

### 参数说明
- **fifo_depth**: 内存请求FIFO深度，默认值为4。控制可以缓冲的未完成内存请求数量。

### 使用示例
```python
from m5.objects import RiscvLsu

# 创建LSU实例
root.lsu = RiscvLsu(fifo_depth=4)
```
