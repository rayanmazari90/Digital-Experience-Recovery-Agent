from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path, **overrides):
    settings = Settings(
        database_path=tmp_path / "test.sqlite3",
        storage_root=tmp_path / "storage",
        hermes_enabled=False,
        hermes_api_key="test-key",
        **overrides,
    )
    return TestClient(create_app(settings))


def create_session(client):
    scenario = client.post(
        "/scenarios",
        json={"name": "Synthetic", "description": "Synthetic only", "data": {"synthetic": True}},
    ).json()
    session = client.post("/sessions", json={"scenario_id": scenario["id"], "title": "Synthetic"}).json()
    return session


def test_api_auth_can_be_required(tmp_path):
    client = make_client(tmp_path, api_auth_enabled=True, api_key="expected-key")
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"X-DERA-API-Key": "expected-key"}).status_code == 200
    assert client.get("/health", headers={"Authorization": "Bearer expected-key"}).status_code == 200


def test_security_headers_and_cors_are_hardened(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_sensitive_payloads_are_rejected_by_default(tmp_path):
    client = make_client(tmp_path)
    session = create_session(client)
    response = client.post(
        f"/sessions/{session['id']}/evidence",
        json={
            "source_type": "synthetic-customer-signal",
            "title": "bad payload",
            "payload": {"customer_email": "person@example.com", "synthetic": True},
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "sensitive_data_rejected"


def test_upload_size_limit_is_enforced(tmp_path):
    client = make_client(tmp_path, max_upload_bytes=10)
    session = create_session(client)
    response = client.post(
        f"/sessions/{session['id']}/artifacts",
        data={"label": "oversize"},
        files={"file": ("too-large.txt", b"01234567890", "text/plain")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "artifact_too_large"


def test_audit_logs_and_retention_endpoint_exist(tmp_path):
    client = make_client(tmp_path)
    session = create_session(client)
    logs = client.get("/audit/logs").json()["audit_logs"]
    assert any(item["action"] == "create_session" and item["resource_id"] == session["id"] for item in logs)
    prune = client.post("/maintenance/retention/prune")
    assert prune.status_code == 200
    assert prune.json()["retention_days"] == 7
