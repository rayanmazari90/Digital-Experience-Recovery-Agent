# Product UX Rebuild Plan — Interactive Incident Command Product

## Product model

The Digital Experience Recovery Agent is an operator cockpit for an on-duty Digital Operations Lead at Apex Global Bank. The user is not watching a presentation; they are investigating and controlling a live incident workflow using Hermes as the agent runtime.

The product must make the operator able to:

1. See customer pain emerging.
2. Ask Hermes what is happening.
3. Inspect specialist sub-agent work.
4. Compare customer evidence with technical evidence.
5. Understand why CHG-1048 is suspected.
6. Review, revise, approve, or reject a local safe recovery dossier.

## New experience structure

The UI is rebuilt around five interactive workspaces:

1. Incident Intake
   - Starts as an operator console, not a landing page.
   - Shows one active incident: Login authentication degradation.
   - Shows customer impact preview, affected journey, estimated users, and the primary CTA: Ask Hermes to investigate.
   - Persistent Hermes command panel is visible immediately.

2. Hermes Investigation Workbench
   - After investigation begins, the main grid is left incident/journey, center evidence canvas, right Hermes chat + specialist agents.
   - The user can ask questions during the investigation.
   - Answers are grounded in the current incident state and evidence.

3. Sub-Agent Operations
   - Five specialist cards update as the state advances:
     - Digital Experience Supervisor
     - Customer Signal Agent
     - Observability Agent
     - Change Correlation Agent
     - Recovery & Communication Agent
   - Each card exposes status, current task, action/tool, finding, confidence, timestamp, and evidence link.

4. Evidence Canvas
   - Evidence is the central product surface.
   - Four lanes: Customer Signal, Technical Telemetry, Change Timeline, Recovery.
   - Cards open an evidence drawer with details.

5. Recovery Dossier and Human Gate
   - Dossier appears only after the investigation builds the case.
   - Includes summary, impact, evidence chain, root-cause hypothesis, confidence, recovery, communication, operational remainder, risks, and approval gate.
   - User can revise customer message, technical action wording, executive summary, and risk explanation.

## State machine

The frontend and backend share this state machine:

- disconnected
- ready_with_incident
- investigating.customer_signal
- investigating.observability
- investigating.change_correlation
- investigating.recovery_planning
- dossier_ready
- revising_dossier
- approval_required
- approved_local
- rejected_local
- error

Every visible region derives from this state:

- headline
- primary CTA
- subagent status cards
- evidence canvas emphasis
- Hermes chat suggestions
- dossier status
- approval safety gate

## Backend contract extension

Add local incident endpoints under `/api` while keeping existing health/run endpoints intact:

- `POST /api/incidents`
- `POST /api/incidents/{id}/investigate`
- `POST /api/incidents/{id}/ask`
- `GET /api/incidents/{id}/state`
- `GET /api/incidents/{id}/evidence`
- `GET /api/incidents/{id}/subagents`
- `POST /api/incidents/{id}/dossier/revise`
- `POST /api/incidents/{id}/approval`
- `GET /api/incidents/{id}/events`

The backend is the source of truth for incident state, evidence, sub-agent cards, dossier content, chat responses, and local approval status.

## Hermes adapter boundary

Hermes remains the reasoning engine and execution plane. The app exposes an adapter layer:

- `hermes_chat(request)`
- `hermes_delegate_task(task)`
- `hermes_get_profile_state()`
- `hermes_stream_events()`

For localhost demo data, deterministic Hermes-compatible adapter behavior may be used in backend code, but product copy must present it as a safe local incident scenario, not as a fake Hermes replacement.

## UI layout

Top bar:

- Product title
- Backend/Hermes/demo-data-safe-mode status
- Current incident severity
- Primary CTA

Main grid:

- Left: incident card, customer journey, impact metrics
- Center: evidence canvas + correlation view
- Right: persistent Hermes chat and specialist agents

Bottom:

- Dossier preview and approval gate once available

Advanced raw runtime streams remain hidden by default.

## Voice operator module

Visible optional module labeled: Browser voice demo — no telephony connected.

Capabilities:

- Browser speech input if available
- Text fallback through Hermes command panel
- Speak current situation
- Speak recovery dossier
- Simulate inbound caller question

The simulated caller asks: “I cannot receive my MFA code. Is my card still working?” Hermes answers with the incident communication policy: acknowledge issue, explain login/auth impact, state cards/ATM remain operational only if evidence supports it, avoid account-specific advice.

## Acceptance gates

The rebuild is done only when:

1. First-time user understands this is an incident recovery product within 3 seconds.
2. First action is obvious: Ask Hermes to investigate.
3. User can talk to Hermes.
4. Five specialist agents show meaningful state and findings.
5. Evidence cards are inspectable.
6. CHG-1048 suspicion is explainable.
7. Customer impact and technical evidence are visible together.
8. Dossier revision works.
9. Approval/rejection is clearly local safe-demo only.
10. Raw streams are hidden by default.
11. 1366x768 remains usable.
12. It feels like a working product, not a slide or passive guided animation.
