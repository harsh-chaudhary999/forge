---
name: forge-self-test
description: WHEN: You need to validate the entire Forge pipeline works end-to-end on a real product. Run before declaring Forge production-ready or after major changes to skills/agents.
type: rigid
requires: [forge-intake-gate, forge-council-gate, forge-tdd, forge-eval-gate, forge-verification]
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

## Seed Product

**ShopApp** — A 4-repo e-commerce product used as the canonical self-test target.

| Repo | Role | Language |
|---|---|---|
| `shared-schemas` | Protobuf definitions | Protobuf |
| `backend-api` | REST API server | Node.js / Express |
| `web-dashboard` | Admin dashboard | TypeScript / Next.js |
| `app-mobile` | Customer app | Kotlin / Android |

**PRD under test:** `seed/prds/01-favorites-cross-surface-sync.md`
— Cross-surface sync of user favorites (backend, web, mobile, shared schemas all touched).

---

## Detailed Workflow

### Phase 0: Environment Setup

**HARD-GATE: Environment must be clean before starting.**

```bash
# 1. Verify seed product repos exist
ls seed-product/backend-api seed-product/web-dashboard seed-product/app-mobile seed-product/shared-schemas

# 2. Set up a clean brain path for this test run
mkdir -p ~/forge/brain/self-test/run-$(date +%Y%m%d-%H%M%S)
export SELF_TEST_BRAIN=~/forge/brain/self-test/run-$(date +%Y%m%d-%H%M%S)

# 3. Verify eval infrastructure is running
# (MySQL, Redis, Kafka, Elasticsearch — per seed/product.md)
# If not running: start them. If can't start: escalate BLOCKED.
```

**Output:** Environment ready, brain path set, infrastructure confirmed.

---

### Phase 1: Intake

**HARD-GATE: PRD must be locked before proceeding to Phase 2.**

1. Invoke `/forge-intake-gate` with seed PRD: `seed/prds/01-favorites-cross-surface-sync.md`
2. Invoke `/intake-interrogate` — ask all 8 questions:
   - Core user problem (what does "favorites sync" solve?)
   - Affected surfaces (backend, web, app, shared-schemas — all 4)
   - Contract changes (API v2 endpoint, new DB table, cache key pattern)
   - Acceptance criteria (user favorites appear in web and app within 500ms)
   - Anti-goals (no changes to existing auth flow)
   - 3-month success (10K users with <1% sync failure rate)
   - Hard constraints (backwards compatible API, no schema breaking changes)
   - Assumptions (users have both web and mobile accounts)
3. Lock PRD in brain: `PRDLK-SELF-TEST-$(date +%Y%m%d)`

**Acceptance Criteria:**
- ✅ PRD locked (decision ID recorded in brain)
- ✅ All 8 questions answered (no "TBD")
- ✅ Surfaces and contracts enumerated

---

### Phase 2: Council

**HARD-GATE: Shared-dev-spec must be locked before Phase 3.**

1. Invoke `/forge-council-gate` with locked PRD from Phase 1
2. Invoke `/council-multi-repo-negotiate`:
   - Backend surface: proposes `POST /api/v2/favorites` with optimistic locking
   - Web surface: requests pagination, 50-item max per page
   - App surface: requests offline support, sync-on-reconnect
   - Infra surface: proposes Redis pub/sub for cross-surface sync
3. Negotiate the 5 contracts:
   - REST API: `POST /api/v2/favorites`, `GET /api/v2/favorites?userId=&page=`
   - Events: `user.favorites.changed` Kafka topic with payload schema
   - Cache: `favorites:{userId}` Redis key, 1h TTL, invalidate-on-write
   - DB schema: `favorites` table (userId, itemId, createdAt, syncedAt)
   - Search: no search index changes (favorites not searchable)
4. Invoke `/spec-freeze` to lock shared-dev-spec
5. Write to brain: `SPECLOCK-SELF-TEST-$(date +%Y%m%d)`

**Acceptance Criteria:**
- ✅ All 4 surfaces attended (backend, web, app, infra)
- ✅ All 5 contracts negotiated (no "TBD")
- ✅ Shared-dev-spec locked in brain
- ✅ No unresolved conflicts (or dreamer decision recorded)

---

### Phase 3: Tech Plans + Build

**HARD-GATE: Each repo must have a tech plan before dev-implementer is dispatched.**

1. Invoke `/tech-plan-write-per-project` for each repo:
   - `shared-schemas`: Add `favorites.proto` definition
   - `backend-api`: Implement `POST/GET /api/v2/favorites` + Redis pub/sub
   - `web-dashboard`: Add favorites UI with pagination
   - `app-mobile`: Add offline favorites store + sync-on-reconnect
