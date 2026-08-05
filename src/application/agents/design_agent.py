from src.application.agents.base_agent import BaseAgent
from src.domain.models.state import EngineeringState


class DesignAgent(BaseAgent):
    """
    Converts architecture into a structured software design.
    """

    def execute(self, state: EngineeringState):

        prompt = f"""
You are a Principal Software Architect.

Based on the architecture and implementation tasks below, create a software design.

Return ONLY valid JSON.

Format:

{{
    "modules": [
        {{
            "name": "",
            "responsibility": ""
        }}
    ],

    "apis":[
        {{
            "name":"",
            "method":"",
            "path":""
        }}
    ],

    "database":[
        {{
            "table":"",
            "purpose":""
        }}
    ]
}}

Tasks:

{state.tasks}

Architecture:

{state.architecture}
"""

        result = self.invoke_json(prompt)

        state.design = result

        return state