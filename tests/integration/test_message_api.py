import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_create_message(client: TestClient):
    response = client.post(
        "/api/v1/messages/",
        json={
            "user_id": 1,
            "brand_id": 1,
            "content": {"text": "Test message"},
            "message_type": "message",
            "sender_type": "user",
            "sender_id": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["content"]["text"] == "Test message"

def test_get_messages(client: TestClient):
    response = client.get(
        "/api/v1/messages/1/1",
        params={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)