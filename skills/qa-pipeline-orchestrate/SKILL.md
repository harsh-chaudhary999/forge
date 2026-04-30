---
name: qa-pipeline-orchestrate
description: "WHEN: A standalone QA run is needed against named feature branches and a target environment — independent of the full /forge delivery pipeline. Chains: brain read → semantic automation CSV + manifest → branch prep → stack-up → semantic eval exec → verdict."
type: rigid
requires: [brain-read, qa-prd-analysis, qa-semantic-csv-orchestrate, qa-branch-env-prep, eval-product-stack-up, eval-judge]
version: 1.0.19
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

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Map to the host’s **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor **`AskQuestion`**; hosts without the tool: **numbered options + stop**). See **`using-forge`** **Interactive human input**, **Multi-question elicitation**, and **Stage-local questioning**; prerequisite order: **`manual-test-cases.csv`** (or waiver) → **`qa/semantic-automation.csv`** + manifest (**`qa-semantic-csv-orchestrate`**). Dialogue norm: **`docs/forge-one-step-horizon.md`** + **`using-forge`** **Multi-question elicitation** items **4–8** (same as all **`commands/*.md`** **Assistant chat** — do not restate the full chain each message; **no defensive downstream-gate narration** mid-elicitation; question-forward; no trailing nag).

**Entry points:**
- `/qa` — full pipeline (write scenarios + branch prep + execute + judge)
- `/qa-write` — write scenarios only (stops after Step QA-P2)
- `/qa-run` — execute only (requires scenarios already in brain; starts at Step QA-P3)

**Terminology + review / process protocol (v1, this slice):**
- **Product terms:** [docs/terminology-review.md](../../docs/terminology-review.md) — **`terminology.md`** in **`~/forge/brain/prds/<task-id>/`**; use for report/assertion wording (**QA-P1** read, **QA-P7** optional `terminology_status` / `terminology_open_doubts` in `qa/qa-run-report-*.md`).
- **Checklist / “todos” in brain:** Implementation and planning **todos** live in **`tech-plans/<repo>.md` Section 2** and **`planning-doubts.md`**, not a separate ad hoc tracker — v1 per same doc; **no `task-progress.md`** unless a team process adopts it and documents it in [forge-brain-layout](../forge-brain-layout/SKILL.md).
- **Dialogue:** **`docs/forge-one-step-horizon.md`**, **`using-forge`** — do **not** use a **blocking** CSV waiver **prompt** before **`prd-locked`** + **`qa-analysis`** + **`manual-test-cases.csv`** (or waiver) exist when policy requires them.

**Entrypoint matrix** (this skill vs `/qa` / `/qa-run`): [docs/terminology-review.md](../../docs/terminology-review.md) (**§ Entrypoint matrix — commands + slice skills**).

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll skip scenario generation, I know what to test" | Untraceable tests cannot be audited. Every scenario must trace to a PRD criterion. |
| "I'll run against main instead of the feature branch" | Testing the wrong branch produces a false GREEN that masks what the feature branch actually does. |
| "Stack is probably already running, I'll skip stack-up" | Probably is not verified. Stack-up health checks are the only authoritative readiness signal. |
| "I'll run only the web surface for a full-stack feature" | A web GREEN with a broken API write is still a broken feature. Multi-surface is not optional for full-stack changes. |
| "The QA run failed but I'll fix it manually and not re-run" | A manual fix without a re-run produces no evidence. The verdict must come from an automated run, not a claim. |
| "I don't need to write results to brain — I can see them in the terminal" | Terminal output is ephemeral. Brain artifacts are auditable across sessions, teams, and CI runs. |
| "`/qa` invoked — I'll use a blocking prompt about eval/CSV waiver before checking brain" | **Violates stage-local questioning** (`using-forge`): **`prd-locked`** → **`qa-prd-analysis`** (**Step 0.5** per **`using-forge`**) → **`manual-test-cases.csv`** (or valid waiver) → **then** **`qa/semantic-automation.csv`** + manifest via **`qa-semantic-csv-orchestrate`**. Read brain **first**; surface the **first missing** artifact. |
| "I'll output **What to do next** runbook prose (intake → qa-analysis → CSV → qa-write) and end with *reply with task-id…* only — no **`AskQuestion`** / numbered list" | **Violates `using-forge` Interactive human input.** Same message must include **`AskQuestion`** or **numbered options + stop** for the **first** fork — never runbook-only. |

