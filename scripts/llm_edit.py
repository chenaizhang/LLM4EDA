#!/usr/bin/env python3
"""
LLM 交互式编辑：用自然语言修改设计 JSON，自动重新生成 Verilog + Block Design。

工作方式：
  1. 读取 specs/schema_v1.json 获取 JSON 规范结构
  2. 将规范 + 用户需求发送给 LLM
  3. LLM 返回结构化变更指令（增/删/改 操作列表）
  4. 程序化地应用到原始 JSON 上（不依赖 LLM 完整重现 JSON）

用法:
  python scripts/llm_edit.py --config                        # 配置 API
  python scripts/llm_edit.py output/design.json -p "..."     # 单次修改
  python scripts/llm_edit.py output/design.json -i           # 交互会话
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "opencode_config.json"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "specs" / "schema_v1.json"


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def load_config():
    if not CONFIG_PATH.exists():
        return {"llm": {"api_url": "https://api.openai.com/v1", "api_key": "", "model": "gpt-4o"}}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    print(f"[OK] 配置已保存到 {CONFIG_PATH}")


def setup_config():
    cfg = load_config()
    llm = cfg.setdefault("llm", {})
    cur_url = llm.get("api_url", "https://api.openai.com/v1")
    cur_key = llm.get("api_key", "")
    cur_model = llm.get("model", "gpt-4o")

    print("=== LLM 配置（直接回车保留当前值） ===")
    url = input(f"API URL [{cur_url}]: ").strip() or cur_url
    hint = cur_key[:8] + "..." if cur_key else "(空)"
    key = input(f"API Key [{hint}]: ").strip() or cur_key
    model = input(f"Model [{cur_model}]: ").strip() or cur_model
    llm.update(api_url=url, api_key=key, model=model)
    save_config(cfg)


# ---------------------------------------------------------------------------
# LLM 调用
# ---------------------------------------------------------------------------

def call_llm(system_prompt, user_prompt, config):
    import urllib.error
    import urllib.request

    llm = config.get("llm", {})
    api_url = llm.get("api_url", "").rstrip("/")
    api_key = llm.get("api_key", "")
    model = llm.get("model", "gpt-4o")

    if not api_key:
        print("[ERROR] API Key 未配置，请先运行: python scripts/llm_edit.py --config")
        sys.exit(1)

    endpoint = f"{api_url}/chat/completions" if "/v1" in api_url else f"{api_url}/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 从 LLM 回复中提取变更指令
# ---------------------------------------------------------------------------

def extract_json(text):
    raw = text.strip()
    m = re.search(r'```(?:json)?\s*\n(.+?)\n```', raw, re.DOTALL)
    if m:
        raw = m.group(1).strip()
    brace_start = raw.find("{")
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    raw = raw[brace_start:i + 1]
                    break
    raw = re.sub(r',\s*}', "}", raw)
    raw = re.sub(r',\s*]', "]", raw)
    raw = re.sub(r"(?<!\\)'", '"', raw)
    raw = re.sub(r'(?<!")\btrue\b(?!")', "true", raw, flags=re.IGNORECASE)
    raw = re.sub(r'(?<!")\bfalse\b(?!")', "false", raw, flags=re.IGNORECASE)
    raw = re.sub(r'(?<!")\bnull\b(?!")', "null", raw, flags=re.IGNORECASE)
    raw = re.sub(r'//[^\n]*', '', raw)
    raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)
    for _ in range(3):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = re.sub(r'(?<=[{,])\s*(\w+)\s*:', r'"\1":', raw)
    lines = raw.split("\n")
    buf = ""
    for line in lines:
        buf += line + "\n"
        if buf.count("{") > 0 and buf.count("{") == buf.count("}"):
            try:
                return json.loads(buf)
            except json.JSONDecodeError:
                pass
            buf = ""
    print("[ERROR] 无法从 LLM 回复中提取有效 JSON")
    print("--- LLM 原始回复前 500 字符 ---")
    print(text[:500])
    sys.exit(1)


# ---------------------------------------------------------------------------
# JSON Patch 应用
# ---------------------------------------------------------------------------

def resolve_path(root, path_str):
    """按 modules[0].ports[1].width 路径访问对象，返回 (父对象, 最后一段的key, 是否有数组索引)。"""
    parts = re.findall(r'(\w+)(?:\[(-?\d+|)\])?', path_str)
    obj = root
    for i, (key, idx) in enumerate(parts):
        if i == len(parts) - 1:
            return obj, key, idx
        if idx:
            obj = obj[key][int(idx)]
        else:
            obj = obj[key]
    return root, None, ''


def apply_changes(design, changes):
    for c in changes:
        op = c.get("op")
        path = c.get("path", "")
        parent, key, idx = resolve_path(design, path)

        try:
            if op == "replace":
                if idx:
                    parent[key][int(idx)] = c["value"]
                else:
                    parent[key] = c["value"]

            elif op == "add":
                if key in parent and isinstance(parent[key], list):
                    parent[key].append(c["value"])
                else:
                    parent[key] = c["value"]

            elif op == "remove":
                if idx:
                    parent[key].pop(int(idx))
                else:
                    del parent[key]
        except Exception as e:
            print(f"  [WARN] 应用变更失败: {path} - {e}")

    return design


# ---------------------------------------------------------------------------
# 构建 system prompt（含 schema 结构）
# ---------------------------------------------------------------------------

def build_system_prompt():
    schema_path = SCHEMA_PATH
    schema_info = ""
    if schema_path.exists():
        schema = json.loads(schema_path.read_text())
        schema_info = json.dumps(schema, indent=2)

    return f"""你是一个 Verilog 芯片设计助手。用户会给你一个设计 JSON 和修改需求。

