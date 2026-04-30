---
name: qa-branch-env-prep
description: "WHEN: About to run QA eval and need to set up the execution environment. Determines run mode: URL-only (test against live URL), branch-local (checkout + start stack + run eval drivers), branch-code-validate (checkout + run repo test suite directly), or branch-tracking (record which branch is on a remote URL). Writes runtime env config for eval drivers."
type: rigid
requires: [brain-read]
version: 1.0.7
preamble-tier: 3
triggers:
  - "checkout branches for QA"
  - "prepare test environment"
  - "set up eval branches"
  - "configure test env"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - mcp__*
---

# QA Branch and Environment Preparation

## Human input (all hosts)

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Map to the host’s **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor **`AskQuestion`**; hosts without the tool: **numbered options + stop**). Run-mode and checkout confirmations below use the same mapping. See **`using-forge`** **Interactive human input**.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

**Terminology + review / process protocol (v1, this slice):** [docs/terminology-review.md](../../docs/terminology-review.md) — **`terminology.md`** can inform **branch-env-manifest.md** and human-readable **branch labels** (product names) when you write narrated evidence; **mechanics** (checkout, **`.eval-env`**) are unchanged. **Checklists / todos** in brain: **`planning-doubts.md`** and **`tech-plans` Section 2** only for v1 (no **`task-progress.md`** unless the team documents [forge-brain-layout](../forge-brain-layout/SKILL.md)). **Entrypoint:** [terminology-review.md — matrix](../../docs/terminology-review.md) (**/qa** chain → QA-P3).

Sets up the execution environment for a QA eval run. **The first decision is always: what kind of run is this?**

| Run mode | When to use | Branch checkout? | Needs URL? |
|---|---|---|---|
| **URL-only** | Testing URL exists (staging, preview, CI deploy) — eval drivers hit it | No | Yes |
| **Branch-local** | Check out feature branches, start the stack locally, run eval drivers against it | Yes | No (localhost) |
| **Branch-code-validate** | Check out feature branches and run the repo's own test suite directly (`npm test`, `pytest`, `go test`, etc.) — no running app needed | Yes | No |
| **Branch-tracking** | Remote URL exists AND you want to record which branch is deployed there (traceability only) | No | Yes |

**Ask run mode only after Step 0.0 discovery — do not assume.** Hardware probes (`uname`, `adb`, `emulator -list-avds`, Chrome) inform Step 0.1 so **`url-only`** is not picked blindly when **branch-local** could boot an existing AVD. The user may still prefer a live URL, stack locally, or repo tests only.

**Branch-code-validate vs branch-local:** Use `branch-code-validate` when the primary goal is validating code logic via the repo's existing test suite. Use `branch-local` when the primary goal is running end-to-end eval scenarios through a running application. Both require a branch checkout.

**Scope:** Operates on repos listed in `~/forge/brain/products/<slug>/product.md`. Never modifies `product.md`, service start commands, or infra configs. Env overrides are runtime-only — they apply to eval drivers, not to running services.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll assume branch-local mode since that's the full workflow" | Assuming branch checkout when the user has a live URL wastes time and may overwrite their working tree. Always ask. |
| "I'll default url-only so we skip checkout — faster" | **Invalid** when Step 0.0 showed **adb + AVD + Chrome** and the task needs **local** driver eval — **`url-only`** never boots **`emulator`**; user must **explicitly** pick **A** after **informed** options. |
| "I'll skip branch confirmation, the user said the branch name" | Typos in branch names silently land on the wrong commit. One confirmation step prevents testing the wrong code entirely. |
| "Dirty working tree is fine, I'll just checkout" | Checking out a branch over uncommitted changes silently discards work or produces a mixed state. Always stash or abort. |
| "I'll just set env vars in my shell session" | Shell session env is invisible to subagents and CI. `.eval-env` is the durable, auditable env record. |
| "product.md lists the right repos, I don't need to re-read it" | product.md changes between PRDs. Always re-read to get the current repo list and paths. |
| "A URL was provided so I'll skip the manifest" | Even for url-only runs, the manifest records WHAT URL was tested and WHEN — this is the reproducibility trail for any verdict. |
| "The test suite passed locally so I'll skip recording the output" | Unrecorded passes are unauditable. Raw test output committed to brain is the only evidence a reviewer can independently verify. |
| "I'll guess the test command from the file extension" | Wrong test commands silently produce misleading exit codes (e.g. a missing script exits 1 for the wrong reason). Always resolve from product.md or ask — never guess. |

