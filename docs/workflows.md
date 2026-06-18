# Forge + Claude Code Dynamic Workflows

[Dynamic Workflows](https://code.claude.com/docs/en/workflows) let Claude Code run a
JavaScript script that orchestrates many subagents in the background (up to 16
concurrent, 1,000 per run), with the orchestration codified and rerunnable. Forge
uses them for the phases that are **parallel-heavy and free of mid-run human
gates** — workflows explicitly **cannot take human input mid-run**, so they cannot
replace the human-gated conductor wholesale.

## Which conductor spans map to workflows

| Conductor phase | Workflow-able? | Why |
|---|---|---|
| Intake (PRD lock) | No | Human Q&A + design lock; ends in a human approval gate. |
| **Council (surfaces + contracts)** | **Yes** | 4 surfaces × 5 contracts fan out independently; output is a *draft* spec, reviewed by a human afterward. Shipped: **`forge-council`**. |
| Spec-freeze | No | Human gate by design. |
| Tech plans | Partly | Per-repo drafting fans out; `HUMAN_SIGNOFF` remains a gate. |
| State 4b (QA CSV, semantic eval) | Partly | CSV sample/count approvals are human gates. |
| Review (spec + quality) | Yes | Per-file/per-dimension review fans out; a good future workflow. |
| Eval (scenario execution) | Yes | Per-scenario drivers fan out; a good future workflow. |
| Self-heal / PR set / merge | No | Merge rights and escalation are human gates. |

The rule of thumb: **a workflow runs the automatable span *between* two human
gates.** The human still runs the gate (approve the draft spec, sign off tech
plans, approve the CSV, authorize the merge).

For the spans marked **No** above — the ones that need a human *in the loop the
whole time* (live adversarial council, parallel review, competing-hypothesis
self-heal) — the right primitive is [Agent Teams](agent-teams.md), not workflows.

## Shipped: `/forge-council`

`.claude/workflows/forge-council.js` — over a locked PRD it:

1. **Surfaces** — fans out backend / web / app / infra reasoning in parallel (each follows its `reasoning-as-*` skill).
2. **Contracts** — fans out REST / events / cache / DB / search analysis, reconciled against the surface outputs (each follows its `contract-*` skill).
3. **Cross-check** — an adversarial verifier per contract flags cross-surface inconsistencies (defaults to *inconsistent* when uncertain).
4. **Synthesize** — one agent writes `prds/<task-id>/shared-dev-spec.DRAFT.md` to the brain with a `## Unresolved conflicts` section.

It writes a **DRAFT only** — `spec-freeze` stays a human gate.

### Run it

```
/forge-council
```

then pass the task id, or invoke with args:

```
Run /forge-council on { "task_id": "my-task" }
```

The locked PRD must exist at `prds/<task-id>/prd-locked.md` in the brain
(default `~/forge/brain`; override with `{ "task_id": "...", "brain": "/path" }`).

> **Cost:** a council run spawns ~14 agents. Try it on one task before relying on
> it. The `/workflows` view shows per-agent token usage and lets you stop early.

### Availability

`install.sh` copies `.claude/workflows/*.js` to `~/.claude/workflows/`, so
`/forge-council` is available in every project. You can also run it from inside the
Forge repo, where Claude Code loads it from the repo's `.claude/workflows/`.

## Authoring more Forge workflows

Save any run you like as a reusable command: in `/workflows`, select the run and
press `s`. Good next candidates are a **review** workflow (dimensions × changed
files → adversarial verify) and an **eval** workflow (one agent per semantic-CSV
scenario → `eval-judge`). Keep each workflow to a single gate-free span.