**If you are thinking any of the above, you are about to violate this skill.**

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] `task_id` is known and `prd-locked.md` exists in brain
- [ ] Product slug is known (resolves `product.md` and repo paths)
- [ ] Entry point is clear: `/qa` (full), `/qa-write` (scenarios only), or `/qa-run` (execute only)
- [ ] If `/qa-run`: valid **`qa/semantic-eval-manifest.json`** + **`qa/semantic-automation.csv`** per **`docs/semantic-eval-csv.md`** / **`verify_forge_task.py`**
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

- **`using-forge`** — **Stage-local questioning** (all phases): prompts must unblock **only** the current stage. **Assistant chat:** **`docs/forge-one-step-horizon.md`** (**one-step horizon**).
- **Prerequisite order** before QA-P2: **`prd-locked.md`** → **`qa-prd-analysis`** → **`manual-test-cases.csv`** or documented waiver — never invert.
- **`qa-prd-analysis`** — must run before this skill (unless reusing existing artifacts) to produce `qa/qa-analysis.md` which feeds QA-P2. Interrogation follows **`using-forge`** **Multi-question elicitation** (coverage Step 0.5 — not a one-shot Q1–Q8 wall).
- **`qa-semantic-csv-orchestrate`** — invoked at QA-P2 / QA-P5 to validate **`qa/semantic-automation.csv`**, run hosts, refresh **`semantic-eval-manifest.json`** + **`semantic-eval-run.log`** (**`docs/semantic-eval-csv.md`**).
- **`qa-branch-env-prep`** — invoked at QA-P3 to check out feature branches and write `.eval-env`.
- **`eval-product-stack-up`** — invoked at QA-P4 to start local services in dependency order.
- **`eval-judge`** — invoked at QA-P6 to render GREEN / YELLOW / RED from **`eval-judge`** § Semantic path (**manifest + run.log**) when QA-P5 ran semantic execution.
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
- **No valid `qa/semantic-eval-manifest.json`** per **`verify_forge_task.py`** **and `/qa-run` was invoked** — STOP. Ask user to run **`qa-semantic-csv-orchestrate`** / **`/qa-write`** first.
- **Branch checkout failed for any repo** — STOP. Do not run eval against a partially-checked-out product.
- **Stack health check failed in local mode** — STOP. Do not run eval against a broken stack. Report which service failed to start.
- **eval-judge returns RED and user asks to merge anyway** — STOP. RED verdict is a hard gate. Fix the failure and re-run.
- **Scenario count in brain is 0** — STOP. No scenarios = no coverage = no valid verdict. Ask user to check PRD completeness.

## Pipeline Phases

```
QA-P1: Load brain artifacts
QA-P2: Semantic automation CSV + manifest (skip if /qa-run)
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

**Before QA-P2:** If **`prd-locked.md`** missing, **BLOCK** (user runs **`/intake`**); if **`qa/qa-analysis.md`** missing or Step 0.5 **sequential interrogation** not completed in chat (**`using-forge`** **QA PRD analysis**), run **`qa-prd-analysis`** first; if CSV baseline missing and no valid waiver, **`qa-manual-test-cases-from-prd`** before authoring **`qa/semantic-automation.csv`**. Do not prompt the user about downstream waivers until upstream steps exist.

```bash
BRAIN=~/forge/brain
TASK=<task-id>
SLUG=<slug>

# Verify required artifacts exist
test -f "$BRAIN/prds/$TASK/prd-locked.md" \
  || { echo "BLOCKED: prd-locked.md not found for task $TASK"; exit 1; }

