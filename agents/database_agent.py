from agents.base_agent import BaseAgent
from models.state import EngineeringState


class DatabaseAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        prompt = f"""
You are a Senior Database Architect.

Based on the database design below, generate database artifacts.

Return ONLY valid JSON.

Format:

{{
  "schema.sql":"...",
  "models.py":"..."
}}

Database Design:

{state.design.get("database", [])}
"""

        result = self.invoke_json(prompt)

        state.database_schema = result

        return state