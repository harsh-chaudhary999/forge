---
stage: build
description: Context injected during Forge build phase (P3.5*/P4.0-*) — TDD, worktrees, QA CSV, semantic machine eval, review
---

# Forge — Build Stage

**You are in the BUILD phase.** Your job is to implement per the frozen spec using TDD, isolated worktrees, and pass two-stage review before eval.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, invoke it before any response. This is not negotiable.

## Iron Law

```
TEST WRITTEN AND WATCHED TO FAIL BEFORE ANY IMPLEMENTATION CODE. WORKTREE CREATED BEFORE ANY FILE EDIT. REVIEW READS THE ACTUAL DIFF — NEVER THE IMPLEMENTER'S SUMMARY. NO GATE IS SKIPPABLE BECAUSE THE CHANGE IS "SMALL".
```

## State 4b — Mandatory Before Dispatch (on /forge or forge_qa_csv_before_eval: true)

These three gates must ALL be satisfied before `[P4.1-DISPATCH]` is logged:

| Gate | Log marker | Artifact |
|---|---|---|
| QA CSV approved | `[P4.0-QA-CSV] approved=yes` | `prds/<id>/qa/manual-test-cases.csv` |
| Semantic machine eval | `[P4.0-SEMANTIC-EVAL]` | `prds/<id>/qa/semantic-automation.csv` + valid `qa/semantic-eval-manifest.json` |
| TDD RED confirmed | `[P4.0-TDD-RED]` | Failing test output observed |

**Do NOT log `[P4.1-DISPATCH]` until all three are present.**

## Active Skills (invoke in this order)

1. `forge-worktree-gate` — verify worktree exists before any edit
2. `worktree-per-project-per-task` — create isolated worktree per repo per task
3. `qa-prd-analysis` → `qa-manual-test-cases-from-prd` — QA CSV gate (get user approval)
4. `qa-semantic-csv-orchestrate` — **`qa/semantic-automation.csv`**, manifest, run log (`docs/semantic-eval-csv.md`)
5. `forge-tdd` — TDD iron law (write test → watch FAIL → implement → watch PASS)
6. `tech-plan-write-per-project` → `tech-plan-self-review` — per-repo plans
7. `forge-trust-code` — spec-reviewer + code-quality-reviewer (read the diff, not the report)

## Anti-Patterns — STOP

- **"The change is tiny, I'll skip the worktree"** — No change is too small for a worktree. One worktree per task, always.
- **"I'll write the test after I know the implementation works"** — This is not TDD. Test must be written BEFORE any implementation code and observed to FAIL on the first run.
- **"The spec-reviewer can trust my summary of what changed"** — It cannot. `forge-trust-code` reads the actual diff. Summaries are not evidence.
- **"QA CSV is optional, we can skip it this time"** — If `forge_qa_csv_before_eval: true` in product.md or if this is a `/forge` run, it is mandatory. No exceptions.
- **"Semantic automation can wait until after implementation"** — State 4b requires a valid manifest + coherent CSV before dispatch; do not treat machine eval as an afterthought.

## Subagent Dispatch Rules

- `dev-implementer` is context-isolated: it sees only the tech plan and TDD rules — NOT the full Forge bootstrap
- `spec-reviewer` reads code, not implementer reports — it is an adversary, not a collaborator
- `code-quality-reviewer` checks naming, patterns, test quality — separately from spec compliance
- Dreamer runs inline only on conflict; it does not pre-empt the review gate

## Next Gate

All of `[P4.0-QA-CSV]`, `[P4.0-SEMANTIC-EVAL]`, `[P4.0-TDD-RED]` logged → log `[P4.1-DISPATCH]` → switch to eval phase.
