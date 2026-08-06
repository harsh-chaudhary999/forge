# PR Set Coordinate — Worked Command Sequences

Full bash implementations and worked examples for each phase of the coordinated PR
set procedure. The operational spine lives in `../SKILL.md`; this file holds the
reference-grade command bodies.

---

## Context: Multi-Repo Dependency Chain

Typical Forge multi-repo product has 4 layers with strict dependencies:

```
shared-schemas (defines domain model)
        ↓ depends on
backend-api (implements logic against schema)
        ↓ depends on
web-dashboard (calls backend API)
        ↓ depends on
app-mobile (also calls backend API)
```

**Merge order is fixed by dependencies:**
1. **shared-schemas** — no upstream dependencies, publish first
2. **backend-api** — depends on schemas, merge after schemas published
3. **web-dashboard** — depends on backend API contracts, merge after API ready
4. **app-mobile** — depends on backend API contracts, can merge in parallel with web or after

---

## 1. PR Creation Phase

**For each affected project (in merge order):**

### 1a. Gather PR Context

```bash
# Inside project worktree (already has committed feature branch)
PROJECT_NAME="$(basename $(pwd))"
BRANCH_NAME="$(git branch --show-current)"
COMMIT_COUNT="$(git rev-list --count origin/main..$BRANCH_NAME)"
COMMIT_HASH="$(git rev-parse HEAD)"

# Fetch shared-dev-spec from brain
# (includes title, description, requirements, links to other PRs)
SPEC_TITLE=$(brain-read --key "shared-dev-spec.title")
SPEC_DESC=$(brain-read --key "shared-dev-spec.description")

# Get list of all affected projects from brain
AFFECTED_PROJECTS=$(brain-read --key "shared-dev-spec.affected_projects")
```

### 1b. Build PR Title

Title is **not unique per repo** — all PRs share the same title (from shared-dev-spec):

```
Title: [From shared-dev-spec]
Example: "feat: add 2FA with TOTP and SMS"
```

### 1c. Build PR Body with Cross-Links

See `templates.md` for the full PR body markdown template.

### 1d. Create PR via GitHub API

```bash
# Use gh CLI to create PR
gh pr create \
  --title "$SPEC_TITLE" \
  --body "$(cat <<'EOF'
$PR_BODY_MARKDOWN
EOF
)" \
  --head "$BRANCH_NAME" \
  --base "main" \
  --draft  # Create as draft to prevent accidental merge before dependencies

# Capture PR number
PR_NUMBER=$(gh pr view --json number --jq .number)
PR_URL="https://github.com/your-org/${PROJECT_NAME}/pull/${PR_NUMBER}"

# Log to brain
brain-write \
  --key "prs.${PROJECT_NAME}.url" \
  --value "$PR_URL"

brain-write \
  --key "prs.${PROJECT_NAME}.number" \
  --value "$PR_NUMBER"

brain-write \
  --key "prs.${PROJECT_NAME}.branch" \
  --value "$BRANCH_NAME"

brain-write \
  --key "prs.${PROJECT_NAME}.created_at" \
  --value "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

---

## 2. PR Cross-Linking Phase

After all PRs are created, add "Depends-On" links in PR comments.

**For each PR, add linking comment:**

```bash
for project in shared-schemas backend-api web-dashboard app-mobile; do
  PR_NUM=$(brain-read --key "prs.${project}.number")
  [[ -z "$PR_NUM" ]] && continue
  
  # Build depends-on comment
  DEPENDS_ON=$(get_dependencies_for_project "$project")
  
  if [[ ! -z "$DEPENDS_ON" ]]; then
    COMMENT="**Depends On:**
$DEPENDS_ON

**Blocks:**
[List of PRs that depend on this one]"
    
    gh pr comment "$PR_NUM" --body "$COMMENT"
  fi
done
```

The cross-link comment example lives in `templates.md`.

---

## 3. Merge Order Enforcement Phase

**Strict serial merge order (no parallelization):**

```bash
MERGE_ORDER=(
  "shared-schemas"
  "backend-api"
  "web-dashboard"
  "app-mobile"
)

