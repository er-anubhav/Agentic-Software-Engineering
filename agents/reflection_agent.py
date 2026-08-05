import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from models.state import EngineeringState
from sandboxes.base_sandbox import SandboxResult


class ReflectionReport(BaseModel):
    error_type: str = Field(default="UnknownError")
    failing_file: str = Field(default="")
    line_number: int = Field(default=0)
    root_cause: str = Field(default="")
    suggested_fix: str = Field(default="")


class ReflectionAgent(BaseAgent):
    """
    Parses empirical execution tracebacks and sandbox logs to diagnose failure root causes.
    """

    def diagnose(self, result: SandboxResult, source_code: Dict[str, str]) -> ReflectionReport:
        self.logger.info("Parsing sandbox execution traceback for self-healing reflection...")

        if result.exit_code == 0:
            return ReflectionReport(error_type="None", root_cause="Execution succeeded with exit code 0.")

        traceback_str = result.traceback or result.stderr or result.stdout

        # Extract python exception pattern: E.g., File "main.py", line 42, in <module>
        file_match = re.search(r'File "([^"]+)", line (\d+)', traceback_str)
        failing_file = file_match.group(1) if file_match else ""
        line_num = int(file_match.group(2)) if file_match else 0

        error_match = re.search(r'([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception): (.*)', traceback_str)
        error_type = error_match.group(1) if error_match else "ExecutionError"
        error_msg = error_match.group(2) if error_match else traceback_str[:200]

        prompt = f"""
You are an expert Debugging & Root Cause Analysis Engineer.

Analyze the following execution traceback and source code snippet.

Traceback Log:

{traceback_str[:1000]}

Target Failing File: {failing_file} (Line {line_num})
Error: {error_type}: {error_msg}

Source Code:

{source_code.get(failing_file, "Source unavailable")}

Return ONLY valid JSON in this format:

{{
    "error_type": "{error_type}",
    "failing_file": "{failing_file}",
    "line_number": {line_num},
    "root_cause": "Detailed explanation of the bug",
    "suggested_fix": "Description of recommended patch"
}}
"""

        try:
            return self.invoke_structured(prompt, ReflectionReport)
        except Exception as e:
            self.logger.warning(f"Reflection structured LLM prompt failed: {e}")
            return ReflectionReport(
                error_type=error_type,
                failing_file=failing_file,
                line_number=line_num,
                root_cause=error_msg,
                suggested_fix="Fix exception at failing line"
            )
