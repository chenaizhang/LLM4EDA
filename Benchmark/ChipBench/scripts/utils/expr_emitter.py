"""AST 表达式生成器：将表达式 AST 递归转换为 Verilog 字符串。"""

OPS = {
    "+": " + ", "-": " - ", "*": " * ", "/": " / ", "%": " % ",
    "&": " & ", "|": " | ", "^": " ^ ", "^~": " ^~ ", "~^": " ~^ ",
    "&&": " && ", "||": " || ",
    "==": " == ", "!=": " != ", "===": " === ", "!==": " !== ",
    "<": " < ", "<=": " <= ", ">": " > ", ">=": " >= ",
    "<<": " << ", ">>": " >> ", "<<<": " <<< ", ">>>": " >>> ",
    "**": " ** ",
}

# Verilog operator precedence (higher number = higher precedence / binds tighter)
# From IEEE Std 1364-2005 Section 5.1.5 (highest to lowest):
#   1: **
#   2: * / %
#   3: + - (binary)
#   4: << >> <<< >>>
#   5: < <= > >=
#   6: == != === !==
#   7: & ^ ^~ ~^ | (bitwise)
#   8: &&
#   9: ||
BIN_PREC = {
    "**": 9,
    "*": 8, "/": 8, "%": 8,
    "+": 7, "-": 7,
    "<<": 6, ">>": 6, "<<<": 6, ">>>": 6,
    "<": 5, "<=": 5, ">": 5, ">=": 5,
    "==": 4, "!=": 4, "===": 4, "!==": 4,
    "&": 3, "^": 3, "^~": 3, "~^": 3, "|": 3,
    "&&": 2,
    "||": 1,
}

UNA_OPS = {"!", "~", "-", "&", "~&", "|", "~|", "^", "~^"}


def emit_expr(expr, indent=0):
    if expr is None:
        return ""
    if isinstance(expr, str):
        return expr
    if not isinstance(expr, dict):
        return str(expr)

    if "ref" in expr:
        return expr["ref"]
    if "literal" in expr:
        return expr["literal"]
    if "type" in expr:
        t = expr["type"]
        if t == "select":
            src = emit_expr(expr["source"], indent)
            rng = expr.get("range", {})
            return f"{src}[{rng['msb']}:{rng['lsb']}]"
        if t == "bit_select":
            src = emit_expr(expr["source"], indent)
            idx_expr = expr["index"]
            if isinstance(idx_expr, dict) and idx_expr.get("type") == "part_select":
                base = emit_expr(idx_expr["base"], indent)
                op = idx_expr["op"]
                width = emit_expr(idx_expr["width"], indent)
                return f"{src}[{base} {op}{width}]"
            idx = emit_expr(idx_expr, indent)
            return f"{src}[{idx}]"
        if t == "part_select":
            base = emit_expr(expr["base"], indent)
            op = expr["op"]
            width = emit_expr(expr["width"], indent)
            return f"[{base} {op}{width}]"
        if t == "concat":
            parts = [emit_expr(p, indent) for p in expr.get("parts", [])]
            return "{" + ", ".join(parts) + "}"
        if t == "replicate":
            times = emit_expr(expr["times"], indent)
            val = emit_expr(expr["value"], indent)
            return "{" + times + "{" + val + "}}"
        if t == "cond":
            cond = emit_expr(expr["condition"], indent)
            te = emit_expr(expr["true_expr"], indent)
            fe = emit_expr(expr["false_expr"], indent)
            return f"({cond} ? {te} : {fe})"
        if t == "call":
            fname = expr.get("function", "")
            if fname == "$part_select":
                args = expr.get("arguments", [])
                if len(args) >= 3:
                    src = emit_expr(args[0], indent)
                    base = emit_expr(args[1], indent)
                    width = emit_expr(args[2], indent)
                    return f"{src}[{base}+:{width}]"
            args = ", ".join(emit_expr(a, indent) for a in expr.get("arguments", []))
            return f"{fname}({args})"
        if t == "type_cast":
            inner_expr = expr.get("expr")
            inner = emit_expr(inner_expr, indent)
            # Remove extra outer parens added by child expression
            if inner.startswith('(') and inner.endswith(')'):
                inner = inner[1:-1]
            return f"{expr['type_name']}'({inner})"
        if t in ("assignment",):
            return emit_stmt(expr, indent)

    if "type" in expr and expr["type"] == "parameter_ref":
        return expr.get("value", "")

    if "op" in expr:
        op = expr["op"]
        if op in UNA_OPS and "operand" in expr:
            operand_expr = expr["operand"]
            operand = emit_expr(operand_expr, indent)
            # Wrap operand in parens if it's a binary op (unary has higher prec)
            if isinstance(operand_expr, dict) and operand_expr.get("op") and operand_expr.get("op") in OPS:
                operand = f"({operand})"
            return f"{op}{operand}"
        if op in OPS and "left" in expr and "right" in expr:
            left_expr = expr["left"]
            right_expr = expr["right"]
            left = emit_expr(left_expr, indent)
            right = emit_expr(right_expr, indent)
            left_op = left_expr.get("op") if isinstance(left_expr, dict) else None
            right_op = right_expr.get("op") if isinstance(right_expr, dict) else None
            parent_prec = BIN_PREC.get(op, 5)
            if left_op and left_op in BIN_PREC and BIN_PREC.get(left_op, 0) <= parent_prec:
                left = f"({left})"
            if right_op and right_op in BIN_PREC and BIN_PREC.get(right_op, 0) <= parent_prec:
                right = f"({right})"
            return f"{left}{OPS[op]}{right}"
        return f"<unknown_op:{op}>"

    if "value" in expr:
        return str(expr["value"])

    return "<unknown_expr>"


