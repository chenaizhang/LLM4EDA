# riscv_pipe_ctrl (RISC-V Pipeline Control)

## 模块功能概述
riscv_pipe_ctrl 是 RISC-V 处理器的流水线控制模块，负责管理流水线的 E1（执行第一周期）、E2（执行第二周期/访存）和 WB（写回）阶段。它实现数据通路的流水线寄存器，管理数据前递（bypass）、写回仲裁和流水线冲刷。

## 逻辑类型
时序逻辑（子模块）

## 端口列表

### 输入信号
| 端口名 | 位宽 | 描述 |
|--------|------|------|
| issue_valid_i | 1 | 发射阶段有效 |
| issue_accept_i | 1 | 发射阶段接受 |
| issue_stall_i | 1 | 发射阶段暂停 |
| issue_lsu_i | 1 | LSU 指令标志 |
| issue_csr_i | 1 | CSR 指令标志 |
| issue_div_i | 1 | 除法指令标志 |
| issue_mul_i | 1 | 乘法指令标志 |
| issue_branch_i | 1 | 分支指令标志 |
| issue_rd_valid_i | 1 | 目标寄存器有效 |
| issue_rd_i | 5 | 目标寄存器索引 |
| issue_exception_i | 6 | 异常码 |
| take_interrupt_i | 1 | 接受中断标志 |
| issue_branch_taken_i | 1 | 分支条件成立 |
| issue_branch_target_i | 32 | 分支目标地址 |
| issue_pc_i | 32 | 指令 PC |
| issue_opcode_i | 32 | 指令操作码 |
| issue_operand_ra_i | 32 | 源操作数 A |
| issue_operand_rb_i | 32 | 源操作数 B |
| alu_result_e1_i | 32 | ALU E1 结果 |
| csr_result_write_e1_i | 1 | CSR E1 写标志 |
| csr_result_value_e1_i | 32 | CSR E1 结果值 |
| csr_result_wdata_e1_i | 32 | CSR E1 写数据 |
| csr_result_exception_e1_i | 6 | CSR E1 异常码 |
| mem_complete_i | 1 | 访存完成 |
| mem_result_e2_i | 32 | E2 访存结果 |
| mem_exception_e2_i | 6 | E2 异常码 |
| mul_result_e2_i | 32 | E2 乘法结果 |
| div_complete_i | 1 | 除法完成 |
| div_result_i | 32 | 除法结果 |
| squash_e1_e2_i | 1 | 冲刷 E1→E2 流水级 |
| squash_wb_i | 1 | 冲刷写回阶段 |

### 输出信号
| 端口名 | 位宽 | 描述 |
|--------|------|------|
| load_e1_o | 1 | E1 加载指令标志 |
| store_e1_o | 1 | E1 存储指令标志 |
| mul_e1_o | 1 | E1 乘法指令标志 |
| branch_e1_o | 1 | E1 分支指令标志 |
| rd_e1_o | 5 | E1 目标寄存器索引 |
| pc_e1_o | 32 | E1 PC |
| opcode_e1_o | 32 | E1 操作码 |
| operand_ra_e1_o | 32 | E1 操作数 A |
| operand_rb_e1_o | 32 | E1 操作数 B |
| load_e2_o | 1 | E2 加载指令标志 |
| mul_e2_o | 1 | E2 乘法指令标志 |
| rd_e2_o | 5 | E2 目标寄存器索引 |
| result_e2_o | 32 | E2 结果值 |
| valid_wb_o | 1 | 写回有效 |
| csr_wb_o | 1 | CSR 写回标志 |
| rd_wb_o | 5 | 写回目标寄存器索引 |
| result_wb_o | 32 | 写回结果值 |
| pc_wb_o | 32 | 写回 PC |
| opcode_wb_o | 32 | 写回操作码 |
| operand_ra_wb_o | 32 | 写回操作数 A |
| operand_rb_wb_o | 32 | 写回操作数 B |
| exception_wb_o | 6 | 写回异常码 |
| csr_write_wb_o | 1 | CSR 写回写使能 |
| csr_waddr_wb_o | 12 | CSR 写回地址 |
| csr_wdata_wb_o | 32 | CSR 写回数据 |
| stall_o | 1 | 流水线暂停 |
| squash_e1_e2_o | 1 | 冲刷 E1→E2 |

## 参数列表
无参数。

## 内部信号说明
### 流水线寄存器
- **E1 寄存器组**：e1_valid_reg, e1_load_reg, e1_store_reg, e1_mul_reg, e1_branch_reg, e1_rd_reg, e1_pc_reg, e1_opcode_reg, e1_operand_ra_reg, e1_operand_rb_reg
- **E2 寄存器组**：e2_valid_reg, e2_load_reg, e2_mul_reg, e2_rd_reg, e2_result_reg, e2_pc_reg, e2_opcode_reg, e2_operand_ra_reg, e2_operand_rb_reg, e2_exception_reg, e2_csr_reg, e2_csr_write_reg, e2_csr_wdata_reg, e2_csr_waddr_reg
