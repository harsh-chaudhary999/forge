---
name: pr-set-coordinate
description: "WHEN: Eval has passed and branches are ready to merge across multiple repos. Raise coordinated PRs in merge order with depends-on links. HARD-GATE: Wait for each merge before raising the next."
type: rigid
requires: [brain-read, brain-write]
version: 1.0.0
preamble-tier: 3
triggers:
  - "coordinate PRs"
  - "multi-repo PR coordination"
  - "align PR set across repos"
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
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

### Step 0 — Verify Eval GREEN (HARD-GATE)

Before raising any PR, confirm eval has passed for this task:

```bash
grep '\[P4\.4-EVAL-PASS\]' ~/forge/brain/prds/<task-id>/conductor.log
```

**Expected:** At least one line matching `[P4.4-EVAL-PASS]` with the correct `task_id=`.

**If absent:** STOP. Do not raise any PR. Log to conductor:
```
[PR-BLOCKED] task_id=<id> reason=eval-not-green
```
Then invoke `forge-eval-gate` to run eval. Only return to this skill after `[P4.4-EVAL-PASS]` is logged.

**HARD-GATE: No PR is raised, no branch is pushed for merge review, until this grep returns a match.**

---

## Purpose

After eval passes and branches are ready to merge, this skill raises N coordinated PRs (one per affected project) in strict dependency order. Each PR links to the others, and the skill waits for each to merge before raising the next.

**Input:** Worktrees with passing eval, feature branches ready to merge
**Output:** All PRs merged in order, feature shipped, PR set documented in brain

---

## Context: Multi-Repo Dependency Chain

Typical Forge multi-repo product has 4 layers with strict dependencies, e.g.
`shared-schemas → backend-api → web-dashboard → app-mobile`. Merge order is fixed
by the dependency DAG: publish the upstream (no-dependency) repo first, then each
downstream after its upstream is merged. Full diagram and ordering rationale in
[`reference/examples.md`](reference/examples.md).

---

## Pattern: Coordinated PR Set (Step Spine)

Execute these phases in strict order. Full bash command bodies for every phase
live in [`reference/examples.md`](reference/examples.md); copy-ready PR body and
cross-link templates in [`reference/templates.md`](reference/templates.md).

1. **PR Creation Phase** — for each affected project, in merge order:
   - **1a.** Gather PR context inside the project worktree (project name, branch,
     commit count/hash) and fetch the shared-dev-spec from brain.
   - **1b.** Build PR title — **same title for every repo** (from shared-dev-spec).
   - **1c.** Build PR body with cross-links (Summary, Affected Project, Commits,
     Dependency Chain, Test Results, Self-Heal History, Related PRs). Template in
     [`reference/templates.md`](reference/templates.md).
   - **1d.** Create PR via `gh pr create --draft` (draft prevents accidental merge
     before dependencies); capture the PR number/URL and `brain-write` url, number,
     branch, created_at per project.

2. **PR Cross-Linking Phase** — after all PRs exist, add a "Depends-On / Blocks /
   Unblocks" comment to each PR via `gh pr comment`. Example comment in
   [`reference/templates.md`](reference/templates.md).

3. **Merge Order Enforcement Phase** — iterate the fixed `MERGE_ORDER` array.
   For every non-first project, confirm the previous project merged before
   processing it (`wait_for_merge`). Skip projects with no PR.

4. **PR Status Polling Phase** — before merging, `check_pr_ready_to_merge` (state
   OPEN, no PENDING/FAILING checks, `mergeable == MERGEABLE`, review decision OK).
   Poll with exponential backoff (30s → 5min cap), max 30 min per PR.

5. **Merge Phase** — merge in strict order, wait for each to complete. Convention:
   `gh pr merge --squash --delete-branch --auto`; verify `merged == true`, then
   `brain-write` `merged_at`.

6. **Post-Merge Validation Phase** — `validate_all_merged`: re-confirm every
   project's PR shows `merged == true` against its repo.

7. **Brain Documentation Phase** — record final state: feature name, full
   `pr_set_json` (number/url/merged_at per project), `merge_order_respected`,
   `all_checks_passed`, `completed_at`.

---

## Edge Cases, Escalation & Error Handling

Five detailed failure scenarios (circular PR references, mid-coordination merge
conflict, branch-protection violation, force-push during coordination, checks
stuck pending) — each with symptom, do-not, mitigation, and escalation class — plus
the error-handling bash snippets (PR creation fails, checks timeout, merge fails,
dependency not yet merged) live in
[`reference/edge-cases.md`](reference/edge-cases.md). The merge-strategy decision
tree (rebase vs squash vs merge commit) is in
[`reference/templates.md`](reference/templates.md).

## Invocation Pattern & Output Format

This skill is invoked by `conductor-orchestrate` after eval passes (with
`--affected-projects`, `--merge-order`, `--task-id`, `--shared-dev-spec`). The
exact invocation command and the success/failure output formats are in
[`reference/examples.md`](reference/examples.md).

---

## Linked Decisions & References

- **D22:** Controller passes full task text inline
- **D30:** Worktree per Project per task
- **D24:** HARD-GATE tags on non-skippable steps
- **Phase 5.1:** PR Set Coordinate (this skill)
- **Merge Order Pattern:** Dependency-aware serial merge (no parallelization of dependent PRs)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] PR created in every repo that has changes (no repo with commits left without a PR).
- [ ] PR title follows project's PR title convention (not "WIP" or untitled).
- [ ] PR body includes task_id and links to brain spec.
- [ ] `[P5-PR-RAISED]` logged to conductor.log after last PR created.
- [ ] All PRs point to the correct base branch (not accidentally targeting main directly).

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

Term definitions (Merge Order, Depends On, Mergeable, StatusCheckRollup,
Cross-Link, Squash) are in [`reference/templates.md`](reference/templates.md).

## Cross-References

- `pr-set-merge-order`: Called after pr-set-coordinate raises all PRs; determines safe merge sequence across repos.
- `forge-eval-gate`: Eval must pass GREEN before PRs can be raised; pr-set-coordinate is blocked if `[P4.4-EVAL-PASS]` not logged.
- `conductor-orchestrate`: Sequences `[P5-PR-RAISED]` after `[P4.3-REVIEW-PASS]`; pr-set-coordinate produces the `[P5-PR-RAISED]` markers.
- `worktree-per-project-per-task`: Produces the branches that pr-set-coordinate turns into PRs.
- `docs/conductor-log-format.md`: `[P5-PR-RAISED]` and `[PR-BLOCKED]` marker formats; `[PR-BLOCKED]` is logged when eval is not GREEN.
