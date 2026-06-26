## Python 配置脚本参数说明

### RiscvTraceSim 参数

RiscvTraceSim 模块不需要额外的 Python 可配置参数。
模块的行为完全由输入端口驱动，通过 set 函数设置输入值，process() 函数在每个周期被调用。

### 父模块使用方式

在父模块（如 riscv_issue）中通过 Param.RiscvTraceSim 引用：
```python
trace_sim = Param.RiscvTraceSim("RISC-V trace simulation monitor")
```

在 C++ 中通过 params 获取引用：
```cpp
RiscvTraceSim &trace_sim = *params.trace_sim;
```

每个周期调用流程：
```cpp
trace_sim.setValidI(valid);
trace_sim.setPcI(pc);
trace_sim.setOpcodeI(opcode);
trace_sim.process();
```
