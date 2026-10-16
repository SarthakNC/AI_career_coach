import os
import pytest
from fastapi.testclient import TestClient

# Ensure sys.path includes backend directory
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from config import get_settings


@pytest.fixture
def client():
    """Create a FastAPI test client instance."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_returns_200(client):
    """Verify GET /health returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_payload(client):
    """Verify GET /health returns expected status and message."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "AI Career Coach API is running"


def test_status_endpoint_returns_200(client):
    """Verify GET /api/v1/status returns HTTP 200 with metadata."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "database" in data


def test_unconfigured_supabase_does_not_crash(client, monkeypatch):
    """
    Verify application handles missing/empty Supabase credentials without crashing,
    reporting 'not_configured' status accurately.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", None)
    monkeypatch.setattr(settings, "supabase_key", None)

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    db_info = data.get("database", {})
    assert db_info.get("configured") is False
    assert db_info.get("status") == "not_configured"
    assert "pending" in db_info.get("message", "").lower() or "not configured" in db_info.get("message", "").lower()


def test_cors_headers_present(client):
    """Verify CORS preflight / origin headers are properly processed."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
