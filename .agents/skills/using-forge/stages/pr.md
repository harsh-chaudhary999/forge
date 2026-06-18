---
stage: pr
description: Context injected during Forge PR/dream phase (P5.*) — PR coordination, merge ordering, dreamer retrospective
---

# Forge — PR Stage

**You are in the PR phase.** Eval is GREEN. Your job is to coordinate PRs across repos in the correct merge order, merge them, and run the dreamer retrospective.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, invoke it before any response. This is not negotiable.

## Iron Law

```
NO PR IS RAISED UNTIL EVAL IS GREEN IN brain/prds/<task-id>/conductor.log. MERGE ORDER IS LOCKED BEFORE THE FIRST MERGE. DREAMER RETROSPECTIVE RUNS AFTER ALL PRS MERGE — NOT BEFORE, NOT SKIPPED.
```

## Active Skills (invoke in this order)

1. `pr-set-coordinate` — collects all branch/PR references across repos, validates eval GREEN precondition
2. `pr-set-merge-order` — determines safe merge sequence (dependency order, schema-first, API-before-consumers)
3. Merge each PR in the locked order — do NOT deviate from the sequence
4. `dream-retrospect-post-pr` — runs dreamer scoring + brain learnings after all PRs merge
5. `brain-write` — commits all retrospective decisions to brain

## Merge Order Rules

- Schema migrations merge **before** API changes that depend on them
- Backend API merges **before** frontend consumers
- Infrastructure changes merge **before** services that depend on them
- If two PRs are independent: alphabetical by repo slug as tiebreaker

## Anti-Patterns — STOP

- **"Eval was GREEN yesterday, it's fine to merge now"** — Re-verify `[P4.4-EVAL-GREEN]` exists in conductor.log. Stale GREEN is not GREEN.
- **"I'll merge all PRs at once and figure out conflicts after"** — Merge order is determined by `pr-set-merge-order` before the first merge. Improvising order causes integration failures.
- **"Dreamer retrospective can wait, we're done"** — Dreamer runs after ALL merges. It writes brain learnings that prevent the same mistakes in future tasks. Skipping it accumulates technical debt in the brain.
- **"One repo's PR can wait, I'll merge the others first"** — If a PR is in the set, it must merge in this release. Partial sets leave the product in a mixed-version state.

## Brain Writes Required

- `~/forge/brain/prds/<task-id>/conductor.log` — append `[P5-PR-MERGED] task_id=<id> repos=N`
- `~/forge/brain/prds/<task-id>/retrospective.md` — dreamer output
- Any new decisions from dreamer → `brain-write` to decisions/

## Next Gate

All PRs merged + `[P5-PR-MERGED]` logged + retrospective written → task complete. Update `forge-status` for the product.
