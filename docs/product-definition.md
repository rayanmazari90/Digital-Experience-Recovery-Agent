# Product Definition: Digital Experience Recovery Agent

Status: product definition derived from frozen/current workspace corpus  
Workspace: `/Users/rayane/digital-experience-recovery-agent`  
Primary corpus sources:

- `.hermes.md`
- `SOUL.md`
- `docs/project-corpus-lock.md`
- `docs/source/extracted-text/Digital_Experience_Recovery_Agent_Solution.txt`
- `docs/source/extracted-text/Session1_IE220426.txt` through `Session12_IE180626.txt` where available
- `docs/source/inventory.json`

## 1. Product Vision

The Digital Experience Recovery Agent is a customer-experience and digital-channels recovery product for Apex Global Bank. Its purpose is to detect customer-impacting digital banking incidents earlier than infrastructure-only monitoring, connect customer symptoms to technical telemetry and recent operational changes, and produce a unified recovery dossier for human operators.

The product is not a generic chatbot. It is an incident diagnosis and service-recovery system for digital banking channels.

The product vision is:

> When digital banking customers experience MFA failures, login timeouts, high transaction latency, or other channel disruptions, the system should stitch together customer signals, observability data, change history, and recovery communications into one auditable, operator-approved recovery workflow.

The product should transform Apex Global Bank's incident lifecycle from reactive, siloed escalation into proactive, cross-channel service recovery.

The product must present itself through its own use: the final experience should demonstrate agentic diagnosis, tool selection, evidence aggregation, and human-in-the-loop recovery by running a realistic recovery scenario through the product itself, not merely describing the architecture in slides.

## 2. Product Positioning

### 2.1 Product Type

Customer experience and digital channels recovery product.

### 2.2 Not a Generic Chatbot

The system must not be positioned as a conversational assistant that answers arbitrary user questions. It must be positioned as an operational recovery system with:

- incident intake,
- customer signal clustering,
- journey-impact mapping,
- telemetry correlation,
- change correlation,
- recovery recommendation,
- communication drafting,
- human approval gates,
- audit-ready incident dossiers.

### 2.3 Single LLM Runtime Constraint

Hermes must be the single LLM runtime for the product.

Implementation implication:

- All LLM reasoning, agent-role prompting, tool selection, dossier synthesis, and communication drafting must route through Hermes.
- Specialized roles may be modeled as Hermes-managed prompts, tool flows, subagent/delegation workflows, or structured runtime modes, but they must not require a second independent LLM runtime.
- External systems may provide data through deterministic tools or APIs, but must not act as independent LLM agents unless explicitly waived.
- Any desired capability not supported or not configured in Hermes must be marked `Unspecified`, not invented.

## 3. Target Users

### 3.1 Primary Users

1. SRE Lead / Incident Commander
   - Owns technical incident response.
   - Reviews the unified incident dossier.
   - Approves or rejects technical recovery actions.
   - Needs fast, evidence-backed root-cause correlation.

2. Digital Operations Manager
   - Owns digital-channel reliability and customer impact.
   - Needs a cross-channel view of web, app, voice, chatbot, and support symptoms.
   - Uses the product to understand business impact and coordinate teams.

3. Contact Center Operations Lead
   - Owns frontline call center and IVR/chatbot response during incidents.
   - Needs accurate, consistent scripts that reduce call handling time and customer panic.

4. Customer Service Representative
   - Uses approved scripts and context to answer affected customers.
   - Needs clear descriptions of what is affected, what still works, and what customers should do.

5. Communications / Customer Experience Lead
   - Reviews public-facing or app-facing messages.
   - Ensures recovery communications are empathetic, factual, and non-technical.

### 3.2 Secondary Users

1. Change Manager
   - Reviews whether a recent change is implicated in a customer-impacting incident.

2. Platform / DevOps Engineer
   - Provides or validates rollback plans, service identifiers, and technical remediations.

3. Compliance / Risk Reviewer
   - Reviews audit records, approval gates, PII controls, and customer communications.

4. Product Owner for Digital Channels
   - Uses incident learning to improve product journeys such as Login/Authentication, Fund Transfer, Remote Check Deposit, Account Balance View, and Card Payment.

## 4. Primary User Journeys

### Journey 1: Detect Customer-Impacting Digital Incident

