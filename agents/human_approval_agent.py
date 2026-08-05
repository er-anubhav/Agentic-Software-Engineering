from models.state import EngineeringState


class HumanApprovalAgent:

    def execute(self, state: EngineeringState):

        print("\n===== Human Approval =====")

        choice = input(
            "Validation completed successfully.\n"
            "Proceed to Code Generation? (Y/N): "
        ).strip().upper()

        state.approved = choice == "Y"

        return state