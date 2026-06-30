# Contributing

This project is designed so collaborators can work on the product without needing Rayane's local Hermes profile or secrets.

## Development modes

### Demo mode: no Hermes required

Use this for UI, CSS, product flow, docs, and most backend changes.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# keep DERA_HERMES_ENABLED=false
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

In another terminal:

```bash
python3 -m http.server 5173 --directory frontend
```

Open `http://127.0.0.1:5173`.

### Live Hermes mode: optional

Only needed if you are testing the real local Hermes integration.

Install and configure Hermes Agent separately:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes setup
```

Start a local Hermes API/gateway using the dedicated `digital-recovery` profile, then set:

```bash
DERA_HERMES_ENABLED=true
DERA_HERMES_BASE_URL=http://127.0.0.1:8000
DERA_HERMES_API_KEY=<local bearer key>
DERA_HERMES_MODEL=digital-recovery-agent
```

Do not commit `.env`, Hermes profiles, credentials, memory, sessions, or runtime databases.

## Git workflow

```bash
git checkout -b feature/short-description
python3 -m pytest -q
node --check frontend/app.js
git add .
git commit -m "feat: short description"
git push origin feature/short-description
```

Open a pull request against `main`.

## Safety boundaries

- Use synthetic/demo-only data.
- Do not connect real bank, customer, observability, messaging, call-center, or telephony systems.
- Do not add another LLM or agent runtime as the reasoning authority; Hermes is the only LLM runtime for this project.
- Label mocks and unsupported integrations clearly.
- Keep side effects behind explicit human approval gates.

## Public repository hygiene

The public repo intentionally excludes raw source corpus files such as course decks, extracted course text, private briefs, local SQLite databases, and local workspace storage. Derived product docs under `docs/` can be committed when they do not contain private or copyrighted source material.
