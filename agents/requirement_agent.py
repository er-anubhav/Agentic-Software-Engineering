import json
from tools.json_parser import parse_llm_json
from config.llm import get_llm
from models.state import EngineeringState

from agents.base_agent import BaseAgent

class RequirementAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        prompt = f"""
You are an experienced Software Architect.

Analyze the following software requirement.

Return ONLY valid JSON.

JSON format:

{{
    "functional_requirements": [],
    "non_functional_requirements": [],
    "assumptions": [],
    "ambiguities": [],
    "risks": []
}}

Requirement:

{state.requirement}
"""

        response = self.llm.invoke(prompt)

        try:
            # result = parse_llm_json(response.content)
            result = self.invoke_json(prompt)

            state.functional_requirements = result.get("functional_requirements", [])
            state.non_functional_requirements = result.get("non_functional_requirements", [])
            state.assumptions = result.get("assumptions", [])
            state.ambiguities = result.get("ambiguities", [])
            state.risks = result.get("risks", [])

        except Exception as e:
            print("JSON Parsing Error:", e)
            print(response.content)

        return state