---
name: qa-pipeline-orchestrate
description: "WHEN: A standalone QA run is needed against named feature branches and a target environment — independent of the full /forge delivery pipeline. Chains: brain read → scenario generation → branch prep → stack-up → multi-surface exec → verdict."
type: rigid
requires: [brain-read, qa-prd-analysis, qa-write-scenarios, qa-branch-env-prep, eval-product-stack-up, eval-coordinate-multi-surface, eval-judge]
version: 1.0.5
preamble-tier: 3
triggers:
  - "run QA pipeline"
  - "start QA run"
  - "qa-pipeline"
  - "test the branch"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - mcp__*
---

# QA Pipeline Orchestrator

Standalone QA pipeline that runs from brain artifacts (PRD + tech plans) through to a GREEN/RED verdict, scoped to specific feature branches and a target environment. This is independent of the full Forge delivery pipeline — it does not require a full conductor run and does not author implementation code or PRs.

## Human input (all hosts)

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Map to the host’s **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor **`AskQuestion`**; hosts without the tool: **numbered options + stop**). See **`using-forge`** **Interactive human input** and **Stage-local questioning**; scenario ordering rules in **`qa-write-scenarios`** **Step −1**.

**Entry points:**
- `/qa` — full pipeline (write scenarios + branch prep + execute + judge)
- `/qa-write` — write scenarios only (stops after Step QA-P2)
- `/qa-run` — execute only (requires scenarios already in brain; starts at Step QA-P3)

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll skip scenario generation, I know what to test" | Untraceable tests cannot be audited. Every scenario must trace to a PRD criterion. |
| "I'll run against main instead of the feature branch" | Testing the wrong branch produces a false GREEN that masks what the feature branch actually does. |
| "Stack is probably already running, I'll skip stack-up" | Probably is not verified. Stack-up health checks are the only authoritative readiness signal. |
| "I'll run only the web surface for a full-stack feature" | A web GREEN with a broken API write is still a broken feature. Multi-surface is not optional for full-stack changes. |
| "The QA run failed but I'll fix it manually and not re-run" | A manual fix without a re-run produces no evidence. The verdict must come from an automated run, not a claim. |
| "I don't need to write results to brain — I can see them in the terminal" | Terminal output is ephemeral. Brain artifacts are auditable across sessions, teams, and CI runs. |
| "`/qa` invoked — I'll use a blocking prompt about eval/CSV waiver before checking brain" | **Violates stage-local questioning** (`using-forge`) **and** **`qa-write-scenarios` Step −1`**: **`prd-locked`** → **`qa-prd-analysis`** → **`manual-test-cases.csv`** (or valid waiver) → **then** QA-P2 eval YAML. Read brain **first**; surface the **first missing** artifact — never a **blocking interactive prompt** about downstream QA/evYAML choices before upstream prerequisites exist. |

**If you are thinking any of the above, you are about to violate this skill.**

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] `task_id` is known and `prd-locked.md` exists in brain
- [ ] Product slug is known (resolves `product.md` and repo paths)
- [ ] Entry point is clear: `/qa` (full), `/qa-write` (scenarios only), or `/qa-run` (execute only)
- [ ] If `/qa-run`: `eval/*.yaml` scenario files already exist in brain
- [ ] Branches and target env are confirmed (or `mode: remote` with valid BASE_URL)

## Pre-Implementation Checklist

Before advancing past QA-P1:

- [ ] `prd-locked.md` verified to exist for the task
- [ ] `product.md` readable and repo paths exist on disk
- [ ] Pipeline phases to execute determined (full vs partial entry point)
- [ ] Resume point identified if restarting after a RED verdict (`--from=QA-PX`)

## Post-Implementation Checklist

Before reporting pipeline complete:

- [ ] All active phase gate lines present in `qa-pipeline.log` (QA-P1 through QA-P7)
- [ ] QA run report committed to brain under `qa/qa-run-report-<ts>.md`
- [ ] If RED verdict: failure root cause documented and `self-heal-triage` invoked
- [ ] If MCP TMS configured: test run linked back to Jira/TestRail ticket
- [ ] Verdict (GREEN / YELLOW / RED) surfaced to user with evidence path

---

## Cross-References

- **`using-forge`** — **Stage-local questioning** (all phases): prompts must unblock **only** the current stage.
- **`qa-write-scenarios` Step −1** — QA→eval **prerequisite order** before QA-P2 or any **blocking interactive prompt** about CSV/evYAML: **`prd-locked.md`** → **`qa-prd-analysis`** → **`manual-test-cases.csv`** or documented waiver — never invert.
- **`qa-prd-analysis`** — must run before this skill (unless reusing existing scenarios) to produce `qa/qa-analysis.md` which feeds QA-P2.
- **`qa-write-scenarios`** — invoked at QA-P2 to generate eval YAML from brain artifacts and `qa-analysis.md`.
- **`qa-branch-env-prep`** — invoked at QA-P3 to check out feature branches and write `.eval-env`.
- **`eval-product-stack-up`** — invoked at QA-P4 to start local services in dependency order.
- **`eval-coordinate-multi-surface`** — invoked at QA-P5 to dispatch scenarios to surface-specific drivers.
- **`eval-judge`** — invoked at QA-P6 to render GREEN / YELLOW / RED verdict from execution results.
- **`self-heal-triage`** — invoked when verdict is RED to classify failure root cause before re-run.

---

## MCP Integration

This skill coordinates other skills that themselves use MCP tools. In addition, the orchestrator may invoke MCP directly for:

| MCP Server | Phase | Use |
|---|---|---|
| Browser MCP (`mcp__browser__navigate`, `mcp__browser__click`) | QA-P5 | Alternative to `eval-driver-web-cdp` for browser-based test execution when a Browser MCP server is installed |
| Appium MCP | QA-P5 | Mobile test execution for Android/iOS scenarios when an Appium MCP server is installed instead of local ADB/XCTest drivers |
| DB MCP (`mcp__db__query`) | QA-P5 | Database verification steps (SELECT assertions after write actions) when a DB MCP server is available |
| Jira MCP (`mcp__claude_ai_Atlassian__createJiraIssue`) | QA-P7 | Create Jira bug tickets automatically for each RED scenario, linked to the test run |
| TestRail / Xray MCP | QA-P7 | Update test run status in TMS with PASS/FAIL per scenario after the verdict |

**Driver resolution order:** If a MCP-based driver is available for a surface, prefer it over a local binary driver (adb, mysql CLI). Record which driver variant was used in the QA run report.

---

## Iron Law

```
NO QA VERDICT IS VALID WITHOUT EVIDENCE FROM EVERY ACTIVE SURFACE IN THE SCENARIO.
NO VERDICT IS ACCEPTED FROM A MANUAL FIX WITHOUT A FULL RE-RUN OF THE QA PIPELINE.
EVERY RUN IS COMMITTED TO BRAIN WITH ITS SHA EVIDENCE — TERMINAL OUTPUT IS NOT A REPORT.
```

## Red Flags — STOP

- **task_id does not resolve to a brain PRD** — STOP. The pipeline cannot operate without `prd-locked.md`. Ask user to run `/intake` first or provide the correct task_id.
- **No eval YAML in brain and `/qa-run` was invoked** — STOP. `/qa-run` requires existing scenarios. Ask user to run `/qa-write` first.
- **Branch checkout failed for any repo** — STOP. Do not run eval against a partially-checked-out product.
- **Stack health check failed in local mode** — STOP. Do not run eval against a broken stack. Report which service failed to start.
- **eval-judge returns RED and user asks to merge anyway** — STOP. RED verdict is a hard gate. Fix the failure and re-run.
- **Scenario count in brain is 0** — STOP. No scenarios = no coverage = no valid verdict. Ask user to check PRD completeness.

## Pipeline Phases

```
QA-P1: Load brain artifacts
QA-P2: Generate eval scenarios (skip if /qa-run)
QA-P3: Branch checkout + env prep  ← determines run mode
QA-P4: Stack-up (skip if url-only / branch-tracking / branch-code-validate)
QA-P5: Multi-surface execution     (skip if branch-code-validate — test suite results used instead)
QA-P6: Judge verdict
QA-P7: Report + brain commit
```

**branch-code-validate shortcut:** QA-P3 → QA-P6 (test suite output feeds directly into eval-judge, skipping QA-P4 and QA-P5)

Each phase logs a gate line to `~/forge/brain/prds/<task-id>/qa-pipeline.log`.

---

## Phase QA-P1 — Load Brain Artifacts

**Before QA-P2:** Satisfy **`qa-write-scenarios` Step −1** — if **`prd-locked.md`** missing, **BLOCK** (user runs **`/intake`**); if **`qa/qa-analysis.md`** missing or interrogation not done in chat, run **`qa-prd-analysis`** first; if CSV baseline missing and no valid waiver, **`qa-manual-test-cases-from-prd`** before generating **`eval/*.yaml`**. Do not prompt the user about downstream waivers until upstream steps exist.

```bash
BRAIN=~/forge/brain
TASK=<task-id>
SLUG=<slug>

# Verify required artifacts exist
test -f "$BRAIN/prds/$TASK/prd-locked.md" \
  || { echo "BLOCKED: prd-locked.md not found for task $TASK"; exit 1; }

cat "$BRAIN/prds/$TASK/prd-locked.md"
cat "$BRAIN/products/$SLUG/product.md"
ls "$BRAIN/prds/$TASK/tech-plans/" 2>/dev/null
ls "$BRAIN/prds/$TASK/eval/" 2>/dev/null && echo "SCENARIOS PRESENT"
```

Log:
```
[QA-P1-LOAD] task_id=<task-id> prd=found tech_plans=<n> existing_scenarios=<n|none>
```

---

## Phase QA-P2 — Generate Eval Scenarios

**Skip this phase if:** `/qa-run` was invoked AND `eval/*.yaml` already exist in brain.

**Order:** Same as **`qa-write-scenarios` Step −1** — never a **blocking interactive prompt** about YAML-before-CSV while **`prd-locked`** or **`qa-analysis.md`** (post-interrogation) is absent.

Invoke `qa-prd-analysis` first (reads PRD, maps surfaces, writes `qa/qa-analysis.md` to brain).
Complete **`qa-manual-test-cases-from-prd`** so **`qa/manual-test-cases.csv`** has ≥1 approved data row — **unless** `qa-analysis.md` frontmatter waives (see **`qa-write-scenarios`** Step 0.0).
Then invoke `qa-write-scenarios` (reads qa-analysis.md + tech plans + CSV baseline, writes `eval/*.yaml`).

**HARD-GATE:** Do not advance to QA-P3 until:
- `~/forge/brain/prds/<task-id>/qa/qa-analysis.md` exists
- **`qa/manual-test-cases.csv` baseline satisfied** (data rows **or** waiver per **`qa-write-scenarios`**) before treating QA-P2 scenario generation as complete
- `~/forge/brain/prds/<task-id>/eval/` contains at least one `.yaml` file
- `~/forge/brain/prds/<task-id>/qa/scenarios-manifest.md` exists

Log:
```
[QA-P2-SCENARIOS] task_id=<task-id> scenario_files=<list> total_scenarios=<n> status=WRITTEN
```

---

## Phase QA-P3 — Branch Checkout and Env Prep

Invoke `qa-branch-env-prep`. It will first ask the user to select a run mode:

| Run mode | What happens next |
|---|---|
| `url-only` | `.eval-env` written with provided URLs; skip QA-P4 (stack already running) |
| `branch-local` | Branches checked out; `.eval-env` written; QA-P4 starts the local stack |
| `branch-code-validate` | Branches checked out; repo test suites run directly (Step 4b); skip QA-P4 and QA-P5 eval drivers; go to QA-P6 verdict using test output |
| `branch-tracking` | Branches recorded for traceability; `.eval-env` written with remote URLs; skip QA-P4 |

Pass the full input config:

```yaml
task_id: <task-id>
slug: <slug>
run_mode: <determined interactively>
branches:
  <repo>: <branch>
  ...
env:
  BASE_URL: ...   # for url-only / branch-local / branch-tracking
  ...
```

**HARD-GATE:** Do not advance to QA-P4 until:
- `~/forge/brain/prds/<task-id>/qa/branch-env-manifest.md` exists (with `run_mode` field)
- If `branch-local` or `url-only`: `~/forge/brain/prds/<task-id>/.eval-env` exists with correct permissions
- If `branch-local` or `branch-code-validate`: all requested branches verified at correct SHA
- If `branch-code-validate`: `[QA-CODE-VALIDATE]` logged with pass/fail counts
- `[QA-BRANCH-ENV]` logged to `qa-pipeline.log`

**For `branch-code-validate`:** After QA-P3, skip QA-P4 and QA-P5. Feed the test suite results directly into QA-P6 (`eval-judge`) as if they were scenario execution results. The verdict is: PASS if all repos exit 0, FAIL if any repo exits non-zero.

---

## Phase QA-P4 — Stack Up

**Skip this phase if:** `run_mode` is `url-only`, `branch-tracking`, or `branch-code-validate`.

Load env before invoking stack-up:
```bash
set -a && source ~/forge/brain/prds/<task-id>/.eval-env && set +a
```

Invoke `eval-product-stack-up`:
- Reads `product.md` for service start commands
- Starts services in dependency order
- Runs health checks for each configured service
- Reports READY or FAILED

**HARD-GATE:** All configured services must be READY before proceeding to QA-P5. A single FAILED service aborts the pipeline with `BLOCKED — fix service startup before running eval`.

Log:
```
[QA-P4-STACK] task_id=<task-id> services=<n> status=READY|FAILED
```

---

## Phase QA-P5 — Multi-Surface Execution

**Skip this phase if:** `run_mode` is `branch-code-validate`. In that mode, the test suite results from Step 4b (logged as `[QA-CODE-VALIDATE]`) are passed directly to QA-P6 as the execution evidence.

Load env:
```bash
set -a && source ~/forge/brain/prds/<task-id>/.eval-env && set +a
```

Invoke `eval-coordinate-multi-surface` with:
- Scenario files from `~/forge/brain/prds/<task-id>/eval/`
- Surface filter from `--surface` flag (default: all surfaces present in scenario files)
- Env variables sourced from `.eval-env`

**Hotfix narrow scope:** If **`qa/qa-analysis.md`** YAML lists **`hotfix_surfaces: [api, web]`** (set during **`qa-prd-analysis`** for urgent patches), run only scenarios whose **`surface`** matches that set; log others as **`SKIP (hotfix scope)`** — do not treat as pass.

The coordinator chains drivers in scenario order:
1. Web scenarios → `eval-driver-web-cdp`
2. API scenarios → `eval-driver-api-http`
3. DB verification steps → `eval-driver-db-mysql`
4. Cache verification steps → `eval-driver-cache-redis`
5. Event verification steps → `eval-driver-bus-kafka`
6. Android scenarios → `eval-driver-android-adb`
7. iOS scenarios → `eval-driver-ios-xctest`

**HARD-GATE:** Every in-scope scenario must be attempted. No scenario is silently skipped unless its `requires_device: true` and `DEVICE_ID` is absent from `.eval-env` — that scenario gets `SKIP` status, not silent omission. (**Hotfix scope** reduces what “in-scope” means — see above.)

Log:
```
[QA-P5-EXEC] task_id=<task-id> scenarios_run=<n> pass=<n> fail=<n> skip=<n>
```

---

## Phase QA-P6 — Verdict

Invoke `eval-judge` with the result payload from QA-P5.

`eval-judge` applies the judgment algorithm:
- **GREEN** — all critical scenarios PASS, no non-retried FAILs
- **YELLOW** — non-critical failures with documented acceptance
- **RED** — any critical scenario FAIL, or FAIL after max retries

If RED: do not proceed to report. Invoke `self-heal-triage` to classify the failure root cause. Output the failure summary to the user and stop. The pipeline must be re-run after the fix — do not patch and claim GREEN without a fresh run.

Log:
```
[QA-P6-VERDICT] task_id=<task-id> verdict=GREEN|RED|YELLOW scenarios=<n> duration_ms=<n>
```

---

## Phase QA-P7 — Report and Brain Commit

Write the QA run report:

```bash
REPORT=~/forge/brain/prds/<task-id>/qa/qa-run-report-<YYYYMMDD-HHMMSS>.md
```

Before writing, capture reproducibility pins (shell or note inline):

```bash
git -C ~/forge/brain rev-parse HEAD   # brain_git_sha for manifest
# Record FORGE_TASK_ID / FORGE_PRD_TASK_ID from env if set
```

If a **previous** `qa-run-report-*.md` exists for this task and **the same scenario IDs** failed in both runs → set **`flake_suspected: true`** in YAML frontmatter below (same RED twice — likely infra flake; still record verdict RED).

If verdict **RED** and Jira MCP is configured: after **`self-heal-triage`**, optionally batch **`createJiraIssue`** per failing scenario (link keys in **Failures**). One path only — do not duplicate Slack + Jira + chat without filing IDs in this report.

```markdown
---
task_id: <task-id>
run_at: <ISO8601>
verdict: GREEN | RED | YELLOW
brain_git_sha: <git -C ~/forge/brain rev-parse HEAD>
forge_task_id_env: <FORGE_TASK_ID or empty>
flake_suspected: false | true
---

# QA Run Report

**task_id:** <task-id>
**run_at:** <ISO8601>
**verdict:** GREEN | RED | YELLOW
**duration:** <total seconds>

## Branch State

| Repo | Branch | SHA |
|---|---|---|
| backend-api | feature/payment-v2 | a1b2c3d |
| web-dashboard | feature/payment-ui | e4f5g6h |

## Environment

| Variable | Value |
|---|---|
| BASE_URL | http://localhost:3000 |
| DEVICE_ID | emulator-5554 |

## Scenario Results

| Scenario ID | Surface | Status | Duration | Notes |
|---|---|---|---|---|
| SC-AUTH-001 | web + api + db | PASS | 2.4s | |
| SC-AUTH-001-negative | web | PASS | 0.8s | |
| SC-PAYMENT-001 | web + api + db | FAIL | 5.1s | DB row not written after checkout |

## Failures (if any)

### SC-PAYMENT-001 — FAIL
- **Step:** DB verification — `SELECT * FROM orders WHERE user_id = ...`
- **Expected:** 1 row
- **Got:** 0 rows
- **Evidence:** screenshot `eval-evidence/SC-PAYMENT-001-step-4.png`
- **Classification:** functional regression — backend did not persist order on checkout

## Next Actions

- [ ] Fix: `backend-api/src/services/payment.service.ts` — order persistence missing `await`
- [ ] Re-run `/qa-run` after fix to verify GREEN
```

Commit to brain:
```bash
git -C ~/forge/brain add prds/<task-id>/qa/
git -C ~/forge/brain commit -m "qa: run report <task-id> — verdict=<GREEN|RED|YELLOW>"
```

Log:
```
[QA-P7-REPORT] task_id=<task-id> report=qa/qa-run-report-<ts>.md status=COMMITTED
```

---

## Full Pipeline Log (end state)

At completion, `qa-pipeline.log` must contain all phase gate lines in order:

```
[QA-P1-LOAD]       task_id=PRD-042 ...
[QA-P2-SCENARIOS]  task_id=PRD-042 ...
[QA-BRANCH-ENV]    task_id=PRD-042 ...
[QA-P4-STACK]      task_id=PRD-042 ...
[QA-P5-EXEC]       task_id=PRD-042 ...
[QA-P6-VERDICT]    task_id=PRD-042 verdict=GREEN
[QA-P7-REPORT]     task_id=PRD-042 ...
```

A pipeline log missing any phase line is an incomplete run. Do not report success without all lines present.

## Edge Cases

### RED verdict and immediate re-run
After a RED, if the user fixes the bug and invokes `/qa-run` again: start from QA-P3 (branch prep) not QA-P1, unless the user changed which branch to test. Use `--from=QA-P3` shorthand in the command.

### Partial surface run (`--surface web`)
All non-web scenarios get status `SKIPPED (surface filter)` in the report. Verdict only covers the requested surfaces. Report must note: "Verdict is partial — `api`, `db` surfaces not run. Re-run without `--surface` filter for full verdict."

### Remote mode (testing staging)
Skip QA-P4. In the report, note the remote BASE_URL as the test target. Record that the branch state is informational (the remote may be running a different commit than local HEAD).

### No tech plans in brain
`qa-write-scenarios` will be blocked. The pipeline logs `[QA-P2-SCENARIOS] status=BLOCKED reason=no-tech-plans`. Ask user: "Tech plans are absent. Would you like to (1) run `/plan` first, (2) provide a brief description of what to test and generate minimal scenarios from the PRD only, or (3) supply existing eval YAML manually?"
