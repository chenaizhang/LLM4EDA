#!/usr/bin/env python3
"""
生成 Gem5 顶层 Python 配置文件 (top.py)。
读取设计 JSON 摘要，生成完整的 m5.objects 配置。
"""

import json
import argparse
import os
import sys

from jinja2 import Environment, BaseLoader

TOP_TEMPLATE = r'''#!/usr/bin/env python3
"""
Gem5 仿真顶层配置 — 由 gen_top.py 自动生成
设计: {{ design_name }}
"""

import m5
from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath

import os

# ============================================================
# 1. 系统创建
# ============================================================
system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

# ============================================================
# 2. 自定义模块实例化
# ============================================================
{% for mod in custom_modules %}
{{ mod.py_name }} = {{ mod.class_name }}()
system.{{ mod.py_name }} = {{ mod.py_name }}
{% endfor %}

# ============================================================
# 3. 内存与总线
# ============================================================
system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# ============================================================
# 4. 调试设置
# ============================================================
try:
    import m5.debug
    m5.debug.flags["SystemC"].enable()
except Exception:
    pass

# ============================================================
# 5. 初始化与运行
# ============================================================
root = Root(full_system=False, system=system)
m5.instantiate()

print("[SIM] 仿真开始")
exit_event = m5.simulate(100000)
print(f"[SIM] 仿真结束: {exit_event.getCause()}")
'''


def camel_to_snake(name):
    result = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)


def generate_config(design_summary):
    custom_modules = []
    internal_nets = []
    connections = []

    # 解析顶层模块
    top = design_summary.get("top_module", "top")
    modules = design_summary.get("modules", [])

    # 找到顶层模块详情
    top_mod_detail = None
    for mod in modules:
        if mod["name"] == top:
            top_mod_detail = mod
            break

    seen_types = set()
    if top_mod_detail:
        # 创建内部信号 (来自顶层模块的 signals)
        # 注意: design_summary 只包含 modules summary, 信号在原始 JSON 里
        # 我们直接从原始设计 JSON 中获取 signals 和内部连线
        pass

    # 收集所有需要实例化的自定义模块类型
    custom_type_names = design_summary.get("custom_types", [])

    # 为每个自定义类型创建实例
    for ct in custom_type_names:
        if ct == top:
            continue
        if ct not in seen_types:
            seen_types.add(ct)
            class_name = "".join(word.capitalize() for word in ct.split("_"))
            custom_modules.append({
                "name": ct,
                "type": ct,
                "class_name": class_name,
                "py_name": camel_to_snake(ct),
            })

    # 从设计模块中提取端口和内部信号连接
    for mod in modules:
        for port in mod.get("ports", []):
            pname = port["name"]
            if port["direction"] == "inout":
                internal_nets.append({
                    "name": f"net_{mod['name']}_{pname}",
                    "width": port["width"],
                })
                connections.append({
                    "description": f"{mod['name']}.{pname} (inout, width={port['width']})",
                    "direction": "inout",
                    "expr": f"# TODO: 连接 inout 端口 {mod['name']}.{pname}",
                })
            elif port["direction"] == "input":
                connections.append({
                    "description": f"{mod['name']}.{pname} 输入端口",
                    "direction": "input",
                    "expr": f"# TODO: 驱动输入端口 {mod['name']}.{pname}",
                })
            elif port["direction"] == "output":
                connections.append({
                    "description": f"{mod['name']}.{pname} 输出端口",
                    "direction": "output",
                    "expr": f"# TODO: 读取输出端口 {mod['name']}.{pname}",
                })

    env = Environment(loader=BaseLoader())
    template = env.from_string(TOP_TEMPLATE)
    code = template.render(
        design_name=design_summary.get("design_name", "unknown"),
        top_module=top,
        custom_modules=custom_modules,
        internal_nets=internal_nets,
        connections=connections,
    )
    return code


def main():
    parser = argparse.ArgumentParser(description="生成 Gem5 顶层 Python 配置")
    parser.add_argument("--input", default="output/design_summary.json",
                        help="设计摘要 JSON (parse_design.py 输出)")
    parser.add_argument("--design", default="example_design_complete.json",
                        help="原始设计 JSON 文件")
    parser.add_argument("--output", default="output/configs/top.py",
                        help="输出的 Gem5 配置路径")
    parser.add_argument("--project", default=None,
                        help="项目名 (rtl 子目录名)，用于输出到 output/configs/<project>/top.py")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_path = args.input if os.path.isabs(args.input) else os.path.join(base_dir, args.input)
    design_path = args.design if os.path.isabs(args.design) else os.path.join(base_dir, args.design)

    # 如果指定了 --project，将输出放到 output/configs/<project>/top.py
    if args.project:
        output_path = os.path.join(base_dir, "output", "configs", args.project, "top.py")
    else:
        output_path = args.output if os.path.isabs(args.output) else os.path.join(base_dir, args.output)

    with open(input_path) as f:
        summary = json.load(f)

    # 加载原始设计以获取完整端口/信号信息
    with open(design_path) as f:
        raw_design = json.load(f)

    # 合并信号和 always/assign 信息
    # 提取原始模块信号
    for mod in raw_design.get("modules", []):
        for sm in summary.get("modules", []):
            if sm["name"] == mod["name"]:
                sm["_signals"] = mod.get("signals", [])
                sm["_assignments"] = mod.get("assignments", [])
                sm["_always_blocks"] = mod.get("always_blocks", [])

    code = generate_config(summary)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(code)
    print(f"[OK] Gem5 顶层配置已生成: {output_path}")
    print(f"     总行数: {len(code.splitlines())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
