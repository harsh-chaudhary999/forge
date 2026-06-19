# Common Pitfalls

### Pitfall 1: Incomplete Commit Messages
**Problem:** Commit says "update spec" with no context. Future readers can't understand why.

**Example (BAD):**
```
git commit -m "spec: update shared dev spec"
```

**Example (GOOD):**
```
git commit -m "spec: lock shared dev spec for PRD-2025-11-streaming

Converged on: backend, web, app, infra
Contracts locked: gRPC v1 service definitions, MySQL schema v3, Redis config
Key assumption: 100k RPS sustainable with 3 service instances per region
Next: Run tech-plan-write-per-project; unblocks implementation

Resolves: D087"
```

**How to avoid:** Always include: WHY (problem/goal), WHAT (what changed), CONTRACTS (what's locked), NEXT (what's unblocked)

---

### Pitfall 2: Missing Alternatives Section
**Problem:** Only document the chosen path. Future team re-litigates the same decision or doesn't understand constraints.

**Example (BAD):**
```markdown
# Decision
Use gRPC for service communication.
```

**Example (GOOD):**
```markdown
# Decision
Use gRPC for service communication (not REST polling, not Kafka, not WebSocket).

## Alternatives Considered
1. **REST with WebSocket upgrade** — Eliminates polling latency. Con: adds protocol complexity; web team would need 2x effort to maintain. Rejected due to dev velocity impact.
2. **Kafka for events** — Would decouple services. Con: wrong pattern for synchronous RPC; would add queuing latency (100ms+). Rejected as wrong tool.
3. **Status quo (REST polling)** — Existing, simple. Con: 2.5s p95 latency breaks real-time features; unacceptable. Rejected.
```

**How to avoid:** For each decision, spend 10 minutes brainstorming alternatives. Document all, explain why each was rejected. Spend as much time on the rejection reasoning as on the chosen path.

---

### Pitfall 3: No Evidence Links
**Problem:** Decision claims "this is better" without data. Auditor or skeptic has no way to verify.

**Example (BAD):**
```markdown
## Why
gRPC is much faster than REST and scales better.
```

**Example (GOOD):**
```markdown
## Why
Load test results (link: https://metrics.internal/reports/grpc-vs-rest-2025-11):
- REST polling: 2k RPS, p95 latency 2.5s, 100% connection pool exhaustion at peak
- gRPC streaming: 20k RPS, p99 latency 50ms, 12% CPU utilization at peak
- Incident analysis (link: incident-2025-11-14): Exactly 45-minute outage caused by connection pool exhaustion in REST polling feature; gRPC would have prevented via stream multiplexing

These results justify the 3-month migration cost.
```

**How to avoid:** Link to load test results, incident reports, metrics dashboards, code benchmarks. Every claim should be citable. Use `evidence:` section in frontmatter.

---

### Pitfall 4: Decisions Without IDs (Can't Reference Later)
**Problem:** Write decision as free-form markdown with no ID. Later, team can't say "let's re-check D087" because there's no D087.

**Example (BAD):**
File: `brain/decisions/gRPC-adoption.md` (no ID in filename or frontmatter)

**Example (GOOD):**
File: `brain/decisions/D087.md` (ID in filename)
```yaml
---
decision_id: D087
title: Adopt gRPC for Service-to-Service Communication
---
```

Later, in a PR comment: "This service needs to follow D087 (gRPC for service-to-service). See /why D087 for full context."

**How to avoid:** Always assign a sequential decision ID before committing. Use `decision_id:` in frontmatter. Reference the ID in commit messages and cross-links. Enable brain-why and brain-link to work.

---

### Pitfall 5: Stale Decisions Never Marked for Archival
**Problem:** Decision was valid in 2024, but situation changed in 2025. New team doesn't know to ignore it or update it. They waste time deciding whether to follow an obsolete decision.

**Example (BAD):**
```yaml
status: active  # Actually invalid since 2025-09 due to new SLA requirements
```

**Example (GOOD):**
```yaml
status: warm  # Being phased out; superseded by D095 (new SLA strategy)
superseded_by: D095
review_date: <~90 days out, e.g. 2026-09-30>  # Quarterly check on status
deprecation_planned: 2027-01-01  # Final sunset; still referenced in runbooks
```

Or, if decision is now archival (historical only):
```yaml
status: cold  # Kept for audit trail; design changed significantly in D095
superseded_by: D095
```

**How to avoid:** Set `review_date:` on every decision (quarterly, or sooner if known change is coming). Include `deprecation_planned:` if decision is time-bound. On review date, update status to `warm` (being phased out) or `cold` (superseded, keep for history). Let brain-forget handle final archival.
