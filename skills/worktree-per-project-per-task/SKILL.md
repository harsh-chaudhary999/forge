---
name: worktree-per-project-per-task
description: WHEN: About to start dev-implementer work on a multi-project product task. Creates fresh git worktrees for isolation, environment setup, and safe cleanup after eval passes/fails.
type: rigid
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

**Example for Node project:**

```bash
cd "$WORKTREE_PATH"
node --version
npm --version
npm ci  # Clean install from package-lock.json
npm run lint -- --fix
npm test -- --testPathPattern='^(?!.*integration)' || EXIT_BASELINE=$?
git status --porcelain
```

**Example for Python project:**

```bash
cd "$WORKTREE_PATH"
python --version
pip --version
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -x --tb=short || EXIT_BASELINE=$?
git status --porcelain
```

---

### 3. Task Execution in Worktree

**When:** Dev-implementer is building the feature.

**Pattern:**

1. Dispatch dev-implementer subagent with exact task text (D22)
2. Subagent works inside worktree at `$WORKTREE_PATH`
3. Subagent commits work to `task/<task-id>` branch
4. Subagent reports: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`

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

**For each Project:**

```bash
cd "$WORKTREE_PATH"

# Confirm on task branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "task/"* ]]; then
  echo "ERROR: Not on task branch. Aborting eval."
  exit 1
fi

# Run evaluation (project-specific: driver pattern)
./scripts/eval.sh  # or npm run eval, or make eval, or python -m pytest scenarios/
EVAL_EXIT_CODE=$?

# Capture results
echo "eval_pass: $([[ $EVAL_EXIT_CODE -eq 0 ]] && echo 'true' || echo 'false')" >> .worktree-meta
echo "eval_timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .worktree-meta

exit $EVAL_EXIT_CODE
```

**Eval result determines cleanup behavior (see step 5).**

---

### 5. Cleanup Logic (HARD-GATE)

#### 5a. If Eval Passes (EVAL_EXIT_CODE=0)

```bash
# Merge task branch back to main in the project
cd "$WORKTREE_PATH"
git checkout main  # or master
git merge --no-ff "task/${TASK_ID}" \
  -m "merge: task ${TASK_ID}

Eval: PASS
Feature: [descriptive summary from tech plan]
Projects affected: [list]
PR ready: ./scripts/pr-prep.sh will generate PR text"

# Tag worktree as "merged"
echo "status: merged" >> .worktree-meta

# Push to origin (Council coordinates PR order separately)
git push origin main

# Remove worktree (cleanup step 5c)
```

#### 5b. If Eval Fails (EVAL_EXIT_CODE!=0)

```bash
cd "$WORKTREE_PATH"

# Self-heal loop (up to 3 attempts, see Forge PLAN)
HEAL_ATTEMPT=1
while [[ $HEAL_ATTEMPT -le 3 ]]; do
  echo "Self-heal attempt $HEAL_ATTEMPT"
  
  # Dispatch self-heal subagent with failing eval output
  # Subagent diagnoses and fixes
  # Re-run eval
  
  EVAL_EXIT_CODE=$?
  [[ $EVAL_EXIT_CODE -eq 0 ]] && break
  
  HEAL_ATTEMPT=$((HEAL_ATTEMPT + 1))
done

# If still failing after 3 heals: escalate to human
if [[ $EVAL_EXIT_CODE -ne 0 ]]; then
  echo "status: eval_failed_escalate" >> .worktree-meta
  echo "self_heal_attempts: 3" >> .worktree-meta
  exit 2  # Signal: needs human intervention
fi

# If healed: continue to 5a (merge)
```

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

**Location:** `.claude/scripts/forge-worktree-cleanup.sh` (in each project)

**Purpose:** Recover from stale or orphaned worktrees.

```bash
#!/bin/bash

# forge-worktree-cleanup.sh
# Removes stale worktrees, archives metadata, audits cleanup

set -euo pipefail

PROJECT_ROOT="${1:-.}"
STALE_THRESHOLD_HOURS="${2:-24}"
VERBOSE="${3:-0}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

log() {
  [[ $VERBOSE -eq 1 ]] && echo "[$(date -u +%H:%M:%S)] $*"
}

[[ -d "$PROJECT_ROOT/.git" ]] || die "Not a git repo: $PROJECT_ROOT"

log "Scanning for stale worktrees in $PROJECT_ROOT..."

WORKTREE_DIR="${PROJECT_ROOT}/.worktrees"
[[ ! -d "$WORKTREE_DIR" ]] && log "No .worktrees directory. Exiting." && exit 0

STALE_TIMESTAMP=$(date -d "$STALE_THRESHOLD_HOURS hours ago" -u +%s)
REMOVED_COUNT=0
ARCHIVED_COUNT=0

