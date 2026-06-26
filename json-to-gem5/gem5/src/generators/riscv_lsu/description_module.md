# riscv_lsu (RISC-V Load Store Unit)

## 模块功能概述
riscv_lsu 是 RISC-V 处理器的加载存储单元，负责执行内存访问指令（LB/LH/LW/LBU/LHU/SB/SH/SW）。它管理内存请求的发出、响应接收、数据写回，并处理加载和存储的异常/错误。

## 逻辑类型
时序逻辑（子模块）- 由顶层模块（riscv_core）每个周期调用 process() 驱动

## 端口列表

### 输入信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| opcode_valid_i | 1 | input | 操作码有效标志 |
| opcode_invalid_i | 1 | input | 操作码非法标志 |
| opcode_opcode_i | 32 | input | 指令操作码 |
| opcode_pc_i | 32 | input | 指令 PC |
| opcode_rd_idx_i | 5 | input | 目标寄存器索引 |
| opcode_ra_idx_i | 5 | input | 基址寄存器索引 |
| opcode_rb_idx_i | 5 | input | 源数据寄存器索引 |
| opcode_ra_operand_i | 32 | input | 基地址值 |
| opcode_rb_operand_i | 32 | input | 存储数据值 |
| mem_data_rd_i | 32 | input | 内存读数据 |
| mem_accept_i | 1 | input | 内存接受请求 |
| mem_ack_i | 1 | input | 内存响应有效 |
| mem_error_i | 1 | input | 内存访问错误 |
| mem_resp_tag_i | 32 | input | 内存响应标签 |
| mem_load_fault_i | 1 | input | 加载页错误 |
| mem_store_fault_i | 1 | input | 存储页错误 |

### 输出信号
| 端口名 | 位宽 | 方向 | 描述 |
|--------|------|------|------|
| mem_addr_o | 32 | output | 内存访问地址 |
| mem_data_wr_o | 32 | output | 内存写数据 |
| mem_rd_o | 1 | output | 内存读请求 |
| mem_wr_o | 1 | output | 内存写请求 |
| mem_cacheable_o | 1 | output | 内存可缓存标志 |
| mem_req_tag_o | 32 | output | 请求标签 |
| mem_invalidate_o | 1 | output | 缓存无效化 |
| mem_writeback_o | 1 | output | 缓存写回 |
| mem_flush_o | 1 | output | 缓存冲刷 |
| writeback_valid_o | 1 | output | 写回有效 |
| writeback_value_o | 32 | output | 写回数据值 |
| writeback_exception_o | 6 | output | 写回异常码 |
| stall_o | 1 | output | 流水线暂停标志 |

## 参数列表
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| fifo_depth | uint32 | 4 | 内存请求FIFO深度 |

## 内部信号说明
- **lsu_state**: LSU状态机状态（IDLE/ACCEPT/WAIT_RESP）
- **req_tag_counter**: 请求标签计数器
- **pending_req**: 当前等待响应的请求信息
- **have_pending**: 是否有待处理的请求
- **request_accepted**: 请求是否已被内存接受
- **fifo**: 内存请求FIFO缓冲区（循环队列）
