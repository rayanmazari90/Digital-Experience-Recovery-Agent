# Security Hardening Review

Status: hardening pass applied for the synthetic/local product shell. Production use remains unsupported until every risky area below is resolved and approved.

## 1. Secrets handling review

### Current controls

- Repository examples use placeholders only; `.env` is gitignored.
- Hermes credentials must live in the dedicated `digital-recovery` profile `.env`, not app code or docs.
- Hermes documented control: keep secret redaction enabled with `hermes config set security.redact_secrets true` and restart Hermes after changes.
- App setting `DERA_HERMES_API_KEY` is only used when `DERA_HERMES_ENABLED=true`.
- App setting `DERA_API_AUTH_ENABLED=true` requires either a bearer-token Authorization header or `X-DERA-API-Key` for backend API calls.

### Required before non-local use

- Replace all `dev-local-only-*` placeholder keys.
- Store real values only in profile `.env` or an approved secret manager.
- Rotate keys after demos or screen-sharing.
- Never commit `.env`, SQLite databases, uploaded artifacts, logs, or generated recordings.

### Risk flags

- `DERA_API_AUTH_ENABLED=false` is acceptable for localhost-only development only.
- There is no production secret manager integration yet: `Pending`.
- There is no automated secret scanning CI yet: `Pending`.

## 2. Hermes profile config review

### Required profile

Use the dedicated Hermes profile:

```bash
hermes --profile digital-recovery ...
```

### Hermes documented controls to prefer

- Profiles for state isolation.
- `.env` for secrets.
- `security.redact_secrets=true` for tool-output secret redaction.
- `privacy.redact_pii=true` for gateway PII redaction when using messaging platforms.
- `approvals.mode=manual` or `smart`; never `off` for recovery workflows.
- Website blocklist via `security.website_blocklist` once real internal/sensitive domains are supplied.
- Narrow toolsets for delegated children.

### Recommended commands

```bash
hermes --profile digital-recovery config set security.redact_secrets true
hermes --profile digital-recovery config set privacy.redact_pii true
hermes --profile digital-recovery config set approvals.mode manual
```

### Risk flags

- Real profile config was not modified by this app hardening pass.
- The sensitive website blocklist content is still not supplied by the corpus.
- Dashboard exposure remains `Pending` / `Unspecified` outside localhost.

## 3. Docker isolation review

### Applied controls

- Container runs as non-root user `dera`.
- Compose binds the API to localhost: `127.0.0.1:8080:8080`.
- Container filesystem is read-only except mounted `/data` and tmpfs `/tmp`.
- `no-new-privileges:true` enabled.
- Linux capabilities dropped with `cap_drop: [ALL]`.
- `pids_limit` and memory limit added.
- App data is isolated in the `dera-data` volume.

### Risk flags

- Docker image is not pinned by digest: `Pending`.
- No SBOM or image vulnerability scan is configured: `Pending`.
- SQLite volume is not encrypted by the app: depends on host/storage controls.

## 4. Website blocklist policy

### Policy

Until a real approved domain list exists:

- Product shell must not browse or query external bank/internal systems.
- Hermes children must not receive browser/web toolsets for incident roles.
- All real banking, observability, messaging, CI/CD, and customer data integrations remain blocked.

### Minimum categories to block once supplied

- bank production domains,
- observability consoles,
- CI/CD systems,
- ServiceNow/ITSM tenants,
- internal Git/repo hosts,
- customer data stores,
- contact-center and messaging systems,
- payment/card systems,
- identity/IAM/admin consoles.

### Risk flags

- Actual domains are missing from the corpus.
- This repo cannot safely infer internal domains; project owner must provide or explicitly waive them.

## 5. API server auth and CORS review

### Applied app controls

- Optional backend API key auth via `DERA_API_AUTH_ENABLED` / `DERA_API_KEY`.
- Accepted auth headers: bearer-token Authorization header or `X-DERA-API-Key`.
- CORS origins are explicit via `DERA_CORS_ALLOW_ORIGINS`.
- CORS credentials are disabled.
- CORS methods limited to `GET` and `POST`.
- CORS headers limited to `Authorization`, `Content-Type`, `X-DERA-API-Key`, `X-DERA-Actor`.
- Security headers are emitted by middleware:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy`
  - `Cache-Control: no-store`
  - `Content-Security-Policy`

### Risk flags

- No user identity provider / SSO integration: `Pending`.
- No per-route authorization model beyond shared API key: `MVP only`.
- No TLS termination in the app: use a reverse proxy if remote exposure is ever approved.

## 6. Dashboard exposure review

### Current stance

- Frontend is a static localhost shell.
- Backend default is localhost-only.
- Docker compose binds to localhost only.
- Remote dashboard exposure is not implemented.

### Required before remote exposure

- TLS reverse proxy.
- Strong authentication.
- Explicit CORS allowlist.
- CSRF strategy if cookies are introduced.
- Audit-log review and retention policy.
- Dashboard access logging.
- No real customer data until data policy is approved.

### Risk flags

- Production dashboard auth is unsupported.
- Multi-user access control is unsupported.
- Enterprise SSO is unsupported.

## 7. Privacy-by-design checklist

- [x] Synthetic/dev-only default.
- [x] App-layer sensitive payload scanner rejects obvious PII/secret-like values by default.
- [x] `DERA_ALLOW_SENSITIVE_PAYLOADS=false` default.
- [x] Upload size limit via `DERA_MAX_UPLOAD_BYTES`.
- [x] Audit log table for create/run/evidence/outcome/upload/retention actions.
- [x] Retention prune endpoint: `POST /maintenance/retention/prune`.
- [x] Configurable retention days: `DERA_RETENTION_DAYS`.
- [x] Local-only Docker port binding.
- [x] No customer messaging or telephony integration.
- [ ] Approved masking/tokenization service for real transcripts: `Pending`.
- [ ] Approved retention/access-control policy for real data: `Pending`.
- [ ] Field-level encryption for sensitive records: `Pending`.
- [ ] SSO/RBAC: `Pending`.

## 8. App-layer controls added

- `app/security.py`:
  - sensitive value scanning,
  - API key dependency,
  - security headers,
  - audit logging helper,
  - retention pruning helper.
- `app/db.py`:
  - `audit_logs` table.
- `app/main.py`:
  - API key dependency,
  - CORS hardening,
  - security headers,
  - PII/secret-like payload rejection,
  - upload size cap,
  - audit-log endpoint,
  - retention prune endpoint.

## 9. Explicit unsupported/risky areas

- Real bank integrations: unsupported.
- Real customer records/transcripts: unsupported without data policy.
- Direct telephony: unsupported.
- Customer messaging/send: unsupported without explicit approval and integration design.
- Remote dashboard/API exposure: unsupported until auth/TLS/SSO/CORS are designed.
- Production monitoring stack integration: unsupported.
- Production database: unsupported; SQLite is dev/demo only.
- Production DLP: unsupported; current scanner is a conservative app-layer guard only.
- Production RBAC/SSO: unsupported.
