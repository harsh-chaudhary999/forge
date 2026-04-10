---
name: forge-subagent-anatomy
description: Template and rules for creating and dispatching subagents. Status state machine, dispatch patterns, isolation rules, review integration.
type: reference
---
# Subagent Anatomy

## Required Sections

Every subagent definition MUST include these sections:

```markdown
# {Subagent Name}

## Role
Brief 1-line description of what this subagent does.

## When to Invoke
Specific conditions when this subagent is dispatched.

## Inputs
- Full task text (complete, no summaries — D30)
- Context needed (files, specs, state)
- Configuration (timeouts, limits)

## Workflow
1. Step 1
2. Step 2
3. ...

## Output
- Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
- Results (code, analysis, decision)
- Reasoning (why this approach)

## Edge Cases
At least 3 documented edge cases with specific actions.

## Examples
Concrete usage examples with realistic inputs and outputs.
```

## Status State Machine

Subagents report one of four statuses. Transitions are one-way — a subagent cannot change its own status after reporting.

```
┌─────────────────────────────────────────────────────┐
│                   DISPATCHED                        │
│            (subagent begins work)                   │
└──────────┬──────────┬──────────┬──────────┬─────────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
        ┌──────┐  ┌────────────┐ ┌──────────┐ ┌───────┐
        │ DONE │  │ DONE_WITH  │ │ NEEDS    │ │BLOCKED│
        │      │  │ _CONCERNS  │ │ _CONTEXT │ │       │
        └──┬───┘  └─────┬──────┘ └────┬─────┘ └───┬───┘
           │            │              │            │
           ▼            ▼              ▼            ▼
        Proceed    Address concerns  Provide     Escalate to
        to review  before review     context &   conductor
                                     re-dispatch  or human
```

| Status | Meaning | Conductor Action |
|---|---|---|
| **DONE** | Task completed successfully | Proceed to review stage |
| **DONE_WITH_CONCERNS** | Completed but correctness issues exist | Address concerns before review |
| **NEEDS_CONTEXT** | Missing information to proceed | Provide context, re-dispatch |
| **BLOCKED** | Cannot proceed, no workaround | Escalate to conductor or human |

## Dispatch Rules

1. **Full context, no summaries** — Pass complete task text, file paths, and spec references. Never summarize inputs for brevity (D30).
2. **Isolated worktree** — Each subagent works in a fresh git worktree. No shared state between tasks (D30).
3. **One task per dispatch** — A subagent handles exactly one task. Multiple tasks = multiple dispatches.
4. **No framework dependencies** — Subagents use native tools only. No LangChain, Playwright, or third-party agent frameworks (D5).
5. **No plugin dependencies** — Subagents must not depend on any external plugin at runtime (D13).

## Existing Subagents

| Subagent | Role | Defined In |
|---|---|---|
| **dev-implementer** | TDD build in isolated worktree | `agents/dev-implementer/` |
| **spec-reviewer** | Verify implementation matches shared-dev-spec | `agents/spec-reviewer/` |
| **code-quality-reviewer** | 8-point quality + performance/security/observability | `agents/code-quality-reviewer/` |
| **dreamer** | Inline conflict resolution + post-merge retrospective | `agents/dreamer/` |

## Review Integration

Subagents that produce code go through a two-stage review:

1. **Spec compliance** (spec-reviewer) — Does the code match the shared-dev-spec?
2. **Code quality** (code-quality-reviewer) — Does the code meet the 8-point quality framework?

The conductor dispatches reviewers after a `DONE` or `DONE_WITH_CONCERNS` status. Reviewers are themselves subagents and follow the same status protocol.

## Creating a New Subagent

1. Create directory: `agents/{subagent-name}/`
2. Create `AGENT.md` following the template above
3. Include at least 3 edge cases with explicit actions
4. Add entry to `forge-glossary` subagents table
5. If platform uses Antigravity, create symlink in `.agent/skills/`
