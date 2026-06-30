# Project Corpus Lock

Generated: 2026-06-26 20:16:33 CEST  
Updated: 2026-06-26 after project brief and course decks were copied into the workspace

Workspace searched: `/Users/rayane/digital-experience-recovery-agent`  
Hermes profile context: `digital-recovery`

## Purpose

This document freezes the currently observed project corpus before implementation begins. It identifies what materials are available, what is missing or pending, and what constraints those gaps create.

Implementation should not begin until the corpus is frozen or the missing materials are explicitly waived by Rayane, the mentor, or the designated project owner.

## Search and Copy Method

The workspace was searched recursively from:

`/Users/rayane/digital-experience-recovery-agent`

Rayane provided one project brief `.docx` file and eleven course/session `.pptx` files. These files were copied into the project workspace so the project does not depend on WhatsApp temp storage or the Downloads folder.

Copied source locations:

- Project brief source: `/Users/rayane/Library/Containers/net.whatsapp.WhatsApp/Data/tmp/documents/3FEAFD4C-D289-4A71-BBCE-934F66A324E7/Digital_Experience_Recovery_Agent_Solution.docx`
- Course material sources: `/Users/rayane/Downloads/Session*.pptx`

Workspace corpus locations:

- Project brief: `docs/source/project-brief/`
- Course materials: `docs/source/course-materials/`
- Extracted text: `docs/source/extracted-text/`
- Machine-readable inventory: `docs/source/inventory.json`

All provided source files were found and copied. No missing source files were reported during the copy step.

## 1. Project Documents Currently Available

| Document | Path | Status | Role | Notes |
|---|---|---:|---|---|
| Hermes project context | `.hermes.md` | Available | Project operating context | Defines mission, operating boundaries, engineering defaults, product intent, initial implementation constraints, and open setup items. |
| Profile SOUL | `SOUL.md` | Available | Profile identity/governance | Defines the dedicated profile purpose, principles, default behavior, governance rules, and current setup assumptions. |
| Project brief / solution blueprint | `docs/source/project-brief/Digital_Experience_Recovery_Agent_Solution.docx` | Available | Primary project brief | Defines the Digital Experience Recovery Agent for Apex Global Bank, Challenge 2: Customer Experience & Digital Channels. |
| Project brief extracted text | `docs/source/extracted-text/Digital_Experience_Recovery_Agent_Solution.txt` | Available | Searchable text copy | Extracted from the `.docx` for easier review. |
| Corpus lock | `docs/project-corpus-lock.md` | Available | Corpus inventory / build gate | This document records the current corpus state and gates implementation. |
| Source inventory | `docs/source/inventory.json` | Available | File audit metadata | Contains source path, destination path, size, checksum, slide counts, and excerpts. |

### Project Brief Summary

The project brief describes:

- Project title: Digital Experience Recovery Agent.
- Context: Apex Global Bank — Challenge 2: Customer Experience & Digital Channels.
- Problem: Customer-facing digital banking failures are disconnected from backend telemetry and operational data.
- Pain points:
  - Siloed customer-service and technical operations data.
  - 37% increase in critical complaints around MFA failures and transaction latency.
  - Contact center overload during incidents.
  - Lack of predictive failure detection and cross-channel context sharing.
- Target outcomes:
  - Reduce MTTR for tier-1 digital incidents from 142 minutes to under 15 minutes.
  - Deflect 45% of contact-center spike overload via multi-channel scripts and IVR/chatbot updates.
  - Create unified incident timelines that connect customer journeys to technical events.
  - Stabilize customer sentiment through proactive transparent notifications.
- Proposed architecture:
  - Hierarchical supervisor-worker multi-agent architecture.
  - Digital Experience Supervisor Agent.
  - Customer Signal Agent.
  - Observability Agent.
  - Change Correlation Agent.
  - Recovery & Communication Agent.
- Tooling concepts:
  - `fetch_customer_signals`
  - `query_observability_metrics`
  - `fetch_recent_changes`
  - `generate_mitigation_plan`
- Governance principle: strict separation between cognitive agent decisions and programmatic tool execution.

## 2. Course / Session Materials Currently Available

The following course decks are now available in the workspace.

