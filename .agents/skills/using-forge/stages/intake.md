---
stage: intake
description: Context injected during Forge intake phase (P1.*) — PRD interrogation, design lock, brain write
---

# Forge — Intake Stage

**You are in the INTAKE phase.** Your job is to interrogate the PRD, lock all ambiguities, and write a complete locked PRD to brain before anything else proceeds.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, invoke it before any response. This is not negotiable.

## Iron Law

```
DO NOT PROCEED TO COUNCIL UNTIL THE PRD IS LOCKED IN BRAIN AND [P1-PRD-LOCKED] IS LOGGED IN CONDUCTOR.LOG. INCOMPLETE INTAKE IS THE ROOT CAUSE OF 80% OF COUNCIL CONFLICTS.
```

## Active Skill: `intake-interrogate`

Invoke immediately on any PRD or feature request. Ask all 9 questions — do not skip, do not infer from context.

**Q9 (Design Lock) is mandatory for any web/app/UI work:**

> "Is there new design work (screens, components, flows) for this PRD? If yes, provide one of:
> - `lovable_github_repo` (+ optional `lovable_path_prefix` + pinned branch/tag/SHA)
> - `figma_file_key` + `figma_root_node_ids`
> - Existing brain design exports under `~/forge/brain/prds/<task-id>/design/`
>
> Bare Figma/Lovable URLs are not accepted — agents cannot read them."

**You must show this blockquote verbatim to the user. You may not infer or skip it.**

## Anti-Patterns — STOP

- **"I understand the PRD well enough, I can skip some questions"** — You cannot. Every question surfaces constraints that downstream agents will not re-ask. Missing one = council conflict.
- **"The user said UI, I'll assume same design as before"** — Never assume. Q9 requires explicit design source. No assumption substitutes for a locked Figma key or Lovable repo.
- **"I'll write the PRD now and fix ambiguities in council"** — Council does not fix intake gaps. It negotiates contracts on top of a locked PRD. Unfixed ambiguities become scope conflicts.
- **"The PRD is in chat, that's enough"** — Chat is not the transport layer. Brain files are. Write the PRD to `~/forge/brain/prds/<task-id>/prd-locked.md` before exiting intake.

## Gate Sequence

```
intake-interrogate (Q1–Q9) → PRD written to brain → [P1-PRD-LOCKED] logged → proceed to council
```

## What to write to brain

- `~/forge/brain/prds/<task-id>/prd-locked.md` — full PRD with all 9 questions answered
- If design exists: `~/forge/brain/prds/<task-id>/design/` — MCP ingest or design export
- `~/forge/brain/prds/<task-id>/conductor.log` — append `[P1-PRD-LOCKED] task_id=<id>`

## Next Gate

`[P1-PRD-LOCKED]` logged → switch to council phase → invoke `forge-council-gate` + `council-multi-repo-negotiate`.
