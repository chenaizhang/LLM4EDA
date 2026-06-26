## Python 配置脚本参数说明

### RiscvMultiplier 参数

RiscvMultiplier 模块不需要额外的 Python 可配置参数。
模块的行为完全由输入端口驱动，通过 set 函数设置输入值，process() 函数在父模块每个周期调用时执行多周期乘法计算。

### 父模块使用方式

在父模块（如 riscv_core）中通过 Param.RiscvMultiplier 引用：
```python
multiplier = Param.RiscvMultiplier("RISC-V Multiplier unit")
```

在 C++ 中通过 params 获取引用：
```cpp
RiscvMultiplier &multiplier = *params.multiplier;
```

每个周期调用流程：
```cpp
multiplier.setOpcodeValidI(valid);
multiplier.setOpcodeInvalidI(invalid);
multiplier.setOpcodeOpcodeI(opcode);
multiplier.setOpcodePcI(pc);
multiplier.setOpcodeRdIdxI(rd_idx);
multiplier.setOpcodeRaIdxI(ra_idx);
multiplier.setOpcodeRbIdxI(rb_idx);
multiplier.setOpcodeRaOperandI(ra_val);
multiplier.setOpcodeRbOperandI(rb_val);
multiplier.setHoldI(hold);
multiplier.process();
uint32_t result = multiplier.getWritebackValueO();
```
