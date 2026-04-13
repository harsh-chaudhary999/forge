---
name: forge-worktree-gate
description: "HARD-GATE: Every task gets fresh worktree (D30). No shared state, no cross-contamination."
type: rigid
---
# Worktree Per Task (D30 HARD-GATE)

**Rule:** Every single task gets a fresh git worktree. No exceptions.

## Anti-Pattern Preamble: Why Agents Skip Worktrees

| Rationalization | The Truth |
|---|---|
| "My change is small, I can work in main without isolation" | Small changes have large blast radius. Untracked dependencies, implicit assumptions, forgotten cleanup all hide in main. Isolation is never optional. |
| "Creating worktrees adds complexity and overhead" | Worktree creation is 2 commands. Debugging cross-contamination from main is 4 hours. The math is clear. |
| "I'll be careful not to break anything, I don't need worktrees" | Vigilance is not isolation. You can't be careful about things you don't know you're doing. Worktrees prevent accidental contamination. |
| "We already have feature branches, that's sufficient isolation" | Feature branches in main still share node_modules, build artifacts, environment state. Worktrees isolate the entire filesystem context. |
| "This task doesn't touch other projects, worktree seems unnecessary" | Tasks are not isolated to single projects. Dependency chains are invisible until isolation reveals them. Always isolate. |
| "Setting up a fresh worktree takes time we don't have" | Fresh worktree: 2 min. Debugging why test passes in main but fails in isolation: 2 hours. Time calculation is backwards. |
| "The test suite passes in my working directory, we're good to go" | Your working directory has 6 months of accumulated build artifacts. Fresh worktree has none. Tests pass there? Then it's real. |
| "We can do worktree isolation retrospectively if needed" | Retrospective isolation is impossible. Once merged, the bug is live. Isolation is pre-merge, always. |
| "One task can reuse the worktree from the previous task" | Worktree reuse means state leakage. Previous task's dependency modifications, config changes, cleanup gaps all infect next task. Fresh only. |
| "Worktrees are overkill for infrastructure or config changes" | Config changes have the most subtle bugs. Fresh environment catches config mistakes that shared main never will. |

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Agent starts editing files in the main branch directly** — Shared state contamination in progress. Stop the task, create a fresh worktree, restart from there.
- **Two tasks share the same `node_modules/` or `dist/` directory** — Worktree isolation has been broken. Both tasks are compromised. Recreate both worktrees fresh from main.
- **A task's branch is based on another task's branch (not main)** — Cross-task dependency introduced. Tasks must branch from main only. Rebase onto main or abort and re-isolate.
- **Agent says "I'll clean up after" or "I'll reset it when done"** — Cleanup-after is not isolation. The contamination already happened. Isolation must be pre-work, not post-work.
- **Multiple tasks are running in the same working directory** — One task will stomp on the other's changes. Stop both. Assign separate worktree directories and restart.
- **Worktree directory already exists with previous task artifacts** — Previous task's state is still present. Destroy and recreate fresh from main before starting.
- **A task branch was merged before all sibling tasks completed** — Remaining tasks may conflict with merged state. Rebase their worktrees onto updated main and verify no conflicts.

## Detailed Workflow

### Identify Task Scope
- **Input:** Locked shared-dev-spec (from council) + per-project tech plans
- **Action:** Break down spec into per-task work units
  - One task per distinct implementation concern (e.g., "backend auth", "web form UI", "infra deployment scripts")
  - Each task is <1 day of work (if >1 day, split further)
- **Output:** Task list with clear scope boundaries

### Create Fresh Worktree Per Task
**For each task:**

1. **Create worktree** (invoke `/worktree-per-project-per-task`)
   ```
   Creates isolated worktree:
   - Branch name: feature/TASKID (e.g., feature/D123-backend-auth)
   - Based on: main (always, not on other tasks' branches)
   - Directory: .claude/worktrees/TASKID/
   - Environment: clean slate (node_modules, build artifacts, cache all fresh)
   ```

2. **Verify isolation:**
   - Worktree has its own package-lock.json / Cargo.lock
   - No shared node_modules with other tasks
   - No shared build artifacts (.next, dist, target)
   - No shared test caches (.jest-cache, .pytest-cache)

