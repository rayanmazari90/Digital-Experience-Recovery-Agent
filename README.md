# Digital Experience Recovery Agent — Backend Shell

This backend shell stores synthetic product/customer demo records for the Digital Experience Recovery Agent recovery cockpit. Hermes remains the only agent runtime and execution plane; this app does not replace Hermes with another agent SDK.

The app database stores product records only:

- scenarios
- sessions
- runs
- SSE-forwarded run events
- uploaded artifact registrations
- evidence records
- recovery outcomes

Hermes state stays profile-scoped inside the `digital-recovery` Hermes profile.

## Safety Scope

This shell is dev-only and synthetic-data-only.

Do not connect it to:

- real bank systems,
- real customer records,
- real observability platforms,
- real messaging systems,
- real call-center systems.

All localhost development assumes mocked or synthetic data unless a future build gate explicitly permits real integrations.

## Local Development

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Start the backend:

```bash
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Health check:

```bash
curl http://127.0.0.1:8080/health
```

## Frontend Cockpit Shell

The premium cockpit shell lives in:

```text
frontend/
  index.html
  styles.css
  app.js
```

Run it locally with any static file server, for example:

```bash
python3 -m http.server 5173 --directory frontend
```

Open:

```text
http://127.0.0.1:5173
```

The cockpit talks to the backend shell at `http://127.0.0.1:8080` by default. The Backend field in the top bar can be changed for local testing.

## Collaborating without Hermes Installed

Most contributors do **not** need Rayane's Hermes profile, credentials, memory, or local agent setup. Keep `DERA_HERMES_ENABLED=false` in `.env` for demo mode, then work normally on the frontend, CSS, docs, tests, and backend shell.

Use live Hermes mode only when testing the real local agent integration:

```bash
DERA_HERMES_ENABLED=true
DERA_HERMES_BASE_URL=http://127.0.0.1:8000
DERA_HERMES_MODEL=digital-recovery-agent
```

Never commit `.env`, Hermes profiles, API keys, session logs, local databases, or workspace storage. See `CONTRIBUTING.md` for the Git workflow and safety boundaries.

Cockpit capabilities:

- morphic central recovery core,
- customer journey timeline,
- evidence/source panel,
- live run status stream via backend SSE,
- subagent activity panel,
- operator approvals panel,
- accessibility toggles,
- presentation mode.

The morphic core is not decorative: each animated state is driven by a documented runtime event name such as `run.started`, `hermes.subagent.customer_signal`, `hermes.tool.observability`, `hermes.subagent.change_correlation`, `hermes.subagent.recovery`, `approval.required`, or `run.stopped`. Critical state changes are also exposed as text in the Text-only equivalent panel and accessibility summary.

The UI uses synthetic/dev-only records and local backend calls. It does not connect to real bank systems, real customer records, real observability platforms, messaging systems, call systems, or telephony.

## Voice-First Recovery Mode and Live Demo Features

The frontend shell includes a clear mode switch between:

- `Text`,
- `Voice`,
- `Operator view`.

MVP voice UX now lives primarily inside the Hermes chat panel: pressing `Talk` opens a voice bubble, microphone input asks Hermes, streamed text continues to render live, sentence chunks are spoken as they arrive, `Mute` silences audio without stopping text, and `Stop conversation` returns the operator to normal text input.

Target local TTS engine: `Kokoro-82M`. It is small, fast, open/free to run locally, and appropriate for the MVP. The current browser shell keeps a browser `speechSynthesis` bridge for zero-install demos; the next backend voice pass should add a local Kokoro streaming TTS endpoint so audio chunks are generated server-side from the same Hermes SSE deltas.

Voice support is deliberately split into documented Hermes capabilities and a labeled app-side bridge:

- Hermes-documented voice capabilities used as the product boundary:
  - gateway voice-message transcription,
  - `/voice on`,
  - `/voice tts`,
  - Hermes TTS tool/provider configuration.
- Custom app-side bridge in the browser shell:
  - `SpeechRecognition` / `webkitSpeechRecognition` for local browser voice input when available,
  - `speechSynthesis` for local spoken response and narrated timeline playback.

The browser bridge is labeled in the UI as `Custom app-side bridge`. It is not direct Hermes telephony, does not call phone systems, and does not send customer-facing messages.

Premium demo features now include:

- voice-first recovery command capture for local demo commands such as “start demo”, “narrate timeline”, and “speak summary”,
- spoken response support through browser speech synthesis as an app-side bridge,
- live subagent watch visualization with role progress meters and a watch graph,
- presentation mode cues for Detect → Correlate → Recover,
- narrated recovery timeline playback with synchronized timeline and presentation cues.