Primary user: Digital Operations Manager

Trigger:

- A spike appears in customer complaints, contact-center transcripts, chatbot sessions, app errors, app-store reviews, or social monitoring.

Flow:

1. Customer-side signals enter the system through approved data sources.
2. Customer Signal Agent role clusters symptoms across channels.
3. The system maps symptoms to a core banking journey.
4. The system estimates affected volume and acceleration timestamp.
5. Digital Experience Supervisor role determines whether this is a meaningful incident pattern.
6. The system opens an incident dossier if the event appears systemic.

Expected output:

- Journey affected.
- Symptom pattern.
- Impact volume estimate.
- Complaint acceleration timestamp.
- Confidence level.
- Evidence references.

### Journey 2: Correlate Customer Symptoms with Technical Telemetry

Primary user: SRE Lead / Incident Commander

Trigger:

- A validated customer-impact pattern exists.

Flow:

1. Supervisor passes the affected journey and timestamp window to the Observability Agent role.
2. Observability Agent queries telemetry sources through deterministic tools.
3. The product retrieves or accepts service health evidence such as latency, HTTP error rate, endpoint failures, dependency issues, and active incidents.
4. The product correlates telemetry timestamps against the customer symptom acceleration curve.
5. The product rejects unsupported conclusions if telemetry evidence is weak.

Expected output:

- Affected service or endpoint.
- Latency and error-rate deltas.
- Timestamp correlation.
- Incident and service identifiers.
- Confidence level.
- Manual-review flag when evidence is insufficient.

### Journey 3: Identify Likely Root-Cause Change

Primary user: Change Manager / Platform Engineer

Trigger:

- Observability evidence identifies affected service components.

Flow:

1. Supervisor sends the service identifiers and incident window to the Change Correlation Agent role.
2. Change Correlation Agent queries recent changes through deterministic tools or synthetic demo data.
3. The product ranks changes using time distance and structural proximity.
4. The product returns a suspected change with a risk correlation score.
5. Low-confidence or conflicting evidence is escalated to human review.

Expected output:

- Change Request ID or deployment ID.
- Component name.
- Deployment timestamp.
- Author or owner if present in approved data.
- Correlation score from 0.0 to 1.0.
- Rationale and evidence.

### Journey 4: Produce Recovery Dossier and Approval Request

Primary user: SRE Lead / Incident Commander

Trigger:

- Root-cause candidate exists or system has enough evidence to propose recovery options.

Flow:

1. Recovery & Communication Agent role receives diagnostic packet.
2. It drafts a technical remediation plan.
3. It drafts customer-facing and frontline communication scripts.
4. Supervisor combines all outputs into a single Incident Response Dossier.
5. The product halts before destructive execution or public communication.
6. Human operator reviews and approves, rejects, or edits the proposed action.

Expected output:

- Incident identifier.
- Impact summary.
- Customer journey affected.
- Technical root-cause hypothesis.
- Recommended technical action.
- Contact center script.
- Mobile app / digital-channel message.
- Confidence and evidence trace.
- Explicit approval state: `Awaiting Human Approval`, `Approved`, `Rejected`, or `Needs More Evidence`.

### Journey 5: Communicate Consistently Across Channels

Primary user: Contact Center Operations Lead / Communications Lead

Trigger:

- A recovery dossier has approved communication drafts.

Flow:

1. Contact Center Operations Lead reviews the frontline script.
2. Communications Lead reviews customer-facing language.
3. The system clarifies affected and unaffected services.
4. Approved scripts are prepared for IVR, chatbot, app banner, or push notification.
5. Actual publishing requires explicit approval and configured integration.

Expected output:

- Approved frontline script.
- Approved mobile/digital notification.
- Affected services.
- Unaffected services.
- Timestamp and approver.
- Channel-specific publication status.

### Journey 6: Demonstrate the Product Through Its Own Use

Primary user: Course evaluator / mentor / project stakeholder

Trigger:

- Final presentation or demo.

Flow:

1. The presenter starts with the synthetic IAM Gateway failure scenario from the project corpus.
2. The Hermes-backed product ingests synthetic customer complaints and synthetic telemetry/change records.
3. Hermes orchestrates the agent roles and tool calls.
4. The system generates the recovery dossier live or from a reproducible recorded run.
5. The presenter uses the dossier to explain problem framing, agent goals, architecture, tool selection, autonomy, guardrails, and measurable value.

