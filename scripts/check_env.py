#!/usr/bin/env python3
"""
环境与依赖检查脚本。
验证项目目录、Python 依赖、JSON Schema 合规性。
"""

import json
import os
import sys
import subprocess

SPEC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "specs")
GEM5_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gem5")

CHECKS = []


def check(description, ok):
    CHECKS.append((description, ok))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {description}")


def main():
    print("=" * 60)
    print("  Gem5 仿真环境检查")
    print("=" * 60)

    # Python 版本
    py_ok = sys.version_info >= (3, 6)
    check(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (>=3.6 required)", py_ok)

    # 依赖检查
    deps = {"jinja2": False, "jsonschema": False}
    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
        except ImportError:
            deps[dep] = False
    all_deps = all(deps.values())
    check(f"Python 依赖: {', '.join(d for d, ok in deps.items() if ok)}",
          all_deps)
    if not all_deps:
        missing = [d for d, ok in deps.items() if not ok]
        check(f"  缺失依赖: {', '.join(missing)}。运行: pip install {' '.join(missing)}", False)

    # Gem5 目录检查
    gem5_exists = os.path.isdir(GEM5_ROOT)
    check(f"Gem5 目录 '{GEM5_ROOT}' 存在", gem5_exists)

    if gem5_exists:
        build_dir = os.path.join(GEM5_ROOT, "build", "X86")
        check(f"Gem5 X86 构建目录 '{build_dir}' 存在", os.path.isdir(build_dir))

    # Schema 文件检查
    schema_path = os.path.join(SPEC_DIR, "schema_v1.json")
    schema_ok = os.path.isfile(schema_path)
    check(f"Schema 文件 '{schema_path}' 存在", schema_ok)

    # 设计 JSON 文件检查
    design_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example_design_complete.json")
    design_ok = os.path.isfile(design_path)
    check(f"设计 JSON 文件 '{design_path}' 存在", design_ok)

    # Schema 验证
    if schema_ok and design_ok:
        try:
            import jsonschema
            with open(schema_path) as f:
                schema = json.load(f)
            with open(design_path) as f:
                design = json.load(f)
            jsonschema.validate(design, schema)
            check("JSON Schema 验证通过", True)
        except jsonschema.ValidationError as e:
            check(f"JSON Schema 验证失败: {e.message}", False)
        except Exception as e:
            check(f"JSON Schema 验证出错: {e}", False)

    # Git 检查
    git_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git_ok = os.path.isdir(os.path.join(git_root, ".git"))
    check(f"Git 仓库 '{git_root}' 存在", git_ok)

    print("-" * 60)
    passed = sum(1 for _, ok in CHECKS if ok)
    total = len(CHECKS)
    print(f"  结果: {passed}/{total} 检查通过")
    print("=" * 60)

    return 0 if all(ok for _, ok in CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
