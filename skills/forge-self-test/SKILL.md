---
name: forge-self-test
description: "WHEN: You need to validate the entire Forge pipeline works end-to-end on a real product. Run before declaring Forge production-ready or after major changes to skills/agents."
type: rigid
requires: [forge-intake-gate, forge-council-gate, forge-tdd, forge-eval-gate, forge-verification, review-readiness]
version: 2.0.1
preamble-tier: 3
triggers:
  - "test forge itself"
  - "forge self-check"
  - "validate forge setup"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Forge Self-Test (End-to-End Validation)

**HARD-GATE: Do NOT declare Forge production-ready without running this skill.**

---

## Anti-Pattern Preamble: Why Agents Skip Self-Test

| Rationalization | The Truth |
|---|---|
| "Individual skills work in isolation, the system must work end-to-end" | Integration is where systems fail. Individual skill correctness does not imply pipeline correctness. Run the full test. |
| "We've run partial tests, that's sufficient validation" | Partial tests only validate partial pipelines. The self-test is the only complete signal. Partial != sufficient. |
| "The seed product is synthetic, real products will differ" | The seed product is deliberately synthetic and adversarial. If Forge can't handle the seed, it can't handle real products. |
| "I just changed one skill, it shouldn't affect the pipeline" | Single-skill changes propagate through the pipeline via shared-dev-spec, contracts, and brain. Always revalidate end-to-end. |
| "Self-test takes too long, we'll trust incremental testing" | Incremental tests catch unit failures. Self-test catches integration, sequencing, and context failures. Both required. |
| "The seed product is old, it may not reflect current features" | Seed product is updated with Forge. It's the canonical test target. If it's stale, update it — don't skip the test. |
| "Output looks right from a spot check, I'll declare it working" | Spot checks miss 60% of pipeline failures (latent failures in downstream phases). Full self-test or BLOCKED. |
| "This is just a documentation change, no need to self-test" | Documentation errors in skills propagate to AI behavior. Self-test validates behavior, not just code. |

---

## Iron Law

```
FORGE IS NOT PRODUCTION-READY UNTIL SELF-TEST PASSES ALL 5 PHASES.
```

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Skipping phases** — If someone suggests running only phases 1-3 "because eval is slow", STOP. All 5 phases are required.
- **Using a non-canonical seed product** — If the test product is not the official ShopApp seed, STOP. Self-test must run on the canonical seed.
- **Claiming success from phase output alone** — If the claim is "phase X output looks right" without verifying acceptance criteria, STOP. Evidence required.
- **Bypassing brain persistence** — If brain decisions are not being written during the test run, STOP. Brain is part of the pipeline.
- **Accepting YELLOW eval verdict as pass** — If eval returns YELLOW, STOP. Self-test requires GREEN. YELLOW is a failure mode.
- **Running phases out of order** — If council is invoked before intake locks, STOP. Phases are strictly sequential.
- **Reusing brain state from a prior run** — If brain decisions from a previous self-test run are bleeding into the current run, STOP. Each run gets a fresh brain path.

---

## Introduction: Why Self-Test Matters

The self-test validates that Forge works end-to-end on a real product. Without it, individual skills may work in isolation, but the orchestration pipeline can fail catastrophically. The self-test:

1. **Validates all skills work in concert** — Proves that intake, council, build, eval, and brain operations don't conflict
2. **Pressure-tests against realistic scenarios** — Uses the seed product (ShopApp), a 4-repo e-commerce stack that exercises all Forge capabilities
3. **Detects regressions before plugin distribution** — Ensures no recent changes broke the pipeline
4. **Runs against canonical seed product** — Guarantees reproducible results and parity across all environments

**Self-test is not optional. It is the only complete validation signal.**

---

## Seed Product

**ShopApp** — A 4-repo e-commerce product used as the canonical self-test target.

| Repo | Role | Language | Key Files |
|---|---|---|---|
| `shared-schemas` | Protobuf definitions | Protobuf | `proto/products.proto`, `proto/orders.proto`, `proto/users.proto` |
| `backend-api` | REST API server | Node.js / Express | `src/api/favorites.js`, `src/db/migrations/`, `src/cache/` |
| `web-dashboard` | Admin dashboard | TypeScript / Next.js | `pages/favorites.tsx`, `components/FavoritesGrid.tsx` |
| `app-mobile` | Customer app | Kotlin / Android | `app/src/main/java/com/shopapp/favorites/`, `app/src/test/` |

