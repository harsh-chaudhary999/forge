---
name: pr-set-coordinate
description: "WHEN: Eval has passed and branches are ready to merge across multiple repos. Raise coordinated PRs in merge order with depends-on links. HARD-GATE: Wait for each merge before raising the next."
type: rigid
requires: [brain-read, brain-write]
---

# PR Set Coordinate — Multi-Repo Coordinated PR Management

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll merge them all at once to save time" | Parallel merges break dependency order. If the API PR merges before the DB migration PR, production breaks between merges. |
| "The PRs are independent, order doesn't matter" | If they were independent, they wouldn't be in a coordinated set. The set exists because there ARE dependencies — respect them. |
| "I'll skip the depends-on links, reviewers know the context" | Reviewers change. Context gets lost. Depends-on links are machine-readable documentation of merge order. They're not optional. |
| "One PR failed review but the others are ready" | A coordinated set ships together or not at all. Merging some PRs while one is blocked creates a partial deployment. |
| "I'll raise all PRs now and sort out order later" | Raising PRs without order invites someone to merge out of sequence. Raise in order, wait for merge, then raise the next. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EVERY PR IN A COORDINATED SET MERGES IN STRICT DEPENDENCY ORDER. NO PR IS RAISED BEFORE ITS DEPENDENCY MERGES. NO PR MERGES WITHOUT EVAL PASSING FIRST. PARTIAL DEPLOYMENT IS BROKEN DEPLOYMENT.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Multiple PRs are raised simultaneously** — Parallel PRs can be merged out of order by reviewers. STOP. Raise PRs sequentially: wait for each to merge before raising the next.
- **A PR is raised before its dependency PR is merged** — Downstream PR may be merged before the upstream PR, breaking the dependency. STOP. Confirm upstream merge before raising the downstream PR.
- **PRs do not include `depends-on` links to other PRs in the set** — Reviewers merge in whatever order they choose. STOP. Add `depends-on: <url>` to every PR description before requesting review.
- **One PR in the set fails review and the others are merged anyway** — Partial deployment creates a broken intermediate state. STOP. If any PR in the set cannot merge, halt the entire set until it is resolved.
- **Eval has not passed before PRs are raised** — PRs raised before eval passes risk merging code that will fail in production. STOP. Confirm GREEN eval verdict before raising any PR.
- **Brain is not updated with PR URLs and merge status** — Audit trail is lost. STOP. Write PR URLs, merge order, and merge timestamps to brain before considering the PR set complete.

## Purpose

After eval passes and branches are ready to merge, this skill raises N coordinated PRs (one per affected project) in strict dependency order. Each PR links to the others, and the skill waits for each to merge before raising the next.

**Input:** Worktrees with passing eval, feature branches ready to merge
**Output:** All PRs merged in order, feature shipped, PR set documented in brain

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

## Pattern: Coordinated PR Set

### 1. PR Creation Phase

**For each affected project (in merge order):**

#### 1a. Gather PR Context

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

#### 1b. Build PR Title

Title is **not unique per repo** — all PRs share the same title (from shared-dev-spec):

```
Title: [From shared-dev-spec]
Example: "feat: add 2FA with TOTP and SMS"
```

#### 1c. Build PR Body with Cross-Links

**For each PR, body includes:**

```markdown
## Summary

[Shared description from shared-dev-spec]

## Affected Project

This PR affects **shared-schemas** (or backend-api, web-dashboard, app-mobile)

## Commits

[List of commits from this project's feature branch]

## Dependency Chain

[Shows which PR(s) this one depends on]

Example for backend-api:
- ✅ Depends on: your-org/shared-schemas#42 (MUST merge first)
- → This PR: your-org/backend-api#123
- → Blocked until: your-org/web-dashboard#124

Example for web-dashboard:
- ✅ Depends on: your-org/backend-api#123 (MUST merge first)
- → This PR: your-org/web-dashboard#124

## Test Results

[Output from eval: test count, pass/fail]

## Self-Heal History

[If eval failed 1-3 times before passing, log the self-heal attempts]

## Related PRs (Cross-Linked)

- your-org/shared-schemas#42
- your-org/backend-api#123
- your-org/web-dashboard#124
- your-org/app-mobile#125

---

🤖 Generated by Forge Phase 5 (pr-set-coordinate skill)
Merge order enforced: schemas → backend → web → app
```

