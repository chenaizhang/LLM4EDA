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
        for m in re.finditer(r'`define\s+(\w+(?:\([^)]*\))?)\s*(.+)', text):
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
                r'(\w+)'
                r'(?:\s*\[([^\]]+)\])?',
                decl, re.DOTALL
            )
            if not m:
                continue
            direction = m.group(1)
            data_type = m.group(2) or "wire"
            signed = bool(m.group(3))
            range_text = m.group(4)
            pname = m.group(5)
            unpacked_range = m.group(6)
            width = 1
            width_expr = None
            if range_text:
                r_parts = range_text.split(':')
                if len(r_parts) == 2:
                    try:
                        msb = int(r_parts[0].strip())
                        lsb = int(r_parts[1].strip())
                        width = msb - lsb + 1
                        if msb != width - 1 or lsb != 0:
                            width_expr = range_text.strip()
                    except ValueError:
                        width_expr = range_text.strip()
                else:
                    width_expr = range_text.strip()
            names = [pname]
            rest = decl[m.end():]
            for nm in re.finditer(r',\s*(\w+)\s*', rest):
                nm_name = nm.group(1)
                if nm_name not in ('input', 'output', 'inout'):
                    names.append(nm_name)
            for name in names:
                if name in ('input', 'output', 'inout', 'wire', 'reg', 'logic'):
                    continue
                p = build_port(name, direction, data_type, width, signed)
                if width_expr:
                    p["width_expr"] = width_expr
                if unpacked_range:
                    p["unpacked_range"] = unpacked_range.strip()
                ports.append(p)
        return ports

    def _parse_sensitivity(self, sens_text):
        sens_list = []
        st = sens_text.strip()
        if st == "@*":
            sens_list.append(build_sensitivity_item("level", "*"))
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

    def _find_top_level(self, text, chars):
        """Find the first top-level occurrence of any char in chars (not inside parens/brackets/braces)."""
        depth_p = 0
        depth_b = 0
        depth_c = 0
        for i, ch in enumerate(text):
            if ch == '(':
                depth_p += 1
            elif ch == ')':
                depth_p -= 1
            elif ch == '[':
                depth_b += 1
            elif ch == ']':
                depth_b -= 1
            elif ch == '{':
                depth_c += 1
            elif ch == '}':
                depth_c -= 1
            if depth_p == 0 and depth_b == 0 and depth_c == 0 and ch in chars:
                return i
        return -1

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

        # Top-level replication: N{value}, `MACRO{value}, or param{value}
        m_rep = re.match(r'(\d+|\`\w+|\w+)\{(.+)\}$', expr_text, re.DOTALL)
        if m_rep and not expr_text.startswith("{") and not expr_text.startswith("'"):
            times_expr = build_literal(m_rep.group(1)) if m_rep.group(1)[0].isdigit() else build_ref(m_rep.group(1))
            return build_replicate(times_expr, self._parse_expression(m_rep.group(2)))

        if expr_text.startswith("{"):
            # Find matching closing brace
            depth = 1
            end_brace = -1
            for i in range(1, len(expr_text)):
                if expr_text[i] == '{':
                    depth += 1
                elif expr_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_brace = i
                        break
            if end_brace == len(expr_text) - 1:
                inner = expr_text[1:-1].strip()
                # Replication: N{value}, `MACRO{value}, or param{value}
                m2 = re.match(r'(\d+|\`\w+|\w+)\{(.+)\}', inner, re.DOTALL)
                if m2:
                    times_text = m2.group(1)
                    times_expr = build_literal(times_text) if times_text[0].isdigit() else build_ref(times_text)
                    return build_replicate(
                        times_expr,
                        self._parse_expression(m2.group(2))
                    )
                parts = [self._parse_expression(p.strip()) for p in self._split_comma(inner)]
                if len(parts) == 1:
                    return parts[0]
                return build_concat(parts)

        # SystemVerilog type cast: Type'(expr)
        tc_match = re.match(r'(\w+)\'\(\s*(.+)\s*\)', expr_text, re.DOTALL)
        if tc_match:
            inner = self._parse_expression(tc_match.group(2))
            return {"type": "type_cast", "type_name": tc_match.group(1), "expr": inner}

        q_pos = self._find_top_level(expr_text, '?')
        if q_pos >= 0:
            col_pos = self._find_top_level(expr_text[q_pos+1:], ':')
            if col_pos >= 0:
                cond = self._parse_expression(expr_text[:q_pos])
                true_e = self._parse_expression(expr_text[q_pos+1:q_pos+1+col_pos])
                false_e = self._parse_expression(expr_text[q_pos+1+col_pos+1:])
                return build_cond(cond, true_e, false_e)

        # Variable part-select with +: or -: (check before binary ops)
        ps_match = re.match(r'(\w+)\[(.+?)\s*(\+:|-\:)\s*(.+?)\]$', expr_text)
        if ps_match:
            return build_call(
                "$part_select",
                [build_ref(ps_match.group(1)),
                 self._parse_expression(ps_match.group(2)),
                 build_literal(ps_match.group(4))]
            )

        # Combined reduction operators (~&, ~|, ~^, ^~) must be checked before binary
        m = re.match(r'(~&|~\||~\^|\^~)\s*(.+)', expr_text, re.DOTALL)
        if m:
            return build_unary(m.group(1), self._parse_expression(m.group(2)))
        # Binary operators: scan text left-to-right, find all top-level ops
        # Then pick the one with lowest precedence (tie-break: rightmost for left-assoc)
        bin_op_prec = {
            '||': 1, '&&': 2,
            '|': 3, '^': 3,
            '&': 4,
            '===': 5, '!==': 5, '==': 5, '!=': 5,
            '>=': 6, '<=': 6, '>': 6, '<': 6,
            '<<<': 7, '>>>': 7, '<<': 7, '>>': 7,
            '+': 8, '-': 8,
            '*': 9, '/': 9, '%': 9,
            '**': 10,
        }
        # Sort ops by length descending so we match '<<<' before '<<' before '<'
        sorted_ops = sorted(bin_op_prec.items(), key=lambda x: -len(x[0]))
        found_ops = []
        i = 0
        while i < len(expr_text):
            trimmed = expr_text[i:].lstrip()
            ws_skip = len(expr_text[i:]) - len(trimmed)
            if ws_skip > 0:
                i += ws_skip
                continue
            matched = False
            for op_str, prec in sorted_ops:
                if trimmed.startswith(op_str):
                    before = expr_text[:i]
                    dp = before.count('(') - before.count(')')
                    db = before.count('[') - before.count(']')
                    dc = before.count('{') - before.count('}')
                    if dp == 0 and db == 0 and dc == 0:
                        if op_str in ('&', '|', '^') and i + len(op_str) < len(expr_text) and expr_text[i + len(op_str)] == '{':
                            pass
                        else:
                            found_ops.append((i, op_str, prec))
                    i += len(op_str)
                    matched = True
                    break
            if not matched:
                i += 1
        if found_ops:
            found_ops.sort(key=lambda x: (x[2], -x[0]))
            best = found_ops[0]
            left = expr_text[:best[0]].strip()
            right = expr_text[best[0] + len(best[1]):].strip()
            if left:
                return build_binary(
                    self._parse_expression(left),
                    best[1],
                    self._parse_expression(right),
                )

        m = re.match(r'(!|~)\s*(.+)', expr_text, re.DOTALL)
        if m:
            return build_unary(m.group(1), self._parse_expression(m.group(2)))
        m = re.match(r'-\s*(.+)', expr_text, re.DOTALL)
        if m and not re.match(r'^\d', m.group(1)):
            return build_unary('-', self._parse_expression(m.group(1)))

        m = re.match(r'(\$?\w+)\s*\((.+)\)', expr_text, re.DOTALL)
        if m:
            args = [self._parse_expression(a.strip()) for a in self._split_comma(m.group(2))]
            return build_call(m.group(1), args)

        m = re.match(r'(\w+)\[(\d+):(\d+)\]', expr_text)
        if m:
            return build_select(build_ref(m.group(1)), int(m.group(2)), int(m.group(3)))

        # Handle chained bit-selects FIRST: arr[idx1][idx2] (2+ indices)
        chain_match = re.match(r'(\w+)((?:\[[^\]]+\]){2,})', expr_text)
        if chain_match:
            base = build_ref(chain_match.group(1))
            indices = re.findall(r'\[([^\]]+)\]', chain_match.group(2))
            for idx_text in indices:
                idx_text = idx_text.strip()
                idx_expr = build_literal(idx_text) if re.match(r'^\d+$', idx_text) else self._parse_expression(idx_text)
                base = build_bit_select(base, idx_expr)
            return base
        m = re.match(r'(\w+)\[(\d+)\]', expr_text)
        if m:
            return build_bit_select(build_ref(m.group(1)), build_literal(m.group(2)))
        m = re.match(r'(\w+)\[(\w+)\]', expr_text)
        if m:
            idx_str = m.group(2)
            if not re.match(r'^\d+$', idx_str):
                return build_bit_select(build_ref(m.group(1)), build_ref(idx_str))
            base = build_ref(chain_match.group(1))
            indices = re.findall(r'\[([^\]]+)\]', chain_match.group(2))
            for idx_text in indices:
                idx_text = idx_text.strip()
                idx_expr = build_literal(idx_text) if re.match(r'^\d+$', idx_text) else self._parse_expression(idx_text)
                base = build_bit_select(base, idx_expr)
            return base

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
            r'assign\s+(?:#\s*(\d+))?\s*(\{[^}]+\}|\w+\s*(?:\[\s*[^\]]*\s*\])?\s*)\s*=\s*([^;]+);',
            clean
        ):
            delay_val = m.group(1)
            lhs = self._parse_expression(m.group(2))
            rhs = self._parse_expression(m.group(3).strip())
            entry = {
                "id": f"assign_{m.start()}",
                "lhs": lhs, "rhs": rhs, "blocking": False,
            }
            if delay_val:
                entry["delay"] = {"value": delay_val, "type": "unit"}
            assigns.append(entry)
        return assigns

    def _extract_signals(self, text):
        """Extract wire/reg/logic/integer/localparam etc declarations."""
        signals = []
        clean = re.sub(r'function.*?endfunction', '', text, flags=re.DOTALL)
        clean = re.sub(r'task.*?endtask', '', clean, flags=re.DOTALL)

        # Match wire/reg/logic with optional signed and range, comma-separated names
        # Also handle unpacked arrays: logic [1:0] pht [2**n-1:0]
        for m in re.finditer(
            r'\b(wire|reg|logic)\b\s*'
            r'(signed)?\s*'
            r'(?:\[(.+?)\])?\s*'
            r'(\w+(?:\s*,\s*\w+)*)\s*'
            r'(?:\[([^\]]+)\])?\s*'
            r'(?:=\s*([^;]+))?\s*;',
            clean
        ):
            sig_type = m.group(1)
            signed = bool(m.group(2))
            range_text = m.group(3)
            names_str = m.group(4)
            unpacked_range = m.group(5)
            init_all = m.group(6)
            width = 1
            width_expr = None
            if range_text:
                r_parts = range_text.split(':')
                if len(r_parts) == 2:
                    try:
                        msb = int(r_parts[0].strip())
                        lsb = int(r_parts[1].strip())
                        width = msb - lsb + 1
                        if msb != width - 1 or lsb != 0:
                            width_expr = range_text.strip()
                    except ValueError:
                        width_expr = range_text.strip()
                else:
                    width_expr = range_text.strip()
            names = [n.strip() for n in names_str.split(',')]
            for name in names:
                sig = build_signal(name, sig_type, width, signed, init_all)
                if width_expr:
                    sig["width_expr"] = width_expr
                if unpacked_range:
                    sig["unpacked_range"] = unpacked_range.strip()
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

        # Match body parameter declarations: parameter [3:0] S0=0, S1=1, ...
        param_clean = re.sub(r'function.*?endfunction', '', text, flags=re.DOTALL)
        param_clean = re.sub(r'task.*?endtask', '', param_clean, flags=re.DOTALL)
        for m in re.finditer(
            r'\bparameter\s+'
            r'(?:(\[\d+:\d+\]|\w+)\s+)?'
            r'(\w+)\s*=\s*([^,;]+)\s*'
            r'(?:,\s*(?:\w+)\s*=\s*([^,;]+)\s*)*'
            r'\s*;',
            param_clean, re.DOTALL
        ):
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
                body_end_pos = len(text)
                # Find the end of this single statement: scan for next module-level keyword
                for keyword in ('assign', 'always_ff', 'always_comb', 'always_latch',
                                'always', 'initial', 'endmodule'):
                    kw_m = re.search(r'\b' + keyword + r'\b', sbody)
                    if kw_m:
                        kw_pos = kw_m.start()
                        prefix = sbody[:kw_pos]
                        if (prefix.count('(') == prefix.count(')') and
                            prefix.count('[') == prefix.count(']') and
                            prefix.count('{') == prefix.count('}')):
                            cand = after + kw_pos
                            if cand < body_end_pos:
                                body_end_pos = cand
                body_text = text[after:body_end_pos].strip()
                stmts = self._extract_statements(body_text)
                if stmts:
                    stmts = [stmts[0]]
                pos = body_end_pos
                blocks.append(build_always_block(f"proc_{idx}", always_type, sensitivity, stmts))
                idx += 1
        return blocks

    def _extract_initial(self, text):
        blocks = []
        idx = 0
        pos = 0
        while pos < len(text):
            m = re.search(r'\binitial\s*', text[pos:])
            if not m:
                break
            after = pos + m.end()
            after_text = text[after:]
            bm = re.match(r'\s*\bbegin\b', after_text)
            if bm:
                body_start = after + bm.end()
                body_end = _find_block_end(text, body_start)
                if body_end > body_start:
                    inner = text[body_start:body_end].strip()
                    stmts = self._extract_statements(inner)
                    blocks.append(build_always_block(f"init_{idx}", "initial", [], stmts))
                    idx += 1
                    pos = body_end + 3
                else:
                    pos = after + 1
            else:
                body_text = text[after:].strip()
                stmts = self._extract_statements(body_text)
                if stmts:
                    stmts = [stmts[0]]
                blocks.append(build_always_block(f"init_{idx}", "initial", [], stmts))
                idx += 1
                pos = len(text)
        return blocks

    def _parse_if_chain(self, chunk):
        """Parse a complete if-else-elseif chain starting at chunk.
        Returns (if_stmt, remaining_text) or (None, chunk)."""
        if_match = re.match(r'if\s*\(', chunk)
        if not if_match:
            return None, chunk
        cond_end = self._match_paren(chunk, if_match.end() - 1)
        if cond_end < 0:
            return None, chunk
        cond = self._parse_expression(chunk[if_match.end():cond_end])
        after = cond_end + 1
        then_stmts, after_then = self._parse_if_body(chunk[after:])
        rest = after_then.lstrip()
        else_stmts = []
        if rest.startswith("else"):
            rest2 = rest[4:].lstrip()
            elif_m = re.match(r'if\s*\(', rest2)
            if elif_m:
                elif_stmt, rest3 = self._parse_if_chain(rest2)
                if elif_stmt:
                    else_stmts = [elif_stmt]
                rest = rest3
            else:
                else_body, rest = self._parse_if_body(rest2)
                else_stmts = else_body
        return build_if(cond, then_stmts, else_stmts), rest

    def _parse_loop_body(self, text):
        """Parse a single loop body that may or may not have begin/end."""
        bm = re.match(r'\s*\bbegin\b', text)
        if bm:
            bs = bm.end()
            be = _find_block_end(text, bs)
            if be > bs:
                stmts = self._extract_statements(text[bs:be])
                return stmts, text[be + 3:]
            return [], text
        st = text.lstrip()
        lead = len(text) - len(st)
        if re.match(r'if\s*\(', st):
            stmt, rest = self._parse_if_chain(st)
            if stmt:
                return [stmt], text[:lead] + (rest or "")
        for_match = re.match(r'for\s*\(', st)
        if for_match:
            for_paren_start = for_match.end() - 1
            for_paren_end = self._match_paren(st, for_paren_start)
            if for_paren_end > 0:
                for_header = st[for_paren_start + 1:for_paren_end]
                semi_parts = for_header.split(';')
                init_text = semi_parts[0].strip() if len(semi_parts) > 0 else ""
                cond_text = semi_parts[1].strip() if len(semi_parts) > 1 else ""
                step_text = semi_parts[2].strip() if len(semi_parts) > 2 else ""
                after_for = st[for_paren_end + 1:]
                body_stmts, rest = self._parse_loop_body(after_for)
                init = self._extract_flat_assignments(init_text + ";")
                step = self._extract_flat_assignments(step_text + ";")
                cond = self._parse_expression(cond_text) if cond_text else None
                for_stmt = {
                    "type": "for",
                    "init": init[0] if init else None,
                    "condition": cond,
                    "step": step[0] if step else None,
                    "body": body_stmts
                }
                return [for_stmt], text[:lead] + (rest or "")
        # Single assignment statement
        sm = re.search(r'[^;]+;', st)
        if sm:
            stmts = self._extract_flat_assignments(sm.group(0) + ";")
            return stmts, text[:lead] + st[sm.end():]
        return [], text

    def _parse_if_body(self, text):
        """Extract body statements from text (may be begin/end wrapped or single stmt).
        Returns (stmts, remaining_text)."""
        bm = re.match(r'\s*\bbegin\b', text)
        if bm:
            bs = bm.end()
            be = _find_block_end(text, bs)
            if be > bs:
                stmts = self._extract_statements(text[bs:be])
                return stmts, text[be + 3:]
            return [], text
        # Check for if statement as the single body (no begin/end)
        st = text.lstrip()
        lead = len(text) - len(st)
        if re.match(r'if\s*\(', st):
            stmt, rest = self._parse_if_chain(st)
            if stmt:
                return [stmt], text[:lead] + (rest or "")
        # Check for case statement as the single body
        if re.match(r'case[xz]?\s*\(', st):
            cm = re.match(r'case[xz]?\s*\(', st)
            cp = self._match_paren(st, cm.end() - 1)
            if cp > 0:
                ec = st.find('endcase', cp)
                if ec > 0:
                    stmts = self._extract_statements(st[:ec + 7])
                    return stmts, text[:lead] + st[ec + 7:]
        # Check for for/while/repeat/forever as the single body
        for_match = re.match(r'for\s*\(', st)
        if for_match:
            for_paren_start = for_match.end() - 1
            for_paren_end = self._match_paren(st, for_paren_start)
            if for_paren_end > 0:
                for_header = st[for_paren_start + 1:for_paren_end]
                semi_parts = for_header.split(';')
                init_text = semi_parts[0].strip() if len(semi_parts) > 0 else ""
                cond_text = semi_parts[1].strip() if len(semi_parts) > 1 else ""
                step_text = semi_parts[2].strip() if len(semi_parts) > 2 else ""
                after_for = st[for_paren_end + 1:]
                body_stmts, rest = self._parse_loop_body(after_for)
                init = self._extract_flat_assignments(init_text + ";")
                step = self._extract_flat_assignments(step_text + ";")
                cond = self._parse_expression(cond_text) if cond_text else None
                for_stmt = {
                    "type": "for",
                    "init": init[0] if init else None,
                    "condition": cond,
                    "step": step[0] if step else None,
                    "body": body_stmts
                }
                return [for_stmt], text[:lead] + (rest or "")
        # Single assignment statement
        sm = re.search(r'[^;]+;', st)
        if sm:
            stmts = self._extract_flat_assignments(sm.group(0) + ";")
            return stmts, text[:lead] + st[sm.end():]
        return [], text

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
                if_stmt, rest = self._parse_if_chain(chunk)
                if if_stmt:
                    stmts.append(if_stmt)
                    i = len(text) - len(rest) if rest else len(text)
                    continue
                else:
                    i += 1
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
                    decl_type = ''
                    dtm = re.match(r'^(int|integer|bit|logic|reg|wire)\s+', init_text)
                    if dtm:
                        decl_type = dtm.group(1)
                        init_text = init_text[dtm.end():]
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
                    for_rest = chunk[after_for:]
                    bm = re.match(r'\s*\bbegin\b', for_rest)
                    for_body = []
                    if bm:
                        fb_start = after_for + bm.end()
                        fb_end = _find_block_end(chunk, fb_start)
                        if fb_end > fb_start:
                            for_body = self._extract_statements(chunk[fb_start:fb_end])
                        i += len(chunk) - len(chunk[fb_end + 3:]) if fb_end < len(chunk) else len(chunk)
                    else:
                        sm = re.search(r'[^;]+;', for_rest)
                        if sm:
                            for_body = self._extract_flat_assignments(for_rest[:sm.end()])
                            i += len(chunk) - len(for_rest[sm.end():])
                        else:
                            i += len(chunk)
                    init_stmt = init[0] if init else None
                    step_stmt = step[0] if step else None
                    for_stmt = build_for(init_stmt, cond, step_stmt, for_body)
                    if decl_type:
                        for_stmt["decl_type"] = decl_type
                    stmts.append(for_stmt)
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
                r'(\{[^}]+\}|\w+\s*(?:\[\s*[^\]]*\s*\])?\s*)\s*(<=|(?<!=)=|(?<!\^)\^=|\|=|&=|\+=|\-=)\s*([^;]+);',
                chunk
            )
            if assign_match:
                op = assign_match.group(2)
                blocking = op in ("=", "^=", "|=", "&=", "+=", "-=")
                stmt = build_assignment(
                    self._parse_expression(assign_match.group(1)),
                    self._parse_expression(assign_match.group(3).strip()),
                    blocking=blocking,
                )
                if op != "=" and op != "<=":
                    stmt["compound_op"] = op
                stmts.append(stmt)
                i += assign_match.end()
                continue

            i += 1

        return stmts

    def _extract_flat_assignments(self, text):
        stmts = []
        for m in re.finditer(
            r'(\{[^}]+\}|\w+\s*(?:\[\s*[^\]]*\s*\])?\s*)\s*(<=|(?<!=)=|(?<!\^)\^=|\|=|&=|\+=|\-=)\s*([^;]+);',
            text
        ):
            lhs_t = m.group(1)
            op = m.group(2)
            rhs_t = m.group(3).strip()
            blocking = op in ("=", "^=", "|=", "&=", "+=", "-=")
            stmt = build_assignment(
                self._parse_expression(lhs_t),
                self._parse_expression(rhs_t),
                blocking=blocking,
            )
            if op != "=" and op != "<=":
                stmt["compound_op"] = op
            stmts.append(stmt)
        return stmts

    def _extract_instances(self, body):
        instances = []
        # Strip function/task/always bodies to avoid false matches
        clean = re.sub(r'function.*?endfunction', '', body, flags=re.DOTALL)
        clean = re.sub(r'task.*?endtask', '', clean, flags=re.DOTALL)
        clean = re.sub(r'always(?:_ff|_comb|_latch)?\s*@?.*?end', '', clean, flags=re.DOTALL)
        clean = re.sub(r'\binitial\s+.*?end', '', clean, flags=re.DOTALL)
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
                ci = 0
                while ci < len(conn_text):
                    cm = re.match(r'\.(\w+)\s*\(\s*', conn_text[ci:])
                    if not cm:
                        ci += 1
                        continue
                    port_name = cm.group(1)
                    paren_start = ci + cm.end() - 1
                    conn_paren_end = self._match_paren(conn_text, paren_start)
                    if conn_paren_end < 0:
                        ci += 1
                        continue
                    conn_val = conn_text[paren_start + 1:conn_paren_end].strip()
                    conns.append(build_port_connection(
                        port_name, self._parse_expression(conn_val)
                    ))
                    ci = conn_paren_end + 1
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
            r'(?:#\s*\(([^()]*)\))?\s*'
            r'(?:\(((?:[^();]|\([^()]*\))*)\))?\s*;',
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
            initial_blocks = self._extract_initial(body)
            assignments = self._extract_assignments(body)
            instances = self._extract_instances(body)
            functions = self._parse_functions(body)
            tasks = self._parse_tasks(body)
            generates = self._parse_generates(body)

            self.modules.append(build_module(
                mod_name, params, ports, signals,
                always_blocks, assignments, instances,
                functions, tasks, generates,
                initial_blocks=initial_blocks,
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
                    inputs.append({"name": arg.group(2), "data_type": arg.group(1), "direction": "input", "width": 1})
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
                # Parse generate case
                case_match = re.match(r'case\s*\(', gen_inner)
                if case_match:
                    cp_start = case_match.end() - 1
                    cp_end = self._match_paren(gen_inner, cp_start)
                    if cp_end > 0:
                        case_expr_text = gen_inner[cp_start + 1:cp_end].strip()
                        case_expr = self._parse_expression(case_expr_text)
                        case_body_text = gen_inner[cp_end + 1:]
                        ec = case_body_text.find("endcase")
                        if ec >= 0:
                            inner = case_body_text[:ec]
                            items = []
                            default_stmts = []
                            ci = 0
                            while ci < len(inner):
                                rest = inner[ci:]
                                vm = re.match(r'([^:]+?)\s*:\s*begin\s*', rest, re.DOTALL)
                                if vm:
                                    val_text = vm.group(1).strip()
                                    ibs_off = vm.end()
                                    ibe = _find_block_end(rest, ibs_off)
                                    body_text = rest[ibs_off:ibe].strip()
                                    body_items = self._extract_instances(body_text)
                                    if not body_items:
                                        body_items = self._extract_assignments(body_text)
                                    if val_text == "default":
                                        default_stmts = body_items
                                    else:
                                        items.append({"value": self._parse_expression(val_text), "body": body_items})
                                    ci += ibe + 3
                                    continue
                                vm2 = re.match(r'([^:]+?)\s*:\s*([^;]+);', rest, re.DOTALL)
                                if vm2:
                                    val_text = vm2.group(1).strip()
                                    body_text = vm2.group(2).strip()
                                    body_items = self._extract_flat_assignments(body_text + ";")
                                    if val_text == "default":
                                        default_stmts = body_items
                                    else:
                                        items.append({"value": self._parse_expression(val_text), "body": body_items})
                                    ci += vm2.end()
                                    continue
                                ci += 1
                            gen_case_entry = {"type": "gen_case", "expression": case_expr, "items": items}
                            if default_stmts:
                                gen_case_entry["default"] = default_stmts
                            gens.append(gen_case_entry)
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
                # else if - create nested generate for the elif chain
                elif_gens = []
                self._parse_gen_if_else(rest_else, elif_gens, indent)
                if elif_gens:
                    else_body = elif_gens
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
                "generated_at": __import__("datetime").datetime.now().isoformat() + "Z",
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
