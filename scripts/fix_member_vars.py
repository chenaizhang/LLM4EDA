#!/usr/bin/env python3
"""Add missing _q member variables to SimObject .hh files.

For each .cc file in src/custom/riscv/, find all `_q` variable names
and add them as uint64_t member variables to the corresponding .hh file
if they don't already exist.
"""

import re
import os
import sys

GEM5_SRC = "/home/gzr/new_test/gem5/src/custom/riscv"

def find_q_vars(cc_path):
    """Find all _q variable names used in a .cc file."""
    with open(cc_path) as f:
        content = f.read()
    
    # Find all identifiers ending in _q
    # Exclude: function/method calls, keywords, known non-vars
    vars_ = set()
    for m in re.finditer(r'\b([a-z_]\w*_q)\b', content):
        name = m.group(1)
        # Exclude things that look like function calls (followed by '(') or method params
        # Also exclude common patterns
        if name in ('clk_q', 'rst_q', 'get', 'set'):
            continue
        if name.endswith('_o_q') or name.endswith('_i_q'):
            # These might be for port-level storage
            pass
        vars_.add(name)
    
    return sorted(vars_)


def find_existing_members(hh_path):
    """Find existing uint64_t member variables in the .hh file."""
    with open(hh_path) as f:
        content = f.read()
    
    existing = set()
    for m in re.finditer(r'uint64_t\s+(\w+)\s*;', content):
        existing.add(m.group(1))
    
    return existing


def add_members_to_hh(hh_path, var_names):
    """Add missing _q variables as uint64_t members to the private section."""
    if not var_names:
        return False
    
    with open(hh_path) as f:
        content = f.read()
    
    existing = find_existing_members(hh_path)
    
    to_add = [v for v in var_names if v not in existing]
    if not to_add:
        return False
    
    # Find the private section or the first member variable
    # We'll add them before the public: section
    pattern = r'(\s+public:)'
    replacement = '\n' + '\n'.join(f'    uint64_t {v};' for v in to_add) + '\n\n  \g<1>'
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    # Also verify the section is correct - check if we need to add private: first
    if 'private:' not in new_content:
        # Add private section before public
        new_content = new_content.replace('  public:', '  private:\n\n  public:')
    
    with open(hh_path, 'w') as f:
        f.write(new_content)
    
    print(f"  Added {len(to_add)} vars: {', '.join(to_add[:10])}{'...' if len(to_add) > 10 else ''}")
    return True


def main():
    files = sorted(os.listdir(GEM5_SRC))
    cc_files = [f for f in files if f.endswith('.cc') and f != 'SConscript']
    
    for cc_file in cc_files:
        cc_path = os.path.join(GEM5_SRC, cc_file)
        base = cc_file[:-3]  # Remove .cc
        
        # Try different naming conventions for the .hh file
        # The .cc and .hh files should have the same base name
        hh_path = os.path.join(GEM5_SRC, f"{base}.hh")
        if not os.path.exists(hh_path):
            print(f"WARNING: No .hh file for {cc_file}")
            continue
        
        q_vars = find_q_vars(cc_path)
        if not q_vars:
            continue
        
        print(f"{cc_file}: {len(q_vars)} _q vars found")
        added = add_members_to_hh(hh_path, q_vars)
        if not added:
            print("  (all already exist)")


if __name__ == '__main__':
    main()