#### 1d. Create PR via GitHub API

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

### 2. PR Cross-Linking Phase

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

**Example: backend-api PR#123 linking comment:**

```
**Depends On:**
- ✅ your-org/shared-schemas#42

**Blocked Until:**
- your-org/shared-schemas#42 merges

**Unblocks:**
- your-org/web-dashboard#124
- your-org/app-mobile#125
```

---

### 3. Merge Order Enforcement Phase

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

### 4. PR Status Polling Phase

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

### 5. Merge Phase

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

### 6. Post-Merge Validation Phase

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

### 7. Brain Documentation Phase

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

---

## Edge Cases & Escalation Paths

### Edge Case 1: PR Merge Order Conflict — Dependency Graph Has Circular PR References

**Scenario**: During PR coordination, you discover that PR A (backend) depends on PR B (web), but PR B also depends on PR A, creating a circular dependency that violates the linear merge order.

**Symptom**: The `merge_order` array cannot be linearized. Attempting to determine which PR must merge first produces a cycle. GitHub UI shows "cannot determine merge order" or the dependency chain links form a loop.

**Do NOT**: Attempt to break the cycle by merging one PR "out of order" to resolve it. This violates the coordination principle and will cause the second PR to merge against an incomplete state.

**Mitigation**:
1. Immediately halt the PR set coordination.
2. Analyze the cyclic dependency: which two PRs form the cycle? What contracts do they share?
3. Escalate to the council with evidence (diagram the cycle, list affected contracts).
4. The council must either: (a) reorder the feature scope to eliminate the cycle, or (b) refactor the contracts to decouple the dependencies.
5. Do not resume PR merging until the council has resolved the dependency graph.

**Escalation**: NEEDS_COORDINATION (full council review required to break cycle)

---

### Edge Case 2: Merge Conflict During Coordination — PR A and PR B Modify the Same File in Incompatible Ways

**Scenario**: PR A (backend-api) modifies `/src/services/auth.ts` lines 50-80 to add new auth logic. PR B (web-dashboard) modifies the same file lines 60-90 to refactor auth integration. When PR A merges, PR B becomes unmergeable due to conflicts.

**Symptom**: After PR A merges to main, PR B shows "This branch has conflicts that must be resolved" in GitHub UI. Attempting to merge produces: `error: Your local changes to the following files would be overwritten by merge`.

**Do NOT**: Manually rebase PR B against main within the coordinator. The PR must be resolved by the task implementer (dev team), not the coordinator.

**Mitigation**:
1. Pause PR set coordination after PR A merges.
2. Notify the dev-implementer team (via brain) that PR B has conflicts requiring resolution.
3. The implementer: (a) pulls latest main into the worktree, (b) resolves merge conflicts, (c) commits the resolution, (d) forces an update to the PR branch.
4. Coordinator waits for the PR branch to become mergeable again (status check: `mergeable == MERGEABLE`).
5. Resume polling and merge PR B after conflicts resolved.

**Escalation**: NEEDS_CONTEXT (implementer must resolve the conflict; coordinator waits)

---

### Edge Case 3: Branch Protection Rule Violation — PR Cannot Merge Due to Branch Protection Requirements

**Scenario**: The target branch (main) has branch protection enabled: "Require at least 2 code reviews" and "Require status checks to pass". PR A has only 1 approval and 1 status check still pending. The coordinator polls `check_pr_ready_to_merge` and discovers these requirements are not met.

**Symptom**: `gh pr merge` command returns error: `error: required status check did not pass` or `error: required number of approvals not met`. The PR reviewDecision shows `APPROVED` but reviewers.length < 2.

