import sys
import argparse
from src.application.orchestration.workflow import Workflow


def main():
    parser = argparse.ArgumentParser(description="Agentic Software Engineering Platform V2")
    parser.add_argument("--serve", action="store_true", help="Run FastAPI server on port 8000")
    parser.add_argument("--requirement", type=str, default="Build a scalable URL shortener service with APIs, persistence and analytics.", help="Requirement prompt")

    args = parser.parse_args()

    if args.serve:
        import uvicorn
        print("Starting Agentic SE Platform API server on http://localhost:8000...")
        uvicorn.run("api.app_api:app", host="0.0.0.0", port=8000, reload=False)
    else:
        workflow = Workflow()
        result = workflow.execute(args.requirement)

        print("\n=============================")
        print("Functional Requirements")
        print(result.functional_requirements)

        print("\nTasks")
        print(result.tasks)

        print("\nArchitecture")
        print(result.architecture)

        print("\nDesign")
        print(result.design)

        print("\nExecution Plan")
        print(result.execution_plan)

        print("\n===== Validation Report =====")
        print(result.validation_report)

        print("\n===== Generated Project =====")
        if result.generated_code:
            for filename in result.generated_code.keys():
                print(filename)
        else:
            print("No project generated.")

        print("\n===== Engineering Summary =====")
        print(result.engineering_summary)


if __name__ == "__main__":
    main()