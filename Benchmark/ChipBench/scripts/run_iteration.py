#!/usr/bin/env python3
"""
Core Iterative Workflow (workflow_process.md)
  Step 3: Resolve pairing -> testpoints
  Step 4: Iterative loop: parse -> check_json -> generate -> check_output
  Step 5-6: LLM feedback loop (analyze failures, improve scripts)
"""

import json
import os
import sys
import subprocess
import argparse
import shutil
import time
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BENCH_DIR / 'scripts'
SRC_DIR = BENCH_DIR / 'src'
TB_DIR = BENCH_DIR / 'tb'
JSON_DIR = BENCH_DIR / 'json'
RESTORED_DIR = BENCH_DIR / 'restored'
PAIRING_JSON = BENCH_DIR / 'pairing.json'
LOG_DIR = BENCH_DIR / 'iter_logs'
MAX_ITERATIONS = 50


def step3_resolve_pairings():
    print("=" * 60)
    print("Step 3: Resolve Pairings -> Testpoints")
    print("=" * 60)

    if PAIRING_JSON.exists():
        with open(PAIRING_JSON) as f:
            pairing = json.load(f)
        print(f"  Loaded pairing.json with {len(pairing)} entries")
    else:
        print("  [WARN] pairing.json not found, scanning src/ and tb/ directories")
        pairing = {}
        src_files = sorted(SRC_DIR.glob('*.v'))
        for sp in src_files:
            base = sp.stem
            candidates = [
                TB_DIR / f"{base}_tb.v",
                TB_DIR / f"tb_{base}.v",
                TB_DIR / f"{base}.v",
            ]
            for tp in candidates:
                if tp.exists():
                    pairing[base] = {
                        "src": f"src/{sp.name}",
                        "tb": f"tb/{tp.name}"
                    }
                    break

    testpoints = []
    for dname, paths in sorted(pairing.items()):
        src_path = BENCH_DIR / paths["src"]
        tb_path = BENCH_DIR / paths["tb"]
        json_path = JSON_DIR / f"{dname}.json"
        restored_path = RESTORED_DIR / f"{dname}.v"

        if not src_path.exists():
            print(f"  [SKIP] {dname}: src file missing: {src_path}")
            continue
        if not tb_path.exists():
            print(f"  [SKIP] {dname}: tb file missing: {tb_path}")
            continue

        tp = {
            "design": dname,
            "src_path": str(src_path),
            "tb_path": str(tb_path),
            "json_path": str(json_path),
            "restored_path": str(restored_path),
        }
        testpoints.append(tp)

    check_output_py = SCRIPTS_DIR / 'check_output.py'
    if not check_output_py.exists():
        print("  [ERROR] scripts/check_output.py not found!")
        sys.exit(1)

    print(f"  Total testpoints: {len(testpoints)}")
    return testpoints


def run_parse_to_json(tp):
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / 'parse_to_json.py'),
        '-o', tp['json_path'],
        tp['src_path'],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timed out"
    except Exception as e:
        return False, str(e)


def run_check_json_spec(tp):
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / 'check_json_spec.py'),
        tp['json_path'],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stdout = result.stdout.strip()
        passed = stdout == "true"
        return passed, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def run_generate_from_json(tp):
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / 'generate_from_json.py'),
        tp['json_path'],
        '-o', tp['restored_path'],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and os.path.exists(tp['restored_path']):
            return True, result.stdout + result.stderr
        return False, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def run_check_output(tp):
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / 'check_output.py'),
        '--src', tp['src_path'],
        '--tb', tp['tb_path'],
        '--restored', tp['restored_path'],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timed out (300s)"
    except Exception as e:
        return False, str(e)


def run_one_iteration(testpoints, round_num):
    print(f"\n{'=' * 60}")
    print(f"Round {round_num}")
    print(f"{'=' * 60}")

    results = []
    for tp in testpoints:
        entry = {
            "design": tp["design"],
            "src": tp["src_path"],
            "tb": tp["tb_path"],
            "json": tp["json_path"],
            "restored": tp["restored_path"],
            "parse_ok": False,
            "spec_ok": False,
            "gen_ok": False,
            "func_ok": False,
            "parse_log": "",
            "spec_log": "",
            "gen_log": "",
            "func_log": "",
        }

        print(f"\n  [{tp['design']}]")
        print(f"    Phase 1: parse_to_json...", end=' ')
        entry["parse_ok"], entry["parse_log"] = run_parse_to_json(tp)
        print("OK" if entry["parse_ok"] else "FAIL")
        if not entry["parse_ok"]:
            results.append(entry)
            continue

        print(f"    Phase 2: check_json_spec...", end=' ')
        entry["spec_ok"], entry["spec_log"] = run_check_json_spec(tp)
        print("OK" if entry["spec_ok"] else "FAIL")
        if not entry["spec_ok"]:
            results.append(entry)
            continue

        print(f"    Phase 3: generate_from_json...", end=' ')
        entry["gen_ok"], entry["gen_log"] = run_generate_from_json(tp)
        print("OK" if entry["gen_ok"] else "FAIL")
        if not entry["gen_ok"]:
            results.append(entry)
            continue

        print(f"    Phase 4: check_output...", end=' ')
        entry["func_ok"], entry["func_log"] = run_check_output(tp)
        print("OK" if entry["func_ok"] else "FAIL")
        results.append(entry)

    passed = sum(1 for r in results if r["spec_ok"] and r["gen_ok"] and r["func_ok"])
    total = len(results)
    failed = [r for r in results if not (r["spec_ok"] and r["gen_ok"] and r["func_ok"])]

    print(f"\n  Round {round_num} Summary:")
    print(f"    Passed: {passed}/{total}")
    print(f"    Failed: {len(failed)}")

    # Log detailed results
    log_file = LOG_DIR / f"round_{round_num}.json"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump({
            "round": round_num,
            "passed": passed,
            "total": total,
            "results": results,
        }, f, indent=2)

    return passed, total, failed, results


