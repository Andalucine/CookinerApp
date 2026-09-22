from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


def test_health_returns_ok():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    app.dependency_overrides.clear()
