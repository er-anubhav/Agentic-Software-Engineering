import re
import difflib
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from agents.reflection_agent import ReflectionReport, ReflectionAgent
from sandboxes.base_sandbox import BaseSandbox, SandboxResult


def apply_unified_diff(original_text: str, diff_text: str) -> str:
    """
    Parses a unified git diff patch string and applies hunk changes cleanly
    to original text without modifying surrounding context lines.
    """
    if not diff_text.strip():
        return original_text

    original_lines = original_text.splitlines()
    patch_lines = diff_text.strip().splitlines()

    # If LLM returned direct code replacement without diff hunk headers
    if not any(line.startswith("@@") or line.startswith("---") or line.startswith("+++") for line in patch_lines):
        return diff_text.strip()

    # Filter header lines if present (--- a/... / +++ b/...)
    i = 0
    while i < len(patch_lines) and (patch_lines[i].startswith("---") or patch_lines[i].startswith("+++")):
        i += 1

    result_lines = list(original_lines)
    offset = 0

    while i < len(patch_lines):
        line = patch_lines[i]
        if line.startswith("@@"):
            hunk_match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if hunk_match:
                orig_start = int(hunk_match.group(1)) - 1  # 0-indexed
                orig_len = int(hunk_match.group(2)) if hunk_match.group(2) is not None else 1
            else:
                orig_start = 0
                orig_len = len(original_lines)

            i += 1
            hunk_removals = []
            hunk_additions = []
            hunk_context = []

            while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
                hline = patch_lines[i]
                if hline.startswith("-"):
                    hunk_removals.append(hline[1:])
                elif hline.startswith("+"):
                    hunk_additions.append(hline[1:])
                elif hline.startswith(" "):
                    hunk_context.append(hline[1:])
                i += 1

            target_start = orig_start + offset
            target_start = max(0, min(target_start, len(result_lines)))

            if hunk_removals:
                matched_idx = -1
                for search_idx in range(max(0, target_start - 5), min(len(result_lines), target_start + 10)):
                    if search_idx + len(hunk_removals) <= len(result_lines):
                        slice_lines = result_lines[search_idx:search_idx + len(hunk_removals)]
                        if [s.strip() for s in slice_lines] == [r.strip() for r in hunk_removals]:
                            matched_idx = search_idx
                            break

                if matched_idx != -1:
                    result_lines[matched_idx:matched_idx + len(hunk_removals)] = hunk_additions
                    offset += len(hunk_additions) - len(hunk_removals)
                else:
                    result_lines[target_start:target_start + len(hunk_removals)] = hunk_additions
            else:
                for idx, add_line in enumerate(hunk_additions):
                    result_lines.insert(target_start + idx, add_line)
                offset += len(hunk_additions)

        else:
            i += 1

    return "\n".join(result_lines)


class RepairAgent(BaseAgent):
    """
    Production-grade AST-Aware Surgical Git Diff Repair Engine (RFC-002).
    Generates minimal unified git diff patches, verifies changes in sandbox,
    and executes iterative self-healing reflection loops with automatic snapshot rollback.
    """

    def generate_unified_diff_patch(self, report: ReflectionReport, file_content: str, target_file: str) -> str:
        lines = file_content.splitlines()
        failing_line_num = report.line_number or 1
        start_line = max(1, failing_line_num - 10)
        end_line = min(len(lines), failing_line_num + 10)
        context_snippet = "\n".join(lines[start_line - 1:end_line])

        prompt = f"""
You are a Principal Software Repair Engineer specializing in AST-Aware Surgical Git Diff Patches.

Create a minimal UNIFIED GIT DIFF PATCH to resolve the failure in `{target_file}`.
DO NOT rewrite the entire file. Modify ONLY the failing lines.

Diagnostic Report:
- Error Type: {report.error_type}
- Failing Line Number: {report.line_number}
- Root Cause: {report.root_cause}
- Recommended Fix: {report.suggested_fix}

Code Context around Line {report.line_number} in {target_file}:
```python
{context_snippet}
```

Return ONLY a valid UNIFIED GIT DIFF PATCH format starting with `--- a/{target_file}` and `+++ b/{target_file}`.

Example Format:
--- a/{target_file}
+++ b/{target_file}
@@ -{start_line},{end_line - start_line + 1} +{start_line},{end_line - start_line + 1} @@
 context line 1
-failing code line
+repaired code line
 context line 2
"""

        patch_str = self.invoke(prompt).strip()

        # Clean markdown code blocks if wrapped by LLM
        if "```" in patch_str:
            lines_list = patch_str.splitlines()
            cleaned = []
            in_code = False
            for line in lines_list:
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if in_code or line.startswith("---") or line.startswith("+++") or line.startswith("@@") or line.startswith("-") or line.startswith("+"):
                    cleaned.append(line)
            patch_str = "\n".join(cleaned)

        return patch_str

    def apply_repair(self, report: ReflectionReport, source_code: Dict[str, str], sandbox: BaseSandbox, max_retries: int = 3) -> Dict[str, str]:
        self.logger.info(f"Initiating RFC-002 AST-Aware Surgical Git Diff Repair for {report.failing_file}...")

        target_file = report.failing_file
        if not target_file or target_file not in source_code:
            target_file = list(source_code.keys())[0] if source_code else "main.py"

        original_code = source_code.get(target_file, "")
        current_report = report
        reflection_agent = ReflectionAgent()

        for attempt in range(1, max_retries + 1):
            self.logger.info(f"Surgical Repair Attempt {attempt}/{max_retries} for {target_file}...")

            # 1. Generate minimal unified diff patch
            patch_str = self.generate_unified_diff_patch(current_report, original_code, target_file)
            self.logger.info(f"Generated Unified Diff Patch:\n{patch_str[:300]}")

            # 2. Apply unified patch surgically
            try:
                patched_code = apply_unified_diff(original_code, patch_str)
            except Exception as ex:
                self.logger.warning(f"Unified diff application error on attempt {attempt}: {ex}")
                continue

            # 3. Write patch to sandbox & verify execution
            source_code[target_file] = patched_code
            sandbox.write_file(target_file, patched_code)

            # Test verification in sandbox
            verify_res = sandbox.execute_command("pytest || python3 -m unittest")
            if verify_res.exit_code == 0:
                self.logger.info(f"Surgical repair succeeded on attempt {attempt}!")
                return source_code

            # 4. If test failed, reflect on new traceback and retry
            self.logger.warning(f"Surgical patch verification failed on attempt {attempt}. Reflecting...")
            current_report = reflection_agent.diagnose(verify_res, source_code)

        # Automatic Rollback if all surgical repair attempts fail
        self.logger.error(f"All {max_retries} surgical repair attempts failed for {target_file}. Rolling back sandbox state.")
        source_code[target_file] = original_code
        sandbox.write_file(target_file, original_code)
        return source_code