**If you are thinking any of the above, you are about to violate this skill.**

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] `task_id` is known and `prd-locked.md` exists in brain for it (needed for **`qa/logs`** path under **`prds/<task-id>/`**)
- [ ] Product slug is known — `product.md` must be readable **before Steps 1+** (Step **0.0–0.1** only need **`task_id`** for logging and run-mode choice)
- [ ] Branch names are provided for each repo that needs switching (or `mode: remote` is confirmed)
- [ ] Target environment is specified: `local` (start stack here) or `remote` (test existing deployment)
- [ ] You are NOT about to use production credentials — QA env only

## Pre-Implementation Checklist

Before running any `git` commands:

- [ ] product.md read and repo paths extracted
- [ ] All repo paths verified to exist on disk
- [ ] Current branch state inventoried for every in-scope repo
- [ ] Dirty state handled: stash confirmed or user instructed to discard

## Post-Implementation Checklist

Before marking this skill complete:

- [ ] All requested branches checked out and post-checkout SHA recorded
- [ ] `.eval-env` written to `brain/prds/<task-id>/.eval-env` with `chmod 600`
- [ ] `.eval-env` entry added to brain's `.gitignore`
- [ ] `branch-env-manifest.md` committed to brain (credentials redacted)
- [ ] `[QA-BRANCH-ENV]` gate line logged to `qa-pipeline.log`
- [ ] Connectivity check results noted in manifest (warnings OK in local mode)

---

## Cross-References

- **`brain-read`** — prerequisite skill that loads product.md and brain artifacts this skill depends on. When **`~/forge/brain/prds/<task-id>/terminology.md`** exists, it is the per-task product term reference for **manifest** copy and human-readable branch labels ([docs/terminology-review.md](../../docs/terminology-review.md)); optional for env prep **mechanics**.
- **`qa-pipeline-orchestrate`** — invokes this skill as phase QA-P3; the orchestrator's HARD-GATE checks for the manifest and `.eval-env` this skill produces. **Step 0.0** host discovery is the **authoritative** input so run mode matches hardware; QA-P5 driver preflight **re-checks** (**safety net**).
- **`eval-product-stack-up`** — downstream skill that reads `.eval-env` to set service environment variables before starting local services.
- **`qa-semantic-csv-orchestrate`** / host runners — execute **`qa/semantic-automation.csv`**; `.eval-env` may still resolve `{{ BASE_URL }}`, `{{ DEVICE_ID }}`, and other variables for local runs.

---

## MCP Integration

This skill may invoke MCP tools when configured:

| MCP Server | Use |
|---|---|
| Remote environment MCP (e.g. `mcp__cloud_env__get_env`) | Fetch remote staging URLs, API keys, or device IDs from a cloud environment manager rather than manual entry |
| DB MCP (`mcp__db__query`) | Verify DB connectivity by running a lightweight `SELECT 1` without requiring a local MySQL client binary |
| Secret manager MCP | Pull test credentials from a team secrets vault (e.g. HashiCorp Vault, AWS SSM) rather than receiving them in plaintext from the user |

**When to invoke secret manager MCP:** If `qa-run-config.yaml` contains `secrets_source: vault` or similar, invoke the MCP instead of prompting the user for credentials. Write the resolved values to `.eval-env` without logging them.

---

## Iron Law

