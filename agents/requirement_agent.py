from models.state import EngineeringState, Requirement
from agents.base_agent import BaseAgent
from schemas import RequirementAnalysisSchema


class RequirementAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        prompt = f"""
You are an experienced Software Architect.

Analyze the following software requirement.

Return ONLY valid JSON.

JSON format:

{{
    "functional_requirements": ["list of requirement strings"],
    "non_functional_requirements": ["list of requirement strings"],
    "assumptions": ["list of assumptions"],
    "ambiguities": ["list of ambiguities"],
    "risks": ["list of risks"]
}}

Requirement:

{state.requirement}
"""

        try:
            analysis = self.invoke_structured(prompt, RequirementAnalysisSchema)

            # Convert string lists to Requirement objects if needed
            state.functional_requirements = [
                Requirement(id=f"FR-{i+1}", description=req)
                for i, req in enumerate(analysis.functional_requirements)
            ]
            state.non_functional_requirements = [
                Requirement(id=f"NFR-{i+1}", description=req)
                for i, req in enumerate(analysis.non_functional_requirements)
            ]
            state.assumptions = [
                Requirement(id=f"ASM-{i+1}", description=req)
                for i, req in enumerate(analysis.assumptions)
            ]
            state.ambiguities = [
                Requirement(id=f"AMB-{i+1}", description=req)
                for i, req in enumerate(analysis.ambiguities)
            ]
            state.risks = [
                Requirement(id=f"RSK-{i+1}", description=req)
                for i, req in enumerate(analysis.risks)
            ]

        except Exception as e:
            self.logger.error(f"Requirement parsing failed: {e}")

        return state