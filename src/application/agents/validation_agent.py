import os
import json

from src.application.agents.base_agent import BaseAgent
from src.domain.models.state import EngineeringState


class ValidationAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        generated_path = "generated_project"

        expected_files = [
            "main.py",
            "routes.py",
            "service.py",
            "repository.py",
            "models.py",
            "config.py",
            "requirements.txt",
            "README.md"
        ]

        existing_files = []

        missing_files = []

        for file in expected_files:

            if os.path.exists(os.path.join(generated_path, file)):
                existing_files.append(file)
            else:
                missing_files.append(file)

        validation_context = {
            "generated_files": existing_files,
            "missing_files": missing_files,
            "database_artifacts": list(state.database_schema.keys()),
            "api_artifacts": list(state.api_spec.keys()),
            "brownfield_analysis": state.codebase_analysis
        }

        prompt = f"""
You are a Principal Software Architect performing an engineering review.

The engineering system has already inspected the generated project.

Project Validation Context

{json.dumps(validation_context, indent=2)}

Database Artifacts

{json.dumps(state.database_schema, indent=2)}

API Artifacts

{json.dumps(state.api_spec, indent=2)}

Validation Requirements

1. Validate architecture consistency.
2. Validate database schema.
3. Validate REST API completeness.
4. Validate OpenAPI correctness.
5. Validate requirement coverage.
6. Validate production readiness.
7. Review Brownfield analysis.
8. Validate generated project structure.
9. Do NOT report missing files if they already exist in generated_files.
10. Only report issues that truly exist.

Return ONLY valid JSON.

{{
    "status":"PASS|PASS_WITH_WARNINGS|FAIL",

    "checks":[
        {{
            "artifact":"",
            "status":"PASS|WARNING|FAIL",
            "message":""
        }}
    ],

    "recommendations":[
        ""
    ],

    "summary":""
}}
"""

        llm_result = self.invoke_json(prompt)

        # ----------------------------------------------------
        # Add deterministic validation
        # ----------------------------------------------------

        deterministic_checks = []

        for file in existing_files:

            deterministic_checks.append({
                "artifact": file,
                "status": "PASS",
                "message": "Artifact generated successfully."
            })

        for file in missing_files:

            deterministic_checks.append({
                "artifact": file,
                "status": "WARNING",
                "message": "Expected artifact was not generated."
            })

        llm_result["checks"] = deterministic_checks + llm_result.get(
            "checks",
            []
        )

        state.validation_report = llm_result

        return state