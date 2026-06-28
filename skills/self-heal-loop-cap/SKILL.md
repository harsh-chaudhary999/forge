---
name: self-heal-loop-cap
description: "WHEN: A self-heal cycle is about to start its next retry. Enforces max 3 retries — locate → triage → fix → verify — then escalates BLOCKED."
type: rigid
requires: [brain-read]
version: 1.1.0
preamble-tier: 3
triggers:
  - "self-heal limit reached"
  - "stop self-heal loop"
  - "3 retries exceeded"
allowed-tools:
  - Bash
---

# Self-Heal Loop Cap Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "One more try and it'll pass" | That's what iteration 4, 5, and 6 say too. The cap exists because unbounded retries waste time and hide fundamental issues. |
| "This is a different fix, so the counter should reset" | The counter tracks attempts per failure, not per fix strategy. Three different wrong fixes still means BLOCKED. |
| "Escalating feels like giving up" | Escalation is the correct engineering response to a problem that resists three systematic attempts. It's not failure — it's efficient triage. |
| "The fix is almost working, just needs a tweak" | "Almost working" after 3 tries means the diagnosis is wrong, not that the fix needs a tweak. Escalate for fresh eyes. |
| "I'll increase the cap just this once" | The cap is a HARD-GATE. Increasing it normalizes infinite loops. If 3 tries can't fix it, the 4th won't either. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
THE SELF-HEAL LOOP CAPS AT 3 ATTEMPTS. EACH ATTEMPT REQUIRES A FULL LOCATE → TRIAGE → FIX → VERIFY CYCLE WITH FRESH EVIDENCE. AFTER 3 FAILURES, ESCALATE — DO NOT RETRY.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Attempt counter is at 3 and you're about to run a 4th fix** — You have hit the hard cap. Running more attempts violates the skill. Escalate immediately with all diagnostic context.
- **You are resetting or ignoring the attempt counter** — Counter manipulation defeats the entire purpose. The count is sacred; treat each attempt as non-renewable.
- **The same fix strategy is being applied again with minor variations** — Repeated similar fixes mean the root cause diagnosis is wrong. Stop, escalate, and document what three attempts revealed.
- **A new failure appeared mid-loop and you are folding it into the current retry** — Each distinct failure gets its own cap. Do not merge failure contexts. Log the new failure separately.
- **You are describing the fix as "almost there"** — "Almost there" after attempt 3 is the exact moment to escalate. Confidence in a near-fix does not override the cap.
- **The verify step was skipped or abbreviated** — Skipped verification means the attempt is incomplete and the result is invalid. Each attempt requires a full locate → triage → fix → verify cycle.
- **No evidence was captured between attempts** — Attempts without documented evidence cannot inform escalation. Stop and reconstruct what each attempt found before continuing.

Enforces a maximum of 3 retry attempts per failure scenario. Implements a structured locate → triage → fix → verify loop with automatic escalation to user when auto-healing fails.

## HARD-GATE Anti-Patterns (Violation Criteria)

Full long-form — the five violation-criteria anti-patterns with enforcement steps —
lives in **`reference/anti-patterns.md`**. The Anti-Pattern Preamble table above is the summary.

## Loop-engineering controls (beyond the 3-cap)

The 3-attempt cap is only the *iteration* control. A well-built loop also needs **no-progress
detection**, a **budget**, and **Reflexion** — see **[`docs/loop-engineering.md`](../../docs/loop-engineering.md)**.

1. **Log a failure signature every attempt.** On each failed eval, log
   `[P4.4-EVAL-FAIL] task_id=<id> signature=<root-cause-id> outcome=<RED|YELLOW>` — `signature`
   is the fault id from `self-heal-locate-fault`. It is what makes no-progress detectable.
2. **Run the guard before each retry:** `python3 tools/forge_loop_guard.py --task-id <id> --strict`.
   - **`ESCALATE_NO_PROGRESS`** — the last two attempts share a signature → the diagnosis is
     wrong; escalate **now**, do not spend the next retry on the same fault.
   - **`ESCALATE_CAP`** — 3 attempts reached → BLOCKED. **`ESCALATE_BUDGET`** — over `--max-seconds` → BLOCKED.
   - **`CONTINUE`** — distinct signature, within cap and budget → proceed.
3. **Reflexion (critique-carry).** After each failed attempt write
   `prds/<task-id>/heal/attempt-<n>.md` (what was tried, the `signature`, why it failed). The
   **next attempt MUST read** the prior critiques and may not repeat a tried-and-failed fix.

