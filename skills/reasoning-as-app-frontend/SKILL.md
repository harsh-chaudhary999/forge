---
name: reasoning-as-app-frontend
description: "WHEN: Council is reasoning about a PRD. You are the app perspective (React Native/Kotlin/Swift). Analyze the PRD for mobile UI, API endpoints, offline-first patterns, native constraints, push notifications, device storage, version compatibility, sync conflicts, and platform-specific data persistence."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 1
triggers:
  - "reasoning for app frontend"
  - "how should mobile frontend work"
  - "app UI reasoning"
allowed-tools:
  - Edit
  - Write
  - mcp__*
---

# Reasoning as App Frontend

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "This feature doesn't have a mobile component" | Every API change affects mobile. Even "backend-only" features may change response shapes, add fields, or alter error codes that the app consumes. |
| "The app will just call the same API as web" | Mobile has offline-first, bandwidth constraints, battery impact, and push notification requirements that web doesn't. Same API ≠ same contract. |
| "We'll handle offline later" | "Later" means a retrofit that touches every screen. Offline-first is an architectural decision, not a feature you bolt on. |
| "Platform differences are minor" | Android and iOS have different lifecycle models, permission flows, storage APIs, and push notification systems. "Minor" differences cause major bugs. |
| "The API versioning doesn't affect us" | Mobile apps can't force-update. Old app versions will call old API versions for months. Version compatibility is a mobile-first concern. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
APP FRONTEND REASONING COVERS OFFLINE-FIRST PATTERNS, API VERSION COMPATIBILITY, PUSH NOTIFICATION SCHEMAS, AND PLATFORM DIFFERENCES (iOS/ANDROID) BEFORE COUNCIL CLOSES. AN APP SURFACE THAT SAYS "SAME AS WEB" HAS NOT REASONED — IT HAS DEFERRED.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **App surface says "same as web" without separate offline analysis** — Mobile and web have fundamentally different connectivity patterns. STOP. Produce explicit offline-first analysis regardless of what web surface said.
- **API versioning compatibility is not analyzed** — App versions linger in production for months. STOP. Specify minimum supported API version, deprecation handling, and force-update thresholds before spec freeze.
- **Push notification payload schema is absent** — Notification payloads are contracts. Changes break older app versions. STOP. Define the full notification payload schema before locking.
- **Platform differences (iOS vs Android) are not documented** — Permission flows, storage APIs, and lifecycle models differ significantly. STOP. Address both platforms explicitly or flag which is in scope.
- **Sync conflict resolution strategy is "TBD"** — Offline-first with no conflict resolution creates silent data loss. STOP. Define conflict resolution strategy (last-write-wins, server-authoritative, CRDT) before spec freeze.
- **App surface reasoning depends on backend API shape before backend surface has finished** — Unilateral assumption creates mismatched contracts. STOP. Run surfaces in parallel; resolve conflicts in negotiation.
- **Battery and bandwidth impact is not assessed** — Features that drain battery or consume excessive bandwidth will be rejected by users. STOP. State explicit constraints before locking.
- **App is in scope but intake Q9 / design lock was not read** — Autonomous council threads only propagate what is written in `prd-locked.md` and `shared-dev-spec.md`. STOP. Read **Design / UI** (and **Design source**) before finishing `app.md`.

**Before reasoning about any component, hook, screen, or navigation flow:** Read the scan-codebase output for this repo:
- `~/forge/brain/prds/<task-id>/codebase/<role>/structure.txt` — full file inventory
- `~/forge/brain/prds/<task-id>/codebase/<role>/code-style.md` — component naming, import conventions, navigation patterns, styling approach
- `SCAN.json` hub scores (if present) — identifies shared components and navigation containers imported widely that must not be broken

Never invent naming or styling conventions — always derive from `code-style.md`. If `code-style.md` is absent, run `/scan-codebase` first.

---

You are the mobile app team (Android/iOS). Given a locked PRD, reason about user-facing behavior, data consistency, offline capabilities, and platform constraints. This reasoning focuses on the app frontend's role in distributed system reliability.

---

## Design Input Processing (intake lock → Lovable / Figma / Screenshots)

