## 模块名称
riscv_issue (RISC-V Issue Unit)

## 逻辑类型
时序逻辑（子模块）

注意：作为子模块，其 process() 调用由顶层模块每个周期触发，代表一个时钟上升沿。
不需要 clk 输入端口和时钟边沿检测逻辑。

## 功能概述
RISC-V 发射单元模块，核心流水线控制单元。负责指令的收发、操作数获取、寄存器文件读取、写回处理、数据前递（bypass）以及分发指令到各个执行单元（ALU、LSU、CSR、乘法器、除法器）。还管理流水线停顿、中断响应和分支刷新。

## 端口定义

### 输入信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| fetch_valid_i | 1 | input | 取指有效标志 |
| fetch_instr_i | 31:0 | input | 指令操作码 |
| fetch_pc_i | 31:0 | input | 指令 PC 值 |
| fetch_fault_fetch_i | 1 | input | 取指故障标志 |
| fetch_fault_page_i | 1 | input | 页故障标志 |
| fetch_instr_exec_i | 1 | input | 指令类型：执行单元 |
| fetch_instr_lsu_i | 1 | input | 指令类型：访存单元 |
| fetch_instr_branch_i | 1 | input | 指令类型：分支单元 |
| fetch_instr_mul_i | 1 | input | 指令类型：乘法单元 |
| fetch_instr_div_i | 1 | input | 指令类型：除法单元 |
| fetch_instr_csr_i | 1 | input | 指令类型：CSR 单元 |
| fetch_instr_rd_valid_i | 1 | input | 指令有目标寄存器写 |
| fetch_instr_invalid_i | 1 | input | 非法指令标志 |
| branch_exec_request_i | 1 | input | 执行单元分支请求 |
| branch_exec_is_taken_i | 1 | input | 执行分支已跳转 |
| branch_exec_is_not_taken_i | 1 | input | 执行分支未跳转 |
| branch_exec_source_i | 1:0 | input | 执行分支源类型 |
| branch_exec_is_call_i | 1 | input | 执行函数调用标志 |
| branch_exec_is_ret_i | 1 | input | 执行函数返回标志 |
| branch_exec_is_jmp_i | 1 | input | 执行无条件跳转标志 |
| branch_exec_pc_i | 31:0 | input | 执行分支目标 PC |
| branch_d_exec_request_i | 1 | input | 延迟分支请求 |
| branch_d_exec_pc_i | 31:0 | input | 延迟分支目标 PC |
| branch_d_exec_priv_i | 1:0 | input | 延迟分支目标特权级 |
| branch_csr_request_i | 1 | input | CSR 分支请求 |
| branch_csr_pc_i | 31:0 | input | CSR 分支目标 PC |
| branch_csr_priv_i | 1:0 | input | CSR 分支目标特权级 |
| writeback_exec_value_i | 31:0 | input | 执行写回值 |
| writeback_mem_valid_i | 1 | input | 访存写回有效 |
| writeback_mem_value_i | 31:0 | input | 访存写回值 |
| writeback_mem_exception_i | 5:0 | input | 访存写回异常 |
| writeback_mul_value_i | 31:0 | input | 乘法写回值 |
| writeback_div_valid_i | 1 | input | 除法写回有效 |
| writeback_div_value_i | 31:0 | input | 除法写回值 |
| csr_result_e1_value_i | 31:0 | input | CSR E1 结果值 |
| csr_result_e1_write_i | 1 | input | CSR E1 写使能 |
| csr_result_e1_wdata_i | 31:0 | input | CSR E1 写数据 |
| csr_result_e1_exception_i | 5:0 | input | CSR E1 异常 |
| lsu_stall_i | 1 | input | 访存暂停标志 |
| take_interrupt_i | 1 | input | 中断响应标志 |

