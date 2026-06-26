## 模块名称
riscv_regfile (RISC-V Register File)

## 逻辑类型
时序逻辑（子模块）

注意：作为子模块，其 process() 调用由顶层模块（riscv_issue）每个周期触发。
不需要 clk 输入端口和时钟边沿检测逻辑。

## 功能概述
riscv_regfile 是 RISC-V 处理器的通用寄存器文件，包含 32 个 x0-x31 通用寄存器。支持双端口读（RA/RB）和单端口写（RD）。可选择使用 Xilinx 原语实现（SUPPORT_REGFILE_XILINX）。

## 端口定义

### 输入信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| ra0_i | 4:0 | input | 读端口 A 寄存器索引 |
| rb0_i | 4:0 | input | 读端口 B 寄存器索引 |
| rd0_i | 4:0 | input | 写端口寄存器索引 |
| rd0_value_i | 31:0 | input | 写端口数据 |

### 输出信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| ra0_value_o | 31:0 | output | 读端口 A 数据 |
| rb0_value_o | 31:0 | output | 读端口 B 数据 |

## 功能说明

### 1. 寄存器读写
- 32 个 32 位通用寄存器（x0-x31）
- x0 寄存器始终为 0（硬连线）
- 双端口同时读取，单端口写入

### 2. Xilinx 原语支持
- 当 SUPPORT_REGFILE_XILINX=1 时，使用 riscv_xilinx_2r1w 实现
- 当 SUPPORT_REGFILE_XILINX=0 时，使用标准寄存器数组实现

### 3. 写前读
- 当读地址等于写地址时，直接转发写数据（避免 RAW 冲突）
