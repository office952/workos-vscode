import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def unauth_client():
    return TestClient(app)

def test_unauthenticated_endpoints(unauth_client):
    endpoints = [
        ("/api/v1/entities/intake_requests/", "GET"),
        ("/api/v1/entities/quotes/", "GET"),
        ("/api/v1/entities/orders/", "GET"),
        ("/api/v1/execution/plan/1", "GET"),
        ("/api/v1/operator/tasks", "GET")
    ]
    for url, method in endpoints:
        if method == "GET":
            response = unauth_client.get(url)
        # 401 Unauthorized or 403 Forbidden is expected
        assert response.status_code in [401, 403], f"Expected 401/403 for {url}, got {response.status_code}"