---
name: self-heal-triage
description: "WHEN: An eval scenario has failed and a fault has been located. Classify the failure — flaky, bad test, real bug, or environment — for YAML driver runs or semantic `semantic-eval-run.log` / manifest outcomes, with evidence and confidence score."
type: rigid
requires: [brain-read]
version: 1.0.2
preamble-tier: 3
triggers:
  - "triage eval failure"
  - "classify failure type"
  - "is this a bug or flake"
allowed-tools:
  - Bash
---

# Self-Heal Triage Skill

## Anti-Pattern Preamble

### Anti-Pattern 1: "The error message says DB error so it's a DB fault"

**Why This Fails**

Surface error often misidentifies root cause. A "DB connection error" might originate from:
- Application timeout causing DB query to fail
- Network layer misconfiguration preventing connection
- Query performance issue (hanging query, not failed connection)
- Connection pool exhaustion (app-side resource leak)
- Authentication token expiration (not DB unavailability)

The error type you see is the symptom, not the diagnosis.

If the latest **`qa-run-report-*.md`** has YAML **`flake_suspected: true`** (same scenario IDs failed on consecutive runs), treat **flake** as a **leading** hypothesis — still verify evidence; do not downgrade triage rigor.

**Enforcement — MUST Do All:**
- MUST trace the error back 3+ layers (where did DB error originate?)
- MUST check application logs for pre-DB errors (timeout, pool exhaustion)
- MUST verify connectivity to DB independently (ping, telnet, health check)
- MUST review query performance metrics (query duration, lock contention)
- MUST check authentication/credentials separately from DB availability

---

### Anti-Pattern 2: "Triage once and assume the category is stable"

**Why This Fails**

Multiple faults can coexist simultaneously. After applying a fix:
- A CONFIG_ERROR fix may reveal a hidden CODE_BUG
- Fixing flakiness in one component exposes flakiness in another
- Evidence quality changes as fixes are applied (state changes, logs grow)
- Initial classification is based on available evidence at one point in time

A single triage is a snapshot, not ground truth.

**Enforcement — MUST Do All:**
- MUST retriage after each fix is applied (do not assume category remains stable)
- MUST document evidence changes as state evolves (before/after comparison)
- MUST track category migration if classification changes (log the transition)
- MUST cross-check confidence score after each step (does it stay MEDIUM+?)
- MUST escalate if category changes more than once (indicates cascading faults)

---

### Anti-Pattern 3: "Low confidence score means skip to manual fix"

**Why This Fails**

Low confidence doesn't mean abandon — it means gather more evidence. Skipping to manual fix when confidence is low means:
- Losing opportunity to improve classification signals
- Applying wrong remediation strategy
- Missing patterns that future automated triage could catch

Low confidence is a request for more data, not permission to exit.

**Enforcement — MUST Do All:**
- MUST expand evidence collection before escalating (logs, state, traces)
- MUST refine classification rules based on new evidence (revisit patterns)
- MUST increase sample size if single failure (re-run 3+ times for signals)
- MUST document confidence gaps (why could confidence not reach MEDIUM+?)
- MUST attach low-confidence evidence to escalation ticket (human can review it)

---

### Anti-Pattern 4: "Infrastructure faults always need escalation"

**Why This Fails**

Many infra faults are transient and self-heal within one retry cycle:
- Network timeouts often recover on retry
- Service overload resolves as load decreases
- Transient DNS failures resolve on retry
- Temporary resource exhaustion recovers
- Brief service restarts complete within seconds

Not all infra faults require immediate escalation.

**Enforcement — MUST Do All:**
- MUST retry before escalating (one deterministic retry, not random retries)
- MUST check transience patterns (does error recur or resolve?)
- MUST document behavior (transient = self-heals, persistent = needs escalation)
- MUST set retry limits (max 1 retry for transient, no retries for persistent)
- MUST escalate only persistent infra faults to NEEDS_CONTEXT

---

### Anti-Pattern 5: "Ambiguous classifications are uncategorizable"

**Why This Fails**

Ambiguity (two categories tied in evidence) doesn't mean uncategorizable — it means apply evidence weighting:
- Primary evidence (direct error type) should weight 60%
- Secondary evidence (context) should weight 30%
- Tertiary evidence (patterns) should weight 10%

Triage always has a strongest signal if you weight properly.

**Enforcement — MUST Do All:**
- MUST apply evidence weights (primary > secondary > tertiary)
- MUST pick the category with highest weighted score (never random)
- MUST document tiebreaker reasoning (which evidence decided it)
- MUST escalate only if weighted scores remain tied after weighting
- MUST attach confidence penalty if tiebreaker was necessary (note in evidence)

