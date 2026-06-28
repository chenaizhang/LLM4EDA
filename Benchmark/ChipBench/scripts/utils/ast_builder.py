"""AST 构建辅助：将解析结果转换为规范 JSON 的适配层。"""


def build_ref(name):
    return {"ref": name}


def build_literal(value):
    return {"literal": value}


def build_binary(left, op, right):
    return {"op": op, "left": left, "right": right}


def build_unary(op, operand):
    return {"op": op, "operand": operand}


def build_select(source, msb, lsb):
    return {"type": "select", "source": source, "range": {"msb": msb, "lsb": lsb}}


def build_bit_select(source, index_expr):
    return {"type": "bit_select", "source": source, "index": index_expr}


def build_concat(parts):
    return {"type": "concat", "parts": parts}


def build_replicate(times_expr, value_expr):
    return {"type": "replicate", "times": times_expr, "value": value_expr}


def build_cond(cond_expr, true_expr, false_expr):
    return {
        "type": "cond",
        "condition": cond_expr,
        "true_expr": true_expr,
        "false_expr": false_expr,
    }


def build_call(func_name, args):
    return {"type": "call", "function": func_name, "arguments": args}


def build_assignment(lhs, rhs, blocking=True, delay=None):
    stmt = {"type": "assignment", "lhs": lhs, "rhs": rhs, "blocking": blocking}
    if delay:
        stmt["delay"] = delay
    return stmt


def build_if(cond, then_stmts, else_stmts=None):
    stmt = {"type": "if", "condition": cond, "then": then_stmts}
    if else_stmts:
        stmt["else"] = else_stmts
    return stmt


def build_case(expr, items, default_stmts=None, case_type=""):
    stmt = {"type": "case", "expression": expr, "items": items}
    if case_type:
        stmt["case_type"] = case_type
    if default_stmts:
        stmt["default"] = default_stmts
    return stmt


def build_case_item(value, body):
    return {"value": value, "body": body}


def build_for(init, cond, step, body):
    return {"type": "for", "init": init, "condition": cond, "step": step, "body": body}


def build_return(value):
    return {"type": "return", "value": value}


def build_always_block(id_str, always_type, sensitivity, body, description=""):
    block = {
        "id": id_str,
        "type": always_type,
        "sensitivity": sensitivity,
        "body": body,
    }
    if description:
        block["description"] = description
    return block


def build_sensitivity_item(stype, signal):
    return {"type": stype, "signal": signal}


def build_instance(name, module, param_mapping=None, port_connections=None):
    inst = {"name": name, "module": module}
    if param_mapping:
        inst["parameter_mapping"] = param_mapping
    else:
        inst["parameter_mapping"] = {}
    if port_connections:
        inst["port_connections"] = port_connections
    else:
        inst["port_connections"] = []
    return inst


def build_port_connection(port_name, connection_expr):
    return {"port": port_name, "connection": connection_expr}


def build_port(name, direction, data_type="wire", width=1, signed=False):
    return {
        "name": name,
        "direction": direction,
        "data_type": data_type,
        "width": width,
        "signed": signed,
    }


def build_signal(name, sig_type="wire", width=1, signed=False, initial_value=None):
    sig = {"name": name, "type": sig_type, "width": width, "signed": signed}
    if initial_value:
        sig["initial_value"] = initial_value
    return sig


def build_parameter(name, param_type="parameter", data_type="int", value=""):
    return {
        "name": name,
        "type": param_type,
        "data_type": data_type,
        "value": value,
    }


def build_define(name, value):
    return {"name": name, "value": value}


def build_function(name, return_type, inputs, body):
    return {"name": name, "return_type": return_type, "inputs": inputs, "body": body}


def build_task(name, inputs, outputs, body):
    return {
        "name": name,
        "inputs": inputs,
        "outputs": outputs,
        "body": body,
    }


def build_generate(condition, body):
    return {"condition": condition, "body": body}


def build_module(name, params, ports, signals, always_blocks, assignments, instances, functions=None, tasks=None, generates=None, description="", initial_blocks=None):
    mod = {
        "name": name,
        "description": description,
        "parameters": params,
        "ports": ports,
        "signals": signals,
        "always_blocks": always_blocks,
        "assignments": assignments,
        "instances": instances,
    }
    if functions:
        mod["functions"] = functions
    if tasks:
        mod["tasks"] = tasks
    if generates:
        mod["generates"] = generates
    if initial_blocks:
        mod["initial_blocks"] = initial_blocks
    return mod