| Session | File | Workspace Path | Slides | First-slide / extracted topic |
|---:|---|---|---:|---|
| 1 | `Session1_IE220426.pptx` | `docs/source/course-materials/Session1_IE220426.pptx` | 17 | Agentic AI for IT — Introduction to Agentic AI |
| 2 | `Session2_IE230426.pptx` | `docs/source/course-materials/Session2_IE230426.pptx` | 25 | Introduction to Agentic AI — Part 2 |
| 3 | `Session3_IE290426.pptx` | `docs/source/course-materials/Session3_IE290426.pptx` | 24 | Market Vision, Strategy & Insights |
| 4 | `Session4_IE060526.pptx` | `docs/source/course-materials/Session4_IE060526.pptx` | 20 | Architecture, Frameworks and Tools |
| 5 | `Session5_IE070526_Students.pptx` | `docs/source/course-materials/Session5_IE070526_Students.pptx` | 14 | Prompting & Security |
| 6 | `Session6_IE130526.pptx` | `docs/source/course-materials/Session6_IE130526.pptx` | 23 | Enterprise Service Management |
| 7 | `Session7_IE210526.pptx` | `docs/source/course-materials/Session7_IE210526.pptx` | 14 | Operations Management |
| 8 | `Session8_IE270526.pptx` | `docs/source/course-materials/Session8_IE270526.pptx` | 10 | Recap / Knowledge Assessment |
| 9 | `Session9_IE030626.pptx` | `docs/source/course-materials/Session9_IE030626.pptx` | 14 | Creating Your First Agent |
| 10 | `Session10_IE100626.pptx` | `docs/source/course-materials/Session10_IE100626.pptx` | 13 | Creating Your First Agent (2/2) |
| 12 | `Session12_IE180626.pptx` | `docs/source/course-materials/Session12_IE180626.pptx` | 9 | Agentic AI for IT |

Searchable extracted text files were created for each course deck under:

`docs/source/extracted-text/`

### Course Coverage Observed

The available course corpus appears to cover:

- Agentic AI foundations.
- Traditional AI vs. Agentic AI.
- Market vision and strategy.
- Agent architecture, frameworks, tools, and multi-agent systems.
- Prompting and security.
- Enterprise Service Management.
- IT Operations Management.
- Mid-course recap / knowledge assessment.
- Building a first agent and first tool.

## 3. Expected Documents Missing or Pending

The corpus is now much stronger, but several expected materials remain missing or pending.

| Expected Material | Current Status | Why It Matters |
|---|---:|---|
| Session 11 deck/materials | Missing / not provided | Sessions 1-10 and 12 are present; Session 11 is absent. If Session 11 contained final-project guidance, integration patterns, evaluation criteria, or implementation guardrails, the build plan could miss important requirements. |
| Formal assignment rubric | Missing | Needed to determine grading priorities, required structure, deadline constraints, and mandatory artifacts. |
| Final submission instructions | Missing | Needed to know expected format, length, demo requirements, allowed tooling, and deadline. |
| Mentor notes as a tracked document | Missing | Mentor guidance has been provided in conversation. It should be summarized into the repo or linked as a decision record to avoid relying on chat history. |
| Product requirements document separate from solution blueprint | Missing | The project brief is a solution blueprint, but a PRD would define functional requirements, non-functional requirements, user roles, acceptance criteria, and release boundaries more explicitly. |
| Domain model / terminology glossary | Missing | Needed to prevent inconsistent naming for incidents, complaints, channels, cases, recovery actions, customers, agents, SLAs, and outcomes. |
| Omnichannel source inventory | Partially implied, not finalized | The brief references IVR, chat, social, mobile app errors, chatbot sessions, APM, ServiceNow, Datadog, Dynatrace, CI/CD, and GitHub. Actual in-scope sources need to be selected for the deliverable. |
| Data availability statement | Missing | Needed to know whether real, anonymized, synthetic, or sample data may be used. |
| PII / privacy / retention policy | Missing | Needed before handling real customer information, contact-center transcripts, app events, or support logs. |
| Security-sensitive domain list | Pending | Website blocklist is enabled in the Hermes profile, but the actual blocked domains list is empty. |
| API/dashboard exposure decision | Pending | API server is configured for localhost. Remote exposure requires auth, TLS/reverse proxy, and explicit approval. |
| Evaluation framework | Missing | Needed to evaluate diagnosis quality, classification quality, recommendation safety, and recovery success. |
| Architecture decision record template | Missing | Needed if the project expects formal ADRs for major design choices. |
| Build plan / milestone plan | Missing | Needed to sequence corpus review, requirements extraction, design, data modeling, implementation, testing, and demo preparation. |

## 4. Constraints Created by Missing Materials

