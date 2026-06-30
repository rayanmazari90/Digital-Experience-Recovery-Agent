# UI Redesign Plan — Digital Experience Recovery Agent

## Current frontend inspection

Current files inspected:

- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- `tests/test_frontend_shell.py`

Current state management approach:

- A single global `state` object stores API base, scenario/session/run IDs, EventSource, approval state, voice state, duplicate event IDs, and demo-start guard.
- Runtime events are mapped through `runtimeEventMap`, then applied directly to scattered DOM elements.
- The UI currently mixes product narrative, technical stream, voice bridge, accessibility controls, evidence, subagents, approvals, and presentation artifacts in one default page.
- Backend contracts currently used and preserved:
  - `GET /health`
  - `POST /scenarios`
  - `POST /sessions`
  - `POST /runs`
  - `GET /runs/{run_id}/events` via `EventSource`
  - `POST /runs/{run_id}/events`
  - `POST /sessions/{session_id}/evidence`
  - `POST /sessions/{session_id}/outcomes`
  - `GET /sessions/{session_id}/history`

## UX problem to solve

The current screen still reads as a technical dashboard. It exposes too many panels at once, makes the user choose where to look, and buries the product story behind implementation artifacts.

The rebuilt product must answer four questions at all times:

1. What is happening now?
2. Why is it happening?
3. What evidence supports it?
4. What should the user do next?

## New product structure

### 1. Setup mode

Shown when the engine is disconnected or connection fails.

Visible content:

- Headline: “Connect the recovery engine”
- Backend status
- Hermes status
- Safe-mode statement
- Primary CTA: “Connect”
- Secondary CTA: “Run synthetic UI preview”

No dashboard panels appear while disconnected.

### 2. Demo mode

Main self-presenting live demo. Above the fold uses three columns:

- Left: customer journey timeline
- Center: large living recovery core
- Right: Hermes workstream

One bottom drawer contains Evidence & Proof and is collapsed by default.

The top bar contains:

- Product identity
- Backend connected / Hermes connected / Synthetic safe mode indicators
- One state-driven primary CTA

### 3. Dossier mode

Final product output after the run reaches `approval_required`.

Shows a polished recovery dossier:

- Customer impact
- Technical evidence
- Likely root cause
- Recommended recovery
- Customer communication
- Safety gate with local-only approve/reject actions

## UI state machine

The rebuild uses an explicit product state machine:

- `disconnected`
- `ready`
- `running.detect`
- `running.observe`
- `running.correlate`
- `running.recover`
- `approval_required`
- `approved`
- `rejected`
- `error`

Every visible headline, CTA, workstream card, journey state, recovery-core animation, dossier state, and detail drawer is derived from this state machine.

## Runtime/event mapping

Existing backend runtime events map into product states:

- `run.started` -> `running.detect`
- `hermes.subagent.customer_signal` -> `running.detect`
- `hermes.tool.observability` -> `running.observe`
- `hermes.subagent.change_correlation` -> `running.correlate`
- `hermes.subagent.recovery` -> `running.recover`
- `approval.required` -> `approval_required`
- local approval -> `approved`
- local rejection -> `rejected`
- API/SSE failure -> `error`

## Visual direction

- Dark banking command center
- One dominant visual center: Recovery engine
- Spacious enterprise UI
- No visible empty panels
- No raw logs in default view
- Subtle stateful motion only
- Advanced/voice/accessibility/runtime details hidden behind drawers
- Responsive for 1366x768 and 1440x900

## Safety and product boundaries

The rebuilt UI keeps all existing safety guardrails:

- Synthetic data only
- Local approval/rejection only
- No real customer messaging
- No telephony
- No bank-system rollback
- Voice bridge remains clearly marked as custom app-side browser bridge in advanced details

## Acceptance check

The final implementation must pass:

- First screen has one dominant action
- Disconnected state does not show full dashboard
- Demo story is understandable without docs
- No empty panels in main experience
- Evidence is available but collapsed by default
- Final dossier is the primary product output
- Advanced details are available but not dominant
- Existing backend contracts are not broken