3. **Document task context** in brain (decision ID: WKRK-YYYY-MM-DD-HH)
   - Task scope (what you will and won't implement)
   - Acceptance criteria (what "done" looks like)
   - Dependencies on other tasks (if any)
   - Worktree location and branch name

### Implement In Isolation
- **Input:** Fresh worktree
- **Action:** Implement the task
  - Write code, tests, infra as normal
  - Do NOT reach into other worktrees or main
  - Do NOT import external state (env variables from main, configs from shared directory)
  - Commit early and often (worktree is your sandbox)
- **Output:** Task complete, all tests pass in isolated environment

### Verify In Isolation
- **Input:** Completed task in worktree
- **Action:** Run verification suites
  - Unit tests (for this task's code)
  - Integration tests (for this task's service boundaries)
  - Build verification (code compiles, no warnings)
- **Output:** All tests PASS in clean worktree environment

### Coordinate Task Integration (If Multi-Task Feature)
**If feature requires multiple tasks working together:**

1. Keep each task in its own worktree (do NOT merge into main yet)
2. Coordinate task dependencies:
   - Task A (backend) → Task B (web) → Task C (app)
   - Task B waits for Task A to define API contracts
   - Task C waits for web to define cache contract
3. Use `/pr-set-coordinate` to raise coordinated PRs (in merge order)
   - PR1: Task A (backend) → main
   - PR2: Task B (web) → main (after PR1 merged)
   - PR3: Task C (app) → main (after PR2 merged)

### Merge Task (Worktree → Main)
- **Input:** Task verified, worktree tests pass, ready to merge
- **Action:** 
  1. Push worktree branch to remote
  2. Create PR (link to PR in brain decision record)
  3. Wait for spec-reviewer code review (forge-trust-code)
  4. After approval: merge to main
  5. Delete worktree branch (cleanup)

### Cleanup Worktree
- **After eval passes on main:**
  1. Invoke `/worktree-per-project-per-task` with action=cleanup
  2. Remove worktree directory (.claude/worktrees/TASKID/)
  3. Record cleanup in brain (closure to WKRK decision)

### Edge Cases & Fallback Paths

#### Case 1: Task Discovers Unexpected Dependency on Other Task
- **Symptom:** "I need to implement X, but it requires changes to Y (which isn't in this task)"
- **Do NOT:** Expand worktree scope to include Y
- **Action:**
  1. Identify minimal interface needed from Y (contract, schema, etc.)
  2. Mock or stub Y in your worktree (so you can test X in isolation)
  3. Document the dependency in brain (WKRK decision)
  4. File follow-up task for Y if not already in backlog
  5. After Y is done: remove mock, integrate real implementation
  6. Re-run tests (should pass without mock)

#### Case 2: Worktree Accumulates Stale Node Modules / Build Artifacts
- **Symptom:** "Worktree tests pass, but merge to main fails (node_modules mismatch)"
- **Do NOT:** Reuse the worktree, ignore the mismatch
- **Action:**
  1. Delete node_modules in worktree
  2. Re-run npm install / cargo update
  3. Re-run tests (if they fail now, you found the real issue)
  4. Update lock files (package-lock.json)
  5. Commit updated lock files

#### Case 3: Task Touches Multiple Projects (Cross-Project Worktree)
- **Symptom:** "Feature requires changes to backend AND web, both in separate repos"
- **Do NOT:** Create separate worktrees, manually coordinate
- **Action:**
  1. Invoke `/worktree-per-project-per-task` with multi_project=true
  2. Single worktree spans multiple project repositories
  3. Shared worktree environment (one node_modules tree, one build artifact tree)
  4. All projects in worktree tested together
  5. Coordinated PR creation across repos

#### Case 4: Previous Task Left Worktree Dirty (Uncommitted Changes)
- **Symptom:** "Worktree for feature X is still around with old changes"
- **Do NOT:** Reuse the dirty worktree
- **Action:**
  1. Check git status in worktree
  2. If changes are useful: cherry-pick to new task, delete old worktree
  3. If changes are stale: discard, delete old worktree
  4. Create fresh worktree for new task

#### Case 5: Worktree Creation Fails (Disk Full, Git Permission Error)
- **Symptom:** "Cannot create worktree, .claude/worktrees already has 50GB"
- **Do NOT:** Skip worktree, work in main
- **Action:**
  1. Investigate worktree bloat (old worktrees not cleaned up?)
  2. Delete old, unused worktrees
  3. Cleanup tool: `rm -rf .claude/worktrees/OLD_TASKID/`
  4. Retry worktree creation
  5. If space still insufficient: escalate as BLOCKED (infrastructure constraint)

#### Case 6: Service Requires Absolute Path (Cannot Work in Worktree)
- **Symptom:** "Deployment script requires /opt/myapp, won't work in .claude/worktrees"
- **Do NOT:** Move worktree to /opt/myapp
- **Action:**
  1. Identify why service requires absolute path (hardcoded config? installer?)
  2. Fix the root cause (parameterize path, use relative paths)
  3. Verify fix in worktree
  4. Then deploy from worktree

### Worktree Checklist

Before implementing, verify:

- [ ] Fresh worktree created (not reused from previous task)
- [ ] Worktree branch is based on main (not on other tasks' branches)
- [ ] Worktree directory is isolated (.claude/worktrees/TASKID/)
- [ ] node_modules / build artifacts are fresh (not shared with main)
- [ ] Task scope is bounded (not creeping)
- [ ] Dependencies documented in brain (WKRK decision)
- [ ] Task context recorded (acceptance criteria, boundaries)

During implementation:

- [ ] No modifications to main during task work (all work in worktree)
- [ ] All tests pass in isolated environment
- [ ] No shared state leakage (no importing from main)
- [ ] No cross-contamination with other tasks

After task complete:

- [ ] Worktree tests all pass
- [ ] Build verification passes
- [ ] PR created and code reviewed
- [ ] PR merged to main
- [ ] Worktree deleted (cleanup)
- [ ] Cleanup recorded in brain

## Additional Edge Cases

### Edge Case 1: Filesystem Space Exhausted (Too Many Worktrees, Disk Full)
**Situation:** Cannot create fresh worktree because disk is full or storage quota exceeded. Previous worktrees were not cleaned up.

**Example:** `.claude/worktrees/` directory is 500GB; 30 old worktrees with node_modules accumulated. Disk has <10GB free.

**Do NOT:** Work in main branch to save space. Space shortage is a real problem that must be fixed.

**Action:**
1. Diagnose: which worktrees are consuming space?
   ```bash
   du -sh .claude/worktrees/*/
   ```
2. Identify old/stale worktrees:
   - Which tasks are complete (merged to main)?
   - Which tasks are abandoned or obsolete?
   - Which worktrees have not been touched in 7+ days?
3. Cleanup stale worktrees:
   ```bash
   rm -rf .claude/worktrees/OLD_TASKID/
   ```
4. If cleanup frees enough space: create fresh worktree for current task
5. If cleanup is insufficient:
   - Escalate as **BLOCKED** (disk space insufficient)
   - Escalate to infrastructure: add more disk, implement automatic cleanup
   - Do NOT proceed with worktree creation until space is restored
6. Implement cleanup policy:
   - Auto-delete worktrees after merge + 7 days
   - Warn when disk usage > 80%
   - Prevent new worktrees when disk < 10%

---

### Edge Case 2: Git Corrupt in Parent Repo (Cannot Create Worktree)
**Situation:** Parent repository is corrupt or in bad state. Worktree creation fails because git cannot work with the repo.

**Example:** "fatal: not a git repository" or "corrupted object file" or "git index lock exists"

**Do NOT:** Skip worktree, work in main. Git corruption must be fixed.

**Action:**
1. Diagnose: is repo actually corrupt?
   ```bash
   git fsck --full
   git status
   ```
2. If index lock exists (but no git corruption):
   ```bash
   rm .git/index.lock
   git status  # should work now
   ```
3. If shallow clone is the issue:
   ```bash
   git fetch --unshallow  # convert to full clone
   ```
4. If actual corruption (broken objects):
   - This is severe. Escalate immediately: **BLOCKED** (git repo corrupted)
   - Do NOT attempt fixes (may worsen)
   - Escalate to infrastructure/DevOps to restore from backup
   - Document: what corruption was found, when, impact
5. After repair: verify repo is healthy
   ```bash
   git fsck --full  # should pass with no errors
   git log -1  # should show recent commit
   ```
6. Then create worktree normally

---

### Edge Case 3: Worktree Cleanup Fails (Stale Files, Permission Issues, Locks)
**Situation:** Worktree exists but cannot be deleted. Files are in use, permissions prevent deletion, or git locks remain.

**Example:** "Permission denied: .claude/worktrees/TASKID/" or "Cannot delete, files in use by another process" or ".git/HEAD is locked"

**Do NOT:** Leave dirty worktrees around. Accumulation of dirty worktrees blocks future work.

**Action:**
1. Identify: why won't cleanup work?
   - Files locked by running process? (kill process, wait for release)
   - Permission issue? (running as wrong user, file ownership)
   - Git lock exists? (left from interrupted operation)
   - Submodule sync incomplete?
2. If files locked:
   - Find process: `lsof +D .claude/worktrees/TASKID/`
   - Kill process: `kill <PID>`
   - Wait for file descriptors to close
   - Retry cleanup: `rm -rf .claude/worktrees/TASKID/`
3. If permission issue:
   - Check file ownership: `ls -la .claude/worktrees/TASKID/`
   - Fix ownership (if running as different user): `chown -R $USER .claude/worktrees/TASKID/`
   - Retry cleanup
4. If git lock exists:
   - Remove lock: `rm .claude/worktrees/TASKID/.git/HEAD.lock`
   - Retry cleanup
5. If cleanup still fails:
   - Force delete (use with caution): `rm -rf --force .claude/worktrees/TASKID/`
   - Document: what was forced, why, what data might be lost
6. Escalate: **NEEDS_COORDINATION** (cleanup failed, potential data loss, manual intervention required)

---

Output: **WORKTREE CREATED** (ready to implement) or **BLOCKED** (disk space full after cleanup, git repo corrupted, worktree cleanup failed)
