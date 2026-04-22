---
name: dream-retrospect-post-pr
description: "WHEN: All PRs merged and feature shipped. Dreamer scores decisions, extracts patterns, identifies opportunities, writes learnings to brain."
type: flexible
requires: [brain-read, brain-write]
version: 1.0.0
preamble-tier: 3
triggers: []
allowed-tools:
  - Bash
  - Read
---

# Dream Retrospect Post-PR

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "Everything went well, no need for a retrospective" | Perfect outcomes hide optimization opportunities. "What would have made this 20% faster?" always has an answer. |
| "The retrospective can wait until the next sprint" | Context decays exponentially. Retrospective within hours of merge captures evidence. Retrospective a week later captures impressions. |
| "I'll just note the one big thing that went wrong" | Single-issue retrospectives miss systemic patterns. Score all 5 categories — the pattern is in the combination, not individual scores. |
| "Low scores look bad, I'll round up" | Inflated scores hide failure patterns. A gotcha that scored 2 but was recorded as 3 won't trigger the anti-pattern promotion at 2 occurrences. |
| "This was a special case, the learnings won't generalize" | Every case feels special in the moment. The pattern promotion rules (seen 3+ times = skill candidate) handle generalization — record everything. |

**If you are thinking any of the above, you are about to violate this skill.**

Post-merge retrospective scoring. The dreamer agent evaluates every decision made during the PRD-to-PR pipeline, extracts patterns, and writes learnings to the brain for future recall.

## When to Invoke

- All PRs in the coordinated set have merged to main
- Feature is shipped and eval passed in main branch
- Conductor signals `TaskCompleted`

## Scoring Rubric

Score every major decision on a 1-5 scale across 5 categories:

### Category 1: Intake Quality (1-5)

| Score | Meaning |
|---|---|
| 5 | PRD was locked with zero ambiguity. No spec changes needed during build. |
| 4 | PRD was clear. 1-2 minor clarifications during build, no scope change. |
| 3 | PRD had gaps. Required council re-negotiation or spec amendments. |
| 2 | PRD was vague. Multiple scope changes during build. Significant rework. |
| 1 | PRD was wrong. Feature shipped doesn't match original intent. |

**Evidence to collect:** Number of spec amendments, scope change requests, stakeholder re-clarifications.

### Category 2: Council Negotiation (1-5)

| Score | Meaning |
|---|---|
| 5 | All 4 surfaces + 5 contracts agreed first time. Zero conflicts during build. |
| 4 | Minor conflicts resolved during council. No conflicts during build. |
| 3 | Contracts required amendment during build. 1-2 cross-service issues. |
| 2 | Major contract violations during eval. Required re-negotiation. |
| 1 | Council missed critical integration requirement. Service-level failure. |

**Evidence to collect:** Contract amendments, cross-service eval failures, dreamer inline invocations.

### Category 3: Tech Plan Accuracy (1-5)

| Score | Meaning |
|---|---|
| 5 | All tasks completed as planned. Zero deviations. Estimates accurate. |
| 4 | 1-2 tasks required adjustment. Minor estimation drift. |
| 3 | 3+ tasks required rework. Plan had placeholder or ambiguous sections. |
| 2 | Plan was structurally wrong. Major task reordering or additions needed. |
| 1 | Plan was abandoned mid-build. Started from scratch. |

**Evidence to collect:** Task completion rate, deviation log, added/removed tasks.

### Category 4: Build Execution (1-5)

| Score | Meaning |
|---|---|
| 5 | All tests green on first pass. Zero self-heal loops. Clean commits. |
| 4 | 1 self-heal loop. Minor test fixes. Clean final state. |
| 3 | 2-3 self-heal loops. Some flaky tests. Required debugging. |
| 2 | Max self-heal loops hit. Required escalation. Significant rework. |
| 1 | Build failed repeatedly. Required human intervention to unblock. |

**Evidence to collect:** Self-heal loop count, escalation count, commit history.

### Category 5: Eval Coverage (1-5)

| Score | Meaning |
|---|---|
| 5 | All scenarios passed. Full cross-surface coverage. No gaps found post-merge. |
| 4 | All scenarios passed. Minor coverage gaps identified but non-critical. |
| 3 | Some scenarios required retry. Coverage missed 1 edge case found post-merge. |
| 2 | Eval missed significant failure mode. Bug found in production post-merge. |
| 1 | Eval was ineffective. Critical bug shipped. |

**Evidence to collect:** Scenario pass rates, post-merge bug reports, coverage analysis.

## Pattern Extraction

After scoring, extract patterns in three buckets:

### Patterns (What Worked)
- Decisions that scored 4-5
- Approaches that prevented problems
- Format: `PATTERN: {description} | Evidence: {what happened} | Applicable when: {conditions}`

