## RiscvCore SimObject Python 配置说明

### 文件路径
`gem5/src/generators/riscv_core/RiscvCore.py`

### SimObject 类名
**RiscvCore** — 继承自 `SimObject`

### 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| fetch | Param.RiscvFetch | (必选) | 取指单元子模块引用 |
| issue | Param.RiscvIssue | (必选) | 发射单元子模块引用，内含 regfile 和 xilinx_2r1w |
| exec | Param.RiscvExec | (必选) | 执行单元子模块引用，内含 alu |
| lsu | Param.RiscvLsu | (必选) | 加载存储单元子模块引用 |
| csr | Param.RiscvCsr | (必选) | CSR 单元子模块引用，内含 csr_regfile |
| mul | Param.RiscvMultiplier | (必选) | 乘法器子模块引用 |
| div | Param.RiscvDivider | (必选) | 除法器子模块引用 |
| mmu | Param.RiscvMmu | (必选) | 内存管理单元子模块引用 |
| support_muldiv | Param.Bool | True | 支持 MUL/DIV 扩展 |
| support_super | Param.Bool | False | 支持 Supervisor 模式 |
| support_mmu | Param.Bool | False | 支持 MMU |
| support_load_bypass | Param.Bool | True | 支持加载前递 |
| support_mul_bypass | Param.Bool | True | 支持乘法前递 |
| support_regfile_xilinx | Param.Bool | False | 使用 Xilinx 寄存器文件原语 |
| extra_decode_stage | Param.Bool | False | 额外译码流水级 |
| mem_cache_addr_min | Param.UInt32 | 0x80000000 | 可缓存地址范围下限 |
| mem_cache_addr_max | Param.UInt32 | 0x8FFFFFFF | 可缓存地址范围上限 |

### 子模块层级说明

- **RiscvCore** (顶层)
  - **u_fetch** (RiscvFetch) — 独立 SimObject
  - **u_decode** (RiscvDecode) — 非 SimObject，C++ 中手动创建
    - **u_dec** (RiscvDecoder) — 组合逻辑子模块，在 C++ 中手动创建
  - **u_issue** (RiscvIssue) — 独立 SimObject
    - regfile (RiscvRegfile) — 通过 Issue 参数引用
    - xilinx_2r1w (RiscvXilinx2r1w) — 通过 Issue 参数引用
  - **u_exec** (RiscvExec) — 独立 SimObject
    - alu (RiscvAlu) — 通过 Exec 参数引用
  - **u_lsu** (RiscvLsu) — 独立 SimObject
  - **u_csr** (RiscvCsr) — 独立 SimObject
    - csrfile (RiscvCsrRegfile) — 通过 CSR 参数引用
  - **u_mul** (RiscvMultiplier) — 独立 SimObject
  - **u_div** (RiscvDivider) — 独立 SimObject
  - **u_mmu** (RiscvMmu) — 独立 SimObject

### 使用示例 (Python 配置脚本)
```python
from RiscvCore import RiscvCore
from RiscvFetch import RiscvFetch
from RiscvDecode import RiscvDecode
...

core = RiscvCore(
    fetch=RiscvFetch(),
    issue=RiscvIssue(regfile=RiscvRegfile()),
    exec=RiscvExec(alu=RiscvAlu()),
    lsu=RiscvLsu(),
    csr=RiscvCsr(csrfile=RiscvCsrRegfile()),
    mul=RiscvMultiplier(),
    div=RiscvDivider(),
    mmu=RiscvMmu(),
    support_muldiv=True,
    extra_decode_stage=False
)
```