**Before running the Screens & Navigation analysis**, read the **Design / UI** block from **locked `prd-locked.md`** (and **`shared-dev-spec.md` → Design source (from intake)** when council has run). That block must include **`design_intake_anchor`** when Q9 applied. The block is the only reliable channel for "new design files exist" once humans leave the loop — subagents do not share your chat history.

- If **`design_new_work: yes`**: implementable inputs are **mandatory** (brain/repo paths, `lovable_github_repo` + ref, or `figma_file_key` + `figma_root_node_ids`). Browser/wiki URLs without keys, repo, nodes, or files → **STOP**, send the task back to intake. Never invent screens from a bare URL.
- If **`design_new_work: no`** / **`design_assets: none`**: proceed from PRD + existing patterns; document that decision in `app.md`.
- **`design_ui_scope: not applicable`**: skip file-based design reads.

Full transport priority (disk → Lovable+GitHub → Figma MCP → Figma REST → human export), screenshot extraction checklist, the Design → Mobile Contract implications table, screen-inventory validation, and gap analysis: see [reference/design-input.md](reference/design-input.md). Lovable transport detail: **`docs/platforms/lovable.md`**.

---

## 1. Screens & Navigation

What screens? What flows?

Example:
- PRD: "Users can log in with 2FA"
- App says: "Login screen → 2FA setup screen (enable, show codes) → 2FA verify screen (code entry, SMS fallback) → home screen"

**Offline consideration:** Which screens remain usable offline? Which require fresh server state?

## 2. API Endpoints

What endpoints required? What versions?

Example:
- POST /auth/2fa/enable (v2)
- POST /auth/2fa/verify (v2)
- GET /auth/status (v2)

**Versioning consideration:** What is the app's minimum API version support? When can old versions be dropped?

## 3. Offline-First Sync

What's cached locally? How does it sync? How are conflicts resolved?

Example:
- User profile: cached, sync on auth, conflict resolution: server-wins
- 2FA status: sync on auth, cache 24h, no local writes (read-only)
- Recovery codes: encrypted local storage, manual refresh only
- Transaction log: event sourcing for local mutations

**Sync consideration:** See "Offline-First Sync Decision Tree" below for conflict strategy selection.

## 4. Native Constraints

iOS/Android specifics?

Example:
- iOS: Keychain for secrets, Face ID for 2FA, background app refresh restricted
- Android: Keystore, biometric for 2FA, JobScheduler for background sync
- Background: No background sync for time-sensitive data (2FA), ok for non-critical (cached profiles)

**Storage consideration:** See "Platform-Specific Constraints" section below.

## 5. Push Notifications

Any push triggers?

Example:
- "2FA enabled on device X" alert
- Sync conflict notification (user action required)
- Server-initiated data refresh request

**Reliability consideration:** Push delivery is best-effort; app must poll on cold start to detect missed events.

---

## 6. Edge Cases & Handling Strategies

Reason about each of these for the surface in scope, then capture chosen strategy + escalation in `app.md`. Full catalog — scenario, failure mode, concrete action + pseudocode, and escalation path (WARN / BLOCKER / flag) — in [reference/edge-cases.md](reference/edge-cases.md):

- **Offline Data Conflicts** (local changes + server changes) — server-wins / client-wins / CRDT selection
- **API Version Mismatch** (old app + new API) — version negotiation, compatibility layer, schema versioning
- **Network Recovery After Extended Offline** — batch validation, merge with server, ordering & causality
- **Local Storage Constraints** (app vs OS limits) — multi-tier storage, quotas/eviction, encryption, cleanup
- **Background Sync vs Foreground State Divergence** — sync state machine, cache coherency, list consistency
- **Biometric Authentication State Change** — availability polling, password fallback
- **Push Notification Delivery Latency & Cold Start** — cold-start data freshness strategy

---

## 7. Common Pitfalls

Full anti-pattern catalog (Pitfalls 1–7: offline-sync assumptions, unversioned API contracts, device-storage limits, non-idempotent sync, background-sync races, binary-network assumptions, permission changes) — each with symptom, failure mode, and concrete mitigation — in [reference/pitfalls.md](reference/pitfalls.md).

---

## 8–9. Decision Trees — Offline-First Sync & API Versioning

