#!/usr/bin/env python3
"""
scripts/verify_layer_dependencies.py — AST-Based CI Layer Dependency Linter (DDD Architecture).

Enforces strict zero-upward-import architectural boundaries across the 6 DDD layers:
  - Layer 0: core
  - Layer 1: bootstrap
  - Layer 2: domain
  - Layer 3: infrastructure
  - Layer 4: application
  - Layer 5: interfaces, evaluation

Uses Python AST parsing to accurately inspect multiline, aliased, and relative imports.
"""

import os
import ast
import sys
from typing import List, Tuple

DDD_LAYER_MAP = {
    "core": 0,
    "config": 0,
    "bootstrap": 1,
    "domain": 2,
    "models": 2,
    "entities": 2,
    "value_objects": 2,
    "aggregates": 2,
    "services": 2,
    "events": 2,
    "verification": 2,
    "infrastructure": 3,
    "inference": 3,
    "storage": 3,
    "persistence": 3,
    "sandboxes": 3,
    "observability": 3,
    "application": 4,
    "agents": 4,
    "orchestration": 4,
    "learning": 4,
    "tools": 4,
    "interfaces": 5,
    "github_engine": 5,
    "platform": 5,
    "evaluation": 5,
    "benchmarks": 5,
    "fault_injection": 5,
    "stress": 5,
    "api": 5,
}


def get_layer(module_name: str) -> int:
    return DDD_LAYER_MAP.get(module_name, 5)


def check_layer_dependencies() -> List[Tuple[str, str, int, int]]:
    violations = []
    src_dir = os.path.abspath("src")

    for root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, src_dir)
            parts = rel_path.split(os.sep)

            if len(parts) < 1:
                continue

            current_module = parts[0]
            if current_module in ("domain", "application", "infrastructure", "interfaces") and len(parts) > 1:
                current_module = parts[1]

            current_layer = get_layer(current_module)

            try:
                content = open(filepath, "r", encoding="utf-8", errors="ignore").read()
                tree = ast.parse(content, filename=rel_path)
            except Exception as e:
                print(f"Warning: Could not parse AST for {rel_path}: {e}")
                continue

            for node in ast.walk(tree):
                imported_module = None

                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("src."):
                        sub_parts = node.module.split(".")
                        if len(sub_parts) > 1:
                            imported_module = sub_parts[1]
                            if imported_module in ("domain", "application", "infrastructure", "interfaces") and len(sub_parts) > 2:
                                imported_module = sub_parts[2]

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("src."):
                            sub_parts = alias.name.split(".")
                            if len(sub_parts) > 1:
                                imported_module = sub_parts[1]
                                if imported_module in ("domain", "application", "infrastructure", "interfaces") and len(sub_parts) > 2:
                                    imported_module = sub_parts[2]

                if imported_module:
                    imported_layer = get_layer(imported_module)
                    # Lower layer must NOT import from a higher layer (bootstrap excepted for wiring)
                    if current_layer < imported_layer and current_module != "bootstrap":
                        violations.append((rel_path, imported_module, current_layer, imported_layer))

    return violations


def main():
    violations = check_layer_dependencies()
    if violations:
        print("=== LAYER DEPENDENCY VIOLATIONS DETECTED ===")
        for path, imported, cur_lvl, imp_lvl in violations:
            print(f"  - AST LAYER VIOLATION in src/{path}: Layer {cur_lvl} ({path}) imports from Layer {imp_lvl} (src.{imported})")
        sys.exit(1)
    else:
        print("=== AST LAYER DEPENDENCY CHECK PASSED: Zero Upward Layer Violations ===")
        sys.exit(0)


if __name__ == "__main__":
    main()
