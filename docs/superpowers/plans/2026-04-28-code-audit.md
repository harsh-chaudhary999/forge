# Forge Codebase Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit all three Forge runtime surfaces (CJS hooks, Python tools, Markdown skills/commands/agents), produce severity-tagged findings per file, and synthesize a Forge-ready `prd-locked.md` that feeds directly into the intake → council → build → eval pipeline.

**Architecture:** Three parallel subagents each audit one surface and write a findings file to `~/forge/brain/prds/audit-2026-04-28/`. A synthesis pass in the main session reads all three, deduplicates, assigns IDs, and writes the final `audit-report.md` and `prd-locked.md`. The conductor log entry gates handoff to council.

**Tech Stack:** Claude Code subagents (Explore type), Bash for verification, Markdown for all outputs. No new source files — outputs are brain files only.

---

## File Map

| File | Role |
|---|---|
| `~/forge/brain/prds/audit-2026-04-28/surface-hooks.md` | Per-file findings for `.claude/hooks/*.cjs` (created by Task 2) |
| `~/forge/brain/prds/audit-2026-04-28/surface-tools.md` | Per-file findings for `tools/*.py` (created by Task 3) |
| `~/forge/brain/prds/audit-2026-04-28/surface-skills.md` | Per-file findings for `skills/`, `commands/`, `agents/` (created by Task 4) |
| `~/forge/brain/prds/audit-2026-04-28/audit-report.md` | Merged, deduplicated, severity-sorted findings (created by Task 5) |
| `~/forge/brain/prds/audit-2026-04-28/prd-locked.md` | Forge PRD ready for forge-intake-gate (created by Task 6) |
| `~/forge/brain/prds/audit-2026-04-28/conductor.log` | Gate checkpoint log (created by Task 7) |

---

## Task 1: Create Brain Directory

**Files:**
- Create: `~/forge/brain/prds/audit-2026-04-28/` (directory)

- [ ] **Step 1.1: Create the brain directory**

```bash
mkdir -p ~/forge/brain/prds/audit-2026-04-28
```

Expected: no output, exit 0.

- [ ] **Step 1.2: Verify**

```bash
ls ~/forge/brain/prds/audit-2026-04-28/
```

Expected: empty directory listing (no error).

- [ ] **Step 1.3: Commit checkpoint**

```bash
touch ~/forge/brain/prds/audit-2026-04-28/.gitkeep
```

No git commit needed — brain is not tracked. Continue to Tasks 2, 3, 4 (run in parallel).

---

## Task 2: Audit Surface 1 — CJS Hooks

> **Run in parallel with Tasks 3 and 4.**

**Files:**
- Read: `.claude/hooks/commit-msg.cjs`, `forge-install-hooks.cjs`, `forge-stage-detect.cjs`, `forge-worktree-cleanup.cjs`, `post-commit.cjs`, `post-merge.cjs`, `post-pr-dreamer.cjs`, `post-rewrite.cjs`, `pre-commit.cjs`, `pre-merge.cjs`, `pre-tool-use.cjs`, `prompt-submit.cjs`, `session-start.cjs`, `test-forge-stage-detect.cjs`
- Create: `~/forge/brain/prds/audit-2026-04-28/surface-hooks.md`

- [ ] **Step 2.1: Dispatch hooks audit subagent**

Dispatch a `general-purpose` subagent with this exact prompt:

```
You are a senior security auditor and software architect.

Audit all 14 CJS hook scripts in /home/lordvoldemort/Documents/forge/.claude/hooks/. Read every file. For each file produce a section using EXACTLY this format:

---
FILE: <basename>
LINES: <line count>

PURPOSE:
- <what this hook is responsible for>

KEY LOGIC:
- <core functionality, decision branches, side effects>

ISSUES:
[SEVERITY] description — file:line
(list every issue found; if none, write "None identified")

SECURITY RISKS:
[SEVERITY] description — file:line
(focus on: command injection, path traversal, unsafe eval/exec, unvalidated env vars, privilege escalation, secrets in logs)

PERFORMANCE CONCERNS:
[SEVERITY] description — file:line

MAINTAINABILITY PROBLEMS:
[SEVERITY] description — file:line

IMPROVEMENTS:
- Actionable fix for each issue above (reference the issue by file:line)
---

Severity tags: [CRITICAL], [HIGH], [MEDIUM], [LOW]

Files to audit (read all of them before writing any output):
1. /home/lordvoldemort/Documents/forge/.claude/hooks/session-start.cjs
2. /home/lordvoldemort/Documents/forge/.claude/hooks/pre-tool-use.cjs
3. /home/lordvoldemort/Documents/forge/.claude/hooks/post-commit.cjs
4. /home/lordvoldemort/Documents/forge/.claude/hooks/forge-install-hooks.cjs
5. /home/lordvoldemort/Documents/forge/.claude/hooks/post-merge.cjs
6. /home/lordvoldemort/Documents/forge/.claude/hooks/post-pr-dreamer.cjs
7. /home/lordvoldemort/Documents/forge/.claude/hooks/pre-commit.cjs
8. /home/lordvoldemort/Documents/forge/.claude/hooks/pre-merge.cjs
9. /home/lordvoldemort/Documents/forge/.claude/hooks/prompt-submit.cjs
10. /home/lordvoldemort/Documents/forge/.claude/hooks/post-rewrite.cjs
11. /home/lordvoldemort/Documents/forge/.claude/hooks/commit-msg.cjs
12. /home/lordvoldemort/Documents/forge/.claude/hooks/forge-worktree-cleanup.cjs
13. /home/lordvoldemort/Documents/forge/.claude/hooks/forge-stage-detect.cjs
14. /home/lordvoldemort/Documents/forge/.claude/hooks/test-forge-stage-detect.cjs

After auditing all 14 files, write the complete findings to:
/home/lordvoldemort/forge/brain/prds/audit-2026-04-28/surface-hooks.md

The file must start with:
# Surface Audit: CJS Hooks
Date: 2026-04-28
Files audited: 14

Then one section per file in the format above. Do not summarize — write the full per-file analysis.
```

- [ ] **Step 2.2: Verify output completeness**

```bash
# All 14 hook filenames must appear in the output
for f in commit-msg forge-install-hooks forge-stage-detect forge-worktree-cleanup \
         post-commit post-merge post-pr-dreamer post-rewrite pre-commit pre-merge \
         pre-tool-use prompt-submit session-start test-forge-stage-detect; do
  grep -q "$f" ~/forge/brain/prds/audit-2026-04-28/surface-hooks.md \
    && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: 14 lines starting with `OK:`. If any show `MISSING:`, re-run the subagent for just that file and append its output.

- [ ] **Step 2.3: Verify severity tags present**

```bash
grep -c '\[CRITICAL\]\|\[HIGH\]\|\[MEDIUM\]\|\[LOW\]' \
  ~/forge/brain/prds/audit-2026-04-28/surface-hooks.md
```

Expected: count > 0. If 0, the subagent produced no findings — investigate by reading `surface-hooks.md` and re-run.

---

## Task 3: Audit Surface 2 — Python Tools

> **Run in parallel with Tasks 2 and 4.**

**Files:**
- Read: all `.py` files in `tools/` (22 files: 16 implementation + 6 test files)
- Create: `~/forge/brain/prds/audit-2026-04-28/surface-tools.md`

- [ ] **Step 3.1: Dispatch tools audit subagent**

Dispatch a `general-purpose` subagent with this exact prompt:

```
You are a senior software engineer and security auditor.

Audit all Python files in /home/lordvoldemort/Documents/forge/tools/. Read every file. For each file produce a section using EXACTLY this format:

---
FILE: <basename>
LINES: <line count>

PURPOSE:
- <what this module is responsible for>

KEY LOGIC:
- <core functionality, algorithms, external dependencies>

