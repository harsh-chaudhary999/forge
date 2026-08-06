---
name: council-multi-repo-negotiate
description: "WHEN: A locked PRD needs to be negotiated across all surfaces before implementation begins. Invokes all 4 surface reasoning skills, all 5 contract skills, resolves conflicts, outputs locked shared-dev-spec.md."
type: rigid
effort: high
requires: [brain-read, reasoning-as-backend, reasoning-as-web-frontend, reasoning-as-app-frontend, reasoning-as-infra, contract-api-rest, contract-event-bus, contract-cache, contract-schema-db, contract-search]
version: 1.0.8
preamble-tier: 3
triggers:
  - "negotiate across repos"
  - "multi-repo council"
  - "cross-repo spec alignment"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
---

# Council Multi-Repo Negotiate

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Blocking prompts follow **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. When multiple human decisions or conflict forks remain, follow **`using-forge`** **Multi-question elicitation** (**transcript-visible**, **one primary topic per message**, **reconcile** after replies). See **`using-forge`** **Interactive human input**.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

## Product terminology (`terminology.md`)

**Before** freezing contracts, **Read** `~/forge/brain/prds/<task-id>/terminology.md` if it exists. **Align** field names, resource names, and event type strings with the **locked** rows (or update `terminology.md` with a **Revision** row and **blocking** user confirm per [docs/terminology-review.md](../../docs/terminology-review.md) when council introduces a **rename**). **After the rename is decided and the Revision row is added:** if **every** table row and Notes cell is now resolved, set frontmatter **`open_doubts: none`** (or leave **`pending` only** while a row still has an open product question) — **spec-freeze** blocks freeze on `pending` without a waiver, so a finished rename must include clearing frontmatter when the sheet is clear. **`[TERMINOLOGY]` line in `conductor.log` is mandatory — see Step 5.4 (last in this section) below** (the **only** append for `/council` after **forge-council-gate**). Append **once at end of this council run**; on a **later** run, append **again** if `open_doubts` changes (append-only log; **`prompt-submit-gates.cjs` uses the last [TERMINOLOGY] line only**). Forge UI vocabulary: [forge-glossary](../forge-glossary/SKILL.md) — not this file.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "Only 2 surfaces are affected, skip the other 2" | Surfaces you skip are surfaces that discover conflicts during build instead of council. All 4 must reason, even if their contribution is "no impact." |
| "The contracts are obvious from the PRD" | PRDs describe features, not interfaces. Contracts emerge from negotiation — they cannot be inferred unilaterally. |
| "We'll resolve conflicts during build" | Build-time conflict resolution means rework, re-testing, and re-eval. Council-time resolution costs minutes, not hours. |
| "Backend can decide the API shape alone" | Every surface consumes or produces data. Unilateral API design creates contracts the frontend can't fulfill. |
| "This is a single-repo change, council is overkill" | Single-repo changes still affect contracts (cache keys, event schemas, DB migrations). Council validates cross-service impact even for single-repo PRDs. |
| "I'll lock the spec now and amend it later if needed" | Amendments after spec-freeze require full re-negotiation. Get it right in council or pay the re-negotiation cost. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO IMPLEMENTATION STARTS BEFORE ALL 4 SURFACES HAVE REASONED AND ALL 5 CONTRACTS ARE LOCKED. A PARTIAL COUNCIL IS NOT A COUNCIL.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Fewer than 4 surfaces produced reasoning outputs** — A skipped surface is a surface that will surface conflicts during build. STOP. All 4 surfaces must produce reasoning, even if "no impact."
- **Fewer than 5 contracts are negotiated** — Any unagreed contract becomes an integration failure during build. STOP. All 5 contracts (REST, events, cache, DB, search) must be explicitly negotiated.
- **Shared-dev-spec contains "TBD" in any field** — Unresolved TBDs become undiscovered bugs. STOP. Resolve every TBD before spec-freeze is called.
- **Conflict between two surfaces is "deferred to implementation"** — Build-time conflict resolution costs 10x more than council-time resolution. STOP. Invoke dreamer to resolve the conflict now.
- **Spec is frozen before all surface reasoning files are written to brain** — Provenance is lost. STOP. Write all surface outputs to brain before calling spec-freeze.
- **Council is invoked before PRD is locked** — Unlocked PRD means the scope can change mid-council. STOP. Confirm PRD lock (brain decision ID) before invoking any surface reasoning.
- **Web or app is in scope but intake design fields never reach `shared-dev-spec.md`** — Subagents and parallel surface skills only see what is written down. If `design_new_work` / `design_assets` from `prd-locked.md` are not copied into the spec, autonomous reasoning invents UI from prose alone. STOP. Paste the intake **Design / UI** block verbatim under `## Design source (from intake)` before surface work is treated as complete.
- **`design_new_work: yes` but `shared-dev-spec.md` lacks implementable design** — Missing **`design_brain_paths`** and missing **`lovable_github_repo`** (+ pinned ref) and missing **`figma_file_key` + `figma_root_node_ids`**, with no **`design_waiver: prd_only`**, means council cannot lock pixels. STOP. Re-open intake or add materialized `design/` artifacts before treating negotiation as complete.
- **Only 1-2 surfaces are "affected" so the rest are skipped** — Surfaces that appear unaffected often discover hidden dependencies. STOP. All surfaces must reason, even if briefly.
- **External parity gate skipped** — No `~/forge/brain/prds/<task-id>/parity/external-plan.md`, no completed `parity/checklist.md` (from **`docs/parity-checklist-template.md`**), and no `parity/waiver.md` with `parity_waiver: true` before **`spec-freeze`**. STOP. Materialize parity or record waiver (see **`spec-freeze`** Step 0).
- **PRD implies gated / variant UI or post-condition behaviour (e.g. after deadline), web in scope, but spec lacks a locked surface matrix** — No enum / flag / route allow-list describing which UI exists in which state. STOP. Add contract text or **`WAIVER: …`** + owner + ticket until intake supplies it.
- **PRD names a third-party verifier / identity or document provider, but spec lacks retention + secret handling** — No rows for token lifetime, hash vs raw storage, encryption boundary, audit. STOP. Lock in **`shared-dev-spec`** or **`contract-*`** or **`WAIVER`** — not silence.
- **PRD puts message broker on critical path, but spec lacks choreography** — Unclear what advances the next stage (sync HTTP vs which consumer), idempotency, DLQ. STOP. Lock in **`contract-event-bus`** or **`WAIVER`** — not silence.
- **Product cohorts / segmentation without a locked matrix** — PRD implies segment-specific behavior but brain lacks **`touchpoints/COHORT-AND-ADJACENCY.md`** (see **`docs/adjacency-and-cohorts.md`** + template **`docs/templates/adjacency-cohort-and-signals.template.md`** Section A) with **USER/PO-backed** rows or **waivers**. STOP. No **`SPEC_INFERENCE`**-only cohort policy at council close.
- **Trust / persistence claims without signal anchors** — PRD lines assert stored truth but there is no **`touchpoints/PRD-SIGNAL-REGISTRY.md`** (same doc + template Section B) mapping to **table.column**, **topic+schema**, **cache key**, or **eval fixture**. STOP. Add rows or **`WAIVER`**.

