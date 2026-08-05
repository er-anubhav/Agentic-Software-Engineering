from config.llm import get_llm
from models.state import EngineeringState


class ArchitectureAgent:

    def __init__(self):
        self.llm = get_llm()

    def execute(self, state: EngineeringState):

        prompt = f"""
        You are a Principal Solution Architect.

        Your responsibility is ONLY to design the high-level software architecture.

        Business Requirement:

        {state.requirement}

        Engineering Tasks:

        {state.tasks}

        DO NOT generate:

        - SQL
        - Database schema
        - REST API definitions
        - Python code
        - Dockerfiles
        - Kubernetes manifests
        - Unit tests
        - Integration tests
        - Deployment scripts

        Return ONLY valid JSON using this format:

        {{
        "architecture_style": "",

        "components": [
            {{
            "name": "",
            "responsibility": ""
            }}
        ],

        "communication": [
            {{
            "from": "",
            "to": "",
            "protocol": ""
            }}
        ],

        "data_flow": [
            ""
        ]
        }}
        """

        response = self.llm.invoke(prompt)

        state.architecture = response.content

        return state