import unittest
from unittest.mock import MagicMock
from src.infrastructure.sandboxes.local_sandbox import LocalSandbox
from src.infrastructure.sandboxes.base_sandbox import SandboxResult
from src.application.agents.reflection_agent import ReflectionReport
from src.application.agents.repair_agent import RepairAgent, apply_unified_diff


class TestSurgicalRepairEngine(unittest.TestCase):

    def test_apply_unified_diff_single_line_replacement(self):
        original = "def foo():\n    return 1 / 0\n\ndef bar():\n    return 42"
        diff_patch = """
--- a/main.py
+++ b/main.py
@@ -1,3 +1,3 @@
 def foo():
-    return 1 / 0
+    return 42
"""
        patched = apply_unified_diff(original, diff_patch)
        self.assertIn("return 42", patched)
        self.assertNotIn("return 1 / 0", patched)
        self.assertIn("def bar():", patched)

    def test_apply_unified_diff_context_preservation(self):
        original = "import math\n\ndef calculate(x):\n    result = x / 0\n    return result"
        diff_patch = """
--- a/main.py
+++ b/main.py
@@ -3,3 +3,5 @@
 def calculate(x):
-    result = x / 0
+    if x == 0:
+        return 0
+    result = x / 2
"""
        patched = apply_unified_diff(original, diff_patch)
        self.assertIn("import math", patched)
        self.assertIn("if x == 0:", patched)
        self.assertNotIn("x / 0", patched)

    def test_surgical_repair_agent_integration(self):
        repair_agent = RepairAgent()
        repair_agent.invoke = MagicMock()
        repair_agent.invoke.return_value = """
--- a/main.py
+++ b/main.py
@@ -1,2 +1,2 @@
 def foo():
-    return 1 / 0
+    return 42
"""

        sandbox = LocalSandbox(base_dir="/tmp/test_surgical_repair_sandbox")
        sandbox.start()
        sandbox.execute_command = MagicMock()
        sandbox.execute_command.return_value = SandboxResult(exit_code=0, stdout="PASSED", stderr="")

        report = ReflectionReport(
            error_type="ZeroDivisionError",
            failing_file="main.py",
            line_number=2,
            root_cause="Division by zero",
            suggested_fix="Return constant integer 42"
        )

        source = {"main.py": "def foo():\n    return 1 / 0"}
        updated_source = repair_agent.apply_repair(report, source, sandbox, max_retries=1)

        self.assertIn("return 42", updated_source["main.py"])
        self.assertEqual(sandbox.read_file("main.py").strip(), "def foo():\n    return 42")
        sandbox.stop()

    def test_surgical_repair_automatic_rollback_on_failure(self):
        repair_agent = RepairAgent()
        repair_agent.invoke = MagicMock()
        repair_agent.invoke.return_value = """
--- a/main.py
+++ b/main.py
@@ -1,2 +1,2 @@
 def foo():
-    return 1 / 0
+    return broken syntax code
"""

        sandbox = LocalSandbox(base_dir="/tmp/test_surgical_repair_rollback")
        sandbox.start()
        sandbox.execute_command = MagicMock()
        # Verification fails with exit code 1
        sandbox.execute_command.return_value = SandboxResult(exit_code=1, stdout="", stderr="SyntaxError: invalid syntax")

        report = ReflectionReport(
            error_type="ZeroDivisionError",
            failing_file="main.py",
            line_number=2,
            root_cause="Division by zero",
            suggested_fix="Fix function"
        )

        original_code = "def foo():\n    return 1 / 0"
        source = {"main.py": original_code}
        updated_source = repair_agent.apply_repair(report, source, sandbox, max_retries=2)

        # Confirm automatic rollback restored original code
        self.assertEqual(updated_source["main.py"], original_code)
        self.assertEqual(sandbox.read_file("main.py"), original_code)
        sandbox.stop()


if __name__ == "__main__":
    unittest.main()
