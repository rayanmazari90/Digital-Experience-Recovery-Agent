from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Header, HTTPException, Request

from app.config import Settings
from app.db import Database, utc_now

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
ACCOUNT_RE = re.compile(r"\b(?:account|acct|iban|card|pan|ssn|dni|passport)[:#\s-]*[A-Z0-9-]{4,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
SECRET_KEY_RE = re.compile(r"\b(?:api[_-]?key|secret|token|password|bearer)\b", re.IGNORECASE)

SENSITIVE_PATTERNS = {
    "email": EMAIL_RE,
    "payment_card_like": CARD_RE,
    "account_identifier_like": ACCOUNT_RE,
    "phone_like": PHONE_RE,
    "secret_key_label": SECRET_KEY_RE,
}


@dataclass(frozen=True)
class PrivacyScanResult:
    allowed: bool
    findings: list[str]


def scan_for_sensitive_values(value: Any) -> PrivacyScanResult:
    """Detect raw PII/secret-like values before they enter the demo database.

    This is intentionally conservative for the synthetic shell. It is not a full
    DLP system; production ingestion still requires approved masking/tokenization.
    """
    text = json.dumps(value, ensure_ascii=False, default=str)
    findings = [name for name, pattern in SENSITIVE_PATTERNS.items() if pattern.search(text)]
    return PrivacyScanResult(allowed=not findings, findings=findings)


def ensure_synthetic_payload(payload: dict[str, Any], *, field_name: str = "payload") -> None:
    scan = scan_for_sensitive_values(payload)
    if not scan.allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "sensitive_data_rejected",
                "field": field_name,
                "findings": scan.findings,
                "message": "Synthetic shell rejects raw PII/secret-like values. Mask/tokenize before ingestion.",
            },
        )


def require_api_key(settings: Settings):
    async def dependency(
        authorization: str | None = Header(default=None),
        x_dera_api_key: str | None = Header(default=None),
    ) -> None:
        if not settings.api_auth_enabled:
            return
        supplied = x_dera_api_key
        if authorization and authorization.lower().startswith("bearer "):
            supplied = authorization.split(" ", 1)[1]
        if not supplied or supplied != settings.api_key:
            raise HTTPException(status_code=401, detail="api_auth_required")

    return dependency


def add_security_headers(response) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=(), payment=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self' http://127.0.0.1:* http://localhost:*; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "media-src 'self'; "
        "base-uri 'none'; frame-ancestors 'none'"
    )


def audit_event(db: Database, *, action: str, resource_type: str, resource_id: str | None, request: Request | None = None, metadata: dict[str, Any] | None = None) -> None:
    actor = "local-dev"
    if request is not None:
        actor = request.headers.get("X-DERA-Actor", "local-dev")[:120]
    with db.connect() as con:
        con.execute(
            "INSERT INTO audit_logs (action, resource_type, resource_id, actor, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (action, resource_type, resource_id, actor, json.dumps(metadata or {}), utc_now()),
        )


def prune_expired_records(db: Database, retention_days: int) -> dict[str, int]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    counts: dict[str, int] = {}
    with db.connect() as con:
        old_sessions = [row["id"] for row in con.execute("SELECT id FROM sessions WHERE created_at < ?", (cutoff,)).fetchall()]
        old_runs = [row["id"] for row in con.execute("SELECT id FROM runs WHERE session_id IN (SELECT id FROM sessions WHERE created_at < ?)", (cutoff,)).fetchall()]
        for table, column, values in [
            ("events", "run_id", old_runs),
            ("artifacts", "session_id", old_sessions),
            ("evidence", "session_id", old_sessions),
            ("outcomes", "session_id", old_sessions),
            ("runs", "session_id", old_sessions),
        ]:
            counts[table] = 0
            for value in values:
                cur = con.execute(f"DELETE FROM {table} WHERE {column} = ?", (value,))
                counts[table] += cur.rowcount
        counts["sessions"] = con.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff,)).rowcount
        counts["scenarios"] = con.execute("DELETE FROM scenarios WHERE created_at < ? AND id NOT IN (SELECT scenario_id FROM sessions)", (cutoff,)).rowcount
        counts["audit_logs"] = con.execute("DELETE FROM audit_logs WHERE created_at < ?", (cutoff,)).rowcount
    return counts