---

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
TRIAGE COMPLETES BEFORE ANY FIX IS APPLIED. CLASSIFY WITH EVIDENCE AT MEDIUM OR HIGHER CONFIDENCE OR ESCALATE. A CLASSIFICATION WITHOUT EVIDENCE IS A GUESS — GUESSES WASTE SELF-HEAL LOOP ATTEMPTS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Triage classification is "probably flaky" with no timing evidence** — Probability-based triage is a guess. STOP. Collect actual timing data (retry counts, timestamps, test duration) before classifying as flaky.
- **Classification is made after only 1 data point (1 failure)** — Single-occurrence failures are unclassifiable without more data. STOP. Run the test 3 times to distinguish flaky from real.
- **"Environment issue" is used to dismiss a failure without a root cause** — Environment failures have root causes. STOP. Identify what specifically broke in the environment and whether it's also broken in production.
- **Triage confidence is LOW and triage proceeds anyway** — Low-confidence triage sends the wrong fix strategy downstream. STOP. Gather more evidence until confidence is MEDIUM or higher.
- **Fix is applied before triage completes** — Fixing before classifying means applying the wrong fix strategy. STOP. Always complete triage before prescribing a fix.
- **Same failure is classified differently on two consecutive runs** — Classification instability means the evidence is insufficient. STOP. Rerun with more isolation and additional log capture.

## Purpose
Automatically classify test and system failures into one of four categories to enable rapid remediation. Each classification provides evidence, confidence scoring, and a suggested action.

## Semantic path (Phase 4.4) — triage without driver payloads

**When:** **`self-heal-locate-fault`** traced RED using **`qa/semantic-eval-run.log`** (JSON lines) and **`qa/semantic-eval-manifest.json`**.

**Evidence priority:**
1. **`semantic-eval-run.log`** — per-step **`status`**, **`error`** / **`message`**, **`surface`**, **`id`**.
2. **`semantic-automation.csv`** — **`Intent`**, **`DependsOn`**, **`Surface`** for the failed **`id`**.
3. **`semantic-eval-manifest.json`** **`outcome`** — must align with log; mismatch → treat as **environment / tooling** or incomplete run (**BAD TEST** / harness).

**Classification hints:**
- **`status: FAILED`** + stack/message pointing at product code → **REAL BUG** on the service mapped from **`surface`** (see **`forge-product.md`**).
- Assertion text in **`intent`** wrong vs spec but app correct → **BAD TEST** (semantic row or expectation drift).
- Empty **`semantic-eval-run.log`** but **`outcome: fail`** → **ENVIRONMENT** or aborted runner; gather host/driver logs.
- Intermittent passes across re-runs with same manifest → **FLAKY** (driver or external dependency).

Do **not** require YAML scenario IDs — use semantic **`id`** fields consistently.

### RED_INFRA Pre-Check (runs BEFORE classification)

Before classifying any failure, check whether `forge-eval-gate` has logged a `RED_INFRA` outcome:

1. Read `~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json` or `conductor.log`.
2. If `outcome: RED_INFRA` is present (ECONNREFUSED, Docker daemon down, MCP unavailable, dependent service not reachable):
   - **Do NOT classify this as a code bug, flaky test, or bad test.**
   - **Do NOT consume a self-heal retry attempt.**
   - Immediately write a BLOCKED escalation to `~/forge/brain/prds/<task-id>/blockers/<timestamp>-infra-failure.md` with the infrastructure symptom.
   - Output: `BLOCKED — RED_INFRA: <symptom>. No retry consumed. Human must resolve infrastructure before re-running eval.`
   - Stop. Do not proceed to the classification procedure below.
3. Only if `outcome` is NOT `RED_INFRA`: proceed to the classification procedure.

**Why:** Infrastructure failures cannot be fixed by code changes. Consuming self-heal retries on infra failures wastes the entire retry budget on unfixable symptoms, leaving zero retries for the real code bug that will surface once infra is restored.

## Classification Categories (4 + transient + escalation)

Classify every located failure into one of four categories — **Flaky Test**, **Bad Test**, **Real Bug**, **Environment Issue** — machine enum `flaky | bad_test | real_bug | environment`. This is the only vocabulary any other skill should cross-reference. The full per-category evidence catalogs (identifying evidence, common error patterns, suggested actions), the `CLASSIFY` decision algorithm, and the HIGH/MEDIUM/LOW confidence-scoring bands live in **`reference/classification.md`** (load on demand). The routing card, confidence-handling decision tree, and pipeline output contract live in **`reference/routing.md`**.

