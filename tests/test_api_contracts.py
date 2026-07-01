import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        database_path=tmp_path / "test.sqlite3",
        storage_root=tmp_path / "storage",
        hermes_enabled=False,
        hermes_api_key="test-key",
    )
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def scenario(client):
    response = client.post(
        "/scenarios",
        json={
            "name": "Synthetic IAM Gateway Failure",
            "description": "Synthetic auth outage with no real customer data",
            "data": {"journey": "Login/Authentication", "synthetic": True},
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def session(client, scenario):
    response = client.post(
        "/sessions",
        json={"scenario_id": scenario["id"], "title": "Morning synthetic recovery simulation"},
    )
    assert response.status_code == 201
    return response.json()


def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["hermes_enabled"] is False
    assert body["hermes_base_url"].startswith("http")


def test_scenario_creation_and_retrieval_contract(client, scenario):
    assert scenario["id"].startswith("scn_")
    assert scenario["name"] == "Synthetic IAM Gateway Failure"
    assert scenario["data"]["synthetic"] is True

    fetched = client.get(f"/scenarios/{scenario['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == scenario


def test_session_creation_contract(client, scenario, session):
    assert session["id"].startswith("ses_")
    assert session["scenario_id"] == scenario["id"]
    assert session["status"] == "created"


def test_session_creation_rejects_unknown_scenario(client):
    response = client.post("/sessions", json={"scenario_id": "scn_missing", "title": "bad"})
    assert response.status_code == 404
    assert response.json()["detail"] == "scenario_not_found"


def test_run_start_stop_and_sse_contract(client, session):
    started = client.post(
        "/runs",
        json={"session_id": session["id"], "prompt": "Run synthetic IAM gateway recovery."},
    )
    assert started.status_code == 201
    run = started.json()
    assert run["id"].startswith("run_")
    assert run["status"] == "running"
    assert run["hermes_thread_id"] is None
    assert run["prompt"] == "Run synthetic IAM gateway recovery."

    events = client.get(f"/runs/{run['id']}/events")
    assert events.status_code == 200
    assert "text/event-stream" in events.headers["content-type"]
    assert "event: run.started" in events.text
    assert "synthetic-dev" in events.text

    custom_event = client.post(
        f"/runs/{run['id']}/events",
        json={"event_type": "hermes.subagent.customer_signal", "payload": {"synthetic": True}},
    )
    assert custom_event.status_code == 201
    assert custom_event.json()["event_type"] == "hermes.subagent.customer_signal"

    stopped = client.post(f"/runs/{run['id']}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopped"


def test_artifact_upload_registers_storage_and_evidence(client, session):
    response = client.post(
        f"/sessions/{session['id']}/artifacts",
        data={"label": "synthetic complaint sample"},
        files={"file": ("complaints.csv", b"timestamp,message\n09:51,cannot login\n", "text/csv")},
    )
    assert response.status_code == 201
    artifact = response.json()
    assert artifact["id"].startswith("art_")
    assert artifact["filename"] == "complaints.csv"
    assert artifact["content_type"] == "text/csv"
    assert artifact["size_bytes"] > 0
    assert len(artifact["sha256"]) == 64

    evidence = client.get(f"/sessions/{session['id']}/evidence")
    assert evidence.status_code == 200
    evidence_body = evidence.json()
    assert len(evidence_body) == 1
    assert evidence_body[0]["source_type"] == "artifact"
    assert evidence_body[0]["payload"]["artifact_id"] == artifact["id"]


def test_incident_command_product_contract(client):
    created = client.post("/api/incidents", json={})
    assert created.status_code == 201
    incident = created.json()
    assert incident["id"].startswith("inc_")
    assert incident["state"] == "ready_with_incident"
    assert incident["title"] == "Login authentication degradation"
    assert len(incident["subagents"]) == 5

    asked = client.post(f"/api/incidents/{incident['id']}/ask", json={"question": "Why do you suspect CHG-1048?"})
    assert asked.status_code == 200
    assert "DERA is reconnecting" in asked.json()["answer"]

    streamed = client.post(f"/api/incidents/{incident['id']}/ask/stream", json={"question": "What is happening?", "voice_mode": True})
    assert streamed.status_code == 200
    assert "text/event-stream" in streamed.headers["content-type"]
    assert "event: status" in streamed.text
    assert "event: delta" in streamed.text
    assert "event: done" in streamed.text
    assert "DERA is reconnecting" in streamed.text

    voice_status = client.get("/api/voice/status")
    assert voice_status.status_code == 200
    assert voice_status.json()["model"] == "Kokoro-82M"
    assert voice_status.json()["speed"] == 1.22
    tts_missing = client.post("/api/voice/tts", json={"text": "Short test."})
    assert tts_missing.status_code in {200, 503}

    states = []
    for _ in range(6):
        response = client.post(f"/api/incidents/{incident['id']}/investigate", json={})
        assert response.status_code == 200
        states.append(response.json()["state"])
    assert states[-1] == "approval_required"

    evidence = client.get(f"/api/incidents/{incident['id']}/evidence")
    assert evidence.status_code == 200
    assert {item["lane"] for item in evidence.json()} == {"customer", "telemetry", "change", "recovery"}

    revised = client.post(
        f"/api/incidents/{incident['id']}/dossier/revise",
        json={"field": "customer_communication", "instruction": "Make the message calmer."},
    )
    assert revised.status_code == 200
    assert revised.json()["state"] == "approval_required"
    assert "Make the message calmer" in revised.json()["dossier"]["customer_communication"]

    approved = client.post(f"/api/incidents/{incident['id']}/approval", json={"decision": "approved_local"})
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved_local"
    assert approved.json()["approval"]["local_only"] is True
    assert approved.json()["approval"]["synthetic_recovery"] is True


def test_evidence_outcomes_and_history_contract(client, session):
    evidence_response = client.post(
        f"/sessions/{session['id']}/evidence",
        json={
            "source_type": "synthetic-telemetry",
            "title": "Auth gateway latency spike",
            "payload": {"endpoint": "/api/v1/auth/gateway/validate", "latency_ms": 4200},
        },
    )
    assert evidence_response.status_code == 201
    evidence = evidence_response.json()
    assert evidence["id"].startswith("evd_")

    outcome_response = client.post(
        f"/sessions/{session['id']}/outcomes",
        json={
            "status": "awaiting_human_approval",
            "summary": "Rollback recommendation drafted; no real action executed.",
            "payload": {"action": "draft_rollback", "synthetic": True},
        },
    )
    assert outcome_response.status_code == 201
    outcome = outcome_response.json()
    assert outcome["id"].startswith("out_")

    history_response = client.get(f"/sessions/{session['id']}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["session"]["id"] == session["id"]
    assert history["evidence"][0]["id"] == evidence["id"]
    assert history["outcomes"][0]["id"] == outcome["id"]
    assert history["artifacts"] == []
