---
name: qa-write
description: "Partial slice — after qa-prd-analysis and approved manual-test-cases.csv: author or refresh qa/semantic-automation.csv + semantic-eval-manifest (Forge machine-eval). Align semantic steps to manual rows via TraceToCsvId where applicable. Does not execute against the stack (use /qa-run). Unit/integration tests in repos come from forge-tdd + CSV acceptance rows."
---

## What `/qa-write` is

Forge machine-eval artifacts are **`qa/semantic-automation.csv`**, **`qa/semantic-eval-manifest.json`**, and **`qa/semantic-eval-run.log`** per **[docs/semantic-eval-csv.md](../docs/semantic-eval-csv.md)**, orchestrated by **`qa-semantic-csv-orchestrate`**.

**`qa/manual-test-cases.csv`** (from **`qa-manual-test-cases-from-prd`**) is the **human acceptance** inventory; machine steps should **trace** to those rows using optional **`TraceToCsvId`** (manual CSV **`Id`** column) so **`forge-tdd`** and **`forge-eval-gate`** can reason about coverage.

They are **not** the same file as **`semantic-automation.csv`** (machine step definitions).

## Surface scoping (no CLI flags)

Unlike a slash-command **`--surface`** switch, scoping is done **in the CSV**:

- Include only the **Surface** values you want this run to cover (**`web`**, **`api`**, **`mysql`**, **`redis`**, **`es`**, **`kafka`**, **`ios`**, **`android`** — see **[docs/semantic-eval-csv.md](../docs/semantic-eval-csv.md)** § CSV columns and **`tools/verify/semantic_csv.py`** aliases).
- Partial pipelines (**`/qa-run --surface web`**) filter **at execution time** in **`qa-pipeline-orchestrate`**; the **authoring** step still defines all rows you intend to maintain.

**Worked example:** **[docs/examples/semantic-automation.csv](../docs/examples/semantic-automation.csv)**.

## Flow

```
prd-locked.md
  → qa-prd-analysis → qa/qa-analysis.md
  → qa-manual-test-cases-from-prd → qa/manual-test-cases.csv (approved)
  → qa-semantic-csv-orchestrate → qa/semantic-automation.csv + manifest + run log
  → log [P4.0-SEMANTIC-EVAL] in conductor.log when using full pipeline
```

## Usage

```
/qa-write <task-id>
```

Invoke **`qa-semantic-csv-orchestrate`** and **`docs/semantic-eval-csv.md`**; use **`python3 tools/run_semantic_csv_eval.py --task-id <id> --brain ~/forge/brain`** (and host drivers per D5) to materialize manifest + run log.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — one-step horizon; no defensive downstream-gate narration while **`prd-locked`** or **`qa-analysis.md`** is missing.
