## 模块名称
riscv_core (RISC-V Core Top Level)

## 模块功能概述
RISC-V 处理器核顶层模块，集成 9 个子模块构成完整的 5 级流水线 RV32IM 处理器核。包含取指（Fetch）、译码（Decode）、发射（Issue）、执行（Exec/ALU/LSU/CSR/乘法/除法）和写回（Writeback）流水线阶段。支持外部内存接口、中断输入，并通过参数配置支持 M/S 模式、MMU、乘法除法扩展等功能。

### 流水线架构
5 级流水线：Fetch → Decode → Issue → Execute/CSR/LSU/Mul/Div → Writeback

### 内存接口
- 指令内存接口：mem_i_*，通过 MMU 访问外部指令存储器
- 数据内存接口：mem_d_*，通过 MMU 访问外部数据存储器
- 支持缓存一致性操作（flush、invalidate、writeback）

### 中断处理
- 通过 intr_i 接收外部中断
- CSR 模块管理中断使能和委托
- 中断响应后流水线冲刷并跳转到中断向量

## 端口列表及说明

### 输入信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| rst_i | 1 | input | 复位信号 |
| mem_d_accept_i | 1 | input | 数据内存接受标志 |
| mem_d_ack_i | 1 | input | 数据内存应答标志 |
| mem_d_error_i | 1 | input | 数据内存错误标志 |
| mem_i_accept_i | 1 | input | 指令内存接受标志 |
| mem_i_valid_i | 1 | input | 指令内存有效标志 |
| mem_i_error_i | 1 | input | 指令内存错误标志 |
| intr_i | 1 | input | 外部中断信号 |

### 输出信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| mem_d_rd_o | 1 | output | 数据内存读请求 |
| mem_d_cacheable_o | 1 | output | 数据内存可缓存标志 |
| mem_d_invalidate_o | 1 | output | 数据内存无效化请求 |
| mem_d_writeback_o | 1 | output | 数据内存写回请求 |
| mem_d_flush_o | 1 | output | 数据内存刷新请求 |
| mem_i_rd_o | 1 | output | 指令内存读请求 |
| mem_i_flush_o | 1 | output | 指令内存刷新请求 |
| mem_i_invalidate_o | 1 | output | 指令内存无效化请求 |

## 参数列表及说明
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| SUPPORT_MULDIV | bool | 1 | 支持乘法除法扩展 |
| SUPPORT_SUPER | bool | 0 | 支持 Supervisor 模式 |
| SUPPORT_MMU | bool | 0 | 支持 MMU |
| SUPPORT_LOAD_BYPASS | bool | 1 | 支持加载前递 |
| SUPPORT_MUL_BYPASS | bool | 1 | 支持乘法前递 |
| SUPPORT_REGFILE_XILINX | bool | 0 | 使用 Xilinx 寄存器文件 |
| EXTRA_DECODE_STAGE | bool | 0 | 额外译码流水级 |
| MEM_CACHE_ADDR_MIN | uint32 | 0x80000000 | 可缓存地址范围下限 |
| MEM_CACHE_ADDR_MAX | uint32 | 0x8FFFFFFF | 可缓存地址范围上限 |

## 内部信号说明
内部信号用于连接各子模块之间的 wire 连接，主要包括：
- Fetch → Decode：指令有效、指令数据、PC、故障标志、squash 信号
- Decode → Issue：指令类型分类（exec/lsu/branch/mul/div/csr）、操作数、PC
- Issue → Exec/LSU/CSR/Mul/Div：各执行单元的操作码有效标志、操作数、寄存器索引
- Exec/LSU/Mul/Div → Issue：写回数据、分支反馈、停顿信号
- CSR → Issue：CSR 结果、分支请求、中断请求
- CSR → MMU：特权级、SUM/MXR 标志、SATP 寄存器、TLB 刷新
- Fetch → MMU：取指请求、PC、特权级
- LSU → MMU：访存地址、读写请求、缓存控制信号
- MMU → Fetch/LSU：地址翻译结果、页错误标志
