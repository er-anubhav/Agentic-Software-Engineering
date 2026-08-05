from src.application.agents.base_agent import BaseAgent
from src.domain.models.state import EngineeringState
from src.domain.models.schemas import ArchitectureSchema


class ArchitectureAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        prompt = f"""
You are a Principal Solution Architect.

Your responsibility is ONLY to design the high-level software architecture.

Business Requirement:

{state.requirement}

Engineering Tasks:

{state.tasks}

DO NOT generate SQL, Database schema, REST API definitions, Python code, or tests.

Return ONLY valid JSON using this format:

{{
    "architecture_style": "Monolithic / Microservices",

    "components": [
        {{
            "name": "Component Name",
            "responsibility": "Component Responsibility"
        }}
    ],

    "communication": [
        {{
            "from": "Sender",
            "to": "Receiver",
            "protocol": "HTTP/REST"
        }}
    ],

    "data_flow": [
        "Description of step 1",
        "Description of step 2"
    ]
}}
"""

        try:
            arch_data = self.invoke_json(prompt)
            state.architecture = str(arch_data)
        except Exception as e:
            self.logger.warning(f"Architecture parsing failed: {e}, falling back to raw invoke")
            state.architecture = self.invoke(prompt)

        return state