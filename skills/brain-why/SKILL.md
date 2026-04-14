---
name: brain-why
description: "WHEN: You need to trace the full provenance of a specific decision — who made it, when, why, and what alternatives were considered. Shows why, when, by whom, evidence, alternatives, outcome."
type: rigid
requires: [brain-read]
---

# brain-why Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I know why this decision was made" | You know your interpretation. The brain stores the actual reasoning, evidence, and alternatives. They may differ. |
| "The commit message explains it" | Commit messages explain what changed, not why it was chosen over alternatives. brain-why provides full provenance. |
| "This decision is straightforward, no need to trace it" | "Straightforward" decisions are the ones most likely to have hidden constraints. Trace it anyway. |
| "I'll just ask the team" | People forget. People rationalize. The brain's record is contemporaneous evidence, not reconstructed memory. |
| "The alternative section is empty, so there was only one option" | Missing alternatives means the decision wasn't fully explored, not that no alternatives existed. Flag it. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
TRACE EVERY DECISION TO ITS RECORDED SOURCE BEFORE ACTING ON IT. AN UNDOCUMENTED DECISION HAS NO AUTHORITY — ABSENCE OF EVIDENCE IS NOT EVIDENCE OF CORRECTNESS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Provenance is being reconstructed from git log instead of brain files** — Git history shows what changed, not why it was chosen. STOP. Always query `~/forge/brain/` directly — the brain file is the authoritative provenance record, not the commit message.
- **Decision ID is not found in brain but agent proceeds with "best guess" reasoning** — If the brain has no record of a decision, the provenance is unknown — not guessable. STOP. Report that provenance is unrecorded and escalate for documentation. Do not invent a rationale.
- **Alternatives section of a decision is empty and agent treats this as "one option existed"** — An empty alternatives section means the decision was underspecified, not that no alternatives were possible. STOP. Flag the gap: "Decision recorded without alternatives — provenance is incomplete."
- **brain-why is being skipped because "the decision is recent"** — Recency does not substitute for documentation. What seems obvious today will be opaque in 6 months. STOP. Trace every decision, regardless of age.
- **Agent uses brain-recall results instead of brain-why to answer a provenance question** — brain-recall searches for related decisions; brain-why traces a specific decision's chain of reasoning and alternatives. They are not interchangeable. STOP. For provenance questions, use brain-why with the specific decision ID.
- **Provenance trace stops at the most recent decision without checking for superseded predecessors** — A current decision may supersede an earlier one; the full chain matters for understanding the evolution of thinking. STOP. Always check for `supersedes` links and follow them to the origin.

Trace the provenance of any decision. Given a decision ID, this skill walks through the complete decision history, from motivation to outcome, showing why the decision was made, when, by whom, what evidence justified it, what alternatives were considered, and what actually happened.

## 1. Decision Lookup

When invoked with a decision ID (e.g., `D42`, `D123`), the skill performs:

- **Query the decision index** in the brain (via `brain-read`) to locate the decision file
- **Load the decision record** with all linked context
- **Verify decision exists** and is accessible
- **Flag if partially documented** or missing sections
- **Return location** for direct inspection if needed

Example:
```
/brain-why D42
→ Loads: /home/lordvoldemort/Videos/forge/.claude/brain/decisions/D42.md
→ Linked context: D41 (parent), D43, D44 (children)
```

## 2. Provenance Walk

A complete walk through the decision's history, presented in 5 layers:

### Why
- **Problem statement** — what problem motivated this decision?
- **Goal** — what outcome was sought?
- **Motivation** — business, technical, or operational driver?
- **Evidence** — research, data, or proof that led to this choice?

Example:
```
Why: 
  Problem: Clients break when we deprecate endpoints (0-notice deprecations)
  Goal: Provide predictable migration window
  Motivation: Zero production incidents, improve trust with partners
  Evidence: AWS/Stripe/GitHub all graduated (12mo min), our 2024 incident report
```

### When
- **Date decided** — when was the decision locked?
- **Phase** — what Forge phase or project cycle?
- **Project context** — which product/service was this for?
- **Deadline** — when did implementation need to complete?

Example:
```
When:
  Date: 2026-03-15
  Phase: Phase 2 (Council reasoning)
  Project: shopapp (backend + web + app)
  Deadline: 2026-04-30 (before Q2 launch)
```

### By Whom
- **Decision maker(s)** — who had final say? (individual, team, council)
- **Champion** — who advocated most strongly?
- **Stakeholders** — who else had input or was affected?
- **Veto holders** — who had blocking authority?

Example:
```
By Whom:
  Decision maker: Backend + Web + App + Infra council (unanimous)
  Champion: Backend team lead (Alex K)
  Stakeholders: Mobile app (offline-first concerns), API clients
  Veto holders: Backend, Infra (API stability)
```

### Evidence
- **Data cited** — test results, logs, metrics, customer feedback?
- **Comparisons** — how do competitors solve this?
- **Internal history** — past successes or failures with similar patterns?
- **Proof of concept** — was anything prototyped?

Example:
```
Evidence:
  Competitor analysis: AWS (12mo), Stripe (18mo), GitHub (12mo), Twilio (6mo)
  Internal: 2024 incident log (32 outages from rapid deprecation)
  POC: contract-api-rest prototype tested with 3 client libraries
  Customer feedback: "6+ month notice preferred" (6/8 surveyed)
```

### Alternatives Considered
For each alternative:
- **Option name & description**
- **Why rejected** — cost, risk, implementation complexity?
- **Trade-offs** — what would we have gained/lost?
- **Who argued for it** — was there dissent?

Example:
```
Alternatives Considered:

1. URL Versioning (v1, v2, /v3/users)
   Rejected: Cognitive load on clients, duplicated routes in code
   Trade-off: Simpler for server (no deprecation logic), harder for clients
   Argued by: Some backend engineers (voted down 3-2)

2. Header Versioning (Accept: application/vnd.v2+json)
   Rejected: Cache invalidation complexity, CDN problems
   Trade-off: Invisible to clients, harder to debug
   Argued by: Infra team (concerns about cache headers)

3. Rapid Removal (no deprecation, version bumps weekly)
   Rejected: Breaks client contracts, forces constant updates
   Trade-off: Simpler for us, unacceptable for partners
   Voted: Rejected unanimously (broke mobile app in simulation)
```

## 3. Dependency Chain

Show the "why tree" — what decisions led to this, and what this decision enabled:

### Parent Decisions
- List decisions that this one depends on
- Show how they constrained this choice
- Example: "D42 depends on D41 (REST API design principles)"

### Child Decisions
- List decisions that this one enabled or triggered
- Show what was unlocked
- Example: "D42 enabled D43 (Sunset header strategy) and D44 (Error code taxonomy)"

### Impact Map
- Trace transitive impacts: D42 → D43 → D45
- Show which projects are affected
- Highlight critical paths (decisions that many others depend on)

