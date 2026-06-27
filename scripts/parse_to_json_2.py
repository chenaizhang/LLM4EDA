#!/usr/bin/env python3
"""
Verilog → 规范 JSON 前向转换脚本。
用法: python parse_to_json.py --top <顶层模块> [--incdir <目录>] <源文件>... -o <输出.json>
"""

import argparse
import json
import os
import sys
import re


from utils.ast_builder import (
    build_ref, build_literal, build_binary, build_unary,
    build_select, build_bit_select, build_concat, build_replicate,
    build_cond, build_call, build_assignment, build_if, build_case,
    build_case_item, build_for, build_return, build_always_block,
    build_sensitivity_item, build_instance, build_port_connection,
    build_port, build_signal, build_parameter, build_define,
    build_function, build_task, build_generate, build_module,
)


def _find_block_end(text, start):
    """查找匹配 begin/end 的 end 位置，支持嵌套。"""
    depth = 1
    i = start
    while i < len(text):
        if re.match(r'\bbegin\b', text[i:]):
            depth += 1
            i += 5
        elif re.match(r'end(?!\w)', text[i:]):
            depth -= 1
            if depth <= 0:
                return i
            i += 3
        else:
            i += 1
    return len(text)


def _find_endmodule(text, start):
    return text.find("endmodule", start)


def _find_kwd_end(text, kwd, start):
    """Find keyword 'kwd' after start, respecting nesting."""
    return text.find(kwd, start)