## Hermes-Facing Orchestration Guidance

The recovery roles are defined as Hermes `delegate_task` leaf subagents in `app/orchestration_guidance.py` and documented in `docs/orchestration-guidance.md`.

Implemented role contracts:

- `fault_diagnostician`,
- `journey_analyst`,
- `recovery_strategist`,
- `evidence_synthesizer`.

Each role declares:

- context it receives,
- narrow allowed toolsets,
- expected JSON output schema,
- parent delegation triggers,
- operator approval triggers.

The backend exposes the active guidance at:

```text
GET /orchestration/guidance
```

The parent supervisor prompt uses Hermes `delegate_task` patterns, keeps children as bounded `leaf` roles, avoids child memory writes, and requires final synthesis to be explainable and replayable from evidence IDs and approval records.

## Security Hardening

Security hardening docs:

- `docs/security-hardening-review.md`
- `docs/security-test-plan.md`
- `docs/deployment-guide.md`
- `docs/monitoring-runbook.md`

Hardening controls now include optional backend API-key auth, explicit CORS, security headers, conservative sensitive-payload rejection, upload size limits, local audit logs, retention pruning, non-root/read-only Docker settings, and explicit unsupported-area flags.

## Docker Local Deployment

Build and run:

```bash
docker compose up --build
```

The API will be available at:

```text
http://127.0.0.1:8080
```

The container stores SQLite and uploaded artifacts in the `dera-data` Docker volume.

## Hermes API Server

Hermes must run under the dedicated `digital-recovery` profile.

Start Hermes API server from a separate terminal:

```bash
hermes --profile digital-recovery gateway run
```

The profile `.env` should contain API server settings similar to:

```bash
API_SERVER_ENABLED=true
API_SERVER_HOST=127.0.0.1
API_SERVER_PORT=8000
API_SERVER_MODEL_NAME=digital-recovery-agent
API_SERVER_KEY=<strong-local-bearer-key>
```

The backend talks to Hermes through these app settings:

```bash
DERA_HERMES_BASE_URL=http://127.0.0.1:8000
DERA_HERMES_API_KEY=<same bearer key as API_SERVER_KEY>
DERA_HERMES_MODEL=digital-recovery-agent
DERA_HERMES_ENABLED=true
```

For docker compose on macOS, the app points at the host Hermes API server with:

```bash
DERA_HERMES_BASE_URL=http://host.docker.internal:8000
```

By default, `.env.example` sets `DERA_HERMES_ENABLED=false`. In that mode, run creation records a synthetic dev event and does not call Hermes. This keeps tests and local shell work safe while preserving the Hermes boundary.

## API Contract Summary

### Health

`GET /health`

Returns service status and Hermes connection mode.

### Scenario Creation

`POST /scenarios`

```json
{
  "name": "Synthetic IAM Gateway Failure",
  "description": "Synthetic authentication outage scenario",
  "data": {
    "journey": "Login/Authentication",
    "synthetic": true
  }
}
```

### Session Creation

`POST /sessions`

```json
{
  "scenario_id": "scn_...",
  "title": "Morning incident simulation"
}
```

### Run Start

`POST /runs`

```json
{
  "session_id": "ses_...",
  "prompt": "Run the synthetic IAM gateway recovery scenario."
}
```

Run start creates app-level run records and, when enabled, calls Hermes through its API server. Hermes profile state remains inside the `digital-recovery` profile.

### Run Stop

`POST /runs/{run_id}/stop`

Marks the app-level run as stopped and appends a `run.stopped` event.

### SSE Event Forwarding

`GET /runs/{run_id}/events`

Returns `text/event-stream` data. Current shell forwards stored app events. Future Hermes streaming can be attached at this boundary without changing the app database ownership model.

### Uploaded Artifact Registration

`POST /sessions/{session_id}/artifacts`

Multipart form:

- `file`: uploaded artifact
- `label`: optional evidence label

The file is copied to workspace storage and registered in the app database. Registration also creates an evidence record.

### Evidence Retrieval

`POST /sessions/{session_id}/evidence`

Creates a synthetic/dev evidence record.

`GET /sessions/{session_id}/evidence`

Returns session evidence records.

### Recovery Outcomes

`POST /sessions/{session_id}/outcomes`

Creates a recovery outcome record.

`GET /sessions/{session_id}/outcomes`

Returns recovery outcomes.

### History

`GET /sessions/{session_id}/history`

Returns the session, runs, events, artifacts, evidence, and outcomes.

## Tests

Run contract tests:

```bash
pytest
```

The tests use temporary SQLite and temporary workspace storage. They do not call real Hermes or real external systems.
