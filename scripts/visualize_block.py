#!/usr/bin/env python3
"""
规范 JSON → Block Design 可视化脚本 (Graphviz DOT / SVG / HTML)。
用法: python visualize_block.py <design.json> [--format svg|png|dot|html] -o <输出文件>
"""

import argparse
import json
import os
import sys
from html import escape
from pathlib import Path


def generate_dot(design):
    """生成 Graphviz DOT 格式的 Block Design 图。"""
    lines = []
    lines.append("digraph BlockDesign {")
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=record, style=filled, fillcolor=lightblue, fontname=\"Courier\"];")
    lines.append("    edge [fontname=\"Courier\", fontsize=10];")
    lines.append("    splines=ortho;")
    lines.append("")

    for mod in design.get("modules", []):
        mod_name = mod["name"]
        is_top = (design.get("design_hierarchy", {}).get("top") == mod_name)

        cluster_label = f"  label=\"{mod_name}\";"
        if is_top:
            cluster_label = f'  label="{mod_name} (top)";\n    style=filled;\n    fillcolor=lightyellow;'

        lines.append(f"  subgraph cluster_{_dot_id(mod_name)} {{")
        lines.append(f"    {cluster_label}")
        lines.append(f'    color="{ "blue" if is_top else "black" }";')

        input_ports = [p for p in mod.get("ports", []) if p["direction"] == "input"]
        output_ports = [p for p in mod.get("ports", []) if p["direction"] == "output"]

        for inst in mod.get("instances", []):
            inst_name = inst["name"]
            inst_mod = inst["module"]

            in_pins = []
            out_pins = []
            for c in inst.get("port_connections", []):
                port_name = c["port"]
                conn = c.get("connection", {})
                if isinstance(conn, dict):
                    conn_str = conn.get("ref", conn.get("literal", "?"))
                else:
                    conn_str = str(conn) if conn is not None else "?"
                if isinstance(conn, dict) and isinstance(conn.get("literal"), str) and conn["literal"].startswith("32"):
                    pass
                in_pins.append(f"<{port_name}> {port_name}")

            if in_pins:
                in_label = " | ".join(in_pins)
            else:
                in_label = ""

            if out_pins:
                out_label = " | ".join(out_pins)
            else:
                out_label = ""

            if in_label and out_label:
                full_label = f"{{{in_label}}} | {inst_mod} | {{{out_label}}}"
            elif in_label:
                full_label = f"{{{in_label}}} | {inst_mod}"
            elif out_label:
                full_label = f"{inst_mod} | {{{out_label}}}"
            else:
                full_label = inst_mod

            lines.append(f'    {_dot_id(inst_name)} [label="{_dot_label(full_label)}"];')

        if input_ports:
            in_label = " | ".join(f"<{p['name']}> {p['name']}" for p in input_ports)
            lines.append(f'    top_inputs [label="{_dot_label("{" + in_label + "} | Inputs")}", shape=box, fillcolor=lightgreen];')
        if output_ports:
            out_label = " | ".join(f"<{p['name']}> {p['name']}" for p in output_ports)
            lines.append(f'    top_outputs [label="{_dot_label("Outputs | {" + out_label + "}")}", shape=box, fillcolor=lightcoral];')

        lines.append("  }")
        lines.append("")

        for inst in mod.get("instances", []):
            for c in inst.get("port_connections", []):
                conn = c.get("connection")
                if not isinstance(conn, dict):
                    continue
                conn_str = ""
                if "ref" in conn:
                    conn_str = conn["ref"]
                elif "literal" in conn:
                    conn_str = conn["literal"]
                if conn_str:
                    label = c["port"]
                    lines.append(f'    {_dot_id(conn_str)} -> {_dot_id(inst["name"])}:{_dot_port(c["port"])} [label="{_dot_label(label)}"];')

        for a in mod.get("assignments", []):
            lhs = a.get("lhs") if isinstance(a.get("lhs"), dict) else {}
            rhs = a.get("rhs") if isinstance(a.get("rhs"), dict) else {}
            lhs_str = lhs.get("ref", "")
            rhs_str = rhs.get("ref", "")
            if lhs_str and rhs_str:
                lines.append(f'    {_dot_id(rhs_str)} -> {_dot_id(lhs_str)} [label="assign", style=dashed, color=green];')

    lines.append("}")
    return "\n".join(lines)


