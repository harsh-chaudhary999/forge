# Forge — JetBrains AI Guidelines

## What Is Forge

Forge is a plug-and-play multi-repo product orchestration plugin. When working in a Forge-managed product, the following rules and workflows apply.

## Core Rules (from Forge locked decisions)

- **Always start with Intake**: Every PRD must go through intake before implementation begins
- **Council before code**: Multi-surface reasoning (backend, web, app, infra) must complete before any dev work
- **Eval gates everything**: Nothing ships without eval passing. E2E product stack verification only.
- **Brain persistence**: Every decision is recorded in `~/forge/brain/` with provenance
- **Worktree isolation**: Every task gets a fresh git worktree. No shared state between tasks.

## Anti-Patterns to Block

| If you think this... | Reality is... |
|---|---|
| "This is a simple change, skip intake" | No spec is ever clear enough. INTAKE every PRD. |
| "I can skip council since it's single-surface" | Multi-surface reasoning clarifies even single-surface work. |
| "Eval is slow, let's skip it" | Eval catches 60% of bugs that unit tests miss. |
| "I'll just fix it directly without a worktree" | Shared state causes cross-task contamination. Worktree always. |
| "This decision doesn't need brain documentation" | Every decision must be traceable. Brain-write always. |

## Skill Invocation

When a workflow might apply, invoke the relevant skill before taking any other action:
- Starting new feature: `forge-intake-gate`
- Reasoning about multi-repo changes: `council-multi-repo-negotiate`
- Implementing a task: `forge-tdd` + `forge-worktree-gate`
- After implementation: `forge-eval-gate`
- Recording a decision: `forge-brain-persist`

## Where Things Live

- Brain: `~/forge/brain/`
- Product config: `forge-product.md` (in product repo)
- Skills: `~/.claude/skills/` (if Forge plugin is installed)

---
*Install Forge: https://github.com/{your-handle}/forge*
*Copy this file to your project: `.junie/guidelines.md`*
