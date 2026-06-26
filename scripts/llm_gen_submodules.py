#!/usr/bin/env python3
"""
LLM 驱动的子模块 C++ 生成器。

用法:
  # 配置 API
  python scripts/llm_gen_submodules.py --config

  # 为 JSON 中所有子模块生成 C++ 实现
  python scripts/llm_gen_submodules.py \
      --design example_design_complete.json \
      --v-dir rtl/riscv \
      --top configs/top.py \
      --simobj-dir gem5/src/custom

  # 仅指定模块
  python scripts/llm_gen_submodules.py \
      --design example_design_complete.json \
      --v-dir rtl \
      --modules riscv_alu riscv_core

工作流:
  1. 解析设计 JSON，提取子模块接口
  2. 在 rtl 目录中查找匹配的 .v 文件
  3. 将 Verilog + 现有 SimObject 头文件 → LLM
  4. LLM 生成 C++ 实现代码 (.cc)
  5. 写回 SimObject 目录
"""

import argparse
import json
import os
import re
import sys
import subprocess
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "opencode_config.json"

# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

def load_config():
    if not CONFIG_PATH.exists():
        return {"llm": {"api_url": "https://api.deepseek.com", "api_key": "", "model": "deepseek-chat"}}
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    print(f"[OK] 配置已保存到 {CONFIG_PATH}")

def setup_config():
    cfg = load_config()
    llm = cfg.setdefault("llm", {})
    cur_url = llm.get("api_url", "https://api.deepseek.com")
    cur_key = llm.get("api_key", "")
    cur_model = llm.get("model", "deepseek-chat")
    print("=== LLM 配置 ===")
    url = input(f"API URL [{cur_url}]: ").strip() or cur_url
    hint = cur_key[:8] + "..." if cur_key else "(空)"
    key = input(f"API Key [{hint}]: ").strip() or cur_key
    model = input(f"Model [{cur_model}]: ").strip() or cur_model
    llm.update(api_url=url, api_key=key, model=model)
    save_config(cfg)

def call_llm(system_prompt, user_prompt, config, temperature=0.2):
    import urllib.request, urllib.error
    llm = config.get("llm", {})
    api_url = llm.get("api_url", "").rstrip("/")
    api_key = llm.get("api_key", "")
    model = llm.get("model", "gpt-4o")
    if not api_key:
        print("[ERROR] API Key 未配置，请先运行 --config")
        sys.exit(1)
    endpoint = f"{api_url}/v1/chat/completions" if "/v1" not in api_url else f"{api_url}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.read().decode()}")
        return None

def extract_code(text, language="cpp"):
    m = re.search(rf'```{language}\s*\n(.*?)\n```', text, re.DOTALL)
    if m:
        return m.group(1)
    if "```" not in text:
        return text
    return text

# ---------------------------------------------------------------------------
# 模块发现
# ---------------------------------------------------------------------------

def find_verilog_files(v_dir):
    """递归查找所有 .v 文件"""
    v_dir = Path(v_dir)
    files = {}
    for f in sorted(v_dir.rglob("*.v")):
        name = f.stem  # riscv_alu -> riscv_alu
        files[name] = f
    return files

def find_matching_verilog(module_name, v_files):
    """尝试为模块名匹配 .v 文件 (精确 > 包含 > 模糊)"""
    if module_name in v_files:
        return v_files[module_name]
    for name, path in v_files.items():
        if name == module_name or name.endswith("_" + module_name) or name.startswith(module_name + "_"):
            return path
    for name, path in v_files.items():
        if module_name in name or name in module_name:
            return path
    return None

