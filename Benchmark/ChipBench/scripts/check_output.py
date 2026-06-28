#!/usr/bin/env python3
"""
ChipBench check_output.py
Compares (src + tb) vs (restored + tb) using iverilog + vvp.
Handles TB pattern: instantiates RefModule (golden) and TopModule (DUT).
For golden run: src provides RefModule, and we alias src module as TopModule.
For DUT run: restored provides TopModule.
"""

import subprocess
import sys
import os
import argparse
import tempfile
import re


def make_topmodule_wrapper(src_file, work_dir):
    """Create a wrapper file with ONLY the first module renamed to TopModule.
    This avoids duplicating submodule definitions from the original file."""
    with open(src_file) as f:
        content = f.read()
    # Find the first 'module' declaration and its matching 'endmodule'
    m = re.search(r'\bmodule\s+', content)
    if not m:
        return None
    first_mod_start = m.start()
    # Find the matching endmodule (handles nested begin/end)
    depth = 0
    i = first_mod_start
    while i < len(content):
        w_match = re.search(r'\b(module|endmodule)\b', content[i:])
        if not w_match:
            break
        kw = w_match.group(1)
        if kw == 'module':
            depth += 1
        elif kw == 'endmodule':
            depth -= 1
            if depth == 0:
                first_mod_end = i + w_match.end()
                break
        i += w_match.end()
    else:
        # fallback: use entire content
        first_mod_end = len(content)

    first_module_text = content[first_mod_start:first_mod_end]
    # Rename the module name
    renamed = re.sub(r'\bmodule\s+\w+', 'module TopModule', first_module_text, count=1)
    out_path = os.path.join(work_dir, 'topmodule_wrapper.v')
    with open(out_path, 'w') as f:
        f.write(renamed)
    return out_path


def run_iverilog_work(work_dir, src_files):
    """Compile and run a set of source files with iverilog."""
    vvp_out = os.path.join(work_dir, 'a.out')
    cmd = ['iverilog', '-g2012', '-o', vvp_out] + src_files
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
    except subprocess.CalledProcessError as e:
        return None, e.stdout + '\n' + e.stderr, e.returncode
    except FileNotFoundError:
        return None, "iverilog not found", -1

    result = subprocess.run(['vvp', vvp_out], capture_output=True, text=True, timeout=300)
    return result.stdout, result.stderr, result.returncode


def run_ref_iverilog(src_file, tb_file, work_dir):
    """Compile and run (src + src_as_TopModule + tb) for golden reference.
    Both RefModule and TopModule come from src, so outputs always match."""
    wrapper = make_topmodule_wrapper(src_file, work_dir)
    return run_iverilog_work(work_dir, [src_file, wrapper, tb_file])


def run_dut_iverilog(src_file, restored_file, tb_file, work_dir):
    """Compile and run (src + restored_as_TopModule + tb) for DUT.
    RefModule comes from src (golden), TopModule comes from restored."""
    wrapper = make_topmodule_wrapper(restored_file, work_dir)
    return run_iverilog_work(work_dir, [src_file, wrapper, tb_file])


def compare_outputs(ref_stdout, ref_stderr, dut_stdout, dut_stderr):
    diffs = []
    if ref_stdout != dut_stdout:
        ref_lines = ref_stdout.splitlines()
        dut_lines = dut_stdout.splitlines()
        for i, (rl, dl) in enumerate(zip(ref_lines, dut_lines)):
            if rl != dl:
                diffs.append(f"stdout line {i+1}:\n  ref: {rl}\n  dut: {dl}")
        if len(ref_lines) != len(dut_lines):
            diffs.append(f"stdout line count mismatch: ref={len(ref_lines)} dut={len(dut_lines)}")
    if ref_stderr != dut_stderr:
        diffs.append("stderr differs")
    return diffs


def main():
    parser = argparse.ArgumentParser(description='Check output of restored design')
    parser.add_argument('--src', required=True, help='Original design file')
    parser.add_argument('--tb', required=True, help='Testbench file')
    parser.add_argument('--restored', required=True, help='Restored design file')
    args = parser.parse_args()

    for f in [args.src, args.tb, args.restored]:
        if not os.path.isfile(f):
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Running ref: {args.src} + {args.tb}")
        ref_stdout, ref_stderr, ref_ret = run_ref_iverilog(args.src, args.tb, tmpdir)
        if ref_stdout is None:
            print(f"Ref compilation failed:\n{ref_stderr}", file=sys.stderr)
            sys.exit(1)

        print(f"Running dut: {args.restored} vs ref={args.src}")
        dut_stdout, dut_stderr, dut_ret = run_dut_iverilog(args.src, args.restored, args.tb, tmpdir)
        if dut_stdout is None:
            print(f"DUT compilation failed:\n{dut_stderr}", file=sys.stderr)
            sys.exit(1)

        diffs = compare_outputs(ref_stdout, ref_stderr, dut_stdout, dut_stderr)
        if diffs:
            print("MISMATCH found:")
            for d in diffs:
                print(d)
            sys.exit(1)
        else:
            print("OK - outputs match")
            sys.exit(0)


if __name__ == '__main__':
    main()