cat "$BRAIN/prds/$TASK/prd-locked.md"
cat "$BRAIN/prds/$TASK/terminology.md" 2>/dev/null
cat "$BRAIN/products/$SLUG/product.md"
ls "$BRAIN/prds/$TASK/tech-plans/" 2>/dev/null
ls "$BRAIN/prds/$TASK/qa/semantic-automation.csv" 2>/dev/null && echo "SEMANTIC CSV PRESENT"
```

**Product terminology:** If **`terminology.md`** exists, use it for **assertion / step** wording in reports and when reconciling driver output to **canonical** product labels ([docs/terminology-review.md](../../docs/terminology-review.md)). Absence does **not** block QA-P1.

Log:
```
[QA-P1-LOAD] task_id=<task-id> prd=found tech_plans=<n> existing_scenarios=<n|none>
```

---

## Phase QA-P2 — Semantic automation + manifest

**Skip this phase if:** `/qa-run` was invoked AND **`verify_forge_task.py`** already passes (**valid `qa/semantic-eval-manifest.json`** + CSV coherence when required).

**Order:** **`prd-locked`** → **`qa-analysis`** → **`manual-test-cases.csv`** — never a **blocking interactive prompt** about automation while upstream artifacts are absent.

Invoke `qa-prd-analysis` first (**sequential interactive** Step 0.5; reads PRD, maps surfaces, writes `qa/qa-analysis.md` to brain).
Complete **`qa-manual-test-cases-from-prd`** so **`qa/manual-test-cases.csv`** has ≥1 approved data row — **unless** `qa-analysis.md` frontmatter waives (see **`qa-manual-test-cases-from-prd`**).
Then invoke **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** to produce **`qa/semantic-automation.csv`**, **`semantic-eval-manifest.json`**, **`semantic-eval-run.log`** (**`docs/semantic-eval-csv.md`**). Product **unit/integration tests** come from **`forge-tdd`** driven by tech plans + CSV — not driver YAML.

**HARD-GATE:** Do not advance to QA-P3 until:
- `~/forge/brain/prds/<task-id>/qa/qa-analysis.md` exists
- **`qa/manual-test-cases.csv` baseline satisfied** (data rows **or** waiver) before treating QA-P2 as complete
- Machine-eval artifacts satisfy **`tools/verify/verify_forge_task.py`**: valid **`qa/semantic-eval-manifest.json`** (+ **`qa/semantic-automation.csv`** when **`kind: semantic-csv-eval`**)
- Optional `~/forge/brain/prds/<task-id>/qa/scenarios-manifest.md` only if your team maintains a coverage inventory

Log:
```
[QA-P2-SCENARIOS] task_id=<task-id> scenario_files=<list> total_scenarios=<n> status=WRITTEN
```

---

## Phase QA-P3 — Branch Checkout and Env Prep

Invoke `qa-branch-env-prep`. **Authoritative host-capability discovery** runs in **`qa-branch-env-prep` Step 0.0** (**`uname`**, **`which adb`**, **`emulator -list-avds`**, browser **`which`**) **before** Step 0.1 run-mode **`AskQuestion`** — so **A/B/C/D** reflect **this machine** (see that skill). If the agent skipped 0.0 and picked **`url-only`**, local **emulator / CDP** preflight may never run; **re-run QA-P3** if QA-P5 later finds the chosen mode **cannot** satisfy in-scope surfaces.

It will then prompt for a run mode using **blocking interactive prompts** per **`using-forge`** (see that skill **Step 0.1** — **`AskQuestion`** / **numbered A–D** + **stop**), not prose-only *pick a mode*:

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

**Eval host preflight (before sourcing env / invoking drivers — safety net):** Re-run / extend **surface-specific** checks per **`eval-driver-ios-xctest`** (Darwin gate), **`eval-driver-android-adb`** (ADB, KVM, AVD, **`qa/logs`**, **including AVD-on-disk-but-not-booted** → boot vs skip), **`eval-driver-web-cdp`** (browser + CDP port / Playwright MCP), **`eval-driver-api-http`** (reachability — formal driver, not curl-only; see that skill **Preflight**). **`mkdir -p ~/forge/brain/prds/<task-id>/qa/logs`** and append probes to **`eval-preflight-<ISO8601>.log`** (**`skills/forge-brain-layout/SKILL.md`**). **QA-P3 Step 0.0** already discovered OS/adb/AVD/chrome — QA-P5 **must not** be the **first** time the host is inspected; if discovery here **contradicts** the chosen **`run_mode`** (e.g. **`branch-local`** but no Chrome and web scenarios exist), **BLOCK** or return to **QA-P3** to change mode/env — **do not** silently downgrade to **curl** or **SKIP** without cause.

When a surface is **known-unrunnable** on this host (e.g. **iOS on Linux**), log **`drivers=skipped_reason=<surface>:<short_reason>`** (e.g. **`ios:host_os_not_darwin`**) — **do not** emit generic **`not_invoked`** with **no** explanation when the skip reason is **already identified**.

Load env:
```bash
set -a && source ~/forge/brain/prds/<task-id>/.eval-env && set +a
```

Invoke **`qa-semantic-csv-orchestrate`** / **`python3 tools/run_semantic_csv_eval.py`** with **`--task-id`**, **`--brain`**, and host driver settings per **`docs/semantic-eval-csv.md`**. Steps come from **`qa/semantic-automation.csv`** (**Id**, **Surface**, **Intent**, **DependsOn**); drivers are web/API/mobile/etc. per row — see **`eval-driver-***`** skills as invoked by the host runner.

**Hotfix narrow scope:** If **`qa/qa-analysis.md`** lists **`hotfix_surfaces: [api, web]`** (set during **`qa-prd-analysis`**), run only CSV rows whose **`Surface`** matches; log others as **`SKIP (hotfix scope)`**.

**HARD-GATE:** Every in-scope CSV step must be attempted or explicitly **SKIPPED** with reason (e.g. missing device). Do not silently omit rows.

Log:
```
[QA-P5-EXEC] task_id=<task-id> scenarios_run=<n> pass=<n> fail=<n> skip=<n>
```

---

## Phase QA-P6 — Verdict

**When QA-P5 ran and produced driver results:** Invoke `eval-judge` with the result payload from QA-P5.

`eval-judge` applies the judgment algorithm:
- **GREEN** — all critical scenarios PASS, no non-retried FAILs
- **YELLOW** — non-critical failures with documented acceptance
- **RED** — any critical scenario FAIL, or FAIL after max retries

**When QA-P5 did not run or produced zero driver attempts** (e.g. QA-P4 SKIP — no stack; no resolved `.eval-env` / URLs; agent session stopped after static checks): **Do not invoke `eval-judge`** for a product verdict — `eval-judge` requires driver result payloads (**Iron Law** in `skills/eval-judge/SKILL.md`). Treat this as **execution not performed**, not as YELLOW. **YELLOW** means “drivers ran and some non-critical steps failed,” not “we didn’t run automation.”

Log **one** of:
```
[QA-P6-VERDICT] task_id=<task-id> verdict=GREEN|RED|YELLOW scenarios=<n> duration_ms=<n>
[QA-P6-VERDICT] task_id=<task-id> verdict=NOT_EXECUTED reason=<no_stack|no_env|session_scope|credentials|...> static_validation=PASS|FAIL|SKIPPED
```

If RED: do not proceed to report. Invoke `self-heal-triage` to classify the failure root cause. Output the failure summary to the user and stop. The pipeline must be re-run after the fix — do not patch and claim GREEN without a fresh run.

If **NOT_EXECUTED**: proceed to QA-P7 with **`execution_scope: static_only`** — this is an **expected gap** in headless/agent sessions without stack or credentials, not a product regression.

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

**Product terminology (optional in report):** If **`~/forge/brain/prds/<task-id>/terminology.md`** exists, set YAML frontmatter **`terminology_status:`** to its frontmatter **`status`** (e.g. `draft` \| `review` \| `locked`) and optionally **`terminology_open_doubts:`** to **`none`** \| **`pending`** (or omit if unknown). Aids **DRIFT** audits when QA runs surface copy conflicts.

**Execution vs product verdict:** Use **`execution_scope: full`** when drivers ran. Use **`execution_scope: static_only`** when only YAML/schema validation (or manifest writes) occurred — set **`product_verdict: null`** and **`pipeline_verdict: NOT_EXECUTED`** (do **not** put **YELLOW** here). **`verdict`** in frontmatter may duplicate **`product_verdict`** for backward compatibility when **`execution_scope: full`**.

```markdown
---
task_id: <task-id>
run_at: <ISO8601>
execution_scope: full | static_only
product_verdict: GREEN | RED | YELLOW | null
pipeline_verdict: GREEN | RED | YELLOW | NOT_EXECUTED
verdict: GREEN | RED | YELLOW | NOT_EXECUTED
brain_git_sha: <git -C ~/forge/brain rev-parse HEAD>
forge_task_id_env: <FORGE_TASK_ID or empty>
flake_suspected: false | true
static_validation: PASS | FAIL | SKIPPED | null
# Optional — set when terminology.md exists (see Phase QA-P7 body text)
terminology_status: draft | review | locked | null
terminology_open_doubts: none | pending | null
---

