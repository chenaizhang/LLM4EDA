#!/usr/bin/env python3
import json
import sys
import os
import re
from jsonschema import validate, ValidationError

SELF_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(SELF_DIR, '..', 'specs', 'schema_v1.json')

STMT_TYPES = frozenset([
    'assignment', 'if', 'case', 'for', 'while', 'repeat', 'forever',
    'return', 'instance', 'call_stmt',
])


def is_expr(obj, _depth=0):
    if _depth > 2000:
        return False
    if not isinstance(obj, dict):
        return False
    if 'ref' in obj:
        return isinstance(obj['ref'], str)
    if 'literal' in obj:
        return isinstance(obj['literal'], str)
    if 'op' in obj:
        if 'operand' in obj:
            return is_expr(obj['operand'], _depth + 1)
        if 'left' in obj and 'right' in obj:
            return is_expr(obj['left'], _depth + 1) and is_expr(obj['right'], _depth + 1)
        return False
    t = obj.get('type')
    if t == 'select':
        return ('source' in obj and 'range' in obj and
                isinstance(obj.get('range'), dict) and
                isinstance(obj['range'].get('msb'), int) and
                isinstance(obj['range'].get('lsb'), int) and
                is_expr(obj['source'], _depth + 1))
    if t == 'bit_select':
        return ('source' in obj and 'index' in obj and
                is_expr(obj['source'], _depth + 1) and is_expr(obj['index'], _depth + 1))
    if t == 'cond':
        return (all(k in obj for k in ('condition', 'true_expr', 'false_expr'))
                and all(is_expr(obj[k], _depth + 1) for k in ('condition', 'true_expr', 'false_expr')))
    if t == 'concat':
        return ('parts' in obj and isinstance(obj['parts'], list)
                and all(is_expr(p, _depth + 1) for p in obj['parts']))
    if t == 'replicate':
        return ('times' in obj and 'value' in obj
                and is_expr(obj['times'], _depth + 1) and is_expr(obj['value'], _depth + 1))
    if t == 'call':
        return ('function' in obj and 'arguments' in obj
                and isinstance(obj['function'], str)
                and isinstance(obj['arguments'], list)
                and all(is_expr(a, _depth + 1) for a in obj['arguments']))
    if t == 'part_select':
        return ('base' in obj and 'op' in obj and 'width' in obj
                and is_expr(obj['base'], _depth + 1) and is_expr(obj['width'], _depth + 1))
    return False


def is_stmt(obj, _depth=0):
    if _depth > 2000:
        return False
    if not isinstance(obj, dict):
        return False
    st = obj.get('type')
    if st is None:
        return True
    if st not in STMT_TYPES:
        return False
    if st == 'assignment':
        return (all(k in obj for k in ('lhs', 'rhs', 'blocking'))
                and isinstance(obj['blocking'], bool))
    if st == 'if':
        return 'condition' in obj and 'then' in obj
    if st == 'case':
        return 'expression' in obj and 'items' in obj
    if st == 'for':
        return all(k in obj for k in ('init', 'condition', 'step', 'body'))
    if st in ('while', 'repeat', 'forever'):
        return 'body' in obj
    if st == 'return':
        return 'value' in obj
    if st == 'instance':
        return 'name' in obj and 'module' in obj
    return True


def validate_bodies(obj, _depth=0):
    if _depth > 2000:
        return False
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key == 'body' and isinstance(val, list):
                for item in val:
                    if not is_stmt(item, _depth + 1):
                        return False
            if isinstance(val, (dict, list)):
                if not validate_bodies(val, _depth + 1):
                    return False
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                if not validate_bodies(item, _depth + 1):
                    return False
    return True


def check_unique_names(items, name_key, scope_label):
    seen = set()
    for item in items:
        name = item.get(name_key)
        if name is not None and name in seen:
            return False
        if name is not None:
            seen.add(name)
    return True


def validate_datetime_format(val):
    if not isinstance(val, str):
        return True
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
    return bool(re.match(pattern, val))


def check_unique_ids(items, id_key):
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        iid = item.get(id_key)
        if iid is not None and iid in seen:
            return False
        if iid is not None:
            seen.add(iid)
    return True


def get_module_port_count(modules, mod_name):
    for m in modules:
        if isinstance(m, dict) and m.get('name') == mod_name:
            ports = m.get('ports', [])
            return len(ports) if isinstance(ports, list) else 0
    return None


def has_return_stmt(body):
    if not isinstance(body, list):
        return False
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if stmt.get('type') == 'return':
            return True
        for key in ('then', 'else', 'body'):
            sub = stmt.get(key)
            if isinstance(sub, list) and has_return_stmt(sub):
                return True
            if isinstance(sub, dict):
                for sk, sv in sub.items():
                    if isinstance(sv, list) and has_return_stmt(sv):
                        return True
    return False


