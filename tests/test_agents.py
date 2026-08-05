import unittest
from unittest.mock import MagicMock
from models.state import EngineeringState
from agents.requirement_agent import RequirementAgent
from agents.architecture_agent import ArchitectureAgent
from agents.base_agent import BaseAgent


class TestAgents(unittest.TestCase):

    def test_base_agent_invocations(self):
        agent = BaseAgent()
        agent.llm = MagicMock()
        agent.llm.invoke.return_value.content = '{"functional_requirements": ["Req 1"]}'

        res = agent.invoke_json("Test Prompt")
        self.assertEqual(res, {"functional_requirements": ["Req 1"]})
        agent.llm.invoke.assert_called_once_with("Test Prompt")

    def test_requirement_agent_single_llm_invocation(self):
        agent = RequirementAgent()
        agent.llm = MagicMock()
        agent.llm.invoke.return_value.content = '''{
            "functional_requirements": ["Create URL Shortener API"],
            "non_functional_requirements": ["Response time < 100ms"],
            "assumptions": ["PostgreSQL DB available"],
            "ambiguities": [],
            "risks": ["High concurrency traffic"]
        }'''

        state = EngineeringState()
        state.requirement = "Build a URL shortener"

        updated_state = agent.execute(state)

        # Ensure LLM was invoked ONLY ONCE (no double invocation bug!)
        self.assertEqual(agent.llm.invoke.call_count, 1)
        self.assertEqual(len(updated_state.functional_requirements), 1)
        self.assertEqual(updated_state.functional_requirements[0].description, "Create URL Shortener API")

    def test_architecture_agent_inheritance(self):
        agent = ArchitectureAgent()
        self.assertIsInstance(agent, BaseAgent)


if __name__ == "__main__":
    unittest.main()