Expected output:

- The product demonstrates the course concepts by operating as the case study.
- The demo shows what the agent decides versus what deterministic tools execute.
- The demo ends at human approval, not automatic rollback or customer notification.

## 5. Recovery Scenarios

### Scenario 1: MFA / Authentication Failure

Source basis: project brief and MVP simulation flow.

Symptoms:

- Customers report that MFA codes are not arriving.
- Mobile app gets stuck on verification.
- Login/authentication complaint volume spikes.

Likely signals:

- Contact-center transcript clusters.
- Chatbot session clusters.
- Mobile app error streams.
- Auth API gateway latency.
- HTTP 504 Gateway Timeout increase.
- Recent IAM gateway change.

Required product response:

- Detect Login/Authentication as affected journey.
- Correlate customer spike with auth gateway telemetry.
- Identify recent IAM gateway patch or change candidate.
- Draft rollback recommendation.
- Draft contact center and mobile app communications.
- Halt for human approval.

### Scenario 2: Severe Transaction Latency

Source basis: project brief references severe latency during core transaction workflows.

Symptoms:

- Customers report slow or failed fund transfer or transaction workflows.
- Contact center receives repetitive complaints about delays.
- App or web journey metrics show degraded completion.

Likely signals:

- Customer complaint text.
- App latency metrics.
- API gateway or backend service latency.
- Database locking metrics.
- Recent deployment or database migration.

Required product response:

- Map symptom to affected journey: Fund Transfer, Account Balance View, Card Payment, or another supported journey.
- Correlate customer reports with telemetry time window.
- Rank recent changes.
- Prepare internal remediation options.
- Draft channel-specific customer messaging.
- Halt for human approval.

### Scenario 3: Cross-Channel Incident Migration

Source basis: project brief describes lack of cross-channel context sharing across web, app, and voice.

Symptoms:

- Customer starts in online banking, switches to mobile app, then calls helpdesk.
- Each channel currently treats the issue independently.

Likely signals:

- Web journey failure.
- Mobile app retry pattern.
- Contact-center transcript.
- Helpdesk ticket or ServiceNow incident.

Required product response:

- Stitch a unified incident timeline.
- Show customer journey movement across web, app, and voice.
- Prevent duplicate or inconsistent triage.
- Give frontline agents the same impact narrative as technical operators.

### Scenario 4: Contact Center Spike Overload

Source basis: project brief targets 45% deflection via multi-channel scripting and IVR/chatbot updates.

Symptoms:

- Sudden call volume spike.
- Repetitive symptom patterns.
- Queue abandonment.
- Inconsistent support responses.

Likely signals:

- IVR transcripts.
- Contact center logs.
- Chatbot sessions.
- Incident status data.

Required product response:

- Cluster repeated symptoms.
- Create uniform frontline scripts.
- Identify unaffected services customers can still use.
- Prepare IVR/chatbot/app text updates.
- Require approval before publication.

### Scenario 5: Low-Confidence or Conflicting Evidence

Source basis: project brief risk guardrails.

Symptoms:

- Customer complaints spike, but telemetry does not clearly match.
- Datadog/Dynatrace shows an alert, but no matching change is found.
- A change exists but correlation is weak.

Required product response:

- Refuse to overclaim.
- Mark confidence as low.
- Route to manual SRE expert review.
- Preserve evidence and uncertainty in the dossier.

## 6. Measurable Success Criteria

### 6.1 Business Success Metrics

The product must be evaluated against the business metrics in the project corpus.

| Metric | Baseline | Target |
|---|---:|---:|
| Mean Time to Resolution for tier-1 digital incidents | 142 minutes | Under 15 minutes through change correlation and rollback recommendation |
| Contact center spike overload | 100% manual triage with high abandonment and inconsistent scripts | 45% deflection through multi-channel scripting and uniform IVR/chatbot updates |
| Cross-channel context sharing | Zero independent tracking across web, app, and voice | Unified incident timeline connecting technical data to customer journeys |
| Customer sentiment during incident weeks | -22% App Store rating drop | Stabilized sentiment through rapid, proactive, transparent notifications |

### 6.2 Product Operating Metrics

Implementation-ready product metrics:

1. Detection latency
   - Time from complaint acceleration to incident candidate creation.
   - Target for MVP demo: under 60 seconds on synthetic data.

2. Correlation completeness
   - Percentage of dossiers with customer signal, telemetry evidence, and change evidence.
   - Target for MVP demo: 100% for supported synthetic scenarios.

3. Evidence specificity
   - Dossiers must include timestamps, service/endpoint IDs, metric deltas, and change IDs when data exists.
   - Target: no root-cause assertion without evidence reference.

4. Approval safety
   - Destructive technical actions and public/customer communications must never execute without approval.
   - Target: 100% of such actions stop at `Awaiting Human Approval` unless a human approves.

5. Script consistency
   - Contact-center and mobile-app scripts must identify affected services and unaffected services.
   - Target: 100% of generated scripts include both where data permits.

6. Confidence handling
   - Low-confidence or conflicting evidence must be routed to manual review.
   - Target: 100% of unsupported correlation cases flag uncertainty rather than inventing a cause.

7. Privacy masking
   - Customer identifiers, account IDs, balances, card numbers, and names must be masked before LLM reasoning.
   - Target: 100% masking in any real-data mode; synthetic data may use clearly synthetic identifiers.

8. Hermes runtime compliance
   - All LLM reasoning must be executed through Hermes.
   - Target: 100% of LLM calls use Hermes as the runtime.

## 7. Non-Goals

The product must not attempt the following in the initial implementation-ready scope:

1. Generic chatbot behavior
   - It must not answer arbitrary customer or employee questions unrelated to digital incident recovery.

2. Autonomous rollback execution
   - It may draft rollback commands or remediation steps, but must not execute destructive actions without human approval.

3. Autonomous customer notification
   - It may draft scripts and notifications, but must not publish customer-facing messages without explicit approval and configured integrations.

4. Real banking system integration without approval
   - Datadog, Dynatrace, ServiceNow, GitHub, CI/CD, app telemetry, contact-center systems, IVR, chatbot, and push channels must remain synthetic or mocked until credentials, data policy, and approval are provided.

5. Real customer data ingestion without policy
   - No raw real customer transcripts, account data, card data, balances, or identifiers should be ingested until privacy and retention requirements are defined.

6. Multi-runtime LLM architecture
   - The product must not depend on multiple LLM runtimes, external agent runtimes, or SaaS agent frameworks. Hermes is the single LLM runtime.

7. Unsupported Hermes feature invention
   - If Hermes capability is not configured or documented in the current workspace, mark it `Unspecified` rather than claiming support.

8. Full production deployment
   - Remote API/dashboard exposure, high availability, enterprise SSO, and production monitoring are not in scope unless explicitly added to the corpus.

9. RLHF or fine-tuning implementation
   - The project brief mentions future learning from human input. Actual RLHF/fine-tuning support through Hermes is `Unspecified` in the current corpus and must not be promised.

## 8. Required Integrations

### 8.1 Runtime and Orchestration

| Integration | Required? | Product Role | Status from Corpus |
|---|---:|---|---|
| Hermes Agent | Yes | Single LLM runtime for all reasoning, prompts, tool selection, and dossier generation | Required by current instruction and profile setup |
| Hermes profile `digital-recovery` | Yes | Isolation of config, memory, skills, state, sessions, secrets, and cron | Configured in workspace setup |
| Hermes Docker terminal backend | Yes for development baseline | Safe isolated execution environment | Configured in profile setup |
| Hermes API server | Conditional | Possible local interface for product or demo | Configured localhost in profile env, but product exposure design is pending |
| Hermes dashboard | Optional / unspecified | Possible operator UI | Remote dashboard auth/exposure is pending; dashboard UX support for this product is unspecified |
| Hermes delegation / subagents | Conditional | Model bounded worker roles under Hermes using `delegate_task` leaf subagents | Implemented as Hermes-facing guidance/prompts in `app/orchestration_guidance.py`; runtime remains synthetic/dev-only until real integrations are approved |
| Hermes memory | Conditional | Store project context or learning if approved | Enabled with write approval; product memory use policy is pending |
| Hermes voice capabilities | Conditional | Voice-first operator experience and spoken response boundary | Documented Hermes capabilities are gateway voice-message transcription, `/voice on`, `/voice tts`, and Hermes TTS providers. Browser microphone/speaker controls in the product shell are implemented only as a custom app-side bridge and are labeled as such. Direct telephony is not implemented. |