**Location:** `seed-product/shopapp/` (relative to Forge root)

**PRD under test:** `seed/prds/01-favorites-cross-surface-sync.md`
— Cross-surface sync of user favorites (backend, web, mobile, shared schemas all touched).

**Seed availability — local-only by design.** `seed-product/` and `seed/` are **gitignored**
(kept out of the repo so the distribution stays lean). A fresh clone therefore has **no** seed,
and Phase 0 will report **BLOCKED — seed not present** until you provide one. This is **expected
on a clean checkout, not a pipeline regression.** To run the self-test, materialize the fixture
locally first: recreate `seed-product/shopapp/` (the 4-repo stack above) + `seed/prds/01-favorites-cross-surface-sync.md`,
or point the run at any local multi-repo product with an equivalent cross-surface PRD. The fixture
is maintained locally by Forge maintainers and is never pushed to the remote.

---

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/self-test-procedure.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

## Cross-References: Skills & Concepts Used in Self-Test

**Core Pipeline Skills:**
- `/forge-intake-gate` — Phase 1 (PRD locking)
- `/forge-council-gate` — Phase 2 (multi-surface negotiation)
- `/forge-tdd` — Phase 3 (TDD discipline enforcement)
- `/forge-eval-gate` — Phase 4 (eval orchestration)
- `/dream-retrospect-post-pr` — Phase 5 (retrospective)

**Surface Reasoning Skills (Phase 2):**
- `reasoning-as-backend` — Backend API design
- `reasoning-as-web-frontend` — Web UI design
- `reasoning-as-app-frontend` — Mobile app design
- `reasoning-as-infra` — Infrastructure & deployment design

**Contract Negotiation Skills (Phase 2):**
- `contract-api-rest` — REST API terms
- `contract-schema-db` — Database schema terms
- `contract-cache` — Cache layer terms
- `contract-event-bus` — Event bus/Kafka terms
- `contract-search` — Search index terms

**Build & Review Skills (Phase 3-4):**
- `worktree-per-project-per-task` — Isolated task environments
- `dev-implementer` — Implementation & self-review
- `tech-plan-write-per-project` — Per-repo planning
- `forge-trust-code` / `spec-reviewer` — Spec compliance review
- `code-quality-reviewer` — 11-point quality framework

**Eval Driver Skills (Phase 4):**
- `eval-product-stack-up` — Start all services
- `eval-driver-api-http` — REST API testing
- `eval-driver-db-mysql` — Database validation
- `eval-driver-cache-redis` — Cache verification
- `eval-driver-bus-kafka` — Event bus validation
- `eval-driver-web-cdp` — Web UI testing (Chrome DevTools)
- `eval-driver-android-adb` — Mobile UI testing (ADB)
- `eval-judge` — Aggregate verdicts

**Brain & Decision Skills (All Phases):**
- `brain-write` — Record decisions
- `brain-read` — Inspect decisions
- `brain-recall` — Search decisions
- `brain-link` — Connect decisions

**Troubleshooting Skills (All Phases):**
- `self-heal-systematic-debug` — 4-phase debugging (investigate, localize, fix, verify)
- `self-heal-locate-fault` — Identify which service failed
- `dream-resolve-inline` — Conflict resolution

**Seed Product:**
- Location: `seed-product/shopapp/`
- 4 repos: shared-schemas, backend-api, web-dashboard, app-mobile
- Test PRD: `seed/prds/01-favorites-cross-surface-sync.md`

**Brain Layout:**
- Location: `brain/self-test/{SELF_TEST_RUN_ID}/`
- Decision format per `forge-brain-layout`
- IDs: PRDLK-*, SPECLOCK-*, DREAMER-*, RETROSPECT-*

---

## Edge Cases & Fallback Paths

### Case 1: Phase Fails Mid-Run
- **Symptom:** Phase 3 fails at task 7 of 12 (4 tasks left)
- **Do NOT:** Skip failed tasks and continue to Phase 4
- **Action:**
  1. Record failure in brain (which task, which error, which repo)
  2. Diagnose: skill bug? seed product issue? infrastructure issue?
  3. Fix the root cause (not the symptom)
  4. Re-run the failed phase from the failed task (not from Phase 1 unless brain state is corrupted)
  5. Continue forward only when phase passes completely

