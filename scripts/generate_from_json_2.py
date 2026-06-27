#!/usr/bin/env python3
"""
规范 JSON → Verilog 反向转换脚本。
用法: python generate_from_json.py <design.json> -o <输出.v>
"""

import argparse
import json
import sys
from utils.expr_emitter import emit_expr, emit_stmt


def generate_verilog(design):
    lines = []

    for inc in design.get("includes", []):
        lines.append(f'`include "{inc}"')

    for d in design.get("defines", []):
        lines.append(f'`define {d["name"]} {d["value"]}')

    if design.get("includes") or design.get("defines"):
        lines.append("")

    for mod in design.get("modules", []):
        lines.extend(_gen_module(mod))

    return "\n".join(lines)


def _gen_module(mod):
    lines = []
    name = mod["name"]

    has_params = bool(mod.get("parameters"))
    has_ports = bool(mod.get("ports"))

    if has_params:
        param_strs = []
        for p in mod["parameters"]:
            dtype = p.get("data_type") or p.get("type", "")
            if dtype in ("parameter", "localparam"):
                dtype = ""
            dtype_str = f" {dtype}" if dtype else ""
            param_strs.append(
                f"  parameter{dtype_str} {p['name']} = {p['value']}"
            )
        lines.append(f"module {name} #(")
        lines.append(",\n".join(param_strs))
        if has_ports:
            lines.append(") (")
        else:
            lines.append(")")

    if has_ports:
        port_strs = []
        for p in mod["ports"]:
            pdir = p["direction"]
            dtype = p.get("data_type", "wire")
            signed = p.get("signed", False)
            width = p.get("width", 1)
            width_expr = p.get("width_expr")
            width_str = ""
            if width_expr:
                width_str = f"[{width_expr}]"
            elif width > 1:
                width_str = f"[{width-1}:0]"
            type_parts = [dtype]
            if signed:
                type_parts.append("signed")
            type_str = " ".join(type_parts)
            port_strs.append(f"  {pdir} {type_str} {width_str} {p['name']}".rstrip())

        if not has_params:
            lines.append(f"module {name} (")
        lines.append(",\n".join(port_strs))
        lines.append(");")
    else:
        lines.append(f"module {name};")

    # Emit signal declarations (wire, reg, logic, integer, localparam, etc.)
    if mod.get("signals"):
        for s in mod["signals"]:
            stype = s.get("type", "wire")
            if stype == "localparam":
                dtype = s.get("data_type", "")
                dtype_str = f" {dtype}" if dtype else ""
                init = s.get("initial_value", "")
                lines.append(f"  localparam{dtype_str} {s['name']} = {init};")
                continue
            signed = "signed " if s.get("signed") else ""
            width = ""
            we = s.get("width_expr")
            if we:
                width = f"[{we}] "
            elif s.get("width", 1) > 1:
                width = f"[{s['width']-1}:0] "
            init = ""
            if s.get("initial_value"):
                init = f" = {s['initial_value']}"
            lines.append(f"  {stype} {signed}{width}{s['name']}{init};")

    if mod.get("functions"):
        lines.append("")
        for func in mod["functions"]:
            lines.extend(_gen_function(func))

    if mod.get("tasks"):
        lines.append("")
        for task in mod["tasks"]:
            lines.extend(_gen_task(task))

    if mod.get("always_blocks"):
        lines.append("")
        for ab in mod["always_blocks"]:
            lines.extend(_gen_always(ab))

    if mod.get("assignments"):
        lines.append("")
        for a in mod["assignments"]:
            delay = ""
            if a.get("delay"):
                delay = f" #{a['delay']['value']}"
            lhs = emit_expr(a["lhs"])
            rhs = emit_expr(a["rhs"])
            lines.append(f"  assign{delay} {lhs} = {rhs};")

    if mod.get("instances"):
        lines.append("")
        for inst in mod["instances"]:
            lines.extend(_gen_instance(inst))

    if mod.get("generates"):
        lines.append("")
        for gen in mod.get("generates", []):
            lines.extend(_gen_generate(gen))

    lines.append("endmodule\n")
    return lines


def _gen_function(func):
    lines = []
    ret = func["return_type"]
    inputs = func.get("inputs", [])
    if inputs:
        input_strs = [f"input {i['type']} {i['name']}" for i in inputs]
        lines.append(f"  function {ret} {func['name']}({', '.join(input_strs)});")
    else:
        lines.append(f"  function {ret} {func['name']};")
    for s in func.get("body", []):
        line = emit_stmt(s, 2)
        if line:
            lines.append(line)
    lines.append("  endfunction")
    return lines