Master orchestration skill that brings together all 4 surface reasoning skills and all 5 contract skills to negotiate conflicts and lock the shared-dev-spec.

## Section 1: Load PRD & Surfaces

### Step 1.1: Read Locked PRD
Use `/brain-read` to load the locked PRD from intake:
```
/brain-read [product-id] [task-id]
```

Verify the PRD is locked (status = LOCKED). Extract:
- Scope: what are we building?
- Success criteria: what must work?
- Affected repos: which codebases change?
- Interfaces: what contracts matter (API, events, cache, DB, search)?
- **Design / UI (from intake `prd-locked.md`):** `design_new_work`, `design_assets`, optional `design_waiver`, or `design_ui_scope: not applicable`. When web or app repos are in scope, these fields **must exist** (per `intake-interrogate` Q9). **Pass the full locked PRD text (including the Design / UI section) into every surface reasoning invocation** so agents do not rely on chat memory alone.
- **Cohort & adjacency (before surface work completes):** Follow **`docs/adjacency-and-cohorts.md`** — read **`discovery-adjacency.md`** if present; **`touchpoints/COHORT-AND-ADJACENCY.md`** must be **drafted or waived** before council is treated as done when the PRD segments users or data.

### Step 1.2: Invoke All 4 Surface Reasoning Skills in Parallel
Invoke these skills in parallel (no dependencies between them):