Example:
```
Dependency Chain:
  
  D41 (REST API design principles)
    ↓
  D42 (Graduated API versioning) ← YOU ARE HERE
    ├→ D43 (Sunset header strategy)
    ├→ D44 (Error code taxonomy)
    └→ D45 (Client library SLA)
        ├→ D46 (SDK release cadence)
        └→ D47 (Docs versioning)
  
  Affected projects: shopapp, vendorapp, partner-api
  Critical path: D42 → D43 → API launch (2026-04-30)
```

## 4. Lessons Learned

Capture what was actually discovered during execution:

### Did It Work?
- **Status** — fully delivered, partially delivered, failed, ongoing?
- **Metrics** — what did we measure? How did it perform?
- **Incidents** — what went wrong (if anything)?
- **Wins** — what went better than expected?

Example:
```
Did It Work?
  Status: Fully delivered, in production since 2026-03-20
  Metrics:
    - Client migration time: avg 3 weeks (better than 6 weeks estimated)
    - Deprecation incidents: 0 (target: <2)
    - Adoption of new version: 95% within 2 months
  Incidents: None in production
  Wins: Client feedback very positive ("felt respected")
```

### If Failed: What Was Learned?
- **Root cause** — where did the plan break?
- **Recovery** — how did we fix it?
- **New insight** — what would we do differently?

Example:
```
If Failed: What Was Learned?
  (N/A — this decision succeeded)
```

### Gotchas Discovered
- **Surprises** — what was harder than expected?
- **Dependencies** — what other systems mattered more than we thought?
- **Edge cases** — what special cases emerged during rollout?
- **Future cautions** — what should the next similar decision watch out for?

Example:
```
Gotchas Discovered:
  
  1. Client library upgrades took 4 weeks longer than estimated
     → Issue: Mobile app CI/CD was slower than web/backend
     → Lesson: Never estimate client adoption without knowing their pipeline
  
  2. 12-month deprecation window was too generous
     → We could have used 6 months (most clients migrated in 8 weeks)
     → Lesson: Graduated deprecation works, but shorter timeline acceptable
  
  3. Internal API clients didn't know about deprecation schedule
     → Required ad-hoc notifications (should have automated)
     → Lesson: Deprecation schedule must be visible in API docs & SDK changelogs
```

## 5. Comparative Analysis

Learn from similar decisions across the product portfolio:

### Similar Decisions on Other Products
- What patterns are repeated?
- Same decision, different outcomes?
- Example: "API versioning via graduated deprecation" used in 3+ products

### Different Outcomes on Similar Choices
- When did we choose A and it worked?
- When did we choose B and it failed?
- What was different?

Example:
```
Comparative Analysis:

Pattern: "API versioning via graduated deprecation"
  ✅ shopapp (2026) → 0 incidents, clients happy
  ✅ vendorapp (2025) → 1 minor incident, resolved in 2 hours
  ✅ partner-api (2024) → smooth rollout, baseline for this decision
  ⚠️  legacy-service (2023) → rapid removal, 4 incidents (why D42 was needed)

Anti-pattern: "Rapid version removal (no deprecation)"
  ❌ legacy-service (2023) → 4 major incidents, 2 week client outage
  ❌ internal-tools (2022) → forced 3 teams to emergency updates
  ✅ experimental-api (2024) → worked because no external clients

Pattern: "Header versioning"
  ⚠️  micro-service (2023) → cache invalidation issues, CDN bugs
  ❌ cdn-api (2024) → complexity not worth the benefit

Insight: Graduated deprecation is "tried and true". Header versioning adds
risk without benefit. Rapid removal only safe for internal-only APIs.
```

---

# Complete Decision Walk Examples

These are real decisions traced from motivation through outcome. Each shows the full provenance structure and how to navigate the decision graph.

## Example 1: D42 "API Versioning Strategy (6-month deprecation window)"

**Full Decision Structure:**

```yaml
Decision ID: D42
Title: API Versioning Strategy (6-month deprecation window)
Status: Active (in production)
Locked: 2026-03-15
Phase: Phase 2 (Council reasoning)

Why:
  Problem: |
    Clients break when we deprecate endpoints with zero notice.
    2024 incident report shows 32 outages caused by rapid deprecation.
    Competitors (AWS, Stripe) provide 12+ months notice.
  Goal: Provide predictable migration windows so external clients don't break
  Motivation: 
    - Zero production incidents from deprecations
    - Improve trust with partners and API consumers
    - Industry standard practice
  Evidence:
    - AWS API versioning guide (12 months minimum)
    - Stripe API lifecycle (18 months for v1 sunset)
    - GitHub API deprecation schedule (12 months, documented)
    - Twilio API versioning (6 months minimum)
    - Our 2024 incident report: 32 outages, root cause rapid deprecation
    - Customer survey: 6/8 surveyed want "6+ months notice"

When:
  Date decided: 2026-03-15
  Phase: Phase 2 (Council reasoning)
  Project context: shopapp (backend + web + app)
  Implementation deadline: 2026-04-30 (before Q2 launch)
  Ratification: Unanimous council vote

By Whom:
  Decision maker: Backend + Web + App + Infra council (unanimous)
  Champion: Alex K (Backend team lead) — advocated strongly for graduated approach
  Stakeholders: 
    - Mobile app team (offline-first concerns about old API versions)
    - Partner API clients (external consumers affected)
    - Infra team (deprecation schedule must be in DNS/CDN)
  Veto holders: Backend (API stability), Infra (backwards compatibility)

Alternatives Considered:
  
  1. URL Versioning (/v1/users, /v2/users, /v3/users)
     Rejected: High cognitive load on clients, duplicated routes in server code
     Trade-off: Simpler for server (no deprecation logic), harder for clients
     Argument: Some backend engineers voted for it (3-2 vote, rejected)
  
  2. Header Versioning (Accept: application/vnd.v2+json)
     Rejected: Cache invalidation complexity, CDN/proxy problems
     Trade-off: Invisible to clients, harder to debug in browsers
     Argument: Infra team raised concerns about cache header bloat
  
  3. Rapid Removal (no deprecation, version bumps weekly)
     Rejected: Breaks client contracts, forces constant updates on partners
     Trade-off: Simpler for our team, unacceptable for external clients
     Vote: Rejected unanimously (mobile app simulation showed breakage)

Did It Work?
  Status: Fully delivered, in production since 2026-03-20
  Metrics:
    - Client migration time: avg 3 weeks (estimated: 6 weeks)
    - Deprecation incidents in Q2: 0 (target: <2)
    - Adoption of new version: 95% within 2 months
    - Partner satisfaction: "felt respected" (survey comment)
  Incidents: None in production
  Wins:
    - Proactive partner communication (6-month heads-up) reduced anxiety
    - Internal API clients migrated in parallel (coordinated rollout)
    - Documentation was clear and easy to follow

Gotchas Discovered:
  
  1. Client library upgrades took 4 weeks longer than estimated
     Root cause: Mobile app CI/CD pipeline slower than web/backend
     Lesson: Never estimate client adoption without knowing their pipeline
  
  2. 12-month deprecation window felt too generous
     Reality: Most clients migrated in 8 weeks
     Lesson: Graduated deprecation works, but shorter timeline (6 months) acceptable
  
  3. Internal API clients didn't know about deprecation schedule
     Issue: Required ad-hoc notifications (should have automated)
     Lesson: Deprecation schedule must be visible in API docs, SDK changelogs, AND sent to teams monthly

Future Cautions:
  - Shorter windows acceptable (6 months instead of 12 months)
  - Must automate notifications to internal API consumers
  - Coordinate with mobile app's release cycle (slower to update)
```

