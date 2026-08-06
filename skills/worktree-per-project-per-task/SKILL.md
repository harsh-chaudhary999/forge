---
name: worktree-per-project-per-task
description: "WHEN: About to start dev-implementer work on a multi-project product task. Creates fresh git worktrees for isolation, environment setup, and safe cleanup after eval passes/fails."
type: rigid
version: 1.0.0
preamble-tier: 2
triggers:
  - "create worktree"
  - "set up worktree per project"
  - "worktree for this task"
allowed-tools:
  - Bash
  - Write
---

# Worktree Per Project Per Task

**Decision D30 Implementation:** Every dev task gets a fresh worktree in each affected Project. Nothing merges until eval is green.

## Anti-Pattern Preamble

| Rationalization | Reality |
|---|---|
| "I'll just work in the main branch, it's faster" | Contaminates the original branch; eval can't run clean; merge is risky |
| "Worktrees are overkill for small changes" | Worktrees enforce isolation, enable parallel work, and guarantee clean rollback |
| "Cleanup later is fine" | Stale worktrees waste disk; cleanup must be deterministic and automated |
| "One worktree per repo is enough" | A single task spans multiple projects; each needs its own isolated branch |

## Iron Law

```
EVERY DEV-IMPLEMENTER TASK RUNS IN A FRESH WORKTREE BASED ON MAIN. NO TASK SHARES A WORKTREE WITH ANOTHER. NO TASK STARTS BEFORE ITS WORKTREE IS CREATED AND VERIFIED.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Code changes are being made in the main branch of any project repo** — Main branch contamination means rollback requires reverting shared history. STOP. Create a worktree first. No exceptions even for "one-line" changes.
- **Two tasks share the same worktree directory** — Shared worktrees create dependency between unrelated tasks: one task's uncommitted changes become visible to the other's eval. STOP. Each task gets its own isolated worktree path.
- **Worktree is created from a non-main base branch** — Basing a task branch on another feature branch creates hidden dependency; if that branch changes or fails, this task inherits the problem. STOP. Always base from the latest `main`/`master` before creating a worktree.
- **`npm install` / `bundle install` / dependency install is shared across worktrees via symlink or cached path** — Shared node_modules between worktrees means a dependency install in one task can break another task mid-eval. STOP. Each worktree must have its own installed dependencies.
- **Worktree cleanup is skipped after eval fails** — Stale worktrees from failed tasks accumulate and fill disk, and may be mistakenly reused. STOP. Run cleanup regardless of eval outcome — cleanup is unconditional.
- **Conductor dispatches a dev-implementer before worktrees are initialized** — Implementer working without a worktree will work directly in main. STOP. Worktrees must be created and verified before any dev-implementer sub-agent is dispatched.

---

## The Pattern

### 1. Pre-Task Worktree Initialization (HARD-GATE)

**When:** Before dispatching dev-implementer, before ANY code changes.

**For each affected Project:**

```bash
# Set variables
PROJECT_ROOT="/path/to/project"
TASK_ID="feature-xyz-abc123"
WORKTREE_NAME="${TASK_ID}-$(date +%s)"
WORKTREE_PATH="${PROJECT_ROOT}/.worktrees/${WORKTREE_NAME}"

# Create fresh worktree from current HEAD of main/master
cd "$PROJECT_ROOT"
git worktree add \
  --detach \
  "$WORKTREE_PATH" \
  "origin/main"

# Create task-specific branch inside worktree
cd "$WORKTREE_PATH"
git checkout -b "task/${TASK_ID}"