2. Invoke `/tech-plan-self-review` to validate each plan
3. Dispatch `dev-implementer` per task per repo:
   - Each task runs in isolated worktree
   - TDD enforced: test first, watch fail, implement, watch pass
   - Dev-implementer self-reviews before committing
4. Verify each dev-implementer reports `DONE` or `DONE_WITH_CONCERNS`

**Acceptance Criteria:**
- ✅ Tech plans written and reviewed for all 4 repos
- ✅ All tasks completed (DONE or DONE_WITH_CONCERNS)
- ✅ No BLOCKED or NEEDS_CONTEXT (or resolved before proceeding)
- ✅ TDD cycle verifiable in commit history (test commit before implementation commit)

---

### Phase 4: Review + Eval

**HARD-GATE: Eval must return GREEN before Phase 5.**

1. Invoke `spec-reviewer` per repo:
   - Reads actual code (not PR descriptions)
   - Verifies against locked shared-dev-spec
   - Reports PASS or FAIL
2. Invoke `code-quality-reviewer` per repo:
   - 11-point quality framework
   - Reports PASS or FAIL
3. If any reviewer reports FAIL: dispatch dev-implementer to fix, re-review
4. Invoke `/forge-eval-gate`:
   - Bring up stack: `/eval-product-stack-up`
   - Run scenarios per driver:
     - API: POST /api/v2/favorites, verify 201
     - DB: query favorites table, verify insert
     - Cache: get Redis key, verify TTL and value
     - Events: consume Kafka topic, verify payload schema
     - Web: CDP test, verify favorites render in dashboard
     - Mobile: ADB test, verify favorites render in app
   - Invoke `/eval-judge` for verdict

**Acceptance Criteria:**
- ✅ spec-reviewer: PASS for all repos
- ✅ code-quality-reviewer: PASS for all repos
- ✅ eval-judge: GREEN verdict
- ✅ All 6 drivers returned results (no skipped drivers)

---

### Phase 5: Ship + Retrospective

**HARD-GATE: All PRs must be coordinated and merged in dependency order.**

1. Invoke `/pr-set-coordinate` to raise PRs in merge order:
   - `shared-schemas` first (no dependencies)
   - `backend-api` second (depends on shared-schemas)
   - `web-dashboard` third (depends on backend-api)
   - `app-mobile` fourth (depends on backend-api)
2. Verify each PR has `depends-on` links
3. Invoke `/pr-set-merge-order` to enforce merge sequence
4. Invoke `/dream-retrospect-post-pr` after all PRs merged:
   - Score decisions (correctness, robustness, efficiency, reversibility, confidence)
   - Extract patterns → write to `brain/products/shopapp/patterns/`
   - Record gotchas → write to brain
   - Record opportunities → write to brain

**Acceptance Criteria:**
- ✅ All 4 PRs raised with correct dependency links
- ✅ Merge order enforced (no PR merged before its dependency)
- ✅ Dreamer retrospective completed (score recorded in brain)
- ✅ Patterns extracted (at least 1 new pattern identified)

---

## Self-Test Output Format

```
FORGE SELF-TEST RESULT
======================
Run ID: SELF-TEST-{timestamp}
Seed PRD: 01-favorites-cross-surface-sync

Phase 1 (Intake):    ✅ PASS — PRD locked PRDLK-{timestamp}
Phase 2 (Council):   ✅ PASS — Spec frozen SPECLOCK-{timestamp}
Phase 3 (Build):     ✅ PASS — 4 repos, 12 tasks, 0 BLOCKED
Phase 4 (Eval):      ✅ PASS — GREEN verdict, 6 drivers
Phase 5 (Ship):      ✅ PASS — 4 PRs merged, retrospective complete

Total Duration: {time}

VERDICT: FORGE IS PRODUCTION-READY
```

Or on failure:
```
FORGE SELF-TEST RESULT
======================
Phase 3 (Build): ❌ FAIL — dev-implementer BLOCKED on backend-api task 2
  Reason: DB migration script not found in seed product
  Action: Fix seed product or update forge-product.md
  Blocker: Cannot proceed to eval without build passing

VERDICT: FORGE NOT READY — Fix Phase 3 blocker and re-run from Phase 3
```

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
- [ ] Seed product repos accessible
- [ ] Brain path initialized (clean state, no prior run contamination)
- [ ] Infrastructure running (MySQL, Redis, Kafka, Elasticsearch)

**Phase 1 (Intake):**
- [ ] `/forge-intake-gate` invoked
- [ ] All 8 questions answered
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

**Phase 5 (Ship):**
- [ ] All PRs raised with dependency links
- [ ] Merge order enforced
- [ ] Dreamer retrospective complete
- [ ] Score and patterns recorded in brain

**Output:** `FORGE IS PRODUCTION-READY` or `FORGE NOT READY — [specific failure]`
