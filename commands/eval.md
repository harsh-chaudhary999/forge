---
description: "Run end-to-end product eval — bring up stack, execute multi-surface scenarios"
---

Invoke the `forge-eval-gate` skill to run the evaluation pipeline.

## Prerequisites

- **`~/forge/brain/prds/<task-id>/eval/*.yaml`** (or `.yml`) — at least **one** scenario file, authored in **State 4b** before P4.1 (`eval-scenario-format`, `eval-translate-english`). Manual QA CSV alone is **not** a substitute for eval YAML.
- **`product.md`** must define runnable **`start`** + **`health`** (or **`deploy_doc`**) for services the eval stack needs (`eval-product-stack-up`).
- Optional **machine check** before merge or in CI:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

See **`docs/forge-task-verification.md`** in the Forge repo.

This brings up the entire product stack from worktrees, then runs multi-driver eval scenarios across all surfaces (web via CDP, API via HTTP, DB via MySQL, cache via Redis, search via ES, mobile via ADB as applicable).

Nothing merges without eval green. If eval fails, use `/heal` to diagnose and fix.
