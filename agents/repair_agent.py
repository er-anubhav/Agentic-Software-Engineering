from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.reflection_agent import ReflectionReport
from sandboxes.base_sandbox import BaseSandbox


class RepairAgent(BaseAgent):
    """
    Formulates surgical code fixes based on diagnostic reflection reports and re-verifies in sandbox.
    """

    def apply_repair(self, report: ReflectionReport, source_code: Dict[str, str], sandbox: BaseSandbox) -> Dict[str, str]:
        self.logger.info(f"Formulating surgical repair patch for {report.failing_file}...")

        target_file = report.failing_file
        if not target_file or target_file not in source_code:
            # Fallback to first python file if failing file path was generic
            target_file = list(source_code.keys())[0] if source_code else "main.py"

        current_code = source_code.get(target_file, "")

        prompt = f"""
You are a Principal Software Repair Engineer.

Fix the bug in the following source code based on the empirical diagnostic reflection report.

Diagnostic Report:
- Error Type: {report.error_type}
- Failing Line: {report.line_number}
- Root Cause: {report.root_cause}
- Recommended Fix: {report.suggested_fix}

Current Code of {target_file}:

{current_code}

Return ONLY the complete updated, working code string for {target_file}. Do NOT include markdown backticks or extra text.
"""

        repaired_code = self.invoke(prompt).strip()
        if repaired_code.startswith("```"):
            lines = repaired_code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            repaired_code = "\n".join(lines)

        source_code[target_file] = repaired_code
        sandbox.write_file(target_file, repaired_code)

        self.logger.info(f"Applied surgical repair patch to {target_file} in sandbox.")
        return source_code
