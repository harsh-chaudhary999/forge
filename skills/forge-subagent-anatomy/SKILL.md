---
name: forge-subagent-anatomy
description: "WHEN: You are creating or reviewing a Forge subagent and need the canonical template, state machine, or dispatch rules."
type: reference
version: 1.0.3
preamble-tier: 1
triggers:
  - "subagent template"
  - "how to write an agent"
  - "subagent format"
allowed-tools:
  - Read
---

# Subagent Anatomy: Complete Authoring Guide

## Anti-Pattern Preamble: Why Subagents Break Down

| Rationalization | Why It Fails |
|---|---|
| "The parent session has context — the subagent will inherit it" | Subagents get only what you explicitly pass in the prompt. They start with zero session history. Anything not written in the dispatch prompt is invisible to them. |
| "A vague role description is fine — the subagent is smart enough to figure it out" | Ambiguous role + no scope boundary = subagent doing half the work or the wrong work. The conductor gets back an output it cannot use and must redispatch. |
| "I'll pass the full conversation history as context" | Context pollution is the failure mode subagents exist to prevent. Pass only the task-specific inputs: the plan file, the relevant brain slice, and the explicit output contract. |
| "The subagent will decide what format to return results in" | If the parent doesn't specify the output format (status enum, file path, JSON fields), the subagent will invent one. The conductor's parse step breaks on first divergence. |
| "Subagents are optional — the conductor can just do all the work" | Parallel subagent dispatch is how Forge compresses wall-clock time. Skipping subagents forces serial execution and caps throughput at single-session token rate. |
| "I'll define the edge cases and error paths later" | Subagents hit edge cases during execution, not planning. Without explicit error-path instructions (what to return on BLOCKED, how to report partial results), the subagent silently drops work or returns NEEDS_CONTEXT. |

## Introduction: Why Specialized Subagents Matter

Subagents are isolated agents that solve a **single, well-defined task** in a fresh context. They are not smaller versions of the main conductor — they are specialists with focused roles, clear boundaries, and zero context pollution.

**Why subagents matter:**

1. **Isolation prevents context pollution** — Subagent gets only the task it needs to solve. No conversation history, no parent session state, no baggage. Clean mental model.

2. **Fresh context per task means subagent stays focused** — With no historical context, subagent doesn't have to parse "which of my prior work applies here?" It focuses entirely on the current task.

3. **Parallel execution with independent reasoning** — Multiple subagents can reason independently on different tasks simultaneously. Each gets its own fresh Haiku context. Parent (conductor) can dispatch 3 code reviewers in parallel, each working in isolation, then collect results.

4. **Clear input/output contracts prevent miscommunication** — A subagent's role, inputs, and outputs are explicit contracts. Parent session knows exactly what to give and what to expect back.

This guide teaches you to write subagents that are **focused, unambiguous, and reliably executable**.

## Product language (brain)

When the parent passes a **`task_id`**, if **`~/forge/brain/prds/<task-id>/terminology.md`** exists, subagents that author **user-facing** text, **API error** copy, or **eval/QA** assertions must **read** that file from the brain path (or ask the parent to pass the path in the dispatch prompt) and use **canonical** product terms — not [forge-glossary](../forge-glossary/SKILL.md) alone. The **conductor does not** auto-inject term excerpts; the subagent’s allowed tools must include **Read** for that path. See [docs/terminology-review.md](../../docs/terminology-review.md).

## Part 1: Required Sections

Every subagent definition MUST include these sections. They form an explicit contract between the parent conductor and the specialized subagent.

```markdown
# {Subagent Name}

## Role
[Specific 1-line role description]

## When to Invoke
[Explicit trigger conditions]

## Inputs
[Complete list of required inputs with formatting specs]

## Workflow
[Step-by-step process the subagent follows]

## Output
[Status codes and structured output format]

## Edge Cases
[At least 3 documented edge cases with explicit actions]

## Examples
[Concrete usage examples with realistic inputs and outputs]
```

Each section is described in detail below.

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/subagent-deep-dive.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

## Part 7: Subagent Status Codes — Clear Definitions and Handling

