# Worktree Examples — Worked Command Sequences

Full worked command sequences for each lifecycle step. The SKILL.md spine
references these; load on demand when you need the exact commands.

## Step 2 — Dev-Implementer Environment Setup Examples

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

## Step 4 — Eval Run in Worktree (full script)

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

## Step 5a — If Eval Passes (EVAL_EXIT_CODE=0)

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

---

## Step 5b — If Eval Fails (EVAL_EXIT_CODE!=0)

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