def extract_module_ports_from_verilog(v_path):
    """从 Verilog 中提取端口列表和 always 块"""
    text = v_path.read_text()
    ports = []
    # Strip Verilog comments first to handle multi-line module declarations
    text_no_comments = re.sub(r'//.*?$|/\*.*?\*/', '', text, flags=re.MULTILINE | re.DOTALL)
    mod_match = re.search(r'module\s+(\w+)\s*(?:#\s*\(.*?\))?\s*\((.*?)\)\s*;', text_no_comments, re.DOTALL)
    port_text = ""
    if mod_match:
        port_text = mod_match.group(2)
    for m in re.finditer(
        r'(?:,\s*)?'
        r'(input|output|inout)\s+'
        r'(?:wire|reg|logic)?\s*'
        r'(?:signed)?\s*'
        r'(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'
        r'(\w+)', port_text
    ):
            ports.append({
                "direction": m.group(1),
                "data_type": "wire",
                "signed": False,
                "width": (int(m.group(2)) - int(m.group(3)) + 1) if m.group(2) else 1,
                "name": m.group(4),
            })
    always_blocks = re.findall(r'always\s*@\s*\([^)]*\)\s*begin(.*?)end', text, re.DOTALL)
    assigns = re.findall(r'assign\s+(\w+)\s*=\s*([^;]+);', text)
    return ports, always_blocks, assigns

# ---------------------------------------------------------------------------
# LLM Prompt 构建
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """你是一个 Verilog → Gem5 C++ SimObject 翻译专家。

你的任务：将 Verilog 模块的功能翻译成 Gem5 C++ SimObject 的 evaluate() 方法实现。

## 翻译规则

1. **端口映射**：Verilog 的 input/output 端口对应 SimObject 的 setXxx() / getXxx() 方法
2. **reg 信号**：Verilog 的 reg 声明对应类成员变量 (uint64_t / int)
3. **wire 信号**：Verilog 的 wire / assign 对应类中的 getter 方法或临时变量
4. **always @(*)**：组合逻辑 → 在 evaluate() 中用阻塞赋值 (=) 实现
5. **always @(posedge clk)**：时序逻辑 → 在 evaluate() 中用非阻塞赋值 (<=) 实现（需依赖时钟触发的逻辑单独处理）
6. **assign**：连续赋值 → 在 getter 中返回计算值
7. **case**：对应 C++ switch-case
8. **拼接 {a, b}**：对应 (a << n) | b
9. **位选择 [msb:lsb]**：对应位掩码和移位操作
10. **函数/任务**：对应类的私有方法

## 输出格式

只返回可以替换 .cc 文件中 `evaluate()` 方法的完整 C++ 代码块（包含所有辅助方法）。
代码放在 ```cpp ... ``` 代码块中。
不要在代码外添加解释。

## 注意事项

- 包含 #include "custom/模块名.hh"
- 包含 #include "params/ClassName.hh"
- 使用 DPRINTF 保留调试日志
- 确保方法签名与 .hh 头文件匹配
- 使用 PARAMS 宏约定的 params() 方法访问参数"""

# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def gen_for_module(module_name, v_path, hh_path, cc_path, config, force=False):
    print(f"\n{'='*60}")
    print(f"  模块: {module_name}")
    print(f"  .v : {v_path}")
    print(f"  .hh: {hh_path}")
    print(f"  .cc: {cc_path}")
    print(f"{'='*60}")

    if not v_path.exists():
        print(f"  [SKIP] .v 文件不存在")
        return
    if not hh_path.exists():
        print(f"  [SKIP] .hh 文件不存在")
        return

    verilog_source = v_path.read_text()
    hh_source = hh_path.read_text()
    cc_source = cc_path.read_text() if cc_path.exists() else ""

    ports, always_blocks, assigns = extract_module_ports_from_verilog(v_path)

    user_prompt = f"""## Verilog 模块: {module_name}

```verilog
{verilog_source}
```

## 现有 C++ 头文件 ({hh_path.name})

```cpp
{hh_source}
```

## 现有 C++ 实现 ({cc_path.name if cc_path.exists() else '新建'})
```cpp
{cc_source if cc_source else '// 空文件'}
```

## 端口摘要
{json.dumps(ports, indent=2)}

## 任务

生成完整的 `evaluate()` 方法（以及需要的辅助方法），实现该 ALU/模块的核心功能。
保留现有的构造函数、析构函数和端口访问方法（set/get）。
只替换或填充 evaluate() 内部的逻辑。"""

    print(f"  [LLM] 发送请求...")
    response = call_llm(SYSTEM_PROMPT, user_prompt, config)
    if not response:
        print(f"  [FAIL] LLM 请求失败")
        return

    code = extract_code(response, "cpp")
    if not code:
        print(f"  [WARN] 未从 LLM 响应中提取到 C++ 代码")
        print(f"  响应片段: {response[:300]}")
        return

    # 从 hh 路径提取项目名
    proj = hh_path.parent.name if hh_path.parent.name != "custom" else None
    new_cc = merge_code(cc_source, code, module_name, hh_source, project_name=proj)
    cc_path.write_text(new_cc)
    print(f"  [OK] 已写入: {cc_path}")
    print(f"      行数: {len(new_cc.splitlines())}")


