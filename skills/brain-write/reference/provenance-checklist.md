# Provenance Tracking Checklist

When writing a decision to the brain, capture these elements systematically. Each ensures future readers understand not just the decision, but why it was made and what context matters.

### 1. Decision ID
- **Why capture:** Unique reference for linking, searching, auditing
- **How to document:** Prefix filename with ID (D123.md), include in frontmatter, reference in commit message
- **Example:** `decisions/D087.md` for "Switch from REST to gRPC for service mesh"
- **Format:** Auto-generate with prefix (D001, D002, ...) or use semantic ID (API-REST-v2, SCHEMA-MIGRATION-v1)

### 2. Decision Title
- **Why capture:** Quick summary for brain-recall searches and human scanning
- **How to document:** H1 heading in markdown, title field in YAML frontmatter
- **Example:** `# API Contract Negotiation: REST v2 with streaming support`
- **Production pattern:** Title describes what, not how; include version/scope in title

### 3. Decision Description & Problem Statement
- **Why capture:** Context for future team members who weren't in the room; audit trail for "why did we do this?"
- **How to document:** Prose paragraph after title explaining the problem, constraints, and goals
- **Example:** "Traffic patterns showed 95th percentile latency of 2.5s with REST polling. Streaming reduces to <100ms. Infra team constraint: must support existing web clients for 6 months during transition."
- **Production pattern:** Write for readers unfamiliar with the decision; link to metrics/evidence

### 4. When Made (Date & Phase)
- **Why capture:** Understand context drift over time; know if decision is time-bound
- **How to document:** YAML frontmatter `date:` field and `phase:` if relevant; commit date in git
- **Example:** `date: 2025-11-15`, `phase: scaling` (or omit phase if decision is always-valid)
- **Production pattern:** Always include ISO date; phase is optional (omit if decision is evergreen)

### 5. By Whom (Decision Maker & Stakeholders)
- **Why capture:** Know who was in the room, who signed off, who dissented; accountability
- **How to document:** YAML `owner:`, `stakeholders:`, `decision_maker:` fields; mention approval in prose
- **Example:**
  ```yaml
  owner: platform-infra
  decision_maker: Alice Chen (Principal Architect)
  stakeholders: [backend-team, web-team, app-team, devops]
  approved_by: [VP Eng, Principal Database Architect]
  ```
- **Production pattern:** Be explicit about who decided vs. who influenced vs. who approved

### 6. What Was Decided (The Actual Decision)
- **Why capture:** Core decision record; what actually changed/locked
- **How to document:** Explicitly stated section or table; include version numbers, SLAs, rollback dates
- **Example:**
  ```markdown
  ## Decision
  Adopt gRPC over REST for service-to-service communication:
  - New services (ID ≥ 100) MUST use gRPC
  - Existing services can migrate on schedule (Q2 2026 target)
  - Keep REST public API unchanged
  - Deadline: Dec 31, 2026 (all services gRPC-native)
  ```
- **Production pattern:** Use declarative language ("MUST", "SHOULD", "MAY"); include deadlines

### 7. What Were Alternatives (Options Considered & Why Rejected)
- **Why capture:** Prevents rework (avoids re-litigating); shows thinking; audit trail
- **How to document:** Table or numbered section with option, pros, cons, verdict
- **Example:**
  ```markdown
  ## Alternatives Considered
  1. **REST with WebSocket upgrade** — Complexity high, reduces team velocity. Rejected.
  2. **Kafka event streaming** — Overkill for RPC. Chose gRPC instead.
  3. **Status quo (REST polling)** — 2.5s latency unacceptable for voice features. Rejected.
  ```
- **Production pattern:** Don't document "we considered X"; document "we considered X, pros [Y], cons [Z], rejected because [W]"

### 8. What's the Impact (Affected Systems, Rollback Strategy)
- **Why capture:** Scope of change; risk assessment; how to undo if wrong
- **How to document:** Section listing affected services, API changes, migration steps, rollback procedure
- **Example:**
  ```markdown
  ## Impact
  - Affected systems: 47 services, 3 data planes
  - Breaking changes: ServiceA.GetUser changes from REST HTTP/1.1 to gRPC
  - Rollback: Revert to commit HASH, re-enable REST fallback, maintain 7-day soak period
  - Timeline: 3 months parallel run (both REST+gRPC active), then REST deprecation
  ```
- **Production pattern:** Always include explicit rollback procedure; understand blast radius

### 9. Linked Decisions (Parent/Child, Related)
- **Why capture:** Trace decision trees; understand dependencies; avoid orphaned decisions
- **How to document:** YAML `related_decisions:` field with links and relationship type
- **Example:**
  ```yaml
  parent_decision: D042  # "Adopt service mesh architecture"
  children_decisions: [D088, D089, D090]  # "gRPC auth strategy", "service discovery config", etc.
  related_decisions:
    - D023: "API versioning contract" (informs gRPC API structure)
    - D055: "Observability stack" (shares tracing instrumentation)
  ```
- **Production pattern:** Use decision links to construct decision graph; enables brain-link and brain-why

### 10. Status (Active, Warm, Cold, Archived)
- **Why capture:** Know if decision still applies; signals to review or deprecate
- **How to document:** YAML `status:` field; update as decision ages or changes
- **Example:**
  ```yaml
  status: active  # In force until Dec 31, 2026
  review_date: 2026-06-15  # Quarterly review of gRPC adoption metrics
  deprecation_planned: 2027-01-01  # REST API fully sunset
  ```
- **Production pattern:** `active` (in force), `warm` (being phased out), `cold` (deprecated, kept for ref), `archived` (historical only)

### 11. Review & Approval Status
- **Why capture:** Governance trail; who signed off; when (for compliance/audit)
- **How to document:** YAML approval fields; update as reviews complete
- **Example:**
  ```yaml
  approval_status: approved
  approved_by: [VP Engineering (2025-11-16), Security Review Board (2025-11-18)]
  review_checklist:
    - security: passed
    - performance: passed (load test: 10k RPS gRPC vs 2k RPS REST)
    - backwards_compat: no breaking changes for 6 months
  ```
- **Production pattern:** Track who reviewed, when, and with what verdict; enables brain-recall "show me all decisions approved by <person>"
