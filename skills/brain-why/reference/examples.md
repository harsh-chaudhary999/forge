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
