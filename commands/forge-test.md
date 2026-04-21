---
name: forge-test
description: "Meta — invoke forge-self-test against the bundled seed product to validate this Forge repo’s skills and pipeline wiring (not your production product)."
---

Invoke the **`forge-self-test`** skill to run the **Forge repository self-test** only.

This exercises the **synthetic seed** product (**`seed-product/`**, seed PRDs under **`seed/prds/`**) to validate: intake → council → tech plans → build → eval → review → PR coordination **as implemented in this plugin repo**.

Reports: **pass/fail per phase**, timing, any skill invocation or output anomalies.

<HARD-GATE>
Do NOT confuse **`/forge-test`** with **`/forge`** — **`/forge-test`** validates **Forge itself**; **`/forge`** runs **your** task through **`conductor-orchestrate`** against **your** brain PRD and **`product.md`**.
</HARD-GATE>

**Forge plugin scope:** This repo + **`seed-product`**; not a substitute for product-specific **`/forge`**.
