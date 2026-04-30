---
name: qa
description: "Full standalone QA pipeline — from PRD + tech plans through branch checkout, scenario generation, automated multi-surface execution on web/emulator/API, to a GREEN/RED verdict. Independent of /forge delivery pipeline."
---

Invoke the **`qa-pipeline-orchestrate`** skill to run the **complete QA pipeline** for a task.

## What this does

```
brain artifacts (PRD + tech plans)
  → semantic automation rows (web / API / Android / iOS / DB / cache) per docs/semantic-eval-csv.md
  → checkout named feature branches
  → configure test environment
  → start product stack (local) or target existing stack (remote)
  → execute multi-surface eval drivers
  → judge verdict (GREEN / RED / YELLOW)
  → write run report to brain
```

If automation cannot run (no stack, no env), the pipeline uses **`NOT_EXECUTED`** / **`execution_scope: static_only`** — **not** **YELLOW**. See **`commands/qa-run.md`** (*When browsers / devices never start*) and **`skills/qa-pipeline-orchestrate/SKILL.md`** Edge case *Static validation only*.

## Usage

```
/qa <task-id>
/qa <task-id> --branch backend-api:feature/payment-v2 --branch web-dashboard:feature/payment-ui
/qa <task-id> --env BASE_URL=http://localhost:3000 --env DEVICE_ID=emulator-5554
/qa <task-id> --surface web                    # web only
/qa <task-id> --surface android                # android only
/qa <task-id> --surface api,db                 # api + db only
/qa <task-id> --mode remote                    # target existing/remote stack, skip local startup
```

## Prerequisites

Same **forward order** as **`/qa-write`**: **`prd-locked`** → **`qa-prd-analysis`** (**`using-forge`** **Multi-question elicitation** / Step 0.5) → **`manual-test-cases.csv`** (or valid waiver) before treating automation as grounded — see **`commands/qa-write.md`**. Council / tech plans **help** but are **not** ordering-table gates. If **`/intake`** isn’t used, see **`commands/qa-write.md`** and **`using-forge`** **Coupling, prerequisites, and alternatives**. Do not open with automation/CSV waiver prompts when upstream artifacts are missing.

**Product terms:** When **`terminology.md`** exists for the task, **`qa-prd-analysis`** / **`qa-manual-test-cases-from-prd`** / **`qa-semantic-csv-orchestrate`** load it so **expected results** and steps use **canonical** names — see [docs/terminology-review.md](../docs/terminology-review.md).

- **`~/forge/brain/prds/<task-id>/prd-locked.md`** — locked PRD (**`/intake`** default; alternatives documented in **`commands/qa-write.md`**)
- **`~/forge/brain/products/<slug>/product.md`** — product topology with repo paths
- For local mode: services must be startable via the `start` commands in `product.md`
- For Android: ADB connected device or emulator (`adb devices`)
- For iOS: Simulator running or Appium MCP configured (`xcrun simctl list`)

## Slices

| Command | What it runs |
|---|---|
| `/qa` | Full pipeline: author/refresh **`qa/semantic-automation.csv`** + manifest, branch prep, execute, judge |
| `/qa-write` | **Semantic machine-eval only** (`qa/semantic-automation.csv` + manifest per **`docs/semantic-eval-csv.md`**). Does **not** write `manual-test-cases.csv` — that path is **`qa-manual-test-cases-from-prd`** after **`qa-prd-analysis`**. |
| `/qa-run` | Execution only (requires existing **`qa/semantic-eval-manifest.json`** + **`qa/semantic-automation.csv`** — e.g. after `/qa-write`) |

**Semantic CSV vs manual CSV:** **`qa/semantic-automation.csv`** = machine step definitions. **`qa/manual-test-cases.csv`** = human/TMS baseline from **`qa-manual-test-cases-from-prd`** — not the same file as semantic automation.

## Pass `entrypoint = full (/qa)` to `qa-pipeline-orchestrate`

Tell the orchestrator: **entrypoint = full pipeline (`/qa`)** so all phases QA-P1 through QA-P7 run.

## Relationship to `/eval` and `/forge`

- **`/eval`** — runs eval against scenarios already in brain as part of the Forge delivery pipeline (State 4b)
- **`/qa`** — standalone QA run, generates scenarios fresh from PRD + tech plans, branch-aware, not tied to delivery phases
- **`/forge`** — full end-to-end delivery including implementation; `/qa` is QA-only

Use `/qa` when you want to verify a feature branch independently of whether the full forge pipeline ran (e.g. QA team testing a branch before PR review, regression check after a hotfix, testing against a staging environment).

<HARD-GATE>
A RED verdict from `/qa` must not be manually overridden. Fix the failing code and re-run `/qa-run` to obtain a verified GREEN before merging.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **headline / first § = immediate next artifact** — **not** *What unlocks machine eval*, **`qa/semantic-automation.csv`**, or Step −1 **as the main heading** when **manual CSV** / **`qa-manual-test-cases-from-prd`** / **`qa-prd-analysis`** is still the next gate (**`docs/forge-one-step-horizon.md`** **Headline = immediate next step**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Skills from `skills/`; brain artifacts from `~/forge/brain/`; repos from `product.md` paths.

**Session style:** Prefer execution-style (stack-up, browser/emulator automation, terminal output). See `docs/platforms/session-modes-forge.md`.