# QA Run Report

**task_id:** <task-id>
**run_at:** <ISO8601>
**execution_scope:** full | static_only
**product verdict (GREEN/RED/YELLOW):** … or **N/A — drivers did not run**
**pipeline verdict:** GREEN | RED | YELLOW | **NOT_EXECUTED**
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

**When `execution_scope: static_only`** — add sections **Why automation did not run** (stack-up skipped, no env, agent session policy, etc.) and **How to get a real verdict** (bullet list: `url-only` / `branch-local` + credentials, device IDs, `/qa-run` from a machine that can reach the target). Tone: **expected limitation**, not failure.

```markdown
## Why WebDriver / Appium / ADB did not run

| Gate | Status | Meaning |
|---|---|---|
| QA-P4 | SKIP | Stack-up not executed — nothing to open in browser or on device |
| QA-P5 | SKIP | Eval drivers not invoked — no resolved env / no stack |
| QA-P6 | NOT_EXECUTED | No driver payload for `eval-judge` — **not** the same as YELLOW |

## How to obtain GREEN / RED / YELLOW

1. Provide **`BASE_URL`** (or run mode **`url-only`** / **`branch-local`**) and any **`DEVICE_ID`** / simulator IDs required by scenarios.
2. Re-run **`/qa-run <task-id>`** from an environment that can start or reach the stack.
```

