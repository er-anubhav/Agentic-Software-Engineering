class ExecutionEngine:
    """
    Executes agents dynamically based on the execution plan.

    Features
    --------
    - Sequential orchestration
    - Retry on validation failure
    - Human approval before code generation
    - Stops workflow on critical failures
    """

    MAX_RETRIES = 1

    def __init__(self, registry):
        self.registry = registry

    def execute(self, state):

        plan = sorted(
            state.execution_plan.get("execution_plan", []),
            key=lambda x: x["step"]
        )

        print("\n===== Execution Engine =====")

        for step in plan:

            agent_name = step["agent"]

            print(f"\nStep {step['step']}")
            print(f"Agent      : {agent_name}")
            print(f"Objective  : {step['objective']}")

            agent = self.registry.get(agent_name)

            if not agent:
                print(f"{agent_name} not implemented yet.")
                continue

            retry = 0

            while retry <= self.MAX_RETRIES:

                state = agent.execute(state)

                # -------------------------------
                # Validation Handling
                # -------------------------------
                if agent_name == "ValidationAgent":

                    status = (
                        state.validation_report.get("status", "FAIL")
                        .upper()
                    )

                    if status in ("PASS", "PASS_WITH_WARNINGS"):

                        print(f"\nValidation Status : {status}")
                        break

                    retry += 1

                    if retry > self.MAX_RETRIES:

                        print("\nValidation failed after retry.")
                        print("Workflow aborted.")
                        return state

                    print("\nValidation failed.")
                    print(f"Retrying Validation ({retry}/{self.MAX_RETRIES})...")

                    continue

                # -------------------------------
                # Human Approval
                # -------------------------------
                if agent_name == "HumanApprovalAgent":

                    if not getattr(state, "approved", False):

                        print("\nWorkflow stopped by user.")
                        return state

                break

        return state