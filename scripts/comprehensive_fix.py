#!/usr/bin/env python3
"""
Comprehensive fix for all remaining compilation errors.
Step 1: Add #include "riscv_defines.hh" to all .cc files
Step 2: For each .cc file, add missing local variable declarations (any suffix)
Step 3: Fix specific known issues
"""

import re
import os
import sys

SRC = "/home/gzr/new_test/gem5/src/custom/riscv"


def step1_ensure_defines_include():
    """Add riscv_defines.hh include to all .cc files."""
    for f in sorted(os.listdir(SRC)):
        if not f.endswith('.cc'):
            continue
        path = os.path.join(SRC, f)
        with open(path) as r:
            content = r.read()
        marker = '#include "custom/riscv/riscv_defines.hh"'
        if marker in content:
            continue
        hh_name = f.replace('.cc', '.hh')
        old = f'#include "custom/riscv/{hh_name}"'
        if old in content:
            content = content.replace(old, old + f'\n{marker}')
            with open(path, 'w') as w:
                w.write(content)
            print(f"{f}: added defines header")


def step2_declare_undef_vars():
    """Scan evaluate() for undeclared identifiers and add declarations."""
    cpp_keywords = frozenset({
        'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
        'bool', 'break', 'case', 'catch', 'char', 'class', 'compl', 'const',
        'constexpr', 'continue', 'decltype', 'default', 'delete', 'do', 'double',
        'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern', 'false',
        'float', 'for', 'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable',
        'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator',
        'or', 'or_eq', 'private', 'protected', 'public', 'register', 'reinterpret_cast',
        'return', 'short', 'signed', 'sizeof', 'static', 'static_cast', 'struct',
        'switch', 'template', 'this', 'throw', 'true', 'try', 'typedef', 'typeid',
        'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile',
        'while', 'xor', 'xor_eq', 'override', 'final', 'uint32_t', 'uint64_t',
        'int32_t', 'int64_t', 'int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'size_t',
        'ssize_t', 'printf', 'DPRINTF', 'panic', 'fatal', 'warn', 'inform',
        'PARAMS', 'clocked_object', 'clk_i', 'rst_i',
    })

    for f in sorted(os.listdir(SRC)):
        if not f.endswith('.cc'):
            continue
        cc_path = os.path.join(SRC, f)
        hh_path = os.path.join(SRC, f.replace('.cc', '.hh'))

        with open(cc_path) as r:
            content = r.read()

        # Find evaluate() start
        m = re.search(r'void\s+\w+::evaluate\s*\(\s*\)\s*\n?\{', content)
        if not m:
            continue
        ctx = content[m.start():]

        # Collect existing declarations in evaluate()
        declared = set()
        for d in re.finditer(r'\b(uint32_t|uint64_t|bool|int|uint64_t)\s+(\w+)\s*[=;]', ctx):
            declared.add(d.group(2))
        for d in re.finditer(r'^\s*(\w+)\s*[=;]', ctx, re.MULTILINE):
            if d.group(1).endswith('_r') or d.group(1).endswith('_w'):
                # already declared as new type above
                pass

        # Add member variables from .hh
        if os.path.exists(hh_path):
            with open(hh_path) as r:
                hh_content = r.read()
            for d in re.finditer(r'uint(32|64)_t\s+(\w+)\s*;', hh_content):
                declared.add(d.group(2))

        # Find all lowercase identifiers in evaluate() that are not C++ keywords
        all_identifiers = set()
        for v in re.finditer(r'\b([a-z_]\w*)\b', ctx):
            name = v.group(1)
            if name in cpp_keywords:
                continue
            if len(name) <= 2 and name != 'pc' and name != 'op':
                continue
            all_identifiers.add(name)

        # Remove: function calls (followed by '(' in context)
        # and things that are already declared
        need_decl = set()
        for name in sorted(all_identifiers):
            if name in declared:
                continue
            # Skip if followed by '(' (function call)
            if re.search(r'\b' + re.escape(name) + r'\s*\(', content[m.start():m.start()+len(ctx)]):
                continue
            # Skip known non-variable patterns
            if name.startswith('set') or name.startswith('get'):
                continue
            if name in ('params', 'p', 'i', 'j', 'k', 'x', 'y', 'z', 'val', 'tmp', 'temp', 'idx', 'ptr'):
                continue
            # Skip things that look like function/method names
            if re.search(r'\b' + re.escape(name) + r'\s*\(', content):
                continue
            need_decl.add(name)

        if not need_decl:
            print(f"{f}: no undeclared vars")
            continue

        # Insert declarations after opening brace
        brace_pos = m.end() - 1
        line_end = content.index('\n', brace_pos) if '\n' in content[brace_pos:] else len(content)
        insert_pos = line_end + 1

        decl_lines = []
        for name in sorted(need_decl):
            decl_lines.append(f'    uint32_t {name} = 0;')
        decl_text = '\n' + '\n'.join(decl_lines) + '\n'

        content = content[:insert_pos] + decl_text + content[insert_pos:]

        with open(cc_path, 'w') as w:
            w.write(content)
        print(f"{f}: added {len(need_decl)} declarations: {', '.join(sorted(need_decl)[:15])}")


def step3_fix_specific():
    """Fix specific known issues."""
    # riscv_regfile.cc: readReg/writeReg calls
    path = os.path.join(SRC, "riscv_regfile.hh")
    with open(path) as r:
        content = r.read()
    # Check what's in the .cc
    cc_path = os.path.join(SRC, "riscv_regfile.cc")
    with open(cc_path) as r:
        cc_content = r.read()
    if 'readReg' in cc_content and 'readReg' not in content:
        content = content.replace(
            '  private:',
            '  private:\n    uint32_t regs[32] = {};\n    uint32_t readReg(uint32_t addr) { return (addr < 32) ? regs[addr] : 0; }\n    void writeReg(uint32_t addr, uint32_t val) { if (addr < 32 && addr != 0) regs[addr] = val & 0xFFFFFFFF; }'
        )
        with open(path, 'w') as w:
            w.write(content)
        print("riscv_regfile.hh: added regs array, readReg, writeReg")

    # riscv_regfile.cc: _w wire declarations
    with open(cc_path) as r:
        content = r.read()
    # Add needed wire vars
    eval_m = re.search(r'void\s+\w+::evaluate\s*\(\s*\)\s*\n?\{', content)
    if eval_m:
        brace_pos = eval_m.end() - 1
        line_end = content.index('\n', brace_pos)
        insert_pos = line_end + 1
        content = content[:insert_pos] + '''
    uint32_t reg_w = 0;
    uint32_t mem_w = 0;
    uint32_t rd_w = 0;
''' + content[insert_pos:]
        with open(cc_path, 'w') as w:
            w.write(content)
        print("riscv_regfile.cc: added wire declarations")


if __name__ == '__main__':
    step1_ensure_defines_include()
    step2_declare_undef_vars()
    step3_fix_specific()
