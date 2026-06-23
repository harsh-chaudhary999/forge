---
name: self-heal-systematic-debug
description: "WHEN: A fault has been triaged and a root cause is identified. Run 4-phase debug: investigate → hypothesize → fix (minimal) → verify (re-eval)."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "debug this failure"
  - "systematic debug"
  - "4-phase debug"
  - "debug eval failure"
allowed-tools:
  - Bash
  - Write
---

# Self-Heal Systematic Debug

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I can see the bug, I'll just fix it" | What you see is a symptom. The systematic 4-phase workflow exists because root causes hide behind obvious symptoms. |
| "I'll fix multiple things while I'm in here" | Multiple fixes in one pass make it impossible to verify which fix resolved the issue. Fix ONE thing, verify, then proceed. |
| "Let me refactor this messy code while debugging" | Refactoring during debugging introduces new variables. If the test still fails after your refactor, you can't tell if the refactor broke it or the original bug persists. |
| "The hypothesis is obvious, skip to fix" | Obvious hypotheses are wrong >50% of the time. Write it down, collect evidence, then fix. Skipping investigation is guessing. |
| "I'll verify later after fixing a few things" | Verification after each fix is the only way to know which fix worked. Batched fixes + late verification = correlation, not causation. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
FIX ONE THING AT A TIME. INVESTIGATE FIRST, HYPOTHESIZE SECOND, FIX THIRD, VERIFY FOURTH. NO EXCEPTIONS TO THE ORDER. NO BATCHED FIXES. NO VERIFICATION SKIPPED.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Agent applies a fix before completing the investigate phase** — Fixing symptoms without root cause produces recurring failures. STOP. Complete investigation and hypothesis before touching any code.
- **Multiple files changed in a single fix attempt** — Multi-file fixes make it impossible to isolate which change resolved the issue. STOP. Make the smallest possible single-change fix, verify, then proceed.
- **Verification is skipped after a fix** — A fix without verification is an assumption. STOP. Re-run the failing test or eval after every single fix before making the next one.
- **The same fix is applied twice** — Repeating a fix that already failed means the root cause is not understood. STOP. Return to the investigate phase with fresh eyes.
- **Debugging is done in the main branch** — Debug changes in main pollute the codebase. STOP. Create a fresh debug worktree before making any changes.
- **Agent describes the fix in words instead of showing actual test output** — "I fixed it" without evidence is not a fix. STOP. Show actual passing test output after every fix.
- **Self-heal attempts have exceeded 3** — The loop cap has been reached. STOP. Escalate to human with full failure context per self-heal-loop-cap.

## Overview

Systematic debugging framework that applies the scientific method to code failures. When a test fails, an API returns 500, or eval breaks, use this skill to isolate the root cause, apply a minimal fix, and verify resolution.

**Philosophy:** Fix ONE thing at a time. No refactoring. No speculative changes. Let the evidence guide the fix.

---

## 4-Phase Workflow

**Before starting any debug work**, checkpoint your session so it can survive context compaction:

```bash
# Invoke /context-save with a title like: debug-<service>-<issue-slug>
# Example: /context-save debug-auth-service-2fa-failure
```

Invoke `/context-save` before beginning any investigation. If context compacts mid-debug, run `/context-restore` in the next session to resume from the last checkpoint.

### Investigate
**Goal:** Find the exact failure point and capture evidence.

**Actions:**
- Read error logs and stack traces
- Identify the service/function that failed
- Trace the request path from entry to failure
- Capture the exact error message and line number
- Note what was the last successful operation before failure
- Document environment state (config, versions, data state)

**Output:** Clear failure signature
- *What failed?* (function, endpoint, test)
- *Where did it fail?* (file, line number)
- *How did it fail?* (error message, exception type)

**Example:**
```
Test: POST /auth/2fa/enable
Failed at: /app/src/routes/auth.ts:145
Error: "ReferenceError: generateSecret is not defined"
Stack: at enableTwoFactor (/app/src/routes/auth.ts:145)
```

**After Investigate — persist evidence to brain:**

```bash
ROOT="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
BRAIN_DIR="$(ls -d "$ROOT"/prds/*/ 2>/dev/null | head -1)debug"
mkdir -p "$BRAIN_DIR"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
# Write to: $BRAIN_DIR/${TIMESTAMP}-investigate.md
# Sections: Error message, Stack trace, Failure point (service/file/line),
#           Environment state, Last successful operation
```

