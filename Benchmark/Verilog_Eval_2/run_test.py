#!/usr/bin/env python3
"""Test round-trip on all _ref.sv files."""
import subprocess, os, json

SCRIPTS = "/home/gzr/LLM4EDA/scripts"
TEST_DIR = "/home/gzr/LLM4EDA/Benchmark/Verilog_Eval_2"
TMP_JSON = "/tmp/test_sv.json"
TMP_JSON2 = "/tmp/test_sv2.json"
TMP_V = "/tmp/test_sv.v"

parse_script = os.path.join(SCRIPTS, "parse_to_json.py")
gen_script = os.path.join(SCRIPTS, "generate_from_json.py")

files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith("_ref.sv"))

def strip_ids(d):
    if isinstance(d, dict):
        d.pop("id", None); d.pop("description", None); d.pop("delay", None)
        d.pop("metadata", None); d.pop("generated_at", None); d.pop("design_hierarchy", None)
        for v in d.values(): strip_ids(v)
    elif isinstance(d, list):
        for item in d: strip_ids(item)

results = {"pass": 0, "fail": 0, "errors": []}

for f in files:
    filepath = os.path.join(TEST_DIR, f)
    r1 = subprocess.run(["python3", parse_script, filepath, "-o", TMP_JSON],
                        capture_output=True, text=True)
    if r1.returncode != 0:
        print(f"  {f}: PARSE FAIL")
        results["fail"] += 1
        results["errors"].append((f, "parse", r1.stderr.strip()[:100]))
        continue
    try:
        with open(TMP_JSON) as jf: d1 = json.load(jf)
    except:
        print(f"  {f}: JSON FAIL")
        results["fail"] += 1
        continue

    r2 = subprocess.run(["python3", gen_script, TMP_JSON, "-o", TMP_V],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"  {f}: GEN FAIL: {r2.stderr.strip()[:100]}")
        results["fail"] += 1
        results["errors"].append((f, "gen", r2.stderr.strip()[:100]))
        continue

    r3 = subprocess.run(["python3", parse_script, TMP_V, "-o", TMP_JSON2],
                        capture_output=True, text=True)
    if r3.returncode != 0:
        print(f"  {f}: REPARSE FAIL: {r3.stderr.strip()[:100]}")
        results["fail"] += 1
        results["errors"].append((f, "reparse", r3.stderr.strip()[:100]))
        continue

    try:
        with open(TMP_JSON2) as jf: d2 = json.load(jf)
    except:
        print(f"  {f}: JSON2 FAIL")
        results["fail"] += 1
        continue

    strip_ids(d1); strip_ids(d2)
    if d1 == d2:
        print(f"  {f}: PASS")
        results["pass"] += 1
    else:
        print(f"  {f}: FAIL")
        results["fail"] += 1
        results["errors"].append((f, "mismatch", ""))

print(f"\nRESULTS: {results['pass']} passed, {results['fail']} failed out of {len(files)}")
if results["errors"]:
    print("\nFirst 10 failures:")
    for f, err, _ in results["errors"][:10]:
        print(f"  {f}: {err}")
