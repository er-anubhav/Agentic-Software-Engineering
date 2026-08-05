import os

from agents.base_agent import BaseAgent
from models.state import EngineeringState


class CodeGenerationAgent(BaseAgent):
    """
    Generates production-ready source code from
    validated architecture, design and API artifacts.
    """

    def execute(self, state: EngineeringState):

        status = state.validation_report.get("status", "FAIL")

        if status not in ["PASS", "PASS_WITH_WARNINGS"]:
            print("Validation failed. Skipping code generation.")
            return state

        prompt = f"""
You are a Principal Python Software Engineer.

Generate a production-ready FastAPI project.

Requirements

{state.functional_requirements}

Architecture

{state.architecture}

Design

{state.design}

Database

{state.database_schema}

API

{state.api_spec}

Generate ONLY JSON.

The keys MUST be file names.

Return exactly this structure:

{{
    "main.py":"",
    "routes.py":"",
    "service.py":"",
    "repository.py":"",
    "models.py":"",
    "config.py":"",
    "requirements.txt":"",
    "README.md":""
}}
"""

        result = self.invoke_json(prompt)

        state.generated_code = result

        output_dir = "generated_project"

        os.makedirs(output_dir, exist_ok=True)

        for filename, content in result.items():

            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"\nGenerated {len(result)} files.")
        print(f"Project saved to '{output_dir}'")

        return state