#!/usr/bin/env python3
"""
为自定义 Verilog 模块生成 Gem5 C++ SimObject 骨架文件。
读取设计 JSON，为每个唯一自定义模块类型生成 .hh / .cc / .py。
"""

import json
import argparse
import os
import sys


HH_TEMPLATE = r'''#ifndef __{{ guard }}_HH__
#define __{{ guard }}_HH__

#include "sim/clocked_object.hh"
#include "params/{{ class_name }}.hh"
#include "debug/SystemC.hh"
#include <vector>
#include <cstdint>

namespace gem5
{

class {{ class_name }} : public ClockedObject
{
  private:
    std::vector<uint64_t> inout_data;

    {% for sig in signals %}
    uint64_t {{ sig.name }};
    {% endfor %}

  public:
    {{ class_name }}(const {{ class_name }}Params &params);
    virtual ~{{ class_name }}();

    {% for port in ports %}
    {% if port.direction == "inout" %}
    void writeInout_{{ port.name }}(uint64_t val);
    uint64_t readInout_{{ port.name }}();
    {% elif port.direction == "input" %}
    void set{{ port.name | capitalize }}(uint64_t val);
    {% elif port.direction == "output" %}
    uint64_t get{{ port.name | capitalize }}();
    {% endif %}
    {% endfor %}

    void evaluate();

  protected:
    Tick clkTick();
};

} // namespace gem5

#endif // __{{ guard }}_HH__
'''


CC_TEMPLATE = r'''#include "{{ mod_type }}.hh"
#include "params/{{ class_name }}.hh"
#include "sim/system.hh"
#include "debug/SystemC.hh"

namespace gem5
{

{{ class_name }}::{{ class_name }}(const {{ class_name }}Params &params)
    : ClockedObject(params)
{
    DPRINTF(SystemC, "创建 {{ class_name }} 实例\\n");

    {% for sig in signals %}
    {{ sig.name }} = 0;
    {% endfor %}

    inout_data.resize({{ inout_count }});
}

{{ class_name }}::~{{ class_name }}()
{
    DPRINTF(SystemC, "销毁 {{ class_name }} 实例\\n");
}

{% for port in ports %}
{% if port.direction == "inout" %}
void
{{ class_name }}::writeInout_{{ port.name }}(uint64_t val)
{
    DPRINTF(SystemC, "[{{ class_name }}] 写入 inout 端口 %s = 0x%x\\n", "{{ port.name }}", val);
}

uint64_t
{{ class_name }}::readInout_{{ port.name }}()
{
    DPRINTF(SystemC, "[{{ class_name }}] 读取 inout 端口 %s\\n", "{{ port.name }}");
    return 0;
}
{% elif port.direction == "input" %}
void
{{ class_name }}::set{{ port.name | capitalize }}(uint64_t val)
{
    DPRINTF(SystemC, "[{{ class_name }}] 设置输入端口 %s = 0x%x\\n", "{{ port.name }}", val);
}
{% elif port.direction == "output" %}
uint64_t
{{ class_name }}::get{{ port.name | capitalize }}()
{
    DPRINTF(SystemC, "[{{ class_name }}] 读取输出端口 %s\\n", "{{ port.name }}");
    return 0;
}
{% endif %}
{% endfor %}

void
{{ class_name }}::evaluate()
{
    DPRINTF(SystemC, "[{{ class_name }}] evaluate() 调用\\n");
}

Tick
{{ class_name }}::clkTick()
{
    DPRINTF(SystemC, "[{{ class_name }}] clkTick() 调用\\n");
    evaluate();
    return clockPeriod();
}

} // namespace gem5
'''


PY_TEMPLATE = r'''from m5.SimObject import SimObject
from m5.params import *
from m5.proxy import *


class {{ class_name }}(SimObject):
    type = "{{ class_name }}"
    cxx_header = "{{ mod_type }}.hh"
    cxx_class = "gem5::{{ class_name }}"

    {% for port in ports %}
    {% if port.direction == "inout" %}
    {{ port.name }} = VectorParam.Unsigned(
        "双向端口 {{ port.name }} (位宽: {{ port.width }})"
    )
    {% elif port.direction == "input" %}
    {{ port.name }} = Param.Unsigned(
        {{ port.width }},
        "输入端口 {{ port.name }} (位宽: {{ port.width }})"
    )
    {% elif port.direction == "output" %}
    {{ port.name }} = Param.Unsigned(
        {{ port.width }},
        "输出端口 {{ port.name }} (位宽: {{ port.width }})"
    )
    {% endif %}
    {% endfor %}
'''


def camel_to_pascal(name):
    return name[0].upper() + name[1:] if name else name