def _dot_id(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _dot_label(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _dot_port(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _expr_to_text(expr):
    if isinstance(expr, dict):
        for key in ("ref", "literal", "value", "name"):
            if key in expr:
                return str(expr[key])
        if expr.get("type") in ("bit_select", "select"):
            source = _expr_to_text(expr.get("source") or expr.get("base"))
            index = _expr_to_text(expr.get("index"))
            if index:
                return f"{source}[{index}]"
            range_obj = expr.get("range") or {}
            if isinstance(range_obj, dict) and "msb" in range_obj and "lsb" in range_obj:
                return f"{source}[{_expr_to_text(range_obj.get('msb'))}:{_expr_to_text(range_obj.get('lsb'))}]"
            return source
        if expr.get("type") == "concat":
            return "{" + ", ".join(_expr_to_text(part) for part in expr.get("parts", [])) + "}"
        if expr.get("type") == "cond":
            return f"{_expr_to_text(expr.get('condition'))} ? {_expr_to_text(expr.get('true_expr'))} : {_expr_to_text(expr.get('false_expr'))}"
        if "index" in expr:
            return f"{_expr_to_text(expr.get('base'))}[{_expr_to_text(expr.get('index'))}]"
        if "left" in expr and "right" in expr:
            return f"{_expr_to_text(expr.get('left'))} {expr.get('op', '?')} {_expr_to_text(expr.get('right'))}"
        if "operand" in expr:
            return f"{expr.get('op', '')}{_expr_to_text(expr.get('operand'))}"
        return json.dumps(expr, ensure_ascii=False)
    if expr is None:
        return ""
    return str(expr)


def _width_to_text(width):
    if isinstance(width, dict):
        return _expr_to_text(width)
    if width in (None, ""):
        return "1"
    return str(width)


def _port_signature(port):
    direction = port.get("direction", "")
    width = _width_to_text(port.get("width"))
    name = port.get("name", "")
    return f"{direction} [{width}] {name}" if width != "1" else f"{direction} {name}"


def _build_visual_model(design):
    modules = design.get("modules", [])
    module_names = {m.get("name") for m in modules}
    top_name = design.get("design_hierarchy", {}).get("top") or (modules[0].get("name") if modules else "")
    visual_modules = []

    for mod in modules:
        mod_name = mod.get("name", "unknown")
        ports = mod.get("ports", [])
        signals = mod.get("signals", [])
        instances = mod.get("instances", [])
        assignments = mod.get("assignments", [])
        signal_names = {s.get("name") for s in signals}

        nodes = [
            {
                "id": f"port:{p.get('name')}",
                "label": p.get("name", ""),
                "kind": f"port {p.get('direction', '')}".strip(),
                "type": "port",
                "direction": p.get("direction", ""),
                "width": _width_to_text(p.get("width")),
                "summary": _port_signature(p),
                "raw": p,
            }
            for p in ports
        ]
        nodes.extend(
            {
                "id": f"inst:{index}:{inst.get('name')}",
                "label": inst.get("name", ""),
                "subtitle": inst.get("module", ""),
                "kind": "instance",
                "type": "instance",
                "isKnownModule": inst.get("module") in module_names,
                "summary": f"{inst.get('name', '')}: {inst.get('module', '')}",
                "raw": inst,
            }
            for index, inst in enumerate(instances)
        )

        edges = []
        used_signals = set()
        for index, inst in enumerate(instances):
            inst_id = f"inst:{index}:{inst.get('name')}"
            for conn in inst.get("port_connections", []):
                conn_text = _expr_to_text(conn.get("connection"))
                if not conn_text:
                    continue
                used_signals.add(conn_text)
                source_id = f"signal:{conn_text}" if conn_text in signal_names else f"external:{conn_text}"
                edges.append(
                    {
                        "source": source_id,
                        "target": inst_id,
                        "label": conn.get("port", ""),
                        "signal": conn_text,
                        "kind": "connection",
                    }
                )

        for assign in assignments:
            lhs = _expr_to_text(assign.get("lhs"))
            rhs = _expr_to_text(assign.get("rhs"))
            if lhs and rhs:
                used_signals.update([lhs, rhs])
                edges.append(
                    {
                        "source": f"signal:{rhs}" if rhs in signal_names else f"external:{rhs}",
                        "target": f"signal:{lhs}" if lhs in signal_names else f"external:{lhs}",
                        "label": "assign",
                        "signal": f"{rhs} -> {lhs}",
                        "kind": "assign",
                    }
                )

        signal_nodes = []
        for sig in signals:
            name = sig.get("name", "")
            if name in used_signals or len(signals) <= 60:
                signal_nodes.append(
                    {
                        "id": f"signal:{name}",
                        "label": name,
                        "kind": sig.get("type", "signal"),
                        "type": "signal",
                        "width": _width_to_text(sig.get("width")),
                        "summary": f"{sig.get('type', 'signal')} [{_width_to_text(sig.get('width'))}] {name}",
                        "raw": sig,
                    }
                )

        existing_ids = {n["id"] for n in nodes + signal_nodes}
        external_nodes = sorted(
            {
                edge[endpoint]
                for edge in edges
                for endpoint in ("source", "target")
                if edge[endpoint] not in existing_ids
            }
        )
        nodes.extend(signal_nodes)
        nodes.extend(
            {
                "id": ext,
                "label": ext.split(":", 1)[1],
                "kind": "external/literal",
                "type": "external",
                "summary": ext.split(":", 1)[1],
                "raw": {"value": ext.split(":", 1)[1]},
            }
            for ext in external_nodes[:80]
        )
        allowed_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in allowed_ids and e["target"] in allowed_ids]

        visual_modules.append(
            {
                "name": mod_name,
                "description": mod.get("description", ""),
                "isTop": mod_name == top_name,
                "counts": {
                    "ports": len(ports),
                    "signals": len(signals),
                    "instances": len(instances),
                    "assignments": len(assignments),
                    "alwaysBlocks": len(mod.get("always_blocks", [])),
                },
                "ports": ports,
                "signals": signals,
                "instances": instances,
                "nodes": nodes,
                "edges": edges,
                "raw": mod,
            }
        )

    return {
        "project": design.get("project", {}),
        "top": top_name,
        "moduleCount": len(modules),
        "modules": visual_modules,
    }


def generate_html_svg_wrapper(svg_path, design):
    """兼容旧 --html 参数；实际使用新的分离式前端。"""
    return generate_interactive_html(design)


def generate_interactive_html(design):
    """生成交互式 HTML；前端代码位于 scripts/visualizer_frontend。"""
    frontend_dir = Path(__file__).resolve().parent / "visualizer_frontend"
    template = (frontend_dir / "template.html").read_text(encoding="utf-8")
    css = (frontend_dir / "style.css").read_text(encoding="utf-8")
    js = (frontend_dir / "app.js").read_text(encoding="utf-8")

    model = _build_visual_model(design)
    title = model.get("top") or "Block Design"
    payload = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")

    return (
        template
        .replace("__TITLE__", escape(title))
        .replace("__CSS__", css)
        .replace("__MODEL__", payload)
        .replace("__JS__", js)
    )


def main():
    parser = argparse.ArgumentParser(description="规范 JSON → Block Design 可视化")
    parser.add_argument("input", help="输入的规范 JSON 文件")
    parser.add_argument("--format", choices=["svg", "png", "dot", "html"], default="svg", help="输出格式")
    parser.add_argument("-o", "--output", default="design_block.svg", help="输出文件路径")
    parser.add_argument("--html", action="store_true", help="同时生成交互式 HTML")
    args = parser.parse_args()

    with open(args.input) as f:
        design = json.load(f)

    dot_source = generate_dot(design)
    output_base = os.path.splitext(args.output)[0]

    if args.format == "html":
        html_content = generate_interactive_html(design)
        with open(args.output, "w") as f:
            f.write(html_content)
        print(f"[OK] 已生成交互式 HTML: {args.output}")
        return

    if args.format == "dot" or not _graphviz_available():
        dot_output = args.output if args.format == "dot" else output_base + ".dot"
        with open(dot_output, "w") as f:
            f.write(dot_source)
        print(f"[OK] 已生成 DOT 文件: {dot_output}")
        if args.format != "dot" and not _graphviz_available():
            print("     提示: 安装 graphviz Python 包可渲染为 SVG/PNG: pip install graphviz")
    else:
        import graphviz
        src = graphviz.Source(dot_source)
        src.format = args.format
        src.render(outfile=args.output, cleanup=True)
        print(f"[OK] 已生成 {args.format.upper()} 文件: {args.output}")

    if args.html:
        html_path = output_base + ".html"
        html_content = generate_html_svg_wrapper(args.output, design)
        with open(html_path, "w") as f:
            f.write(html_content)
        print(f"[OK] 已生成交互式 HTML: {html_path}")


def _graphviz_available():
    try:
        import graphviz
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
