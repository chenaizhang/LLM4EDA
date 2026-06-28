# 🧠 LLM4EDA — Chip Design Automation Toolkit

A comprehensive toolchain for hardware design automation, bridging **Verilog**, **JSON**, **interactive HTML visualization**, and **Gem5 simulation**.  
Built for agile chip development, LLM-assisted design, and rigorous validation workflows.

---

## ✨ Features

### 🔄 Verilog ↔ JSON Conversion
- **Standard JSON schema** defined in [`specs/schema_v1.json`](specs/schema_v1.json)
- **Strict schema validation** – automated check via [`workflow_check_json_spec.md`](workflow_check_json_spec.md)
- **Dataset-driven verification**  
  - Conversion scripts: `parse_to_json.py` & `generate_from_json.py`  
  - Validated using benchmarks (see below)  
  - Iterative refinement ensures correctness

### 🖥️ JSON Visualization
- Generate **DOT / SVG / HTML** visualizations
- **Browser-based interactive viewer** with Hierarchy / Module / Trace views, zoom/pan canvas, node inspector, signal tracing, and SVG export
- **LLM-assisted editing** – discuss and modify the design with a language model; changes sync back to the JSON

### ⚙️ JSON → Gem5 Simulation
- Full workflow documented at [`json-to-gem5/documents/workflow.md`](json-to-gem5/documents/workflow.md)
- Pre-established workflow for RTL modules in `LLM4EDA/rtl/riscv`

---

## 📁 Project Structure

