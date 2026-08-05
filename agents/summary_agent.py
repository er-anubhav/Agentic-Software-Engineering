import os

from models.state import EngineeringState


class SummaryAgent:
    """
    Generates the final engineering execution summary.
    """

    def execute(self, state: EngineeringState):

        codebase = state.codebase_analysis if state.codebase_analysis else {}

        summary = {

            "implementation_plan": state.tasks,

            "generated_artifacts": {
                "database": list(state.database_schema.keys()),
                "api": list(state.api_spec.keys()),
                "application": list(state.generated_code.keys())
            },

            "validation_status": state.validation_report.get(
                "status",
                "UNKNOWN"
            ),

            "validation_summary": state.validation_report.get(
                "summary",
                ""
            ),

            "risks": state.validation_report.get(
                "recommendations",
                []
            ),

            "brownfield_analysis": {

                "project_type": codebase.get(
                    "project_type",
                    "greenfield"
                ),

                "python_files": len(
                    codebase.get("python_files", [])
                ),

                "classes": len(
                    codebase.get("classes", [])
                ),

                "functions": len(
                    codebase.get("functions", [])
                ),

                "dependencies": len(
                    codebase.get("dependencies", [])
                ),

                "apis_detected": codebase.get(
                    "apis",
                    []
                ),

                "database_models": codebase.get(
                    "database_models",
                    []
                )
            },

            "assumptions": state.assumptions,

            "limitations": [
                "Prototype implementation intended for interview demonstration.",
                "Advanced orchestration (parallel execution and retries) is not yet implemented.",
                
            ]
        }

        state.engineering_summary = summary

        self.write_markdown(summary)

        print("\nEngineering summary generated.")

        return state

    def write_markdown(self, summary):

        os.makedirs("generated_project", exist_ok=True)

        path = "generated_project/engineering_summary.md"

        with open(path, "w", encoding="utf-8") as f:

            f.write("# Engineering Execution Summary\n\n")

            f.write("## Validation Status\n\n")
            f.write(f"**{summary['validation_status']}**\n\n")

            if summary["validation_summary"]:
                f.write(summary["validation_summary"])
                f.write("\n\n")

            f.write("## Implementation Plan\n\n")

            for task in summary["implementation_plan"]:
                f.write(f"- {task}\n")

            f.write("\n")

            f.write("## Generated Artifacts\n")

            for category, artifacts in summary["generated_artifacts"].items():

                f.write(f"\n### {category.title()}\n")

                for artifact in artifacts:
                    f.write(f"- {artifact}\n")

            brownfield = summary["brownfield_analysis"]

            f.write("\n## Brownfield Repository Analysis\n\n")

            f.write(f"- Project Type : {brownfield['project_type']}\n")
            f.write(f"- Python Files : {brownfield['python_files']}\n")
            f.write(f"- Classes : {brownfield['classes']}\n")
            f.write(f"- Functions : {brownfield['functions']}\n")
            f.write(f"- Dependencies : {brownfield['dependencies']}\n")

            f.write("\n### Detected APIs\n")

            if brownfield["apis_detected"]:

                for api in brownfield["apis_detected"]:

                    method = api.get("method", "")
                    path = api.get("path", "")
                    function = api.get("function", "")

                    f.write(
                        f"- {method} {path} ({function})\n"
                    )

            else:

                f.write("- No APIs detected\n")

            f.write("\n### Database Models\n")

            if brownfield["database_models"]:

                for model in brownfield["database_models"]:

                    f.write(
                        f"- {model['name']} ({model['file']})\n"
                    )

            else:

                f.write("- No database models detected\n")

            f.write("\n## Risks / Recommendations\n\n")

            for risk in summary["risks"]:
                f.write(f"- {risk}\n")

            f.write("\n## Assumptions\n\n")

            for assumption in summary["assumptions"]:
                f.write(f"- {assumption}\n")

            f.write("\n## Current Limitations\n\n")

            for limitation in summary["limitations"]:
                f.write(f"- {limitation}\n")