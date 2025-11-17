from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert "overall_status" in body


def test_query_endpoint():
    response = client.post("/query", json={"text": "ping"})
    assert response.status_code == 200
    body = response.json()
    assert "response" in body

