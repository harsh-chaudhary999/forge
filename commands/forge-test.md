---
description: "Run Forge end-to-end self-test on the synthetic seed product"
---

Invoke the `forge-self-test` skill to run the full Forge pipeline against the seed product (ShopApp).

This validates the entire system: intake → council → tech plans → build → eval → review → PR coordination. Uses the seed product at `seed-product/` and the seed PRD at `seed/prds/01-favorites-cross-surface-sync.md`.

Reports: pass/fail per phase, total time, any skills that failed to invoke or produced unexpected output.
