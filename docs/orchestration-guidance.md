# Hermes Orchestration Guidance

This document defines the Hermes-facing orchestration pattern for the Digital Experience Recovery Agent. Hermes remains the only LLM runtime. Specialized roles are implemented as bounded Hermes `delegate_task` leaf subagents with narrow toolsets and replayable JSON outputs.

## Parent supervisor rules

- Use Hermes `delegate_task` only; do not introduce external agent runtimes.
- Child subagents must be `role='leaf'`.
- Keep nested orchestration disabled for incident roles; the parent performs orchestration, approval routing, and final verification.
- Pass compact, explicit, synthetic-only context. Children have no conversation memory.
- Use each role's `allowed_toolsets` exactly.
- Never give children `memory`, `messaging`, `cronjob`, `browser`, `web`, `terminal`, or `delegation` toolsets.
- Children must not write memory, send messages, schedule jobs, mutate shared state, or perform side effects.
- Parent must validate child JSON and preserve evidence IDs for replay.

## Delegate sequence

1. `journey_analyst` and `fault_diagnostician` may run in parallel when both customer/journey and telemetry/change evidence exist.
2. `recovery_strategist` runs after at least one impact finding and one fault hypothesis are available, or returns an insufficient-evidence safe posture.
3. `evidence_synthesizer` runs last after child outputs, run events, evidence records, outcomes, and operator approval decisions are collected.

## Operator approval rules

The parent must ask for operator approval before executing or claiming any:

- rollback,
- deployment,
- traffic shift,
- feature disablement,
- cache purge,
- data mutation,
- customer notification,
- external message send,
- real-system access.

The parent must also ask when:

- a child sets `approval_required=true`,
- `recovery_strategist.operator_approval_request.required=true`,
- confidence is low for a side-effecting action,
- evidence appears non-synthetic,
- evidence includes potential PII requiring policy review.

The parent should not ask merely to continue analysis, summarize evidence, or draft non-sending internal text.

## Role contracts

The executable contract lives in `app/orchestration_guidance.py` and is exposed by:

```text
GET /orchestration/guidance
```

### fault_diagnostician

Receives:

- run/session IDs,
- scenario summary and affected journey,
- synthetic telemetry excerpts,
- recent synthetic changes and incident/change records,
- optional customer-signal summary,
- constraints, missing evidence, and safety scope.

Allowed toolsets:

```json
["file"]
```

Delegated when the parent needs fault hypotheses from telemetry, errors, deployments, dependency signals, or conflicting evidence.

Expected output includes:

- `primary_hypothesis`,
- `supporting_evidence`,
- `alternative_hypotheses`,
- `recommended_next_checks`,
- approval fields,
- replay notes.

### journey_analyst

Receives:

- run/session IDs,
- scenario journey definition,
- synthetic customer/contact/chatbot/IVR/app signals,
- timestamps and sanitized wording samples,
- safety scope and audit requirements.

Allowed toolsets:

```json
["file"]
```

Delegated when customer-facing signals need impact analysis, symptom clustering, journey mapping, or timeline interpretation.

Expected output includes:

- `journey`,
- `impact_summary`,
- `affected_steps`,
- `customer_language_themes`,
- `timeline_observations`,
- approval fields,
- replay notes.

### recovery_strategist

Receives:

- run/session IDs,
- `fault_diagnostician` output,
- `journey_analyst` output,
- synthetic runbook excerpts,
- confidence thresholds and approval policy,
- business impact summary and incident status.

Allowed toolsets:

```json
["file"]
```

Delegated after impact and fault findings exist, when the cockpit needs safe recovery options, risk tradeoffs, and approval wording.

Expected output includes:

- `recommended_strategy`,
- ranked `options`,
- `operator_approval_request`,
- internal/customer communication drafts,
- replay notes.

### evidence_synthesizer

Receives:

- run/session IDs,
- complete ordered event stream and evidence records,
- outputs from the other roles,
- operator approvals,
- outcomes and unresolved questions.

Allowed toolsets:

```json
["file"]
```

Delegated last to produce a replayable incident dossier and reconcile conflicts.

Expected output includes:

- executive summary,
- what happened,
- customer impact,
- likely cause,
- recommended/taken action,
- confidence,
- evidence table,
- approval log,
- conflicts and uncertainties,
- replay plan,
- final operator message.

## Final synthesis

The parent produces final synthesis by:

1. validating every child returned parseable JSON for the expected role,
2. checking evidence references against session history,
3. recording role outputs as run events or evidence/outcome payloads,
4. collecting operator approvals or denial records,
5. delegating `evidence_synthesizer`,
6. verifying the dossier directly against latest history,
7. reporting final findings while preserving uncertainty and approval boundaries.

No final synthesis may claim a side-effecting action occurred unless an approved outcome record supports it.