# ---------------------------------------------------------------------------
# 头文件自动生成
# ---------------------------------------------------------------------------

def gen_header(mod_name, class_name, ports, hh_path):
    """从 Verilog 端口列表自动生成 SimObject .hh 文件"""
    lines = []
    guard = class_name.upper()
    lines.append(f"#ifndef __{guard}_HH__")
    lines.append(f"#define __{guard}_HH__\n")
    lines.append('#include "sim/clocked_object.hh"')
    lines.append(f'#include "params/{class_name}.hh"')
    lines.append('#include <cstdint>\n')
    lines.append("namespace gem5\n{")
    lines.append("")
    lines.append(f"class {class_name} : public ClockedObject")
    lines.append("{")
    lines.append("  private:")

    inouts = [p for p in ports if p["direction"] == "inout"]
    inputs = [p for p in ports if p["direction"] == "input"]
    outputs = [p for p in ports if p["direction"] == "output"]

    if inouts:
        lines.append("    std::vector<uint64_t> inout_data;")
    for p in inputs + outputs:
        lines.append(f"    uint64_t {p['name']}_val;")

    lines.append("")
    lines.append("  public:")
    lines.append(f"    PARAMS({class_name});")
    lines.append(f"    {class_name}(const Params &p);")
    lines.append(f"    virtual ~{class_name}();")
    lines.append("")

    for p in ports:
        n = p["name"]
        if p["direction"] == "inout":
            lines.append(f"    void write{p['name'].capitalize()}(uint64_t val);")
            lines.append(f"    uint64_t read{p['name'].capitalize()}();")
        elif p["direction"] == "input":
            cap = n[0].upper() + n[1:] if n else n
            lines.append(f"    void set{cap}(uint64_t val);")
        elif p["direction"] == "output":
            cap = n[0].upper() + n[1:] if n else n
            lines.append(f"    uint64_t get{cap}();")

    lines.append("")
    lines.append("    void evaluate();")
    lines.append("};")
    lines.append("")
    lines.append("} // namespace gem5")
    lines.append("")
    lines.append(f"#endif // __{guard}_HH__")

    hh_path.write_text("\n".join(lines) + "\n")
    print(f"  [OK] 已生成 .hh: {hh_path}")


def gen_python_simobject(mod_name, class_name, ports, output_dir, project_name=None):
    """生成 SimObject Python 绑定文件"""
    lines = []
    lines.append("from m5.objects.ClockedObject import ClockedObject")
    lines.append("from m5.params import *")
    lines.append("from m5.proxy import *")
    lines.append("")
    lines.append("")
    lines.append(f"class {class_name}(ClockedObject):")
    lines.append(f'    type = "{class_name}"')
    header_path = f"custom/{mod_name}.hh"
    if project_name:
        header_path = f"custom/{project_name}/{mod_name}.hh"
    lines.append(f'    cxx_header = "{header_path}"')
    lines.append(f'    cxx_class = "gem5::{class_name}"')
    lines.append("")
    for p in ports:
        n = p["name"]
        w = p.get("width", 1)
        if p["direction"] == "inout":
            lines.append(f"    {n} = VectorParam.Unsigned(")
            lines.append(f'        "双向端口 {n} (位宽: {w})"')
            lines.append("    )")
        elif p["direction"] == "input":
            lines.append(f"    {n} = Param.Unsigned({w},")
            lines.append(f'        "输入端口 {n} (位宽: {w})"')
            lines.append("    )")
        elif p["direction"] == "output":
            lines.append(f"    {n} = Param.Unsigned({w},")
            lines.append(f'        "输出端口 {n} (位宽: {w})"')
            lines.append("    )")
        lines.append("")
    py_name = f"{class_name}.py"
    py_path = output_dir / py_name
    py_path.write_text("\n".join(lines) + "\n")
    print(f"  [OK] 已生成 .py: {py_path}")


