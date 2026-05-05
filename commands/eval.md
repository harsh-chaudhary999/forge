---
name: eval
description: "Partial slice — forge-eval-gate: stack-up + semantic machine-eval (qa/semantic-automation.csv → manifest + run log). Does not author QA CSV or machine-eval artifacts (State 4b); use those skills or /forge earlier in the flow."
---

Invoke the **`forge-eval-gate`** skill to run the **evaluation pipeline** only: **`eval-product-stack-up`** then **`qa-semantic-csv-orchestrate`** / **`tools/run_semantic_csv_eval.py`** (or host drivers per **`docs/semantic-eval-csv.md`**), then **`eval-judge`.

## Prerequisites

- **`~/forge/brain/prds/<task-id>/qa/semantic-automation.csv`** committed and executed so **`qa/semantic-eval-manifest.json`** + **`qa/semantic-eval-run.log`** exist — log **`[P4.0-SEMANTIC-EVAL]`** when authoring completes (**`docs/semantic-eval-csv.md`**, **`docs/forge-task-verification.md`**).
- Manual QA CSV (**`manual-test-cases.csv`**) is human acceptance + **`forge-tdd`** traceability — not the machine-eval file.
- **`~/forge/brain/products/<slug>/product.md`** must define runnable **`start`** + **`health`** (or **`deploy_doc`**) for services the eval stack needs (**`eval-product-stack-up`**).

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

See **`docs/forge-task-verification.md`**.

<HARD-GATE>
Do NOT treat **`/eval`** as “create test cases” — **semantic CSV execution** (manifest + run log) plus (when required) **manual QA CSV** are **State 4b** artifacts. This command **runs** eval against existing committed automation.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`**.

**Forge plugin scope:** Forge repo **`tools/`** and **`skills/`**; brain **`~/forge/brain/`**.

**vs `/forge`:** **`/eval`** runs **P4.4-style** eval only. Full E2E: **`commands/forge.md`** (`/forge`).

**Product terms:** Align **`Intent`** / **`ExpectedHint`** in **`qa/semantic-automation.csv`** with **`terminology.md`** — [docs/terminology-review.md](../docs/terminology-review.md).

Nothing merges without eval **GREEN** per **`forge-eval-gate`**. If eval fails, use **`/heal`**.