```
RUN HOST HARDWARE DISCOVERY BEFORE THE RUN-MODE PROMPT (STEP 0.0) — THEN ASK RUN MODE (STEP 0.1) WITH OPTIONS THAT REFLECT WHAT THIS MACHINE ACTUALLY HAS — NEVER ASSUME OR SILENTLY DEFAULT URL-ONLY WHEN LOCAL DRIVERS ARE AVAILABLE.
ALWAYS ASK RUN MODE (URL-ONLY / BRANCH-LOCAL / BRANCH-CODE-VALIDATE / BRANCH-TRACKING) — NEVER ASSUME.
NEVER CHECKOUT A BRANCH WITHOUT EXPLICIT USER CONFIRMATION SHOWING: REPO PATH, CURRENT BRANCH, AND TARGET BRANCH.
NEVER WRITE TO product.md, docker-compose.yml, OR ANY SERVICE CONFIG — .eval-env IS THE ONLY OUTPUT FILE.
ALWAYS WRITE A MANIFEST — EVEN FOR URL-ONLY RUNS — RECORDING WHAT WAS TESTED AND WHEN.
ALWAYS RECORD THE POST-CHECKOUT GIT SHA FOR EVERY REPO (branch-local / branch-code-validate / branch-tracking).
FOR BRANCH-CODE-VALIDATE: RECORD RAW TEST OUTPUT TO BRAIN — "TESTS PASSED" IN CHAT IS NOT EVIDENCE.
```

## Red Flags — STOP

- **Branch name contains `main` or `master` and the PRD is for a feature** — STOP. Check whether the user intended to run QA against main or if the branch name is wrong.
- **Working tree is dirty in any repo** — STOP. Report dirty files. Ask user: stash, discard, or abort.
- **Branch does not exist on remote** — STOP. Do not create it. Ask user to push the branch first or confirm the correct name.
- **`.eval-env` already contains values from a prior run** — STOP. Show existing values. Confirm overwrite with user.
- **`product.md` repo paths do not exist on disk** — STOP. Cannot checkout without valid repo path. Report missing repos.
- **Remote env URL is provided but no connectivity check passes** — STOP. Log: `CONNECTIVITY FAIL: <URL> unreachable`. Ask user to verify the URL before continuing.
- **Skipping Step 0.0 host discovery and presenting generic A/B/C/D** — STOP. The run-mode choice **must** be informed by what the host can actually run (ADB, AVDs, browsers, OS). Otherwise the agent may **silently pick `url-only`** and **never** exercise **`eval-driver-*`** preflight or local emulator boot — see **Step 0.0**.

## Step 0 — Determine Run Mode (discovery first, then A–D)

### Step 0.0 — Host hardware discovery (HARD-GATE — before Step 0.1)

**Run this before** **`AskQuestion`** for run mode and **before** reading **`product.md`** for repo lists (discovery needs **no** product parse — only the shell).

