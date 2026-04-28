# Design: Forge Codebase Audit

**Date:** 2026-04-28
**Status:** Approved
**Output target:** `~/forge/brain/prds/audit-2026-04-28/prd-locked.md`

---

## Problem

The Forge plugin has three distinct runtime surfaces — CJS hook scripts, Python tooling, and Markdown skills/commands — that have grown substantially and have never received a systematic cross-surface audit. Issues in any of these surfaces can silently corrupt agent behavior, expose security vulnerabilities, or cause the Forge pipeline to produce incorrect results. A structured audit is needed to surface and prioritize all defects before further feature work compounds them.

---

## Goals

- Produce a complete, severity-tagged findings inventory across all three surfaces
- Identify CRITICAL and HIGH issues that block safe continued development
- Produce a Forge-ready `prd-locked.md` that feeds directly into the intake → council → build → eval pipeline

---

## Scope

### Surfaces covered

| Surface | Files | Location |
|---|---|---|
| CJS hooks | 14 `.cjs` files (~3,250 LOC) | `.claude/hooks/` |
| Python tools | 22 `.py` files (~2,930 LOC) | `tools/` |
| Skills / commands / agents | ~84 skills + 17 commands + 4 agents | `skills/`, `commands/`, `agents/` |

### Out of scope

- `brain/` contents (runtime state, not source)
- `seed-product/` (example product, not plugin code)
- Third-party vendored files
- Documentation files not directly governing agent behavior

---

## Architecture

Three subagents run in parallel, each scoped to one surface. Each agent uses the standard per-file audit format:

```
FILE: <filename>
PURPOSE / KEY LOGIC / ISSUES / SECURITY RISKS /
PERFORMANCE CONCERNS / MAINTAINABILITY PROBLEMS /
IMPROVEMENTS / SEVERITY TAGS
```

After all three complete, a synthesis pass (main agent) reads the three surface files, deduplicates cross-cutting findings, assigns IDs, and writes the consolidated outputs.

---

## Brain File Structure

```
~/forge/brain/prds/audit-2026-04-28/
├── surface-hooks.md        # per-file findings: .claude/hooks/*.cjs
├── surface-tools.md        # per-file findings: tools/*.py
├── surface-skills.md       # per-file findings: skills/, commands/, agents/
├── audit-report.md         # merged, severity-sorted findings (all surfaces)
├── prd-locked.md           # Forge PRD ready for forge-intake-gate
└── conductor.log           # gate checkpoint log
```

---

## Synthesis Process

1. Read all three surface files
2. Deduplicate findings that span multiple surfaces (single entry, multiple file refs)
3. Sort by severity: CRITICAL → HIGH → MEDIUM → LOW
4. Assign finding IDs: `H-###` (hooks), `T-###` (tools), `S-###` (skills/commands)
5. Write `audit-report.md` and `prd-locked.md`
6. Append `[P1-PRD-LOCKED] task_id=audit-2026-04-28` to `~/forge/brain/prds/audit-2026-04-28/conductor.log`

---

## PRD Format (`prd-locked.md`)

```
# PRD: Forge Codebase Hardening

## Problem
## Goals
## Scope
## Fix Plan
  ### Phase 1 — Critical   (H-###, T-###, S-### items)
  ### Phase 2 — High
  ### Phase 3 — Medium/Low
## Out of Scope
## Success Criteria
```

Each entry in the fix plan includes: finding ID, `file:line`, description, and concrete fix.

---

## Severity Definitions

| Tag | Meaning |
|---|---|
| CRITICAL | Data loss, security exploit, silent failure that corrupts state |
| HIGH | Incorrect behavior under normal use, auth bypass, perf cliff |
| MEDIUM | Code smell, missed edge case, degraded maintainability |
| LOW | Naming, style, minor inconsistency |

---

## Success Criteria

- All three surface files written to brain with at least one finding per file audited
- `audit-report.md` contains a deduplicated, ID-tagged, severity-sorted findings list
- `prd-locked.md` passes the Forge intake checklist (all 9 questions answerable from the document)
- `conductor.log` contains `[P1-PRD-LOCKED] task_id=audit-2026-04-28`