| Status | Definition | When to Use | Parent Action |
|---|---|---|---|
| **DONE** | Task completed successfully. All requirements met, no gaps, no concerns. Output is final and ready for next stage. | - All criteria met - No ambiguities or gaps - No extra scope to clarify | Proceed to next stage (review, merge, deploy) |
| **DONE_WITH_CONCERNS** | Task completed but flags observations, doubts, or scope clarifications needed before proceeding. Work is done, but parent should be aware of caveats. | - All core requirements done - Extra code present (good practice, but not spec'd) - Minor ambiguities resolved with assumptions - Recommendations for follow-up | Review concerns, decide: acceptable or needs rework? If acceptable, proceed. If not, send back for fixes. |
| **NEEDS_CONTEXT** | Task cannot proceed. Missing information, ambiguous requirements, or unclear inputs. Subagent has identified what's needed. | - Required input is missing - Specification is ambiguous - Context is incomplete - Parent must clarify before subagent can work | Provide clarification, send corrected inputs, re-dispatch. Do NOT assume or fill gaps yourself. |
| **BLOCKED** | Task cannot be completed. Requires intervention, redesign, or escalation. No workaround available. | - Specification contradicts itself - Infrastructure is missing - Requirements are impossible to meet - Subagent needs higher-level decision | Escalate to conductor or human. May require spec redesign, architecture review, or external decision. |

---

## Part 8: Pre-Dispatch Checklist (15 Items)

Before dispatching a subagent, verify all 15 items:

1. **[ ] Role is specific and bounded**
   - Subagent role is not vague (not "code reviewer" but "spec compliance reviewer")
   - Scope boundaries are explicit (in scope: X, out of scope: Y)
   - Expertise level is stated

2. **[ ] Inputs are complete and explicit**
   - Every input is named and described
   - No file paths; full text provided
   - Format specifications included (YAML, JSON, Markdown, line count)

3. **[ ] Scene-setting context explains task purpose**
   - Business context is clear (why is this task needed?)
   - Task has been introduced to subagent (not just "review this" but "we're implementing Auth for GDPR compliance")

4. **[ ] Workflow is step-by-step**
   - Not high-level (not "review code") but granular ("read spec, extract requirements, compare to code line-by-line")
   - Checkpoints are marked

5. **[ ] Output format is specified**
   - Status codes are explicit (only DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED)
   - Output structure is defined (findings, reasoning, next steps)
   - Examples show what DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT output looks like

6. **[ ] Status codes are clear**
   - All 4 status codes have definitions
   - Subagent knows when to use each

7. **[ ] Examples are complete and realistic**
   - Examples are actual-scale, not toy examples
   - Examples show happy path AND edge cases
   - Subagent reasoning is visible in examples

8. **[ ] Subagent knows what questions to ask**
   - Workflow includes questions subagent should ask before proceeding
   - Subagent knows what "done" means (acceptance criteria)

9. **[ ] No conversation history pollution**
   - Inputs are task-specific only
   - No conversation history, prior attempts, or unrelated context
   - Subagent gets fresh context for this task only

10. **[ ] Tool access is appropriate**
    - Subagent has tools to complete task (read, analyze, output)
    - Subagent does NOT have write/deploy/execute tools (those belong in parent session)

11. **[ ] Escalation paths are clear**
    - If subagent hits BLOCKED, what happens? (Escalate to conductor, human review?)
    - If subagent hits NEEDS_CONTEXT repeatedly, what's the escalation?

12. **[ ] Overlap with existing agents checked**
    - New subagent doesn't duplicate existing role
    - Check Existing Subagents table before creating new subagent

13. **[ ] Role distinction from parent session is clear**
    - Subagent's role is different from parent conductor's role
    - Subagent is NOT the parent session, it's a specialist

14. **[ ] Error handling is specified**
    - What if input is malformed?
    - What if specification is locked/read-only?
    - What if code is unreadable?
    - For each error scenario, what status does subagent return?

15. **[ ] Success criteria are defined**
    - How does subagent know it succeeded?
    - What does DONE output look like?
    - Can parent session tell success from failure by reading status code and output?

---

## Existing Subagents Reference

| Subagent | Role | Location | Status Code | Best For |
|---|---|---|---|---|
| **dev-implementer** | TDD implementation in isolated worktree. Writes code from spec. | `agents/dev-implementer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Building features from shared-dev-spec |
| **spec-reviewer** | Verify implementation matches shared-dev-spec requirements line-by-line. | `agents/spec-reviewer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Verifying spec compliance after dev-implementer |
| **code-quality-reviewer** | Audit code against 8-point quality framework (performance, security, observability, readability, maintainability, testability, modularity, robustness). | `agents/code-quality-reviewer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Reviewing code quality after spec compliance |
| **dreamer** | Inline conflict resolution and post-merge retrospective. Scores decisions, surfaces anti-patterns, recommends improvements. | `agents/dreamer/` | Summary + recommendations | Post-PR retrospective and decision review |

---

## Review Integration

Subagents that produce code go through a two-stage review:

1. **Spec compliance** (spec-reviewer) — Does the code match the shared-dev-spec?
2. **Code quality** (code-quality-reviewer) — Does the code meet the 8-point quality framework?

The conductor dispatches reviewers after a `DONE` or `DONE_WITH_CONCERNS` status from dev-implementer. Both reviewers are themselves subagents and follow the same status protocol.

**Dispatch sequence:**
1. Conductor dispatches dev-implementer → returns DONE / DONE_WITH_CONCERNS
2. If DONE or DONE_WITH_CONCERNS, conductor dispatches spec-reviewer in parallel
3. If spec-reviewer returns DONE, conductor dispatches code-quality-reviewer
4. If all return DONE, code is ready to merge
5. If any returns DONE_WITH_CONCERNS, parent reviews concerns and decides: merge or rework
6. If any returns NEEDS_CONTEXT or BLOCKED, escalate to conductor or human

---

## Creating a New Subagent

1. **Check for overlap**: Review Existing Subagents table. Does this role already exist?
2. **Create directory**: `agents/{subagent-name}/`
3. **Create AGENT.md**: Follow this template with all 8 sections (Role, When to Invoke, Inputs, Workflow, Output, Edge Cases, Examples, Status Codes)
4. **Include anti-patterns**: Ensure your subagent anatomy doesn't fall into the 5 anti-patterns listed in Part 3
5. **Document edge cases**: Include at least 3 edge cases with explicit actions
6. **Write realistic examples**: Include example inputs, workflow reasoning, and expected outputs for each status
7. **Add to glossary**: Update `forge-glossary` subagents table with entry for new subagent
8. **Review for readability**: Another engineer should be able to dispatch this subagent from AGENT.md alone, without asking questions
9. **If platform uses Antigravity**: Create symlink in `.agent/skills/`

---

## Cross-Reference: Superpowers

This skill pairs with **superpowers:subagent-driven-development** for executing complex tasks with specialized subagents. Use when:
- You have a complex multi-stage task (implementation → review → integration)
- Different stages need different expertise
- You want parallel execution and independent reasoning
- Parent session needs to route results and make decisions

**Related skills:**
- `superpowers:dispatching-parallel-agents` — Dispatch multiple subagents in parallel
- `superpowers:receiving-code-review` — Handle DONE_WITH_CONCERNS status and address feedback
- `forge-skill-anatomy` — Write new skills (similar to subagents but different scope)
