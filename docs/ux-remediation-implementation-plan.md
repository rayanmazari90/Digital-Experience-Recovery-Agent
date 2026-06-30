# Digital Experience Recovery Agent — UX Remediation Implementation Plan

## Purpose

This plan turns the UX journey audit into a concrete implementation roadmap for the Digital Experience Recovery Agent cockpit.

The goal is not to add more panels. The goal is to make the product feel like an elite, operational incident command system where the operator always understands:

1. What is happening now.
2. Why it matters.
3. Which evidence supports it.
4. What Hermes is doing.
5. What the operator should do next.
6. What is safe-mode demo behavior versus live Hermes reasoning.

## Product north star

The product should be understandable in one sentence:

> Left is the incident, center is the investigation workspace, right is live Hermes command, and the next operator decision is always obvious.

## Non-negotiable guardrails

- Hermes is the only reasoning runtime.
- No fake Hermes answers labeled as live.
- Demo data remains synthetic and visibly safe-mode.
- No real rollback, customer messaging, telephony, bank integration, or external system mutation.
- The cockpit stays above-the-fold usable at 1366x768.
- Raw streams and JSON remain available, but never dominate the default journey.
- Every disabled action explains why it is disabled.
- Every primary action changes visible state immediately.
- The dossier becomes a polished decision artifact, not a chat transcript.

---

## Phase 0 — Baseline and Regression Harness

### Objective

Before changing UX, lock in the current behavior so we can confidently refactor without breaking live Hermes, streaming, safety labels, or core navigation.

### Work items

#### 0.1 Capture current product state contract

Create a short product-state document or test fixture describing current states:

- `ready_with_incident`
- `investigating.customer_signal`
- `investigating.observability`
- `investigating.change_correlation`
- `investigating.recovery_planning`
- `dossier_ready`
- `approval_required`
- `approved_local`
- `rejected_local`
- `error`

Each state should define:

- primary CTA text
- primary CTA enabled/disabled reason
- current stage label
- active agent
- active tab suggestion
- visible Hermes prompt suggestions
- dossier readiness
- allowed approval actions

#### 0.2 Add visual/DOM smoke assertions

Add tests that check the DOM contains the required UX primitives, not just scripts compiling.

Required assertions:

- Product has one global primary CTA.
- The CTA has a disabled reason container.
- Stage tracker exists.
- Dossier readiness checklist exists.
- Hermes chat has a non-empty pending/progress state.
- Evidence drawer includes human summary and raw evidence section.
- Voice tab includes browser permission/scope copy.
- Expanded chat mode has a compact incident rail state.

#### 0.3 Preserve existing green tests

Current baseline from prior run:

- Backend health returns Hermes enabled.
- Frontend loads locally.
- Full test suite passes: `21 passed`.

Acceptance criteria:

- No regression starts without a known baseline.
- Existing test suite remains green before Phase 1 begins.

---

## Phase 1 — Product State Machine and One Canonical Next Action

### Problem

The product currently has multiple overlapping action paths:

- Top CTA: `Ask Hermes to investigate` / `Continue investigation`
- Right rail quick prompt: `Start investigation`
- Tab CTA: `Ask Hermes for technical timeline`
- Prompt chips that sometimes act like investigation control

This creates uncertainty about which action is primary.

### Objective

Make the cockpit state-driven. Every region should derive from one central product state model.

### Work items

#### 1.1 Create explicit frontend state model

In `frontend/app.js`, centralize state into a contract like:

```js
const PRODUCT_STATES = {
  ready_with_incident: {
    stage: 'Ready',
    headline: 'Login authentication degradation',
    primaryCta: 'Start investigation',
    primaryAction: 'start_investigation',
    ctaEnabled: true,
    ctaDisabledReason: null,
    recommendedTab: 'chronology',
    activeAgent: 'supervisor',
    chatPrompts: [
      'What is happening?',
      'Start investigation',
      'Show affected customer journey',
      'What evidence do we have?'
    ],
    dossierReadiness: {...}
  },
  investigating_customer_signal: {...}
}
```