```
/reasoning-as-backend [locked-prd]
/reasoning-as-web-frontend [locked-prd]
/reasoning-as-app-frontend [locked-prd]
/reasoning-as-infra [locked-prd]
```

**What each reasoning skill returns:**

- **backend.md**: REST/gRPC endpoints, data models, service boundaries, async patterns, performance SLOs
- **web.md**: React/Next.js components, state management, API client contracts, performance budgets, accessibility
- **app.md**: React Native/Kotlin/Swift UI, offline-first patterns, native constraints, push notifications, device storage
- **infra.md**: MySQL schema, Redis caching strategy, Kafka topics, Elasticsearch indexes, monitoring, scaling

Store outputs in: `~/forge/brain/prds/<task-id>/council/` — each reasoning skill writes its own file there (`backend.md`, `web.md`, `app.md`, `infra.md`) per `reasoning-as-*`'s own Output section; this skill only reads them back, it does not rename or relocate them.

---

## Section 2: Identify Conflicts

### Step 2.1: Compare Across Surfaces

Read all 4 reasoning outputs and compare systematically against the **Comparison Matrix** (API protocol, async pattern, caching, data model, search) in **[`reference/conflict-catalog.md`](reference/conflict-catalog.md)** — flag any dimension where surfaces mismatch.

### Step 2.2: Categorize Conflicts

Label each identified conflict by category and severity: **Architectural** (HIGH), **Contract** (MEDIUM), **Priority/Scope** (MEDIUM), **Non-blocking Mismatch** (LOW). Full category definitions, examples, and severities are in **[`reference/conflict-catalog.md`](reference/conflict-catalog.md)**.

### Step 2.3: Document Conflict Log

For each conflict, create an entry using the **conflict-log entry template** (surfaces affected, category, description, per-surface positions, severity, status = UNRESOLVED) in **[`reference/conflict-catalog.md`](reference/conflict-catalog.md)**.

---

## Section 3: Invoke Contract Skills

### Step 3.1: Route Conflicts to Contract Skills

For each HIGH or MEDIUM severity conflict, invoke the relevant contract skill. The full **contract-skill routing table** (conflict type → contract skill → input → output file) is in **[`reference/conflict-catalog.md`](reference/conflict-catalog.md)**.

### Step 3.2: Invoke Contract Skills in Parallel

```
/contract-api-rest [conflict-log] [surface-positions]
/contract-event-bus [conflict-log] [surface-positions]
/contract-cache [conflict-log] [surface-positions]
/contract-schema-db [conflict-log] [surface-positions]
/contract-search [conflict-log] [surface-positions]
```

Each contract skill will:
1. Analyze the conflict positions
2. Propose a negotiated solution that satisfies all surfaces
3. Document trade-offs and rationale
4. Return a locked contract that all surfaces can sign off on

### Step 3.3: Collect Negotiated Contracts

Store outputs, per the `<domain>-contract.md` convention (`contract-event-bus` cites this explicitly as "council convention"):
- `~/forge/brain/prds/<task-id>/contracts/api-contract.md`
- `~/forge/brain/prds/<task-id>/contracts/event-contract.md`
- `~/forge/brain/prds/<task-id>/contracts/db-contract.md`
- `~/forge/brain/prds/<task-id>/contracts/search-contract.md`

**Cache is the exception:** `contract-cache` writes only into `shared-dev-spec.md`'s cache section (no standalone `cache-contract.md`) — treat that as this skill's actual convention, not a gap to fill.

---

## Section 4: Resolve Unresolved Conflicts

### Step 4.1: Identify Unresolved Conflicts

After contract skill invocation, check if all conflicts are resolved:
- If contract skill found a negotiated solution, mark as RESOLVED
- If contract skill could not negotiate a solution, mark as UNRESOLVED

### Step 4.2: Escalate to Dreamer (if needed)

For UNRESOLVED conflicts that require human-level counterfactual reasoning, invoke the `dream-resolve-inline` skill (via the `/dream` command):

```
/dream [unresolved-conflict]
```

Provide to dreamer:
- The conflict description
- All surface positions (backend, web, app, infra)
- Contract skill's attempt to negotiate
- Request: counterfactual reasoning to find creative solutions or trade-offs

Dreamer will return:
- Counterfactual scenario (e.g., "what if we accept offline-first but sync critical paths?")
- Recommended resolution with rationale
- Signed-off decision

