# Adjunct skills (optional)

These skills extend Forge with **extra workflows** (benchmarking, session snapshots, guardrails, etc.). They are **not** required for the default **conductor-orchestrate** path from intake through PR.

## Canonical path

**`conductor-orchestrate`** plus the skills it names per state remains the **source of truth** for shipping a task. If an adjunct skill conflicts with a conductor-mandated skill, **follow the conductor skill** unless the human explicitly opts into the adjunct workflow for that session.

## Catalog (optional)

| Skill | Use when |
|-------|----------|
| **`autoplan`** | You want structured auto-planning outside the default tech-plan flow. |
| **`benchmark`** | You need repeatable performance measurement notes. |
| **`canary`** | Canary-style rollout checks (distinct from session **FORGE_CANARY** injection). |
| **`context-save`** / **`context-restore`** | Checkpoint / restore long session context to disk. |
| **`freeze`** | Explicit freeze workflow outside **spec-freeze** naming. |
| **`guard`** | Extra guardrail pass before an action. |
| **`health`** | Stack or dependency health review. |
| **`learn`** | Capture learning notes into a structured pass. |
| **`retro`** | Retrospective facilitation outside **dream-retrospect-post-pr**. |
| **`review-readiness`** | Pre-PR checklist beyond **forge-trust-code** / standards reviewer. |
| **`qa-live-app`** | Live-app QA patterns when eval drivers are not enough. |

When in doubt, read the skill’s own **WHEN** description in `skills/<name>/SKILL.md`.

## Wiring

Adjunct skills are **not** auto-invoked by **`session-start`** stage stubs. To use one, invoke it by name when the task warrants it, or add explicit references in your team’s **conductor** overrides / runbooks (optional future work).