Avoid scattered ad hoc DOM updates.

#### 1.2 Add a single global next-action resolver

Implement:

```js
function getNextAction(state) {}
function performNextAction(action) {}
function renderPrimaryCta(state) {}
```

The top CTA should always reflect the canonical next action.

#### 1.3 Demote duplicate state-changing quick prompts

Prompt chips should mostly be questions, not duplicate state transitions.

Before:

- `Start investigation`
- `What is happening?`
- `Show affected customer journey`
- `What evidence do we have?`

After ready state:

- Primary CTA: `Start investigation`
- Prompt chips:
  - `What is happening?`
  - `What evidence will Hermes inspect?`
  - `What remains operational?`

After investigation begins:

- Primary CTA: `Continue to telemetry`
- Prompt chips:
  - `What evidence supports this?`
  - `What is uncertain?`
  - `What should I watch next?`

#### 1.4 Disabled CTA reason

Every disabled CTA needs visible reason text.

Example:

```html
<button disabled>Continue investigation</button>
<p class="cta-reason">Waiting for Hermes to finish customer signal analysis.</p>
```

Acceptance criteria:

- There is one dominant primary CTA.
- If disabled, it has an immediately visible explanation.
- Prompt chips no longer compete with the global CTA.
- Switching states updates CTA, stage tracker, agent cards, dossier readiness, and chat prompts from the same state source.

---

## Phase 2 — Immediate Hermes Progress and Streaming Trust

### Problem

After starting investigation, the UI can show a `Live Hermes` bubble before meaningful text appears. This makes the system feel stuck even when streaming is working.

### Objective

Make Hermes activity visible within 150ms and never show an empty assistant response shell.

### Work items

#### 2.1 Add Hermes pre-token progress phases

Before first streamed delta, show a compact progress line:

- `Opening incident context...`
- `Reading customer signal evidence...`
- `Checking synthetic safety scope...`
- `Preparing operator summary...`

These are UI progress states, not fake answer content.

#### 2.2 Replace empty assistant bubble with pending component

Instead of:

`Hermes | Live Hermes` with empty body

Render:

```html
<div class="message message-pending">
  <div class="message-meta">Hermes · Live Hermes</div>
  <div class="hermes-progress">
    <span class="pulse-dot"></span>
    <span>Reading customer signal evidence...</span>
  </div>
</div>
```

When the first delta arrives, replace progress body with streamed answer.

#### 2.3 Add stream lifecycle handling

The frontend stream consumer should track:

- `stream_opening`
- `first_delta_received`
- `stream_done`
- `stream_error`
- `fallback_used`

Each state should visibly map to UI.

#### 2.4 Add retry affordance for failed stream

If `/ask/stream` fails and `/ask` fallback also fails:

- show `Hermes unavailable`
- show reason from backend if safe
- add `Retry` button
- do not label fallback as `Live Hermes`

Acceptance criteria:

- No empty Hermes message bubble is visible.
- User sees progress within 150ms.
- First token replaces progress cleanly.
- Stream failure is honest and recoverable.

---

## Phase 3 — Stage Tracker and Investigation Storyline

### Problem

The user can infer the workflow from tabs and timeline, but there is no single global `you are here` path.

### Objective

Add a compact stage tracker that explains the investigation progression without turning the cockpit into a passive wizard.

### Work items

#### 3.1 Add stage tracker component

Stages:

1. Customer signal
2. Telemetry
3. Change correlation
4. Recovery plan
5. Approval
6. Dossier

Each stage has:

- `pending`
- `active`
- `complete`
- `blocked`

#### 3.2 Link stage tracker to tabs

Clicking a stage should switch to the relevant tab:

- Customer signal -> Evidence or Agents
- Telemetry -> Evidence
- Change correlation -> Evidence
- Recovery plan -> Dossier or Agents
- Approval -> Dossier
- Dossier -> Dossier

#### 3.3 Show stage-specific operator focus

The left rail or center header should display a concise operator focus:

- Ready: `Start Hermes investigation.`
- Customer signal: `Confirm whether complaints cluster around MFA delivery.`
- Telemetry: `Check whether auth latency and 504s match customer symptoms.`
- Change correlation: `Compare incident window against CHG-1048.`
- Recovery: `Review rollback and validation plan.`
- Approval: `Approve or reject local synthetic recovery.`
- Dossier: `Review final incident artifact.`

Acceptance criteria:

- User can identify current stage in under 3 seconds.
- The stage tracker does not replace tabs; it explains progression.
- Each stage maps to an actionable tab or next step.

---

## Phase 4 — Dossier Readiness and Approval Clarity

### Problem

The Dossier tab says it is waiting, but does not explain what is missing or how to unlock it.

### Objective

Make the dossier a transparent decision artifact with visible prerequisites and approval state.

### Work items

#### 4.1 Add readiness checklist

Dossier tab should always show:

- Customer signal: complete/pending/blocked
- Telemetry: complete/pending/blocked
- Change correlation: complete/pending/blocked
- Recovery plan: complete/pending/blocked
- Operator approval: not required/pending/approved/rejected

Each item includes:

- status icon or text label
- evidence count
- linked tab/action
- confidence if available

#### 4.2 Split dossier into readiness and artifact modes

If incomplete:

- Show readiness checklist first.
- Show concise explanation of what Hermes needs next.
- Provide CTA to continue investigation.

If complete:

Show polished artifact sections:

- Executive summary
- Customer impact
- Evidence chain
- Likely root cause
- Recommended recovery
- Validation plan
- Customer-safe communication draft
- Risks and uncertainties
- Approval record

#### 4.3 Add approval gate component

When recovery requires approval:

- Clearly state this is local synthetic approval only.
- Show what will and will not happen.
- Show approve/reject buttons.
- Require explicit local approval for simulated recovery state change.

Copy example:

`Local safe-mode approval only. This records a synthetic recovery decision. It does not contact customers, deploy code, shift traffic, rollback production, or touch bank systems.`

#### 4.4 Dossier revision actions

Add focused revision buttons:

- `Revise executive summary`
- `Tighten customer-safe message`
- `Explain technical evidence`
- `List unresolved risks`

Each routes to live Hermes when enabled.

Acceptance criteria:

- Dossier never just says `waiting` without prerequisites.
- Approval decision is impossible to confuse with real-world action.
- Completed dossier looks like a product artifact, not a chat transcript.

---

## Phase 5 — Structured Hermes Answers

### Problem

Hermes answers are useful but too dense for an operator under pressure.

### Objective

Render Hermes output into operational sections while preserving live Hermes as the source.

### Work items

#### 5.1 Define preferred answer structure in backend prompt context

When sending incident context to Hermes, ask for concise sections:

- Situation
- Evidence
- Uncertainty
- Next action
- Approval needed

For longer answers, request markdown headings or JSON-ish structure that the frontend can render.

#### 5.2 Add frontend markdown/section rendering

Without overengineering, parse common patterns:

- headings
- bullet lists
- short tables
- `Evidence:` blocks
- `Next step:` blocks

Render as compact cards.

#### 5.3 Pin recommended next action

At the bottom of each Hermes answer, render a visually distinct next-action strip if present:

`Recommended next action: Continue to telemetry check.`

This should not auto-execute. It should point to the canonical CTA.

#### 5.4 Add answer controls

Each Hermes response should allow:

- `Use as dossier note`
- `Show supporting evidence`
- `Ask follow-up`
- `Collapse`

Keep controls compact.

Acceptance criteria:

- Operator can scan a Hermes answer in under 10 seconds.
- Evidence and uncertainty are visually separated.
- The answer still clearly says `Live Hermes` only when live.

---

## Phase 6 — Evidence Canvas and Drawer Upgrade

### Problem

Evidence lanes are conceptually strong but currently static. The drawer is raw-first and JSON-heavy.

### Objective

Make evidence the center of the product's credibility.

### Work items

#### 6.1 Add evidence state metadata

Each evidence card should have:

