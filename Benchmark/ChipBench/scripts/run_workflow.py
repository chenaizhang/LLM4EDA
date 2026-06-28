#!/usr/bin/env python3
"""
ChipBench Dataset Preprocessing Workflow
Implements workflow_dataset.md steps 3-6:
  3. Classification & Differentiated Filtering
  4. Archive & Re-classification
  5. Pairing & Cleanup
  6. Generate check_output.py
"""

import os
import sys
import re
import shutil
import subprocess
import json
import argparse
import hashlib
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_DIR = BENCH_DIR / 'original'
FILTERED_DIR = BENCH_DIR / 'filtered'
SRC_DIR = BENCH_DIR / 'src'
TB_DIR = BENCH_DIR / 'tb'
SCRIPTS_DIR = BENCH_DIR / 'scripts'

DISCARD_LOG = BENCH_DIR / 'discard_design.log'
PAIRING_JSON = BENCH_DIR / 'pairing.json'

TB_SYSTEM_TASKS = {'$display', '$dumpfile', '$dumpvars', '$finish', '$stop', '$monitor'}
DELAY_PATTERN = re.compile(r'#\s*\d+')
CLOCK_PATTERN = re.compile(r'forever\s+#\d+\s+\w+\s*=\s*~\w+')


def classify_file(content: str) -> str:
    if any(t in content for t in TB_SYSTEM_TASKS):
        return 'testbench'
    if DELAY_PATTERN.search(content):
        return 'testbench'
    if CLOCK_PATTERN.search(content):
        return 'testbench'
    if re.search(r'module\s+\w+', content) and re.search(r'endmodule', content):
        return 'design'
    return 'unknown'


