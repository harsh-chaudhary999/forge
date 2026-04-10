---
name: forge-glossary
description: Forge glossary. Terms and definitions in Forge context. Look up when encountering unfamiliar Forge terminology.
type: reference
---
# Forge Glossary

## Pipeline Stages

| Term | Definition |
|---|---|
| **Intake** | 8-question PRD interrogation that locks scope, success criteria, and constraints. Gate: `forge-intake-gate`. |
| **Council** | Multi-surface contract negotiation. 4 surfaces (backend, web, app, infra) + 5 contracts (REST, events, cache, DB, search) negotiate to produce shared-dev-spec. Gate: `forge-council-gate`. |
| **Spec Freeze** | Immutable lock on shared-dev-spec after council. No changes without full re-negotiation. Skill: `spec-freeze`. |
| **Tech Plan** | Per-project bite-sized implementation tasks (2-5 min each, exact code, exact commands). One plan per repo. |
| **Build** | TDD implementation in isolated worktrees. Dev-implementer subagent executes tasks. |
| **Eval** | End-to-end product test across all services. Drivers: API, DB, cache, search, events, web, mobile. Gate: `forge-eval-gate`. |
| **Self-Heal** | Auto-fix loop when eval fails: locate fault → triage → fix → verify. Max 3 retries before escalation. |
| **Review** | Two-stage code review: spec compliance (spec-reviewer) then code quality (code-quality-reviewer). |
| **Dream** | Dreamer retrospective: score decisions, extract patterns, write learnings to brain. |
| **PR Set** | Coordinated PRs across repos, merged in dependency order. |

## Core Concepts

| Term | Definition |
|---|---|
| **PRD** | Product Requirements Document. Locked via intake. Immutable after lock. |
| **Shared-Dev-Spec** | Contract agreement across all services. Output of council. Frozen before build. |
| **Contract** | Explicit agreement on interface between services: API (REST), events (Kafka), cache (Redis), DB schema (MySQL), search (Elasticsearch). |
| **Surface** | A perspective in council: backend, web frontend, app frontend, infrastructure. Each surface reasons about the PRD from its domain. |
| **Brain** | Git-backed decision log at `~/forge/brain/`. Immutable, auditable, searchable. Every decision has provenance (who, when, why, evidence). |
| **Worktree** | Fresh git worktree per project per task (D30). Isolated workspace. No shared state between tasks. |
| **HARD-GATE** | Non-skippable process gate. Cannot be rationalized away. Examples: intake, council, eval, TDD, verification. |
| **Anti-Pattern Preamble** | Rationalization table at the top of discipline skills. Lists common excuses and their rebuttals. Prevents shortcut-seeking. |

## Subagents

| Term | Definition |
|---|---|
| **dev-implementer** | Builds code with TDD. Dispatched per task in isolated worktree. Reports: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED. |
| **spec-reviewer** | Verifies implementation matches shared-dev-spec. Reads actual code, not reports. |
| **code-quality-reviewer** | 8-point quality framework + performance, security, observability review. |
| **dreamer** | Inline conflict resolution (during eval) and post-merge retrospective scoring. |

## Subagent Status Codes

| Status | Meaning |
|---|---|
| **DONE** | Task completed successfully. Proceed to review. |
| **DONE_WITH_CONCERNS** | Task completed but correctness issues exist. Address before review. |
| **NEEDS_CONTEXT** | Missing information. Provide context and re-dispatch. |
| **BLOCKED** | Cannot proceed. Escalate to conductor or human. |

## Decision References (D1-D30)

Key locked decisions:

| Decision | Summary |
|---|---|
| D5 | No third-party agent frameworks (no LangChain, Playwright, Puppeteer) |
| D13 | No runtime dependency on any external plugin at runtime |
| D14 | Cialdini persuasion grounding: Authority, Commitment, Social Proof, Clarity, Unity |
| D15 | Skills are TDD'd against seed product pressure scenarios |
| D24 | HARD-GATE tags on every non-skippable step |
| D25 | Anti-Pattern preambles on every discipline-enforcing skill |
| D30 | Fresh worktree per project per task. No shared state. |

## Eval Verdicts

| Verdict | Meaning |
|---|---|
| **GREEN** | All critical scenarios passed. Ready to merge. |
| **YELLOW** | All critical passed, some non-critical failed. Review and decide. |
| **RED** | Critical scenario failed. Cannot merge. Enter self-heal loop. |