### 8.2 Customer Signal Inputs

| Integration | Required for Concept | MVP Mode | Production Mode | Notes |
|---|---:|---|---|---|
| Contact center transcripts | Yes | Synthetic CSV/text | Approved transcript feed with masking | Must tokenize PII before LLM reasoning. |
| IVR logs | Yes | Synthetic logs | Approved IVR data/API | Needed for call-volume spike and script update workflows. |
| Chatbot sessions | Yes | Synthetic JSON/CSV | Approved chatbot transcript export/API | Required for cross-channel symptom clustering. |
| Mobile app error streams | Yes | Synthetic JSON | Approved app telemetry stream | Required to connect customer journey failures to technical incidents. |
| App-store reviews / social monitoring | Optional | Synthetic examples | Approved external/social feed | External monitoring scope and privacy policy are pending. |

### 8.3 Observability and Incident Inputs

| Integration | Required for Concept | MVP Mode | Production Mode | Notes |
|---|---:|---|---|---|
| Datadog | Yes | Synthetic `datadog_metrics.json` | API integration if approved | Corpus references Datadog telemetry queries. |
| Dynatrace | Yes | Synthetic telemetry | API integration if approved | Corpus references Dynatrace as active APM. |
| ServiceNow incidents / CMDB | Yes | Synthetic `servicenow_incidents.json` | Table API integration if approved | Corpus references ServiceNow incidents and CMDB. |
| Network logs | Optional for MVP | Synthetic or omitted | Approved log source | Exact provider unspecified. |
| API gateway logs | Yes for auth/latency scenarios | Synthetic metrics JSON | Approved log/metrics source | Required for MFA/auth gateway incident. |

### 8.4 Change and Recovery Inputs

| Integration | Required for Concept | MVP Mode | Production Mode | Notes |
|---|---:|---|---|---|
| CI/CD deployment logs | Yes | Synthetic `recent_changes.json` | Approved CI/CD API | Needed for change correlation. |
| GitHub repository commit logs | Yes in brief | Synthetic or local sample | Approved GitHub API/repo access | Real repo access must be approved. |
| Infrastructure-as-code repo history | Optional for MVP | Synthetic examples | Approved repo access | Exact platform unspecified. |
| ServiceNow Change Requests | Yes | Synthetic CHG records | ServiceNow Table API if approved | Needed for CHG-1048-style correlation. |
| Runbook library | Yes for recovery plans | Synthetic markdown/JSON runbooks | Approved internal runbooks | Needed by `generate_mitigation_plan`. |

### 8.5 Communication Outputs

| Integration | Required for Concept | MVP Mode | Production Mode | Notes |
|---|---:|---|---|---|
| Contact-center script export | Yes | Markdown/text dossier | Approved contact-center platform integration | Publishing requires approval. |
| IVR update | Optional for MVP | Draft only | Approved IVR API/webhook | Must require approval. |
| Chatbot update | Optional for MVP | Draft only | Approved chatbot platform integration | Must require approval. |
| Mobile app banner / push notification | Yes conceptually | Draft only | Approved mobile comms platform | Must require approval. |
| SRE dashboard approval | Yes conceptually | Local document or API-server endpoint | Approved operator UI | Current UI implementation is unspecified. |

### 8.6 Unsupported or Unspecified Capabilities

The following must be explicitly marked `Unspecified` until confirmed:

- Direct Hermes-native Datadog connector.
- Direct Hermes-native Dynatrace connector.
- Direct Hermes-native ServiceNow connector.
- Direct Hermes-native IVR publishing connector.
- Direct Hermes-native mobile push notification connector.
- Direct Hermes-native customer support platform connector.
- Product-specific dashboard components for SRE approval.
- Production-grade audit log backend.
- Production SSO / RBAC integration.
- RLHF or fine-tuning pipeline inside Hermes.
- Accessibility capabilities of any future dashboard UI.

The product may define deterministic tool interfaces for these integrations, but it must not claim the integrations exist until implemented or configured.

## 9. Trust, Privacy, Security, and Accessibility Principles

### 9.1 Trust Principles

1. Evidence before conclusion
   - Every diagnosis must cite concrete evidence: timestamps, metric deltas, endpoint IDs, change IDs, or transcript clusters.