def check_with_iverilog(filepath: Path) -> bool:
    try:
        result = subprocess.run(
            ['iverilog', '-g2012', '-o', '/dev/null', str(filepath)],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [WARN] iverilog timed out on {filepath.name}")
        return False
    except FileNotFoundError:
        print("  [ERROR] iverilog not found. Install Icarus Verilog.")
        return False


def step3_classify_and_filter():
    print("=" * 60)
    print("Step 3: Classification & Differentiated Filtering")
    print("=" * 60)

    FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    sv_files = sorted(ORIGINAL_DIR.glob('*.sv'))
    if not sv_files:
        print("  No .sv files found in original/")
        return

    stats = {'design': 0, 'testbench': 0, 'unknown': 0,
             'design_pass': 0, 'design_fail': 0}

    for fpath in sv_files:
        content = fpath.read_text()
        ftype = classify_file(content)
        stats[ftype] += 1
        dest = FILTERED_DIR / fpath.name

        if ftype == 'design':
            print(f"  [DESIGN] {fpath.name} -> checking syntax...", end=' ')
            if check_with_iverilog(fpath):
                shutil.copy2(fpath, dest)
                print("PASS")
                stats['design_pass'] += 1
            else:
                print("FAIL (discarded)")
                stats['design_fail'] += 1
                with open(DISCARD_LOG, 'a') as log:
                    log.write(f"{fpath.name}\tiverilog syntax check failed\n")

        elif ftype == 'testbench':
            print(f"  [TB]    {fpath.name} -> auto-pass")
            shutil.copy2(fpath, dest)

        else:
            print(f"  [WARN]  {fpath.name} -> unknown type, skipping")

    print()
    print(f"  Summary:")
    print(f"    Design files:   {stats['design']}  (pass={stats['design_pass']}, fail={stats['design_fail']})")
    print(f"    Testbench files: {stats['testbench']}")
    print(f"    Unknown:        {stats['unknown']}")
    if stats['design_fail'] > 0:
        print(f"  Discard log written to {DISCARD_LOG}")


def step4_archive():
    print("\n" + "=" * 60)
    print("Step 4: Archive & Re-classification")
    print("=" * 60)

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    TB_DIR.mkdir(parents=True, exist_ok=True)

    filtered_files = sorted(FILTERED_DIR.glob('*.sv'))
    if not filtered_files:
        print("  No files in filtered/")
        return

    for fpath in filtered_files:
        content = fpath.read_text()
        ftype = classify_file(content)
        stem = fpath.stem
        new_name = f"{stem}.v"
        if ftype == 'design':
            shutil.move(str(fpath), str(SRC_DIR / new_name))
            print(f"  {fpath.name} -> src/{new_name}")
        elif ftype == 'testbench':
            shutil.move(str(fpath), str(TB_DIR / new_name))
            print(f"  {fpath.name} -> tb/{new_name}")
        else:
            print(f"  {fpath.name} -> unknown type, left in filtered/")


def extract_base_name(stem: str) -> str:
    for suffix in ['_test', '_ref']:
        if stem.endswith(suffix):
            return stem[:-len(suffix)]
    return stem


def step5_pair_and_cleanup():
    print("\n" + "=" * 60)
    print("Step 5: Pairing & Cleanup")
    print("=" * 60)

    src_files = {f.stem: f for f in SRC_DIR.glob('*.v')}
    tb_files = {f.stem: f for f in TB_DIR.glob('*.v')}

    # Index TB files by their base name (strip _test)
    tb_by_base = {}
    for tstem, tf in tb_files.items():
        tbase = extract_base_name(tstem)
        tb_by_base[tbase] = tf

    pairing = {}
    orphan_tbs = set(tb_files.keys())
    paired_tbs = set()

    for sname, spath in sorted(src_files.items()):
        base = extract_base_name(sname)

        if base in tb_by_base:
            matched = tb_by_base[base]
            paired_tbs.add(matched.stem)
            pairing[base] = {
                "src": f"src/{spath.name}",
                "tb": f"tb/{matched.name}"
            }
            print(f"  PAIRED: {spath.name} <-> {matched.name}")
        else:
            print(f"  [WARN] No TB found for {spath.name}. Will need LLM generation. Skipping for now.")
            print(f"    Base name: '{base}'")

    orphan_tbs -= paired_tbs
    if orphan_tbs:
        print(f"\n  Cleaning {len(orphan_tbs)} orphan TB file(s):")
        for tname in sorted(orphan_tbs):
            (TB_DIR / tb_files[tname].name).unlink()
            print(f"    Removed tb/{tb_files[tname].name}")

    with open(PAIRING_JSON, 'w') as f:
        json.dump(pairing, f, indent=2)
    print(f"\n  Pairing saved to {PAIRING_JSON}")
    print(f"  Total pairs: {len(pairing)}")


def step6_generate_check_output():
    print("\n" + "=" * 60)
    print("Step 6: Generate check_output.py")
    print("=" * 60)

    tb_v_files = sorted(TB_DIR.glob('*.v'))
    if not tb_v_files:
        print("  No TB files in tb/")
        return

    tb_contents = {}
    for f in tb_v_files:
        tb_contents[f.stem] = f.read_text()

    if not PAIRING_JSON.exists():
        print("  [ERROR] pairing.json not found. Run step 5 first.")
        return

    with open(PAIRING_JSON) as f:
        pairing = json.load(f)

    script_path = SCRIPTS_DIR / 'check_output.py'
    generate_check_output_script(script_path, tb_v_files, pairing, BENCH_DIR)
    script_path.chmod(0o755)
    print(f"  Generated: {script_path}")


def generate_check_output_script(script_path, tb_v_files, pairing, bench_dir):
    script_content = '''#!/usr/bin/env python3
"""
ChipBench check_output.py
Generated by workflow pipeline.
Compares (src + tb) vs (restored + tb) using iverilog + vvp.
"""

import subprocess
import sys
import os
import argparse
import tempfile
import shutil


def run_iverilog(src_file, tb_file, work_dir):
    vvp_out = os.path.join(work_dir, 'a.out')
    cmd = ['iverilog', '-o', vvp_out, src_file, tb_file]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
    except subprocess.CalledProcessError as e:
        return None, e.stdout + '\\n' + e.stderr, e.returncode

    result = subprocess.run(['vvp', vvp_out], capture_output=True, text=True, timeout=300)
    return result.stdout, result.stderr, result.returncode


def compare_outputs(ref_stdout, ref_stderr, dut_stdout, dut_stderr):
    diffs = []
    if ref_stdout != dut_stdout:
        ref_lines = ref_stdout.splitlines()
        dut_lines = dut_stdout.splitlines()
        for i, (rl, dl) in enumerate(zip(ref_lines, dut_lines)):
            if rl != dl:
                diffs.append(f"stdout line {i+1}:\\n  ref: {rl}\\n  dut: {dl}")
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

    with tempfile.TemporaryDirectory() as tmpdir:
        # Ensure files exist
        for f in [args.src, args.tb, args.restored]:
            if not os.path.isfile(f):
                print(f"Error: file not found: {f}")
                sys.exit(1)

        print(f"Running ref: {args.src} + {args.tb}")
        ref_stdout, ref_stderr, ref_ret = run_iverilog(args.src, args.tb, tmpdir)
        if ref_stdout is None:
            print(f"Ref compilation failed:\\n{ref_stderr}")
            sys.exit(1)

        print(f"Running dut: {args.restored} + {args.tb}")
        dut_stdout, dut_stderr, dut_ret = run_iverilog(args.restored, args.tb, tmpdir)
        if dut_stdout is None:
            print(f"DUT compilation failed:\\n{dut_stderr}")
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
'''
    with open(script_path, 'w') as f:
        f.write(script_content)
    print(f"  Generated check_output.py at {script_path}")


def cleanup_temp_dirs():
    print("\nCleaning up temporary directory: filtered/")
    if FILTERED_DIR.exists():
        shutil.rmtree(FILTERED_DIR)
        print("  Removed filtered/")


def main():
    parser = argparse.ArgumentParser(description='ChipBench Dataset Workflow Pipeline')
    parser.add_argument('--skip-filter', action='store_true', help='Skip Step 3 (classification & filtering)')
    parser.add_argument('--skip-archive', action='store_true', help='Skip Step 4 (archive)')
    parser.add_argument('--skip-pair', action='store_true', help='Skip Step 5 (pairing)')
    parser.add_argument('--skip-check', action='store_true', help='Skip Step 6 (generate check_output.py)')
    parser.add_argument('--keep-filtered', action='store_true', help='Keep filtered/ directory after completion')
    args = parser.parse_args()

    os.chdir(BENCH_DIR)

    if not args.skip_filter:
        step3_classify_and_filter()
    else:
        print("Skipping Step 3")

    if not args.skip_archive:
        step4_archive()
    else:
        print("Skipping Step 4")

    if not args.skip_pair:
        step5_pair_and_cleanup()
    else:
        print("Skipping Step 5")

    if not args.skip_check:
        step6_generate_check_output()
    else:
        print("Skipping Step 6")

    if not args.keep_filtered:
        cleanup_temp_dirs()

    print("\n" + "=" * 60)
    print("Workflow complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