def update_sconscript(simobj_dir, mod_name, class_name, project_name=None):
    """向 SConscript 注册新的 SimObject 和源文件"""
    sconscript_path = simobj_dir / "SConscript"
    py_name = f"{class_name}.py"
    simobj_line = f"SimObject('{py_name}', sim_objects=['{class_name}'])"
    source_line = f"Source('{mod_name}.cc')"

    if not sconscript_path.exists():
        sconscript_path.write_text(f"Import('*')\n\n"
                                   f"{simobj_line}\n"
                                   f"{source_line}\n"
                                   f"DebugFlag('SystemC')\n")
        print(f"  [OK] 已创建 SConscript: {sconscript_path}")
        return

    existing = sconscript_path.read_text()
    if simobj_line in existing:
        print(f"  [OK] SConscript 已包含 {mod_name}")
        return
    # 在 SimObject 块后插入
    lines = existing.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("Source(") and i < insert_at:
            insert_at = i
    lines.insert(insert_at, source_line)
    lines.insert(insert_at, simobj_line)
    sconscript_path.write_text("\n".join(lines) + "\n")
    print(f"  [OK] 已更新 SConscript: {sconscript_path}")


def _extract_evaluate_body(code_str):
    """从代码字符串中提取 evaluate() 方法体。支持完整文件或方法片段。"""
    # 尝试匹配完整方法签名
    for pat in [
        r'void\s+\w+\s*::\s*evaluate\s*\(\s*\)\s*\{',
        r'void\s+\w+::evaluate\(\)\s*\{',
    ]:
        m = re.search(pat, code_str)
        if m:
            depth = 0
            i = m.end() - 1
            while i < len(code_str):
                if code_str[i] == '{':
                    depth += 1
                elif code_str[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return code_str[m.start():i+1]
                i += 1
            return code_str[m.start():]
    # 没有签名，假设整个内容就是 body
    return code_str


def merge_code(old_cc, new_evaluate, module_name, hh_source, project_name=None):
    """将 LLM 生成的 evaluate() 合并到现有 .cc 文件中。"""
    class_name_match = re.search(r'class\s+(\w+)\s*:', hh_source)
    class_name = class_name_match.group(1) if class_name_match else module_name

    # 如果 LLM 返回了完整文件（含 #include），提取其中的 evaluate()
    if '#include' in new_evaluate:
        ev_body = _extract_evaluate_body(new_evaluate)
    else:
        ev_body = new_evaluate

    if not old_cc:
        # 从头生成完整的 .cc
        hdr_path = f"custom/{module_name}.hh"
        if project_name:
            hdr_path = f"custom/{project_name}/{module_name}.hh"
        code = f"#include \"{hdr_path}\"\n"
        code += f"#include \"params/{class_name}.hh\"\n"
        code += '#include "debug/SystemC.hh"\n'
        code += '#include "sim/system.hh"\n\n'
        code += "namespace gem5\n{\n\n"

        code += f"{class_name}::{class_name}(const Params &p)\n"
        code += f"    : ClockedObject(p)\n"
        code += "{\n"
        code += f'    DPRINTF(SystemC, "创建 {class_name} 实例\\n");\n'
        code += "}\n\n"

        code += f"{class_name}::~{class_name}()\n"
        code += "{\n"
        code += f'    DPRINTF(SystemC, "销毁 {class_name} 实例\\n");\n'
        code += "}\n\n"

        # 从 hh 提取 set/get 方法并生成桩
        methods = re.findall(r'(void|uint64_t)\s+(set|get)(\w+)\(([^)]*)\)', hh_source)
        for ret, prefix, name, args in methods:
            if prefix == "set":
                code += f"void\n{class_name}::set{name}({args})\n{{\n"
                code += f'    DPRINTF(SystemC, "[{class_name}] set{name}\\n");\n'
                code += "}\n\n"
            elif prefix == "get":
                code += f"uint64_t\n{class_name}::get{name}()\n{{\n"
                code += f'    DPRINTF(SystemC, "[{class_name}] get{name}\\n");\n'
                code += "    return 0;\n"
                code += "}\n\n"

        code += ev_body
        code += "\n} // namespace gem5\n"
        return code

    # 已有 .cc，替换 evaluate() 内容
    for pat in [
        r'void\s*\n\s*\w+::evaluate\s*\(\s*\)\s*\n?\{',
        r'void\s+\w+::evaluate\s*\(\s*\)\s*\{',
    ]:
        eval_match = re.search(pat, old_cc)
        if eval_match:
            break

    if eval_match:
        start = eval_match.start()
        depth = 0
        i = eval_match.end() - 1
        while i < len(old_cc):
            if old_cc[i] == '{':
                depth += 1
            elif old_cc[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            i += 1
        sig = old_cc[eval_match.start():eval_match.end()]
        new_cc = old_cc[:start] + sig + " " + ev_body + old_cc[end:]
        return new_cc

    # fallback: 在文件末尾追加
    return old_cc + "\n\n" + ev_body


def main():
    parser = argparse.ArgumentParser(description="LLM 驱动子模块 C++ 实现生成器")
    parser.add_argument("--config", action="store_true", help="配置 API")
    parser.add_argument("--project", default=None,
                        help="项目名 (rtl 下的子目录名)，只处理该项目中的 .v 文件")
    parser.add_argument("--top-module", default=None,
                        help="手动指定顶层模块名 (默认自动检测: 不被其他模块实例化的模块)")
    parser.add_argument("--design", default="example_design_complete.json",
                        help="设计 JSON 文件")
    parser.add_argument("--v-dir", default="rtl",
                        help="Verilog 源文件目录 (递归搜索)")
    parser.add_argument("--top", default="output/configs/top.py",
                        help="顶层 Python 配置")
    parser.add_argument("--simobj-dir", default="gem5/src/custom",
                        help="SimObject 输出目录")
    parser.add_argument("--modules", nargs="*",
                        help="指定模块名 (默认: JSON 中所有自定义类型)")
    parser.add_argument("--force", action="store_true",
                        help="强制重新生成 (覆盖现有)")
    args = parser.parse_args()

    if args.config:
        setup_config()
        return

    base_dir = Path(__file__).resolve().parent.parent
    config = load_config()

    design_path = base_dir / args.design
    if not design_path.exists():
        print(f"[ERROR] 设计文件不存在: {design_path}")
        sys.exit(1)

    design = json.loads(design_path.read_text())
    v_dir = base_dir / args.v_dir
    if not v_dir.exists():
        print(f"[ERROR] Verilog 目录不存在: {v_dir}")
        sys.exit(1)

    simobj_dir = base_dir / args.simobj_dir
    if not simobj_dir.exists():
        print(f"[INFO] 创建 SimObject 目录: {simobj_dir}")
        simobj_dir.mkdir(parents=True)

    # 发现 .v 文件 (如果指定了 --project，限制到 rtl/<project>/)
    if args.project:
        project_dir = v_dir / args.project
        if not project_dir.exists():
            print(f"[ERROR] 项目目录不存在: {project_dir}")
            sys.exit(1)
        v_files = find_verilog_files(project_dir)
        file_source = f"{project_dir}"
    else:
        v_files = find_verilog_files(v_dir)
        file_source = f"{v_dir}"
    print(f"[INFO] 在 {file_source} 中找到 {len(v_files)} 个 .v 文件")

    # 自动检测顶层模块 (不被其他模块实例化的模块)
    top_module = args.top_module
    if not top_module:
        # 读取所有 v 文件中模块实例化关系
        all_instantiations = set()
        all_modules = set(v_files.keys())
        for vpath in v_files.values():
            text = vpath.read_text()
            # 匹配 Verilog 模块实例化: <module_name> #(...) <inst_name> ( ... );
            for m in re.finditer(r'(\w+)\s+(?:#\s*\([^)]*\)\s*)?\w+\s*\(', text):
                callee = m.group(1)
                # 排除关键词
                if callee.lower() in ('module', 'if', 'else', 'for', 'begin', 'end', 'case', 'assign', 'always', 'input', 'output', 'inout'):
                    continue
                # 排除 Verilog 原语
                if callee in ('and', 'or', 'not', 'nand', 'nor', 'xor', 'xnor'):
                    continue
                all_instantiations.add(callee)
        # 顶层 = 存在于项目中但未被实例化
        top_candidates = all_modules - (all_instantiations & all_modules)
        if top_candidates:
            top_module = sorted(top_candidates)[0]
            if len(top_candidates) > 1:
                print(f"  [INFO] 检测到多个候选顶层模块: {sorted(top_candidates)}，使用 '{top_module}'")
        else:
            top_module = sorted(all_modules)[0]
        print(f"  [INFO] 自动检测顶层模块: {top_module}")

    # 确定需要处理的模块
    modules_to_process = []
    if args.modules:
        if "all" in args.modules:
            modules_to_process = sorted(v_files.keys())
        else:
            modules_to_process = args.modules
    else:
        # 从 JSON 中提取所有子模块类型
        custom_types = set()
        for mod in design.get("modules", []):
            for inst in mod.get("instances", []):
                custom_types.add(inst["module"])
            for gen in mod.get("generates", []):
                for item in gen.get("body", []):
                    if item.get("type") == "instance":
                        custom_types.add(item["module"])
        modules_to_process = sorted(custom_types)

    print(f"[INFO] 需要处理的模块: {modules_to_process}")

    for mod_name in modules_to_process:
        v_path = find_matching_verilog(mod_name, v_files)
        if not v_path:
            alt = list(v_files.keys())
            print(f"  [SKIP] {mod_name}: 未找到匹配的 .v 文件 (可用: {alt[:10]})")
            continue

        v_mod_name = v_path.stem  # 实际 Verilog 模块名
        class_name = "".join(word.capitalize() for word in v_mod_name.split("_"))

        # 确定项目名: --project 优先，否则用 v 文件的父目录名
        project_name = args.project
        if not project_name:
            project_name = v_path.parent.name

        # 输出到 simobj_dir/<project>/ 子目录
        out_dir = simobj_dir / project_name if project_name else simobj_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        hh_path = out_dir / f"{v_mod_name}.hh"
        cc_path = out_dir / f"{v_mod_name}.cc"
        py_path = out_dir / f"{class_name}.py"

        # 自动生成 .hh + .py (如果不存在)
        if not hh_path.exists():
            print(f"  [GEN] 从 Verilog 自动生成 SimObject 骨架")
            ports, _, _ = extract_module_ports_from_verilog(v_path)
            gen_header(v_mod_name, class_name, ports, hh_path)
            gen_python_simobject(v_mod_name, class_name, ports, out_dir, project_name)
            update_sconscript(out_dir, v_mod_name, class_name, project_name)

        if cc_path.exists() and not args.force:
            print(f"  [SKIP] {v_mod_name}: .cc 已存在 (使用 --force 覆盖)")
            continue

        gen_for_module(v_mod_name, v_path, hh_path, cc_path, config, args.force)

    print(f"\n[DONE] 完成")


if __name__ == "__main__":
    main()