def infer_module_interfaces(design):
    """
    从设计 JSON 中的实例化连接推断每个模块类型的端口接口。
    """
    interfaces = {}

    for mod in design.get("modules", []):
        for inst in mod.get("instances", []):
            mod_type = inst["module"]
            if mod_type not in interfaces:
                interfaces[mod_type] = {"ports": [], "signals": []}
            for conn in inst.get("port_connections", []):
                port_name = conn["port"]
                # 检查是否已存在同名端口
                existing = [p for p in interfaces[mod_type]["ports"]
                           if p["name"] == port_name]
                if not existing:
                    # 推断端口方向 (无法精确知道, 默认 input)
                    direction = "input"
                    if conn.get("connection", {}).get("ref", "").startswith("inst_"):
                        direction = "output"
                    interfaces[mod_type]["ports"].append({
                        "name": port_name,
                        "direction": direction,
                        "width": 32,
                        "data_type": "wire",
                    })

        # 也检查 generate 块
        for gen in mod.get("generates", []):
            for item in gen.get("body", []):
                if item.get("type") == "instance":
                    mod_type = item["module"]
                    if mod_type not in interfaces:
                        interfaces[mod_type] = {"ports": [], "signals": []}
                    for conn in item.get("port_connections", []):
                        port_name = conn["port"]
                        existing = [p for p in interfaces[mod_type]["ports"]
                                   if p["name"] == port_name]
                        if not existing:
                            interfaces[mod_type]["ports"].append({
                                "name": port_name,
                                "direction": "input",
                                "width": 32,
                                "data_type": "wire",
                            })

    # 也为顶层模块创建接口 (如果有详细端口定义)
    for mod in design.get("modules", []):
        mod_name = mod["name"]
        if mod_name not in interfaces:
            interfaces[mod_name] = {"ports": [], "signals": []}
        for p in mod.get("ports", []):
            existing = [x for x in interfaces[mod_name]["ports"]
                       if x["name"] == p["name"]]
            if not existing:
                interfaces[mod_name]["ports"].append({
                    "name": p["name"],
                    "direction": p["direction"],
                    "width": p.get("width", 1),
                    "data_type": p.get("data_type", "wire"),
                    "signed": p.get("signed", False),
                })
        for s in mod.get("signals", []):
            existing = [x for x in interfaces[mod_name]["signals"]
                       if x["name"] == s["name"]]
            if not existing:
                interfaces[mod_name]["signals"].append({
                    "name": s["name"],
                    "width": s.get("width", 1),
                    "type": s.get("type", "reg"),
                })

    return interfaces


def generate_simobjects(design, output_dir):
    interfaces = infer_module_interfaces(design)

    os.makedirs(output_dir, exist_ok=True)

    generated = []
    for mod_type, iface in interfaces.items():
        class_name = camel_to_pascal(mod_type)
        guard = class_name.upper()
        ports = iface["ports"]
        signals = iface["signals"]
        inout_count = sum(1 for p in ports if p["direction"] == "inout")

        # 处理模板
        from jinja2 import Environment, BaseLoader
        env = Environment(loader=BaseLoader())

        # 自定义 capitalize 过滤器
        def capitalize(s):
            return s[0].upper() + s[1:] if s else s
        env.filters["capitalize"] = capitalize

        # .hh
        hh_code = env.from_string(HH_TEMPLATE).render(
            class_name=class_name,
            mod_type=mod_type,
            guard=guard,
            ports=ports,
            signals=signals,
            inout_count=inout_count,
        )
        hh_path = os.path.join(output_dir, f"{mod_type}.hh")
        with open(hh_path, "w") as f:
            f.write(hh_code)
        generated.append(hh_path)

        # .cc
        cc_code = env.from_string(CC_TEMPLATE).render(
            class_name=class_name,
            mod_type=mod_type,
            ports=ports,
            signals=signals,
            inout_count=inout_count,
        )
        cc_path = os.path.join(output_dir, f"{mod_type}.cc")
        with open(cc_path, "w") as f:
            f.write(cc_code)
        generated.append(cc_path)

        # .py (SimObject Python 绑定)
        py_code = env.from_string(PY_TEMPLATE).render(
            class_name=class_name,
            mod_type=mod_type,
            ports=ports,
        )
        py_path = os.path.join(output_dir, f"{mod_type}.py")
        with open(py_path, "w") as f:
            f.write(py_code)
        generated.append(py_path)

        print(f"  [OK] 生成 {mod_type}:")
        print(f"       {hh_path}")
        print(f"       {cc_path}")
        print(f"       {py_path}")

    return generated


def main():
    parser = argparse.ArgumentParser(description="为自定义模块生成 Gem5 SimObject")
    parser.add_argument("--input", default="example_design_complete.json",
                        help="输入设计 JSON")
    parser.add_argument("--project", default=None,
                        help="项目名 (rtl 子目录名)")
    parser.add_argument("--output-dir", default="gem5/src/custom",
                        help="输出目录")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = args.input if os.path.isabs(args.input) else os.path.join(base_dir, args.input)
    output_dir = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(base_dir, args.output_dir)

    with open(input_path) as f:
        design = json.load(f)

    print(f"[阶段 3] 生成自定义 SimObject 骨架")
    print(f"  输入: {input_path}")
    print(f"  输出: {output_dir}")
    print()

    generated = generate_simobjects(design, output_dir)

    print()
    print(f"  共生成 {len(generated)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
