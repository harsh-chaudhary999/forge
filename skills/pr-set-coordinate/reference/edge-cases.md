# PR Set Coordinate — Edge Cases, Escalation Paths & Error Handling

Detailed failure scenarios with symptom, do-not, mitigation, and escalation
classification, plus the error-handling bash snippets for each failure mode.
The operational spine lives in `../SKILL.md`.

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
