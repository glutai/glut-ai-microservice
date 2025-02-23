import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_create_user(client: TestClient):
    response = client.post(
        "/api/v1/users/",
        json={"user_id": 1, "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Test User"
    assert data["data"]["user_id"] == 1

def test_get_user(client: TestClient):
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["user_id"] == 1