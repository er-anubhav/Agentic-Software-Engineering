import unittest
from src.domain.models.schemas import (
    RequirementAnalysisSchema,
    PlannerSchema,
    ArchitectureSchema,
    DesignSchema,
    ValidationSchema,
    ValidationCheck
)


class TestSchemas(unittest.TestCase):

    def test_requirement_schema(self):
        data = {
            "functional_requirements": ["FR1", "FR2"],
            "non_functional_requirements": ["NFR1"],
            "assumptions": ["A1"],
            "ambiguities": ["B1"],
            "risks": ["R1"]
        }
        schema = RequirementAnalysisSchema.model_validate(data)
        self.assertEqual(len(schema.functional_requirements), 2)
        self.assertEqual(schema.non_functional_requirements[0], "NFR1")

    def test_planner_schema(self):
        data = {"tasks": ["Task 1", "Task 2"]}
        schema = PlannerSchema.model_validate(data)
        self.assertEqual(len(schema.tasks), 2)

    def test_validation_schema(self):
        data = {
            "status": "PASS",
            "checks": [
                {"artifact": "main.py", "status": "PASS", "message": "OK"}
            ],
            "recommendations": [],
            "summary": "Validation successful"
        }
        schema = ValidationSchema.model_validate(data)
        self.assertEqual(schema.status, "PASS")
        self.assertEqual(len(schema.checks), 1)


if __name__ == "__main__":
    unittest.main()
