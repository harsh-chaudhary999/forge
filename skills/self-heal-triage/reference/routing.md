# Routing, decision tree & quick-reference — reference for `self-heal-triage`

> Progressive-disclosure Level 3 (loaded on demand). The confidence-handling decision tree, the quick-reference routing card, the Forge pipeline trigger/output contract, and future-enhancement notes relocated from SKILL.md. The SKILL.md retains the operational decision spine; this file is the full routing lookup.

## Decision Tree: Confidence Handling

When classification confidence is below MEDIUM (< 60%), use this decision tree:

```
START: Classification complete, confidence score calculated
  |
  +-- Confidence >= 85% (HIGH)?
  |    YES → STOP. Classification ready for downstream routing.
  |    NO  → Continue
  |
  +-- Confidence >= 60% (MEDIUM)?
  |    YES → STOP. Classification ready, note confidence penalty in output.
  |    NO  → Continue (confidence < 60%, LOW)
  |
  +-- LOW Confidence (< 60%)
       |
       +-- Can we collect more evidence?
       |    YES:
       |      1. Expand evidence search:
       |         - Check logs from ±5 minutes around failure
       |         - Query service state (DB, cache, API)
       |         - Check process state and resource metrics
       |         - Review recent code changes in that area
       |      2. Re-run pattern matching with expanded evidence
       |      3. Recalculate confidence
       |      4. LOOP back to "Confidence >= 60%?" check
       |
       |    NO:
       |      1. Document evidence gaps (what prevented gathering more evidence?)
       |      2. Apply evidence weighting to maximize signal from available evidence
       |      3. Re-score with weights applied
       |      4. If confidence still < 60%:
       |         a. Mark output with ESCALATION: NEEDS_CONTEXT
       |         b. Attach all evidence collected
       |         c. Include confidence score and reasoning
       |         d. Route to human triage
       |      5. If confidence now >= 60%:
       |         a. STOP. Classification ready with confidence note.
```

**Key Branches Explained:**

1. **HIGH Confidence (>= 85%):** Clear signals, low ambiguity. Proceed to fix routing without additional checks.

2. **MEDIUM Confidence (60-84%):** Acceptable for automated fix attempt. Note: if first fix doesn't resolve, re-triage before second fix.

3. **LOW Confidence (< 60%) with Available Evidence:**
   - Expand search scope (logs, state, metrics)
   - Re-score with complete evidence
   - Often raises confidence to MEDIUM with just more data
   - Re-check after each evidence collection round

4. **LOW Confidence with No Additional Evidence:**
   - Apply evidence weighting to maximize signal
   - If still LOW after weighting: escalate
   - Document gaps for human investigator
   - Include confidence and evidence in escalation ticket

---

## Quick Reference Card

| Category | Primary Signals | Secondary Evidence | Confidence Triggers | High Confidence | Escalation Route |
|---|---|---|---|---|---|
| **FLAKY TEST** | timeout, deadline, race, async, intermittent | timing patterns, test isolation, external service mock | 1+ explicit timing errors + context | timeout + deadline, clear async/await issue, test passes on retry | flaky-test-fixer skill |
| **BAD TEST** | AssertionError, assertion mismatch, expected != actual | test setup, mock config, expected values | 1+ assertion mismatch + context shows it's wrong | assertion fails + API spec contradicts expectation, mock config clearly wrong | test-corrector skill |
| **REAL BUG** | Exception, TypeError, NullPointer, ReferenceError, crash | unhandled edge case, logic error, uninitialized resource | 1+ exception type + code path is valid | exception in app code + null/undefined with valid input | bug-fixer skill + tag: real_bug |
| **ENVIRONMENT** | ECONNREFUSED, ENOTFOUND, connection refused, service timeout | DNS resolution, port verification, firewall/auth | 1+ connection error + external service involved | connection refused + verified service down, DNS fails to resolve | environment-recover skill |
| **TRANSIENT** | error present in eval, absent in logs/state by triage time | one-off occurrence, no pattern history | no logging evidence but timing suggests transience | first occurrence, disappears from state before investigation | monitor + re-triage next run |
| **NEEDS_CONTEXT** | ambiguous patterns, missing evidence, unrecognized error | low confidence, conflicting signals, unable to expand evidence | < 50% confidence after evidence expansion, unresolvable ambiguity | multiple categories tied, logs missing, error code not found | human escalation ticket |

**How to Use:**

1. **Find your error in "Primary Signals"** column → identifies likely category
2. **Check "Secondary Evidence"** column → confirm with additional signals
3. **Count confidence signals from "Confidence Triggers"** → is confidence >= 60%?
4. **If HIGH confidence** (>= 85%) → proceed to "High Confidence" action
5. **If LOW confidence** (< 60%) → row indicates "NEEDS_CONTEXT"
6. **Route to skill** listed in "Escalation Route" column

**Examples:**

- Error: "timeout waiting for response" → FLAKY TEST (timeout in Primary Signals)
  - Check: is it async operation? (Secondary Evidence) → yes? → HIGH confidence
  - Route to: flaky-test-fixer skill

- Error: "ECONNREFUSED 127.0.0.1:5432" → ENVIRONMENT (ECONNREFUSED in Primary)
  - Check: is external service involved? (Secondary) → yes, DB → HIGH confidence
  - Route to: environment-recover skill

- Error: "Widget assertion failed with code XYZ_ERR_9847" → NEEDS_CONTEXT (not in Primary)
  - No primary signal match → LOW confidence
  - Try expanding evidence → check code, error handling, recent changes
  - If still can't identify → escalate as NEEDS_CONTEXT

---

## Usage in Forge Pipeline

### Trigger Points
1. **Test Failure:** Automatically classify when test fails
2. **Flaky Detection:** Run when test passes then fails repeatedly
3. **Manual Triage:** User requests classification of specific failure
4. **Batch Analysis:** Process multiple failures from CI/CD runs

### Output Format
```yaml
classification:
  type: "flaky|bad_test|real_bug|environment"
  confidence: "high|medium|low"
  score: 0.92
  evidence:
    - pattern: "timeout error"
      match: true
    - pattern: "async issue"
      match: true
  suggested_action: "Add retry logic with exponential backoff"
  links:
    - test_file: "path/to/test.js"
    - impl_file: "path/to/impl.js"
    - error_log: "path/to/log"
```

### Integration with Self-Heal
- **Flaky:** Route to flaky-test-fixer skill
- **Bad Test:** Route to test-corrector skill
- **Real Bug:** Route to bug-fixer skill with real_bug tag
- **Environment:** Route to environment-recover skill

---

## Future Enhancements

1. **Machine Learning:** Train classifier on historical failures
2. **Semantic Analysis:** Use NLP for error message understanding
3. **Cross-Correlation:** Link related failures across tests
4. **Trend Analysis:** Detect newly flaky or newly broken tests
5. **Automated Repair:** Suggest specific code fixes, not just actions
6. **Integration with Debugger:** Auto-launch debug session for real bugs
</content>
