---
name: forge-status
description: "Read-only snapshot of brain health: active product, pending PRDs, eval state, decisions, worktrees — no pipeline side effects."
---

Produce a **concise status** summary for the **Forge brain** (read-only; no skill dispatch required unless the user asks to go deeper).

1. Inspect **`~/forge/brain/`** for the most recently active **product** (e.g. under **`products/<slug>/`**).
2. List **pending PRDs** (intake started but not locked), if detectable from **`prds/`** layout.
3. Note any **in-progress eval** artifacts or logs if obvious from **`prds/<task-id>/`**.
4. **Brain health:** last git commit on brain (if a repo), approximate **decisions** count under **`decisions/`** if present.
5. **Worktrees:** list open worktrees tied to active products if discoverable via git or documented paths.

Format: **one line per item**, scannable.

**Forge plugin scope:** **`~/forge/brain/`** only; no third-party status APIs.

**vs `/forge`:** Status is **observability**, not orchestration. Full E2E: **`commands/forge.md`**.