- ID
- source type
- title
- summary
- supports
- limitations
- confidence/weight
- related stage
- related agent
- timestamp/window
- raw payload

#### 6.2 Active evidence highlighting

When user selects:

- timeline event
- agent card
- Hermes answer evidence link
- dossier checklist item

The relevant evidence card should highlight in the Evidence tab.

#### 6.3 Drawer human summary first

Drawer layout:

1. Header: title, source, confidence
2. Human summary
3. What this supports
4. Limitations / uncertainty
5. Related agent and timeline event
6. Raw evidence collapsed by default

#### 6.4 Add evidence filters

Small filters:

- Customer signal
- Telemetry
- Change
- Recovery
- Used in dossier
- Needs review

#### 6.5 Reduce empty lane space

If each lane has only one card, reduce lane height and use lower area for selected evidence details or evidence relationship graph.

Acceptance criteria:

- User can click any evidence and understand it without reading JSON.
- Raw evidence remains available but secondary.
- Evidence visibly connects to agents, timeline, and dossier.

---

## Phase 7 — Agents Workstream Lifecycle

### Problem

Agents are visible, but their states feel too static. The operator needs to see specialist progress and evidence consumed.

### Objective

Make subagent work cards feel operational, auditable, and connected to Hermes reasoning.

### Work items

#### 7.1 Add lifecycle model per agent

Each agent card should include:

- status: queued/running/complete/blocked
- current operation
- evidence consumed
- finding
- confidence
- started_at
- updated_at
- output available

#### 7.2 Add mini event history

Example:

- 09:51 Queued
- 09:52 Reading complaint samples
- 09:52 Complete: MFA delay cluster found

#### 7.3 Add evidence consumed chips

Each agent should list evidence IDs as clickable chips:

- `ev_customer_complaints`
- `ev_auth_latency`
- `ev_chg_1048`

#### 7.4 Distinguish simulated/local state from live Hermes output

If the agent state is a frontend/backend synthetic fixture, label it as synthetic scenario state.

If generated by Hermes, label it as `Live Hermes` or `Hermes-derived` depending on exact source.

Do not imply actual delegate_task ran unless it did.

Acceptance criteria:

- Operator knows what each specialist is doing or did.
- Agent evidence links open the drawer.
- No misleading implication that real external systems were queried.

---

## Phase 8 — Chat Expansion and Layout Responsiveness

### Problem

Expanded chat improves answer readability but compresses the left incident rail and can cause awkward wrapping.

### Objective

Make expanded chat a first-class reading mode, not a layout compromise.

### Work items

#### 8.1 Compact incident rail in expanded mode

When chat is expanded:

Replace full incident rail with a compact strip:

- SEV-2
- Login/Auth
- 18.4k users
- Stage: Customer signal
- Safe mode

Move detailed incident cards behind `Incident details`.

#### 8.2 Preserve workspace minimum width

Define grid constraints:

- compact left rail: 190-220px
- center workspace: minimum 360-420px
- expanded chat: 580-680px depending viewport

Avoid truncating essential labels.

#### 8.3 Add collapsible answer history

In expanded chat, long histories should not push the input out of context.

Options:

- collapse older answers automatically
- keep latest answer expanded
- add `Show previous response` controls

#### 8.4 Mobile/narrow layout plan

At narrow widths:

- Use bottom navigation: Incident, Timeline, Evidence, Hermes, Dossier
- Hermes input sticky at bottom
- One primary CTA sticky at top or bottom
- Left rail becomes incident overview tab

Acceptance criteria:

- Expanded chat improves reading without making primary workflow unusable.
- No important card text wraps into unreadable fragments.
- 1366x768 and 1280x633 remain usable.

---

## Phase 9 — Left Rail and Copy Polish

### Problem

The left incident rail is useful but some text wraps awkwardly and all-caps labels are overused.

### Objective

Preserve the command-center feel while improving scanability.

### Work items

#### 9.1 Convert operational scope to chips

Before:

`Cards, ATM, branch systems, and authenticated sessions`

After:

- Cards
- ATM
- Branch
- Active sessions