**HARD-GATE:** a retry that repeats a prior attempt's `signature`, or proceeds without reading
prior critiques, violates this skill — escalate instead of retrying.

## Overview

This skill prevents infinite retry loops by capping attempts at 3 retries. When an evaluation fails, the skill enters a controlled retry cycle, tracking all attempts and evidence. After 3 failed retry cycles, it escalates the issue to the user with full context and diagnostic data.

## Loop Flow

```
Initial Failure
       ↓
   Retry 1: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   Retry 2: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   Retry 3: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   BLOCKED → Escalate to User
```

## State Tracking

The loop maintains state throughout all retries:

```yaml
LoopState:
  attempt_count: 0-3          # Current retry attempt (0 = initial, 1-3 = retries)
  max_attempts: 3             # Hard cap on retry attempts
  previous_fixes: []          # List of fixes already tried (avoid repetition)
  failure_logs: []            # All failure evidence from each attempt
  current_eval_scenario: {}   # The failing evaluation scenario
  blocked: false              # Set to true if all retries exhausted
```

## Detailed Loop Cycle

### Locate Fault
- Parse error messages from the failed evaluation
- Identify root cause category:
  - Code logic error
  - Configuration issue
  - Environment/dependency problem
  - Test assertion mismatch
  - Integration point failure

### Triage
- Categorize severity and scope
- Determine if issue is auto-fixable
- Check against `previous_fixes` to avoid repeated attempts
- Estimate confidence in fix approach

### Fix
- Apply targeted fix based on triage
- Document the fix applied
- Add fix to `previous_fixes` list
- Make minimal, isolated changes

### Verify
- Re-run the evaluation scenario
- Check if original failure is resolved
- Capture pass/fail result with full logs
- If fail, collect evidence for next retry

## Escalation Protocol