### 输出信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| fetch_accept_o | 1 | output | 上游接受标志 |
| branch_request_o | 1 | output | 分支请求（发送给 Fetch） |
| branch_pc_o | 31:0 | output | 分支目标 PC（发送给 Fetch） |
| branch_priv_o | 1:0 | output | 分支目标特权级（发送给 Fetch） |
| exec_opcode_valid_o | 1 | output | 执行单元操作码有效 |
| lsu_opcode_valid_o | 1 | output | 访存单元操作码有效 |
| csr_opcode_valid_o | 1 | output | CSR 单元操作码有效 |
| mul_opcode_valid_o | 1 | output | 乘法单元操作码有效 |
| div_opcode_valid_o | 1 | output | 除法单元操作码有效 |
| opcode_opcode_o | 31:0 | output | 指令操作码（通用输出） |
| opcode_pc_o | 31:0 | output | 指令 PC（通用输出） |
| opcode_invalid_o | 1 | output | 非法指令标志（通用输出） |
| opcode_rd_idx_o | 4:0 | output | 目标寄存器索引（通用输出） |
| opcode_ra_idx_o | 4:0 | output | 源操作数 A 索引（通用输出） |
| opcode_rb_idx_o | 4:0 | output | 源操作数 B 索引（通用输出） |
| opcode_ra_operand_o | 31:0 | output | 源操作数 A 值（通用输出） |
| opcode_rb_operand_o | 31:0 | output | 源操作数 B 值（通用输出） |
| lsu_opcode_opcode_o | 31:0 | output | 访存单元指令操作码 |
| lsu_opcode_pc_o | 31:0 | output | 访存单元指令 PC |
| lsu_opcode_invalid_o | 1 | output | 访存单元非法指令标志 |
| lsu_opcode_rd_idx_o | 4:0 | output | 访存单元目标寄存器索引 |
| lsu_opcode_ra_idx_o | 4:0 | output | 访存单元源操作数 A 索引 |
| lsu_opcode_rb_idx_o | 4:0 | output | 访存单元源操作数 B 索引 |
| lsu_opcode_ra_operand_o | 31:0 | output | 访存单元源操作数 A 值 |
| lsu_opcode_rb_operand_o | 31:0 | output | 访存单元源操作数 B 值 |
| mul_opcode_opcode_o | 31:0 | output | 乘法单元指令操作码 |
| mul_opcode_pc_o | 31:0 | output | 乘法单元指令 PC |
| mul_opcode_invalid_o | 1 | output | 乘法单元非法指令标志 |
| mul_opcode_rd_idx_o | 4:0 | output | 乘法单元目标寄存器索引 |
| mul_opcode_ra_idx_o | 4:0 | output | 乘法单元源操作数 A 索引 |
| mul_opcode_rb_idx_o | 4:0 | output | 乘法单元源操作数 B 索引 |
| mul_opcode_ra_operand_o | 31:0 | output | 乘法单元源操作数 A 值 |
| mul_opcode_rb_operand_o | 31:0 | output | 乘法单元源操作数 B 值 |
| csr_opcode_opcode_o | 31:0 | output | CSR 单元指令操作码 |
| csr_opcode_pc_o | 31:0 | output | CSR 单元指令 PC |
| csr_opcode_invalid_o | 1 | output | CSR 单元非法指令标志 |
| csr_opcode_rd_idx_o | 4:0 | output | CSR 单元目标寄存器索引 |
| csr_opcode_ra_idx_o | 4:0 | output | CSR 单元源操作数 A 索引 |
| csr_opcode_rb_idx_o | 4:0 | output | CSR 单元源操作数 B 索引 |
| csr_opcode_ra_operand_o | 31:0 | output | CSR 单元源操作数 A 值 |
| csr_opcode_rb_operand_o | 31:0 | output | CSR 单元源操作数 B 值 |
| csr_writeback_write_o | 1 | output | CSR 写回写使能 |
| csr_writeback_waddr_o | 11:0 | output | CSR 写回写地址 |
| csr_writeback_wdata_o | 31:0 | output | CSR 写回写数据 |
| csr_writeback_exception_o | 5:0 | output | CSR 写回异常 |
| csr_writeback_exception_pc_o | 31:0 | output | CSR 写回异常 PC |
| csr_writeback_exception_addr_o | 31:0 | output | CSR 写回异常地址 |
| exec_hold_o | 1 | output | 执行暂停标志 |
| mul_hold_o | 1 | output | 乘法暂停标志 |
| interrupt_inhibit_o | 1 | output | 中断禁止标志 |

## 子模块依赖
- riscv_regfile：通用寄存器文件接口
- riscv_xilinx_2r1w（可选）：Xilinx 2R1W 原语接口

## 功能说明

### 1. 指令接收与分派
- 从译码级接收指令及相关信息
- 根据指令类型分发到不同执行单元
- 支持双发射（SUPPORT_DUAL_ISSUE）
- 维护指令类型标志（exec、lsu、csr、mul、div）

### 2. 寄存器文件访问与数据前递
- 读取通用寄存器文件获取操作数
- 实现数据前递（bypass）逻辑，解决流水线数据冒险
- 支持加载前递（load bypass）
- 支持乘法前递（mul bypass）

### 3. 写回处理
- 接收各执行单元的写回结果
- 合并写回到寄存器文件
- 处理 CSR 写回（包括异常和异常地址）
- 除法器写回需要 valid 信号

### 4. 分支与中断
- 转发执行单元的分支结果到 Fetch
- 转发 CSR 单元的分支结果到 Fetch
- 响应中断请求，禁止后续指令发射
- 处理分支预测错误后的流水线刷新

### 5. 流水线控制
- 执行暂停（exec_hold_o）：当执行单元忙时暂停发射
- 乘法暂停（mul_hold_o）：当乘法器忙时暂停乘法指令发射
- 访存暂停（lsu_stall_i）：当 LSU 忙时暂停发射
- 中断禁止（interrupt_inhibit_o）：中断处理期间禁止新中断