ISSUES:
[SEVERITY] description — file:line
(list every issue; if none, write "None identified")

SECURITY RISKS:
[SEVERITY] description — file:line
(focus on: shell injection via subprocess, path traversal, unsafe pickle/yaml, hardcoded secrets, missing input validation, arbitrary file write)

PERFORMANCE CONCERNS:
[SEVERITY] description — file:line

MAINTAINABILITY PROBLEMS:
[SEVERITY] description — file:line

IMPROVEMENTS:
- Actionable fix for each issue above (reference file:line)
---

Severity tags: [CRITICAL], [HIGH], [MEDIUM], [LOW]

Files to audit (read all before writing output):
Implementation files:
1. /home/lordvoldemort/Documents/forge/tools/verify_forge_task.py
2. /home/lordvoldemort/Documents/forge/tools/verify_tech_plans.py
3. /home/lordvoldemort/Documents/forge/tools/phase_ledger.py
4. /home/lordvoldemort/Documents/forge/tools/lint_skill_allowed_tools.py
5. /home/lordvoldemort/Documents/forge/tools/scan_bench.py
6. /home/lordvoldemort/Documents/forge/tools/forge_adjacency_scan.py
7. /home/lordvoldemort/Documents/forge/tools/forge_graph_query.py
8. /home/lordvoldemort/Documents/forge/tools/forge_drift_check.py
9. /home/lordvoldemort/Documents/forge/tools/eval_yaml_stdlib.py
10. /home/lordvoldemort/Documents/forge/tools/brain_restore_deleted.py
11. /home/lordvoldemort/Documents/forge/tools/forge_codebase_search.py
12. /home/lordvoldemort/Documents/forge/tools/append_phase_ledger.py
13. /home/lordvoldemort/Documents/forge/tools/shared_spec_policy.py
14. /home/lordvoldemort/Documents/forge/tools/check_frozen_spec.py
15. /home/lordvoldemort/Documents/forge/tools/forge_scan.py
16. /home/lordvoldemort/Documents/forge/tools/verify_scan_outputs.py

Test files (audit for test quality: coverage gaps, wrong assertions, missing edge cases):
17. /home/lordvoldemort/Documents/forge/tools/test_verify_forge_task.py
18. /home/lordvoldemort/Documents/forge/tools/test_verify_tech_plans.py
19. /home/lordvoldemort/Documents/forge/tools/test_phase_ledger.py
20. /home/lordvoldemort/Documents/forge/tools/test_eval_yaml_stdlib.py
21. /home/lordvoldemort/Documents/forge/tools/test_lint_skill_allowed_tools.py
22. /home/lordvoldemort/Documents/forge/tools/test_shared_spec_policy.py

After auditing all 22 files, write the complete findings to:
/home/lordvoldemort/forge/brain/prds/audit-2026-04-28/surface-tools.md

The file must start with:
# Surface Audit: Python Tools
Date: 2026-04-28
Files audited: 22

Then one section per file in the format above.
```

- [ ] **Step 3.2: Verify output completeness**

```bash
for f in verify_forge_task verify_tech_plans phase_ledger lint_skill_allowed_tools \
         scan_bench forge_adjacency_scan forge_graph_query forge_drift_check \
         eval_yaml_stdlib brain_restore_deleted forge_codebase_search \
         append_phase_ledger shared_spec_policy check_frozen_spec forge_scan \
         verify_scan_outputs test_verify_forge_task test_verify_tech_plans \
         test_phase_ledger test_eval_yaml_stdlib test_lint_skill_allowed_tools \
         test_shared_spec_policy; do
  grep -q "$f" ~/forge/brain/prds/audit-2026-04-28/surface-tools.md \
    && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: 22 lines starting with `OK:`.

- [ ] **Step 3.3: Verify severity tags present**

```bash
grep -c '\[CRITICAL\]\|\[HIGH\]\|\[MEDIUM\]\|\[LOW\]' \
  ~/forge/brain/prds/audit-2026-04-28/surface-tools.md
```

