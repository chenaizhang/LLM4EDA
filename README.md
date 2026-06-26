# LLM4EDA
Verilog/Json converter

## Verilog to Json
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/parse_to_json.py --top riscv_core /home/gzr/test/riscv-master/riscv-master/core/riscv/*.v -o output/design_riscv.json
[OK] 已生成规范 JSON: output/design_riscv.json
     模块数: 19
```

## Json to Verilog
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/generate_from_json.py output/design_riscv.json -o output/generated/riscv_core_restored.v
[OK] 已生成 Verilog: output/generated/riscv_core_restored.v
     总行数: 3363
```

## Json Visualization
Support Json to interactive HTML and Dot/SVG.
```shell
(base) root@DESKTOP-SRPEBB4:/home/gzr/new_test# python scripts/visualize_block.py output/design_riscv.json --format svg -o output/diagrams/design_riscv.svg
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
# generate submodules
python scripts/llm_gen_submodules.py \
      --design example_design_complete.json \
      --v-dir rtl/riscv \
      --top configs/top.py \
      --simobj-dir gem5/src/custom

# generate top
python3 scripts/gen_top.py --project $PROJECT

# build
$ cd /home/gzr/new_test/gem5 && PYTHON_CONFIG=python3.12-config scons \
  build/X86/custom/riscv/riscv_core.o \
  build/X86/custom/riscv/riscv_csr.o \
  build/X86/custom/riscv/riscv_csr_regfile.o \
  build/X86/custom/riscv/riscv_decode.o \
  build/X86/custom/riscv/riscv_decoder.o \
  build/X86/custom/riscv/riscv_defs.o \
  build/X86/custom/riscv/riscv_divider.o \
  build/X86/custom/riscv/riscv_exec.o \
  build/X86/custom/riscv/riscv_fetch.o \
  build/X86/custom/riscv/riscv_issue.o \
  build/X86/custom/riscv/riscv_lsu.o \
  build/X86/custom/riscv/riscv_mmu.o \
  build/X86/custom/riscv/riscv_multiplier.o \
  build/X86/custom/riscv/riscv_pipe_ctrl.o \
  build/X86/custom/riscv/riscv_regfile.o \
  build/X86/custom/riscv/riscv_trace_sim.o \
  build/X86/custom/riscv/riscv_xilinx_2r1w.o \
  -j$(nproc) 2>&1 | grep -E "error:|scons:|Compiling" | tail -30
```
