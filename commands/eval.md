---
name: eval
description: "Partial slice — forge-eval-gate: stack-up + multi-surface eval from committed brain scenarios. Does not author QA CSV or eval YAML (State 4b); use those skills or /forge earlier in the flow."
---

Invoke the **`forge-eval-gate`** skill to run the **evaluation pipeline** only (`eval-product-stack-up` + `eval-coordinate-multi-surface` / drivers per scenario).

## Prerequisites

- **`~/forge/brain/prds/<task-id>/eval/*.yaml`** (or `.yml`) — at least **one** scenario file, authored in **State 4b** before P4.1 (`**eval-scenario-format**`, **`eval-translate-english`**). Manual QA CSV **alone** is **not** a substitute for eval YAML.
- **`~/forge/brain/products/<slug>/product.md`** must define runnable **`start`** + **`health`** (or **`deploy_doc`**) for services the eval stack needs (`eval-product-stack-up`).
- Optional **machine check** before merge or in CI (paths relative to Forge repo root):

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

See **`docs/forge-task-verification.md`**.

<HARD-GATE>
Do NOT treat **`/eval`** as “create test cases” — **YAML scenarios** and (when required) **manual QA CSV** are **State 4b** artifacts. This command **runs** eval against existing scenarios.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Forge repo **`tools/`** and **`skills/`**; brain **`~/forge/brain/`**.

**vs `/forge`:** **`/eval`** runs **P4.4-style** eval only. Full E2E from intake through QA CSV authoring, RED, build, merge, dream: **`commands/forge.md`** (`/forge`).

**Session style:** Prefer **execution-style** (stack-up, drivers, logs). See **`docs/platforms/session-modes-forge.md`**.

**Product terms:** **`expected`** text in **`eval/*.yaml`** should match **locked** names in **`~/forge/brain/prds/<task-id>/terminology.md`** when that file exists. If a scenario predates a rename, note **terminology DRIFT** in the eval log or run report, then align YAML or the term sheet — [docs/terminology-review.md](../docs/terminology-review.md).

Nothing merges without eval **GREEN** per **`forge-eval-gate`**. If eval fails, use **`/heal`**.
