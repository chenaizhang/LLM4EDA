#!/usr/bin/env python3
"""
设计规格解析脚本。
从 example_design_complete.json 提取模块拓扑、连接和层级信息。
"""

import json
import argparse
import os
import sys


def load_json(path):
    with open(path) as f:
        return json.load(f)


def extract_modules(design):
    modules = []
    for mod in design.get("modules", []):
        entry = {
            "name": mod["name"],
            "type": "module",
            "parameters": [],
            "ports": [],
            "has_inout": False,
            "inout_ports": [],
            "instances": [],
        }
        for p in mod.get("parameters", []):
            entry["parameters"].append({
                "name": p["name"],
                "type": p.get("type", p.get("data_type", "int")),
                "value": p["value"],
            })
        for p in mod.get("ports", []):
            port_entry = {
                "name": p["name"],
                "direction": p["direction"],
                "width": p["width"],
                "data_type": p.get("data_type", "wire"),
                "signed": p.get("signed", False),
            }
            entry["ports"].append(port_entry)
            if p["direction"] == "inout":
                entry["has_inout"] = True
                entry["inout_ports"].append(port_entry)
        for inst in mod.get("instances", []):
            entry["instances"].append({
                "name": inst["name"],
                "module_type": inst["module"],
            })
        for gen in mod.get("generates", []):
            for item in gen.get("body", []):
                if item.get("type") == "instance":
                    entry["instances"].append({
                        "name": item["name"],
                        "module_type": item["module"],
                        "generate": True,
                    })
        modules.append(entry)
    return modules


def extract_connections(design):
    connections = []
    for mod in design.get("modules", []):
        for inst in mod.get("instances", []):
            for conn in inst.get("port_connections", []):
                connection_entry = {
                    "type": "instance",
                    "source_module": mod["name"],
                    "instance": inst["name"],
                    "instance_type": inst["module"],
                    "port": conn["port"],
                    "connection": conn["connection"],
                }
                connections.append(connection_entry)
    return connections


def extract_hierarchy(design):
    hier = design.get("design_hierarchy", {})
    return {
        "top_module": hier.get("top", ""),
        "tree": hier.get("tree", {}),
    }


def find_custom_types(design, standard_types=None):
    if standard_types is None:
        standard_types = {"cpu", "cache", "memory", "bus", "bridge",
                          "X86TimingSimpleCPU", "X86O3CPU",
                          "DDR3_1600_8x8", "SimpleMemory",
                          "SystemXBar", "Crossbar", "Bridge"}
    all_types = set()
    for mod in design.get("modules", []):
        all_types.add(mod["name"])
        for inst in mod.get("instances", []):
            all_types.add(inst["module"])
        for gen in mod.get("generates", []):
            for item in gen.get("body", []):
                if item.get("type") == "instance":
                    all_types.add(item["module"])
    custom = sorted(all_types - standard_types)
    return custom


def main():
    parser = argparse.ArgumentParser(description="解析设计 JSON，提取拓扑摘要")
    parser.add_argument("input", nargs="?", default="example_design_complete.json",
                        help="输入设计 JSON 文件路径")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 JSON 摘要路径 (默认输出到 stdout)")
    parser.add_argument("--project", default=None,
                        help="项目名，用于输出到 output/<project>_summary.json")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = args.input if os.path.isabs(args.input) else os.path.join(base_dir, args.input)

    design = load_json(input_path)

    summary = {
        "design_name": design.get("metadata", {}).get("design_name", "unknown"),
        "version": design.get("version", ""),
        "top_module": extract_hierarchy(design)["top_module"],
        "hierarchy_tree": extract_hierarchy(design)["tree"],
        "modules": extract_modules(design),
        "connections": extract_connections(design),
        "custom_types": find_custom_types(design),
        "has_bidirectional_ports": any(
            p["direction"] == "inout"
            for mod in design.get("modules", [])
            for p in mod.get("ports", [])
        ),
        "total_modules": len(design.get("modules", [])),
        "total_connections": sum(
            len(inst.get("port_connections", []))
            for mod in design.get("modules", [])
            for inst in mod.get("instances", [])
        ),
    }

    output = args.output
    if args.project and not output:
        output_path = os.path.join(base_dir, "output", f"design_{args.project}.json")
    elif output:
        output_path = output if os.path.isabs(output) else os.path.join(base_dir, output)
    else:
        output_path = None
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[OK] 设计摘要已写入: {output_path}")
    else:
        print(json.dumps(summary, indent=2))

    print(f"\n统计:")
    print(f"  模块数: {summary['total_modules']}")
    print(f"  连接数: {summary['total_connections']}")
    print(f"  自定义类型: {summary['custom_types']}")
    print(f"  含双向端口: {summary['has_bidirectional_ports']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