for project in "${MERGE_ORDER[@]}"; do
  PR_NUM=$(brain-read --key "prs.${project}.number")
  [[ -z "$PR_NUM" ]] && continue
  
  echo "[$(date -u +%H:%M:%S)] Processing $project PR#$PR_NUM"
  
  # Skip merge-order enforcement if PR doesn't exist
  # (not all projects may be affected)
  
  # If this is not the first project, check that previous project merged
  if [[ "$project" != "shared-schemas" ]]; then
    PREV_PROJECT=$(get_previous_in_merge_order "$project")
    
    wait_for_merge "$PREV_PROJECT" || {
      echo "ERROR: Cannot merge $project until $PREV_PROJECT merges"
      exit 1
    }
  fi
done
```

---

## 4. PR Status Polling Phase

**Before attempting merge, verify:**

```bash
check_pr_ready_to_merge() {
  local project=$1
  local pr_num=$2
  
  # 1. Check PR status
  local pr_state=$(gh pr view "$pr_num" --json state --jq .state)
  if [[ "$pr_state" != "OPEN" ]]; then
    echo "PR is not open (state: $pr_state)"
    return 1
  fi
  
  # 2. Check all checks passing
  local checks=$(gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[].status')
  if [[ $(echo "$checks" | grep -ic "PENDING\|FAILING") -gt 0 ]]; then
    echo "Some checks are pending or failing"
    return 1
  fi
  
  # 3. Check for merge conflicts
  local mergeable=$(gh pr view "$pr_num" --json mergeable --jq .mergeable)
  if [[ "$mergeable" != "MERGEABLE" ]]; then
    echo "PR has merge conflicts"
    return 1
  fi
  
  # 4. Check review approvals
  local review_state=$(gh pr view "$pr_num" --json reviewDecision --jq .reviewDecision)
  if [[ "$review_state" != "APPROVED" && "$review_state" != "UNAPPROVED" ]]; then
    echo "PR needs review"
    return 1
  fi
  
  return 0
}
```

**Poll with exponential backoff (max 30 min per PR):**

```bash
poll_for_ready() {
  local project=$1
  local pr_num=$2
  local max_wait_seconds=$((30 * 60))  # 30 minutes
  local poll_interval=30  # Start at 30 seconds
  local elapsed=0
  
  while [[ $elapsed -lt $max_wait_seconds ]]; do
    if check_pr_ready_to_merge "$project" "$pr_num"; then
      echo "[$(date -u +%H:%M:%S)] PR $project#$pr_num is ready to merge"
      return 0
    fi
    
    echo "[$(date -u +%H:%M:%S)] Waiting for PR $project#$pr_num... (waited ${elapsed}s)"
    sleep "$poll_interval"
    
    # Exponential backoff: 30s → 60s → 120s → 300s (cap at 5min)
    poll_interval=$((poll_interval * 2))
    [[ $poll_interval -gt 300 ]] && poll_interval=300
    
    elapsed=$((elapsed + poll_interval))
  done
  
  echo "ERROR: PR $project#$pr_num not ready after 30 minutes"
  return 1
}
```

---

## 5. Merge Phase

**Merge in strict order, wait for each to complete:**

```bash
merge_pr() {
  local project=$1
  local pr_num=$2
  
  echo "[$(date -u +%H:%M:%S)] Merging $project PR#$pr_num"
  
  # Merge with squash (clean history) or rebase (preserve commits)
  # Convention: use squash for multi-commit features
  gh pr merge "$pr_num" \
    --squash \
    --delete-branch \
    --auto  # Merge automatically when conditions met
  
  # Wait for merge to complete
  sleep 5  # GitHub API eventual consistency
  
  # Verify merge completed
  local merged=$(gh pr view "$pr_num" --json merged --jq .merged)
  if [[ "$merged" != "true" ]]; then
    echo "ERROR: Failed to merge $project PR#$pr_num"
    return 1
  fi
  
  echo "[$(date -u +%H:%M:%S)] ✅ Merged $project PR#$pr_num"
  
  # Log merge in brain
  brain-write \
    --key "prs.${project}.merged_at" \
    --value "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  
  return 0
}
```

---

## 6. Post-Merge Validation Phase

**After all PRs merged, verify:**

```bash
validate_all_merged() {
  echo "[$(date -u +%H:%M:%S)] Validating all PRs merged"
  
  for project in shared-schemas backend-api web-dashboard app-mobile; do
    PR_NUM=$(brain-read --key "prs.${project}.number")
    [[ -z "$PR_NUM" ]] && continue
    
    local merged=$(gh pr view "$PR_NUM" --repo "your-org/$project" \
      --json merged --jq .merged)
    
    if [[ "$merged" != "true" ]]; then
      echo "ERROR: PR $project#$PR_NUM not merged"
      return 1
    fi
    
    echo "✅ $project PR#$PR_NUM merged"
  done
  
  echo "[$(date -u +%H:%M:%S)] ✅ All PRs successfully merged"
  return 0
}
```

---

## 7. Brain Documentation Phase

**After all PRs merged, record final state:**

```bash
brain-write \
  --key "completed_prs.feature_name" \
  --value "$SPEC_TITLE"

brain-write \
  --key "completed_prs.pr_set_json" \
  --value "$(cat <<'EOF'
{
  "shared-schemas": {
    "number": $PR_SCHEMAS,
    "url": "https://github.com/your-org/shared-schemas/pull/$PR_SCHEMAS",
    "merged_at": "2026-04-10T14:22:15Z"
  },
  "backend-api": {
    "number": $PR_BACKEND,
    "url": "https://github.com/your-org/backend-api/pull/$PR_BACKEND",
    "merged_at": "2026-04-10T14:23:30Z"
  },
  "web-dashboard": {
    "number": $PR_WEB,
    "url": "https://github.com/your-org/web-dashboard/pull/$PR_WEB",
    "merged_at": "2026-04-10T14:24:45Z"
  },
  "app-mobile": {
    "number": $PR_APP,
    "url": "https://github.com/your-org/app-mobile/pull/$PR_APP",
    "merged_at": "2026-04-10T14:25:50Z"
  }
}
EOF
)"

