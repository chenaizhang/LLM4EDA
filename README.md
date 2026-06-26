# LLM4EDA
Verilog/Json converter

## Verilog to Json
| # | Benchmark | 描述 | 数量 | SConscript |
|---|------|------|---------|------------|
| 1 | Generated dataset 1 | 基础Verilog语法 | 100 | ✅ |  
  
The Verilog/Json conversion model is currently undergoing iterative testing.
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/parse_to_json.py --top riscv_core /home/gzr/test/riscv-master/riscv-master/core/riscv/*.v -o output/design_riscv.json
[OK] 已生成规范 JSON: output/design_riscv.json
     模块数: 19
```

## Json to Verilog
| # | Benchmark | 描述 | 数量 | SConscript |
|---|------|------|---------|------------|
| 1 | Generated dataset 1 | 基础Verilog语法 | 100 | ✅ |
  
The Verilog/Json conversion model is currently undergoing iterative testing.
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/generate_from_json.py output/design_riscv.json -o output/generated/riscv_core_restored.v
[OK] 已生成 Verilog: output/generated/riscv_core_restored.v
     总行数: 3363
```

## Json Visualization
Support Json to interactive HTML and Dot/SVG.
<img width="10520" height="9680" alt="e48c96876af4dbefe423fa17315c9424" src="https://github.com/user-attachments/assets/cde11d50-00ca-4cd5-a6bd-a14194f12c5c" />
<img width="3840" height="2160" alt="31f9b178c8eb561f5844469852b9584f" src="https://github.com/user-attachments/assets/2ec6b30d-0348-4ac5-99fa-27d15fea3cd2" />
```shell
# Dot/SVG
python scripts/visualize_block.py output/design_riscv.json --format svg -o output/diagrams/design_riscv.svg
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
[OK] 已生成 SVG 文件: output/diagrams/design_riscv.svg

# Browser-based visualization with Hierarchy / Module / Trace views, zoom/pan canvas,
# node inspector, signal tracing, and SVG export.
python scripts/visualize_block.py output/design_riscv.json --format html -o output/diagrams/design_riscv_interactive.html
```
Frontend source for the browser visualizer lives in `scripts/visualizer_frontend/`.

## LLM Editing
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/llm_edit.py --config
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/llm_edit.py output/design_riscv.json -p "将riscv_alu的description的值改为alu运算器"
  [LLM] 发送修改请求...
[OK] 已保存修改后的 JSON: output/design_riscv.json
     应用了 1 项变更
```

## Gem5 Simulation

```shell
请执行LLM4EDA/json-to-gem5/documents/workflow.md，任务位于LLM4EDA/rtl/riscv。
```

This is a pre-established workflow, please send this prompt to Opencode.

Results (PROGRESS.md) ：

| # | 模块 | 类型 | 测试向量 | SConscript |
|---|------|------|---------|------------|
| 1 | riscv_alu | combinational | 32 | ✅ |
| 2 | riscv_csr_regfile | sequential | 25 | ✅ |
| 3 | riscv_xilinx_2r1w | sequential | 13 | ✅ |
| 4 | riscv_divider | sequential | 18 | ✅ |
| 5 | riscv_multiplier | sequential | 15 | ✅ |
| 6 | riscv_regfile | sequential | 14 | ✅ |
| 7 | riscv_trace_sim | combinational | 7 | ✅ |
| 8 | riscv_pipe_ctrl | combinational | 15 | ✅ |
| 9 | riscv_fetch | sequential | 15 | ✅ |
| 10 | riscv_issue | sequential | 22 | ✅ |
| 11 | riscv_exec | sequential | 25 | ✅ |
| 12 | riscv_lsu | sequential | 20 | ✅ |
| 13 | riscv_csr | sequential | 18 | ✅ |
| 14 | riscv_mmu | sequential | 20 | ✅ |
| 15 | riscv_core（顶层） | sequential | 18 | ✅ |

**总计：277 个测试向量**  