#### 9.2 Clarify incident state labels

Replace ambiguous states:

- `Ready with incident` -> `Ready for investigation`
- `Investigating customer signal` -> `Customer signal active`
- `Confidence pending` -> `Dossier prerequisites pending`

#### 9.3 Reduce all-caps usage

Keep all-caps for section/kicker labels:

- ACTIVE INCIDENT
- CHRONOLOGY
- HERMES COMMAND

Use sentence case for statuses and longer labels.

#### 9.4 Make safe-mode copy concise

Safe-mode copy should be visible but not repeated excessively.

Recommended persistent badge:

`Safe mode: no real systems touched`

Detailed explanation appears in approval gate and setup docs.

Acceptance criteria:

- Incident rail scans cleanly in standard and expanded layout.
- Labels are operationally precise.
- Safety remains clear without making Hermes feel fake.

---

## Phase 10 — Voice Operator Mode Clarification

### Problem

Voice tab correctly says no telephony, but action grouping and permission implications can be clearer.

### Objective

Make voice feel like an app-side browser bridge, with explicit boundaries.

### Work items

#### 10.1 Group controls

Input group:

- Start voice input
- Microcopy: `Uses browser microphone permission only. No calls are placed.`

Output group:

- Speak situation
- Speak dossier

Simulation group:

- Simulate caller question
- Microcopy: `Synthetic caller prompt. Not connected to telephony or customer records.`

#### 10.2 Add permission/error states

Handle:

- browser speech unavailable
- microphone permission denied
- speech recognition active
- speech recognition stopped
- text fallback available

#### 10.3 Voice transcript handoff

If voice input produces text, show it in the Hermes input before submitting, or submit with a visible transcript.

Acceptance criteria:

- User understands exactly what voice can/cannot do.
- No telephony implication remains.
- Text fallback is always visible.

---

## Phase 11 — Backend State Contract Hardening

### Problem

The frontend still carries too much scenario state. For a real product feel, the backend should own incident state, evidence, agents, dossier, approval, and events.

### Objective

Move toward backend-owned state contracts while keeping the app local and synthetic.

### Work items

#### 11.1 Audit existing endpoints

Verify current state of:

- `/api/incidents/{id}/state`
- `/api/incidents/{id}/evidence`
- `/api/incidents/{id}/events`
- `/api/incidents/{id}/ask`
- `/api/incidents/{id}/ask/stream`
- approval/dossier endpoints if present

#### 11.2 Define canonical response shapes

State endpoint should return:

```json
{
  "incident_id": "...",
  "state": "investigating.customer_signal",
  "stage": {...},
  "primary_action": {...},
  "incident": {...},
  "dossier_readiness": {...},
  "safety": {...}
}
```

Evidence endpoint should return:

```json
{
  "evidence": [
    {
      "id": "ev_customer_complaints",
      "lane": "customer_signal",
      "title": "Complaint spike",
      "summary": "37% spike in MFA-code-not-arriving complaints",
      "supports": [...],
      "limitations": [...],
      "raw": {...}
    }
  ]
}
```

Agents endpoint should return:

```json
{
  "agents": [
    {
      "id": "customer_signal_agent",
      "name": "Customer Signal Agent",
      "status": "complete",
      "current_operation": "Clustered masked complaint samples",
      "finding": "MFA delay cluster found",
      "confidence": 0.86,
      "evidence_ids": ["ev_customer_complaints"],
      "events": [...]
    }
  ]
}
```

Dossier endpoint should return readiness and artifact separately.

#### 11.3 Keep Hermes streaming endpoint separate

Retain:

- `/ask/stream` for live chat
- `/ask` fallback for non-stream

But ensure both include:

- source label
- live boolean
- unavailable reason if applicable
- safety scope

Acceptance criteria:

- Frontend renders from backend state where practical.
- State contract is test-covered.
- Live Hermes chat remains working.

---

## Phase 12 — Test Plan

### Unit/static tests

Frontend:

- `node --check frontend/app.js`
- state resolver returns correct CTA per state
- disabled CTA always has reason
- prompt suggestions update by state
- stage tracker maps to correct tabs
- evidence drawer renders summary and raw sections
- expanded chat toggles compact incident rail

Backend:

- health endpoint still reports Hermes status
- `/ask/stream` emits SSE `status`, `delta`, `done`
- unavailable Hermes never returns `live: true`
- state/evidence/agents/dossier contracts validate
- approval endpoint records local-only approval/rejection

### Browser smoke tests

At 1366x768 or comparable viewport:

1. Load app.
2. Confirm one primary CTA.
3. Click Start investigation.
4. Confirm visible progress within 150ms-1s.
5. Confirm first Hermes content streams into non-empty answer.
6. Confirm stage tracker advances.
7. Open Evidence tab.
8. Click evidence card.
9. Confirm drawer shows summary first and raw collapsed.
10. Open Agents tab.
11. Confirm agent lifecycle and evidence chips.
12. Open Dossier tab.
13. Confirm readiness checklist.
14. Continue until approval_required if supported.
15. Confirm approval copy says local synthetic only.
16. Expand chat.
17. Confirm compact incident rail and readable chat.
18. Open Voice tab.
19. Confirm no-telephony and browser-permission copy.
20. Check browser console for JS errors.

### Visual acceptance checks

- No horizontal overflow.
- No overlapping panels.
- No unreadable wrapped metric text.
- Primary CTA visible above fold.
- Hermes input visible in normal and expanded modes.
- Advanced raw streams collapsed by default.

---

## Phase 13 — Implementation Order

Recommended order to avoid churn:

1. Phase 0: baseline tests and state inventory.
2. Phase 1: central state model and primary CTA.
3. Phase 2: Hermes pending/streaming trust fix.
4. Phase 4: dossier readiness checklist.
5. Phase 6: evidence drawer hierarchy.
6. Phase 7: agent lifecycle cards.
7. Phase 8: expanded chat layout.
8. Phase 9: left rail copy/layout polish.
9. Phase 10: voice mode clarification.
10. Phase 11: backend state contract hardening.
11. Final browser QA and regression pass.

Reasoning:

- CTA/state model is the foundation.
- Streaming trust is the most visible critical issue.
- Dossier readiness and evidence hierarchy unlock the decision journey.
- Layout polish should come after state/content structure stabilizes.

---

## Success Criteria

The remediation is complete when:

- A first-time user knows where to start within 3 seconds.
- The primary CTA always reflects the correct next action.
- Disabled actions always explain why.
- Hermes progress appears immediately after operator action.
- Hermes responses are structured and scannable.
- Evidence connects visibly to timeline, agents, Hermes answers, and dossier.
- The Dossier tab explains exactly what is complete and what is pending.
- Approval is clearly local synthetic safe-mode only.
- Expanded chat improves readability without destroying the cockpit layout.
- Voice mode clearly states browser-only, no telephony.
- Browser console remains clean.
- Automated tests pass.
- The product remains usable at 1366x768.

---

## High-level implementation checklist

- [ ] Add central product state contract.
- [ ] Add primary action resolver.
- [ ] Add disabled CTA reason UI.
- [ ] Add stage tracker.
- [ ] Add Hermes pre-token progress component.
- [ ] Harden stream lifecycle handling.
- [ ] Structure Hermes output sections.
- [ ] Add dossier readiness checklist.
- [ ] Split dossier readiness from final artifact.
- [ ] Add local synthetic approval gate copy.
- [ ] Upgrade evidence metadata model.
- [ ] Redesign evidence drawer summary-first.
- [ ] Add evidence highlighting and filters.
- [ ] Add agent lifecycle histories.
- [ ] Add evidence chips to agent cards.
- [ ] Redesign expanded chat layout with compact incident rail.
- [ ] Polish left rail chips and wrapping.
- [ ] Clarify voice controls and permission states.
- [ ] Strengthen backend state/evidence/agent/dossier contracts.
- [ ] Add unit/static tests.
- [ ] Add browser smoke verification.
- [ ] Update UX QA report with before/after screenshots and findings.
