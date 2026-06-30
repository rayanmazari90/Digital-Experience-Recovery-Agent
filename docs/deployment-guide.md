# Deployment Guide

This guide covers safe localhost/demo deployment only. Production deployment is not approved by the current corpus.

## Deployment status

- Supported: localhost synthetic demo.
- Supported: Docker localhost synthetic demo.
- Unsupported: remote dashboard/API exposure without explicit security design.
- Unsupported: real bank/customer/observability/messaging integrations.

## Prerequisites

1. Use the dedicated Hermes profile:

```bash
hermes --profile digital-recovery doctor
```

2. Confirm Hermes security settings where applicable:

```bash
hermes --profile digital-recovery config set security.redact_secrets true
hermes --profile digital-recovery config set privacy.redact_pii true
hermes --profile digital-recovery config set approvals.mode manual
```

3. Create local app env:

```bash
cp .env.example .env
```

4. For any non-trivial demo, replace placeholder API keys in `.env` and keep `.env` uncommitted.

## Local backend and frontend

Backend:

```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Frontend:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Open:

```text
http://127.0.0.1:5173
```

## Docker localhost deployment

```bash
docker compose up --build
```

Docker hardening in compose:

- localhost port binding only,
- non-root container user,
- read-only container filesystem,
- `/tmp` tmpfs,
- dropped Linux capabilities,
- no-new-privileges,
- memory and process limits.

## API authentication

For demos that should not be open on localhost, set:

```bash
DERA_API_AUTH_ENABLED=true
DERA_API_KEY=<strong-local-random-value>
```

Then clients must send either a bearer-token Authorization header or `X-DERA-API-Key`.

## CORS

Default allowed origins:

```text
http://localhost:5173,http://127.0.0.1:5173
```

Do not use wildcard CORS. Add only exact local/demo origins.

## Retention

Default retention window:

```text
DERA_RETENTION_DAYS=7
```

Manual prune:

```bash
curl -X POST http://127.0.0.1:8080/maintenance/retention/prune
```

If API auth is enabled, include the configured API key header.

## Remote exposure requirements

Remote exposure is currently unsupported. Before enabling it, add and verify:

- TLS reverse proxy,
- strong auth / SSO,
- explicit CORS allowlist,
- audit log review,
- retention policy approval,
- dashboard access logs,
- vulnerability scanning,
- production database plan,
- backup/restore runbook,
- threat model sign-off.

## Rollback

Local app rollback is file/process rollback only:

1. Stop frontend static server.
2. Stop backend uvicorn or `docker compose down`.
3. Restore previous code revision or backup.
4. Restore SQLite volume only if approved and required.
5. Re-run tests before restarting.

No infrastructure rollback, customer notice, or external system action exists in this shell.