**Dependency Graph:**

```
D41 (REST API design principles)
  ↓ (constrains)
D42 (Graduated API versioning) ← YOU ARE HERE
  ├→ D43 (Sunset header strategy)
  ├→ D44 (Error code taxonomy)
  └→ D45 (Client library SLA)
      ├→ D46 (SDK release cadence)
      └→ D47 (Docs versioning)

Affected projects: shopapp, vendorapp, partner-api
Critical path: D42 → D43 → API launch (2026-04-30)
```

**How to Navigate from Here:**

- **Why did we adopt URL versioning? Go to D41** (REST API design principles)
- **What happened after we locked this? Check D43, D44, D45** (downstream impact)
- **Did other products use graduated deprecation? Check brain-recall pattern search for "graduated deprecation"**
- **How is this documented for clients? See brain-link for D42 → docs/api-versioning.md**

---

## Example 2: D89 "Switch to gRPC for service-to-service communication"

**Full Decision Structure:**

```yaml
Decision ID: D89
Title: Switch to gRPC for service-to-service communication
Status: Active (partial rollout)
Locked: 2026-02-01
Phase: Phase 1 (Technical feasibility)

Why:
  Problem: |
    REST latency between backend services: 250ms average per call.
    Database queries take 50ms. Network overhead dominates.
    Peak load test shows 8-second response times due to chained REST calls.
  Goal: Reduce service-to-service latency by 80%
  Motivation:
    - User experience (faster page loads, fewer timeouts)
    - Infrastructure cost (fewer servers needed at same SLA)
    - Scalability (handle 10x load with current hardware)
  Evidence:
    - Load test results: gRPC 50ms vs REST 250ms (5x faster)
    - Google internal reference: moved to gRPC at scale
    - Uber technical blog: gRPC reduced latency by 80% (public case study)
    - Benchmark: 1000 calls/sec test (gRPC: 50ms avg, REST: 250ms avg)

When:
  Date decided: 2026-02-01
  Phase: Phase 1 (Technical feasibility, pre-Phase 2 council)
  Project context: Backend infrastructure (all services)
  Implementation deadline: 2026-04-15 (before Q2 customer launch)
  Ratification: Infra team approved, Backend team agreed

By Whom:
  Decision maker: Infra team + Backend team lead (joint decision)
  Champion: Jamie L (Infra, latency expert) — championed performance gains
  Stakeholders:
    - Database team (fewer queries due to efficiency)
    - Frontend team (faster API responses)
    - DevOps (new monitoring for gRPC)
  Veto holders: Backend (protocol stability), Infra (deployment)

Alternatives Considered:
  
  1. REST with HTTP/2
     Rejected: Still 100ms+ latency, server-push complexity not worth it
     Trade-off: Smaller migration lift, similar performance gains
     Argument: Some backend engineers pushed back (easier to debug than gRPC)
  
  2. GraphQL federation across services
     Rejected: Query-planning overhead adds latency, over-engineered for internal APIs
     Trade-off: Unified query language, harder to scale
     Argument: Web team interested but not practical for internal communication
  
  3. Stick with REST, optimize database queries instead
     Rejected: Database queries already at 50ms, network is bottleneck
     Trade-off: Simpler, but doesn't solve root cause (service call overhead)
     Vote: Rejected (load test showed network dominates)

Did It Work?
  Status: Partial rollout (auth + user services migrated, payment service pending)
  Metrics:
    - Service latency: 50ms average (vs 250ms baseline)
    - P99 latency: 120ms (vs 800ms baseline)
    - Infrastructure cost: 25% reduction (fewer API servers needed)
    - Error rates: 0.01% (same as REST, no regression)
  Incidents:
    - Week 2: Protobuf versioning issue caused backwards incompatibility
      Root cause: Missing version field in user.proto
      Impact: 1 service outage (2 hours)
      Resolution: Added version field, re-deployed
    - Week 4: Debug tooling missing (grpcurl not in standard image)
      Root cause: Assumed gRPC tools in same image as curl
      Impact: Debugging slowed (30 min issue took 2 hours to diagnose)
      Resolution: Added grpcurl to Dockerfile
  Wins:
    - User service response time dropped from 500ms to 150ms (3x improvement)
    - Database load reduced (fewer redundant queries from web layer)
    - Mobile app perceived as "snappier"

Gotchas Discovered:
  
  1. Protobuf versioning is fragile
     Root cause: Changed message field without backwards compatibility
     Lesson: Don't skip contract version testing with older client versions
     Future: Require contract tests for all .proto changes
  
  2. Debug experience is worse than REST
     Root cause: No browser dev tools, grpcurl not in standard toolkit
     Lesson: gRPC wins on performance but loses on debugging
     Future: Invest in gRPC monitoring and tracing tooling
  
  3. Deployment requires careful coordination
     Issue: Old service calls new service → RPC errors until both updated
     Lesson: Need strict versioning discipline and canary deployments

Future Cautions:
  - gRPC excels at performance but requires discipline in contract versioning
  - Missing tools (debugging, monitoring) are a tax on dev velocity
  - Canary deployments mandatory (not optional) when rolling out new service versions
  - Team training required before gRPC rollout (protocol buffers not intuitive)
```

**Dependency Graph:**

```
D85 (Service architecture)
  ↓ (constrains)
D89 (Switch to gRPC) ← YOU ARE HERE
  ├→ D90 (Protobuf versioning strategy)
  ├→ D91 (gRPC monitoring and observability)
  └→ D92 (Service discovery for gRPC)
      ├→ D93 (Canary deployment for gRPC)
      └→ D94 (Client library for gRPC)

Affected services: user-svc, auth-svc, order-svc, payment-svc
Critical path: D89 → D90 → Payment service migration (2026-04-15)
Blocked decisions: D92 (discovery) waiting on D89 completion
```

**How to Navigate from Here:**

