---
description: "Run end-to-end product eval — bring up stack, execute multi-surface scenarios"
---

Invoke the `forge-eval-gate` skill to run the evaluation pipeline.

This brings up the entire product stack from worktrees, then runs multi-driver eval scenarios across all surfaces (web via CDP, API via HTTP, DB via MySQL, cache via Redis, search via ES, mobile via ADB as applicable).

Nothing merges without eval green. If eval fails, use `/heal` to diagnose and fix.
