import os

from src.application.agents.base_agent import BaseAgent
from src.domain.models.state import EngineeringState
from src.infrastructure.storage.memory.context_engine import ContextEngine


class CodeGenerationAgent(BaseAgent):
    """
    Generates production-ready source code from
    validated architecture, design and API artifacts.
    """

    def __init__(self):
        super().__init__()
        self.context_engine = ContextEngine()

    def execute(self, state: EngineeringState):

        status = state.validation_report.get("status", "FAIL")

        if status not in ["PASS", "PASS_WITH_WARNINGS"]:
            self.logger.warning("Validation failed. Skipping code generation.")
            return state

        # Retrieve relevant codebase context via 9-stage RRF context engine
        context_payload = self.context_engine.query(
            prompt=state.requirement or "Generate codebase implementation",
            repo_id=getattr(state, "repository_path", "default")
        )
        context_str = context_payload.assembled_prompt_context or "No prior context snippets."

        prompt = f"""
You are a Principal Python Software Engineer.

Generate a production-ready FastAPI project.

Codebase Context & Retrieved Memory:
{context_str}

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