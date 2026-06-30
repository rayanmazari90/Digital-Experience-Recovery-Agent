# Security and Privacy Test Plan

## Automated tests

Run on every hardening change:

```bash
node --check frontend/app.js
python3 -m pytest -q
python3 -m compileall app
```

Expected coverage:

- API contracts still work for synthetic data.
- API auth blocks requests when enabled and permits valid API keys.
- Sensitive payload scanner rejects obvious PII/secret-like values.
- Upload size limit rejects oversize artifacts.
- Audit logs are written for state-changing actions.
- Security headers are present.
- CORS is explicit and not wildcard/credentialed.
- Frontend still exposes accessibility, voice-boundary, presentation, and live watch contracts.
- Orchestration children remain bounded to narrow toolsets.

## Manual smoke tests

1. Start backend and frontend on localhost.
2. Load frontend in a browser.
3. Confirm browser console has no JavaScript errors.
4. Start a synthetic run.
5. Confirm evidence/outcome records remain synthetic.
6. Confirm approval panel records local approval/rejection only.
7. Confirm voice mode labels browser speech as custom app-side bridge.
8. Confirm no telephony/customer messaging claim is visible.
9. Query audit logs.
10. Run retention prune.

## Negative tests

- Submit an email address in evidence payload: expect `422 sensitive_data_rejected`.
- Submit a card-like number in evidence payload: expect rejection.
- Submit secret/key labels in payload: expect rejection.
- Upload a file larger than `DERA_MAX_UPLOAD_BYTES`: expect `413 artifact_too_large`.
- Enable `DERA_API_AUTH_ENABLED=true` and omit API key: expect `401 api_auth_required`.
- Send request from disallowed CORS origin in browser: expect browser block.

## Unsupported areas requiring future tests

- Real transcript masking/tokenization pipeline.
- Production DLP.
- SSO/RBAC.
- TLS reverse proxy.
- Production database migration and encryption.
- Real observability/ITSM integrations.
- Remote dashboard exposure.
- Backup/restore for production records.
- Load/performance tests.

## Exit criteria for local demo hardening

- Full pytest suite passes.
- Frontend JS syntax check passes.
- Static page loads without browser console errors.
- Security docs list all unsupported/risky areas.
- Docker compose remains localhost-bound.
- `.env` remains uncommitted.
- No real credentials or customer records are present in repo files.