Expected: count > 0.

---

## Task 4: Audit Surface 3 — Skills, Commands, Agents

> **Run in parallel with Tasks 2 and 3.**

**Files:**
- Read: 84 skill directories in `skills/`, 17 command files in `commands/`, 4 agent files in `agents/`
- Create: `~/forge/brain/prds/audit-2026-04-28/surface-skills.md`

- [ ] **Step 4.1: Dispatch skills audit subagent**

Dispatch a `general-purpose` subagent with this exact prompt:

```
You are a senior software architect and technical writer auditing an AI plugin's behavioral specifications.

Audit the skill files, command files, and agent files in the Forge plugin at /home/lordvoldemort/Documents/forge/. These are Markdown files with YAML frontmatter that govern AI agent behavior. Your job is to find:
- Missing required frontmatter fields (name, description, type)
- Vague or unparseable trigger conditions (description fields that don't clearly say WHEN to invoke)
- Missing HARD-GATE markers on steps that are described as non-negotiable
- Contradictions between steps within a skill
- Skills that reference other skills that don't exist
- Steps that say what to do without saying how (no code, no command, no concrete output)
- Unreachable or dead steps
- Duplicate skills (two skills that do the same thing)
- Commands that invoke skills not in the catalog

For EACH file produce a section using EXACTLY this format:

---
FILE: <basename>
TYPE: skill | command | agent

PURPOSE:
- <what this file governs>

ISSUES:
[SEVERITY] description — file:line (or "frontmatter" for YAML issues)
(if none: "None identified")

IMPROVEMENTS:
- Actionable fix for each issue (reference file:line)
---

Severity tags: [CRITICAL], [HIGH], [MEDIUM], [LOW]

Audit all files in these directories:
- /home/lordvoldemort/Documents/forge/skills/ (84 subdirectories — each contains a SKILL.md)
- /home/lordvoldemort/Documents/forge/commands/ (17 .md files)
- /home/lordvoldemort/Documents/forge/agents/ (4 .md files)

Read every SKILL.md in every skills/ subdirectory. Read all command and agent .md files.

After auditing all files, write the complete findings to:
/home/lordvoldemort/forge/brain/prds/audit-2026-04-28/surface-skills.md

The file must start with:
# Surface Audit: Skills, Commands, Agents
Date: 2026-04-28
Files audited: 105 (84 skills + 17 commands + 4 agents)

Then one section per file. Do not skip files with "None identified" issues — write the section anyway so coverage is verifiable.
```

- [ ] **Step 4.2: Verify output completeness (sample check)**

```bash
# Spot-check 10 known skill names
for s in autoplan benchmark brain-forget forge-tdd forge-verification \
         intake-interrogate scan-codebase council-multi-repo-negotiate \
         eval-judge self-heal-systematic-debug; do
  grep -q "$s" ~/forge/brain/prds/audit-2026-04-28/surface-skills.md \
    && echo "OK: $s" || echo "MISSING: $s"
done
# Check all 17 commands
for c in build.md council.md dream.md eval.md forge-install.md forge.md \
         forge-status.md forge-test.md heal.md intake.md plan.md recall.md \
         remember.md review.md scan.md why.md workspace.md; do
  grep -q "${c%.md}" ~/forge/brain/prds/audit-2026-04-28/surface-skills.md \
    && echo "OK: $c" || echo "MISSING: $c"
done
```

Expected: all lines start with `OK:`.

- [ ] **Step 4.3: Verify severity tags present**

```bash
grep -c '\[CRITICAL\]\|\[HIGH\]\|\[MEDIUM\]\|\[LOW\]' \
  ~/forge/brain/prds/audit-2026-04-28/surface-skills.md
```

Expected: count > 0.

---

## Task 5: Synthesis — Merge Findings into audit-report.md

> **Run after Tasks 2, 3, and 4 are all complete.**

