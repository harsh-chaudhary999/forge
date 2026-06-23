# Shared-Dev-Spec Template & Worked Example

This is the full `shared-dev-spec.md` template that Step 5.1 produces. Copy the
structure below; fill every bracketed placeholder from the negotiated contracts
and reasoning outputs. The **Design source (from intake)** block and the worked
**Sync vs Async API** conflict example are included verbatim.

Create the master `~/forge/brain/prds/<task-id>/shared-dev-spec.md`:

```markdown
# Shared Development Spec

**Status**: LOCKED — Immutable, ready for tech-planning  
**Locked at**: [ISO timestamp]  
**Locked by**: council-multi-repo-negotiate

---

## Product Request Document (PRD)

[Locked PRD from intake, all surfaces agree on scope & success criteria]

---

## Design source (from intake)

**HARD-GATE:** Copy verbatim from `prd-locked.md` the subsection **Design / UI (Q9)** (or `design_ui_scope: not applicable` when backend-only).

- `design_intake_anchor:` (verbatim from `prd-locked.md` — user’s answer to single design source of truth)
- `design_new_work:` (yes | no / engineering-only)
- `design_assets:` (human pointers: links, Confluence — optional for people)
- **`design_brain_paths`:** (paths under `~/forge/brain/prds/<task-id>/design/` — **required when `design_new_work: yes`** unless lovable repo or figma keys below are present)
- **`lovable_github_repo` + `lovable_path_prefix` (optional) + pinned ref:** (when [Lovable](https://lovable.dev) UI is authoritative — GitHub-synced code; see **`docs/platforms/lovable.md`**)
- **`figma_file_key` + `figma_root_node_ids`:** (when Figma is authoritative — enables MCP/REST)
- `design_waiver: prd_only` + owner + risk (only if present)

**Council must add one line of implementable contract for net-new UI:** e.g. “Implementation spacing/typography/component states for [feature] must match Figma nodes `<ids>` or files under `design/` listed above.”

**Downstream:** `web.md` / `app.md` (council) should name **screens and major components** implied by the PRD + design anchors so **`tech-plan-write-per-project` Section 1b.4** can map each anchor → file or `NET_NEW` without guesswork. Figma in intake is wasted if council leaves only prose and tech planning never tables nodes → components.

Surface reasoning (web, app) and tech plans **must** treat this block as authoritative for “is there new visual work?” and “where are the pixels?” — not inferred from hallway chat. **Wiki-only URLs without brain paths or figma key+nodes are not sufficient** when `design_new_work: yes` — return to intake before treating council output as complete.

---

## REST API Contract

[From contract-api-rest negotiation]

### Endpoints
- [endpoint pattern]
- [endpoint pattern]

### Versioning Strategy
[how do we version the API?]

### Error Codes
[standard error response format]

### Auth & Rate Limits
[authentication, rate limits, idempotency]

---

## Event Bus Contract

[From contract-event-bus negotiation]

### Topics & Schema
- [topic name: schema & versioning]
- [topic name: schema & versioning]

### Idempotency & Ordering
[consumer group strategy, dead-letter queues]

### Retention Policy
[topic retention, compaction]

---

## Cache Contract

[From contract-cache negotiation]

### Key Patterns
- [namespace:entity:id pattern]
- [namespace:aggregate pattern]

### TTL Strategy
[how long do cached values live?]

### Invalidation Rules
[when and how to invalidate?]

### Consistency Model
[eventual | strong | write-through]

---

## Database Schema Contract

[From contract-schema-db negotiation]

### Core Tables
- [table name]: [purpose]
- [table name]: [purpose]

### Migration Strategy
[how do we evolve the schema safely?]

### Backward Compatibility
[what schema versions coexist?]

### Indexing & Constraints
[indexes, foreign keys, unique constraints]

---

## Search Contract

[From contract-search negotiation]

### Index Mapping
- [index name]: [field mapping]
- [index name]: [field mapping]

### Analyzer Strategy
[tokenization, stemming, synonyms]

### Consistency & Refresh Policy
[how fresh is search index?]

### Reindex Procedures
[how do we reindex without downtime?]

---

## Conflict Resolution Log

[All conflicts from Section 2, with resolutions from Section 3 & 4]

### Example:

**Conflict: Sync vs Async API**
- **Surfaces affected**: backend, web, app
- **Category**: Architectural
- **Description**: Backend prefers async Kafka events for scalability. Web expects synchronous API response for immediate UI feedback. App wants offline-first queue.
- **Backend position**: Emit events to Kafka, decouple frontend from service processing
- **Web position**: Need sync API response to show confirmation to user immediately
- **App position**: Queue events locally, sync when online
- **Severity**: HIGH

**Resolution**: Hybrid approach
- Sync API responds immediately with accepted status (no processing wait)
- Backend processes async via Kafka event
- Web shows optimistic UI update, listens for webhook/event for final status
- App queues locally, syncs on reconnect
- **Decided by**: contract-api-rest + dreamer
- **Surfaces sign-off**: backend ✅ | web ✅ | app ✅ | infra ✅

---

## Surface Sign-Offs

| Surface | Reasoning Output | Contracts Signed | Status |
|---------|------------------|------------------|--------|
| Backend | backend.md | ✅ API, Events, DB, Cache, Search | LOCKED |
| Web | web.md | ✅ API, Cache | LOCKED |
| App | app.md | ✅ API, Cache, DB (local) | LOCKED |
| Infra | infra.md | ✅ DB, Cache, Events, Search | LOCKED |

---

## Status

**LOCKED** — All surfaces agree. All contracts locked. Immutable.  
Ready for → **Phase 2.11: tech-planning** (architecture review & task breakdown)

```
