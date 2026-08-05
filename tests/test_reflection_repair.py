import unittest
from unittest.mock import MagicMock
from src.infrastructure.sandboxes.base_sandbox import SandboxResult
from src.infrastructure.sandboxes.local_sandbox import LocalSandbox
from src.application.agents.reflection_agent import ReflectionAgent, ReflectionReport
from src.application.agents.repair_agent import RepairAgent
from fastapi.testclient import TestClient
from src.interfaces.platform.api.app_api import app


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
        sandbox.execute_command = MagicMock()
        sandbox.execute_command.return_value = SandboxResult(exit_code=0, stdout="PASSED", stderr="")

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

    def test_api_async_job_submission(self):
        client = TestClient(app)
        response = client.post("/api/v1/execute", json={"requirement": "Create REST API"})
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "QUEUED")

        job_id = data["job_id"]
        status_res = client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(status_res.status_code, 200)
        self.assertIn(status_res.json()["status"], ["QUEUED", "RUNNING", "COMPLETED", "FAILED"])


if __name__ == "__main__":
    unittest.main()