**Do NOT**: Attempt to bypass branch protection by using `--force` flag or contacting administrators. Protection rules exist for a reason.

**Mitigation**:
1. Identify which protection rule is blocking: approvals, status checks, or protected branch.
2. For missing approvals: notify the PR author; request another reviewer. Coordinator waits with 30-minute polling timeout.
3. For pending status checks: poll for completion (default 30-minute wait). If checks timeout, escalate to infrastructure team.
4. For protected branch restrictions: verify the base branch is correct. If base branch is wrong, the PR must be closed and recreated with correct base.
5. Resume merge attempt once all branch protection requirements are satisfied.

**Escalation**: BLOCKED (if approvals missing) or NEEDS_INFRA_CHANGE (if status checks perpetually failing)

---

### Edge Case 4: Force Push During Coordination — Another Dev Force-Pushes to a Coordinated Branch

**Scenario**: Coordinator is waiting for PR A (backend-api) to merge. Meanwhile, another developer on the backend team runs `git push --force-with-lease origin task/feature-xyz` to update the PR branch with new commits. The branch SHA changes. The coordinator's logged PR URL and commit hash are now stale.

**Symptom**: When coordinator polls the PR status, the `merge_commit_sha` in GitHub API differs from the stored `COMMIT_HASH` in brain. The PR is still open, but the commits have changed, and the validation of "which commits are in this PR" becomes ambiguous.

**Do NOT**: Assume the force push is safe and continue with merge. Force pushes on coordinated branches can invalidate the order of changes.

**Mitigation**:
1. Detect the force push: compare current PR head commit SHA with the logged `COMMIT_HASH` from brain.
2. If SHAs differ: stop coordination immediately. Log the force push event in brain with timestamp and new SHA.
3. Notify the dev team (via brain comment) that a force push occurred and the PR needs revalidation.
4. Request the team to confirm: (a) the force push was intentional, (b) the new commits are still in merge order, (c) eval still passes on the new commits.
5. Once confirmed, update the logged `COMMIT_HASH` in brain and resume polling.

**Escalation**: NEEDS_CONTEXT (requires dev team confirmation that force push is safe)

---

### Edge Case 5: All Checks Pending After 30+ Minutes — Status Checks Stuck in "Running" State

**Scenario**: PR A (shared-schemas) has been in the coordinated set for 45 minutes. The GitHub status check rollup shows 2 of 5 checks as "PENDING". The CI pipeline appears stuck: no new logs for 20 minutes, no error messages. The 30-minute polling timeout has elapsed.

**Symptom**: `poll_for_ready` function returns failure code. `statusCheckRollup` shows: `[{name: "build", status: "PENDING"}, {name: "lint", status: "SUCCESS"}, ...]`. Neither the coordinator nor the PR author can see why the check is stuck.

**Do NOT**: Force-merge the PR or mark it as "approved anyway" to bypass the check. A stuck check may indicate a real failure.

**Mitigation**:
1. When polling timeout (30 min) is reached, do not attempt merge.
2. Log the timeout event in brain with the pending check names and timestamps.
3. Notify the infra team (via brain escalation) with the PR URL and list of stuck checks.
4. Coordinator waits for manual investigation (infra team analyzes CI pipeline, restarts runner, etc.).
5. Once infra confirms the check is resolved or determines it was a false positive, coordinator resumes polling (reset timer to 30 min).
6. If no resolution after 1 hour of waiting, escalate to BLOCKED and halt the entire PR set.

**Escalation**: NEEDS_INFRA_CHANGE (CI pipeline issue; infra team investigation required)

---

## Decision Tree: PR Merge Strategy Selection

```
┌─ ARE ALL COMMITS LOGICALLY SEPARATE AND VALUABLE?
│  ├─ YES ─→ Use REBASE MERGE
│  │  (Preserves individual commits in main history)
│  │  (Good for: schema changes, API updates, each commit is a story)
│  │
│  └─ NO ─→ IS THE FEATURE A SINGLE COHESIVE UNIT?
│     ├─ YES ─→ Use SQUASH MERGE
│     │  (Combines all commits into one; clean history)
│     │  (Good for: coordinated PR sets, multi-repo features)
│     │
│     └─ UNSURE ─→ Default: SQUASH MERGE
│        (Safer default for multi-repo coordination)
└─ EDGE CASE: Is this a hotfix or critical patch?
   └─ YES ─→ Use MERGE COMMIT (no rebase/squash)
      (Preserves exact commit SHA for traceability)
```

