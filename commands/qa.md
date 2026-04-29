---
name: qa
description: "Full standalone QA pipeline — from PRD + tech plans through branch checkout, scenario generation, automated multi-surface execution on web/emulator/API, to a GREEN/RED verdict. Independent of /forge delivery pipeline."
---

Invoke the **`qa-pipeline-orchestrate`** skill to run the **complete QA pipeline** for a task.

## What this does

```
brain artifacts (PRD + tech plans)
  → generate eval scenarios (web / API / Android / iOS / DB / cache)
  → checkout named feature branches
  → configure test environment
  → start product stack (local) or target existing stack (remote)
  → execute multi-surface eval drivers
  → judge verdict (GREEN / RED / YELLOW)
  → write run report to brain
```

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

- **`~/forge/brain/prds/<task-id>/prd-locked.md`** — locked PRD (run `/intake` first)
- **`~/forge/brain/products/<slug>/product.md`** — product topology with repo paths
- For local mode: services must be startable via the `start` commands in `product.md`
- For Android: ADB connected device or emulator (`adb devices`)
- For iOS: Simulator running or Appium MCP configured (`xcrun simctl list`)

## Slices

| Command | What it runs |
|---|---|
| `/qa` | Full pipeline: write scenarios + branch prep + execute + judge |
| `/qa-write` | Scenario generation only (stops after writing `eval/*.yaml` to brain) |
| `/qa-run` | Execution only (requires existing `eval/*.yaml` in brain) |

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

**Forge plugin scope:** Skills from `skills/`; brain artifacts from `~/forge/brain/`; repos from `product.md` paths.

**Session style:** Prefer execution-style (stack-up, browser/emulator automation, terminal output). See `docs/platforms/session-modes-forge.md`.