Because the corpus is still incomplete, the following constraints apply.

### Scope Constraint

The project brief is now available and gives a strong target architecture and use case, but the exact deliverable scope is still not locked. It is unclear whether the expected output is a conceptual blueprint, a demo prototype, a runnable agent, a presentation, a written report, or some combination.

### Session 11 Constraint

The course sequence has Sessions 1-10 and 12, but no Session 11. Until Session 11 is added or waived, there is a risk that an important late-course requirement is missing.

### Rubric Constraint

The assignment rubric and final submission instructions are still missing. Without them, implementation might optimize for technical completeness while missing grading criteria such as presentation structure, conceptual mapping to course frameworks, or explicit security discussion.

### Implementation Constraint

Product code should still not be built yet. The project brief is solution-oriented and includes production-grade agent/tool concepts, but the course/rubric gaps mean implementation could encode premature assumptions.

### Data Constraint

No approved datasets or sample inputs are present. The project must not assume access to real customer data, contact-center transcripts, APM logs, ServiceNow records, GitHub commits, or CI/CD events. Any examples should remain synthetic until explicit data permission and handling rules are provided.

### Privacy and Compliance Constraint

The brief references customer-side signals, transcripts, mobile app error streams, chatbot sessions, and sentiment data. These could contain PII or sensitive banking information. No retention, redaction, minimization, access-control, or audit policy exists yet.

### Architecture Constraint

The brief proposes a hierarchical supervisor-worker architecture with five agents. Course materials also discuss agent architecture, frameworks, tools, prompting, security, ESM, and ITOps. The implementation should not choose specific frameworks, databases, queues, or integrations until requirements are extracted from both the brief and course materials.

### Security Constraint

The project brief includes potentially sensitive banking and operational integrations: Datadog, Dynatrace, ServiceNow, CI/CD, GitHub, app telemetry, contact-center data, IVR/chatbot updates, and rollback recommendations. The project must use synthetic mocks unless real access is explicitly approved.

### Operations Constraint

API server is configured for localhost only. Remote dashboard/API operation should not be assumed until explicit deployment and authentication requirements are supplied.

## 5. Safe Assumptions Until Missing Class Docs Arrive

The following assumptions are safe because they are directly supported by the available corpus or conservative governance practice.

1. Work should remain isolated in the `digital-recovery` Hermes profile.
2. The workspace root is `/Users/rayane/digital-experience-recovery-agent`.
3. Docker-backed terminal execution is the intended baseline.
4. The project is centered on Apex Global Bank's customer experience and digital channels challenge.
5. The product concept is a Digital Experience Recovery Agent that connects customer impact signals with technical operations data.
6. The intended architecture is hierarchical supervisor-worker multi-agent orchestration.
7. The core agent roles are Supervisor, Customer Signal, Observability, Change Correlation, and Recovery & Communication.
8. Early work should produce corpus analysis, requirements extraction, architecture notes, data contracts, and safe synthetic examples rather than production integrations.
9. Customer-facing communications require explicit human approval for the specific send.
10. Synthetic or explicitly approved sample data should be used until real data rules are provided.
11. Raw customer PII should not be stored or processed without a clear policy.
12. The system should eventually be auditable across ingestion, normalization, classification, recommendation, approval, execution, and monitoring.
13. Security and access should default to least privilege.
14. API/dashboard exposure should remain local-only unless remote exposure is explicitly authorized and protected.
15. Implementation should be gated until Session 11 and rubric/submission requirements are supplied or formally waived.

## Conflicting or Potentially Conflicting Priorities

The updated corpus reveals the following potential tensions.

| Potential Priority A | Potential Priority B | Risk |
|---|---|---|
| Project brief proposes a production-grade multi-agent architecture with external systems and tool schemas | Current governance requires no product code until corpus is frozen | Building immediately could skip rubric/course alignment and encode unsafe assumptions. |
| Brief targets aggressive business outcomes such as MTTR under 15 minutes and 45% contact-center deflection | Course deliverable may prioritize conceptual explanation, architecture, prompting, and security rather than a production-grade system | Overbuilding could distract from the expected academic deliverable. |
| Recovery & Communication Agent can generate scripts for IVR, chatbot, and customer communication | Project setup requires human approval before any customer-facing action | Automation must stop at draft/recommendation unless explicitly approved. |
| Observability and Change Correlation Agents imply Datadog, Dynatrace, ServiceNow, GitHub, and CI/CD integrations | No approved credentials, datasets, internal domains, or security policy are provided | Real integrations are out of scope until explicitly authorized. |
| Course materials emphasize prompting and security | Brief includes powerful tool actions such as rollback recommendation and customer communication | Security guardrails and approval gates must be first-class design artifacts, not implementation afterthoughts. |
| Course materials emphasize building first agents/tools | Corpus lock requires implementation delay until missing materials are waived | Permitted work should focus on requirements and design extraction, not executable product code. |

