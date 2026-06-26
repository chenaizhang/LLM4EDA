## Python 配置脚本参数说明

### RiscvAlu 参数

RiscvAlu 模块不需要额外的 Python 可配置参数。
模块的行为完全由输入端口驱动，通过 set 函数设置输入值，process() 函数在父模块调用时执行组合逻辑计算。

### 父模块使用方式

在父模块（如 riscv_exec）中通过 Param.RiscvAlu 引用：
```python
alu = Param.RiscvAlu("RISC-V ALU unit")
```

在 C++ 中通过 params 获取引用：
```cpp
RiscvAlu &alu = *params.alu;
```

每个周期调用流程：
```cpp
alu.setAluA(a_val);
alu.setAluB(b_val);
alu.setAluOp(op);
alu.process();
uint32_t result = alu.getAluP();
```