def validate_semantic_rules(instance):
    if not isinstance(instance, dict):
        return True

    modules = instance.get('modules', [])
    if not isinstance(modules, list):
        return True

    version = instance.get('version')
    if isinstance(version, str):
        if not re.match(r'^\d+\.\d+\.\d+', version):
            return False

    module_names = []
    for mod in modules:
        if not isinstance(mod, dict):
            continue
        mname = mod.get('name')
        if mname is not None:
            module_names.append(mname)

    if not check_unique_names(modules, 'name', 'module'):
        return False

    module_name_set = set(module_names)

    for mod in modules:
        if not isinstance(mod, dict):
            continue

        ports = mod.get('ports', [])
        if isinstance(ports, list):
            if not check_unique_names(ports, 'name', 'port'):
                return False

        signals = mod.get('signals', [])
        if isinstance(signals, list):
            if not check_unique_names(signals, 'name', 'signal'):
                return False

        ports_by_name = {}
        if isinstance(ports, list):
            for p in ports:
                if isinstance(p, dict):
                    pname = p.get('name')
                    if pname:
                        ports_by_name[pname] = p

        driven_signals = set()
        for assign in mod.get('assignments', []):
            if isinstance(assign, dict):
                lhs = assign.get('lhs', {})
                if isinstance(lhs, dict) and 'ref' in lhs:
                    ref_name = lhs['ref']
                    if isinstance(ref_name, str):
                        driven_signals.add(ref_name)

        for blk in mod.get('always_blocks', []):
            if isinstance(blk, dict):
                for stmt in blk.get('body', []):
                    if isinstance(stmt, dict) and stmt.get('type') == 'assignment':
                        lhs = stmt.get('lhs', {})
                        if isinstance(lhs, dict) and 'ref' in lhs:
                            ref_name = lhs['ref']
                            if isinstance(ref_name, str):
                                driven_signals.add(ref_name)

        for s in driven_signals:
            if s in ports_by_name:
                pdir = ports_by_name[s].get('direction')
                if pdir == 'input':
                    return False

        instances = mod.get('instances', [])
        if isinstance(instances, list):
            if not check_unique_names(instances, 'name', 'instance'):
                return False
            for inst in instances:
                if isinstance(inst, dict):
                    ref_mod = inst.get('module')
                    if isinstance(ref_mod, str) and ref_mod not in module_name_set:
                        return False

                    connections = inst.get('port_connections', [])
                    if isinstance(connections, list):
                        target_port_count = get_module_port_count(modules, ref_mod)
                        if target_port_count is not None and len(connections) != target_port_count:
                            return False

        always_blocks = mod.get('always_blocks', [])
        if isinstance(always_blocks, list):
            if not check_unique_ids(always_blocks, 'id'):
                return False
            for blk in always_blocks:
                if isinstance(blk, dict):
                    if blk.get('type') == 'always_comb':
                        sens = blk.get('sensitivity', [])
                        if isinstance(sens, list) and len(sens) > 0:
                            return False

        functions = mod.get('functions', [])
        if isinstance(functions, list):
            for func in functions:
                if isinstance(func, dict):
                    body = func.get('body', [])
                    if not has_return_stmt(body):
                        func_name = func.get('name', '')
                        def _has_fn_assign(stmts):
                            for s in stmts:
                                if not isinstance(s, dict):
                                    continue
                                if (s.get('type') == 'assignment' and
                                    isinstance(s.get('lhs'), dict) and
                                    s['lhs'].get('ref') == func_name):
                                    return True
                                for key in ('then', 'else', 'body'):
                                    sub = s.get(key)
                                    if isinstance(sub, list) and _has_fn_assign(sub):
                                        return True
                            return False
                        if not _has_fn_assign(body):
                            return False

    metadata = instance.get('metadata', {})
    if isinstance(metadata, dict):
        gen_at = metadata.get('generated_at')
        if gen_at is not None:
            if not validate_datetime_format(gen_at):
                return False

    return True


def main():
    try:
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
    except Exception as e:
        print("false", file=sys.stderr)
        sys.exit(1)

    try:
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            with open(sys.argv[1]) as f:
                instance = json.load(f)
        elif len(sys.argv) > 1:
            instance = json.loads(sys.argv[1])
        else:
            instance = json.load(sys.stdin)
    except Exception:
        print("false")
        sys.exit(1)

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    try:
        try:
            validate(instance, schema)
        except Exception:
            print("false")
            sys.exit(1)

        try:
            if not validate_bodies(instance):
                print("false")
                sys.exit(1)
        except Exception:
            print("false")
            sys.exit(1)

        try:
            if not validate_semantic_rules(instance):
                print("false")
                sys.exit(1)
        except Exception:
            print("false")
            sys.exit(1)

        print("true")
    finally:
        sys.setrecursionlimit(old_limit)


if __name__ == '__main__':
    main()
