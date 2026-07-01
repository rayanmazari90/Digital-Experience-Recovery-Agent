from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.db import Database, make_database, row_to_dict, utc_now
from app.hermes_client import HermesClient
from app.orchestration_guidance import PARENT_ORCHESTRATION_GUIDANCE, ROLE_GUIDANCE, SUPERVISOR_PROMPT
from app.security import add_security_headers, audit_event, ensure_synthetic_payload, prune_expired_records, require_api_key
from app.tts import KokoroTTS
from app.schemas import (
    Artifact,
    Event,
    EventCreate,
    Evidence,
    EvidenceCreate,
    HealthResponse,
    HistoryResponse,
    Outcome,
    OutcomeCreate,
    Run,
    RunStart,
    Scenario,
    ScenarioCreate,
    Session,
    SessionCreate,
)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    db = make_database(settings)
    hermes = HermesClient(settings)
    tts = KokoroTTS(settings)
    settings.storage_root.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title=settings.app_name, version="0.1.0", dependencies=[Depends(require_api_key(settings))])
    app.state.settings = settings
    app.state.db = db
    app.state.hermes = hermes
    app.state.tts = tts
    app.state.incidents = {}

    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-DERA-API-Key", "X-DERA-Actor"],
    )

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        add_security_headers(response)
        return response

    def get_db() -> Database:
        return app.state.db

    def get_hermes() -> HermesClient:
        return app.state.hermes

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", hermes_enabled=settings.hermes_enabled, hermes_base_url=settings.hermes_base_url)

    @app.get("/api/voice/status")
    def voice_status() -> dict[str, Any]:
        available = tts.available() if settings.tts_provider == "kokoro" else False
        return {
            "provider": settings.tts_provider,
            "model": "Kokoro-82M" if settings.tts_provider == "kokoro" else settings.tts_provider,
            "available": available,
            "voice": settings.tts_kokoro_voice,
            "speed": settings.tts_kokoro_speed,
            "streaming_strategy": "sentence-chunk",
            "error": None if available else tts.last_error,
        }

    @app.post("/api/voice/tts")
    async def synthesize_voice(request: Request) -> Response:
        body = await request.json()
        text = body.get("text", "")
        if settings.tts_provider != "kokoro":
            raise HTTPException(status_code=503, detail="tts_provider_not_configured")
        try:
            result = tts.synthesize_wav(text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            tts.last_error = str(exc)
            raise HTTPException(status_code=503, detail={"code": "kokoro_unavailable", "message": str(exc)}) from exc
        return Response(content=result.audio, media_type=result.media_type, headers={"X-DERA-TTS-Engine": result.engine})

    @app.get("/orchestration/guidance")
    def orchestration_guidance() -> dict[str, Any]:
        return {
            "supervisor_prompt": SUPERVISOR_PROMPT,
            "parent_guidance": PARENT_ORCHESTRATION_GUIDANCE,
            "roles": ROLE_GUIDANCE,
        }

    @app.post("/scenarios", response_model=Scenario, status_code=201)
    def create_scenario(payload: ScenarioCreate, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        if not settings.allow_sensitive_payloads:
            ensure_synthetic_payload(payload.data, field_name="scenario.data")
        scenario_id = new_id("scn")
        created_at = utc_now()
        with db.connect() as con:
            con.execute(
                "INSERT INTO scenarios (id, name, description, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (scenario_id, payload.name, payload.description, json.dumps(payload.data), created_at),
            )
            row = con.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        audit_event(db, action="create_scenario", resource_type="scenario", resource_id=scenario_id, request=request, metadata={"synthetic_only": True})
        return row_to_dict(row)

    @app.get("/scenarios/{scenario_id}", response_model=Scenario)
    def get_scenario(scenario_id: str, db: Database = Depends(get_db)) -> dict[str, Any]:
        with db.connect() as con:
            row = con.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        scenario = row_to_dict(row)
        if scenario is None:
            raise HTTPException(status_code=404, detail="scenario_not_found")
        return scenario

    @app.post("/sessions", response_model=Session, status_code=201)
    def create_session(payload: SessionCreate, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        session_id = new_id("ses")
        created_at = utc_now()
        with db.connect() as con:
            if con.execute("SELECT 1 FROM scenarios WHERE id = ?", (payload.scenario_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="scenario_not_found")
            con.execute(
                "INSERT INTO sessions (id, scenario_id, title, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, payload.scenario_id, payload.title, "created", created_at),
            )
            row = con.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        audit_event(db, action="create_session", resource_type="session", resource_id=session_id, request=request, metadata={"scenario_id": payload.scenario_id})
        return row_to_dict(row)

    async def reconcile_hermes_run(run_id: str, session_id: str, prompt: str, context: dict[str, Any]) -> None:
        """Call Hermes after /runs has returned so the product UI never appears frozen.

        The recovery cockpit has its own synthetic event stream for the demo story.
        Hermes remains the configured agent runtime, but a slow API-server response
        must not block creation of the local run record or the visible demo flow.
        """
        try:
            result = await hermes.start_recovery_run(session_id=session_id, prompt=prompt, context=context)
            completed_at = utc_now()
            with db.connect() as con:
                con.execute("UPDATE runs SET hermes_thread_id = ? WHERE id = ?", (result.hermes_thread_id, run_id))
                con.execute(
                    "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                    (run_id, "hermes.runtime.ready", json.dumps(result.initial_event), completed_at),
                )
        except Exception as exc:  # pragma: no cover - defensive background error path
            failed_at = utc_now()
            with db.connect() as con:
                con.execute(
                    "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                    (run_id, "hermes.runtime.error", json.dumps({"message": str(exc), "synthetic": True}), failed_at),
                )

    @app.post("/runs", response_model=Run, status_code=201)
    async def start_run(payload: RunStart, request: Request, db: Database = Depends(get_db), hermes: HermesClient = Depends(get_hermes)) -> dict[str, Any]:
        run_id = new_id("run")
        started_at = utc_now()
        with db.connect() as con:
            session_row = con.execute("SELECT * FROM sessions WHERE id = ?", (payload.session_id,)).fetchone()
            if session_row is None:
                raise HTTPException(status_code=404, detail="session_not_found")
            scenario_row = con.execute("SELECT * FROM scenarios WHERE id = ?", (session_row["scenario_id"],)).fetchone()
            context = {"session": row_to_dict(session_row), "scenario": row_to_dict(scenario_row)}
            initial_event = {
                "mode": "hermes-api-pending" if settings.hermes_enabled else "synthetic-dev",
                "message": "Run record created; Hermes runtime call continues in the background." if settings.hermes_enabled else "Hermes API call skipped because DERA_HERMES_ENABLED=false.",
                "session_id": payload.session_id,
                "context_keys": sorted(context.keys()),
            }
            con.execute(
                "INSERT INTO runs (id, session_id, status, hermes_thread_id, started_at, prompt) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, payload.session_id, "running", None, started_at, payload.prompt),
            )
            con.execute("UPDATE sessions SET status = ? WHERE id = ?", ("running", payload.session_id))
            con.execute(
                "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, "run.started", json.dumps(initial_event), started_at),
            )
            row = con.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        audit_event(db, action="start_run", resource_type="run", resource_id=run_id, request=request, metadata={"session_id": payload.session_id, "hermes_enabled": settings.hermes_enabled})
        if settings.hermes_enabled:
            asyncio.create_task(reconcile_hermes_run(run_id, payload.session_id, payload.prompt, context))
        return row_to_dict(row)

    @app.post("/runs/{run_id}/stop", response_model=Run)
    def stop_run(run_id: str, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        stopped_at = utc_now()
        with db.connect() as con:
            row = con.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="run_not_found")
            con.execute("UPDATE runs SET status = ?, stopped_at = ? WHERE id = ?", ("stopped", stopped_at, run_id))
            con.execute("UPDATE sessions SET status = ? WHERE id = ?", ("stopped", row["session_id"]))
            con.execute(
                "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, "run.stopped", json.dumps({"reason": "user_requested"}), stopped_at),
            )
            updated = con.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        audit_event(db, action="stop_run", resource_type="run", resource_id=run_id, request=request, metadata={"reason": "user_requested"})
        return row_to_dict(updated)

    @app.post("/runs/{run_id}/events", response_model=Event, status_code=201)
    def append_run_event(run_id: str, payload: EventCreate, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        if not settings.allow_sensitive_payloads:
            ensure_synthetic_payload(payload.payload, field_name="event.payload")
        created_at = utc_now()
        with db.connect() as con:
            if con.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="run_not_found")
            cursor = con.execute(
                "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, payload.event_type, json.dumps(payload.payload), created_at),
            )
            row = con.execute("SELECT * FROM events WHERE id = ?", (cursor.lastrowid,)).fetchone()
        audit_event(db, action="append_event", resource_type="run", resource_id=run_id, request=request, metadata={"event_type": payload.event_type})
        return row_to_dict(row)

    @app.get("/runs/{run_id}/events")
    async def stream_events(run_id: str, db: Database = Depends(get_db)) -> StreamingResponse:
        with db.connect() as con:
            if con.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="run_not_found")

        async def event_generator():
            last_id = 0
            idle_ticks = 0
            while idle_ticks < 3:
                with db.connect() as con:
                    rows = con.execute(
                        "SELECT * FROM events WHERE run_id = ? AND id > ? ORDER BY id ASC",
                        (run_id, last_id),
                    ).fetchall()
                if rows:
                    idle_ticks = 0
                    for row in rows:
                        event = row_to_dict(row)
                        last_id = event["id"]
                        yield f"id: {event['id']}\nevent: {event['event_type']}\ndata: {json.dumps(event['payload'])}\n\n"
                else:
                    idle_ticks += 1
                    yield ": keepalive\n\n"
                    await asyncio.sleep(0.05)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/sessions/{session_id}/artifacts", response_model=Artifact, status_code=201)
    async def upload_artifact(
        session_id: str,
        request: Request,
        file: UploadFile = File(...),
        label: str = Form(default="uploaded-artifact"),
        db: Database = Depends(get_db),
    ) -> dict[str, Any]:
        artifact_id = new_id("art")
        created_at = utc_now()
        session_dir = settings.storage_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename or "artifact.bin").name
        dest = session_dir / f"{artifact_id}_{safe_name}"
        size = 0
        digest = hashlib.sha256()
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    dest.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="artifact_too_large")
                digest.update(chunk)
                out.write(chunk)
        with db.connect() as con:
            if con.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone() is None:
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=404, detail="session_not_found")
            con.execute(
                "INSERT INTO artifacts (id, session_id, filename, content_type, storage_path, size_bytes, sha256, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (artifact_id, session_id, safe_name, file.content_type or "application/octet-stream", str(dest), size, digest.hexdigest(), created_at),
            )
            con.execute(
                "INSERT INTO evidence (id, session_id, source_type, title, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (new_id("evd"), session_id, "artifact", label, json.dumps({"artifact_id": artifact_id, "filename": safe_name}), created_at),
            )
            row = con.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        audit_event(db, action="upload_artifact", resource_type="artifact", resource_id=artifact_id, request=request, metadata={"session_id": session_id, "size_bytes": size, "sha256": digest.hexdigest()})
        return row_to_dict(row)

    @app.post("/sessions/{session_id}/evidence", response_model=Evidence, status_code=201)
    def create_evidence(session_id: str, payload: EvidenceCreate, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        if not settings.allow_sensitive_payloads:
            ensure_synthetic_payload(payload.payload, field_name="evidence.payload")
        evidence_id = new_id("evd")
        created_at = utc_now()
        with db.connect() as con:
            if con.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="session_not_found")
            con.execute(
                "INSERT INTO evidence (id, session_id, source_type, title, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (evidence_id, session_id, payload.source_type, payload.title, json.dumps(payload.payload), created_at),
            )
            row = con.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        audit_event(db, action="create_evidence", resource_type="evidence", resource_id=evidence_id, request=request, metadata={"session_id": session_id, "source_type": payload.source_type})
        return row_to_dict(row)

    @app.get("/sessions/{session_id}/evidence", response_model=list[Evidence])
    def list_evidence(session_id: str, db: Database = Depends(get_db)) -> list[dict[str, Any]]:
        with db.connect() as con:
            rows = con.execute("SELECT * FROM evidence WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [row_to_dict(row) for row in rows]

    @app.post("/sessions/{session_id}/outcomes", response_model=Outcome, status_code=201)
    def create_outcome(session_id: str, payload: OutcomeCreate, request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        if not settings.allow_sensitive_payloads:
            ensure_synthetic_payload(payload.payload, field_name="outcome.payload")
        outcome_id = new_id("out")
        created_at = utc_now()
        with db.connect() as con:
            if con.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="session_not_found")
            con.execute(
                "INSERT INTO outcomes (id, session_id, status, summary, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (outcome_id, session_id, payload.status, payload.summary, json.dumps(payload.payload), created_at),
            )
            row = con.execute("SELECT * FROM outcomes WHERE id = ?", (outcome_id,)).fetchone()
        audit_event(db, action="create_outcome", resource_type="outcome", resource_id=outcome_id, request=request, metadata={"session_id": session_id, "status": payload.status})
        return row_to_dict(row)

    @app.get("/sessions/{session_id}/outcomes", response_model=list[Outcome])
    def list_outcomes(session_id: str, db: Database = Depends(get_db)) -> list[dict[str, Any]]:
        with db.connect() as con:
            rows = con.execute("SELECT * FROM outcomes WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [row_to_dict(row) for row in rows]

    @app.get("/sessions/{session_id}/history", response_model=HistoryResponse)
    def get_history(session_id: str, db: Database = Depends(get_db)) -> dict[str, Any]:
        with db.connect() as con:
            session = row_to_dict(con.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone())
            if session is None:
                raise HTTPException(status_code=404, detail="session_not_found")
            runs = [row_to_dict(row) for row in con.execute("SELECT * FROM runs WHERE session_id = ? ORDER BY started_at ASC", (session_id,)).fetchall()]
            events = [row_to_dict(row) for row in con.execute("SELECT e.* FROM events e JOIN runs r ON e.run_id = r.id WHERE r.session_id = ? ORDER BY e.id ASC", (session_id,)).fetchall()]
            artifacts = [row_to_dict(row) for row in con.execute("SELECT * FROM artifacts WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()]
            evidence = [row_to_dict(row) for row in con.execute("SELECT * FROM evidence WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()]
            outcomes = [row_to_dict(row) for row in con.execute("SELECT * FROM outcomes WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()]
        return {"session": session, "runs": runs, "events": events, "artifacts": artifacts, "evidence": evidence, "outcomes": outcomes}

    INCIDENT_STEPS = [
        "investigating.customer_signal",
        "investigating.observability",
        "investigating.change_correlation",
        "investigating.recovery_planning",
        "dossier_ready",
        "approval_required",
    ]

    def incident_event(incident: dict[str, Any], event_type: str, payload: dict[str, Any]) -> None:
        incident.setdefault("events", []).append({"id": len(incident.get("events", [])) + 1, "event_type": event_type, "payload": payload, "created_at": utc_now()})

    def base_incident() -> dict[str, Any]:
        incident_id = new_id("inc")
        now = utc_now()
        evidence = [
            {"id": "ev_customer_complaints", "lane": "customer", "title": "Complaint spike", "summary": "37% spike in MFA-code-not-arriving complaints", "details": {"masked_samples": ["I can’t receive my MFA code after entering my password.", "Login code never arrives; I need to access my account.", "Authentication text is delayed and the app times out."], "affected_journey": "Login / Authentication", "sentiment": "High frustration", "estimated_users": "18.4k potentially affected"}, "visible_after": "ready_with_incident"},
            {"id": "ev_telemetry_latency", "lane": "telemetry", "title": "Auth gateway latency", "summary": "p95 latency rose 180ms → 4200ms with 504 errors", "details": {"endpoint": "/api/v1/auth/gateway/validate", "before": "180ms", "after": "4200ms", "status_codes": "504 spike from 0.2% to 8.7%"}, "visible_after": "investigating.observability"},
            {"id": "ev_change_chg1048", "lane": "change", "title": "CHG-1048 deployment", "summary": "IAM Gateway optimization deployed 5 minutes before latency spike", "details": {"change_id": "CHG-1048", "service": "iam-gateway", "deployment_time": "09:46", "incident_start": "09:51", "correlation_distance": "5 minutes"}, "visible_after": "investigating.change_correlation"},
            {"id": "ev_recovery_plan", "lane": "recovery", "title": "Recovery plan", "summary": "Rollback stable-v4.12.2, validate MFA, publish customer-safe message", "details": {"rollback_target": "stable-v4.12.2", "checks": ["MFA code delivery latency < 500ms", "504 rate returns below 0.5%", "Login completion returns to baseline"], "residual_risk": "Monitor delayed SMS backlog for 20 minutes."}, "visible_after": "investigating.recovery_planning"},
        ]
        subagents = [
            {"id": "supervisor", "name": "Digital Experience Supervisor", "status": "running", "task": "Coordinate incident investigation and safety gate", "tool": "DERA incident orchestration", "finding": "Incident opened: login authentication degradation", "confidence": 0.86, "timestamp": "09:51", "evidence_id": "ev_customer_complaints"},
            {"id": "customer_signal", "name": "Customer Signal Agent", "status": "queued", "task": "Cluster customer complaints across app/chat/contact-center samples", "tool": "complaint_cluster.sample", "finding": "Waiting for investigation", "confidence": None, "timestamp": "09:51", "evidence_id": "ev_customer_complaints"},
            {"id": "observability", "name": "Observability Agent", "status": "queued", "task": "Check auth gateway latency and 504 errors", "tool": "observability.query.sample", "finding": "Waiting for customer signal", "confidence": None, "timestamp": "09:52", "evidence_id": "ev_telemetry_latency"},
            {"id": "change_correlation", "name": "Change Correlation Agent", "status": "queued", "task": "Compare failure window with recent changes", "tool": "change_record.lookup.sample", "finding": "Waiting for telemetry", "confidence": None, "timestamp": "09:53", "evidence_id": "ev_change_chg1048"},
            {"id": "recovery", "name": "Recovery & Communication Agent", "status": "queued", "task": "Draft rollback recommendation and customer communication", "tool": "recovery_dossier.draft", "finding": "Waiting for root-cause hypothesis", "confidence": None, "timestamp": "09:54", "evidence_id": "ev_recovery_plan"},
        ]
        dossier = {
            "executive_summary": "Login authentication is degraded because MFA code validation is timing out for a subset of users.",
            "customer_impact": "Customers in the Login / Authentication journey may not receive MFA codes. Card purchases, ATM access, and already-authenticated mobile sessions remain operational in this sample incident.",
            "evidence_chain": ["Complaint spike", "Auth gateway latency and 504 errors", "CHG-1048 deployed five minutes before the spike", "Rollback target identified"],
            "root_cause_hypothesis": "CHG-1048 likely introduced latency in the IAM Gateway validation path.",
            "confidence": 0.92,
            "recommended_recovery": "Rollback iam-gateway to stable-v4.12.2, validate MFA latency and login completion, then keep the customer banner active until metrics normalize.",
            "customer_communication": "We are investigating delays with login authentication codes. Card purchases and ATM access remain operational. Please retry login shortly; no account-specific action is required.",
            "operational_remainder": "Card purchases, ATM withdrawals, branch systems, and authenticated sessions remain operational in this sample incident.",
            "risks": "Rollback may temporarily reduce IAM Gateway optimization benefits; monitor SMS delivery backlog and login completion after rollback.",
            "status": "drafting",
            "revision_count": 0,
        }
        incident = {"id": incident_id, "state": "ready_with_incident", "severity": "SEV-2", "title": "Login authentication degradation", "created_at": now, "updated_at": now, "impact": {"complaint_spike": "37%", "affected_journey": "Login / Authentication", "estimated_users": "18.4k", "what_still_works": "Cards, ATM, branch systems, and authenticated sessions"}, "evidence": evidence, "subagents": subagents, "dossier": dossier, "chat": [{"role": "hermes", "content": "Incident intake is ready. Ask me what is happening or start the investigation.", "created_at": now}], "events": []}
        incident_event(incident, "incident.created", {"state": incident["state"], "title": incident["title"]})
        return incident

    def get_incident_or_404(incident_id: str) -> dict[str, Any]:
        incident = app.state.incidents.get(incident_id)
        if incident is None:
            raise HTTPException(status_code=404, detail="incident_not_found")
        return incident

    def visible_evidence(incident: dict[str, Any]) -> list[dict[str, Any]]:
        order = ["ready_with_incident", *INCIDENT_STEPS, "approved_local", "rejected_local"]
        current_idx = order.index(incident["state"]) if incident["state"] in order else 0
        return [ev for ev in incident["evidence"] if order.index(ev["visible_after"]) <= current_idx]

    def advance_incident(incident: dict[str, Any], target_state: str | None = None) -> None:
        if target_state is None:
            current = incident["state"]
            target_state = INCIDENT_STEPS[0] if current == "ready_with_incident" else INCIDENT_STEPS[min(INCIDENT_STEPS.index(current) + 1, len(INCIDENT_STEPS) - 1)]
        incident["state"] = target_state
        incident["updated_at"] = utc_now()
        updates = {
            "investigating.customer_signal": ("customer_signal", "complete", "37% spike in MFA-code-not-arriving complaints", 0.91),
            "investigating.observability": ("observability", "complete", "Latency rose 180ms → 4200ms; 504 errors increased", 0.94),
            "investigating.change_correlation": ("change_correlation", "complete", "CHG-1048 deployed 5 minutes before latency spike", 0.98),
            "investigating.recovery_planning": ("recovery", "complete", "Rollback and customer-safe message drafted", 0.9),
        }
        if target_state in updates:
            agent_id, status, finding, confidence = updates[target_state]
            for agent in incident["subagents"]:
                if agent["id"] == agent_id:
                    agent.update({"status": status, "finding": finding, "confidence": confidence, "timestamp": utc_now()[11:16]})
                elif agent["status"] == "queued" and agent["id"] != "supervisor":
                    agent["status"] = "running" if agent["id"] in ["observability", "change_correlation", "recovery"] else agent["status"]
        if target_state in {"dossier_ready", "approval_required"}:
            incident["dossier"]["status"] = "ready"
            for agent in incident["subagents"]:
                if agent["id"] == "supervisor":
                    agent.update({"status": "complete", "finding": "Evidence chain and human gate are ready", "confidence": 0.93, "timestamp": utc_now()[11:16]})
        incident_event(incident, "incident.state_changed", {"state": target_state})

    def unavailable_hermes_answer(question: str, incident: dict[str, Any]) -> str:
        return (
            "DERA is reconnecting to the live reasoning runtime right now, so I won’t invent an answer. "
            "The incident workspace is loaded locally; live analysis needs the DERA runtime online."
        )

    def hermes_incident_context(incident: dict[str, Any], *, voice_mode: bool = False, dashboard_context: dict[str, Any] | None = None) -> dict[str, Any]:
        answer_style = (
            "Voice conversation mode: you are DERA, an expert digital-experience recovery lead speaking to an operator. Sound warm, human, energetic, and focused; confident but never theatrical. Use natural conversational phrasing, contractions, and short pauses. Keep it to 1-2 short sentences under 38 words. Avoid markdown, long lists, robotic labels, raw IDs, or the safety-boundary label unless the operator explicitly asks about safety boundaries."
            if voice_mode
            else "Default chat mode: be concise by default. Use 2-4 short bullets or a short paragraph; give long explanations only when the operator asks for detail."
        )
        return {
            "product_role": "You are DERA, the live Digital Experience Recovery Agent inside the Apex Global Bank cockpit.",
            "instruction": "Answer as DERA: an expert in digital experience recovery, incident diagnosis, customer-impact reasoning, and safe recovery coordination. Reason over the provided sample incident state and the live dashboard context. Know which workspace tab the operator is currently viewing, what evidence is visible, which agent is active, and what the next CTA is. If the question belongs in a different workspace, say where you moved/focused the operator and answer using that placement. Do not claim real bank-system access. Keep approvals clearly local and supervised.",
            "answer_style": answer_style,
            "state": incident["state"],
            "incident": incident["title"],
            "severity": incident["severity"],
            "impact": incident["impact"],
            "visible_evidence": visible_evidence(incident),
            "dashboard_context": dashboard_context or {},
            "subagents": incident["subagents"],
            "dossier": incident["dossier"],
        }

    @app.post("/api/incidents", status_code=201)
    def create_incident(request: Request) -> dict[str, Any]:
        incident = base_incident()
        app.state.incidents[incident["id"]] = incident
        audit_event(db, action="create_incident", resource_type="incident", resource_id=incident["id"], request=request, metadata={"safe_demo": True})
        return incident

    @app.post("/api/incidents/{incident_id}/investigate")
    async def investigate_incident(incident_id: str, request: Request, hermes: HermesClient = Depends(get_hermes)) -> dict[str, Any]:
        incident = get_incident_or_404(incident_id)
        advance_incident(incident)
        if settings.hermes_enabled and incident["state"].startswith("investigating."):
            active_agent_by_state = {
                "investigating.customer_signal": "customer_signal",
                "investigating.observability": "observability",
                "investigating.change_correlation": "change_correlation",
                "investigating.recovery_planning": "recovery",
            }
            agent_id = active_agent_by_state.get(incident["state"])
            agent = next((item for item in incident["subagents"] if item["id"] == agent_id), None)
            if agent:
                try:
                    result = await hermes.hermes_delegate_task(
                        task=(
                            f"As {agent['name']}, perform this specialist task for the incident cockpit: {agent['task']}. "
                            "Return one concise operator-facing finding grounded only in the provided incident context."
                        ),
                        context=hermes_incident_context(incident),
                    )
                    if result.get("content"):
                        agent["finding"] = result["content"][:900]
                        agent["tool"] = "live DERA specialist reasoning"
                        agent["status"] = "complete"
                        incident_event(incident, "hermes.subagent.live", {"agent": agent_id, "mode": result.get("mode", "hermes-api")})
                except Exception as exc:
                    if agent.get("status") == "complete":
                        agent["tool"] = f"{agent['tool']} · live DERA unavailable"
                        agent["finding"] = f"{agent['finding']} Live specialist reasoning was unavailable, so this step is using the local sample evidence."
                    else:
                        agent["status"] = "blocked"
                        agent["finding"] = "Live DERA specialist reasoning is unavailable; no invented specialist finding was substituted."
                    incident_event(incident, "hermes.subagent.unavailable", {"agent": agent_id, "message": str(exc)})
        audit_event(db, action="investigate_incident", resource_type="incident", resource_id=incident_id, request=request, metadata={"state": incident["state"], "hermes_enabled": settings.hermes_enabled})
        return incident

    @app.post("/api/incidents/{incident_id}/ask/stream")
    async def ask_incident_stream(incident_id: str, request: Request, hermes: HermesClient = Depends(get_hermes)) -> StreamingResponse:
        incident = get_incident_or_404(incident_id)
        body = await request.json()
        question = body.get("question", "What is happening?")
        voice_mode = bool(body.get("voice_mode"))
        dashboard_context = body.get("dashboard_context") if isinstance(body.get("dashboard_context"), dict) else {}

        async def event_generator():
            answer_parts: list[str] = []
            adapter_mode = "hermes-api" if settings.hermes_enabled else "hermes-disabled"
            yield f"event: status\ndata: {json.dumps({'adapter_mode': adapter_mode, 'message': 'DERA is writing'})}\n\n"
            if settings.hermes_enabled:
                try:
                    async for chunk in hermes.hermes_chat_stream(prompt=question, context=hermes_incident_context(incident, voice_mode=voice_mode, dashboard_context=dashboard_context)):
                        answer_parts.append(chunk)
                        yield f"event: delta\ndata: {json.dumps({'delta': chunk})}\n\n"
                except Exception as exc:
                    adapter_mode = "hermes-unavailable"
                    fallback = unavailable_hermes_answer(question, incident)
                    answer_parts = [fallback]
                    incident_event(incident, "hermes.chat.stream_unavailable", {"message": str(exc)})
                    yield f"event: delta\ndata: {json.dumps({'delta': fallback})}\n\n"
            else:
                fallback = unavailable_hermes_answer(question, incident)
                answer_parts = [fallback]
                yield f"event: delta\ndata: {json.dumps({'delta': fallback})}\n\n"
            answer = "".join(answer_parts)
            now = utc_now()
            incident["chat"].extend([
                {"role": "operator", "content": question, "created_at": now},
                {"role": "hermes", "content": answer, "created_at": utc_now(), "adapter_mode": adapter_mode},
            ])
            incident_event(incident, "hermes.chat.stream", {"question": question, "adapter_mode": adapter_mode})
            yield f"event: done\ndata: {json.dumps({'adapter_mode': adapter_mode})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/api/incidents/{incident_id}/ask")
    async def ask_incident(incident_id: str, request: Request, hermes: HermesClient = Depends(get_hermes)) -> dict[str, Any]:
        incident = get_incident_or_404(incident_id)
        body = await request.json()
        question = body.get("question", "What is happening?")
        voice_mode = bool(body.get("voice_mode"))
        dashboard_context = body.get("dashboard_context") if isinstance(body.get("dashboard_context"), dict) else {}
        if settings.hermes_enabled:
            answer = ""
            adapter_mode = "hermes-api"
            try:
                result = await hermes.hermes_chat(prompt=question, context=hermes_incident_context(incident, voice_mode=voice_mode, dashboard_context=dashboard_context))
                answer = result.get("content", "")
                adapter_mode = result.get("mode", "hermes-api")
            except Exception as exc:
                adapter_mode = "hermes-unavailable"
                answer = unavailable_hermes_answer(question, incident)
                incident_event(incident, "hermes.chat.unavailable", {"message": str(exc)})
        else:
            answer = unavailable_hermes_answer(question, incident)
            adapter_mode = "hermes-disabled"
        message = {"role": "operator", "content": question, "created_at": utc_now()}
        reply = {"role": "hermes", "content": answer, "created_at": utc_now(), "adapter_mode": adapter_mode}
        incident["chat"].extend([message, reply])
        incident_event(incident, "hermes.chat", {"question": question, "adapter_mode": adapter_mode})
        return {"answer": answer, "chat": incident["chat"], "state": incident["state"], "adapter_mode": adapter_mode}

    @app.get("/api/incidents/{incident_id}/state")
    def incident_state(incident_id: str) -> dict[str, Any]:
        return get_incident_or_404(incident_id)

    @app.get("/api/incidents/{incident_id}/evidence")
    def incident_evidence(incident_id: str) -> list[dict[str, Any]]:
        return visible_evidence(get_incident_or_404(incident_id))

    @app.get("/api/incidents/{incident_id}/subagents")
    def incident_subagents(incident_id: str) -> list[dict[str, Any]]:
        return get_incident_or_404(incident_id)["subagents"]

    @app.post("/api/incidents/{incident_id}/dossier/revise")
    async def revise_dossier(incident_id: str, request: Request, hermes: HermesClient = Depends(get_hermes)) -> dict[str, Any]:
        incident = get_incident_or_404(incident_id)
        body = await request.json()
        field = body.get("field", "customer_communication")
        instruction = body.get("instruction", "Make it clearer for customers.")
        if field not in incident["dossier"]:
            raise HTTPException(status_code=400, detail="unknown_dossier_field")
        incident["state"] = "revising_dossier"
        original = incident["dossier"][field]
        original_text = json.dumps(original) if isinstance(original, (list, dict)) else str(original)
        revised = original
        adapter_mode = "hermes-disabled"
        if settings.hermes_enabled:
            try:
                result = await hermes.hermes_chat(
                    prompt=(
                        f"Revise only the `{field}` field in the recovery dossier.\n"
                        "Use the current dashboard field text as the source of truth and keep all facts consistent with the full dossier context. "
                        "Do not add new facts, external actions, or approval claims. Return only the revised field text.\n\n"
                        f"Current `{field}` text:\n{original_text}\n\n"
                        f"Operator instruction:\n{instruction}"
                    ),
                    context=hermes_incident_context(incident),
                )
                revised = result.get("content") or original
                adapter_mode = result.get("mode", "hermes-api")
            except Exception as exc:
                revised = original
                adapter_mode = "hermes-unavailable"
                incident_event(incident, "dossier.revision.unavailable", {"field": field, "message": str(exc)})
        else:
            revised = f"{original} DERA live reasoning is disabled, so no live rewrite was performed. Operator request was: {instruction}"
        incident["dossier"][field] = revised
        incident["dossier"]["revision_count"] += 1
        incident["dossier"]["status"] = "revised" if adapter_mode == "hermes-api" else "revision_needs_hermes"
        incident["state"] = "approval_required"
        incident_event(incident, "dossier.revised", {"field": field, "instruction": instruction, "adapter_mode": adapter_mode})
        return {
            "dossier": incident["dossier"],
            "state": incident["state"],
            "adapter_mode": adapter_mode,
            "revised_field": field,
            "original_text": original_text,
            "revised_text": str(incident["dossier"][field]),
        }

    @app.post("/api/incidents/{incident_id}/approval")
    async def approve_incident(incident_id: str, request: Request) -> dict[str, Any]:
        incident = get_incident_or_404(incident_id)
        body = await request.json()
        decision = body.get("decision")
        if decision not in {"approved_local", "rejected_local"}:
            raise HTTPException(status_code=400, detail="invalid_decision")
        incident["state"] = decision
        incident["approval"] = {"decision": decision, "local_only": True, "synthetic_recovery": True, "created_at": utc_now()}
        incident_event(incident, "approval.recorded", incident["approval"])
        audit_event(db, action="incident_approval", resource_type="incident", resource_id=incident_id, request=request, metadata=incident["approval"])
        return incident

    @app.get("/api/incidents/{incident_id}/events")
    async def stream_incident_events(incident_id: str) -> StreamingResponse:
        incident = get_incident_or_404(incident_id)

        async def event_generator():
            last_id = 0
            idle_ticks = 0
            while idle_ticks < 60:
                events = [event for event in incident.get("events", []) if event["id"] > last_id]
                if events:
                    idle_ticks = 0
                    for event in events:
                        last_id = event["id"]
                        yield f"id: {event['id']}\nevent: {event['event_type']}\ndata: {json.dumps(event['payload'])}\n\n"
                else:
                    idle_ticks += 1
                    yield ": keepalive\n\n"
                    await asyncio.sleep(0.25)
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/audit/logs")
    def list_audit_logs(limit: int = 100, db: Database = Depends(get_db)) -> dict[str, Any]:
        capped_limit = min(max(limit, 1), 500)
        with db.connect() as con:
            rows = con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (capped_limit,)).fetchall()
        return {"audit_logs": [row_to_dict(row) for row in rows]}

    @app.post("/maintenance/retention/prune")
    def prune_retention(request: Request, db: Database = Depends(get_db)) -> dict[str, Any]:
        counts = prune_expired_records(db, settings.retention_days)
        audit_event(db, action="retention_prune", resource_type="maintenance", resource_id=None, request=request, metadata={"retention_days": settings.retention_days, "counts": counts})
        return {"retention_days": settings.retention_days, "deleted": counts}

    return app


app = create_app()