2. Confidence is mandatory
   - Every root-cause hypothesis must include confidence and rationale.

3. Low confidence routes to humans
   - If evidence conflicts or is incomplete, the product must route to manual SRE review.

4. Tools execute; agents decide
   - Course materials and project brief emphasize the separation between agent decision-making and tool execution.

5. Human approval gates are non-negotiable
   - Rollbacks, customer notifications, IVR updates, chatbot updates, and other external side effects require explicit approval.

6. Auditability by design
   - Every incident dossier must preserve input sources, decisions, tool calls, generated outputs, approval state, and final action.

### 9.2 Privacy Principles

1. PII minimization
   - Use only the minimum customer data needed for symptom clustering and journey impact analysis.

2. Tokenization before LLM reasoning
   - Names, account IDs, card numbers, account balances, and other identifiers must be masked before reaching Hermes.

3. Synthetic data first
   - Until data policy is approved, all demo and development scenarios must use synthetic data.

4. No unapproved customer data persistence
   - Do not store raw transcripts, recordings, account data, or customer identifiers without retention and access-control policy.

5. Memory governance
   - Hermes memory is enabled with write approval, but product memory writes must not store sensitive customer data.

### 9.3 Security Principles

1. Least privilege
   - Tool credentials should only permit necessary read/write actions.

2. No destructive credentials in reasoning layer
   - The LLM runtime must not hold credentials that can execute rollback or customer notification without separate approval.

3. Manual approvals for dangerous actions
   - The Hermes profile is configured for manual approvals; product workflow must preserve that posture.

4. Prompt injection resistance
   - Customer text, social messages, chatbot transcripts, and logs are untrusted input. They must never override system policies.

5. Website and internal-system controls
   - Website blocklist is enabled, but domain list remains pending. Until populated or waived, external browsing against sensitive systems is not allowed.

6. Local-first API posture
   - API server is configured for localhost. Remote exposure requires explicit design, bearer key protection, dashboard auth, and TLS/reverse proxy decisions. The backend shell now includes optional API-key auth, explicit CORS, security headers, local audit logs, and retention pruning for localhost/demo hardening; production SSO/RBAC remains unsupported.

### 9.4 Accessibility Principles

Accessibility requirements are not specified in the current corpus. Therefore dashboard or UI accessibility capabilities must be marked `Unspecified` until a UI is designed.

Implementation-ready accessibility principles for future UI work:

1. Incident dossiers must be readable as structured text, not only visual charts.
2. Critical status must not rely on color alone.
3. Operator approval controls must have clear labels and confirmation states.
4. Generated scripts must use plain language suitable for frontline agents.
5. Customer-facing messages must be concise, non-technical, and anxiety-reducing.
6. Any dashboard must support keyboard navigation and screen-reader-friendly structure before production use.

## 10. Product Architecture Definition

### 10.1 Runtime Architecture

The implementation must use Hermes as the single LLM runtime.

Canonical runtime model:

1. Hermes receives a structured incident input or synthetic scenario.
2. Hermes runs the Supervisor role.
3. Supervisor invokes or simulates worker-role steps through Hermes-managed prompts and deterministic tools.
4. Deterministic tools retrieve, normalize, or mock data.
5. Hermes synthesizes the Incident Response Dossier.
6. Hermes halts before destructive execution or customer-facing communication.
7. Human operator approves, rejects, or asks for more evidence.

### 10.2 Required Agent Roles

The product definition keeps the five roles from the project brief, but binds them to Hermes rather than separate runtimes.

| Role | Responsibility | Hermes Runtime Constraint |
|---|---|---|
| Digital Experience Supervisor | Orchestrates incident flow, state, routing, synthesis, and approval barriers | Must run through Hermes |
| Customer Signal Agent | Clusters customer-side symptoms and maps affected journeys | Must run through Hermes; input must be masked |
| Observability Agent | Queries or reads telemetry evidence and reports hard metrics | Must run through Hermes for reasoning; tool/data access deterministic |
| Change Correlation Agent | Correlates technical symptoms with recent changes | Must run through Hermes for reasoning; tool/data access deterministic |
| Recovery & Communication Agent | Drafts remediation plan and communication scripts | Must run through Hermes; must not publish without approval |

### 10.3 Required Data Objects

Implementation should define these records before product code begins.