When `attempt_count >= max_attempts` and verification still fails, escalate to user with a
full BLOCKED report (What Failed / What We Tried / Why It's Blocked / Evidence).

> Escalation report template + per-attempt/per-phase decision matrix (Quick Reference Card):
> [`reference/escalation.md`](reference/escalation.md).

## Edge Cases

> Full edge-case catalog (5 cases: same-error, different-error, locate/triage conflict, stack
> state drift, all-3-BLOCKED) with do-NOT actions and escalation keywords:
> [`reference/edge-cases.md`](reference/edge-cases.md).

## Decision Tree: Loop Continuation Logic

After each verify phase, given RESULT, determine what to do:

```
┌─ START (attempt_count = 0)
│
├─ Run Evaluation
│  └─ RESULT?
│     ├─ PASS → DONE ✅ (no retry needed)
│     └─ FAIL → Enter Retry Loop
│
└─ RETRY LOOP (attempt_count < 3)
   │
   ├─ Increment attempt_count (1, 2, or 3)
   │
   ├─ LOCATE FAULT
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ NO_FIX_AVAILABLE → Escalate, exit ⛔
   │     └─ LOCATED → Continue to Triage
   │
   ├─ TRIAGE
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ NOT_AUTO_FIXABLE → Escalate, exit ⛔
   │     ├─ FIX_ALREADY_TRIED → Escalate, exit ⛔
   │     └─ AUTO_FIXABLE → Continue to Fix
   │
   ├─ FIX
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ APPLY_FAILED → Escalate, exit ⛔
   │     └─ APPLIED → Continue to Verify
   │
   ├─ VERIFY (Re-run Eval)
   │  └─ RESULT?
   │     ├─ PASS → DONE ✅ (fix successful, exit)
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ SAME_ERROR → 
   │     │  └─ attempt_count < 3?
   │     │     ├─ YES → Loop back to LOCATE (deepen triage)
   │     │     └─ NO → Escalate (attempt_count = 3), exit ⛔
   │     ├─ NEW_ERROR →
   │     │  └─ Escalate as NEEDS_CONTEXT, exit (new fault)
   │     └─ DIFFERENT_FAILURE →
   │        └─ attempt_count < 3?
   │           ├─ YES → Loop back to LOCATE (new fault entry)
   │           └─ NO → Escalate, exit ⛔
   │
   └─ EXIT CONDITIONS:
      ├─ ✅ DONE: Eval passes
      ├─ ⛔ BLOCKED: No more retries or escalation triggered
      ├─ ⛔ NEEDS_CONTEXT: Human decision needed
      ├─ ⛔ NEEDS_COORDINATION: Ops/team involvement required
      └─ ⛔ (attempt_count = 3, no pass): Loop exhausted
```

---

> Per-attempt / per-phase Quick Reference Card (which output each phase must produce, when it
> is safe to continue, and the escalation token if stuck): [`reference/escalation.md`](reference/escalation.md).

> Reference loop-driver pseudocode (`runSelfHealLoop`) and a full worked failure scenario that
> exhausts all 3 attempts into BLOCKED: [`reference/examples.md`](reference/examples.md).

## Output States

### SUCCESS
```yaml
status: SUCCESS
retries_needed: N                    # 1-3 (or 0 if passed on first try)
final_fix: <fix description>
evidence:
  - attempt: 1
    error: <error message>
  - attempt: 2
    error: <error message>
  # ... etc if needed
```

### BLOCKED
```yaml
status: BLOCKED
eval_scenario: <scenario details>
attempts_tried: 3
fixes_attempted:
  - fix 1 description
  - fix 2 description
  - fix 3 description
all_failure_logs:
  - attempt: 1
    error: <full error>
    timestamp: <ISO timestamp>
  - attempt: 2
    error: <full error>
    timestamp: <ISO timestamp>
  - attempt: 3
    error: <full error>
    timestamp: <ISO timestamp>
reason: "Could not auto-fix after 3 attempts"
escalation_required: true
needs_human_review: true
```

## Safety Guarantees

1. **Hard Cap:** Loop never exceeds 3 retry attempts
2. **No Repetition:** `previous_fixes` prevents trying the same fix twice
3. **Evidence Trail:** Every attempt logged with full error context
4. **User Escalation:** All blocked cases reported to user with actionable data
5. **Timeout Safety:** Each retry cycle has implicit timeout from outer eval driver

## Integration Points

- **Trigger:** Invoked when any evaluation fails
- **Dependency:** Requires `brain-read` to access eval scenario metadata
- **Output:** Reports to user via standard escalation channel
- **State:** Local to current evaluation context (not persisted across sessions)

## Checklist

Before declaring BLOCKED and escalating:

- [ ] Attempt counter verified — exactly 3 full locate → triage → fix → verify cycles completed
- [ ] Fresh evidence collected on each attempt (not reusing stale logs from attempt 1)
- [ ] Same fix strategy not repeated — each attempt used a distinct diagnosis angle
- [ ] Each verify step ran the full original failing eval scenario (not abbreviated)
- [ ] All three attempts documented with fix description and result
- [ ] Escalation report includes: failing scenario, all fixes tried, failure evidence per attempt

## Post-Implementation Checklist

- [ ] Iteration counter incremented before each self-heal attempt (not after).
- [ ] At iteration > 3: BLOCKED written to brain and human escalated — no silent retry.
- [ ] Iteration count logged to conductor.log alongside each `[SELF-HEAL-*]` marker.
- [ ] Counter reset only when a new eval run starts (not per-step reset within the same run).
- [ ] Partial eval results preserved to brain before BLOCKED is declared.

## Cross-References

This skill depends on and coordinates with:

1. **self-heal-locate-fault**
   - **How:** Located faults feed into triage phase of each loop attempt
   - **Why:** Accurate fault location is prerequisite for targeted fix
   - **Sync Point:** Output of locate-fault is input to triage phase

2. **self-heal-triage**
   - **How:** Triage classifies fault type (CODE_BUG, CONFIG_ERROR, etc.) and determines auto-fixability
   - **Why:** Triage output determines if auto-fix can proceed or escalate
   - **Sync Point:** Triage confidence score influences retry decision

3. **self-heal-systematic-debug**
   - **How:** Invoked when loop reaches BLOCKED to provide deeper 4-phase investigation
   - **Why:** Loop cap escalation may benefit from systematic debugging approach
   - **Sync Point:** BLOCKED with insufficient evidence routes to systematic-debug

4. **forge-eval-gate**
   - **How:** Eval gate receives BLOCKED/DONE result from loop-cap; gates merge based on final status
   - **Why:** Loop cap status determines if eval passes for merge gate
   - **Sync Point:** Loop completion status reported to eval-gate

---

## Version History

- **v1.0:** Initial implementation with 3-retry cap, locate-triage-fix-verify loop, escalation protocol