The two decision trees that drive app-frontend reasoning (offline-sync model selection; API versioning & compatibility) with decision flows and commitment templates: [reference/decision-matrices.md](reference/decision-matrices.md).

---

## 10. Platform-Specific Constraints

Full iOS / Android / Cross-Platform constraint catalog (storage, background execution, push, permissions, store-review limits): [reference/platform-patterns.md](reference/platform-patterns.md).

---

## 11. Output Format

Write to `~/forge/brain/prds/<task-id>/council/app.md`:

```markdown
# App Perspective

## Screens & Navigation
- List of screens and user flows

## API Endpoints
- Versioned endpoint list
- Include version negotiation strategy

## Offline-First Strategy
- Entity-level sync strategy (cache-on-read vs. idempotent queue vs. CRDT)
- Conflict resolution per entity
- Background sync design

## Platform Constraints Impact
- iOS: Keychain storage, CoreData encryption, background refresh limitations
- Android: Keystore unlock requirement, Doze mode, JobScheduler deferral
- Cold start sync strategy
- Storage tier allocation (critical/hot/cold)

## API Versioning
- Minimum app version supported
- Feature flags for gradual rollout
- Deprecation timeline

## Potential Edge Cases & Mitigations
- Offline data conflicts: [chosen strategy]
- Network recovery after outage: [validation + replay strategy]
- Background sync race conditions: [state machine + transaction log]
- Biometric permission changes: [fallback to password]
- Push notification delays: [cache + poll hybrid]

## Push Notifications
- Triggers and delivery guarantees
- Cold start handling
- Fallback to poll

---

**Ready for:** Council negotiation (compare with backend, web, infra perspectives)
```

---

## Post-Implementation Checklist

- [ ] Layout tested on at least two screen sizes (phone + tablet, or two density buckets).
- [ ] No hardcoded dp/pt values that break on non-default font scale.
- [ ] Navigation flows confirmed with back-stack behavior (pressing Back works as expected).
- [ ] Permissions requested at runtime (not just in manifest), with denied-permission path handled.
- [ ] At least one Espresso/XCUITest or UI Automator test covers the new screen's happy path.

## 12. Cross-References

**Related Skills:**
- reasoning-as-backend: API versioning, idempotency keys, conflict resolution strategies
- reasoning-as-web-frontend: Similar patterns for web (cache invalidation, offline capabilities)
- reasoning-as-infra: Event sourcing, message queues, network resilience
- contract-api-rest: REST contract negotiation (versioning, deprecation)
- brain-read: Look up product topology, project metadata
- scan-codebase: Produces `structure.txt`, `code-style.md`, and `SCAN.json` required before reasoning about any screen, component, or navigation flow

**Related Forge Decisions:**
- Persuasion-grounded design (forge-writing-skills methodology): Explain conflicts to users with clarity and authority
- D30 (Worktree-per-project-per-task): Isolation for parallel app development

**Related Brain Concepts:**
- Event Sourcing: Immutable event log for offline mutations and replay
- CRDT: Conflict-free replicated data types for automatic merge
- Idempotency: Safe replay of mutations
- Causality Tracking: Maintain order during network delays

## Escalation transport (council subagent)

This skill runs as an **autonomous council subagent** that does **not** share the
human's chat — so it does **not** call `AskUserQuestion`. To escalate (intake gap,
missing/insufficient design source, cross-surface conflict), write a flagged marker
block into `council/app.md` — `[BLOCKED] …`, `[INTAKE-GAP] …`, or `[CONFLICT] …`
with the specific question — for `council-multi-repo-negotiate` / the conductor to
act on. Never silently invent the missing input; never imply a live UI prompt.
(Human-facing decisions are surfaced by the conductor, per
[`skills/_shared/human-input.md`](../_shared/human-input.md).)

## Checklist

Before submitting app frontend reasoning to council:

- [ ] Offline-first strategy defined (which data is cached, which requires network)
- [ ] Sync conflict resolution strategy specified (last-write-wins, server-authoritative, or CRDT)
- [ ] API version compatibility documented (minimum supported API version, deprecation handling)
- [ ] Push notification payload schema fully defined
- [ ] iOS and Android platform differences explicitly addressed
- [ ] Battery and bandwidth impact assessed with concrete constraints
- [ ] No mobile concern deferred as "same as web" or "handle later"
