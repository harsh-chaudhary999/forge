# Edge Cases, Troubleshooting & Strategy Selection

Extended edge-case deep-dives, the troubleshooting table, and the isolation
strategy decision tree. Load on demand when an anomaly is hit during the
worktree lifecycle.

## Troubleshooting

| Problem | Root Cause | Fix |
|---|---|---|
| "fatal: ... is already checked out" | Worktree branch already exists in another worktree | Run `git worktree prune` in project root |
| Worktree permission denied on removal | Another process holds file handle (IDE, editor) | Close all open files; retry cleanup script |
| .worktrees directory bloats to GB | Stale worktrees not cleaned up | Run `forge-worktree-cleanup.sh` with aggressive threshold |
| Eval passes but merge fails | Branch renamed or deleted before merge | Log full eval output; escalate to Self-Heal |
| Git push fails in merged worktree | Remote out of date or permission issue | Fetch, rebase before push; check SSH keys |

---

## Edge Cases & Escalation Paths

### Edge Case 1: Filesystem Space Exhausted During Worktree Creation — Disk Full When Cloning Repos

**Scenario**: You are attempting to create a worktree for a large multi-repo product. The first 3 projects clone successfully. While cloning the 4th project, the filesystem runs out of space (remaining < 100 MB). The `git worktree add` command fails midway, leaving a partially-cloned worktree directory on disk.

**Symptom**: `git worktree add` returns error: `fatal: could not create work tree dir ... No space left on device`. The worktree directory exists but is incomplete (.git directory is present but HEAD is unresolved, working directory is empty).

**Do NOT**: Attempt to retry the worktree creation without freeing disk space. The partial worktree will consume disk and subsequent attempts will also fail.

**Mitigation**:
1. Halt worktree creation immediately. Do not dispatch dev-implementer yet.
2. Identify the problem: `df -h` to check remaining space. If < 500 MB, escalate to infra (need cleanup of old worktrees, logs, or build artifacts).
3. List all old worktrees and archives: `find .worktrees -type d | wc -l` and `find .worktree-archive -name "*.meta" | wc -l`.
4. Run aggressive cleanup on projects: `bash .claude/scripts/forge-worktree-cleanup.sh . 0 1` (stale_threshold = 0 hours, removes everything).
5. Free additional space: `rm -rf build/ dist/ node_modules/.cache/` if safe.
6. Only after freeing > 1 GB, retry: `git worktree add` again.
7. If space still insufficient, escalate to NEEDS_INFRA_CHANGE (require storage expansion or disk migration).

**Escalation**: NEEDS_INFRA_CHANGE (requires infrastructure intervention to free/add disk space)

---

### Edge Case 2: Concurrent Worktree Creation for Same Project — Two Tasks Attempt to Create Worktree for Same Project

**Scenario**: Task A is dispatched to work on feature "add-auth". Task B is dispatched to work on feature "add-payments". Both tasks affect the backend-api project. Two conductors simultaneously invoke `worktree-per-project-per-task --action init --project backend-api`. Both attempt to create the same worktree branch `task/add-auth` and `task/add-payments` at the same time.

**Symptom**: Second `git worktree add` command fails with: `fatal: 'task/add-auth' is already checked out in '../.worktrees/add-auth-1712596335'`. The second task cannot proceed because the branch is locked by the first task's worktree.

**Do NOT**: Force-create a new worktree with a renamed branch. This violates the isolation principle and creates a hidden dependency between tasks.

**Mitigation**:
1. Detect the collision: `git worktree list | grep "task/add-auth"` before creating new worktree.
2. If collision detected, immediately halt and log the conflict in brain (decision ID: WRKTRK-COLLISION-YYYY-MM-DD-HH).
3. Determine which task has priority (execution order from conductor). The lower-priority task waits.
4. Lower-priority task retries worktree creation after higher-priority task completes (eval passes and worktree is removed).
5. Add a mutex check in the conductor: only one task can initialize worktrees for a given project at a time. Use brain-lock (advisory lock in decision tree).

**Escalation**: NEEDS_COORDINATION (conductor must sequence task execution to avoid worktree collisions)

---

### Edge Case 3: Stale Worktree Not Cleaned Up — Previous Task Crashed, Worktree Left Orphaned

**Scenario**: Task A started 48 hours ago. Dev-implementer was dispatched. During implementation, the implementer sub-agent crashed (timeout, network error, etc.). The worktree was never cleaned up. Now it sits in `.worktrees/` with status "in_flight" (never transitioned to "merged" or "eval_failed_escalate"). A new task B is about to start and wants to initialize worktrees.

**Symptom**: `git worktree list` shows an orphaned worktree that hasn't been accessed in 48+ hours. `.worktree-meta` file shows `status: in_flight` with creation timestamp from 2+ days ago. The task_id in the meta file is not on the active task list.

**Do NOT**: Assume the old worktree is dead and delete it. The original task may be retrying and the implementer may re-attach to the worktree.

