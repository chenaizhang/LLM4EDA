# riscv_pipe_ctrl SimObject 参数说明

## SimObject 类名
RiscvPipeCtrl

## 参数
此模块为纯硬件流水线控制模块，不需要任何可配置参数。

Python 定义:
```python
class RiscvPipeCtrl(SimObject):
    type = 'RiscvPipeCtrl'
    cxx_header = "generators/riscv_pipe_ctrl/riscv_pipe_ctrl.hh"
    cxx_class = "gem5::RiscvPipeCtrl"
```

## 使用方式
作为子模块被 riscv_issue 使用，通过 set/get 函数进行连接：

```cpp
// 在 riscv_issue 中
pipe_ctrl->setIssueValidI(issue_valid);
pipe_ctrl->setIssuePcI(pc);
// ...
pipe_ctrl->process();
// 读取输出
bool stall = pipe_ctrl->getStallO();
```
