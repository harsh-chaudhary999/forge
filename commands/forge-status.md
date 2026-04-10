---
description: "Show current Forge status: active product, pending PRDs, eval state, brain health"
---

Show the current Forge status:
1. Read `~/forge/brain/` to find the most recently active product
2. List any pending PRDs (intake-started but not locked)
3. Show current eval state if any evals are in progress
4. Report brain health: last commit date and total decision count
5. List any open worktrees across active products

Format output as a concise status summary, one line per item.