Write this file now with all evidence collected in this phase. If context compacts before the fix is verified, the next session reads this file to know exactly where the debug loop is.

---

### Hypothesize
**Goal:** Determine root cause from evidence, not intuition.

**Actions:**
- Analyze the failure signature
- Ask: What changed recently that could cause this?
- Check: Is the required dependency imported?
- Check: Is the required service running?
- Check: Is configuration correct?
- Check: Is the data in the expected state?
- Form a single, testable hypothesis

**Output:** Root cause statement
- *"The X is missing/broken/misconfigured because..."*
- Confidence: High/Medium/Low
- Test strategy: How to verify this hypothesis

**Example:**
```
Hypothesis: generateSecret function is not imported in auth.ts
Evidence: ReferenceError says "generateSecret is not defined"
Location: /app/src/lib/crypto exports generateSecret but auth.ts doesn't import it
Confidence: HIGH
Test: Add import, re-run test
```

---

### Fix
**Goal:** Apply ONE minimal change. No refactoring, no optimization.

**Actions:**
1. Locate the exact lines to change
2. Apply ONLY what's needed to test the hypothesis
3. Make one atomic change
4. Do NOT:
   - Refactor surrounding code
   - Optimize performance
   - "While you're at it" improvements
   - Clean up unrelated issues

**Output:** Minimal code change

**Example:**
```typescript
// BEFORE
import { hash, verify } from './lib/crypto';
// ← generateSecret is missing

// AFTER
import { hash, verify, generateSecret } from './lib/crypto';
// ← Added generateSecret import only

// Do NOT do:
import { hash, verify, generateSecret } from './lib/crypto';
// + cleanup exports
// + reorganize imports alphabetically
// + refactor function signatures
```

**After each Fix attempt — persist attempt to brain:**

```bash
ROOT="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
BRAIN_DIR="$(ls -d "$ROOT"/prds/*/ 2>/dev/null | head -1)debug"
mkdir -p "$BRAIN_DIR"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
# Write to: $BRAIN_DIR/${TIMESTAMP}-fix-attempt.md
# Include: hypothesis tested, file+line changed, diff summary
# After Verify: add result (PASS/FAIL) and new error if FAIL
```

Write this file before running Verify. Update it with the result after Verify completes. Increment attempt number across attempts (attempt-1, attempt-2, attempt-3).

---

### Verify
**Goal:** Confirm the fix works and no new failures appear.

**Actions:**
1. Re-run the exact same test/eval that failed
2. Confirm success
3. Run related tests to catch regressions
4. Check logs for new errors
5. If fix worked → Commit
6. If fix didn't work → Return to Phase 1 with new evidence

**Output:** Green test + clean logs

**Example:**
```bash
# Test the fix
npm test -- auth.test.ts

# Expected output
✓ POST /auth/2fa/enable returns 201
✓ 2FA secret is generated correctly
✓ QR code is valid

# Commit if all green
git add src/routes/auth.ts
git commit -m "fix: import generateSecret in auth.ts"
```

---

## When to Use This Skill

- ❌ A test is failing
- ❌ An API endpoint returns 500
- ❌ Eval scenario breaks
- ❌ Feature doesn't work as specified
- ❌ Mysterious error in logs
- ❌ Service won't start

---

## When NOT to Use This Skill

- ✓ Feature is working, making improvements (use refactoring skill)
- ✓ Writing new code from scratch (use TDD skill)
- ✓ Performance optimization without a failure (use profiling skill)

---

## Minimal Fix Philosophy

See [reference/minimal-fix-philosophy.md](reference/minimal-fix-philosophy.md) for the refactor-vs-minimal-fix contrast (the buried-fix anti-pattern vs the single-line fix) and the four reasons minimal fixes matter (easier to verify, revert, understand; fewer regressions).

---

## Common Debugging Patterns & Command Catalog

See [reference/debugging-patterns.md](reference/debugging-patterns.md) for the 6 common failure patterns (missing import/export, wrong function call, missing env var, broken dependency, wrong data format, service not running) — each with symptom/investigation/fix — plus the per-phase command catalog (Investigate / Hypothesize / Fix / Verify bash commands).

---