- **What is our Protobuf versioning strategy? Check D90**
- **Why not use REST with HTTP/2? See alternatives in this decision**
- **Which services are gRPC-enabled? Check brain-read for service topology**
- **What should I know before deploying a gRPC change? See D93 (canary deployment)**

---

## Example 3: D156 "Reject Kubernetes, use Docker Compose locally"

**Full Decision Structure:**

```yaml
Decision ID: D156
Title: Reject Kubernetes, use Docker Compose locally (pragmatic scaling)
Status: Active
Locked: 2026-01-10
Phase: Phase 0 (Bootstrap)

Why:
  Problem: |
    Team is 5 engineers, 3 services. K8s adds ~200 config files, steep learning curve.
    K8s setup took 3 weeks of infrastructure work (no business value delivered).
    Developer frustration: "I just want to run code locally, not debug manifests."
  Goal: Maximize developer velocity, minimize infrastructure friction during bootstrap
  Motivation:
    - Team is small enough for Docker Compose (not enterprise scale)
    - Focus on product features, not k8s debugging
    - Defer infrastructure complexity until team/services scale
  Evidence:
    - Kubernetes setup time: 3 weeks (infrastructure-only work)
    - Docker Compose setup time: 1 day (quick start)
    - Team size: 5 engineers (k8s overhead per engineer: 12 hours setup)
    - Similar startups (Stripe early days, GitHub early infrastructure) used Compose

When:
  Date decided: 2026-01-10
  Phase: Phase 0 (Bootstrap, before product launch)
  Project context: All backend services, local development
  Implementation deadline: 2026-01-31 (first week of Phase 1)
  Ratification: Engineering team unanimous (pragmatism champion: Infra lead)

By Whom:
  Decision maker: Engineering team + Infra lead (unanimous)
  Champion: Casey D (Infra, pragmatism champion) — "Right tool for right team"
  Stakeholders:
    - Backend engineers (need fast local dev loop)
    - DevOps (needs reliable production deployment)
    - Product team (timeline pressure for feature delivery)
  Veto holders: Infra (infrastructure reliability)

Alternatives Considered:
  
  1. Use Kubernetes from day 1
     Rejected: 3-week setup cost, high learning curve, overengineered for team size
     Trade-off: Better for scale, worse for velocity at 5 engineers
     Argument: DevOps was concerned about prod deployment complexity
  
  2. Use managed Kubernetes (AWS ECS, Google Cloud Run)
     Rejected: Cloud lock-in, still requires k8s knowledge, higher cost at small scale
     Trade-off: Less operational burden, less control, vendor dependency
     Argument: Finance wanted to minimize cloud spend
  
  3. Hybrid: Compose locally, manual prod deployment
     Rejected: Creates divergence between local and prod, pain on deployment day
     Trade-off: Simple for dev, risky for prod launch
     Vote: Rejected (too much drift between environments)

Did It Work?
  Status: Fully delivered, in production
  Metrics:
    - Developer setup time: 1 day (vs 3 weeks k8s)
    - Team velocity: 2x faster than if k8s was adopted
    - Production deployment: Manual but reliable (5 deployments, 0 issues)
    - Infrastructure bugs: 0 in first 2 months
  Incidents:
    - Week 1: Docker volume mount permissions issue (Linux containers)
      Impact: Mobile dev couldn't run local environment
      Resolution: Use named volumes instead of bind mounts
  Wins:
    - New engineers onboarded in 1 day (just `docker-compose up`)
    - Bug debugging faster (can run single service locally)
    - Fewer "works on my machine" issues

Gotchas Discovered:
  
  1. Compose doesn't enforce resource limits
     Issue: One engineer's service consumed all CPU, broke others' dev environment
     Lesson: Add compose overrides for dev (memory/cpu limits)
  
  2. Production drift creeping in
     Risk: Prod setup diverging from Compose over time
     Lesson: Automate prod deployment too (Compose → systemd script)
  
  3. Scaling limitations obvious at 10 engineers
     Timeline: 2026-04-15, team grows to 10 engineers
     Lesson: Revisit k8s decision when team size justifies it
     Decision needed: D200 (when to migrate to k8s, probably Q3 2026)

Future Cautions:
  - Right tool for team size (5 engineers: Compose wins, 50: k8s wins)
  - Don't stay on Compose forever; revisit at 10+ engineers
  - Prod must match local (automate same way in prod)
  - Infrastructure decisions must be revisited when constraints change
```

**Dependency Graph:**

```
Phase 0 bootstrap decisions
  ├→ D154 (PostgreSQL for primary database)
  ├→ D155 (Redis for cache)
  └→ D156 (Docker Compose for local dev) ← YOU ARE HERE
      ├→ D157 (CI/CD pipeline design)
      └→ D158 (Local dev environment setup script)

Related decisions (same pattern, different context):
  - D89 (gRPC for internal services) — infrastructure decision
  - D42 (API versioning) — scaling decision
  
Future revisit: D200 (Kubernetes adoption) — planned for Q3 2026 when team scales to 10 engineers
```

**How to Navigate from Here:**

- **Why did we choose PostgreSQL? See D154**
- **What CI/CD setup did we use? Check D157**
- **When should we migrate to Kubernetes? Planned for 2026-Q3 (D200)**
- **What was the constraint that made this decision? Team size (5 engineers) + timeline pressure**

---

# Decision Walk Patterns

When you need to trace a decision, use these 5 patterns. Each pattern answers a specific question and shows how to walk the decision graph.

## Pattern 1: Root Cause Walk (Current Problem → Which Decision Caused It?)

**Question:** "We're seeing API timeouts. Which decision led to this?"

**Graph traversal:**
1. Start with current problem (API timeouts in production)
2. Check recent decisions in affected service (D42, D89, D91)
3. Walk children of those decisions (D43 → D44, D89 → D90)
4. Check "Did It Work?" and "Gotchas Discovered" sections
5. Look for "Incidents" that match current problem

**Real example query:**
```
Problem: API timeouts (250ms p99) in user service
→ Recent decision D89 (gRPC migration)?
   - Check D89 incidents: Yes, Week 2 had Protobuf versioning issue
   - Check D89 impact: user-svc latency 50ms (not timing out)
   - Not this one
→ Recent decision D91 (gRPC monitoring)?
   - Check D91 changes to observability
   - Might be contributing (monitoring overhead?)
   - Unlikely root cause
→ Parent decision D85 (Service architecture)?
   - Check if service topology changed
   - Maybe added synchronous calls that weren't async before?
→ Walk unrelated decisions: D42 (API versioning)?
   - Check if deprecation logic added latency
   - Found it! D42 added deprecation header parsing (5ms overhead per request)
   - With 50 internal API calls per user request = 250ms added

Root cause: D42 deprecation logic, not D89 gRPC (red herring)
```

## Pattern 2: Precedent Walk (Similar Problem in Past → Which Decision Addressed It?)

**Question:** "We need to deprecate a service. How did we handle this before?"

