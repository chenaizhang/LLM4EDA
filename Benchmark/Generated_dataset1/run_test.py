#!/usr/bin/env python3
"""Test round-trip: verilog -> json -> verilog for all 100 test files."""
import subprocess
import os
import sys
import json
import re

SCRIPTS = "/home/gzr/new_test/scripts"
TEST_DIR = "/home/gzr/new_test/rtl/test_trans"
TMP_JSON = "/tmp/test_roundtrip.json"
TMP_JSON2 = "/tmp/test_roundtrip2.json"
TMP_V = "/tmp/test_roundtrip.v"

os.makedirs(TEST_DIR, exist_ok=True)
parse_script = os.path.join(SCRIPTS, "parse_to_json.py")
gen_script = os.path.join(SCRIPTS, "generate_from_json.py")

files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".v") and not f.startswith("gen_") and f != "run_test.py")

def strip_metadata(json_data):
    """Remove non-semantic fields for comparison."""
    if isinstance(json_data, dict):
        json_data.pop("metadata", None)
        json_data.pop("generated_at", None)
        json_data.pop("design_hierarchy", None)
        json_data.pop("id", None)
        json_data.pop("description", None)
        for k, v in json_data.items():
            strip_metadata(v)
    elif isinstance(json_data, list):
        for item in json_data:
            strip_metadata(item)

results = {"pass": 0, "fail": 0, "errors": []}

for f in files:
    filepath = os.path.join(TEST_DIR, f)
    print(f"Testing: {f}")

    # Step 1: Parse original verilog -> json
    r1 = subprocess.run(
        ["python3", parse_script, filepath, "-o", TMP_JSON],
        capture_output=True, text=True
    )
    if r1.returncode != 0:
        print(f"  PARSE FAILED: {r1.stderr.strip()[:200]}")
        results["fail"] += 1
        results["errors"].append((f, "parse_error", r1.stderr.strip()[:200]))
        continue

    try:
        with open(TMP_JSON) as jf:
            data1 = json.load(jf)
    except json.JSONDecodeError as e:
        print(f"  JSON DECODE FAILED: {e}")
        results["fail"] += 1
        results["errors"].append((f, "json_decode", str(e)))
        continue

    # Step 2: Generate json -> verilog
    r2 = subprocess.run(
        ["python3", gen_script, TMP_JSON, "-o", TMP_V],
        capture_output=True, text=True
    )
    if r2.returncode != 0:
        print(f"  GENERATE FAILED: {r2.stderr.strip()[:200]}")
        results["fail"] += 1
        results["errors"].append((f, "gen_error", r2.stderr.strip()[:200]))
        continue

    # Step 3: Parse generated verilog -> json again
    r3 = subprocess.run(
        ["python3", parse_script, TMP_V, "-o", TMP_JSON2],
        capture_output=True, text=True
    )
    if r3.returncode != 0:
        print(f"  RE-PARSE FAILED: {r3.stderr.strip()[:200]}")
        results["fail"] += 1
        results["errors"].append((f, "reparse_error", r3.stderr.strip()[:200]))
        continue

    try:
        with open(TMP_JSON2) as jf:
            data2 = json.load(jf)
    except json.JSONDecodeError as e:
        print(f"  RE-JSON DECODE FAILED: {e}")
        results["fail"] += 1
        results["errors"].append((f, "rejson_decode", str(e)))
        continue

    # Compare JSON outputs (strip metadata)
    strip_metadata(data1)
    strip_metadata(data2)

    if data1 == data2:
        print(f"  PASS")
        results["pass"] += 1
    else:
        print(f"  FAIL: JSON mismatch")
        # Show diff of module structures
        m1 = data1.get("modules", [])
        m2 = data2.get("modules", [])
        if len(m1) != len(m2):
            print(f"  Module count: original={len(m1)}, generated={len(m2)}")
        else:
            for mi, (mod1, mod2) in enumerate(zip(m1, m2)):
                if mod1 != mod2:
                    for key in set(list(mod1.keys()) + list(mod2.keys())):
                        if mod1.get(key) != mod2.get(key):
                            print(f"  Module {mi} key '{key}' differs")
                            if key in ("instances", "signals", "ports", "parameters"):
                                print(f"    orig: {json.dumps(mod1.get(key), indent=2, default=str)[:200]}")
                                print(f"    gen:  {json.dumps(mod2.get(key), indent=2, default=str)[:200]}")
                            break
        results["fail"] += 1
        results["errors"].append((f, "json_mismatch", ""))

print(f"\n{'='*60}")
print(f"RESULTS: {results['pass']} passed, {results['fail']} failed out of {len(files)}")
print(f"{'='*60}")
if results["errors"]:
    print("\nFailed tests summary:")
    for f, err, _ in results["errors"]:
        print(f"  {f}: {err}")