class SimpleVerilogParser:
    def __init__(self, src_files, inc_dirs=None, top_module=None):
        self.src_files = src_files
        self.inc_dirs = inc_dirs or []
        self.top_module = top_module
        self.defines = {}
        self.includes = []
        self.modules = []
        self.source_text = ""
        self._load_sources()

    def _load_sources(self):
        for f in self.src_files:
            with open(f) as fh:
                self.source_text += fh.read() + "\n"

    def _strip_comments(self, text):
        text = re.sub(r'//.*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        return text

    def _find_defines(self, text):
        for m in re.finditer(r'`define\s+(\w+)\s+(.+)', text):
            self.defines[m.group(1)] = m.group(2).strip().split('//')[0].strip()

    def _find_includes(self, text):
        for m in re.finditer(r'`include\s+"([^"]+)"', text):
            self.includes.append(m.group(1))

    def _remove_strings(self, text):
        """Remove quoted strings to avoid false matches inside strings."""
        return re.sub(r'"[^"]*"', '', text)

    def _parse_ports(self, port_text):
        """Parse only from module header port list, NOT from body."""
        ports = []
        # Split by port direction keywords to get individual declarations
        decls = re.split(r'(?=\b(?:input|output|inout)\b)', port_text)
        for decl in decls:
            decl = decl.strip()
            if not decl:
                continue
            # Match: direction [type] [signed] [range] names (first name)
            m = re.match(
                r'(input|output|inout)\s+'
                r'(wire|reg|logic)?\s*'
                r'(signed)?\s*'
                r'(?:\[([^\]]+)\])?\s*'
                r'(\w+)',
                decl, re.DOTALL
            )
            if not m:
                continue
            direction = m.group(1)
            data_type = m.group(2) or "wire"
            signed = bool(m.group(3))
            range_text = m.group(4)
            width = 1
            width_expr = None
            if range_text:
                r_parts = range_text.split(':')
                if len(r_parts) == 2:
                    try:
                        msb = int(r_parts[0].strip())
                        lsb = int(r_parts[1].strip())
                        width = msb - lsb + 1
                    except ValueError:
                        width_expr = range_text.strip()
            # Get all names by scanning remaining text for comma-separated identifiers
            names = [m.group(5)]
            rest = decl[m.end():]
            # Find additional names separated by commas (not followed by direction keywords)
            for nm in re.finditer(r',\s*(\w+)\s*', rest):
                nm_name = nm.group(1)
                if nm_name not in ('input', 'output', 'inout'):
                    names.append(nm_name)
            # Only add if we got valid names
            for name in names:
                if name in ('input', 'output', 'inout', 'wire', 'reg', 'logic'):
                    continue
                p = build_port(name, direction, data_type, width, signed)
                if width_expr:
                    p["width_expr"] = width_expr
                ports.append(p)
        return ports

    def _parse_sensitivity(self, sens_text):
        sens_list = []
        st = sens_text.strip()
        if st == "@*":
            sens_list.append(build_sensitivity_item("wildcard", "*"))
            return sens_list
        for m in re.finditer(r'(posedge|negedge)\s+(\w+)', sens_text):
            sens_list.append(build_sensitivity_item(m.group(1), m.group(2)))
        # Split by 'or' or ',' to get all level-sensitive signals
        # Handle both "a or b" and "a, b" and "a,b" patterns
        separators = re.split(r'(?:\s+(?:or|,)\s*|,\s*)', sens_text)
        for part in separators:
            part = part.strip()
            if not part:
                continue
            if re.match(r'(posedge|negedge)\s', part):
                continue
            if not any(s["signal"] == part for s in sens_list):
                sens_list.append(build_sensitivity_item("level", part))
        return sens_list

    def _parse_expression(self, expr_text):
        expr_text = expr_text.strip()
        if not expr_text:
            return None

        if re.match(r'^\d+\'[bodh]', expr_text, re.IGNORECASE):
            return build_literal(expr_text)
        if re.match(r'^\d+$', expr_text):
            return build_literal(expr_text)
        if re.match(r'^\'[xXzZbB01]', expr_text):
            return build_literal(expr_text)

        if expr_text.startswith("("):
            depth = 0
            for i, ch in enumerate(expr_text):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                if depth == 0:
                    if i == len(expr_text) - 1:
                        return self._parse_expression(expr_text[1:-1])
                    break

        if expr_text.startswith("{") and expr_text.endswith("}"):
            inner = expr_text[1:-1].strip()
            # Replication: N{value} or `MACRO{value}
            m2 = re.match(r'(\d+|\`\w+)\{(.+)\}', inner, re.DOTALL)
            if m2:
                times_text = m2.group(1)
                times_expr = build_literal(times_text) if times_text[0].isdigit() else build_ref(times_text)
                return build_replicate(
                    times_expr,
                    self._parse_expression(m2.group(2))
                )
            parts = [self._parse_expression(p.strip()) for p in self._split_comma(inner)]
            return build_concat(parts)

        # SystemVerilog type cast: Type'(expr)
        tc_match = re.match(r'(\w+)\'\(\s*(.+)\s*\)', expr_text, re.DOTALL)
        if tc_match:
            inner = self._parse_expression(tc_match.group(2))
            return {"type": "type_cast", "type_name": tc_match.group(1), "expr": inner}

        if "?" in expr_text and ":" in expr_text:
            parts = re.split(r'\s*\?\s*', expr_text, maxsplit=1)
            if len(parts) == 2:
                tf = re.split(r'\s*:\s*', parts[1], maxsplit=1)
                if len(tf) == 2:
                    return build_cond(
                        self._parse_expression(parts[0]),
                        self._parse_expression(tf[0]),
                        self._parse_expression(tf[1]),
                    )

        # Variable part-select with +: or -: (check before binary ops)
        ps_match = re.match(r'(\w+)\[(\w+(?:\s*[+\-*/]\s*\w+)*)\s*(\+:|-\:)\s*(\w+)\]$', expr_text)
        if ps_match:
            return build_bit_select(
                build_ref(ps_match.group(1)),
                {"type": "part_select", "base": self._parse_expression(ps_match.group(2)),
                 "op": ps_match.group(3), "width": self._parse_expression(ps_match.group(4))}
            )

        for op_pat in [r'\|\|', r'&&', r'==', r'!=', r'===', r'!==',
                       r'<', r'>', r'>=', r'<=',
                       r'<<', r'>>', r'<<<', r'>>>',
                       r'[+\-*/%&|^]', r'^~', r'~^', r'\*\*']:
            # Find operator NOT inside parentheses/brackets/braces
            match_obj = None
            is_multi_op = op_pat in (r'[+\-*/%&|^]',)
            for m in re.finditer(r'\s*(' + op_pat + r')\s*', expr_text):
                before = expr_text[:m.start()]
                dp = before.count('(') - before.count(')')
                db = before.count('[') - before.count(']')
                dc = before.count('{') - before.count('}')
                if dp == 0 and db == 0 and dc == 0:
                    match_obj = m
                    if not is_multi_op:
                        break  # Use FIRST match for single operators (precedence order)
            if match_obj:
                left = expr_text[:match_obj.start()].strip()
                right = expr_text[match_obj.end():].strip()
                if left:
                    return build_binary(
                        self._parse_expression(left),
                        match_obj.group(1),
                        self._parse_expression(right),
                    )

        m = re.match(r'(!|~)\s*(.+)', expr_text)
        if m:
            return build_unary(m.group(1), self._parse_expression(m.group(2)))
        m = re.match(r'-\s*(.+)', expr_text)
        if m and not re.match(r'^\d', m.group(1)):
            return build_unary('-', self._parse_expression(m.group(1)))

        m = re.match(r'(\$?\w+)\s*\((.+)\)', expr_text, re.DOTALL)
        if m:
            args = [self._parse_expression(a.strip()) for a in self._split_comma(m.group(2))]
            return build_call(m.group(1), args)

        m = re.match(r'(\w+)\[(\d+):(\d+)\]', expr_text)
        if m:
            return build_select(build_ref(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = re.match(r'(\w+)\[(\d+)\]', expr_text)
        if m:
            return build_bit_select(build_ref(m.group(1)), build_literal(m.group(2)))
        m = re.match(r'(\w+)\[(\w+)\]', expr_text)
        if m:
            idx_str = m.group(2)
            if not re.match(r'^\d+$', idx_str):
                return build_bit_select(build_ref(m.group(1)), build_ref(idx_str))
        if re.match(r'^\w+$', expr_text):
            return build_ref(expr_text)
        if expr_text.startswith('`'):
            return build_ref(expr_text)

        return build_ref(expr_text)

    def _split_comma(self, text):
        depth = 0
        parts, cur = [], ""
        for ch in text:
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
                continue
            cur += ch
        parts.append(cur)
        return [p.strip() for p in parts if p.strip()]

    def _extract_assignments(self, text):
        assigns = []
        clean = re.sub(r'generate.*?endgenerate', '', text, flags=re.DOTALL)
        for m in re.finditer(
            r'assign\s+(?:#\s*(\d+))?\s*(\w+(?:\[[^\]]*\])?)\s*=\s*([^;]+);',
            clean
        ):
            delay_val = m.group(1)
            lhs = self._parse_expression(m.group(2))
            rhs = self._parse_expression(m.group(3).strip())
            delay = {"value": delay_val, "type": "unit"} if delay_val else None
            assigns.append({
                "id": f"assign_{m.start()}",
                "lhs": lhs, "rhs": rhs, "delay": delay,
            })
        return assigns

    def _extract_signals(self, text):
        """Extract wire/reg/logic/integer/localparam etc declarations."""
        signals = []
        clean = re.sub(r'function.*?endfunction', '', text, flags=re.DOTALL)
        clean = re.sub(r'task.*?endtask', '', clean, flags=re.DOTALL)

        # Match wire/reg/logic with optional signed and range, comma-separated names
        for m in re.finditer(
            r'(wire|reg|logic)\s+'
            r'(signed)?\s*'
            r'(?:\[(.+?)\])?\s*'
            r'(\w+(?:\s*,\s*\w+)*)\s*'
            r'(?:=\s*([^;]+))?\s*;',
            clean
        ):
            sig_type = m.group(1)
            signed = bool(m.group(2))
            range_text = m.group(3)
            width = 1
            if range_text:
                r_parts = range_text.split(':')
                if len(r_parts) == 2:
                    try:
                        msb = int(r_parts[0].strip())
                        lsb = int(r_parts[1].strip())
                        width = msb - lsb + 1
                    except ValueError:
                        width = 1
            init_val = m.group(5)
            if init_val:
                init_val = init_val.strip()
            names = [n.strip() for n in m.group(4).split(',')]
            for name in names:
                sig = build_signal(name, sig_type, width, signed, init_val)
                if range_text:
                    try:
                        int(range_text.split(':')[0].strip())
                    except ValueError:
                        sig["width_expr"] = range_text.strip()
                signals.append(sig)

        # Match integer declarations
        for m in re.finditer(
            r'\binteger\s+(\w+(?:\s*,\s*\w+)*)\s*;', clean
        ):
            for name in m.group(1).split(','):
                signals.append(build_signal(name.strip(), "integer", 1, False))

        # Match real declarations
        for m in re.finditer(
            r'\breal\s+(\w+)\s*;', clean
        ):
            signals.append(build_signal(m.group(1), "real", 1, False))

        # Match time declarations
        for m in re.finditer(
            r'\btime\s+(\w+)\s*;', clean
        ):
            signals.append(build_signal(m.group(1), "time", 1, False))

        # Match genvar declarations
        for m in re.finditer(
            r'\bgenvar\s+(\w+)\s*;', clean
        ):
            signals.append(build_signal(m.group(1), "genvar", 1, False))

        # Match localparam (store as signal with type "localparam")
        for m in re.finditer(
            r'\blocalparam\s+'
            r'(?:(\w+)\s+)?'
            r'(\w+)\s*=\s*([^;]+)\s*;',
            clean
        ):
            data_type = m.group(1) or ""
            name = m.group(2)
            value = m.group(3).strip()
            sig = build_signal(name, "localparam", 1, False, value)
            sig["data_type"] = data_type
            signals.append(sig)

        # Match body parameter declarations: parameter A=0, B=1, ...
        param_clean = re.sub(r'function.*?endfunction', '', text, flags=re.DOTALL)
        param_clean = re.sub(r'task.*?endtask', '', param_clean, flags=re.DOTALL)
        for m in re.finditer(
            r'\bparameter\s+'
            r'(?:(\w+)\s+)?'
            r'(\w+)\s*=\s*([^,;]+)\s*'
            r'(?:,\s*(?:(\w+)\s+)?(\w+)\s*=\s*([^,;]+)\s*)*'
            r'\s*;',
            param_clean, re.DOTALL
        ):
            # Extract all param=value pairs
            param_text = m.group(0)
            for pm in re.finditer(r'(\w+)\s*=\s*([^,;]+)', param_text):
                pname = pm.group(1)
                pval = pm.group(2).strip()
                if pname not in ('parameter', 'input', 'output', 'wire', 'reg', 'logic', 'integer'):
                    sig = build_signal(pname, "parameter", 1, False, pval)
                    signals.append(sig)

        return signals

    def _extract_always(self, text):
        blocks = []
        idx = 0
        pos = 0
        while pos < len(text):
            m = re.search(r'(always_ff|always_comb|always_latch|always)\s*'
                          r'(@\s*(?:\(\s*\*\s*\)|\*\s*|\([^)]*\)))?\s*',
                          text[pos:], re.DOTALL)
            if not m:
                break
            always_type = m.group(1)
            raw_sens = (m.group(2) or "").strip()
            if raw_sens.startswith("@*") or raw_sens.startswith("@(*)"):
                sens_text = "@*"
            elif raw_sens.startswith("@(") and raw_sens.endswith(")"):
                sens_text = raw_sens[2:-1].strip()
            else:
                sens_text = raw_sens.lstrip("@").strip()

            after = pos + m.end()
            after_text = text[after:]
            # Determine if always body has its own begin/end or a single statement
            bm = re.match(r'\s*\bbegin\b', after_text)
            if bm:
                body_start = after + bm.end()
                body_end = _find_block_end(text, body_start)
                if body_end > body_start:
                    inner = text[body_start:body_end].strip()
                    sensitivity = self._parse_sensitivity(sens_text) if sens_text else []
                    stmts = self._extract_statements(inner)
                    blocks.append(build_always_block(f"proc_{idx}", always_type, sensitivity, stmts))
                    idx += 1
                    pos = body_end + 3
                else:
                    pos = after + 1
            else:
                # Single statement body: for/if/while/repeat/forever
                sensitivity = self._parse_sensitivity(sens_text) if sens_text else []
                sbody = text[after:]
                # Find body extent by looking for begin...end or semicolon
                bm_body = re.search(r'\bbegin\b', sbody)
                body_end_pos = after
                if bm_body:
                    be = _find_block_end(text, after + bm_body.end())
                    if be > after:
                        body_end_pos = be + 3
                else:
                    # Single line statement: find next ;
                    sm_body = re.search(r'[^;]+;', sbody)
                    if sm_body:
                        body_end_pos = after + sm_body.end()
                    else:
                        body_end_pos = after + len(sbody)
                body_text = text[after:body_end_pos].strip()
                stmts = self._extract_statements(body_text)
                blocks.append(build_always_block(f"proc_{idx}", always_type, sensitivity, stmts))
                idx += 1
                pos = body_end_pos
        return blocks

    def _extract_statements(self, text):
        """Extract if-else, case, and flat assignment statements from always block body."""
        stmts = []
        i = 0
        while i < len(text):
            chunk = text[i:].lstrip()
            i += len(text[i:]) - len(chunk)
            if not chunk:
                break

            if_match = re.match(r'if\s*\(', chunk)
            if if_match:
                cond_end = self._match_paren(chunk, if_match.end() - 1)
                if cond_end < 0:
                    i += 1
                    continue
                cond = self._parse_expression(chunk[if_match.end():cond_end])

                # find then body
                after = cond_end + 1
                else_pos = chunk.find('else', after)
                search_end = else_pos if else_pos > 0 else len(chunk)
                # Only use 'begin' if it's not preceded by a nested if (which would own it)
                bm = None
                if after < search_end:
                    temp_bm = re.search(r'\bbegin\b', chunk[after:search_end])
                    if temp_bm:
                        between_cond = chunk[after:after + temp_bm.start()]
                        if not re.search(r'\bif\s*\(', between_cond):
                            bm = temp_bm
                then_end = len(chunk)
                then_stmts = []
                has_begin_end = False
                if bm:
                    ts = after + bm.end()
                    then_end = _find_block_end(chunk, ts)
                    has_begin_end = True
                    if then_end > ts:
                        then_stmts = self._extract_statements(chunk[ts:then_end])
                else:
                    # Check for case statement as then body
                    cm = re.match(r'\s*case[xz]?\s*\(', chunk[after:])
                    if cm:
                        case_end = self._match_paren(chunk, after + cm.end() - 1)
                        if case_end > 0:
                            ec = chunk.find('endcase', case_end)
                            if ec > 0:
                                then_stmts = self._extract_statements(chunk[after:ec + 7])
                                then_end = ec + 7
                    else:
                        sm = re.search(r'[^;]+;', chunk[after:])
                        if sm:
                            then_stmts = self._extract_flat_assignments(chunk[after:after + sm.end()])
                            then_end = after + sm.end()

                # find else body
                else_stmts = []
                after_then = (then_end + 3) if (has_begin_end and then_end < len(chunk)) else then_end
                rest = chunk[after_then:].lstrip()
                if rest.startswith("else"):
                    rest = rest[4:].lstrip()
                    elif_match = re.match(r'if\s*\(', rest)
                    if elif_match:
                        elif_end = self._match_paren(rest, elif_match.end() - 1)
                        if elif_end > 0:
                            elif_cond = self._parse_expression(rest[elif_match.end():elif_end])
                            elif_body = rest[elif_end + 1:].lstrip()
                            bm3 = re.search(r'\bbegin\b', elif_body)
                            elif_then = []
                            elif_rest = elif_body
                            if bm3:
                                ets = bm3.end()
                                ete = _find_block_end(elif_body, ets)
                                if ete > ets:
                                    elif_then = self._extract_statements(elif_body[ets:ete])
                                elif_rest = elif_body[ete + 3:].lstrip()
                            else:
                                # Check for nested if statement in elif body
                                elif_if_match = re.match(r'if\s*\(', elif_body)
                                if elif_if_match:
                                    elif_then = self._extract_statements(elif_body)
                                    elif_rest = ""
                                else:
                                    cm3 = re.match(r'case[xz]?\s*\(', elif_body)
                                    if cm3:
                                        cp3 = self._match_paren(elif_body, cm3.end() - 1)
                                        if cp3 > 0:
                                            ec3 = elif_body.find('endcase', cp3)
                                            if ec3 > 0:
                                                elif_then = self._extract_statements(elif_body[:ec3 + 7])
                                                elif_rest = elif_body[ec3 + 7:].lstrip()
                                    else:
                                        sm3 = re.search(r'[^;]+;', elif_body)
                                        if sm3:
                                            elif_then = self._extract_flat_assignments(sm3.group(0))
                                            elif_rest = elif_body[sm3.end():].lstrip()
                            elif_else = []
                            if elif_rest.startswith("else"):
                                elif_rest2 = elif_rest[4:].lstrip()
                                bm4 = re.search(r'\bbegin\b', elif_rest2)
                                if bm4:
                                    ees = bm4.end()
                                    eee = _find_block_end(elif_rest2, ees)
                                    if eee > ees:
                                        elif_else = self._extract_statements(elif_rest2[ees:eee])
                                else:
                                    cm4 = re.match(r'case[xz]?\s*\(', elif_rest2)
                                    if cm4:
                                        cp4 = self._match_paren(elif_rest2, cm4.end() - 1)
                                        if cp4 > 0:
                                            ec4 = elif_rest2.find('endcase', cp4)
                                            if ec4 > 0:
                                                elif_else = self._extract_statements(elif_rest2[:ec4 + 7])
                                    else:
                                        sm4 = re.search(r'[^;]+;', elif_rest2)
                                        if sm4:
                                            elif_else = self._extract_flat_assignments(sm4.group(0))
                            else_stmts = [build_if(elif_cond, elif_then, elif_else)]
                            i = len(chunk)
                    else:
                        bm2 = re.search(r'\bbegin\b', rest)
                        if bm2:
                            es = bm2.end()
                            ee = _find_block_end(rest, es)
                            if ee > es:
                                else_stmts = self._extract_statements(rest[es:ee])
                            i += len(chunk) - len(rest[(ee + 3):]) if ee < len(rest) else len(chunk)
                        else:
                            # Check for if statement in else body (no begin/end)
                            if re.match(r'if\s*\(', rest):
                                else_stmts = self._extract_statements(rest)
                                i = len(chunk)
                            elif re.match(r'case[xz]?\s*\(', rest):
                                cp2 = self._match_paren(rest, re.match(r'case[xz]?\s*\(', rest).end() - 1)
                                if cp2 > 0:
                                    ec2 = rest.find('endcase', cp2)
                                    if ec2 > 0:
                                        else_stmts = self._extract_statements(rest[:ec2 + 7])
                                        i += len(chunk) - len(rest[ec2 + 7:])
                            else:
                                sm = re.search(r'[^;]+;', rest)
                                if sm:
                                    else_stmts = self._extract_flat_assignments(sm.group(0))
                                    i += len(chunk) - len(rest[sm.end():])
                                else:
                                    i += len(chunk) - len(rest)
                else:
                    i += len(chunk) - len(rest)

                stmts.append(build_if(cond, then_stmts, else_stmts))
                continue

            case_match = re.match(r'(casex|casez|case)\s*\(', chunk)
            if case_match:
                case_kw = case_match.group(1)
                ct = ""
                if case_kw == "casex":
                    ct = "x"
                elif case_kw == "casez":
                    ct = "z"
                expr_end = self._match_paren(chunk, case_match.end() - 1)
                if expr_end < 0:
                    i += 1
                    continue
                case_expr = self._parse_expression(chunk[case_match.end():expr_end])
                case_text = chunk[expr_end + 1:]

                # Find endcase to delimit the case body (no begin/end wrapping case)
                ec = case_text.find("endcase")
                if ec < 0:
                    i += 1
                    continue
                inner = case_text[:ec]

                items = []
                default_stmts = []
                ci = 0
                while ci < len(inner):
                    rest = inner[ci:]
                    # Try with begin/end first
                    vm = re.match(r'([^:]+?)\s*:\s*begin\s*', rest, re.DOTALL)
                    if vm:
                        val_text = vm.group(1).strip()
                        ibs_off = vm.end()
                        ibe = _find_block_end(rest, ibs_off)
                        body_text = rest[ibs_off:ibe].strip()
                        if val_text == "default":
                            default_stmts = self._extract_statements(body_text)
                        else:
                            items.append(build_case_item(
                                self._parse_expression(val_text),
                                self._extract_statements(body_text)
                            ))
                        ci += ibe + 3
                        continue
                    # val: if-else chain without begin/end (check before vm2)
                    val_end2 = rest.find(':')
                    if val_end2 >= 0:
                        after_val = rest[val_end2+1:].lstrip()
                        if re.match(r'if\s*\(', after_val):
                            val_text2 = rest[:val_end2].strip()
                            chain_stmts = self._extract_statements(after_val)
                            next_case = re.search(r'\n\s*\w+\s*:', after_val)
                            endcase_pos = after_val.find('endcase')
                            end_pos2 = len(after_val)
                            if next_case: end_pos2 = min(end_pos2, next_case.start())
                            if endcase_pos >= 0: end_pos2 = min(end_pos2, endcase_pos)
                            body2 = [chain_stmts[0]] if chain_stmts else []
                            if val_text2 == "default":
                                default_stmts = body2
                            else:
                                items.append(build_case_item(self._parse_expression(val_text2), body2))
                            # Correct ci advancement: account for lstrip offset
                            before_lstrip = rest[val_end2+1:]
                            lstrip_offset = len(before_lstrip) - len(after_val)
                            ci += val_end2 + 1 + lstrip_offset + end_pos2
                            continue
                    # Without begin/end: val: stmt;
                    vm2 = re.match(r'([^:]+?)\s*:\s*([^;]+);', rest, re.DOTALL)
                    if vm2:
                        val_text = vm2.group(1).strip()
                        body_text = vm2.group(2).strip()
                        if val_text == "default":
                            default_stmts = self._extract_flat_assignments(body_text + ";")
                        else:
                            items.append(build_case_item(
                                self._parse_expression(val_text),
                                self._extract_flat_assignments(body_text + ";")
                            ))
                        ci += vm2.end()
                        continue
                    # val: if-else chain without begin/end (alternate)
                    val_end2 = rest.find(':')
                    if val_end2 >= 0:
                        after_val = rest[val_end2+1:].lstrip()
                        if re.match(r'if\s*\(', after_val):
                            val_text = rest[:val_end2].strip()
                            # Parse if-else chain using _extract_statements on body after ':'
                            chain_stmts = self._extract_statements(after_val)
                            # Find next case value or endcase to determine extent
                            next_case = re.search(r'\n\s*\w+\s*:', after_val)
                            endcase_pos = after_val.find('endcase')
                            end_pos = len(after_val)
                            if next_case:
                                end_pos = min(end_pos, next_case.start())
                            if endcase_pos >= 0:
                                end_pos = min(end_pos, endcase_pos)
                            chain_text = after_val[:end_pos].strip()
                            if chain_stmts:
                                body = [chain_stmts[0]]
                            else:
                                body = self._extract_flat_assignments(chain_text + ";")
                            if val_text == "default":
                                default_stmts = body
                            else:
                                items.append(build_case_item(self._parse_expression(val_text), body))
                            ci += val_end2 + 1 + end_pos
                            continue
                    ci += 1

                if items or default_stmts:
                    stmts.append(build_case(case_expr, items, default_stmts, ct))
                i += len(chunk) - len(case_text[ec + 7:])
                continue

            # for loop
            for_match = re.match(r'for\s*\(', chunk)
            if for_match:
                for_paren_start = for_match.end() - 1
                for_paren_end = self._match_paren(chunk, for_paren_start)
                if for_paren_end < 0:
                    i += 1
                    continue
                for_header = chunk[for_paren_start + 1:for_paren_end]
                semi_parts = for_header.split(';')
                if len(semi_parts) >= 3:
                    # Handle int/bit/logic type prefix in init (SystemVerilog)
                    init_text = semi_parts[0].strip()
                    init_text = re.sub(r'^(int|integer|bit|logic|reg|wire)\s+', '', init_text)
                    init = self._extract_flat_assignments(init_text + ";")
                    cond = self._parse_expression(semi_parts[1].strip()) if semi_parts[1].strip() else None
                    # Handle i++ / i-- style step
                    step_text = semi_parts[2].strip()
                    step_match = re.match(r'(\w+)\s*(\+\+|\-\-)\s*', step_text)
                    if step_match:
                        var = step_match.group(1)
                        op = step_match.group(2)
                        step_rhs = f"{var} + 1" if op == "++" else f"{var} - 1"
                        step_text = f"{var} = {step_rhs}"
                    step = self._extract_flat_assignments(step_text + ";")
                    after_for = for_paren_end + 1
                    bm = re.search(r'\bbegin\b', chunk[after_for:])
                    for_body = []
                    if bm:
                        fb_start = after_for + bm.end()
                        fb_end = _find_block_end(chunk, fb_start)
                        if fb_end > fb_start:
                            for_body = self._extract_statements(chunk[fb_start:fb_end])
                        i += len(chunk) - len(chunk[fb_end + 3:]) if fb_end < len(chunk) else len(chunk)
                    else:
                        sm = re.search(r'[^;]+;', chunk[after_for:])
                        if sm:
                            for_body = self._extract_flat_assignments(chunk[after_for:after_for + sm.end()])
                            i += len(chunk) - len(chunk[after_for + sm.end():])
                        else:
                            i += len(chunk)
                    init_stmt = init[0] if init else None
                    step_stmt = step[0] if step else None
                    stmts.append(build_for(init_stmt, cond, step_stmt, for_body))
                    continue
                else:
                    i += 1
                    continue

            # while loop
            while_match = re.match(r'while\s*\(', chunk)
            if while_match:
                wp_start = while_match.end() - 1
                wp_end = self._match_paren(chunk, wp_start)
                if wp_end < 0:
                    i += 1
                    continue
                wcond = self._parse_expression(chunk[wp_start + 1:wp_end])
                after_w = wp_end + 1
                bm = re.search(r'\bbegin\b', chunk[after_w:])
                wbody = []
                if bm:
                    wb_start = after_w + bm.end()
                    wb_end = _find_block_end(chunk, wb_start)
                    if wb_end > wb_start:
                        wbody = self._extract_statements(chunk[wb_start:wb_end])
                    i += len(chunk) - len(chunk[wb_end + 3:]) if wb_end < len(chunk) else len(chunk)
                else:
                    sm = re.search(r'[^;]+;', chunk[after_w:])
                    if sm:
                        wbody = self._extract_flat_assignments(chunk[after_w:after_w + sm.end()])
                        i += len(chunk) - len(chunk[after_w + sm.end():])
                    else:
                        i += len(chunk)
                stmts.append({"type": "while", "condition": wcond, "body": wbody})
                continue

            # repeat loop
            repeat_match = re.match(r'repeat\s*\(', chunk)
            if repeat_match:
                rp_start = repeat_match.end() - 1
                rp_end = self._match_paren(chunk, rp_start)
                if rp_end < 0:
                    i += 1
                    continue
                rcount = self._parse_expression(chunk[rp_start + 1:rp_end])
                after_r = rp_end + 1
                bm = re.search(r'\bbegin\b', chunk[after_r:])
                rbody = []
                if bm:
                    rb_start = after_r + bm.end()
                    rb_end = _find_block_end(chunk, rb_start)
                    if rb_end > rb_start:
                        rbody = self._extract_statements(chunk[rb_start:rb_end])
                    i += len(chunk) - len(chunk[rb_end + 3:]) if rb_end < len(chunk) else len(chunk)
                else:
                    sm = re.search(r'[^;]+;', chunk[after_r:])
                    if sm:
                        rbody = self._extract_flat_assignments(chunk[after_r:after_r + sm.end()])
                        i += len(chunk) - len(chunk[after_r + sm.end():])
                    else:
                        i += len(chunk)
                stmts.append({"type": "repeat", "count": rcount, "body": rbody})
                continue

            # forever loop
            forever_match = re.match(r'forever\s+', chunk)
            if forever_match:
                after_f = forever_match.end()
                bm = re.search(r'\bbegin\b', chunk[after_f:])
                fbody = []
                if bm:
                    fb_start = after_f + bm.end()
                    fb_end = _find_block_end(chunk, fb_start)
                    if fb_end > fb_start:
                        fbody = self._extract_statements(chunk[fb_start:fb_end])
                    i += len(chunk) - len(chunk[fb_end + 3:]) if fb_end < len(chunk) else len(chunk)
                else:
                    sm = re.search(r'[^;]+;', chunk[after_f:])
                    if sm:
                        fbody = self._extract_flat_assignments(chunk[after_f:after_f + sm.end()])
                        i += len(chunk) - len(chunk[after_f + sm.end():])
                    else:
                        i += len(chunk)
                stmts.append({"type": "forever", "body": fbody})
                continue

            # task/function call statement: identifier(...) or identifier;
            call_match = re.match(r'(\w+)\s*\(', chunk)
            if call_match:
                cp_start = call_match.end() - 1
                cp_end = self._match_paren(chunk, cp_start)
                if cp_end > 0:
                    call_end = chunk.find(';', cp_end)
                    if call_end > 0:
                        call_name = call_match.group(1)
                        args_raw = chunk[cp_start:cp_end + 1].strip()
                        stmts.append({"type": "call_stmt", "name": call_name, "args_raw": args_raw})
                        i += call_end + 1
                        continue
            # Bare task enable: name;
            bare_call = re.match(r'(\w+)\s*;', chunk)
            if bare_call:
                call_name = bare_call.group(1)
                # Only treat as call if not a keyword
                if call_name not in ('end', 'begin', 'endcase', 'endfunction', 'endtask', 'endif'):
                    stmts.append({"type": "call_stmt", "name": call_name, "args_raw": ""})
                    i += bare_call.end()
                    continue

            assign_match = re.match(
                r'(\w+(?:\[[^\]]*\])?)\s*(<=|=)\s*([^;]+);',
                chunk
            )
            if assign_match:
                stmts.append(build_assignment(
                    self._parse_expression(assign_match.group(1)),
                    self._parse_expression(assign_match.group(3).strip()),
                    blocking=(assign_match.group(2) == "="),
                ))
                i += assign_match.end()
                continue

            # Concatenation LHS: {a, b, c} = expr;
            alt_assign = re.match(r'(\{[^}]+\})\s*(<=|=)\s*([^;]+);', chunk)
            if alt_assign:
                stmts.append(build_assignment(
                    self._parse_expression(alt_assign.group(1)),
                    self._parse_expression(alt_assign.group(3).strip()),
                    blocking=(alt_assign.group(2) == "="),
                ))
                i += alt_assign.end()
                continue

            i += 1

        return stmts

    def _extract_flat_assignments(self, text):
        stmts = []
        for m in re.finditer(
            r'(\w+(?:\[[^\]]*\])?)\s*(<=|=)\s*([^;]+);',
            text
        ):
            lhs_t = m.group(1)
            op = m.group(2)
            rhs_t = m.group(3).strip()
            stmts.append(build_assignment(
                self._parse_expression(lhs_t),
                self._parse_expression(rhs_t),
                blocking=(op == "="),
            ))
        # Also handle concatenation LHS
        for m in re.finditer(
            r'(\{[^}]+\})\s*(<=|=)\s*([^;]+);',
            text
        ):
            if not any(s['lhs'] == self._parse_expression(m.group(1)) for s in stmts):
                stmts.append(build_assignment(
                    self._parse_expression(m.group(1)),
                    self._parse_expression(m.group(3).strip()),
                    blocking=(m.group(2) == "="),
                ))
        return stmts

    def _extract_instances(self, body):
        instances = []
        # Strip function/task/always bodies to avoid false matches
        clean = re.sub(r'function.*?endfunction', '', body, flags=re.DOTALL)
        clean = re.sub(r'task.*?endtask', '', clean, flags=re.DOTALL)
        clean = re.sub(r'always(?:_ff|_comb|_latch)?\s*.*?\bend\b', '', clean, flags=re.DOTALL)
        clean = re.sub(r'\bassign\s+.*?;', '', clean)
        clean = re.sub(r'\b(wire|reg|logic)\b\s+.*?;', '', clean)
        clean = re.sub(r'\bendgenerate\b', '', clean)
        clean = re.sub(r'\bgenerate\b', '', clean)

        # Verilog keywords that should never appear as module names
        _KWD_BLOCK = {'begin', 'end', 'if', 'else', 'case', 'endcase', 'for',
                      'while', 'repeat', 'forever', 'function', 'endfunction',
                      'task', 'endtask', 'generate', 'endgenerate', 'always',
                      'always_comb', 'always_ff', 'always_latch',
                      'initial', 'assign', 'default', 'input', 'output', 'inout',
                      'wire', 'reg', 'logic', 'integer', 'real', 'time', 'genvar'}

        idx = 0
        while idx < len(clean):
            # Match: module_name [param_parens] inst_name parens;
            m = re.search(
                r'(\w+)\s+'
                r'(?:#\s*\(((?:[^()]|\([^()]*\))*)\)\s*)?'
                r'(\w+)\s*\(',
                clean[idx:], re.DOTALL
            )
            if not m:
                break
            mod_name = m.group(1)
            if mod_name in _KWD_BLOCK:
                idx += m.end()
                continue
            param_text = m.group(2)
            inst_name = m.group(3)

            param_map = {}
            if param_text:
                for pm in re.finditer(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', param_text):
                    param_map[pm.group(1)] = self._parse_expression(pm.group(2).strip())

            paren_open = idx + m.end(0) - 1
            paren_end = self._match_paren(clean, paren_open)
            if paren_end < 0:
                idx = paren_open + 1
                continue
            conn_text = clean[paren_open+1:paren_end]

            conns = []
            if conn_text.strip():
                for c in re.finditer(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', conn_text):
                    conn_val = c.group(2).strip()
                    conns.append(build_port_connection(
                        c.group(1), self._parse_expression(conn_val)
                    ))
            instances.append(build_instance(inst_name, mod_name, param_map, conns))
            idx = paren_end + 1

        return instances

    def _match_paren(self, text, start):
        depth = 1
        i = start + 1
        while i < len(text) and depth > 0:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            i += 1
        return i - 1 if depth == 0 else -1

    def parse(self):
        text = self._strip_comments(self.source_text)
        self._find_defines(text)
        self._find_includes(text)

        mod_re = re.compile(
            r'module\s+(\w+)\s*'
            r'(?:#\s*\((.*?)\))?\s*'
            r'\((.*?)\)\s*;',
            re.DOTALL
        )

        mod_cursor = 0
        while True:
            m = mod_re.search(text, mod_cursor)
            if not m:
                break
            mod_name = m.group(1)
            param_text = m.group(2) or ""
            port_text = m.group(3) or ""

            after_header = m.end()
            em = _find_endmodule(text, after_header)
            if em < 0:
                break
            body = text[after_header:em]

            params = self._parse_params(param_text)
            ports = self._parse_ports(port_text)
            signals = self._extract_signals(body)
            always_blocks = self._extract_always(body)
            assignments = self._extract_assignments(body)
            instances = self._extract_instances(body)
            functions = self._parse_functions(body)
            tasks = self._parse_tasks(body)
            generates = self._parse_generates(body)

            self.modules.append(build_module(
                mod_name, params, ports, signals,
                always_blocks, assignments, instances,
                functions, tasks, generates,
            ))
            mod_cursor = em + 9

        return self._build_output()

    def _parse_params(self, param_text):
        params = []
        if not param_text.strip():
            return params
        for p in re.finditer(r'parameter\s+(\w+)\s+(\w+)\s*=\s*([^,)]+)', param_text):
            params.append(build_parameter(
                p.group(2), "parameter", p.group(1), p.group(3).strip()
            ))
        for p in re.finditer(r'parameter\s+(\w+)\s*=\s*([^,)]+)', param_text):
            if not any(pp["name"] == p.group(1) for pp in params):
                params.append(build_parameter(
                    p.group(1), "parameter", "", p.group(2).strip()
                ))
        return params

    def _parse_functions(self, body):
        funcs = []
        idx = 0
        while idx < len(body):
            m = re.search(r'\bfunction\s+', body[idx:])
            if not m:
                break
            after = idx + m.end()

            # Find either '(' or ';' to determine function header end
            paren_pos = body.find('(', after)
            semi_pos = body.find(';', after)
            if semi_pos < 0:
                break

            has_paren_inputs = paren_pos >= 0 and paren_pos < semi_pos

            if has_paren_inputs:
                args_end = self._match_paren(body, paren_pos)
                if args_end < 0:
                    idx = semi_pos + 1
                    continue
                header_end = args_end + 1
                # function name is the word just before '('
                pre_paren = body[after:paren_pos].strip()
                pre_parts = pre_paren.split()
                func_name = pre_parts[-1] if pre_parts else ""
                ret_type = " ".join(pre_parts[:-1]) if len(pre_parts) > 1 else ""
                # inputs are inside the parens
                args_text = body[paren_pos + 1:args_end]
                inputs = []
                for arg in re.finditer(r'\binput\s+(\S+(?:\s*\[[^\]]+\])?)\s+(\w+)', args_text):
                    inputs.append({"name": arg.group(2), "type": arg.group(1)})
            else:
                header_end = semi_pos
                header = body[after:header_end].strip()
                parts = header.split()
                if len(parts) < 2:
                    idx = semi_pos + 1
                    continue
                func_name = parts[-1]
                ret_type = " ".join(parts[:-1])
                inputs = []

            # Find endfunction
            func_end_kw = body.find("endfunction", header_end)
            if func_end_kw < 0:
                break
            func_body_text = body[header_end + 1:func_end_kw]
            funcs.append(build_function(func_name, ret_type, inputs,
                                        self._extract_statements(func_body_text)))
            idx = func_end_kw + 11
        return funcs

    def _parse_tasks(self, body):
        tasks_list = []
        idx = 0
        while idx < len(body):
            m = re.search(r'\btask\s+(\w+)', body[idx:])
            if not m:
                break
            task_name = m.group(1)
            after = idx + m.end()
            semi = body.find(";", after)
            if semi < 0:
                break

            inputs, outputs = [], []
            arg_match = re.search(r'\(\s*', body[after:semi])
            if arg_match:
                args_end = self._match_paren(body, after + arg_match.start())
                if args_end > 0:
                    args_text = body[after + arg_match.start() + 1:args_end]
                    for arg in re.finditer(r'\b(input|output)\s+(\S+(?:\s*\[[^\]]+\])?)\s+(\w+)', args_text):
                        entry = {"name": arg.group(3), "type": arg.group(2)}
                        if arg.group(1) == "input":
                            inputs.append(entry)
                        else:
                            outputs.append(entry)

            task_end_kw = body.find("endtask", semi)
            if task_end_kw < 0:
                break
            tasks_list.append(build_task(task_name, inputs, outputs,
                                        self._extract_flat_assignments(body[semi + 1:task_end_kw])))
            idx = task_end_kw + 7
        return tasks_list

    def _parse_generates(self, body):
        gens = []
        # Find generate blocks and extract their content
        gen_cursor = 0
        while True:
            gm = re.search(r'\bgenerate\b', body[gen_cursor:])
            if not gm:
                break
            gen_start = gen_cursor + gm.start()
            gen_end_kw = body.find("endgenerate", gen_start)
            if gen_end_kw < 0:
                break
            gen_inner = body[gen_start + 9:gen_end_kw].strip()

            # Parse generate if/else if/else
            if_match = re.match(r'if\s*\(', gen_inner)
            if if_match:
                self._parse_gen_if_else(gen_inner, gens)
            else:
                # Parse generate for
                for_match = re.match(r'for\s*\(', gen_inner)
                if for_match:
                    fp_start = for_match.end() - 1
                    fp_end = self._match_paren(gen_inner, fp_start)
                    if fp_end > 0:
                        for_header = gen_inner[fp_start + 1:fp_end]
                        parts = for_header.split(';')
                        init_text = parts[0].strip() if len(parts) > 0 else ""
                        cond_text = parts[1].strip() if len(parts) > 1 else ""
                        step_text = parts[2].strip() if len(parts) > 2 else ""
                        after_for = gen_inner[fp_end + 1:].strip()
                        bm = re.search(r'\bbegin\b', after_for)
                        if bm:
                            fb_start = bm.end()
                            fb_end = _find_block_end(after_for, fb_start)
                            gen_body_text = after_for[fb_start:fb_end].strip()
                            gen_body = self._extract_instances(gen_body_text)
                            gen_assigns = self._extract_assignments("module dummy;\n" + gen_body_text + "\nendmodule")
                            # Store as a special generate item
                            gens.append({
                                "type": "gen_for",
                                "init": self._extract_flat_assignments(init_text + ";"),
                                "condition": self._parse_expression(cond_text) if cond_text else None,
                                "step": self._extract_flat_assignments(step_text + ";"),
                                "body": gen_body + gen_assigns
                            })

            gen_cursor = gen_end_kw + 11
        return gens

    def _parse_gen_if_else(self, text, gens, indent=""):
        """Recursively parse generate if/else if/else chains."""
        m = re.match(r'if\s*\((.*?)\)\s*', text, re.DOTALL)
        if not m:
            return
        cond_text = m.group(1).strip()
        cond = self._parse_expression(cond_text)
        after_cond = text[m.end():].strip()

        bm = re.search(r'\bbegin\b', after_cond)
        if_body = []
        rest = ""
        if bm:
            bb = bm.end()
            be = _find_block_end(after_cond, bb)
            if be > bb:
                body_text = after_cond[bb:be].strip()
                if_body = self._extract_instances(body_text)
                if not if_body:
                    if_body = self._extract_assignments(body_text)
                # Also check for nested generate if inside body
                nested_gen = re.search(r'\bgenerate\b', body_text)
                if not nested_gen:
                    # Check for nested if that isn't in a generate block
                    nested_if = re.match(r'if\s*\(', body_text)
                    if nested_if:
                        self._parse_gen_if_else(body_text, gens, indent + "  ")
                        if_body = []
            rest = after_cond[be + 3:].strip()
        else:
            # No begin/end
            sm = re.search(r'[^;]+;', after_cond)
            if sm:
                if_body = self._extract_flat_assignments(sm.group(0))
                rest = after_cond[sm.end():].strip()

        # Check for else
        else_body = []
        if rest.startswith("else"):
            rest_else = rest[4:].strip()
            if re.match(r'if\s*\(', rest_else):
                # else if - recurse
                self._parse_gen_if_else(rest_else, gens, indent)
            else:
                bm2 = re.search(r'\bbegin\b', rest_else)
                if bm2:
                    eb = bm2.end()
                    ee = _find_block_end(rest_else, eb)
                    if ee > eb:
                        else_body_text = rest_else[eb:ee].strip()
                        else_body = self._extract_instances(else_body_text)
                        if not else_body:
                            else_body = self._extract_assignments(else_body_text)
                else:
                    sm = re.search(r'[^;]+;', rest_else)
                    if sm:
                        else_body = self._extract_flat_assignments(sm.group(0))

        gen_entry = build_generate(cond, if_body)
        if else_body:
            gen_entry["else_body"] = else_body
        gens.append(gen_entry)

    def _build_output(self):
        defines_list = [build_define(k, v) for k, v in self.defines.items()]
        hierarchy = {}
        for mod in self.modules:
            children = [inst["name"] for inst in mod.get("instances", [])]
            hierarchy[mod["name"]] = children

        return {
            "version": "1.0.0",
            "metadata": {
                "design_name": self.top_module or "unknown",
                "source_files": self.src_files,
                "top_module": self.top_module or "",
                "description": f"Parsed from {len(self.src_files)} file(s)",
                "generated_by": "parse_to_json.py v1.0",
                "generated_at": __import__("datetime").datetime.now().isoformat(),
            },
            "includes": self.includes,
            "defines": defines_list,
            "modules": self.modules,
            "design_hierarchy": {
                "top": self.top_module or (self.modules[0]["name"] if self.modules else ""),
                "tree": hierarchy,
            },
        }


def main():
    parser = argparse.ArgumentParser(description="Verilog → 规范 JSON 转换")
    parser.add_argument("--top", help="顶层模块名")
    parser.add_argument("--incdir", action="append", default=[], help="include 目录")
    parser.add_argument("-o", "--output", default="design.json", help="输出 JSON 路径")
    parser.add_argument("src", nargs="+", help="Verilog 源文件")
    args = parser.parse_args()

    vp = SimpleVerilogParser(args.src, args.incdir, args.top)
    result = vp.parse()

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[OK] 已生成规范 JSON: {args.output}")
    print(f"     模块数: {len(result['modules'])}")


if __name__ == "__main__":
    main()
