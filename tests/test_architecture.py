"""
tests/test_architecture.py — Executable Architecture Test Suite.

Enforces zero-upward layer dependency rules and clean architecture boundaries directly inside pytest.
"""
import os
import ast
import unittest
from scripts.verify_layer_dependencies import check_layer_dependencies


class TestArchitectureGovernance(unittest.TestCase):
    """
    Executable CI Architecture Governance Tests.
    """

    def test_layer_dependency_hierarchy(self):
        """Verify zero upward layer import violations across all DDD layers."""
        violations = check_layer_dependencies()
        if violations:
            violation_msgs = [
                f"Layer violation in src/{path}: Layer {cur_lvl} imports from Layer {imp_lvl} (src.{imported})"
                for path, imported, cur_lvl, imp_lvl in violations
            ]
            self.fail("Architecture violations detected:\n" + "\n".join(violation_msgs))

    def test_domain_has_no_infrastructure_imports(self):
        """Verify domain layer has ZERO dependencies on infrastructure or interfaces."""
        domain_dir = os.path.abspath(os.path.join("src", "domain"))
        if not os.path.exists(domain_dir):
            return

        forbidden_prefixes = ("src.infrastructure", "src.interfaces")

        for root, _, files in os.walk(domain_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue

                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, domain_dir)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read(), filename=rel_path)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for forbidden in forbidden_prefixes:
                            self.assertFalse(
                                node.module.startswith(forbidden),
                                f"Domain file 'src/domain/{rel_path}' illegally imports from '{node.module}'"
                            )


if __name__ == "__main__":
    unittest.main()
