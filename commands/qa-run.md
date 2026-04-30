---
name: qa-run
description: "Partial slice — execute existing eval scenarios against named feature branches and a target environment. Requires eval/*.yaml already in brain (run /qa-write first). Chains: branch checkout → env config → stack-up → multi-surface drivers → verdict."
---

**Input is `eval/*.yaml` only** (automation). Does not read **`manual-test-cases.csv`**. Optional: read **`~/forge/brain/prds/<task-id>/terminology.md`** when present so **verdicts** and **run reports** use **canonical** product labels ([docs/terminology-review.md](../docs/terminology-review.md)).

Invoke **`qa-pipeline-orchestrate`** starting at **Phase QA-P3** (branch prep) to execute eval scenarios that already exist in brain.

## What this does

```
existing eval/*.yaml in brain
  → checkout named feature branches (with confirmation)
  → write .eval-env (runtime overrides for drivers)
  → start product stack in dependency order (local mode)
  → run web/mobile/API/DB/cache drivers against all scenario files
  → judge: GREEN / RED / YELLOW
  → write run report to brain/prds/<task-id>/qa/
```

## Usage

```
/qa-run <task-id>
/qa-run <task-id> --branch backend-api:feature/payment-v2 --branch web-dashboard:feature/payment-ui
/qa-run <task-id> --env BASE_URL=http://localhost:3000 --env DEVICE_ID=emulator-5554
/qa-run <task-id> --surface web
/qa-run <task-id> --surface android --env DEVICE_ID=emulator-5554
/qa-run <task-id> --surface ios --env IOS_SIMULATOR_ID=booted
/qa-run <task-id> --mode remote --env BASE_URL=https://staging.myapp.com
/qa-run <task-id> --from QA-P5   # re-run execution only, skip branch checkout
```

## Input reference

| Flag | Default | Description |
|---|---|---|
| `--branch repo:branch` | stay on current | Branch to checkout per repo (repeat for multiple repos) |
| `--env KEY=VALUE` | from .eval-env if exists | Runtime env override for eval drivers (repeat for multiple) |
| `--surface <list>` | all | Comma-separated: `web`, `android`, `ios`, `api`, `db`, `cache`, `kafka`, `all` |
| `--mode local\|remote` | `local` | `local` = start stack locally; `remote` = target existing URL, skip stack-up |
| `--from <phase>` | `QA-P3` | Resume from a specific phase (useful after a partial failure fix) |

## Prerequisites

- **`qa-write-scenarios` Step −1** satisfied **before** `/qa-write`: **`prd-locked.md`**, **`qa-prd-analysis`** + **`qa-analysis.md`**, then **`manual-test-cases.csv`** or documented waiver where policy requires — see **`skills/qa-write-scenarios/SKILL.md`**. `/qa-run` assumes upstream authoring order was respected.
- **`~/forge/brain/prds/<task-id>/eval/*.yaml`** — scenarios must exist (run `/qa-write` first)
- **`~/forge/brain/products/<slug>/product.md`** — for repo paths and service start commands
- For Android: `adb devices` shows connected device or running emulator
- For iOS: simulator running (`xcrun simctl list | grep Booted`) or Appium MCP configured

## Local vs Remote mode

**Local mode (default):** Stack is started by Forge on the current machine. Use when testing on a dev machine or CI with a fresh environment.

**Remote mode (`--mode remote`):** Stack is already running (staging, preview, CI environment). Forge skips stack-up entirely. Point `BASE_URL` and other env vars at the remote stack. Branch checkout is still recorded for reproducibility even if the remote runs a different SHA.

## When browsers / devices never start (expected in some sessions)

If stack-up is skipped and drivers are not invoked (no reachable URL, no emulator, no credentials), the pipeline records **`NOT_EXECUTED`** / **`execution_scope: static_only`** — **not** **YELLOW**. **YELLOW** from **`eval-judge`** means automation ran and some non-critical steps failed. See **`skills/qa-pipeline-orchestrate/SKILL.md`** **Phase QA-P6**, **Edge Cases → Static validation only**, and the QA-P7 report template **Why WebDriver / Appium / ADB did not run**.

## After a RED verdict

```
/qa-run <task-id> --from QA-P5   # skip branch checkout, re-run execution only after fixing code
/qa-run <task-id>                 # full re-run including branch checkout (if you switched branches)
```

Do not manually declare a fix GREEN without a verified re-run. The report must show a new passing run.

## What gets written to brain

```
~/forge/brain/prds/<task-id>/
  qa/
    branch-env-manifest.md       # repo SHAs + env vars used in this run
    qa-run-report-<timestamp>.md # scenario results, verdict, failure details, next actions
  qa-pipeline.log                 # gate log lines for every phase
```

<HARD-GATE>
Do NOT declare the feature ready to merge on a RED or YELLOW **product** verdict after drivers ran. **`NOT_EXECUTED`** means no product verdict yet — obtain GREEN after a real **`/qa-run`** against an environment. Fix → re-run → GREEN is the only valid path to merge readiness.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Skills from `skills/`; brain from `~/forge/brain/`; repo paths from `product.md`.

**vs `/eval`:** `/eval` is the forge delivery pipeline eval gate (State P4.4, requires State 4b artifacts). `/qa-run` is standalone — works without a full conductor run, targets any branch, generates its report independently.

**vs `/qa`:** `/qa-run` assumes eval YAML already exists. `/qa` writes scenarios first then runs them.
