---
name: qa-write
description: "Partial slice — after qa-prd-analysis and approved manual-test-cases.csv: author or refresh qa/semantic-automation.csv + semantic-eval-manifest (Forge machine-eval). Does not execute against the stack (use /qa-run). Unit/integration tests in repos come from forge-tdd + CSV acceptance rows."
---

## What `/qa-write` is

Forge machine-eval artifacts are **`qa/semantic-automation.csv`**, **`qa/semantic-eval-manifest.json`**, and **`qa/semantic-eval-run.log`** per **`docs/semantic-eval-csv.md`**, orchestrated by **`qa-semantic-csv-orchestrate`**.

**`qa/manual-test-cases.csv`** (from **`qa-manual-test-cases-from-prd`**) is the **human acceptance** set; those rows **inform `forge-tdd`** RED/GREEN tests in product repos. They are **not** the same file as **`semantic-automation.csv`** (machine step definitions).

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