## Build Gate

Status: **PARTIALLY OPEN — backend shell and frontend shell only**

Backend shell implementation and frontend shell implementation are allowed under the waivers recorded below. All other product implementation remains blocked.

### Backend Shell Waiver

Rayane explicitly opened the build gate for implementation of the backend shell only. Remaining missing class-doc/corpus-freeze requirements are waived for this phase only.

Constraints for this waiver:

- Use synthetic/dev-only data.
- Use localhost-only development assumptions.
- Do not connect to real bank systems, real customer records, real observability platforms, or real messaging/call systems.
- Do not waive privacy, security, or sensitive-data rules.
- Keep all customer/business records synthetic.
- Hermes remains the only agent runtime.
- App database stores product/customer demo records; Hermes state stays profile-scoped.

### Frontend Shell Waiver

Rayane explicitly requested implementation of the frontend shell for a premium customer-experience recovery cockpit. Remaining missing class-doc/corpus-freeze requirements are waived for this frontend-shell phase only.

Constraints for this waiver:

- Use synthetic/dev-only data.
- Use localhost-only development assumptions.
- Do not connect to real bank systems, real customer records, real observability platforms, real messaging systems, or real call systems.
- Do not waive privacy, security, or sensitive-data rules.
- Keep all displayed customer/business records synthetic.
- Hermes remains the only agent runtime.
- The UI must be a cockpit, not a generic chatbot.
- Every animated state must map to a documented runtime event/state, and critical states require text-only equivalents.
- The UI may call the local backend shell only; Hermes state remains profile-scoped behind the backend/Hermes API boundary.

The build gate remains closed for all work outside these backend/frontend shells until one of the following happens:

1. Session 11 is added to the workspace or explicitly waived; and
2. The assignment rubric / final submission instructions are added or explicitly waived; and
3. The project corpus is declared frozen by Rayane, the mentor, or the designated project owner; and
4. Any waiver is recorded in this document or a linked decision record; and
5. The security-sensitive domain blocklist is populated or explicitly waived; and
6. The API/dashboard exposure mode is confirmed as local-only or remote-with-auth; and
7. The data policy is confirmed as synthetic-only, anonymized, or approved real data.

### Minimum Materials Needed to Open the Gate

The following are the minimum recommended materials before implementation:

- Session 11 materials, or explicit waiver.
- Formal rubric / final deliverable instructions, or explicit waiver.
- Project-owner confirmation that the provided project brief is the authoritative brief.
- Data policy and sample data decision.
- Security-sensitive domain list or explicit waiver.
- API/dashboard exposure decision.
- Initial build plan / milestone plan.

### Permitted Work While Gate Is Closed

The following work is allowed before the gate opens:

- Corpus inventory maintenance.
- Requirements extraction from the project brief and course materials.
- Course-to-project alignment matrix.
- Glossary creation.
- Risk register creation.
- Data contract drafting using synthetic examples.
- Architecture option notes without committing to implementation.
- Build plan drafting.
- Security and governance documentation.

The following work is not allowed while the gate is closed:

- Product code implementation.
- External integrations.
- Customer-facing message automation.
- Real customer data ingestion.
- Remote API/dashboard exposure.
- Persistent cron jobs with external side effects.

## Next Actions

1. Confirm whether Session 11 exists and add it to `docs/source/course-materials/`, or explicitly waive it.
2. Add the formal assignment rubric and final submission instructions if available.
3. Confirm that `Digital_Experience_Recovery_Agent_Solution.docx` is the authoritative project brief.
4. Provide the actual sensitive/internal domains for the website blocklist, or waive the blocklist content requirement.
5. Decide whether API/dashboard access remains localhost-only or will be remotely exposed.
6. Define data usage policy: synthetic-only, anonymized, or approved real data.
7. Create a requirements extraction document from the project brief and course decks.
8. Create a course-to-project alignment matrix.
9. Re-run corpus inventory after any new materials are added.
10. Open the build gate only after the corpus is frozen or missing items are explicitly waived.