def collect_failure_report(failed):
    report_lines = []
    report_lines.append(f"FAILURE REPORT: {len(failed)} testpoints failed\n")
    report_lines.append("=" * 60)
    for f in failed:
        report_lines.append(f"\n--- {f['design']} ---")
        report_lines.append(f"  src: {f['src']}")
        report_lines.append(f"  tb: {f['tb']}")
        if not f['parse_ok']:
            report_lines.append(f"  Phase 1 FAIL (parse_to_json):")
            report_lines.append(f"    {f['parse_log'][:500]}")
        if f['parse_ok'] and not f['spec_ok']:
            report_lines.append(f"  Phase 2 FAIL (check_json_spec):")
            report_lines.append(f"    {f['spec_log'][:500]}")
        if f['parse_ok'] and f['spec_ok'] and not f['gen_ok']:
            report_lines.append(f"  Phase 3 FAIL (generate_from_json):")
            report_lines.append(f"    {f['gen_log'][:500]}")
        if f['parse_ok'] and f['spec_ok'] and f['gen_ok'] and not f['func_ok']:
            report_lines.append(f"  Phase 4 FAIL (check_output):")
            report_lines.append(f"    {f['func_log'][:500]}")
    return "\n".join(report_lines)


def show_scripts():
    pj = SCRIPTS_DIR / 'parse_to_json.py'
    gj = SCRIPTS_DIR / 'generate_from_json.py'
    print(f"\n--- parse_to_json.py ({pj.stat().st_size} bytes) ---")
    print(pj.read_text()[:300] + "...")
    print(f"\n--- generate_from_json.py ({gj.stat().st_size} bytes) ---")
    print(gj.read_text()[:300] + "...")


def main():
    parser = argparse.ArgumentParser(description='ChipBench Core Iteration Workflow')
    parser.add_argument('--rounds', type=int, default=MAX_ITERATIONS, help='Max iterations')
    parser.add_argument('--start-round', type=int, default=1, help='Starting round number')
    args = parser.parse_args()

    os.chdir(BENCH_DIR)

    testpoints = step3_resolve_pairings()

    for round_num in range(args.start_round, args.start_round + args.rounds):
        passed, total, failed, results = run_one_iteration(testpoints, round_num)

        if passed == total:
            print(f"\n{'=' * 60}")
            print("ALL TESTPOINTS PASSED!")
            print(f"{'=' * 60}")
            break

        if round_num >= args.start_round + args.rounds - 1:
            print(f"\nReached max iterations ({args.rounds}). Manual intervention needed.")
            print(f"Failed: {len(failed)}/{total}")
            report = collect_failure_report(failed)
            print(report)
            break

        # LLM Feedback Step
        print(f"\n{'=' * 60}")
        print("LLM Feedback: Analyzing failures & improving scripts")
        print(f"{'=' * 60}")

        failure_report = collect_failure_report(failed)
        print(failure_report[:2000])

        # Read current scripts
        parse_to_json_src = (SCRIPTS_DIR / 'parse_to_json.py').read_text()
        gen_from_json_src = (SCRIPTS_DIR / 'generate_from_json.py').read_text()

        # Task: launch LLM to analyze and fix scripts
        print(f"\n  Sending failure data to LLM for analysis...")
        print(f"  (This would invoke an LLM to improve parse_to_json.py and generate_from_json.py)")

        # Here we would invoke an LLM via task tool
        # For now, we log the failure report and continue
        # In a real setup, this is where the LLM would analyze and return fixes

    print(f"\nFinal iteration logs in: {LOG_DIR}/")
    print(f"JSON files in: {JSON_DIR}/")
    print(f"Restored files in: {RESTORED_DIR}/")


if __name__ == '__main__':
    main()
