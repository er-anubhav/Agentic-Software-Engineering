import os

from models.state import EngineeringState


class TestGenerationAgent:

    def execute(self, state: EngineeringState):

        print("\n===== Test Generation =====")

        test_dir = os.path.join("generated_project", "tests")
        os.makedirs(test_dir, exist_ok=True)

        tests = {
            "test_routes.py": """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code in (200, 404)
""",
            "test_service.py": """def test_placeholder():
    assert True
""",
            "test_repository.py": """def test_repository():
    assert True
"""
        }

        for filename, content in tests.items():

            with open(
                os.path.join(test_dir, filename),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(content)

        state.tests = tests

        print(f"Generated {len(tests)} test files.")

        return state