## 模块名称
riscv_multiplier (RISC-V Multiplier Unit)

## 逻辑类型
时序逻辑（子模块）

注意：作为子模块，其 process() 调用由顶层模块（riscv_core）每个周期触发。
不需要 clk 输入端口和时钟边沿检测逻辑。

## 功能概述
riscv_multiplier 是 RISC-V 处理器的乘法单元，负责执行 MUL/MULH/MULHSU/MULHU 乘法指令。乘法操作需要 32 个时钟周期完成，模块内部维护部分积累加状态，完成后通过写回接口输出结果。支持流水线暂停（hold_i）功能。

## 端口定义

### 输入信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| opcode_valid_i | 1 | input | 操作码有效标志 |
| opcode_invalid_i | 1 | input | 操作码非法标志 |
| opcode_opcode_i | 31:0 | input | 指令操作码 |
| opcode_pc_i | 31:0 | input | 指令 PC |
| opcode_rd_idx_i | 4:0 | input | 目标寄存器索引 |
| opcode_ra_idx_i | 4:0 | input | 源寄存器 A 索引 |
| opcode_rb_idx_i | 4:0 | input | 源寄存器 B 索引 |
| opcode_ra_operand_i | 31:0 | input | 源操作数 A |
| opcode_rb_operand_i | 31:0 | input | 源操作数 B |
| hold_i | 1 | input | 流水线暂停标志 |

### 输出信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| writeback_value_o | 31:0 | output | 乘法结果写回值 |

## 功能说明

### 1. 乘法操作类型
- MUL: 32 位有符号整数乘法，取低 32 位结果
- MULH: 32 位有符号整数乘法，取高 32 位结果
- MULHSU: 32 位有符号×无符号整数乘法，取高 32 位结果
- MULHU: 32 位无符号整数乘法，取高 32 位结果

### 2. 多周期计算
- 使用移位加（shift-and-add）算法，每周期处理一位
- 初始状态（MULT_IDLE）：等待有效操作码，解码操作类型并初始化计算
- 计算状态（MULT_COMPUTE）：每周期执行一次移位加操作，共 32 个周期
- 完成状态（MULT_DONE）：计算结果输出到 writeback_value_o，下一周期回到空闲状态

### 3. 暂停与写回
- 当 hold_i 有效时暂停内部状态更新，计算冻结
- 计算完成后通过 writeback_value_o 输出结果
- 输出值在 MULT_DONE 状态稳定保持，直到新操作到来

### 4. 符号处理
- MUL：无符号乘法结果低 32 位（与有符号结果相同）
- MULH：对无符号乘积进行符号修正（减去有符号操作数的高位贡献）
- MULHSU：对无符号乘积进行单边符号修正
- MULHU：无符号乘法的高 32 位，无需修正