def _gen_task(task):
    lines = []
    io = []
    for i in task.get("inputs", []):
        io.append(f"input {i['type']} {i['name']}")
    for o in task.get("outputs", []):
        io.append(f"output {o['type']} {o['name']}")
    if io:
        lines.append(f"  task {task['name']}({', '.join(io)});")
    else:
        lines.append(f"  task {task['name']};")
    for s in task.get("body", []):
        line = emit_stmt(s, 2)
        if line:
            lines.append(line)
    lines.append("  endtask")
    return lines


def _gen_always(ab):
    lines = []
    ab_type = ab["type"]
    sens_items = ab.get("sensitivity", [])
    if sens_items:
        # Check for wildcard sensitivity
        if any(s.get("type") == "wildcard" for s in sens_items):
            lines.append(f"  {ab_type} @(*) begin")
        else:
            sens_strs = []
            for si in sens_items:
                if si["type"] in ("posedge", "negedge"):
                    sens_strs.append(f"{si['type']} {si['signal']}")
                else:
                    sens_strs.append(si["signal"])
            lines.append(f"  {ab_type} @({' or '.join(sens_strs)}) begin")
    else:
        lines.append(f"  {ab_type} begin")
    for s in ab.get("body", []):
        line = emit_stmt(s, 2)
        if line:
            lines.append(line)
    lines.append("  end")
    return lines


def _gen_instance(inst):
    lines = []
    mod_name = inst["module"]
    inst_name = inst["name"]

    pmap = inst.get("parameter_mapping") or {}
    if pmap:
        lines.append(f"  {mod_name} #(")
        pstrs = [f"    .{k}({emit_expr(v)})" for k, v in pmap.items()]
        lines.append(",\n".join(pstrs))
        lines.append(f"  ) {inst_name} (")
    else:
        lines.append(f"  {mod_name} {inst_name} (")

    conns = inst.get("port_connections", [])
    if conns:
        cstrs = []
        for c in conns:
            conn_expr = emit_expr(c["connection"])
            cstrs.append(f"    .{c['port']}({conn_expr})")
        lines.append(",\n".join(cstrs))

    lines.append("  );")
    return lines


def _gen_generate(gen):
    lines = []
    gtype = gen.get("type", "if")
    if gtype == "gen_for":
        init_list = gen.get("init", [])
        step_list = gen.get("step", [])
        init_str = emit_stmt(init_list[0], 0) if init_list else ""
        step_str = emit_stmt(step_list[0], 0) if step_list else ""
        init_str = init_str.rstrip(";")
        step_str = step_str.rstrip(";")
        cond_str = emit_expr(gen.get("condition"))
        lines.append(f"  generate")
        lines.append(f"    for ({init_str}; {cond_str}; {step_str}) begin")
        for item in gen.get("body", []):
            if item.get("type") == "instance":
                for l in _gen_instance(item):
                    lines.append("      " + l)
            elif "lhs" in item:
                delay = ""
                if item.get("delay"):
                    delay = f" #{item['delay']['value']}"
                lhs = emit_expr(item["lhs"])
                rhs = emit_expr(item["rhs"])
                lines.append(f"      assign{delay} {lhs} = {rhs};")
        lines.append("    end")
        lines.append(f"  endgenerate")
        return lines

    cond = emit_expr(gen["condition"])
    lines.append(f"  generate")
    lines.append(f"    if ({cond}) begin")
    for item in gen.get("body", []):
        if item.get("type") == "instance":
            for l in _gen_instance(item):
                lines.append("    " + l)
        elif "lhs" in item:  # assign type
            delay = ""
            if item.get("delay"):
                delay = f" #{item['delay']['value']}"
            lhs = emit_expr(item["lhs"])
            rhs = emit_expr(item["rhs"])
            lines.append(f"    assign{delay} {lhs} = {rhs};")
    else_body = gen.get("else_body", [])
    if else_body:
        lines.append("    end else begin")
        for item in else_body:
            if item.get("type") == "instance":
                for l in _gen_instance(item):
                    lines.append("    " + l)
            elif "lhs" in item:
                delay = ""
                if item.get("delay"):
                    delay = f" #{item['delay']['value']}"
                lhs = emit_expr(item["lhs"])
                rhs = emit_expr(item["rhs"])
                lines.append(f"    assign{delay} {lhs} = {rhs};")
    lines.append("    end")
    lines.append(f"  endgenerate")
    return lines


def main():
    parser = argparse.ArgumentParser(description="规范 JSON → Verilog 反向生成")
    parser.add_argument("input", help="输入的规范 JSON 文件")
    parser.add_argument("-o", "--output", required=True, help="输出 .v 文件路径")
    args = parser.parse_args()

    with open(args.input) as f:
        design = json.load(f)

    code = generate_verilog(design)

    with open(args.output, "w") as f:
        f.write(code)
    print(f"[OK] 已生成 Verilog: {args.output}")
    print(f"     总行数: {len(code.splitlines())}")


if __name__ == "__main__":
    main()