Commit to brain:
```bash
git -C ~/forge/brain add prds/<task-id>/qa/
git -C ~/forge/brain commit -m "qa: run report <task-id> — verdict=<GREEN|RED|YELLOW|NOT_EXECUTED>"
```

Log:
```
[QA-P7-REPORT] task_id=<task-id> report=qa/qa-run-report-<ts>.md status=COMMITTED
```

---

## Full Pipeline Log (end state)

At completion, `qa-pipeline.log` must contain phase gate lines in order. **Full execution path** example:

```
[QA-P1-LOAD]       task_id=PRD-042 ...
[QA-P2-SCENARIOS]  task_id=PRD-042 ...
[QA-BRANCH-ENV]    task_id=PRD-042 ...
[QA-P4-STACK]      task_id=PRD-042 ...
[QA-P5-EXEC]       task_id=PRD-042 ...
[QA-P6-VERDICT]    task_id=PRD-042 verdict=GREEN
[QA-P7-REPORT]     task_id=PRD-042 ...
```

**Static-only / execution blocked** path is valid when documented: QA-P4 or QA-P5 may log **SKIP**, then **`[QA-P6-VERDICT] … verdict=NOT_EXECUTED`** — still complete if QA-P7 records **`execution_scope: static_only`** and explains the gap. Do not treat **NOT_EXECUTED** as **YELLOW**.

## Edge Cases

### RED verdict and immediate re-run
After a RED, if the user fixes the bug and invokes `/qa-run` again: start from QA-P3 (branch prep) not QA-P1, unless the user changed which branch to test. Use `--from=QA-P3` shorthand in the command.

### Partial surface run (`--surface web`)
All non-web scenarios get status `SKIPPED (surface filter)` in the report. Verdict only covers the requested surfaces. Report must note: "Verdict is partial — `api`, `db` surfaces not run. Re-run without `--surface` filter for full verdict."

### Remote mode (testing staging)
Skip QA-P4. In the report, note the remote BASE_URL as the test target. Record that the branch state is informational (the remote may be running a different commit than local HEAD).

### Static validation only (no stack, no drivers — common in agent sessions)

When the session validates **`qa/semantic-automation.csv`** and/or writes **`semantic-eval-manifest.json`** but **does not** start a stack or invoke drivers (no **`BASE_URL`**, no device, no credentials, or policy forbids long-running services):

- Label the outcome **`pipeline_verdict: NOT_EXECUTED`** and **`execution_scope: static_only`** — **not** **YELLOW**.
- **YELLOW** remains reserved for **`eval-judge`** when drivers ran and non-critical steps failed.
- The human summary should read like **“automation not run — environment gap”**, not **“partial pass.”**

### No tech plans in brain
Semantic CSV authoring needs targets from tech plans + contracts. The pipeline logs `[QA-P2-SCENARIOS] status=BLOCKED reason=no-tech-plans`. Ask user: "Tech plans are absent. Would you like to (1) run `/plan` first, (2) provide a brief description for minimal **`qa/semantic-automation.csv`** rows from the PRD only, or (3) supply **`qa/semantic-automation.csv`** + **`semantic-eval-manifest.json`** manually?"