你的任务：返回一个包含 **最小变更指令** 的 JSON 对象，而不是返回整个设计 JSON。

## 输出格式

返回一个 JSON 对象，其中 key "changes" 包含变更操作列表：

```json
{{
  "changes": [
    {{ "op": "replace", "path": "modules[0].ports[0].width", "value": 64 }},
    {{ "op": "add", "path": "modules[0].ports[-]", "value": {{"name":"debug","direction":"output","data_type":"wire","width":32,"signed":false}} }},
    {{ "op": "remove", "path": "modules[0].signals[2]" }}
  ]
}}
```

## 操作类型

| op | 说明 | path 格式 |
|----|------|-----------|
| replace | 修改已有字段的值 | modules[0].ports[0].width |
| add | 添加新字段或数组元素 | modules[0].ports[-] （- 表示追加到数组末尾） |
| remove | 删除字段或数组元素 | modules[0].signals[2] |

## 路径规则

- 用点号连接，数组用 [索引] 表示
- 索引从 0 开始
- -1 表示最后一个元素

## 设计 JSON 结构（依据规范）

{schema_info}

## 关键约束

- value 中涉及表达式（表达式 AST）的字段：connection、rhs、lhs、condition、value(参数) 等必须使用规范中的 AST 对象格式
  - 信号引用: {{"ref": "signal_name"}}
  - 字面量: {{"literal": "32'hDEAD_BEEF"}}
  - 二元运算: {{"op": "+", "left": {{...}}, "right": {{...}}}}
  - 位选择: {{"type": "select", "source": {{"ref": "x"}}, "range": {{"msb": 7, "lsb": 0}}}}