# Mark worktree as "in flight"
echo "task_id: ${TASK_ID}" > .worktree-meta
echo "created_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .worktree-meta
echo "status: in_flight" >> .worktree-meta
```

**Output:** Fresh worktree isolated at `.worktrees/<task-id>-<timestamp>/` on branch `task/<task-id>`, ready for dev work.

---

### 2. Dev-Implementer Environment Setup (HARD-GATE)

**When:** Inside the worktree, before running any build/test commands.

**Checklist (TodoWrite-required):**

- [ ] Verify worktree is on correct task branch: `git branch -v`
- [ ] Install/reinstall dependencies (exact commands per project type)
- [ ] Run linters with --fix if applicable
- [ ] Run test suite baseline (capture exit code)
- [ ] Confirm no uncommitted state from prior runs: `git status` is clean
- [ ] Log environment: Node version, Python version, language version, key tool versions

Worked per-language env-setup command sequences (Node `npm ci`/lint/test, Python venv/`pip`/`pytest`) live in **`reference/examples.md`**.

---

### 3. Task Execution in Worktree

**When:** Dev-implementer is building the feature.

**Pattern:**

1. Dispatch dev-implementer subagent with exact task text (D22)
2. Subagent works inside worktree at `$WORKTREE_PATH`
3. Subagent commits work to `task/<task-id>` branch
4. Subagent reports: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`

**Next step after worktree is verified:**
Before dispatching dev-implementer, invoke `forge-tdd` to write RED (failing) tests inside the worktree. Implementation (GREEN code) follows only after RED tests are observed failing and logged. The sequence is:
1. Worktree created and verified (`git worktree list` confirms task branch) ← you are here
2. `forge-tdd` RED phase: write failing tests, confirm they fail
3. dev-implementer: write minimal code to make tests GREEN
4. `forge-tdd` GREEN verification: confirm tests pass
Never dispatch dev-implementer to write implementation code without a prior RED phase in the same worktree.

**Subagent must NOT:**
- Merge into main/master
- Push to origin
- Run system-wide installs (use worktree-local tooling)

**Subagent MUST:**
- Commit every logical change
- Leave worktree clean for eval
- Report test results (pass/fail counts)

---

### 4. Eval Run in Worktree (HARD-GATE)

**When:** After dev-implementer finishes (DONE or DONE_WITH_CONCERNS).

**For each Project:** confirm you are on the `task/*` branch (abort eval if not), run the project-specific eval driver, then append `eval_pass` and `eval_timestamp` to `.worktree-meta` and exit with `$EVAL_EXIT_CODE`. The full eval script lives in **`reference/examples.md`**.

**Eval result determines cleanup behavior (see step 5).**

---

### 5. Cleanup Logic (HARD-GATE)

#### 5a. If Eval Passes (EVAL_EXIT_CODE=0)

Checkout main, `git merge --no-ff "task/${TASK_ID}"` with an `Eval: PASS` commit message, set `status: merged` in `.worktree-meta`, `git push origin main` (Council coordinates PR order separately), then proceed to removal (5c). Full merge script in **`reference/examples.md`**.

#### 5b. If Eval Fails (EVAL_EXIT_CODE!=0)

Run the self-heal loop (max 3 attempts: dispatch self-heal subagent with failing eval output → re-run eval → break on pass). If still failing after 3 heals, write `status: eval_failed_escalate` + `self_heal_attempts: 3` to `.worktree-meta` and `exit 2` (needs human intervention). If healed, continue to 5a (merge). Full self-heal loop script in **`reference/examples.md`**.

#### 5c. Worktree Removal

**Always runs (PASS or FAIL after heal):**

```bash
cd /  # Exit worktree before removing

# Preserve .worktree-meta for audit
PROJECT_ROOT="/path/to/project"
WORKTREE_PATH="${PROJECT_ROOT}/.worktrees/${WORKTREE_NAME}"

# Archive metadata
mkdir -p "$PROJECT_ROOT/.worktree-archive"
cp "${WORKTREE_PATH}/.worktree-meta" \
   "$PROJECT_ROOT/.worktree-archive/${WORKTREE_NAME}.meta"

# Remove worktree
git -C "$PROJECT_ROOT" worktree remove --force "$WORKTREE_PATH"
git -C "$PROJECT_ROOT" branch -D "task/${TASK_ID}"  # Local branch cleanup

# Log removal
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) — worktree $WORKTREE_NAME removed" \
  >> "$PROJECT_ROOT/.worktree-archive/cleanup.log"
```

