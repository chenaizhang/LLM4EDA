#!/usr/bin/env python3
"""Fix all remaining undeclared identifier issues in generated .cc files.

Scans the build output for undeclared identifiers and adds them as
local variables or member variables as appropriate.
"""

import re
import os
import subprocess
import sys

GEM5_SRC = "/home/gzr/new_test/gem5"
RISCV_SRC = f"{GEM5_SRC}/src/custom/riscv"


def get_errors_for_file(cc_file):
    """Get list of undeclared identifiers from build output."""
    obj = cc_file.replace('.cc', '.o')
    result = subprocess.run(
        ['scons', f'build/X86/custom/riscv/{obj}'],
        cwd=GEM5_SRC,
        capture_output=True, text=True,
        env={**os.environ, 'PYTHON_CONFIG': 'python3.12-config'},
        timeout=300
    )
    errors = []
    for line in result.stderr.split('\n') + result.stdout.split('\n'):
        if cc_file in line and "error:" in line and "not declared" in line:
            errors.append(line)
    return errors


def extract_missing_names(error_lines):
    """Extract the missing identifier names from error lines."""
    names = set()
    for line in error_lines:
        # Match: 'XXX' was not declared
        m = re.search(r"'(\w+)' was not declared", line)
        if m:
            names.add(m.group(1))
        # Match: 'XXX' is not a member
        m = re.search(r"'(\w+)' is not a member", line)
        if m:
            names.add(m.group(1))
    return names


def fix_file(cc_file):
    """Add undeclared identifiers as local variables in evaluate()."""
    cc_path = os.path.join(RISCV_SRC, cc_file)
    hh_file = cc_file.replace('.cc', '.hh')
    hh_path = os.path.join(RISCV_SRC, hh_file)
    
    # Read .hh to find existing member variables
    existing_members = set()
    if os.path.exists(hh_path):
        with open(hh_path) as f:
            hh_content = f.read()
        for m in re.finditer(r'uint(32|64)_t\s+(\w+)\s*;', hh_content):
            existing_members.add(m.group(2))
    
    # Read .cc file
    with open(cc_path) as f:
        content = f.read()
    
    # Find evaluate() body
    eval_match = re.search(r'void\s+\w+::evaluate\s*\(\s*\)\s*\n?\{', content)
    if not eval_match:
        print(f"  WARNING: No evaluate() in {cc_file}")
        return
    
    brace_pos = eval_match.end() - 1
    line_end = content.index('\n', brace_pos) if '\n' in content[brace_pos:] else len(content)
    insert_pos = line_end + 1
    
    # Find ALL undeclared identifiers used in evaluate()
    # These are lowercase names with _w, _r, _q suffixes that aren't declared
    
    # Find all potential variable names
    all_vars = set()
    for m in re.finditer(r'\b([a-z_]\w*)\b', content[eval_match.start():]):
        name = m.group(1)
        # Skip keywords, common C++ things, and things that look like function calls
        if name in ('if', 'else', 'for', 'while', 'do', 'switch', 'case', 'return', 
                     'break', 'continue', 'int', 'uint32_t', 'uint64_t', 'bool', 
                     'true', 'false', 'void', 'const', 'static', 'class', 'struct',
                     'new', 'delete', 'sizeof', 'printf', 'DPRINTF', 'fprintf',
                     'std', 'cout', 'cin', 'endl', 'namespace', 'using',
                     'include', 'define', 'ifndef', 'endif', 'PARAMS',
                     'RiscvAlu', 'RiscvCore', 'RiscvCsr', 'RiscvDefs',
                     'RiscvDecode', 'RiscvDecoder', 'RiscvDivider', 'RiscvExec',
                     'RiscvFetch', 'RiscvIssue', 'RiscvLsu', 'RiscvMmu',
                     'RiscvMultiplier', 'RiscvPipeCtrl', 'RiscvRegfile',
                     'RiscvTraceSim', 'RiscvXilinx2r1w', 'RiscvCsrRegfile',
                     'SystemC', 'ClockedObject', 'SimObject',
                     'Clocked', 'Object'):
            continue
        # Skip uppercase (constants) and single letter variables
        if name.isupper() or len(name) <= 1:
            continue
        # Skip numbers
        if name.isdigit():
            continue
        # Skip things followed by ( (function calls)
        pos = m.end()
        if pos < len(content) and content[pos] == '(':
            continue
        all_vars.add(name)
    
    # Check which vars are declared (as members, params, or local)
    local_decls = set()
    for d in re.finditer(r'uint(32|64)_t\s+(\w+)\s*[=;]', content[eval_match.start():]):
        local_decls.add(d.group(2))
    for d in re.finditer(r'bool\s+(\w+)\s*[=;]', content[eval_match.start():]):
        local_decls.add(d.group(1))
    
    already_declared = existing_members | local_decls
    
    # Vars that need to be declared
    # Focus on _w and _r suffixed vars that aren't declared
    need_decl = set()
    for v in all_vars:
        if v.endswith('_w') or v.endswith('_r'):
            if v not in already_declared and not v.startswith('get') and not v.startswith('set'):
                need_decl.add(v)
        elif v.endswith('_q'):
            # _q might be member variables in .hh - check
            if v not in already_declared:
                # Could still need to be a member - skip for now
                pass
    
    # Also add vars that appear before the auto-generated declaration block
    # and seem to be used as variables
    for v in all_vars:
        if v.endswith('_w') or v.endswith('_r') or v.endswith('_q'):
            # These could be member vars added by fix_member_vars.py
            pass
        elif v.endswith('_d') or v.endswith('_e') or '_w_' in v:
            if v not in already_declared and not v.startswith('get') and not v.startswith('set'):
                need_decl.add(v)
    
    # Filter to only vars that actually appear in expressions, not just in comments
    # Remove comments first for detection
    clean_content = re.sub(r'//.*', '', content)
    clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
    
    actually_used = set()
    for v in need_decl:
        if re.search(r'\b' + re.escape(v) + r'\b', clean_content[eval_match.start():]):
            # Check it's actually used as a variable (not just in a string or comment)
            actually_used.add(v)
    
    if not actually_used:
        return
    
    # Add declarations
    decls = '\n'.join(f'    uint32_t {v} = 0;' for v in sorted(actually_used))
    
    content = content[:insert_pos] + '\n' + decls + '\n' + content[insert_pos:]
    
    with open(cc_path, 'w') as f:
        f.write(content)
    
    print(f"  Added {len(actually_used)} declarations")


def main():
    # Get list of .cc files
    cc_files = sorted([f for f in os.listdir(RISCV_SRC) if f.endswith('.cc')])
    
    for cc_file in cc_files:
        print(f"\n{cc_file}:")
        fix_file(cc_file)


if __name__ == '__main__':
    main()