- 端口必须包含: name, direction, data_type, width, signed
- 信号必须包含: name, type, width, signed
- 实例必须包含: name, module, parameter_mapping, port_connections
- always_block 必须包含: id, type, sensitivity, body
- 只返回 JSON，不要添加额外文字说明
"""


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def _regenerate(json_path):
    base = json_path.parent
    proj_root = Path(__file__).resolve().parent.parent
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{json_path.stem}_{ts}"

    gen_v = base / "generated" / f"{stem}.v"
    print(f"  [阶段] 反向生成 Verilog...")
    subprocess.run(
        [sys.executable, str(proj_root / "scripts/generate_from_json.py"),
         str(json_path), "-o", str(gen_v)], check=True)

    dot_file = base / "diagrams" / f"{stem}.dot"
    print(f"  [阶段] 生成 Block Design 图表...")
    subprocess.run(
        [sys.executable, str(proj_root / "scripts/visualize_block.py"),
         str(json_path), "--format", "dot", "-o", str(dot_file)], check=True)

    print(f"[OK] 完成！Verilog: {gen_v}  图表: {dot_file}")

    latest_v = base / "generated" / f"{json_path.stem}_latest.v"
    latest_dot = base / "diagrams" / f"{json_path.stem}_latest.dot"
    try:
        if latest_v.exists() or latest_v.is_symlink():
            latest_v.unlink()
        latest_v.symlink_to(gen_v.name)
        if latest_dot.exists() or latest_dot.is_symlink():
            latest_dot.unlink()
        latest_dot.symlink_to(dot_file.name)
        print(f"  [OK] latest 链接: {latest_v.name} -> {gen_v.name}")
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(description="LLM 交互式编辑设计 JSON")
    parser.add_argument("input", nargs="?", help="输入的规范 JSON 文件")
    parser.add_argument("-p", "--prompt", help="修改描述（自然语言）")
    parser.add_argument("--config", action="store_true", help="配置 LLM API URL / Key")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互式会话模式")
    parser.add_argument("--regenerate", action="store_true", help="修改后自动重新生成")
    parser.add_argument("-o", "--output", help="输出 JSON 路径（默认覆盖输入文件）")
    args = parser.parse_args()

    if args.config:
        setup_config()
        return

    if not args.input:
        parser.print_help()
        print("\n请提供输入文件")
        sys.exit(1)

    config = load_config()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] 文件不存在: {args.input}")
        sys.exit(1)

    design = json.loads(input_path.read_text())
    output_path = Path(args.output) if args.output else input_path
    system_prompt = build_system_prompt()

    # -----------------------------------------------------------------------
    # 交互模式
    # -----------------------------------------------------------------------
    if args.interactive:
        print("=== LLM 交互式编辑会话 ===")
        print("输入修改描述，或 'quit' 退出，'save' 保存，'diff' 查看当前 JSON，'help' 帮助")
        print("---")

        while True:
            try:
                prompt = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not prompt:
                continue
            if prompt.lower() in ("quit", "exit", "q"):
                break
            if prompt.lower() == "save":
                output_path.write_text(json.dumps(design, indent=2))
                print(f"[OK] 已保存到 {output_path}")
                continue
            if prompt.lower() == "diff":
                print(json.dumps(design, indent=2)[:2000])
                continue
            if prompt.lower() == "help":
                print("可用命令: quit / save / diff / help")
                continue

            design_summary = _summarize(design)
            user_msg = f"## 修改需求\n{prompt}\n\n## 当前设计摘要\n{design_summary}"

            print("  [LLM] 处理中...")
            response = call_llm(system_prompt, user_msg, config)

            try:
                instructions = extract_json(response)
                changes = instructions.get("changes", [])
                if not changes:
                    print("  [WARN] LLM 返回了空的变更列表")
                    continue
                old = json.dumps(design, indent=2)
                design = apply_changes(design, changes)
                new = json.dumps(design, indent=2)
                print(f"  [OK] 已应用 {len(changes)} 项变更（输入 'save' 保存）")
            except Exception as e:
                print(f"[ERROR] {e}")

        output_path.write_text(json.dumps(design, indent=2))
        print(f"[OK] 已保存到 {output_path}")
        if args.regenerate:
            _regenerate(output_path)
        return

    # -----------------------------------------------------------------------
    # 单次修改模式
    # -----------------------------------------------------------------------
    if not args.prompt:
        parser.print_help()
        print("\n请提供修改描述 (-p)，或使用 --interactive 进入交互模式")
        sys.exit(1)

    design_summary = _summarize(design)
    user_msg = f"## 修改需求\n{args.prompt}\n\n## 当前设计摘要\n{design_summary}"

    print("  [LLM] 发送修改请求...")
    response = call_llm(system_prompt, user_msg, config)

    try:
        instructions = extract_json(response)
        changes = instructions.get("changes", [])
        if not changes:
            print("[ERROR] LLM 返回了空的变更列表")
            sys.exit(1)
        design = apply_changes(design, changes)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    output_path.write_text(json.dumps(design, indent=2))
    print(f"[OK] 已保存修改后的 JSON: {output_path}")
    print(f"     应用了 {len(changes)} 项变更")

    if args.regenerate:
        _regenerate(output_path)


def _summarize(design):
    """生成本地摘要传给 LLM 以减少 token 消耗。"""
    lines = []
    lines.append(f"顶层模块: {design.get('metadata', {}).get('top_module', '?')}")
    for mod in design.get("modules", []):
        lines.append(f"\n### 模块: {mod['name']}")
        lines.append(f"  参数: {len(mod.get('parameters', []))}")
        ports = mod.get("ports", [])
        for p in ports:
            lines.append(f"  端口: {p['direction']} {p['name']} [{p.get('width',1)}] {p.get('data_type','wire')}")
        for s in mod.get("signals", []):
            lines.append(f"  信号: {s['name']} [{s.get('width',1)}]")
        for inst in mod.get("instances", []):
            lines.append(f"  实例: {inst['name']} : {inst['module']}")
        for ab in mod.get("always_blocks", []):
            sens = ", ".join(f"{s['type']} {s['signal']}" for s in ab.get("sensitivity", []))
            lines.append(f"  always: {ab['type']} @({sens})  body: {len(ab.get('body',[]))} stmts")
        for fn in mod.get("functions", []):
            lines.append(f"  函数: {fn['name']} -> {fn.get('return_type','?')}")
        for tk in mod.get("tasks", []):
            lines.append(f"  任务: {tk['name']}")
        for a in mod.get("assignments", []):
            lines.append(f"  assign: ...")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