## Worked Examples & Step-by-Step Walkthrough

See [reference/worked-examples.md](reference/worked-examples.md) for the 7-step "when you encounter a failure" walkthrough, a full 4-phase debug session (POST /api/users/register OOM → minimal data-size fix), and the "Fix Didn't Work" troubleshooting loop (revert and change one thing at a time).

---

## Success Criteria

- ✅ Found exact failure point (file, line, error)
- ✅ Identified root cause with evidence
- ✅ Applied ONE minimal code change
- ✅ Original test/eval now passes
- ✅ No new test failures introduced
- ✅ Minimal fix is committed with clear message

---

## Related Skills

- **brain-read:** Look up past debugging decisions and patterns
- **eval-driver-api-http:** Re-run API eval scenarios
- **forge-verification:** Broader verification framework
- **forge-tdd:** Prevent bugs with tests

---

## Quick Reference Card

| Phase | Goal | Key Question |
|-------|------|---|
| **Investigate** | Find failure point | What broke and where? |
| **Hypothesize** | Root cause | Why did it break? |
| **Fix** | Minimal change | What ONE thing fixes it? |
| **Verify** | Confirm working | Does it work now? |

---

## Edge Cases & Fallback Paths

See [reference/edge-cases.md](reference/edge-cases.md) for the 5 fallback paths — each with diagnosis, response, and escalation code: (1) logs missing/truncated → NEEDS_CONTEXT; (2) root cause in infrastructure → NEEDS_INFRA_CHANGE; (3) fix affects other services → NEEDS_COORDINATION; (4) multiple possible fixes, ranked by blast radius → NEEDS_ANALYSIS; (5) fix works in isolation but fails in full stack.

---

## Quick Reference Card

**Remember:** Evidence → Hypothesis → Minimal Fix → Verification. Follow the chain.

## Checklist

Before claiming the bug is fixed:

- [ ] Investigate phase completed — logs, stack traces, request/response read before any fix
- [ ] Hypothesis written down explicitly (not assumed) and tied to evidence
- [ ] Fix is minimal — touches the smallest possible scope (single file if possible)
- [ ] Verification run — failing test/eval re-run and passes after fix
- [ ] Related tests pass (not just the one that was failing)
- [ ] Fix committed with descriptive message explaining the root cause
- [ ] Learning captured (see below)

---

## Capture Learning (REQUIRED after every resolved debug session)

After the fix is committed and verified, append one entry to the learnings log. This makes the session durable — the next person (or next context window) hitting a similar failure can skip the investigate phase.

```bash
LEARN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}/learnings"
mkdir -p "$LEARN_DIR"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
# Fill in each field below before running — do not leave angle-bracket placeholders
cat >> "$LEARN_DIR/debug-learnings.jsonl" << 'ENTRY'
{"timestamp":"FILL_TIMESTAMP","type":"pitfall","symptom":"FILL_SYMPTOM","root_cause":"FILL_ROOT_CAUSE","location":"FILL_FILE:LINE","fix":"FILL_FIX","regression_test":"FILL_TEST","confidence":"high"}
ENTRY
```

Replace each `FILL_*` placeholder with the actual value for this debug session before appending. Use single-quoted heredoc (`<< 'ENTRY'`) to prevent accidental shell expansion of the JSON content.

**Required fields:**

| Field | What to put |
|---|---|
| `symptom` | The error message or observable failure (one line) |
| `root_cause` | The actual cause — not "there was a bug" but the specific invariant that was violated |
| `location` | `file:line` where the root cause lived |
| `fix` | The exact change made (import added, config corrected, etc.) |
| `regression_test` | Test name or eval scenario that now guards against recurrence |
| `confidence` | How certain you are that this is the real root cause (`high` = verified by regression test, `medium` = fix worked but root cause inferred, `low` = fix worked but root cause unknown) |

If `confidence` is `low`, note it in `root_cause` so the next reader knows the diagnosis was incomplete.

## Post-Implementation Checklist

- [ ] Debug followed a structured hypothesis → test → result cycle (not random edits).
- [ ] Each hypothesis was written before being tested (not reverse-engineered from the fix).
- [ ] Failing command reproduced locally before any fix was attempted.
- [ ] Fix verified by re-running the exact failing command (not just "should work now").
- [ ] Debug session summary written to brain with task_id: anchor.