```
LLM4EDA/
├── README.md
├── workflow.md, workflow_check_json_spec.md, workflow_llm_editing.md, workflow_sim.md
├── run_check_tests.py, run_simulation.sh, run_workflow.sh
│
├── Benchmark/
│   ├── workflow_dataset.md, workflow_process.md
│   ├── ChipBench/               {src(38.v), tb(38), json(38), original(90.sv), restored(38)}
│   ├── Generated_dataset1/      {src(99), tb(99), json(99), original(100), restored(99)}
│   ├── Verilog_Eval_2/          {src(115), tb(115), json(115), original(313), restored(115)}
│   ├── dataset_cpu_ip/          {src(5), tb(5), json(5), original(18), restored(5)}
│   ├── dataset_not_self_contain/{src(3), tb(3), json(6), original(12), restored(6)}
│   └── dataset_self_contain/    {src(30), tb(30), json(30), original(60), restored(30)}
│
├── json-to-gem5/                # JSON spec → gem5 component tooling
│   ├── AGENTS.md, PROGRESS.md
│   ├── documents/               (6 Chinese docs)
│   ├── configs/                 (15 test config dirs)
│   ├── input/                   (18 RISC-V module input dirs, each with .txt or .json spec)
│   └── gem5/src/generators/     (18 generator subdirs)
│
├── output/                      # Generated outputs
│   ├── design.json, design_riscv.json, design_summary.json
│   ├── diagrams/                (5 .dot/.svg)
│   ├── generated/               (3 .v: from_example.v, riscv_core_generated.v, riscv_core_restored.v)
│   └── configs/  m5out/         (empty)
│
├── rtl/                         # Reference RTL
│   ├── riscv/                   (18 Verilog modules: core, alu, csr, decode, decoder, exec, fetch, issue, lsu, mmu, ...)
│   └── test/test.v
│
├── scripts/                     (20+ Python scripts)
│   ├── llm_edit.py, llm_gen_submodules.py
│   ├── parse_design.py, parse_to_json.py, generate_from_json.py
│   ├── check_json_spec.py, extract_rules.py
│   ├── fix_*.py                 (batch, comprehensive, verilog_patterns, all_undeclared, remaining_errors, ...)
│   ├── gen_report.py, gen_simobjects.py, gen_top.py, gen_versioned_suite.py
│   ├── diff_design.py, visualize_block.py, check_env.py
│   ├── utils/                   (ast_builder.py, expr_emitter.py)
│   └── visualizer_frontend/     (app.js, elk.bundled.js, index.html, style.css, template.html)
│
├── specs/                       # Schema & specification
│   ├── VERILOG_JSON_BIDIRECTIONAL_SPEC.md
│   ├── example_design_complete.json
│   └── schema_v1.json
│
├── test_suite/                  # Master test suite
│   ├── manifest.csv
│   ├── positive/                (14 valid JSON cases)
│   ├── negative/                (43 rule-violation dirs)
│   └── robustness/              (12 edge-case files)
│
└── test_suites/                 (6 timestamped runs: 20260628_043003, ...)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Optional] Graphviz (for DOT rendering)
- [Optional] A modern browser for the interactive viewer

### Installation
```bash
git clone https://github.com/ZirongGuo/LLM4EDA.git
cd LLM4EDA
```

---

## 📖 Usage Examples

### 1. Convert Verilog to JSON
```bash
python scripts/parse_to_json.py --top riscv_core /home/gzr/test/riscv-master/riscv-master/core/riscv/*.v -o output/design_riscv.json
```
```
[OK] 已生成规范 JSON: output/design_riscv.json 模块数: 19
```

### 2. Convert JSON back to Verilog
```bash
python scripts/generate_from_json.py output/design_riscv.json -o output/generated/riscv_core_restored.v
```
```
[OK] 已生成 Verilog: output/generated/riscv_core_restored.v 总行数: 3363
```

### 3. Generate Visualization (DOT / SVG / HTML)
```bash
# SVG
python scripts/visualize_block.py output/design_riscv.json --format svg -o output/diagrams/design_riscv.svg

# Interactive HTML (Hierarchy / Module / Trace views, zoom/pan, node inspector, signal tracing, SVG export)
python scripts/visualize_block.py output/design_riscv.json --format html -o output/diagrams/design_riscv_interactive.html
```

### 4. LLM-Assisted Editing
```bash
python scripts/llm_edit.py output/design_riscv.json -p "将riscv_alu的description的值改为alu运算器"
```
```
[LLM] 发送修改请求...
[OK] 已保存修改后的 JSON: output/design_riscv.json 应用了 1 项变更
```

### 5. JSON → Gem5 Simulation
```bash
# Follow the pre-established workflow in json-to-gem5/documents/workflow.md
# Task located at LLM4EDA/rtl/riscv
```

---

## 📊 Benchmark Validation

To ensure the correctness of the Verilog↔JSON conversion, we follow a **two-stage benchmark process**:

1. **Dataset preparation** – [`Benchmark/workflow_dataset.md`](Benchmark/workflow_dataset.md)  
2. **Iterative verification** – [`Benchmark/workflow_process.md`](Benchmark/workflow_process.md)

### Json Spec Validation

| 类别 | 总数 | 正确 | 通过率 |
|------|------|------|--------|
| 正例集 | 35 | 35 | **100%** |
| 负例集 | 50 | 50 | **100%** |
| 鲁棒性集 | 14 | 14 | **100%** |
| **总计** | 99 | 99 | **100%** |

### Verilog → JSON Benchmarks

| Benchmark | 描述 | 数量 | SConscript |
|-----------|------|------|------------|
| Generated dataset 1 | 基础Verilog语法 | 100 | ✅ |
| Verilog Eval 2 | 更抽象地指定模块接口 | 156 | ✅ |
| ChipBench_self_contain | 无子模块编写 | 30 | ✅ |
| ChipBench_not_self_contain | 含有子模块的顶层模块编写 | 3 | ✅ |
| ChipBench_cpu_ip | CPU IP核 | 5 | ✅ |
| ChipBench | 综合能力 | 38 | ✅ |

### JSON → Verilog Benchmarks

| Benchmark | 描述 | 数量 | SConscript |
|-----------|------|------|------------|
| Generated dataset 1 | 基础Verilog语法 | 100 | ✅ |
| Verilog Eval 2 | 更抽象地指定模块接口 | 156 | ✅ |
| ChipBench_self_contain | 无子模块编写 | 30 | ✅ |
| ChipBench_not_self_contain | 含有子模块的顶层模块编写 | 3 | ✅ |
| ChipBench_cpu_ip | CPU IP核 | 5 | ✅ |
| ChipBench | 综合能力 | 38 | ✅ |

> The Verilog/JSON conversion model is currently undergoing iterative testing.

---

## ⚙️ Gem5 Simulation Status

Pre-established workflow for RTL modules in `LLM4EDA/rtl/riscv`. Current progress:

| 模块 | 类型 | 测试向量 | SConscript |
|------|------|----------|------------|
| riscv_alu | combinational | 32 | ✅ |
| riscv_csr_regfile | sequential | 25 | ✅ |
| riscv_xilinx_2r1w | sequential | 13 | ✅ |
| riscv_divider | sequential | 18 | ✅ |
| riscv_multiplier | sequential | 15 | ✅ |
| riscv_regfile | sequential | 14 | ✅ |
| riscv_trace_sim | combinational | 7 | ✅ |
| riscv_pipe_ctrl | combinational | 15 | ✅ |
| riscv_fetch | sequential | 15 | ✅ |
| riscv_issue | sequential | 22 | ✅ |
| riscv_exec | sequential | 25 | ✅ |
| riscv_lsu | sequential | 20 | ✅ |
| riscv_csr | sequential | 18 | ✅ |
| riscv_mmu | sequential | 20 | ✅ |
| riscv_core（顶层） | sequential | 18 | ✅ |
| **总计** | | **277 个测试向量** | |

---

## 🛠️ Development & Contribution

We welcome contributions! Please check the workflow documents for detailed specifications.  
For LLM-based design discussions, see the interactive HTML module.

---

## 📜 License

[MIT](LICENSE) © ZirongGuo

---

## 📫 Contact

Open an issue or reach out via [GitHub Issues](https://github.com/ZirongGuo/LLM4EDA/issues).

---

> **Note**: Replace any placeholder paths with your actual project paths when running commands.
