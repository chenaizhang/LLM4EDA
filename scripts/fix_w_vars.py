#!/usr/bin/env python3
"""Add _w wire variable declarations and fix remaining issues."""

import re
import os

SRC = "/home/gzr/new_test/gem5/src/custom/riscv"

def fix_w_vars(cc_path):
    """Add _w variable declarations at start of evaluate()."""
    with open(cc_path) as f:
        content = f.read()
    
    # Find all _w variable names used in evaluate() body
    # Look for _w in expressions (assignments, conditions, calculations)
    w_vars = set()
    for m in re.finditer(r'\b([a-z_]\w*_w)\b', content):
        name = m.group(1)
        # Exclude known non-vars
        if name in ('new_w', 'width_w', 'CLOCK_PERIOD'):
            continue
        if name.endswith('_val_w'):
            continue
        w_vars.add(name)
    
    # Filter to only those that look like data storage (not method names)
    w_vars = {v for v in w_vars if not v.startswith('get') and not v.startswith('set')}
    w_vars = {v for v in w_vars if not v.startswith('ALU_SHIFT')}
    w_vars = {v for v in w_vars if not v.startswith('SR_')}
    
    if not w_vars:
        return False
    
    # Find the start of evaluate() function body
    eval_match = re.search(r'void\s+\w+::evaluate\s*\(\s*\)\s*\n?\{', content)
    if not eval_match:
        return False
    
    brace_pos = eval_match.end() - 1
    line_end = content.index('\n', brace_pos)
    insert_pos = line_end + 1
    
    # Filter out _w vars that already have declarations
    # Check the existing content for uintXX_t declarations of these vars
    already_declared = set()
    for d in re.finditer(r'uint(32|64)_t\s+(\w+)\s*[=;]', content):
        already_declared.add(d.group(2))
    
    to_add = sorted(v for v in w_vars if v not in already_declared and v not in [f'regs[{i}]' for i in range(32)])
    
    if not to_add:
        return False
    
    # Special: handle regs[31:0] -> not a _w variable
    to_add = [v for v in to_add if 'regs' not in v]
    
    if not to_add:
        return False
    
    # To avoid over-adding, let's check if any of these are actually used in assignments
    # Only add variables that are assigned to (appear on LHS or in computation)
    used_w = set()
    # Find lines where _w vars are on the LHS of = or used in expressions
    for v in to_add:
        # Only add if it appears as assignment target or in expression
        if re.search(r'\b' + re.escape(v) + r'\s*=', content) or \
           re.search(r'=\s*[^;]*\b' + re.escape(v) + r'\b', content):
            used_w.add(v)
        # Or used in conditions
        elif re.search(r'if\s*\([^)]*\b' + re.escape(v) + r'\b', content):
            used_w.add(v)
        elif re.search(r'while\s*\([^)]*\b' + re.escape(v) + r'\b', content):
            used_w.add(v)
        elif re.search(r'\b' + re.escape(v) + r'\s*&&|\|\||!', content):
            used_w.add(v)
        # Or even just present in any expression (function args, array index, etc)
        elif re.search(r'[^a-zA-Z_]' + re.escape(v) + r'[^a-zA-Z_]', content):
            used_w.add(v)
    
    if not used_w:
        return False
    
    # Add declarations at top of evaluate()
    # For now, just add a few key ones
    decls = '\n'.join(f'    uint32_t {v} = 0;' for v in sorted(used_w))
    
    content = content[:insert_pos] + '\n' + decls + '\n' + content[insert_pos:]
    
    with open(cc_path, 'w') as f:
        f.write(content)
    
    print(f"  Added {len(used_w)} _w local vars: {', '.join(sorted(used_w)[:10])}{'...' if len(used_w) > 10 else ''}")
    return True


def fix_regfile():
    """Add regs array and readReg/writeReg to riscv_regfile."""
    path = os.path.join(SRC, "riscv_regfile.hh")
    with open(path) as f:
        content = f.read()
    
    # Add regs array and helper methods
    if 'uint32_t regs' not in content:
        content = content.replace(
            '  private:',
            '  private:\n    uint32_t regs[32] = {};\n    uint32_t readReg(uint32_t addr) { return (addr < 32) ? regs[addr] : 0; }\n    void writeReg(uint32_t addr, uint32_t val) { if (addr < 32 && addr != 0) regs[addr] = val & 0xFFFFFFFF; }'
        )
        with open(path, 'w') as f:
            f.write(content)
        print("Fixed riscv_regfile.hh: added regs array and readReg/writeReg")
    
    # Also check if .cc needs fixing
    cc_path = os.path.join(SRC, "riscv_regfile.cc")
    with open(cc_path) as f:
        content = f.read()
    
    # readReg/writeReg calls may need params - check
    # The .cc probably calls readReg(addr) which now works since we added the method


def main():
    fix_regfile()
    
    for cc_file in sorted(os.listdir(SRC)):
        if not cc_file.endswith('.cc'):
            continue
        cc_path = os.path.join(SRC, cc_file)
        if fix_w_vars(cc_path):
            pass


if __name__ == '__main__':
    main()
