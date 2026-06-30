# UX QA Report — True Hermes Streaming Pass

## Verification date

2026-06-30

## Why this pass happened

The previous chat improvement showed `Hermes Writing` immediately, but the backend still returned the Hermes answer as one complete response and the frontend progressively revealed it afterward. The requested behavior was closer to true streaming: show the answer while it is being generated.

## Changes made

Backend:

- Added `HermesClient.hermes_chat_stream(...)`.
- Uses Hermes API `/v1/chat/completions` with `stream: true`.
- Parses OpenAI-compatible `data:` chunks and yields text deltas.
- Added `POST /api/incidents/{id}/ask/stream`.
- The stream endpoint emits SSE events:
  - `status`
  - `delta`
  - `done`
- If Hermes streaming fails or Hermes is disabled, the stream honestly emits an unavailable fallback instead of pretending.

Frontend:

- `askHermes(...)` now tries `/ask/stream` first.
- Uses `fetch(...).body.getReader()` to consume chunks as they arrive.
- Appends streamed `delta` text directly into the active Hermes message.
- Keeps fallback to the older `/ask` endpoint if streaming fails.
- Still shows immediate `Hermes Writing` while the stream opens.
- Keeps `Live Hermes` / `Hermes unavailable` labels.

## Automated checks

Command:

```bash
node --check frontend/app.js && python3 -m pytest -q
```

Result:

```text
21 passed
```

## Backend runtime check

Health:

```json
{"status":"ok","hermes_enabled":true,"hermes_base_url":"http://127.0.0.1:8000"}
```

## Browser smoke check

URL tested:

```text
http://127.0.0.1:5173/?v=true-stream
```

Clicked prompt:

```text
What is happening?
```

Observed shortly after:

```json
{
  "live": true,
  "writing": false
}
```

Observed visible answer contained the live Hermes response and was rendered into the active chat message, not appended only after a separate final reveal step.

## Remaining refinement

The UX now streams from backend to browser, but the exact chunk granularity depends on what Hermes API emits. If the model/provider buffers chunks upstream, the UI will still show `Hermes Writing` immediately and then append larger chunks as they arrive.

---

# UX QA Addendum — Journey Remediation Pass

## Verification date

2026-06-30

## Scope

Implemented the first major remediation batch from `docs/ux-remediation-implementation-plan.md`:

- central product state model,
- one canonical primary CTA,
- disabled CTA reason text,
- investigation stage tracker,
- non-empty Hermes progress state before first streamed token,
- dossier readiness checklist,
- evidence drawer summary-first hierarchy,
- agent lifecycle/evidence chips,
- expanded chat layout improvements,
- left-rail operational chips,
- voice mode permission/scope clarification.

## Automated checks

Command:

```bash
node --check frontend/app.js && python3 -m pytest -q
```

Result:

```text
21 passed
```

## Browser smoke checks

URL tested:

```text
http://127.0.0.1:5173/?ux-fix=1
```

Observed at load:

- Top CTA is now `Start investigation`.
- Stage tracker is visible above workspace tabs.
- Runtime badges remain visible: backend, Hermes, safe mode, severity.
- Left rail uses compact operational chips: Cards, ATM, Branch, Active sessions.
- Browser console showed no JavaScript errors.

Start investigation check:

- Clicking `Start investigation` immediately changed the CTA to `Hermes is working...`.
- Visible reason appeared: `Waiting for Hermes to finish this investigation step.`
- After completion, state advanced to `Customer signal active` and CTA became `Continue to telemetry`.

Hermes progress check:

- Clicking a prompt immediately created a non-empty Hermes progress message.
- Visible pending state showed `Hermes is writing` before answer content arrived.
- The streamed answer populated the same Hermes message and retained the `Live Hermes` label.

Dossier readiness check:

- Dossier tab now shows `Dossier prerequisites pending`.
- Readiness checklist shows Customer signal complete and Telemetry / Change correlation / Recovery plan pending.
- The pending list explains what Hermes still needs before the dossier is ready.

Evidence drawer check:

- Clicking the customer evidence card opens a drawer with:
  - evidence title and summary,
  - `What this supports`,
  - `Limitations`,
  - collapsed `Raw evidence`.
- Raw JSON is no longer the first visible detail.

Expanded chat check:

- Expanding chat changes the button to `Collapse chat`.
- The chat becomes much more readable.
- The incident rail becomes more compact and hides the journey/operator-focus panels.
- No horizontal overflow was detected at the tested viewport.

Voice tab check:

- Voice mode now separates Input, Output, and Simulation.
- Input clearly states: `Uses browser microphone permission only. No calls are placed.`
- Simulation clearly states it is not connected to telephony or customer records.

## Known follow-up refinements

- The stage tracker currently treats `Customer signal` as active in `ready_with_incident`; this is acceptable for now because the incident starts with customer-signal evidence, but a future polish pass could add a separate `Ready` stage if desired.
- In expanded chat mode, the evidence canvas remains usable but cards can become narrow at 1280px. If evidence work becomes primary while chat is expanded, add a selected-evidence details row or allow the center workspace to temporarily hide inactive lanes.

---

# UX QA Addendum — Live Agent Visibility Pass

## Verification date

2026-06-30

## Scope

Responded to the product issue that `Start investigation` still lacked visual feedback in the part of the cockpit doing the work. Added operator-visible specialist activity so the user can see agents working, inspect what they are doing, and open a work drawer for each agent.

## Changes made

Frontend:

- Added `activeWorkstream` live activity banner under the workspace tabs.
- Clicking `Start investigation` now immediately switches to the Agents tab.
- The active specialist card changes to `running live` with highlighted styling.
- Added optimistic local work logs while the backend/Hermes request is in flight.
- Added an `Open live agent work` action during active investigation.
- Added an agent drawer with:
  - Status,
  - Visible reasoning summary,
  - Tool / action,
  - Work log,
  - Evidence consumed.
- Agent cards are now clickable.
- The drawer explicitly labels the reasoning as an operator-facing summary, not hidden chain-of-thought.

## Automated checks

Command:

```bash
node --check frontend/app.js && python3 -m pytest -q
```

Result:

```text
21 passed
```

## Browser smoke checks

URL tested:

```text
http://127.0.0.1:5173/?agent-visual=1
```

Observed after clicking `Start investigation`:

- CTA immediately changed to `Hermes is working...`.
- Workspace automatically switched to the Agents tab.
- Active workstream banner appeared with `Customer Signal Agent` running.
- Active agent card showed `RUNNING LIVE`.
- Current operation and work log updated visually while the request was in flight.
- `Open live agent work` appeared in the banner and agent card.

Observed after clicking `Open work`:

- Agent drawer opened.
- Drawer showed status, visible reasoning summary, tool/action, work log, and evidence consumed.
- Browser console showed no JavaScript errors.

## Known follow-up refinements

- Backend incident advancement currently marks some later queued agents as `running` after the first step. This pre-existing backend behavior makes the workstream look more active than strictly sequential. A future backend-state pass should model `queued -> running -> complete` per exact active stage.
- The visible reasoning summary is intentionally not private chain-of-thought. It is an operator-facing explanation of the agent's evidence and tool path.