**Vocabulary note:** `reference/triage-examples-edge-cases.md` and some Anti-Pattern prose in this file use informal working labels (`CODE_BUG`, `CONFIG_ERROR`) in worked scenarios written before the 4-category enum above was finalized. Those informal labels are **not** a second valid vocabulary — `CODE_BUG` maps to `real_bug`, `CONFIG_ERROR` maps to `environment` (or `real_bug` when the fix is a code change, per the scenario). Treat the canonical enum above as authoritative; the worked examples' scenario content (evidence, decision logic) is still valid, only the ad hoc labels are stale.

## Reference (load on demand)

Deep detail follows Agent Skills progressive disclosure. This SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists. Load the reference file you need:

- **`reference/classification.md`** — the four category catalogs, classification algorithm, and confidence-scoring/confidence-rules bands.
- **`reference/routing.md`** — confidence-handling decision tree, quick-reference routing card, Forge-pipeline trigger/output contract, future enhancements.
- **`reference/triage-examples-edge-cases.md`** — worked triage examples and edge-case deep-dives (ambiguous, cascading, missing-evidence, new-pattern, transient).

## Implementation Workflow

### 1. Input Validation
- Validate failure message exists
- Extract error type from stack trace
- Gather test context (timeout settings, environment)
- Check for previous similar failures

### 2. Pattern Matching
- Check against all defined error patterns
- Calculate match score for each category
- Weight evidence by priority

### 3. Context Analysis
- Review test setup and teardown
- Check for timing-dependent code
- Verify mock/stub configuration
- Analyze implementation code

### 4. Confidence Calculation
- Count matching indicators (weighted)
- Check for conflicting signals
- Apply confidence scoring rules
- Add human review flag if < 50%

### 5. Output Generation
- Return classification with evidence
- Include confidence score
- Suggest actionable remediation
- Provide links to relevant code/logs

---

## Routing & confidence handling (load on demand)

Once classified, route the failure and resolve confidence:

- **Pipeline trigger points, the `classification` YAML output contract, and the per-category self-heal routing** (Flaky→flaky-test-fixer, Bad Test→test-corrector, Real Bug→bug-fixer +tag real_bug, Environment→environment-recover) live in **`reference/routing.md`**.
- **Confidence Rules** (HIGH indicators / MEDIUM degradation / LOW triggers) and the **Decision Tree: Confidence Handling** (HIGH ≥85% proceed; MEDIUM 60–84% fix-then-retriage; LOW <60% expand-evidence-or-escalate to NEEDS_CONTEXT) live in **`reference/routing.md`**.
- The **Quick Reference Card** (per-category primary/secondary signals, confidence triggers, escalation route) and worked routing examples live in **`reference/routing.md`**.

---

## Post-Implementation Checklist

- [ ] Triage decision is one of: fix-code / fix-test / fix-config / escalate — not "investigate more".
- [ ] Fix strategy written to brain with task_id: anchor before any code is changed.
- [ ] If fix-code: specific files and lines to change are named (not "update the handler").
- [ ] If escalate: BLOCKED written to brain with blocker description and next step for human.
- [ ] Self-heal iteration counter checked — triage does not proceed on iteration > 3.

## Cross-References

- **`self-heal-locate-fault`** — **Semantic path triage** depends on its parse of **`semantic-eval-run.log`**.
- **`eval-judge`**, **`qa-semantic-csv-orchestrate`**, [docs/semantic-eval-csv.md](../../docs/semantic-eval-csv.md)

## Checklist

Before routing to a fix strategy:

- [ ] **Source artifact identified** — driver payload vs **`semantic-eval-run.log`** JSON lines
- [ ] Failure message and error type extracted from eval output
- [ ] At least 3 data points collected before classifying as flaky (not single-occurrence)
- [ ] Classification supported by primary evidence pattern (timeout, assertion, exception, connection)
- [ ] Confidence score is MEDIUM (≥60%) or higher — LOW triggers escalation, not fix
- [ ] Evidence and confidence score documented in triage output
- [ ] Fix strategy routed based on classification (not assumed)

**Related Skills in Self-Heal Workflow:**

1. **self-heal-locate-fault** — Diagnose which service failed in eval. Run this BEFORE triage to identify failure scope. Triage works on failures identified by locate-fault.

2. **self-heal-loop-cap** — Max 3 retries per failure. Implements retry cap and sequencing. Triage output feeds into loop-cap to determine if failure is retryable.

3. **self-heal-systematic-debug** — 4-phase debugging workflow (investigate, hypothesize, test, confirm). Use this for deep-dive when triage routes to CODE_BUG with real_bug tag. Systematic-debug handles investigation phase.

---

## Future Enhancements

Roadmap items (ML classifier, NLP error-message understanding, cross-correlation, trend analysis, automated repair, debugger integration) are listed in **`reference/routing.md`**.
