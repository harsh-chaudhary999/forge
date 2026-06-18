# Human input — canonical convention (Claude Code)

> Shared support artifact (the `_` prefix marks a non-skill directory, like
> `_preamble/`). Skills that take a blocking human decision point here instead of
> repeating the convention inline. This is the single source of truth for the
> Claude-only line.

## The tool

**`AskUserQuestion`** is the canonical tool for every blocking human decision
(task-id confirmation, doubt resolution, waiver, fork, driver choice). A skill that
takes human input lists `AskUserQuestion` in its `allowed-tools` and uses it — never
a prose-only "reply if…" affordance.

## The norms (live dialogue)

These come from [`docs/forge-one-step-horizon.md`](../../docs/forge-one-step-horizon.md)
and `using-forge` (**Interactive human input** / **Multi-question elicitation**, items
4–8). They apply to every skill that drives chat:

- **One-step horizon** — resolve the next decision; don't bundle unrelated forks into one turn.
- **Question-forward** — no unsolicited reference-doc preface, no trailing later-stage status on a single-answer turn (unless the user asked for status/roadmap).
- **Multi-question elicitation** — when several answers are needed in sequence, one primary topic per turn, transcript-first, reconcile at the end (items 4–8).
- A skill's own **HARD-GATE** chat-visibility rules still apply on top of this — this convention does not relax them.

## Multi-host note

This branch is **Claude-only**. Hosts without `AskUserQuestion` (and per-IDE tool
renames) are out of scope here — see the dedicated branch for that host. Do **not**
re-introduce per-IDE conditionals into skill bodies.
