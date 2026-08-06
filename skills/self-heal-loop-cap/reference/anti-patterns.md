# Self-heal loop-cap — HARD-GATE anti-patterns (reference for `self-heal-loop-cap`)

> Progressive-disclosure Level 3 (loaded on demand). The five violation-criteria anti-patterns with full enforcement detail. The SKILL.md keeps the Anti-Pattern Preamble summary table.

## HARD-GATE Anti-Patterns (Violation Criteria)

### Anti-Pattern 1: "3 attempts is conservative — just try more"

**Why It Fails:**
The 3-attempt cap prevents infinite loops that consume tokens, delay pipeline delivery, and mask fundamental architectural issues. Unbounded retries create false confidence in fix validity. After 3 systematic attempts using evidence from each cycle, attempting more is debugging theater, not engineering.

**Enforcement (MUST):**
1. MUST honor the hard cap: 3 retry attempts maximum
2. MUST track attempt counter accurately; no skipping or resetting
3. MUST escalate immediately when attempt_count reaches 3 and verification fails
4. MUST document why you believe a 4th attempt would differ (if tempted)
5. MUST rely on escalation for fresh human perspective, not retry loop hunger

---

### Anti-Pattern 2: "If the fix looks right, skip verify and move on"

**Why It Fails:**
Self-heal fixes are only valid after re-running the exact evaluation scenario that initially failed. A theoretically correct fix is not proven correct until the original failure reproduces and passes. Skipping verify means you cannot distinguish lucky silence from actual healing.

**Enforcement (MUST):**
1. MUST always re-run the evaluation after applying any fix
2. MUST verify using the identical scenario/inputs that triggered the original failure
3. MUST capture the full verify result (pass/fail, output, logs, timing)
4. MUST fail the attempt if verify was skipped or abbreviated
5. MUST treat incomplete verify cycles as attempt waste; they do not count toward completion

---

### Anti-Pattern 3: "BLOCKED means we failed — try one more time"

**Why It Fails:**
BLOCKED is an explicit escalation signal indicating that the current attempt vector is unsafe or impossible. Overriding BLOCKED to squeeze in another retry violates the escalation protocol and often repeats the same failure under different framing.

**Enforcement (MUST):**
1. MUST respect BLOCKED status from any phase (locate, triage, fix, verify)
2. MUST NOT retry after BLOCKED; immediately escalate
3. MUST include the BLOCKED reason and phase in escalation report
4. MUST treat BLOCKED as terminal within the current loop iteration
5. MUST document why BLOCKED was triggered before escalating

---

### Anti-Pattern 4: "Evidence from attempt 1 is still valid for attempt 3"

**Why It Fails:**
System state changes between attempts. Services restart, caches clear, environment variables shift, deployment progresses. Evidence stale by 2 attempts may point to a fault that no longer exists or mask a new fault. Reusing old evidence causes retriage of ghosts and fixes for problems that changed shape.

**Enforcement (MUST):**
1. MUST collect fresh evidence on each attempt (logs, state, error messages)
2. MUST re-triage failure on each attempt using current evidence
3. MUST recheck system state before applying each fix
4. MUST document state changes observed between attempts
5. MUST discard previous attempt evidence from active decision making; use only for escalation trail

---

### Anti-Pattern 5: "Loop cap only applies to code bugs, not infra faults"

**Why It Fails:**
Infrastructure failures classified as `RED_INFRA` by `forge-eval-gate` (ECONNREFUSED, Docker daemon down, MCP unavailable) do **NOT** consume a retry cycle — they escalate immediately to BLOCKED. Only classification types `CODE_BUG`, `FLAKY`, and `TEST_BUG` from `self-heal-triage` consume retries from the 3-attempt budget.

**Enforcement (MUST):**
1. MUST apply 3-attempt cap to code faults, config errors, and flaky/test failures
2. MUST NOT consume a retry attempt for `RED_INFRA` outcomes — escalate immediately
3. MUST check `self-heal-triage` RED_INFRA Pre-Check output before incrementing attempt counter
4. MUST document fault category in escalation for proper routing
5. MUST treat "it's an infra problem so we can retry more" as anti-pattern violation

---

