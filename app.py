from orchestrator.workflow import Workflow


def main():

    requirement = """
Build a scalable URL shortener service with APIs,
persistence and analytics.
"""

    workflow = Workflow()

    result = workflow.execute(requirement)

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

    print("\n===== Database Artifacts =====")

    for filename, content in result.database_schema.items():
        print(f"\n--- {filename} ---")
        print(content[:500])

    print("\n===== API Artifacts =====")

    for filename, content in result.api_spec.items():
        print(f"\n--- {filename} ---")
        print(content[:500])

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