brain-write \
  --key "completed_prs.merge_order_respected" \
  --value "true"

brain-write \
  --key "completed_prs.all_checks_passed" \
  --value "true"

brain-write \
  --key "completed_prs.completed_at" \
  --value "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

---

## Invocation Pattern

### From Conductor Orchestrate (After Eval Passes)

`--merge-order` comes from `pr-set-merge-order`'s brain-write key `merge_order.sequence` — a **space**-separated
sequence (that skill's own `echo "${sorted[@]}"`), not comma-separated. The comma-joined form below is illustrative
only; read the actual value rather than hardcoding a delimiter:

```bash
# Conductor calls this skill after eval-product-stack passes AND pr-set-merge-order has run
MERGE_ORDER_RAW="$(brain-read --key merge_order.sequence)"  # space-separated, from pr-set-merge-order
invoke pr-set-coordinate \
  --affected-projects "shared-schemas,backend-api,web-dashboard,app-mobile" \
  --merge-order "$MERGE_ORDER_RAW" \
  --task-id "feature-xyz-abc123" \
  --shared-dev-spec "$(brain-read --key shared-dev-spec)"
```

### Output Format

On success:
```
✅ DONE

PR Set Summary:
- shared-schemas#42 merged at 2026-04-10T14:22:15Z
- backend-api#123 merged at 2026-04-10T14:23:30Z
- web-dashboard#124 merged at 2026-04-10T14:24:45Z
- app-mobile#125 merged at 2026-04-10T14:25:50Z

All PRs merged. Feature ready for deployment.
```

On failure:
```
ERROR

Failed PR:
- backend-api#123: merge_failed (conflicts with main)

Action: Resolve conflicts manually, then retry merge
```
