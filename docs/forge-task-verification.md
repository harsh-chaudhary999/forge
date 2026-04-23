# Forge task verification (machine checks)

Forge’s **skills** and **agents** enforce Phase 4 ordering **procedurally**. This document describes an **optional machine layer**: a small **Python** tool that fails CI (or pre-push) when the **brain** is missing required artifacts or `conductor.log` shows invalid ordering.

**Tool:** [`tools/verify_forge_task.py`](../tools/verify_forge_task.py) (stdlib only; no extra pip install).

## What it checks

| Check | When it fails |
|--------|----------------|
| **Task directory** | `prds/<task-id>/` missing under `--brain` |
| **Eval YAML** | No `*.yaml` / `*.yml` files under `prds/<task-id>/eval/` |
| **`forge_qa_csv_before_eval: true`** | Resolved `products/<slug>/product.md` (via `--product` or `prd-locked.md` **Product:** matching `name:`) — requires data rows in `qa/manual-test-cases.csv` |
| **Log order** | If `conductor.log` exists: first `[P4.1-DISPATCH]` must not appear before `[P4.0-EVAL-YAML]`; with QA flag, `[P4.0-QA-CSV]` … `approved=yes` must precede `[P4.0-EVAL-YAML]` |
| **Net-new design** | If `prd-locked.md` indicates **design_new_work: yes** and no `design_waiver` … `prd_only`: requires files under `design/` and/or `[DESIGN-INGEST]` before first `[P4.1-DISPATCH]` when a log exists; if the log is missing, **design/** must be non-empty |
| **`--strict-tdd`** | `[P4.0-TDD-RED]` must appear before the first `[P4.1-DISPATCH]` |

If **`conductor.log`** is absent, **log ordering** checks are skipped by default (warning only). Use **`--require-log`** to fail when the log is missing.

## Usage

From the **Forge** clone (absolute path to the script is fine):

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

Environment default for brain:

```bash
export FORGE_BRAIN=~/forge/brain
python3 tools/verify_forge_task.py --task-id <task-id>
```

If **`forge_qa_csv_before_eval: true`** and **`prd-locked.md` `**Product:**`** does not match any `products/*/product.md` `name:` field, pass **`--product <slug>`** explicitly.

```bash
python3 tools/verify_forge_task.py --task-id add-2fa --brain ~/forge/brain --product shopapp --strict-tdd
```

Exit code **0** = all enforced checks passed; **1** = one or more failures (messages on stderr).

## CI (brain repository)

Your **brain** is usually its **own git repo**. Point CI at:

1. A checkout of the **brain** (workspace root = brain root, with `prds/`, `products/`).
2. A checkout of **Forge** (or a pinned copy of `verify_forge_task.py`).

Example (brain repo workflow): see [`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml). Set repository variables **`FORGE_TASK_ID`** and, if your Forge fork is not the default, **`FORGE_TOOLS_REPO`** (`owner/repo` for the sparse checkout of `tools/verify_forge_task.py`). If **`FORGE_TOOLS_REPO`** is unset, the template defaults to **`harsh-chaudhary999/forge`**.

Minimal inline job:

```yaml
- uses: actions/checkout@v4
  with:
    repository: ${{ vars.FORGE_TOOLS_REPO || 'harsh-chaudhary999/forge' }}
    path: forge
    sparse-checkout: |
      tools/verify_forge_task.py
    sparse-checkout-cone-mode: false
- run: python3 forge/tools/verify_forge_task.py --brain "${{ github.workspace }}" --task-id "${{ vars.FORGE_TASK_ID }}" --require-log
```

Adjust **`--brain`** if the brain content is in a subdirectory.

## Limits

- Does **not** prove scenarios are **green** or that **stack-up** works — only that **gates and files** expected by Forge’s own rules are present and ordered in the log.
- Does **not** stop a misbehaving LLM in the IDE; it stops **bad commits** and **broken merge candidates** when wired into CI or hooks.