### Case 2: Eval Returns YELLOW
- **Symptom:** eval-judge returns YELLOW (all critical passed, some non-critical failed)
- **Do NOT:** Accept YELLOW as self-test pass
- **Action:**
  1. Read YELLOW verdict details (which scenarios failed, why)
  2. Determine: is this a Forge skill bug or a seed product limitation?
  3. If skill bug: fix skill, re-run eval
  4. If seed product limitation: document as known limitation, update seed product
  5. Self-test requires GREEN

### Case 3: Infrastructure Unavailable (MySQL, Kafka, etc.)
- **Symptom:** `eval-product-stack-up` fails because Redis or Kafka not running
- **Do NOT:** Skip drivers that depend on unavailable infrastructure
- **Action:**
  1. Start the missing infrastructure
  2. Re-run `eval-product-stack-up`
  3. If infrastructure cannot be started: escalate BLOCKED
  4. Do NOT run partial eval and claim success

### Case 4: Dreamer Cannot Resolve Council Conflict During Test
- **Symptom:** Backend and app surfaces deadlock on sync strategy (push vs. pull)
- **Do NOT:** Skip conflict resolution and proceed with one surface's proposal
- **Action:**
  1. Record the conflict in brain
  2. Invoke dreamer inline
  3. Dreamer decides: push (lower app battery drain) or pull (simpler backend)
  4. Record dreamer decision with rationale
  5. Continue council with resolved conflict

### Case 5: Self-Test Reveals a Skill Bug
- **Symptom:** `forge-tdd` skill is not enforcing RED step (allowing implementation before test failure is confirmed)
- **Do NOT:** Patch around the skill bug, mark self-test as passed
- **Action:**
  1. Record the skill bug in brain (which skill, what behavior)
  2. STOP self-test
  3. Fix the skill (per `forge-writing-skills` TDD-for-skills workflow)
  4. Re-run self-test from Phase 1 (skill change may affect all phases)

---

## Self-Test Checklist

Before declaring Forge production-ready, verify all items:

**Phase 0:**
- [ ] Seed present locally — `seed-product/shopapp/` + `seed/prds/` exist (both **gitignored by design**; absent on a fresh clone → **BLOCKED — seed not present** is expected, see **Seed Product** above, not a regression)
- [ ] Seed product repos accessible
- [ ] Brain path initialized (clean state, no prior run contamination)
- [ ] Infrastructure running (MySQL, Redis, Kafka, Elasticsearch)

**Phase 1 (Intake):**
- [ ] `/forge-intake-gate` invoked
- [ ] All mandatory intake lock fields satisfied
- [ ] PRD locked in brain (decision ID recorded)

**Phase 2 (Council):**
- [ ] `/forge-council-gate` invoked
- [ ] All 4 surfaces attended
- [ ] All 5 contracts negotiated
- [ ] Shared-dev-spec frozen (SPECLOCK decision ID)

**Phase 3 (Build):**
- [ ] Tech plans written for all 4 repos
- [ ] Tech plans self-reviewed
- [ ] All tasks dispatched to dev-implementer in isolated worktrees
- [ ] All tasks report DONE (no BLOCKED remaining)
- [ ] TDD cycle verifiable in commit history

**Phase 4 (Review + Eval):**
- [ ] spec-reviewer: PASS for all repos
- [ ] code-quality-reviewer: PASS for all repos
- [ ] eval-product-stack-up succeeded
- [ ] All 6 drivers ran (no skipped drivers)
- [ ] eval-judge: GREEN verdict
- [ ] **`[P4.0-SEMANTIC-EVAL]`** in **`conductor.log`**; **`semantic-eval-manifest.json`** **`outcome: pass`** for ship bar; **`semantic-eval-run.log`** committed when produced
- [ ] **`verify_forge_task.py`** exit **0** on seed task + brain

**Phase 4.5 (Review readiness):**
- [ ] **`review-readiness`** — all six checks pass (pre-PR gate)

**Phase 5 (Ship):**
- [ ] All PRs raised with dependency links
- [ ] Merge order enforced
- [ ] Dreamer retrospective complete
- [ ] Score and patterns recorded in brain

**Output:** `FORGE IS PRODUCTION-READY` or `FORGE NOT READY — [specific failure]`