---

## Cleanup Script

The standalone recovery script **`.claude/scripts/forge-worktree-cleanup.sh`** (in each project) — which removes stale worktrees, archives metadata, and audits cleanup — plus its usage examples live in **`reference/examples.md`**.

---

## Audit & Observability

Worktree lifecycle state is tracked in a per-worktree `.worktree-meta` file (`task_id`, `created_at`, `status`, `eval_pass`, `eval_timestamp`, `self_heal_attempts`, `branch_name`) and persisted after removal in `.worktree-archive/`. The metadata-file schema, archive-directory layout, and query patterns (find eval failures, find worktrees older than 48h) live in **`reference/audit.md`**.

---

## Controller Integration

This skill is invoked **before dispatching dev-implementer** (init worktrees for all affected Projects, D22), **after eval completes** (merge/heal/cleanup deterministically), and **weekly** (prune stale worktrees). The full controller invocation pseudocode (init → dispatch → eval → cleanup loops) and the **Git Worktree Basics** primer (`git worktree list`/`add`/`remove`/`prune`; worktrees are independent filesystem checkouts, not branches) live in **`reference/examples.md`**.

---

## Edge Cases, Troubleshooting & Strategy Selection

The troubleshooting table (already-checked-out, permission-denied removal, `.worktrees` bloat, merge-fail-after-pass, push-fail), the five edge-case deep-dives (disk-full mid-clone → NEEDS_INFRA_CHANGE; concurrent same-project create → NEEDS_COORDINATION; orphaned stale worktree → DONE_WITH_CONCERNS; upstream branch divergence → NEEDS_CONTEXT; eval-passes-but-merge-fails → DONE_WITH_CONCERNS), and the **Worktree Isolation Strategy Selection** decision tree all live in **`reference/edge-cases.md`**.

---

## Linked Decisions

- **D30:** Worktree per Project per task
- **D22:** Controller passes full task text inline
- **D24:** HARD-GATE tags on non-skippable steps
- **D26:** TodoWrite-required checklists on multi-step process skills

## Post-Implementation Checklist

- [ ] Worktree created with branch name `task/<task-id>` (task-id scoped, not generic).
- [ ] `git worktree list` confirms the new worktree is isolated from main.
- [ ] Implementation ran inside the worktree (not in the main working directory).
- [ ] Worktree branch pushed to remote before PR creation.
- [ ] Worktree marked for pruning after PR merged (not left dangling).

## Checklist

Before dispatching dev-implementer to any project:

- [ ] Fresh worktree created for every affected project (not reused from prior task)
- [ ] Each worktree branched from `main`/`master` (not from another feature branch)
- [ ] Worktree paths are unique per task — no two tasks share a directory
- [ ] Dependencies installed in each worktree independently (no shared node_modules)
- [ ] Cleanup plan confirmed: worktree deleted unconditionally after eval passes or task fails
- [ ] Dev-implementer dispatched only after worktrees are verified (not before)

## Cross-References

- `conductor-orchestrate`: Calls worktree-per-project-per-task before dispatching dev-implementer; worktrees must be verified before `[P4.1-DISPATCH]`.
- `forge-tdd`: Runs inside the worktree created by this skill; TDD RED phase is confirmed in the isolated branch.
- `tech-plan-write-per-project`: Produces per-repo plans that determine which repos need worktrees.
- `pr-set-coordinate`: Creates PRs from the branches produced by this skill after eval passes.
- `docs/conductor-log-format.md`: `[P4.1-WORKTREE-FAIL]` marker — logged when worktree creation fails; includes `repos_affected` and `reason`.
