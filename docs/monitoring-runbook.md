# Monitoring and Runbook

This runbook covers the synthetic/local Digital Experience Recovery Agent shell.

## Monitoring scope

Implemented local checks:

- `GET /health` for app liveness/config status.
- `GET /audit/logs` for local audit records.
- SSE stream `GET /runs/{run_id}/events` for run event playback.
- Frontend status console for runtime events.

Unsupported monitoring:

- Real Datadog/Dynatrace/ServiceNow integration.
- Real customer-impact telemetry.
- Production alerting.
- Remote dashboard monitoring.

## Health check

```bash
curl http://127.0.0.1:8080/health
```

Expected dev response includes:

```json
{"status":"ok","hermes_enabled":false}
```

If `hermes_enabled` is true, confirm the Hermes API server is running under the `digital-recovery` profile and protected by its configured bearer key.

## Audit review

```bash
curl http://127.0.0.1:8080/audit/logs
```

Review after demos for:

- unexpected actor values,
- evidence/outcome creations,
- local approval records,
- retention prune actions,
- any sensitive-data rejection events surfaced in API responses.

## Retention runbook

Manual retention prune:

```bash
curl -X POST http://127.0.0.1:8080/maintenance/retention/prune
```

Then verify:

```bash
curl http://127.0.0.1:8080/audit/logs
```

## Incident runbook

### Backend unavailable

1. Check process:
   ```bash
   pgrep -af 'uvicorn app.main:app'
   ```
2. Restart backend:
   ```bash
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
   ```
3. Re-run health check.

### Frontend unavailable

1. Check static server:
   ```bash
   pgrep -af 'http.server 5173'
   ```
2. Restart frontend:
   ```bash
   python3 -m http.server 5173 --bind 127.0.0.1 --directory frontend
   ```
3. Open `http://127.0.0.1:5173`.

### Hermes API unavailable

1. Confirm whether app is in synthetic mode:
   ```bash
   grep DERA_HERMES_ENABLED .env
   ```
2. If Hermes is enabled, start Hermes gateway/API server under the dedicated profile per README.
3. Never fall back to another LLM runtime.

### Sensitive payload rejected

1. Treat rejection as expected behavior.
2. Mask/tokenize the input.
3. Do not set `DERA_ALLOW_SENSITIVE_PAYLOADS=true` unless a privacy policy and approval exist.

### Approval required

1. Verify the proposed action is local-only or external.
2. Do not execute rollback, notification, traffic shift, deployment, or customer messaging from this shell.
3. Record local approval/rejection only through the cockpit approval panel.

## Escalation criteria

Stop the demo and escalate if:

- real customer data appears,
- real credentials appear,
- frontend/backend is exposed outside localhost unexpectedly,
- Hermes is configured with `approvals.mode=off`,
- a child/subagent receives broad toolsets or memory/messaging access,
- any external side-effect integration is connected without approval.

## Evidence to preserve

For demo debugging, preserve only synthetic artifacts:

- test output,
- console errors,
- audit log excerpts,
- synthetic run IDs,
- synthetic event payloads.

Do not preserve raw customer transcripts, recordings, account identifiers, production logs, or secrets.
