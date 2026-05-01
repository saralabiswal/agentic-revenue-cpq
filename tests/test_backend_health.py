"""Test coverage for backend health behavior.

Author: Sarala Biswal
"""

from fastapi.testclient import TestClient

from apps.backend.main import app


def test_health_returns_ok() -> None:
    """Verify health returns ok behavior."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
