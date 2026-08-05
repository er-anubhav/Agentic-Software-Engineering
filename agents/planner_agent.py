from agents.base_agent import BaseAgent
from models.state import EngineeringState


class PlannerAgent(BaseAgent):
    """
    Planner Agent

    Converts functional requirements into
    implementation tasks for the engineering team.
    """

    def execute(self, state: EngineeringState):

        # Convert Requirement objects into readable text
        requirements = "\n".join(
            f"- {req['description'] if isinstance(req, dict) else req.description}"
            for req in state.functional_requirements
        )

        prompt = f"""
You are a Senior Software Engineering Manager.

Your job is to break software requirements into implementation tasks.

Return ONLY valid JSON.

Example:

{{
    "tasks": [
        "Design REST APIs",
        "Design Database Schema",
        "Implement URL Shortening Algorithm",
        "Implement Redirect Service",
        "Implement Analytics Service",
        "Implement Persistence Layer",
        "Write Unit Tests",
        "Write Integration Tests"
    ]
}}

Requirements:

{requirements}
"""

        result = self.invoke_json(prompt)

        state.tasks = result.get("tasks", [])

        return state