while IFS= read -r worktree_path; do
  [[ -z "$worktree_path" ]] && continue
  
  worktree_name=$(basename "$worktree_path")
  meta_file="${worktree_path}/.worktree-meta"
  
  # Check if stale
  if [[ -f "$meta_file" ]]; then
    created_at=$(grep '^created_at:' "$meta_file" | cut -d' ' -f2- || echo "")
    if [[ -z "$created_at" ]]; then
      log "Skipping $worktree_name: no creation timestamp"
      continue
    fi
    
    created_timestamp=$(date -d "$created_at" -u +%s 2>/dev/null || echo "0")
    if [[ $created_timestamp -lt $STALE_TIMESTAMP ]]; then
      log "Marking $worktree_name as stale (age: $(( ($(date +%s) - created_timestamp) / 3600 )) hours)"
      
      # Archive
      mkdir -p "$PROJECT_ROOT/.worktree-archive"
      cp "$meta_file" "$PROJECT_ROOT/.worktree-archive/${worktree_name}.meta"
      ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
      
      # Remove
      git -C "$PROJECT_ROOT" worktree remove --force "$worktree_path" 2>/dev/null || true
      REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi
  fi
done < <(find "$WORKTREE_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)

# Log summary
{
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) — cleanup run"
  echo "  stale_threshold: ${STALE_THRESHOLD_HOURS}h"
  echo "  worktrees_removed: $REMOVED_COUNT"
  echo "  metadata_archived: $ARCHIVED_COUNT"
} >> "$PROJECT_ROOT/.worktree-archive/cleanup.log"

log "Cleanup complete: removed=$REMOVED_COUNT archived=$ARCHIVED_COUNT"
exit 0
```

**Usage:**

```bash
# From any project directory
bash .claude/scripts/forge-worktree-cleanup.sh . 24 1

# Run from forge controller
for project in $(forge config projects); do
  bash "$project/.claude/scripts/forge-worktree-cleanup.sh" "$project" 24 0
done
```

---

## Audit & Observability

### Metadata File (.worktree-meta)

Created inside each worktree, tracked through lifecycle:

```
task_id: feature-xyz-abc123
created_at: 2026-04-08T14:32:15Z
status: in_flight|merged|eval_failed_escalate|rolled_back
eval_pass: true|false
eval_timestamp: 2026-04-08T14:45:22Z
self_heal_attempts: 0|1|2|3
branch_name: task/feature-xyz-abc123
```

### Archive Directory (.worktree-archive/)

Persists metadata and cleanup logs after worktree removal:

```
.worktree-archive/
  feature-xyz-abc123-1712596335.meta     ← Metadata snapshot
  cleanup.log                             ← Cleanup audit trail
```

### Query Pattern

Find all eval failures for a task:

```bash
grep -r "eval_pass: false" .worktree-archive/ | wc -l
```

Find worktrees older than 48 hours:

```bash
find .worktrees -name ".worktree-meta" -exec \
  grep -l "created_at:" {} \; | while read f; do
    created=$(grep "created_at:" "$f" | cut -d' ' -f2-)
    created_ts=$(date -d "$created" +%s)
    if (( $(date +%s) - created_ts > 172800 )); then
      echo "$(dirname $f)"
    fi
  done
```

---

## Controller Integration

**When to invoke this skill:**

1. **Before dispatching dev-implementer** — Initialize worktrees for all affected Projects (D22: inline full task text)
2. **After eval completes** — Merge, heal, cleanup deterministically
3. **Weekly maintenance** — Run cleanup script to prune stale worktrees

**Invocation (pseudocode):**

```bash
# Controller step: init
for project in $(get_affected_projects "$TASK_ID"); do
  invoke worktree-per-project-per-task \
    --action init \
    --project "$project" \
    --task-id "$TASK_ID"
done

# Dispatch implementer
dispatch dev-implementer --task-id "$TASK_ID" --inline-full-task

# Controller step: eval
for project in $(get_affected_projects "$TASK_ID"); do
  invoke worktree-per-project-per-task \
    --action eval \
    --project "$project" \
    --task-id "$TASK_ID"
done

# Controller step: cleanup (always)
for project in $(get_affected_projects "$TASK_ID"); do
  invoke worktree-per-project-per-task \
    --action cleanup \
    --project "$project" \
    --task-id "$TASK_ID"
done
```

---

## Reference: Git Worktree Basics

For implementers unfamiliar with git worktrees:

```bash
# List all worktrees in a repo
git worktree list

# View worktree details
git worktree list --verbose

# Create worktree (used by skill, not manually)
git worktree add [--detach] <path> <branch>

# Remove worktree
git worktree remove <path>

# Prune broken worktree entries
git worktree prune
```

Worktrees are **not branches**. They are independent filesystem checkouts of the same git repo. Each worktree can be on a different branch, at a different commit, with a different working directory state. This isolation is the whole point.

---

## Troubleshooting

| Problem | Root Cause | Fix |
|---|---|---|
| "fatal: ... is already checked out" | Worktree branch already exists in another worktree | Run `git worktree prune` in project root |
| Worktree permission denied on removal | Another process holds file handle (IDE, editor) | Close all open files; retry cleanup script |
| .worktrees directory bloats to GB | Stale worktrees not cleaned up | Run `forge-worktree-cleanup.sh` with aggressive threshold |
| Eval passes but merge fails | Branch renamed or deleted before merge | Log full eval output; escalate to Self-Heal |
| Git push fails in merged worktree | Remote out of date or permission issue | Fetch, rebase before push; check SSH keys |

---

## Linked Decisions

- **D30:** Worktree per Project per task
- **D22:** Controller passes full task text inline
- **D24:** HARD-GATE tags on non-skippable steps
- **D26:** TodoWrite-required checklists on multi-step process skills
