import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_weather_endpoint_not_found_for_invalid_city():
    response = client.get("/weather/invalid_city")
    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}

def test_weather_endpoint_valid_city():
    response = client.get("/weather/london")
    assert response.status_code == 200
    # Add assertions for the expected response for a valid city
    assert "city" in response.json()
    assert "temperature" in response.json()
    assert "description" in response.json()