def emit_stmt(stmt, indent=0):
    pad = "  " * indent
    if stmt.get("type") == "assignment":
        lhs = emit_expr(stmt["lhs"])
        rhs = emit_expr(stmt["rhs"])
        arrow = "=" if stmt.get("blocking", True) else "<="
        delay = ""
        if "delay" in stmt:
            delay = f" #{stmt['delay']['value']}"
        space = " " if delay else ""
        return f"{pad}{lhs}{space}{delay} {arrow} {rhs};"

    if stmt.get("type") == "if":
        cond = emit_expr(stmt["condition"])
        then_s = stmt.get("then", [])
        else_s = stmt.get("else", [])
        # Use begin/end if then body is a single if (to prevent dangling else)
        needs_begin_end = len(else_s) > 0 and len(then_s) == 1 and then_s[0].get("type") == "if"
        if needs_begin_end:
            result = f"{pad}if ({cond}) begin\n"
            for s in then_s:
                result += emit_stmt(s, indent + 1) + "\n"
            result += f"{pad}end else begin\n"
            for s in else_s:
                result += emit_stmt(s, indent + 1) + "\n"
            result += f"{pad}end"
            return result
        elif len(then_s) == 1 and not else_s:
            return f"{pad}if ({cond})\n{emit_stmt(then_s[0], indent + 1)}"
        elif len(then_s) == 1 and len(else_s) == 1:
            return f"{pad}if ({cond})\n{emit_stmt(then_s[0], indent + 1)}\n{pad}else\n{emit_stmt(else_s[0], indent + 1)}"
        result = f"{pad}if ({cond}) begin\n"
        for s in then_s:
            result += emit_stmt(s, indent + 1) + "\n"
        if else_s:
            result += f"{pad}end else begin\n"
            for s in else_s:
                result += emit_stmt(s, indent + 1) + "\n"
        result += f"{pad}end"
        return result

    if stmt.get("type") == "case":
        exp = emit_expr(stmt["expression"])
        ct = stmt.get("case_type", "")
        kw = "casex" if ct == "x" else ("casez" if ct == "z" else "case")
        result = f"{pad}{kw} ({exp})\n"
        for item in stmt.get("items", []):
            val = emit_expr(item.get("value", ""))
            item_body = item.get("body", [])
            if len(item_body) == 1:
                line = emit_stmt(item_body[0], 0)
                result += f"{pad}  {val}: {line}\n"
            else:
                result += f"{pad}  {val}: begin\n"
                for s in item_body:
                    result += emit_stmt(s, indent + 2) + "\n"
                result += f"{pad}  end\n"
        if stmt.get("default"):
            def_body = stmt["default"]
            if len(def_body) == 1:
                line = emit_stmt(def_body[0], 0)
                result += f"{pad}  default: {line}\n"
            else:
                result += f"{pad}  default: begin\n"
                for s in def_body:
                    result += emit_stmt(s, indent + 2) + "\n"
                result += f"{pad}  end\n"
        result += f"{pad}endcase"
        return result

    if stmt.get("type") == "for":
        init_val = stmt["init"]
        init = emit_stmt(init_val, 0) if init_val else ""
        init = init.rstrip(";") if init else ""
        cond = emit_expr(stmt["condition"]) if stmt.get("condition") else ""
        step_val = stmt["step"]
        step = emit_stmt(step_val, 0) if step_val else ""
        step = step.rstrip(";") if step else ""
        body = stmt.get("body", [])
        result = f"{pad}for ({init}; {cond}; {step}) begin\n"
        for s in body:
            result += emit_stmt(s, indent + 1) + "\n"
        result += f"{pad}end"
        return result

    if stmt.get("type") == "while":
        cond = emit_expr(stmt["condition"])
        body = stmt.get("body", [])
        result = f"{pad}while ({cond}) begin\n"
        for s in body:
            result += emit_stmt(s, indent + 1) + "\n"
        result += f"{pad}end"
        return result

    if stmt.get("type") == "repeat":
        count = emit_expr(stmt["count"])
        body = stmt.get("body", [])
        result = f"{pad}repeat ({count}) begin\n"
        for s in body:
            result += emit_stmt(s, indent + 1) + "\n"
        result += f"{pad}end"
        return result

    if stmt.get("type") == "forever":
        body = stmt.get("body", [])
        result = f"{pad}forever begin\n"
        for s in body:
            result += emit_stmt(s, indent + 1) + "\n"
        result += f"{pad}end"
        return result

    if stmt.get("type") == "call_stmt":
        args_raw = stmt.get("args_raw", "")
        return f"{pad}{stmt['name']}{args_raw};"

    if stmt.get("type") == "return":
        val = emit_expr(stmt.get("value"))
        return f"{pad}return {val};"

    if stmt.get("type") == "instance":
        result = f"{pad}{stmt['module']} {stmt['name']} ("
        conns = stmt.get("port_connections", [])
        if conns:
            conn_strs = []
            for c in conns:
                conn_strs.append(f".{c['port']}({emit_expr(c['connection'])})")
            result += "\n" + ",\n".join("  " + pad + cs for cs in conn_strs) + "\n" + pad
        result += ");"
        return result

    return f"{pad}<unknown_stmt>;"