**Files:**
- Read: `~/forge/brain/prds/audit-2026-04-28/surface-hooks.md`, `surface-tools.md`, `surface-skills.md`
- Create: `~/forge/brain/prds/audit-2026-04-28/audit-report.md`

- [ ] **Step 5.1: Read all three surface files**

Read `~/forge/brain/prds/audit-2026-04-28/surface-hooks.md`, `surface-tools.md`, and `surface-skills.md` in full before writing anything.

- [ ] **Step 5.2: Deduplicate cross-surface findings**

Identify findings that reference the same root cause across surfaces. Merge them into one entry with multiple file references. Example: if `session-start.cjs` and `forge_scan.py` both call `execSync` without input sanitization, that's one finding: `H-001 / T-001 (cross-surface)`.

- [ ] **Step 5.3: Assign IDs**

- Hooks findings: `H-001`, `H-002`, … (sequential across all hooks files)
- Tools findings: `T-001`, `T-002`, …
- Skills findings: `S-001`, `S-002`, …
- Cross-surface findings: `X-001`, `X-002`, …

- [ ] **Step 5.4: Write audit-report.md**

Write `~/forge/brain/prds/audit-2026-04-28/audit-report.md` with this structure:

```markdown
# Forge Codebase Audit — Full Report
Date: 2026-04-28
Surfaces: CJS hooks (14 files), Python tools (22 files), Skills/commands/agents (105 files)

## Summary
| Severity | Count |
|---|---|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |
| Total | N |

## CRITICAL Findings
### H-001 [CRITICAL] <title>
**File:** path:line
**Description:** ...
**Fix:** ...

### T-001 [CRITICAL] <title>
...

## HIGH Findings
...

## MEDIUM Findings
...

## LOW Findings
...

## Cross-Surface Findings
### X-001 [SEVERITY] <title>
**Files:** path1:line, path2:line
**Description:** ...
**Fix:** ...
```

- [ ] **Step 5.5: Verify summary counts are non-zero**

```bash
grep -A5 "## Summary" ~/forge/brain/prds/audit-2026-04-28/audit-report.md | grep "Total"
```

Expected: `| Total | N |` where N > 0.

- [ ] **Step 5.6: Verify all severity sections present**

```bash
for section in "CRITICAL Findings" "HIGH Findings" "MEDIUM Findings" "LOW Findings"; do
  grep -q "## $section" ~/forge/brain/prds/audit-2026-04-28/audit-report.md \
    && echo "OK: $section" || echo "MISSING: $section"
done
```

Expected: 4 lines starting with `OK:`.

---

## Task 6: Write prd-locked.md

> **Run after Task 5 is complete.**

**Files:**
- Read: `~/forge/brain/prds/audit-2026-04-28/audit-report.md`
- Create: `~/forge/brain/prds/audit-2026-04-28/prd-locked.md`

- [ ] **Step 6.1: Write prd-locked.md from audit-report**

Read `audit-report.md` in full, then write `~/forge/brain/prds/audit-2026-04-28/prd-locked.md` with this exact structure:

