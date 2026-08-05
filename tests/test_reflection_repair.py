import unittest
from unittest.mock import MagicMock
from sandboxes.base_sandbox import SandboxResult
from sandboxes.local_sandbox import LocalSandbox
from agents.reflection_agent import ReflectionAgent, ReflectionReport
from agents.repair_agent import RepairAgent
from fastapi.testclient import TestClient
from api.app_api import app


class TestReflectionRepairAPI(unittest.TestCase):

    def test_reflection_traceback_parsing(self):
        agent = ReflectionAgent()
        agent.invoke_structured = MagicMock()
        agent.invoke_structured.return_value = ReflectionReport(
            error_type="ZeroDivisionError",
            failing_file="main.py",
            line_number=10,
            root_cause="Division by zero",
            suggested_fix="Check denominator before division"
        )

        dummy_result = SandboxResult(
            exit_code=1,
            stdout="",
            stderr='File "main.py", line 10\nZeroDivisionError: division by zero',
            traceback='File "main.py", line 10\nZeroDivisionError: division by zero'
        )

        report = agent.diagnose(dummy_result, {"main.py": "x = 1 / 0"})
        self.assertEqual(report.error_type, "ZeroDivisionError")
        self.assertEqual(report.failing_file, "main.py")

    def test_repair_agent_patching(self):
        agent = RepairAgent()
        agent.invoke = MagicMock()
        agent.invoke.return_value = "def foo():\n    return 42\n"

        sandbox = LocalSandbox(base_dir="/tmp/test_repair_sandbox")
        sandbox.start()

        report = ReflectionReport(
            error_type="SyntaxError",
            failing_file="main.py",
            line_number=1,
            root_cause="Syntax error",
            suggested_fix="Fix function definition"
        )

        source = {"main.py": "def foo(): broken"}
        updated_source = agent.apply_repair(report, source, sandbox)

        self.assertEqual(updated_source["main.py"].strip(), "def foo():\n    return 42")
        self.assertEqual(sandbox.read_file("main.py").strip(), "def foo():\n    return 42")

        sandbox.stop()

    def test_api_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "HEALTHY")


if __name__ == "__main__":
    unittest.main()