### Gotchas (What Failed)
- Decisions that scored 1-2
- Approaches that caused rework or failure
- Format: `GOTCHA: {description} | Evidence: {what happened} | Avoid when: {conditions}`

### Opportunities (What Was Missed)
- Things not attempted that would have helped
- Improvements for next iteration
- Format: `OPPORTUNITY: {description} | Would have helped because: {reasoning} | Implement by: {action}`

## Pattern Promotion Rules

| Condition | Action |
|---|---|
| Pattern seen 1 time | Record in brain as `warm` decision |
| Pattern seen 2 times (same product) | Promote to `active` decision |
| Pattern seen 3+ times (across products) | Promote to **skill candidate** — flag for `forge-writing-skills` |
| Gotcha seen 2+ times | Add to relevant skill's anti-pattern preamble |
| Gotcha seen 3+ times | Create dedicated anti-pattern skill |

## Confidence Scoring

Each learning gets a confidence score:

| Confidence | Criteria |
|---|---|
| HIGH | Clear causal evidence. Repeatable. Would recommend unconditionally. |
| MEDIUM | Correlational evidence. Worked here, likely generalizes. Some caveats. |
| LOW | Single observation. Might be context-specific. Worth tracking. |

## Brain Write Format

Write retrospective to: `~/forge/brain/products/{product-slug}/learnings/{prd-id}-retrospective.md`

```markdown
# Retrospective: {PRD Title}

## Scores
| Category | Score | Evidence |
|---|---|---|
| Intake Quality | X/5 | {brief evidence} |
| Council Negotiation | X/5 | {brief evidence} |
| Tech Plan Accuracy | X/5 | {brief evidence} |
| Build Execution | X/5 | {brief evidence} |
| Eval Coverage | X/5 | {brief evidence} |

**Overall: X/25**

## Patterns
- PATTERN: ...

## Gotchas
- GOTCHA: ...

## Opportunities
- OPPORTUNITY: ...

## Promotions
- {pattern/gotcha} promoted to {level} (seen N times)
```

Commit with message: `brain: retrospective for {prd-id} (score: X/25)`

## Edge Cases

### Edge Case 1: No Clear Failures (All 5s)
**Action:** Still write retrospective. Focus on opportunities. Perfect scores hide optimization potential. Ask: "What would have made this 20% faster?"

### Edge Case 2: Catastrophic Failure (Score < 10/25)
**Action:** Write retrospective with CRITICAL flag. Escalate gotchas to relevant skill maintainers. Consider whether the failure mode needs a new skill or anti-pattern preamble.

### Edge Case 3: External Factors (Infra Down, API Changed)
**Action:** Score based on team response, not the external event. Did intake anticipate the risk? Did eval catch it? External factors are opportunities, not excuses.

### Edge Case 4: Single-Repo Product (No Cross-Surface)
**Action:** Council score is N/A. Adjust to 4-category scoring (out of 20). Still extract patterns — single-repo has its own failure modes.

### Edge Case 5: Retrospective Contradicts Prior Learning
**Action:** Update the prior learning with new evidence. Don't create conflicting entries. Brain should converge, not diverge.

## Post-Retrospective: Scan Refresh

After writing the retrospective, the codebase has changed — PRs merged means modules added, dependencies changed, API surface updated. The brain scan is now stale.

**REQUIRED: Trigger a codebase scan refresh after every retrospective.**

```bash
# Check scan age
cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep scanned_at

# Re-run scan (always after PR merge — codebase changed)
# Invoke scan-codebase skill for each repo in the product
```

**Why this matters:**
- The next `/intake` or `/council` session will load stale module maps if scan isn't refreshed
- New modules added by this feature won't appear in hub scoring
- Architecture patterns may have shifted (e.g., a new service was introduced)
- `product-context-load` will flag a staleness warning — preempt it here

**Scan failure handling:**
- If scan fails or is blocked (e.g., repo not accessible): write `scan-status: STALE` into the retrospective file and flag in the retrospective output
- Do NOT fail the retrospective because the scan failed — retrospective is independent
- Escalation: `DONE_WITH_CONCERNS` if scan could not be refreshed

**Commit convention for post-retrospective scan:**
```bash
git -C ~/forge/brain commit -m "scan: refresh after <prd-id> merge — <N> files, <N> hubs"
```

## Cross-References

- **brain-write**: For persisting retrospective to brain
- **brain-recall**: For checking prior patterns before writing new ones
- **conductor-orchestrate**: Signals when to invoke retrospective
- **forge-writing-skills**: For promoting patterns to skill candidates
- **scan-codebase**: Invoked after retrospective to refresh brain's module map
