from models.state import EngineeringState


class ExecutionPlannerAgent:
    """
    Builds the execution pipeline for the engineering agents.
    """

    def execute(self, state: EngineeringState):

        state.execution_plan = {
            "execution_plan": [

                {
                    "step": 1,
                    "agent": "DatabaseAgent",
                    "objective": "Generate database schema and ORM models"
                },

                {
                    "step": 2,
                    "agent": "APIAgent",
                    "objective": "Generate OpenAPI specification and REST API routes"
                },

                {
                    "step": 3,
                    "agent": "ValidationAgent",
                    "objective": "Validate generated engineering artifacts"
                },

                {
                    "step": 4,
                    "agent": "HumanApprovalAgent",
                    "objective": "Obtain human approval before generating source code"
                },

                {
                    "step": 5,
                    "agent": "CodeGenerationAgent",
                    "objective": "Generate production-ready source code"
                },

                {
                    "step": 6,
                    "agent": "TestGenerationAgent",
                    "objective": "Generate unit and integration test scaffolding"
                },

                {
                    "step": 7,
                    "agent": "SummaryAgent",
                    "objective": "Generate engineering execution summary"
                }

            ]
        }

        return state