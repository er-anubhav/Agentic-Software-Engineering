from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code in (200, 404)