### Step 4.3: Document Decision Trail

For each resolved conflict, update the conflict log using the **decision-trail entry template** (status = RESOLVED, resolution, reasoning, decided-by, surfaces sign-off) in **[`reference/conflict-catalog.md`](reference/conflict-catalog.md)**.

---

## Section 5: Output Shared-Dev-Spec

### Step 5.1: Consolidate All Agreements

Create the master `~/forge/brain/prds/<task-id>/shared-dev-spec.md`. It must contain, in order, these sections (full fill-in template + worked conflict example in **[`reference/spec-template.md`](reference/spec-template.md)**):

1. **Header** — `Status: LOCKED`, `Locked at: [ISO timestamp]`, `Locked by: council-multi-repo-negotiate`.
2. **Product Request Document (PRD)** — the locked PRD from intake; all surfaces agree on scope & success criteria.
3. **Design source (from intake)** — **HARD-GATE:** copy verbatim from `prd-locked.md` the **Design / UI (Q9)** subsection (or `design_ui_scope: not applicable` when backend-only). Includes `design_intake_anchor`, `design_new_work`, `design_assets`, and — when `design_new_work: yes` — **`design_brain_paths`** OR **`lovable_github_repo` + pinned ref** (see **`docs/platforms/lovable.md`**) OR **`figma_file_key` + `figma_root_node_ids`**, else `design_waiver: prd_only` + owner + risk. Council must add one line of implementable contract for net-new UI, and `web.md`/`app.md` must name the screens/components so `tech-plan-write-per-project` Section 1b.4 can map each anchor → file or `NET_NEW`. **Wiki-only URLs without brain paths or figma key+nodes are not sufficient** when `design_new_work: yes` — return to intake. Full field-by-field notes in **[`reference/spec-template.md`](reference/spec-template.md)**.
4. **REST API Contract** (from contract-api-rest) — endpoints, versioning, error codes, auth & rate limits.
5. **Event Bus Contract** (from contract-event-bus) — topics & schema, idempotency & ordering, retention.
6. **Cache Contract** (from contract-cache) — key patterns, TTL, invalidation, consistency model.
7. **Database Schema Contract** (from contract-schema-db) — core tables, migration strategy, backward compatibility, indexing & constraints.
8. **Search Contract** (from contract-search) — index mapping, analyzer, consistency & refresh, reindex procedures.
9. **Conflict Resolution Log** — all conflicts from Section 2 with resolutions from Sections 3 & 4.
10. **Surface Sign-Offs** — table of each surface's reasoning output, contracts signed, LOCKED status.
11. **Status** — `LOCKED`, ready for Phase 2.11 (tech-planning).

### Step 5.2: Validate Spec Completeness

Before marking LOCKED, verify:
- [ ] All 4 surface reasoning outputs included/summarized
- [ ] All 5 contracts included and negotiated
- [ ] All conflicts documented and resolved
- [ ] All surfaces have signed off (✅ status)
- [ ] No open questions or TODO items
- [ ] Spec is internally consistent (e.g., API endpoints match DB schema, cache keys match what infra supports)

### Step 5.3: Use brain-write to Lock Spec

```
/brain-write [task-id] [shared-dev-spec.md]
```

This marks the spec as immutable in the brain.

### Step 5.4: Append [TERMINOLOGY] line to `conductor.log` (MANDATORY — /council session-resume)

**Owning step** for `prompt-submit-gates.cjs` on the **standalone /council** path (this skill runs **last**; **forge-council-gate** does **not** append — avoid duplicate [TERMINOLOGY] lines). After **`terminology.md`** matches the negotiated `shared-dev-spec` and frontmatter / **Revision** rows are updated, **append one line** to `~/forge/brain/prds/<task-id>/conductor.log`:

`[TERMINOLOGY] task_id=<id> file=present|missing status=<draft|review|locked|unknown> open_doubts=<none|pending|unknown>`

- **Hooks use only the last [TERMINOLOGY] line** in the file; append a **new** line on a **later** council or conductor step if `open_doubts` changes.
- **conductor-orchestrate** may have logged already in a full **/forge** run; a line appended **here** at council close is the **authoritative handoff of session state** for the task to the next prompt (via `prompt-submit-gates.cjs`).

---

## Edge Cases & Fallback Paths