---

## Error Handling

### Scenario: PR Creation Fails

```bash
if ! gh pr create ...; then
  echo "ERROR: Failed to create PR for $project"
  brain-write --key "prs.${project}.error" --value "creation_failed: $(date)"
  exit 1
fi
```

### Scenario: Checks Pending > 30 Minutes

```bash
if ! poll_for_ready "$project" "$pr_num"; then
  echo "ERROR: Checks not ready after 30 min for $project PR#$pr_num"
  echo "ACTION: Check PR manually at $PR_URL"
  brain-write --key "prs.${project}.error" --value "checks_timeout: $(date)"
  exit 1
fi
```

### Scenario: Merge Fails

```bash
if ! merge_pr "$project" "$pr_num"; then
  echo "ERROR: Merge failed for $project PR#$pr_num"
  echo "ACTION: Investigate merge conflicts manually"
  brain-write --key "prs.${project}.error" --value "merge_failed: $(date)"
  exit 1
fi
```

### Scenario: Dependency PR Not Yet Merged

```bash
PREV_PROJECT=$(get_previous_in_merge_order "$project")
PREV_PR=$(brain-read --key "prs.${PREV_PROJECT}.number")

if ! is_merged "$PREV_PROJECT" "$PREV_PR"; then
  echo "ERROR: Cannot merge $project until $PREV_PROJECT#$PREV_PR merges"
  echo "ACTION: Wait for $PREV_PROJECT PR to merge, then retry"
  exit 1
fi
```

---

## Invocation Pattern

### From Conductor Orchestrate (After Eval Passes)

```bash
# Conductor calls this skill after eval-product-stack passes
invoke pr-set-coordinate \
  --affected-projects "shared-schemas,backend-api,web-dashboard,app-mobile" \
  --merge-order "shared-schemas,backend-api,web-dashboard,app-mobile" \
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

---

## Linked Decisions & References

- **D22:** Controller passes full task text inline
- **D30:** Worktree per Project per task
- **D24:** HARD-GATE tags on non-skippable steps
- **Phase 5.1:** PR Set Coordinate (this skill)
- **Merge Order Pattern:** Dependency-aware serial merge (no parallelization of dependent PRs)

## Checklist

Before claiming PR set complete:

- [ ] Eval passed (GREEN verdict) before any PR was raised
- [ ] PRs raised in strict dependency order (no parallel PR creation)
- [ ] Every PR includes `depends-on` links to upstream PRs
- [ ] Each merge confirmed complete before the next PR was raised
- [ ] No PR in the set merged while another was failing review or checks
- [ ] Brain updated with all PR URLs, merge order, and merge timestamps

---

## TodoWrite Checklist (If Merged Manually)

If manual PR merge is needed:

- [ ] Verify PR dependencies all merged before proceeding
- [ ] Confirm all checks passing (GitHub shows green checkmark)
- [ ] Review merge strategy (squash vs rebase vs merge commit)
- [ ] Delete branch after merge (cleanup)
- [ ] Verify merged commit in main branch
- [ ] Update brain with merge completion timestamp
- [ ] Check next PR in merge order is unblocked

---

## Glossary

- **Merge Order:** Sequence in which PRs must merge (fixed by dependency DAG)
- **Depends On:** PR B depends on PR A means A must merge before B
- **Mergeable:** PR has no conflicts, all checks pass, ready to merge
- **StatusCheckRollup:** GitHub's list of all status checks (CI, linting, tests, etc.)
- **Cross-Link:** Comment in PR referencing related PRs (for traceability)
- **Squash:** Merge strategy that combines all commits into one (clean history)