#### CustomerSignalCluster

- `cluster_id`
- `source_channels`
- `journey_affected`
- `symptom_pattern`
- `sample_masked_phrases`
- `volume_baseline`
- `volume_current`
- `volume_delta_percent`
- `acceleration_start_time`
- `confidence`

#### TelemetryFinding

- `finding_id`
- `service_name`
- `endpoint`
- `metric_name`
- `baseline_value`
- `current_value`
- `delta_percent`
- `time_window_start`
- `time_window_end`
- `source_system`
- `confidence`

#### ChangeCandidate

- `change_id`
- `component_name`
- `change_type`
- `deployed_at`
- `owner_or_author`
- `time_distance_minutes`
- `structural_proximity`
- `correlation_score`
- `evidence`

#### RecoveryRecommendation

- `recommendation_id`
- `incident_id`
- `technical_action_type`
- `draft_command_or_steps`
- `risk_level`
- `requires_human_approval`
- `approval_status`
- `rollback_or_reversal_path`

#### CommunicationDraft

- `draft_id`
- `incident_id`
- `audience`
- `channel`
- `message_text`
- `affected_services`
- `unaffected_services`
- `approval_status`

#### IncidentResponseDossier

- `incident_id`
- `status`
- `created_at`
- `customer_impact_summary`
- `customer_signal_clusters`
- `telemetry_findings`
- `change_candidates`
- `recommended_actions`
- `communication_drafts`
- `confidence_summary`
- `human_approval_state`
- `audit_trail`

## 11. Why the Product Should Present Itself Through Its Own Use

The course corpus emphasizes agent goals, prompt quality, agentic architecture, realistic tools, agentic thinking, autonomy, and the distinction between what agents decide and what tools execute. The project brief also includes a concrete live-incident walkthrough and final unified incident dossier.

Therefore, the product should present itself through its own use for four reasons:

1. It proves the product is not just a concept
   - A live or reproducible synthetic incident run shows that the architecture can produce a useful recovery dossier.

2. It demonstrates agentic behavior
   - The demo can show perception, reasoning, tool use, correlation, synthesis, and human approval.

3. It makes the business value visible
   - The evaluator can see how MTTR reduction, contact-center deflection, and cross-channel context sharing would happen.

4. It reinforces safety and trust
   - The demo can show that the system stops before rollback or public notification and requires human approval.

Recommended presentation format:

1. Start with the problem: disconnected customer impact and technical telemetry.
2. Feed the synthetic IAM Gateway failure scenario into the Hermes-backed product.
3. Show customer symptom clustering.
4. Show telemetry correlation.
5. Show change correlation to CHG-1048.
6. Show generated recovery and communication drafts.
7. Show the human approval gate.
8. End with measurable success criteria and the guardrails that prevent unsafe automation.

## 12. Open Questions and Explicit Unspecified Items

The following remain unresolved in the current corpus and must not be invented:

1. Is Session 11 waived or still pending?
2. What is the formal grading rubric or final submission format?
3. Is the project brief the authoritative and final scope?
4. Is the data policy synthetic-only, anonymized, or approved real data?
5. Which internal/sensitive domains must be blocklisted?
6. Will API/dashboard access remain localhost-only?
7. What UI, if any, will be used for the SRE approval dashboard?
8. Which enterprise platforms are actually available for integration?
9. Are Datadog, Dynatrace, ServiceNow, GitHub, CI/CD, IVR, chatbot, and push notification integrations required as real APIs or acceptable as synthetic mocks?
10. What audit log retention policy is required?
11. What accessibility standard applies to any UI?
12. Does Hermes support any required connector directly, or must each connector be implemented as a deterministic project tool?

Until resolved, these items must remain marked `Unspecified` in implementation documents.

## 13. Implementation Readiness Summary

This product definition is implementation-ready at the requirements level, but not yet a build authorization.

Allowed next artifacts while the build gate remains closed:

- requirements extraction matrix,
- data contract specification,
- synthetic dataset specification,
- tool interface specification,
- incident dossier schema,
- approval workflow specification,
- risk and guardrail register,
- course-to-product alignment matrix.

Not allowed until build gate opens:

- product code,
- external integrations,
- real customer data ingestion,
- remote dashboard/API exposure,
- customer-facing communications,
- autonomous rollback execution.
