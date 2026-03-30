import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import os
from unittest.mock import patch, MagicMock

# Ensure we import from our local package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app import app
from backend.models import User, BillRecord

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def test_user():
    return {"username": "test_agent", "password": "secure_password_123"}

@pytest.fixture
def auth_token(test_user):
    # Register the user directly through the API
    client.post("/auth/register", json=test_user)
    # Login to get the token
    resp = client.post("/auth/login", data={"username": test_user["username"], "password": test_user["password"]})
    assert resp.status_code == 200, "Setup failed: Could not login test user"
    return resp.json()["access_token"]


# ── Tests: Authentication ─────────────────────────────────

def test_auth_registration_requires_strong_password():
    short_pw_user = {"username": "weak_user", "password": "12"}
    resp = client.post("/auth/register", json=short_pw_user)
    assert resp.status_code == 422 # Unprocessable Entity per validation rules


def test_auth_duplicate_username_fails(test_user):
    # Register once
    client.post("/auth/register", json=test_user)
    # Register twice
    resp = client.post("/auth/register", json=test_user)
    # Expect 400 Bad Request
    assert resp.status_code == 400 
    assert "already registered" in resp.json()["detail"].lower()


# ── Tests: Protected API Boundaries ───────────────────────

def test_download_endpoint_rejects_unauthenticated():
    # Attempt to download without passing a Bearer token
    resp = client.get("/bills/jobs/fake-uuid-1234/download?format=zip")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json()["detail"]


@patch("backend.routes.bills.is_rate_limited_redis")
def test_generate_endpoint_rate_limits(mock_ratelimit, auth_token):
    # Simulate Redis ratelimiter returning True
    mock_ratelimit.return_value = True
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "fileId": "mock_id",
        "titleData": {},
        "billItems": [],
        "extraItems": [],
        "options": {
            "generatePdf": False, "generateHtml": False,
            "templateVersion": "v1", "premiumPercent": 0, "premiumType": "above",
            "previousBillAmount": 0
        }
    }
    
    resp = client.post("/bills/generate", json=payload, headers=headers)
    assert resp.status_code == 429
    assert "Too many requests" in resp.json()["detail"]


def test_download_path_traversal_aborts(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Pass an obviously fake, traversal-oriented UUID (e.g., ../../../)
    # The getJob method intercepts 404s, but let's test a fake path execution.
    # We must patch the Redis job retrieval to simulate an attacker altering storage
    with patch("redis.asyncio.from_url") as mock_redis:
        from unittest.mock import AsyncMock
        mock_instance = AsyncMock()
        import json
        
        # Give it a hijacked output_dir inside the Redis JSON (from the legacy bug)
        fake_job_state = json.dumps({"status": "complete", "output_dir": "/etc/passwd"})
        mock_instance.get.return_value = fake_job_state
        mock_redis.return_value.__aenter__.return_value = mock_instance
        
        # Test download
        resp = client.get("/bills/jobs/fake-id/download", headers=headers)
        # Even with the redis fake output_dir injected above, the backend should completely 
        # ignore it because the new refactoring dictates output parsing purely from output_dir / UUID
        # Thus, it will fail at the DB boundary check saying "You do not have access" (since we didn't mock DB)
        assert resp.status_code in [403, 404]