```markdown
# PRD: Forge Codebase Hardening
task_id: audit-2026-04-28
status: locked
date: 2026-04-28

## Problem
<2-3 sentences derived from the CRITICAL and HIGH findings: what is broken, what is at risk>

## Goals
- Eliminate all CRITICAL findings (Phase 1)
- Resolve all HIGH findings (Phase 2)
- Address MEDIUM and LOW findings (Phase 3)

## Scope
Surfaces: CJS hooks (.claude/hooks/), Python tools (tools/), Skills/commands/agents (skills/, commands/, agents/)
Repo: /home/lordvoldemort/Documents/forge

## Fix Plan

### Phase 1 — Critical
| ID | File:Line | Description | Fix |
|---|---|---|---|
| H-001 | path:line | description | fix |
...

### Phase 2 — High
| ID | File:Line | Description | Fix |
|---|---|---|---|
...

### Phase 3 — Medium/Low
| ID | File:Line | Description | Fix |
|---|---|---|---|
...

## Out of Scope
- brain/ contents (runtime state)
- seed-product/ (example product)
- Third-party vendored files
- Documentation not governing agent behavior

## Success Criteria
- All Phase 1 findings resolved and verified by re-running the relevant tool or manual test
- All Phase 2 findings resolved
- Phase 3 addressed where effort is proportionate
- No new CRITICAL or HIGH findings introduced by fixes (verified by re-audit of changed files)

## Q1–Q9 Answers (Forge Intake Checklist)
Q1 (What): Fix all severity-tagged findings from the 2026-04-28 codebase audit across three surfaces
Q2 (Why): Prevent agent behavior corruption, security exploits, and silent failures identified in audit
Q3 (Who): Engineering — no user-facing changes
Q4 (When): Phase 1 ASAP; Phase 2 within current sprint; Phase 3 as capacity allows
Q5 (How): Direct code fixes per finding; no new dependencies introduced
Q6 (Dependencies): None external; internal only (hooks depend on CJS runtime, tools on Python 3.x)
Q7 (Risks): A fix for a CRITICAL finding may change hook behavior observed by other hooks — test each fix in isolation
Q8 (Rollback): All changes via git; rollback = git revert on the fixing commit
Q9 (Design): No UI/design work — code and Markdown only
```

- [ ] **Step 6.2: Verify Phase 1 table is populated**

```bash
grep -A3 "### Phase 1" ~/forge/brain/prds/audit-2026-04-28/prd-locked.md | grep "|"
```

Expected: at least one table row (a `|` line beyond the header).

- [ ] **Step 6.3: Verify Q1–Q9 section present**

```bash
grep -c "^Q[0-9]" ~/forge/brain/prds/audit-2026-04-28/prd-locked.md
```

Expected: 9.

---

## Task 7: Log Conductor Checkpoint and Final Verification

> **Run after Task 6 is complete.**

**Files:**
- Create: `~/forge/brain/prds/audit-2026-04-28/conductor.log`

- [ ] **Step 7.1: Write conductor log entry**

```bash
echo "[P1-PRD-LOCKED] task_id=audit-2026-04-28 date=2026-04-28 surfaces=hooks,tools,skills" \
  >> ~/forge/brain/prds/audit-2026-04-28/conductor.log
```

- [ ] **Step 7.2: Verify all six brain files exist**

```bash
for f in surface-hooks.md surface-tools.md surface-skills.md \
         audit-report.md prd-locked.md conductor.log; do
  test -f ~/forge/brain/prds/audit-2026-04-28/$f \
    && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: 6 lines starting with `OK:`.

- [ ] **Step 7.3: Verify PRD is self-contained (gate check)**

```bash
# prd-locked.md must contain all mandatory sections
for section in "## Problem" "## Goals" "## Scope" "## Fix Plan" \
               "### Phase 1" "### Phase 2" "### Phase 3" \
               "## Out of Scope" "## Success Criteria" "Q1 " "Q9 "; do
  grep -q "$section" ~/forge/brain/prds/audit-2026-04-28/prd-locked.md \
    && echo "OK: $section" || echo "MISSING: $section"
done
```

Expected: 11 lines starting with `OK:`.

- [ ] **Step 7.4: Report completion**

Output:

```
AUDIT COMPLETE
Brain path: ~/forge/brain/prds/audit-2026-04-28/
PRD ready: ~/forge/brain/prds/audit-2026-04-28/prd-locked.md
Gate logged: [P1-PRD-LOCKED] task_id=audit-2026-04-28
Next step: hand prd-locked.md to forge-intake-gate → council
```

---

## Execution Notes

- **Tasks 2, 3, 4 are independent — dispatch all three subagents in a single parallel message.**
- **Tasks 5, 6, 7 are strictly sequential** — each depends on the previous.
- If a subagent omits files from its surface output (detected by the verify steps), append a follow-up subagent prompt for just the missing files and append the output to the existing surface file.
- Do not modify source files. This plan produces brain files only.