**Graph traversal:**
1. Search brain for similar decisions (use brain-recall pattern search)
2. Find decisions with similar problem statement
3. Check "Why" and "Evidence" sections
4. Look at "Did It Work?" and lessons learned
5. Check if decision was superseded (use brain-forget status)

**Real example query:**
```
Problem: Need to deprecate legacy auth service
→ Search brain for "deprecation" decisions
   - D42 (API versioning → 6-month deprecation window) ✓
   - D45 (Client library SLA → SDK updates) ✓
   - D88 (Old payment service → replaced by D89) ✓
→ D42 most relevant (we deprecated endpoint, they deprecated API)
   - Evidence: Graduated approach works
   - Timeline: 6 months for clients to migrate
   - Lessons: Automated notifications important
   → Apply same pattern: 6-month deprecation for legacy-auth-svc
→ D88 also relevant (service deprecation, not just API endpoint)
   - How long for teams to switch? 4 weeks
   - Did we notify teams? Ad-hoc (mistake)
   - Should have been automated
   → Add notification system this time

Precedent solution: Combine D42 (timeline) + D88 (service communication)
```

## Pattern 3: Cascading Impact Walk (This Decision Affects Which Downstream Decisions?)

**Question:** "We just changed API versioning strategy. What else breaks?"

**Graph traversal:**
1. Start with decision (D42)
2. Walk all child decisions (D43, D44, D45)
3. For each child, walk their children
4. Check "Status" fields (active, archived, planned)
5. Find decisions with "depends on" links to your decision
6. Trace impact to products/services (use brain-read for topology)

**Real example query:**
```
Decision: D42 (API versioning) changed from 12-month to 6-month window
→ Immediate children: D43, D44, D45
   - D43 (Sunset header strategy): Uses D42 timeline, needs update
   - D44 (Error code taxonomy): Independent, no change
   - D45 (Client library SLA): Directly tied to deprecation timeline, needs update
→ Grandchildren:
   - D46 (SDK release cadence): Depends on D45, may need faster cadence
   - D47 (Docs versioning): Depends on D45, must document new timeline
→ Check impacted products:
   - shopapp: D42 in production, clients assume 12-month window
   - vendorapp: D42 baseline, using same 12-month approach
   - partner-api: D42 published to external docs, clients depending on it
→ Impact assessment:
   - D43 must change (header strategy tied to timeline)
   - D45 must change (SLA timeline)
   - D46 optional (can work with existing cadence)
   - D47 must update (docs show new timeline)
   - External docs must update (partner-api clients reading)

Cascading decisions to update: D43, D45, D47 (+ docs/api-versioning.md)
Requires: Communication plan to partner-api clients
```

## Pattern 4: Alternative Evaluation Walk (We Rejected Option X in D42, Why?)

**Question:** "Should we use URL versioning instead of header versioning?"

**Graph traversal:**
1. Find decision that evaluated alternatives (D42)
2. Go to "Alternatives Considered" section
3. Read "Why rejected" for each option
4. Check "Trade-offs" (what would we gain/lose?)
5. Look for similar decisions on other products
6. Check if rejected alternative is used elsewhere (brain-recall)

**Real example query:**
```
Option: URL versioning (/v1/users vs /v2/users)

In D42 alternatives:
  - Why rejected: "High cognitive load on clients, duplicated routes in server"
  - Trade-off: "Simpler for server, harder for clients"
  - Vote: Rejected (3-2 vote, showed dissent)

Why this matters:
  - We had to maintain both /v1 and /v2 routes (duplication)
  - Clients must hardcode version in URL (coupling)
  - Harder to deprecate (can't just remove route, breaks clients)

Check other decisions:
  - D35 (older API versioning): Used URL versioning, had to support 5 versions
  - D102 (new service API): Chose header versioning after learning from D35

Pattern across org: Moved away from URL versioning → header/graduated deprecation

Conclusion: Reject URL versioning (we tried it, learned it's costly)
```

## Pattern 5: Timeline Walk (Decision Lifecycle → When Superseded, Archived, Evergreen?)

**Question:** "Is this decision still valid, or has it been superseded?"

**Graph traversal:**
1. Check decision's "Status" field (Active, Archived, Superseded)
2. Look for "Locked" date vs current date
3. Search for "supersedes:" link (using brain-link)
4. Check "Did It Work?" section for ongoing applicability
5. Look for "Future Cautions" (when to revisit)
6. Use brain-forget to check archive status

**Real example query:**
```
Decision: D156 (Docker Compose for local dev)
  - Locked: 2026-01-10
  - Current date: 2026-04-10 (3 months later)
  - Status: Active
  - Check future cautions: "Revisit at 10+ engineers, probably Q3 2026"

Timeline:
  - Jan 2026: 5 engineers → Docker Compose chosen ✓
  - Feb 2026: 6 engineers → still fine
  - Mar 2026: 8 engineers → starting to show strain (manual deploys slow)
  - Apr 2026: 10 engineers → threshold reached
  - Decision point: Migrate to Kubernetes or find middle ground?

Check related decision:
  - D200 (Kubernetes adoption) → planned for Q3 2026
  - D200 supersedes D156? → Not yet, D156 still active
  - Timeline alignment: D200 planned for July 2026 (Q3)

Current decision: D156 still active, but evaluate Kubernetes migration now
Next step: Create D200 (Kubernetes decision) for Q3 launch
```

---

# Evidence Quality Guidelines

Not all evidence is equal. When reading a decision, evaluate the evidence strength. When writing a decision, ensure you have strong evidence.

## Types of Evidence

### 1. Data Evidence (Strongest)
- Load test results with methodology documented
- Metrics from production (latency, error rates, throughput)
- Customer feedback (surveys, support tickets)
- Incident reports with root cause analysis
- Benchmark comparisons (apples-to-apples)

**Examples from D42:**
- Customer survey: 6/8 want 6+ months notice (60% of sample)
- Our incident report: 32 outages from rapid deprecation (hard data)
- Competitor timelines: AWS 12mo, Stripe 18mo, GitHub 12mo (verifiable facts)

**Examples from D89:**
- Load test: gRPC 50ms vs REST 250ms (5x improvement, methodology shown)
- Benchmark: 1000 calls/sec test (specific numbers, reproducible)

### 2. Authority Evidence (Medium-Strong)
- Industry-standard practices (Google, AWS, Stripe public docs)
- Published case studies (Uber latency improvements)
- Open-source precedent (popular libraries using same pattern)
- Expert recommendations from known experts
- Academic papers on specific problem

**Examples from D42:**
- AWS API versioning guide (authoritative source)
- Stripe API lifecycle documentation (competitor precedent)
- GitHub API deprecation schedule (industry leader example)

**Examples from D156:**
- Kubernetes adoption patterns (ecosystem evidence)
- Similar startups early decisions (implicit precedent)

