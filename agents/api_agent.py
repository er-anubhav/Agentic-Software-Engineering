from agents.base_agent import BaseAgent
from models.state import EngineeringState


class APIAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        prompt = f"""
You are a Principal API Architect.

Generate a VALID OpenAPI 3.0 specification.

Requirements:

{state.design}

IMPORTANT

The OpenAPI document MUST contain:

- openapi
- info
- paths
- responses

NEVER use keys like:
- devices
- apis
- routes

Use ONLY OpenAPI 3.0 standard fields.

Return ONLY valid JSON in this format:

{{
    "openapi.yaml": "...",
    "routes.py": "..."
}}
"""

        result = self.invoke_json(prompt)

        state.api_spec = result

        return state