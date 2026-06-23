# Self-Heal Loop Cap — Escalation Report & Per-Phase Decision Matrix

Full escalation report template (emitted when `attempt_count >= max_attempts` and verify
still fails) plus the per-attempt / per-phase quick-reference matrix. Load when assembling a
BLOCKED escalation or when deciding whether a given phase is safe to continue.

## Escalation Report

When `attempt_count >= max_attempts` and verification still fails, escalate to user with:

**What Failed:**
- Evaluation scenario ID/name
- Brief description of what was being tested
- Initial failure message

**What We Tried:**
- Attempt 1: [fix description] → [result]
- Attempt 2: [fix description] → [result]
- Attempt 3: [fix description] → [result]

**Why It's Blocked:**
- All 3 auto-fix attempts exhausted
- Unable to determine next safe fix
- Risk of infinite loop reached
- Human judgment needed

**Evidence:**
- Full error log from each attempt
- Code changes applied per attempt
- Timeline of all 3 retries
- Environment/context information

## Quick Reference Card

| Attempt # | Phase | Expected Output | Safe to Continue? | Escalation If Stuck |
|---|---|---|---|---|
| 1 | Locate | Fault identified, root cause clear | YES if located | BLOCKED, escalate |
| 1 | Triage | Auto-fixable? High confidence? | YES if fixable | NOT_AUTO_FIXABLE, escalate |
| 1 | Fix | Changes applied, previous_fixes logged | YES if applied | APPLY_FAILED, escalate |
| 1 | Verify | Re-run eval, check original error | YES if PASS, retry if FAIL | BLOCKED, escalate |
| 2 | Locate | New triage angle, fresh evidence | YES if located and different | BLOCKED, escalate |
| 2 | Triage | Different fix strategy than Attempt 1 | YES if not already tried | FIX_ALREADY_TRIED, escalate |
| 2 | Fix | Apply revised fix, check scope | YES if applied | APPLY_FAILED, escalate |
| 2 | Verify | Re-run eval with same scenario | YES if PASS, retry if FAIL | BLOCKED, escalate |
| 3 | Locate | Last chance; deepest triage | YES if located | BLOCKED, escalate |
| 3 | Triage | Highest confidence fix remaining | YES if fixable | NOT_AUTO_FIXABLE, escalate |
| 3 | Fix | Final attempt; validate application | YES if applied | APPLY_FAILED, escalate |
| 3 | Verify | Re-run eval; capture full evidence | **FINAL** if FAIL: BLOCKED | BLOCKED (mandatory escalate) |