### 3. Experience Evidence (Medium)
- Internal incident reports (our past failures)
- Team's previous success with similar decisions
- Customer support feedback (anecdotal but from users)
- War stories from team members (pattern recognition)

**Examples from D42:**
- Our 2024 incident report (internal experience)
- Partner feedback (customer experience)

**Examples from D89:**
- Google/Uber case studies (their experience, published)

## Weak Evidence (Be Suspicious)

- **Assumptions without data:** "I think latency is the bottleneck" (test it)
- **Expert opinion alone:** "Jamie says gRPC is better" (where's the data?)
- **Anecdotal feedback:** "One customer complained" (10% vs 10 customers?)
- **Outdated comparisons:** "Node.js was slow in 2015" (it's 2026 now)
- **Missing methodology:** "Load tests showed improvement" (how many requests? traffic pattern?)
- **Single source:** Only internal opinion, no external reference

## How to Evaluate Evidence Quality When Reading a Decision

**Checklist:**
- [ ] Is this data or assumption? (Look for numbers, logs, reports)
- [ ] Is it from a reliable source? (Named company, published docs, our incident report)
- [ ] Is methodology described? (If test, how many samples? What traffic pattern?)
- [ ] Is it current? (Decision made 2026, evidence from 2024? Still relevant?)
- [ ] Are there multiple sources? (One data point or three?)
- [ ] Does it answer the right question? (Load test proves latency, but is latency the bottleneck?)

**Red flags:**
- "Everyone uses gRPC" (no data)
- "I'm pretty sure this will work" (no evidence)
- "Competitors do this" (which competitors? how do you know?)
- "Best practice" (best for what team size? context?)

## When to Challenge Evidence (Evidence Outdated or Context Changed)

**Question:** "Is this evidence still valid?"

**Challenge checklist:**
- [ ] **Timeline:** Decision 2024, evidence 2023. Is 1-year-old data still accurate?
- [ ] **Context shift:** Decision assumes REST. We now use gRPC. Does evidence still apply?
- [ ] **Scale change:** Evidence from 100 requests/sec. We now do 10k requests/sec. Bottleneck still same?
- [ ] **Technology update:** Evidence from Python 2.7. We now use Python 3.11. Still relevant?
- [ ] **Team size change:** Evidence from 20-person team. We now have 5. Same constraints?
- [ ] **Broken link:** Original incident report deleted. Can't verify root cause anymore.

**Real example challenge:**

Original D42 evidence: "AWS uses 12-month deprecation"
Question: Is AWS evidence still valid in 2026?
- AWS likely updated their strategy (check current docs)
- Our context: 5-engineer team (vs enterprise at AWS)
- Challenge: Maybe 6 months is right for us, even if AWS uses 12?
- Resolution: Re-read current AWS docs, compare with our team size

---

# Common Decision Walk Pitfalls

Avoid these mistakes when navigating decision history.

## Pitfall 1: Following Stale Decisions (Archived Decision Treated as Active)

**What happens:** You find decision D88 "Use MongoDB for cache" from 2024. It's in the brain. You implement based on it. But D88 was archived in 2025 and replaced by D150 "Use Redis for cache."

**How to detect:**
- Check decision's "Status" field (should be Active, not Archived)
- Look for "supersedes:" link (brain-link shows D150 supersedes D88)
- Check brain-forget archive status
- If decision is 6+ months old, verify it's still in use

**How to fix:**
- When reading a decision, check its status first
- If status is Archived, don't use it
- Search for superseding decision (use brain-link or brain-recall)
- If you can't find a replacement, ask the team (decision might be orphaned)

**Real example:**
```
You find: D88 "Use MongoDB for cache" (locked 2025-01-15)
Status: Archived (June 2025)
Superseded by: D150 "Use Redis for cache"
Mistake: Implementing MongoDB based on D88
Correct: Read D150 instead, understand why we switched
```

## Pitfall 2: Missing Superseded Links (Old Decision Not Marked as Replaced)

**What happens:** Two decisions exist: D42 "6-month deprecation" and D42b "3-month deprecation" (made later). You don't know which one is active. You implement using old D42, but team expected D42b.

**How to detect:**
- Search brain for similar decisions (use brain-recall)
- Multiple decisions with same topic?
- Check dates (newer decision might be override)
- Ask: Does this decision have a superseding decision?

**How to fix:**
- When adding a new decision, use brain-link to mark old decision as superseded
- Create a chain: D42 --superseded-by--> D42b
- Both decisions must link to each other (D42b --supersedes--> D42)
- Archive the old decision (use brain-forget)

**Prevention:**
- Use brain-write to create decision, it will prompt for superseding links
- brain-link tool should enforce bidirectional links

**Real example:**
```
D42 (6-month deprecation window) — locked 2026-03-15
Later: Team realizes 6 months too generous
D42-revised (3-month deprecation window) — locked 2026-04-10

Mistake: Someone implements D42 (old), not D42-revised
Fix: D42-revised should have link: "supersedes: D42"
       D42 should have link: "superseded-by: D42-revised"
       D42 should be archived
```

## Pitfall 3: Evidence Links Broken (Original Incident Report Deleted)

**What happens:** Decision D89 cites "our 2024 incident report" as evidence. But 2 years later, the incident report was deleted (storage cleanup). You can't verify the evidence anymore. Should you trust D89?

**How to detect:**
- Check if evidence links are resolvable (can you find the document?)
- Look for "Evidence" section with broken links
- Try to load incident report, test results, or benchmark
- If link is missing/deleted, mark as unverifiable

**How to fix:**
- Evidence should have stable links (e.g., to archived incident reports)
- Use version control for evidence (keep old reports in /archives)
- When referencing evidence, include enough detail to re-create it
- Don't rely on links alone; summarize findings in decision

**Prevention:**
- Store evidence in permanent locations (brain/evidence, not temp files)
- Use brain-write tool, it will enforce evidence storage
- Require at least one summary of evidence in decision (not just link)

**Real example from D42:**
```
Evidence: "2024 incident report shows 32 outages"
Link: /incidents/2024-deprecation-incident.md
Problem: File was deleted during storage cleanup

Better evidence:
  "2024 incident report (archived): 32 outages from rapid deprecation
   Root cause: Clients not notified before endpoint removal
   See: /brain/archive/2024-deprecation-incident.md (permanent archive)"
```

## Pitfall 4: Single-Source Evidence (Only Internal Opinion, No External Reference)

**What happens:** Decision D156 "Reject Kubernetes" is based only on "Infra team agrees it's overkill." No external reference. No similar companies cited. Pure opinion.

**How to detect:**
- Read "Evidence" section
- Ask: Where did this come from? Data or opinion?
- Is there external validation? (Competitors, case studies, best practices?)
- Is there internal data? (Test, metrics, incident reports?)
- If answer is "just our opinion," it's weak

**How to fix:**
- Add external reference (Google, AWS, similar startup)
- Add internal data (timeline comparison, team size analysis)
- Show methodology (why is 5-engineer threshold chosen?)
- Cite multiple sources

**Prevention:**
- brain-write should prompt for evidence sources
- Require at least 2 of: {internal data, external reference, test results}

**Real example from D156:**
```
Weak evidence:
  "Kubernetes is overkill for our team"
  (pure opinion, no data)

Better evidence:
  "Kubernetes setup: 3 weeks (measured)
   Docker Compose setup: 1 day (measured)
   Team size: 5 engineers (fact)
   Similar startups (Stripe, GitHub) used Compose at early stage (reference)"
```

## Pitfall 5: Circular Decision Graphs (D42 Depends on D89 Depends on D42)

**What happens:** D42 says "use graduated deprecation because gRPC is fast" (depends on D89). D89 says "use gRPC because API versioning is stable" (depends on D42). Reading one requires reading the other, which requires reading the first. Infinite loop.

**How to detect:**
- Walk dependency chain (D42 → D89 → D42)
- If you end up where you started, you have a cycle
- Tools should detect and warn (brain-write, brain-link validation)

**How to fix:**
- One decision must be independent (doesn't depend on other)
- Re-order: D89 doesn't depend on D42, it depends on performance needs
- D42 depends on D41 (REST principles), not D89
- Break the cycle by clarifying what each decision actually depends on

**Prevention:**
- brain-write should validate dependency graph (reject cycles)
- Use brain-link to audit graphs before committing

**Real example:**
```
Circular dependency (WRONG):
  D42 (API versioning) depends on D89 (gRPC for performance)
  D89 (gRPC) depends on D42 (versioning for stability)
  Reading D42 requires D89, reading D89 requires D42

Correct dependency:
  D89 (gRPC for performance) — independent, depends on D85 (service architecture)
  D42 (API versioning) — depends on D41 (REST principles), not D89
  They are related but not dependent
```

---

# Integration with Other Brain Skills

`brain-why` works with other brain skills to form a complete decision knowledge system.

## brain-why ← brain-read (How to Fetch a Decision)

When you invoke `/brain-why D42`, internally it calls `/brain-read` to:
1. Query the decision index (where is D42?)
2. Load the decision file from `/brain/decisions/D42.md`
3. Fetch linked context (parent decisions, child decisions)
4. Validate decision exists and is accessible

**What you invoke:** `brain-why D42`
**What happens under the hood:** brain-why calls brain-read to load D42 from disk

**Example:**
```
/brain-why D42
→ brain-why queries brain-read: "Load D42 and its context"
→ brain-read searches /brain/decisions index
→ brain-read finds /brain/decisions/D42.md
→ brain-read loads all linked decisions (D41, D43, D44, D45)
→ brain-why formats the output and returns it
```

## brain-why ← brain-write (Provenance Info Written by brain-write)

When you create a decision via `/brain-write`, it prompts you for:
1. Why? (Problem, goal, motivation, evidence)
2. When? (Date, phase, deadline)
3. By whom? (Decision maker, champion, stakeholders)
4. Alternatives considered (rejected options with rationale)
5. Impact map (what decisions depend on this?)

**brain-why depends on brain-write to record provenance.** The Why/When/By Whom/Evidence structure is created by brain-write, then navigated by brain-why.

**Example:**
```
/brain-write D42 "API Versioning Strategy"
→ brain-write prompts for all 5 provenance layers
→ Saves to /brain/decisions/D42.md
→ Later: /brain-why D42
→ brain-why reads what brain-write created
```

## brain-why → brain-recall (Recall Uses Why for Ranking)

When you search for a decision via `/brain-recall`, it looks for:
1. Decisions with similar "Why" (problem statements)
2. Similar "Evidence" (shared metrics, sources)
3. Related "Alternatives" (same design patterns)

**brain-recall uses brain-why structure to find relevant decisions.** The richness of your Why/Evidence sections makes search more useful.

**Example:**
```
/brain-recall "API versioning strategy"
→ brain-recall searches decision index
→ Finds D42, D45, D102 (all about versioning)
→ Ranks by relevance (Why matches your query)
→ Returns: "D42 has the most relevant Why"
→ You then call /brain-why D42 to read full provenance
```

## brain-why ← brain-link (Semantic Edges Show Relationships)

`brain-link` creates semantic edges between decisions:
1. "D42 enables D43" (dependency edge)
2. "D42 supersedes D88" (replacement edge)
3. "D42 similar to D102" (pattern edge)
4. "D42 conflicts with D33" (tradeoff edge)

**These links augment the Why structure.** When you call `/brain-why D42`, it shows:
- Parent decisions (what D42 depends on)
- Child decisions (what depends on D42)
- Related decisions (similar patterns)
- Superseded decisions (old versions)

**Example:**
```
/brain-link D42 --depends-on D41
/brain-link D42 --enables D43
/brain-link D42 --supersedes D88

Later: /brain-why D42
→ Shows D41 as parent, D43 as child, D88 as replaced version
→ These links are created by brain-link, navigated by brain-why
```

## brain-why → brain-forget (Understand Why Decision Was Archived)

When you archive a decision via `/brain-forget D88`, it:
1. Marks decision as Archived (status change)
2. Links it to the replacement decision (supersedes edge)
3. Records why it was archived (brief reason)
4. Keeps it in read-only status (for history)

**brain-why helps you understand the archive decision.** You can still read `/brain-why D88` to see:
- Why was this decision made? (original Why section)
- When was it archived? (archive date)
- What replaced it? (superseded-by link)
- What did we learn? (Lessons section)

**Example:**
```
Original: /brain-why D88 "MongoDB for cache"
→ Shows original decision, why we chose MongoDB

Later: Switched to Redis
/brain-forget D88 "Replaced by D150"
→ Marks D88 as Archived
→ Links D88 → D150 (superseded-by)

Later: /brain-why D88 (on archive)
→ Shows original decision + archive metadata
→ Shows why we switched: "Redis more reliable for cache"
```

## Full Integration Example: Tracing a Decision Across All Skills

```
Scenario: We want to understand why we use gRPC for service communication

Step 1: Find the decision
  /brain-read D89
  → brain-read returns: "D89 Switch to gRPC"

Step 2: Understand the provenance
  /brain-why D89
  → brain-why returns: full 5-layer walk (Why/When/By Whom/Evidence/Alternatives)
  → Shows problem: "REST latency bottleneck (250ms)"
  → Shows evidence: "Load test 50ms vs 250ms"

Step 3: Find related decisions
  /brain-recall "gRPC performance latency"
  → brain-recall returns: D89 (primary), D91 (gRPC monitoring), D85 (service arch)

Step 4: Understand relationships
  /brain-link D89
  → brain-link shows: D85 (parent), D90/D91/D92 (children)

Step 5: See current status
  /brain-why D89 (check status, gotchas, lessons)
  → Status: Active (partial rollout)
  → Gotchas: Protobuf versioning fragile
  → Future: Need better tooling

Step 6: If decision was archived
  /brain-forget D89 (hypothetically, once replaced)
  → Shows what replaced it and why
```

---



## Usage

Invoke this skill with a decision ID:

```
/brain-why D42
```

Returns a formatted walk through all 5 sections, with linked references to:
- Parent decisions (for context)
- Child decisions (for downstream impact)
- Related decisions (same pattern, different products)
- Brain files (for deep dive)

## Integration Points

- **brain-read**: Queries the decision index and loads decision files
- **Decision format**: Must follow the standardized DECISION.md schema
- **Dependency tracking**: Links to parent and child decision IDs
- **Pattern library**: Cross-references similar decisions across products

## Edge Cases

### Edge Case 1: Circular dependency in decision links (A→B→A)

**Symptom:** Provenance trace loops back on itself (parent → child → parent creates cycle).

**Do NOT:** Follow cycle infinitely. Do NOT treat circular dependency as acceptable.

**Mitigation:**
1. Detect cycle: Track visited decision IDs during traverse
2. Report when found: "Circular dependency detected: D42 → D43 → D42"
3. Break cycle by reporting at cycle detection point (not following back edge)
4. Escalate: This indicates decision graph corruption

**Escalation:** BLOCKED — Circular dependency in decision graph. Indicates data corruption or modeling error. One decision references the other incorrectly. Contact decision owners to remove circular reference and restore linear provenance chain.

---

### Edge Case 2: Decision has no parent (orphaned decision)

**Symptom:** Decision lacks `parent_decision:` field, showing no upstream context or justification.

**Do NOT:** Assume decision stands alone. Do NOT treat missing parent as authoritative.

**Mitigation:**
1. Check for `parent_decision:` field in frontmatter
2. If empty or missing, search for implicit parent: `grep -r "related.*D<id>" ~/forge/brain --include="*.md"`
3. If truly orphaned, document: "Decision D### has no recorded parent (orphan or root decision)"
4. For orphan: Review decision title and problem statement — may be foundational decision (no parent needed)

**Escalation:** NEEDS_CONTEXT — Orphaned decision may be root decision (acceptable) or indicate incomplete decision graph. Verify with decision author whether parent is missing or decision is intentionally foundational.

---

### Edge Case 3: Provenance chain broken (linked decision deleted)

**Symptom:** Decision references parent/child that no longer exists (file was archived or moved).

**Do NOT:** Ignore broken reference. Do NOT proceed with incomplete provenance.

**Mitigation:**
1. Verify referenced decision exists: `grep -r "^decision_id: D<parent-id>" ~/forge/brain --include="*.md"`
2. If not found, check archive: `grep -r "^decision_id: D<parent-id>" ~/forge/brain/archive --include="*.md"`
3. If archived: Note in provenance that parent was archived; flag for investigation
4. If truly deleted: Flag as data integrity issue — decisions should never be deleted

**Escalation:** BLOCKED — Broken provenance chain. Parent/child decision missing or archived. Cannot trace complete lineage. Contact brain maintainers to restore reference or document why parent was removed.

---

### Edge Case 4: Too many hops to root (provenance path > 5 levels)

**Symptom:** Provenance trace requires traversing > 5 parent decisions (D1 → D2 → D3 → D4 → D5 → D6 → ...).

**Do NOT:** Treat excessively deep chains as normal. Deep chains indicate poor decision granularity.

**Mitigation:**
1. Count hops while tracing parent chain
2. If > 5 hops, warn: "Long provenance chain detected (6+ decisions)"
3. Report intermediate decisions at each level (help readers understand path)
4. Recommend decision consolidation: consider merging some decisions

**Escalation:** NEEDS_COORDINATION — Very deep provenance chain suggests decision graph could be simplified. Consult decision owners about consolidating related decisions or creating summary decision at intermediate level.

---

### Edge Case 5: (EXISTING) Partially documented decisions missing sections

**Symptom:** Decision file lacks expected sections (Why, When, By Whom, Alternatives, Evidence).

**Do NOT:** Ignore gaps. Do NOT guess missing information.

**Mitigation:**
1. Check for required sections: grep for "^##" (heading level 2) in decision file
2. List missing sections: "Decision D### missing: Evidence, Alternatives Considered"
3. Flag as incomplete: "Provenance incomplete — cannot fully trace reasoning"
4. Point to original author: "Contact <decision_author> to document missing sections"

**Escalation:** NEEDS_CONTEXT — Decision partially documented. Cannot trace full provenance without missing sections. Notify decision author to complete documentation.

---

## Decision Tree: Trace Depth Strategy

```
Asked to trace provenance of decision D###
    ↓
Is decision marked as Active or Warm?
├─ NO (Cold/Archived) → Proceed with warning that decision is no longer current
└─ YES → Continue below

Is full parent chain available (all parent → parent → ... → root)?
├─ YES → Trace to root and report full chain
└─ NO → Identify break point and escalate

Do you need shallow trace (immediate parent only)?
├─ YES → Return 1 level: "D### depends on <parent>"
└─ NO → Continue below

Do you need deep trace (full decision graph from root)?
├─ YES → Check depth; warn if > 5 levels
└─ NO → Continue below

Is this decision a root decision (no parent)?
├─ YES → Check evergreen status; if not evergreen, flag as orphan
└─ NO → Continue below

Is provenance complete (all sections documented)?
├─ YES → Trace and return full Why/When/By Whom/Evidence/Alternatives
└─ NO → Trace what's available, flag gaps, escalate for completion

Result:
- Default: Trace to root, report all 5 sections (Why/When/By Whom/Evidence/Alternatives)
- If incomplete: Report available sections, flag gaps
- If deep (>5 levels): Warn about chain depth, still return full trace
- If broken reference: Flag and escalate to brain maintainers
- If circular: Detect and break at cycle point, escalate
```

---

**Linked Skills:**
- `brain-read` — load decision index and decision files
- `brain-write` — record new decisions and lessons learned
- `conductor-orchestrate` — track Phase assignments to decisions

**Example Invocation:**
```bash
/brain-why D42
/brain-why D100
/brain-why D15
```

**Output Format:** Structured markdown with 5 main sections, dependencies, lessons, and patterns.

## Checklist

Before claiming provenance trace complete:

- [ ] Decision ID located in brain files (not reconstructed from memory or git log)
- [ ] Full decision chain traced to root decision
- [ ] Alternatives section reviewed; empty alternatives section flagged as incomplete
- [ ] Evidence and contemporaneous reasoning documented as output
- [ ] Linked decisions and downstream lessons surfaced
- [ ] Circular or broken references flagged and escalated