Eight diagnosis/response/escalation cards live in **[`reference/edge-cases.md`](reference/edge-cases.md)** (load on demand):

1. **Incompatible technical requirements** (API v2 breaking change vs consumer that can't refactor) → dreamer, else NEEDS_CONTEXT.
2. **PRD updated mid-negotiation** (reasoning outputs stale) → pause, re-run affected reasoning/contracts, else escalate.
3. **No conflicts — all surfaces agree** → valid; still run contracts, still produce spec; mark NO_CONFLICTS_DETECTED.
4. **New surface constraint invalidates a locked contract** (e.g. infra scaling limit) → re-negotiate or workaround; re-lock with new timestamp.
5. **Council cannot converge** (incompatible architecture recommendations) → dreamer, else NEEDS_CONTEXT to set priorities.
6. **Negotiation reveals a missing service** not in PRD → scope decision: add / defer / redesign — NEEDS_CONTEXT.
7. **Circular dependency in spec validation** → break the cycle (defer / redesign / intermediate service); document why.
8. **Brain-write fails** (git conflict in brain repo) → pull, merge, retry; if unresolvable → BLOCKED.

---

## Execution Checklist

- [ ] Read locked PRD via `/brain-read`
- [ ] Invoke all 4 reasoning skills in parallel
- [ ] Collect outputs to `reasoning/` folder
- [ ] Compare surfaces, identify conflicts
- [ ] Categorize conflicts (Architectural, Contract, Priority, Non-blocking)
- [ ] Document conflict log
- [ ] Invoke relevant contract skills in parallel
- [ ] Collect negotiated contracts
- [ ] Identify any unresolved conflicts
- [ ] Escalate unresolved conflicts to `dream-resolve-inline` (via `/dream`)
- [ ] Document decision trail for all conflicts
- [ ] Consolidate shared-dev-spec.md with all sections (including **Design source (from intake)** when web or app is in scope)
- [ ] **Parity:** Create `parity/` with **`external-plan.md`** OR completed **`checklist.md`** (from **`docs/parity-checklist-template.md`**) OR **`waiver.md`** — before **`spec-freeze`**
- [ ] **Optional:** Write **`delivery-plan.md`** (rollout, flags, pyramid targets, open questions) — non-frozen; links spec headings only
- [ ] Validate spec completeness
- [ ] Use `/brain-write` to lock spec
- [ ] Report: DONE, spec locked, parity satisfied — ready for **`spec-freeze`** then tech-planning

---

## Notes

- **Parallelization**: Sections 1.2 and 3.2 can run in parallel within the skill (no inter-dependencies)
- **Escalation**: Unresolved conflicts are escalated to dreamer, not left hanging
- **Immutability**: Once locked, the shared-dev-spec cannot be modified without explicit unlock + re-negotiation
- **Next Phase**: Output of this skill feeds directly into Phase 2.11 (tech-planning), which breaks the spec into implementation tasks

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] All 5 contracts (REST API, event bus, cache, DB schema, search) reached `negotiated` status — no contract is still `open`, `draft`, or `disputed`
- [ ] `shared-dev-spec.md` is committed to the brain under `~/forge/brain/prds/<task-id>/` with a `task_id:` anchor in the file header, not merely written to disk
- [ ] A `[P2-SPEC-FROZEN]` conductor marker (or equivalent `[SPECLOCK]` decision record) is logged in `conductor.log` — confirming council is complete and spec is ready for `spec-freeze`
- [ ] No contract is left in `open` or `disputed` state before proceeding: every unresolved conflict was escalated to the dreamer and resolved with a signed-off decision record
- [ ] The `[TERMINOLOGY]` line is appended to `conductor.log` with `open_doubts=none` (or `pending` only if an explicit waiver is recorded) — `spec-freeze` blocks on `pending` without a waiver

## Checklist

Before claiming council complete:

- [ ] All 4 surfaces (backend, web frontend, app frontend, infra) produced reasoning outputs
- [ ] All 5 contracts negotiated (REST API, event bus, cache, DB schema, search)
- [ ] No TBD fields remain in shared-dev-spec
- [ ] **Design source** subsection present or explicitly `not applicable` when scope includes web/app
- [ ] All cross-surface conflicts resolved — none deferred to implementation
- [ ] shared-dev-spec.md locked and written to brain via brain-write
- [ ] spec-freeze invoked to prevent post-council mutations