1. **`mkdir -p ~/forge/brain/prds/<task-id>/qa/logs`** (see **`skills/forge-brain-layout/SKILL.md`** **qa/logs/**).
2. Append a **`--- qa-branch-env-prep Step0 ---`** section to **`eval-preflight-<ISO8601>.log`** (same filename convention as **`eval-driver-*`** preflight — one log per run is OK; use **one** timestamp for the session).
3. Run **non-destructive** probes; **tee** stdout/stderr into that log:
   - **`uname -s`** (if **not** **`Darwin`**, **iOS XCTest is not runnable on this host** — note in summary).
   - **`which adb`** ; if found: **`adb version`** (first line).
   - **`which emulator`** ; if found: **`emulator -list-avds`** (lists **offline** AVDs such as **`Pixel_10_Pro_XL`** even when **not** booted).
   - **Linux + Android in scope:** **`test -r /dev/kvm && echo kvm_readable=yes || echo kvm_readable=no`** (if **`no`**, the hardware emulator is often **slow or hangs on boot** — same class of failure as **`eval-driver-android-adb`** KVM preflight; prefer **physical device**, **remote** URL + device farm, or a host where your user is in the **`kvm`** group).
   - **Browsers:** **`which google-chrome-stable google-chrome chromium chromium-browser`** (distro-dependent); record **first hit** or **none**.
4. **Summarize in chat** (3–7 lines): OS, adb path or missing, **named AVDs** from **`emulator -list-avds`** or “none”, **KVM** (`/dev/kvm` readable or not on Linux), Chrome/Chromium path or missing, and **iOS viability** (macOS only).

This discovery **feeds QA-P3** (authoritative fit for run mode). **`qa-pipeline-orchestrate`** QA-P5 repeats / deepens checks per **`eval-driver-*`** — it is a **safety net**, not a substitute for an uninformed Step 0.1.

### Step 0.1 — Determine run mode (HARD-GATE)

**After Step 0.0**, present **A–D** via **`AskQuestion`** / **`AskUserQuestion`** or **numbered 1–4** + **stop** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — **not** generic boilerplate. **Prepend** the Step 0.0 summary so each option is **grounded**:

- State which modes are **viable on this machine** given discovery — e.g. *“**B) Branch-local** is viable: Chrome at `<path>` and AVD `<name>` exists (emulator not running yet — will boot at QA-P5 / driver preflight per **`eval-driver-android-adb`**).”*
- *“**A) URL-only** always works if you have a reachable URL; it does **not** start local emulator or Chrome CDP — use when targeting **remote** staging only.”*
- If **`uname`** is not **Darwin**, say explicitly: *“**iOS XCTest scenarios cannot run here** — use a Mac/CI for iOS or mark iOS N/A.”*
- **Do not** silently steer toward **`url-only`** when **`branch-local`** is viable and the PRD expects multi-surface eval — let the user choose with eyes open.

Template body (fill **`<DISCOVERY>`** from Step 0.0). **Do not** shorten to literal ellipsis — use the full lines below (or copy the matching row from the **Run mode** table in this skill’s intro).

```
How do you want to run these tests?

<DISCOVERY — short bullets: OS, adb/AVDs, KVM on Linux, browser, iOS note>

  A) URL-only — Target an already-running environment (staging / preview / CI deploy). You provide:
     BASE_URL, API_BASE_URL, plus any driver secrets (DB_DSN, REDIS_URL, TEST_USER_*, …) needed for eval.
     No git checkout, no local stack, no booting AVD/emulator or local Chrome CDP unless drivers point at reachable endpoints.

  B) Branch-local — Check out feature branches, bring up the product stack per product.md, then run eval drivers
     (eval-product-stack-up → qa-pipeline QA-P5). Requires branches map + runtime env (BASE_URL after stack-up,
     DEVICE_ID / IOS_SIMULATOR_ID / DB_DSN / REDIS_URL as scenarios require). Uses host resources from discovery
     (Chrome for CDP, emulator if Android in scope — see KVM note on Linux).

  C) Branch-code-validate — Check out branches and run each repo’s native test suite only (npm test, pytest,
     go test, …). No full product stack or eval-driver UI automation. Same branches map; optional test_commands
     overrides from product.md.

  D) Branch-tracking — You provide BASE_URL to the deployed stack; record which branch/SHA is live per repo
     in the branch-env manifest for traceability (optional shallow checkout for diff only — see workflow notes).
```

Record the answer as `run_mode: url-only | branch-local | branch-code-validate | branch-tracking`. (**Hotfix** is not a separate mode — use **`branch-local`** or **`branch-code-validate`** and list **`hotfix_surfaces`** in **`qa-analysis.md`** so QA-P5 runs a narrowed surface set.)

**For `url-only`:** Skip Steps 2–4. Proceed directly to Step 5 (write `.eval-env`).

**For `branch-local`:** Follow the full workflow (Steps 1–8). Then invoke `eval-product-stack-up` + `qa-semantic-csv-orchestrate` / `run_semantic_csv_eval.py`.

**For `branch-code-validate`:** Follow Steps 1–4 (checkout), then execute Step 4b (run test suite per repo). Skip Step 5 env write (no drivers needed). Proceed directly to Step 7 (manifest) and Step 8 (log gate).

**For `branch-tracking`:** Record branch refs in the manifest, skip git checkout. Proceed to Step 5.

---

## Inputs

The skill accepts a structured input — either provided inline or read from `~/forge/brain/prds/<task-id>/qa-run-config.yaml` if it exists:

```yaml
task_id: PRD-042
slug: shopapp                       # product slug — resolves repos from product.md
run_mode: url-only | branch-local | branch-code-validate | branch-tracking

# For branch-local, branch-code-validate, and branch-tracking: branch overrides per repo
branches:
  backend-api: feature/payment-v2
  web-dashboard: feature/payment-ui

# For branch-code-validate: test commands per repo (if not in product.md)
test_commands:
  backend-api: "npm test"
  web-dashboard: "npm run test:unit"
  # Fallback: if absent, read test_command from product.md Projects section for that repo

# Runtime env — injected into .eval-env for eval drivers (branch-local / url-only only)
env:
  BASE_URL: https://staging.shopapp.com
  API_BASE_URL: https://api.staging.shopapp.com
  DB_DSN: mysql://root:root@localhost:3306/shopapp_test
  REDIS_URL: redis://localhost:6379/1
  DEVICE_ID: emulator-5554
  IOS_SIMULATOR_ID: booted
  TEST_USER_EMAIL: qa@example.com
  TEST_USER_PASSWORD: qapassword123
```

**Required minimum per mode:**
- `url-only`: `task_id`, `slug`, `run_mode`, `BASE_URL`
- `branch-local`: `task_id`, `slug`, `run_mode`, at least one `branches` entry
- `branch-code-validate`: `task_id`, `slug`, `run_mode`, at least one `branches` entry (test commands from `product.md` or `test_commands` override)
- `branch-tracking`: `task_id`, `slug`, `run_mode`, `BASE_URL`, at least one `branches` entry

## Workflow

> Steps 1–4 run only in `branch-local` mode. In `url-only` and `branch-tracking` modes, skip directly to Step 5.

### Step 1 — Read product topology

```bash
BRAIN=~/forge/brain
SLUG=<slug>
cat "$BRAIN/products/$SLUG/product.md"
```

Extract all repo paths from the `Projects` section. Build a map of `project-name → repo-path`.

### Step 2 — Inventory current branch state

For every repo in the product:

```bash
for REPO in <repo-paths>; do
  echo "=== $REPO ==="
  git -C "$REPO" status -sb
  git -C "$REPO" rev-parse --abbrev-ref HEAD
  git -C "$REPO" rev-parse --short HEAD
done
```

Report the current state table to the user:

```
Repo               Current Branch         SHA       Dirty?
backend-api        main                   a1b2c3d   no
web-dashboard      develop                e4f5g6h   YES (2 modified files)
```

If any repo is dirty: **STOP**. Report which files are modified. Ask: "Stash changes, discard them, or abort the QA run?"

### Step 3 — Show the checkout plan and confirm

Build the checkout plan showing current → target for each repo in `branches`:

```
CHECKOUT PLAN
──────────────────────────────────────────────────────
Repo               Current Branch    →  Target Branch
backend-api        main              →  feature/payment-v2
web-dashboard      develop           →  feature/payment-ui
──────────────────────────────────────────────────────
Repos staying on current branch (not in branches list):
app-mobile         main              (no change)
shared-schemas     main              (no change)
```

**HARD-GATE:** Use a **blocking interactive prompt** (`AskUserQuestion` per **`allowed-tools`**; host mapping in **`using-forge`**) to confirm before any `git checkout`:

> "About to check out the branches above. Confirm to proceed, or cancel to adjust."
> Options: [ Proceed ] [ Cancel ]

Only proceed after explicit confirmation.

### Step 4 — Fetch and checkout

For each repo in the branches map:

```bash
REPO=<path>
BRANCH=<target-branch>

# Fetch from origin
git -C "$REPO" fetch origin "$BRANCH" 2>&1

# Verify branch exists on remote
git -C "$REPO" ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH" \
  || { echo "ERROR: $BRANCH not found on remote for $REPO"; exit 1; }

# Checkout
git -C "$REPO" checkout "$BRANCH" 2>&1

# Verify
ACTUAL=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
SHA=$(git -C "$REPO" rev-parse --short HEAD)
echo "✓ $REPO: $ACTUAL @ $SHA"
```

If any checkout fails: STOP. Report the failure. Do not proceed to env config with a partial checkout state.

### Step 4b — Run Test Suite (branch-code-validate mode only)

> Skip this step for all other run modes.

For each repo in the `branches` map, run the configured test command:

```bash
REPO=<path>
TEST_CMD=<test_command from product.md or test_commands override>

echo "=== Running tests in $REPO ==="
echo "Command: $TEST_CMD"
echo "Branch: $(git -C "$REPO" rev-parse --abbrev-ref HEAD) @ $(git -C "$REPO" rev-parse --short HEAD)"

# Run the test suite and capture output + exit code
cd "$REPO" && $TEST_CMD 2>&1 | tee /tmp/qa-test-output-$(basename "$REPO").txt
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "PASS: $REPO — test suite exited 0"
else
  echo "FAIL: $REPO — test suite exited $TEST_EXIT_CODE"
fi
```

**How to resolve the test command per repo:**
1. Check `test_commands` in the input config (explicit override)
2. Else read `product.md` for the repo's `test_command` field in the Projects section
3. Else detect from repo structure: `package.json` → `npm test`, `pytest.ini`/`setup.py` → `pytest`, `go.mod` → `go test ./...`, `pom.xml` → `mvn test`, `build.gradle` → `./gradlew test`
4. If still unknown: STOP. Use a **blocking interactive prompt** per **`using-forge`** — paste **`product.md`** `test_command`, pick from numbered detector guesses, or free-text **one** command — **never guess** without confirmation.

**Record results per repo:**

```
Repo               Test Command     Exit Code   Tests Run   Pass   Fail   Skip
backend-api        npm test         0           142         142    0      0
web-dashboard      npm run test:unit 1          87          80     7      0
```

If any repo exits non-zero: record as FAIL. Do not stop the entire run — run all repos first, then surface all failures at the end.

**Write raw test output to brain:**
```bash
cp /tmp/qa-test-output-<repo>.txt ~/forge/brain/prds/<task-id>/qa/test-output-<repo>-<ts>.txt
```

**HARD-GATE (branch-code-validate):** After running all repos:
- [ ] Test results table written to `branch-env-manifest.md`
- [ ] Raw test output files copied to `brain/prds/<task-id>/qa/`
- [ ] Overall result recorded: PASS (all repos 0) or FAIL (any repo non-zero) + which repos failed
- [ ] `[QA-CODE-VALIDATE]` gate line logged to `qa-pipeline.log`:

```bash
echo "[QA-CODE-VALIDATE] task_id=<task-id> repos=<n> pass=<n> fail=<n> status=<PASS|FAIL>" \
  >> ~/forge/brain/prds/<task-id>/qa-pipeline.log
```

After this step, proceed directly to Step 7 (manifest) and Step 8 (log gate). Skip Steps 5–6.

---

### Step 5 — Write `.eval-env`

Write to `~/forge/brain/prds/<task-id>/.eval-env`:

```bash
EVAL_ENV=~/forge/brain/prds/<task-id>/.eval-env

cat > "$EVAL_ENV" << 'ENVEOF'
# QA eval runtime environment
# Generated by qa-branch-env-prep — do not edit manually
# task_id: <task-id>
# generated_at: <ISO8601>

BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:4000
DB_DSN=mysql://root:root@localhost:3306/shopapp_test
REDIS_URL=redis://localhost:6379/1
DEVICE_ID=emulator-5554
IOS_SIMULATOR_ID=booted
TEST_USER_EMAIL=qa@example.com
TEST_USER_PASSWORD=qapassword123
ENVEOF

chmod 600 "$EVAL_ENV"   # credentials — restrict to owner only
```

**Security:** `.eval-env` must never be committed to brain git (contains credentials). Add to brain's `.gitignore`:

```bash
echo "prds/*/.eval-env" >> ~/forge/brain/.gitignore
git -C ~/forge/brain add .gitignore
git -C ~/forge/brain commit -m "qa: exclude .eval-env from brain git (credentials)"
```

### Step 6 — Connectivity check (remote mode or BASE_URL set)

```bash
# Check BASE_URL is reachable
curl -sf --max-time 5 "${BASE_URL}/health" > /dev/null 2>&1 \
  && echo "✓ BASE_URL reachable" \
  || echo "⚠ BASE_URL not reachable — stack may not be running yet"

# Check DB
mysql -h <host> -u <user> -p<pass> <db> -e "SELECT 1" > /dev/null 2>&1 \
  && echo "✓ DB reachable" \
  || echo "⚠ DB not reachable"
```

In `local` mode, unreachable services at this stage is expected (stack-up runs next). Log warnings but do not block.
In `remote` mode, unreachable services at this stage is a **STOP** condition.

### Step 7 — Write reproducibility manifest

```bash
cat > ~/forge/brain/prds/<task-id>/qa/branch-env-manifest.md << 'EOF'
# QA Branch & Env Manifest

**task_id:** <task-id>
**prepared_at:** <ISO8601>
**mode:** local | remote

## Repo State (post-checkout)

| Repo | Branch | SHA | Status |
|---|---|---|---|
| backend-api | feature/payment-v2 | a1b2c3d | clean |
| web-dashboard | feature/payment-ui | e4f5g6h | clean |
| app-mobile | main (unchanged) | i7j8k9l | clean |

## Env Variables Written to .eval-env

| Variable | Value |
|---|---|
| BASE_URL | http://localhost:3000 |
| API_BASE_URL | http://localhost:4000 |
| DB_DSN | mysql://root:***@localhost:3306/shopapp_test |
| DEVICE_ID | emulator-5554 |
| TEST_USER_EMAIL | qa@example.com |
| TEST_USER_PASSWORD | *** (redacted) |

## Connectivity (at prep time)

- BASE_URL: ⚠ not reachable (local mode — stack not yet started)
- DB: ⚠ not reachable (local mode)
EOF

git -C ~/forge/brain add qa/branch-env-manifest.md
git -C ~/forge/brain commit -m "qa: branch-env manifest for <task-id>"
```

### Step 8 — Log gate

```bash
echo "[QA-BRANCH-ENV] task_id=<task-id> run_mode=<url-only|branch-local|branch-code-validate|branch-tracking> repos_checked=<n|N/A> branches_switched=<n|N/A> env_vars=<n|N/A> status=READY" \
  >> ~/forge/brain/prds/<task-id>/qa-pipeline.log
```

**HARD-GATE:** Do not advance until:
- [ ] Run mode recorded in manifest
- [ ] If `branch-local` or `branch-code-validate`: all requested branches checked out and SHA recorded
- [ ] If `branch-local` or `url-only` or `branch-tracking`: `.eval-env` written with `chmod 600` and in brain `.gitignore`
- [ ] If `branch-code-validate`: `[QA-CODE-VALIDATE]` gate logged with pass/fail counts and raw output files copied to brain
- [ ] `branch-env-manifest.md` committed to brain (with `run_mode` field)
- [ ] `[QA-BRANCH-ENV]` logged to `qa-pipeline.log`

## Edge Cases

### Branch not found on remote
Ask user: "Branch `<name>` not found on remote for `<repo>`. Options: (1) Push the branch and retry, (2) Use a different branch name, (3) Skip this repo and stay on current branch."

### Repo not in branches list
Stay on current branch. Log to manifest as "unchanged". This is expected — only repos with feature branches in scope need switching.

### Remote mode with no branches provided
Valid: user is testing against an already-deployed remote stack (CI/staging). Skip Steps 2–4 entirely. Still write `.eval-env` and the manifest.

### Credentials in env
If `TEST_USER_PASSWORD`, `API_KEY`, or similar secrets are provided: confirm they are safe for the test environment. Never use production credentials. Redact all `*_PASSWORD`, `*_SECRET`, `*_KEY` values in the manifest.

### Monorepo (all services in one git repository)
When `product.md` lists multiple services that all live in the same git repo (e.g. a monorepo at a single path), treat that repo as a single checkout target. The `branches` map entry uses the monorepo path as the key. Do not attempt separate checkouts per logical service — there is only one working tree. Record the single post-checkout SHA in the manifest against all logical services that share it.