**Mitigation**:
1. Detect stale worktrees: `find .worktrees -name ".worktree-meta" -type f`. For each, extract creation timestamp and compare to current time.
2. If creation timestamp > 24 hours old AND status != "merged": mark as potentially orphaned.
3. Check brain for any active task matching the task_id in the worktree. If task_id is not active, the worktree is orphaned.
4. Before removing, log the discovery in brain (decision ID: WRKTRK-ORPHAN-YYYY-MM-DD-HH) with evidence: worktree path, creation time, status, task_id.
5. Run cleanup with explicit logging: `bash .claude/scripts/forge-worktree-cleanup.sh . 24 1` (24-hour threshold, verbose output).
6. Archive the .worktree-meta file. Remove the worktree with `git worktree remove --force`.
7. Notify the original task owner (if contactable) that their worktree was cleaned up due to age.

**Escalation**: DONE_WITH_CONCERNS (orphaned worktree cleaned up; log archived for audit)

---

### Edge Case 4: Branch Divergence After Worktree Creation — Upstream Branch Changed While Worktree Exists

**Scenario**: Worktree is created from `origin/main` at commit SHA `abc123`. Dev-implementer is working on the feature branch `task/feature-xyz` inside the worktree. Meanwhile, another developer pushes a commit to `origin/main` (now at SHA `def456`). The upstream branch has diverged from the worktree's base.

**Symptom**: When dev-implementer finishes and attempts to merge `task/feature-xyz` back to main (step 5a), git finds that main has advanced (new commits from `abc123` to `def456`). The merge may have conflicts or may succeed but produce an unexpected merge commit with new upstream changes.

**Do NOT**: Ignore the divergence. Merging against a stale base means the feature hasn't been tested against recent upstream changes.

**Mitigation**:
1. Before merge, detect upstream divergence: `git log abc123..origin/main --oneline | wc -l`. If > 0, upstream has new commits.
2. If divergence detected, halt the merge and rebase the task branch: `git fetch origin && git rebase origin/main task/feature-xyz`.
3. After rebase, re-run eval in the worktree to verify the feature still passes against the new upstream base.
4. Only after eval re-passes, proceed with merge.
5. Log the divergence and rebase in brain with decision ID: WRKTRK-DIVERGENCE-YYYY-MM-DD-HH.

**Escalation**: NEEDS_CONTEXT (require implementer to rebase and re-eval against new upstream)

---

### Edge Case 5: Eval Passes but Merge Fails — Branch Renamed or Deleted Before Merge

**Scenario**: Dev-implementer finishes work. Eval passes (EVAL_EXIT_CODE=0). The cleanup logic (step 5a) attempts to merge the task branch back to main. However, the merge command fails with: `fatal: Cannot resolve 'task/feature-xyz'`. The branch was deleted or renamed before merge could occur.

**Symptom**: `git merge --no-ff task/feature-xyz` returns error: `error: pathspec 'task/feature-xyz' did not match any file(s) known to git`. The worktree-meta shows `eval_pass: true` but merge never happened.

**Do NOT**: Assume the merge is impossible. The commits from the task branch still exist somewhere and can be identified.

**Mitigation**:
1. Detect the missing branch: `git rev-parse task/feature-xyz 2>/dev/null || echo "branch not found"`.
2. If branch is missing, find the task commits: `git log origin/main..HEAD --oneline`. These are commits not yet on main.
3. Identify the task commit SHA (should be the HEAD commit before the branch rename/deletion). Use `git log --all --oneline | head -10` to find recent commits.
4. Merge the specific commit directly: `git merge --no-ff $COMMIT_SHA -m "merge: task commits for feature-xyz (branch was deleted)"`.
5. Log the recovery in brain with decision ID: WRKTRK-MERGE-RECOVERY-YYYY-MM-DD-HH.
6. Verify the merge succeeded: `git log -1 --format=%H` should show the merge commit on main.

**Escalation**: DONE_WITH_CONCERNS (merged successfully, but via recovery path; log the incident)

---

## Decision Tree: Worktree Isolation Strategy Selection

```
┌─ IS THIS A LONG-RUNNING TASK (> 2 HOURS EXPECTED DEV TIME)?
│  ├─ YES ─→ Strategy: PER-TASK ISOLATION
│  │  (One worktree per task; task owns the worktree lifecycle)
│  │  (Typical: feature development, multi-step builds)
│  │
│  └─ NO ─→ IS THIS A QUICK FIX OR HOTFIX (< 30 MIN)?
│     ├─ YES ─→ Strategy: PER-TASK ISOLATION (still recommended)
│     │  (Isolation is worth the 10-second overhead; safety > speed)
│     │
│     └─ UNSURE ─→ Default: PER-TASK ISOLATION
│        (Always isolate; the isolation principle is non-negotiable)
└─ MULTI-PROJECT SCENARIO: Does the task affect multiple projects?
   ├─ YES ─→ Strategy: PER-PROJECT-PER-TASK ISOLATION
   │  (Each project gets its own worktree, all tracked under task_id)
   │  (Enables parallel work: one implementer per project worktree)
   │
   └─ NO ─→ Use PER-TASK ISOLATION for single project
```
