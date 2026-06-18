# Forge + Claude Code Agent Teams

[Agent teams](https://code.claude.com/docs/en/agent-teams) coordinate several Claude
Code sessions as a team: one **lead** spawns **teammates**, they share a **task list**
and a **mailbox**, and — unlike subagents — teammates talk to each other *and* you can
message any teammate directly mid-run. They are the human-in-the-loop, discussion-heavy
counterpart to [Dynamic Workflows](workflows.md).

> **Experimental, off by default.** Agent teams require
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (in `settings.json` `env` or your shell) and
> have known limitations (no `/resume` of in-process teammates, task-status lag, one team
> per session, no nested teams). Forge does not depend on them; this doc maps where they
> *fit* the conductor when you opt in.

## Workflows vs. agent teams (the dividing line)

Both run many agents; the difference is **who holds the plan** and **whether a human can
intervene mid-run**:

| | Dynamic workflow | Agent team |
|---|---|---|
| Plan lives in | A script the runtime executes | The lead, turn by turn |
| Mid-run human input | **No** (only permission prompts pause it) | **Yes** — message any teammate, approve/reject their plan |
| Scale | Dozens–hundreds of agents | ~3–5 teammates |
| Results | Only the final answer returns | Shared task list; you watch and steer |
| Best for | Gate-free, repeatable fan-out | Collaborative spans needing discussion + judgment |

The rule from [`docs/workflows.md`](workflows.md): **a workflow runs the automatable span
*between* two human gates.** An agent team runs the span where the *human is in the loop
the whole time* — exactly the spans a workflow can't, because a workflow "cannot take
human input mid-run."

## Which conductor spans map to agent teams

| Conductor phase | Team-able? | Why |
|---|---|---|
| Intake (PRD lock) | No | Single human Q&A, not parallel exploration. |
| **Council (adversarial)** | **Yes** | The 4 surfaces can *debate* each other (challenge owns/consumes claims) with you steering — a richer version of the gate-free [`/forge-council`](workflows.md) workflow draft. Use the workflow for a hands-off draft; a team when you want to argue it out live. |
| Spec-freeze | No | Human gate by design (a team feeds it, doesn't replace it). |
| Tech plans | Partly | One teammate per repo drafts in parallel; the lead synthesizes; `HUMAN_SIGNOFF` stays a gate. |
| **Review (spec + quality)** | **Yes** | One teammate per dimension (spec-compliance / security / performance / tests), each a Forge subagent, cross-challenging findings — the canonical "parallel PR review" team. |
| **Self-heal (competing hypotheses)** | **Yes** | The canonical "competing-hypotheses debugging" team — one teammate per root-cause theory, actively trying to disprove each other. Strong fit for `self-heal-*`. |
| Build (multi-repo) | Partly | Cross-layer changes where each teammate owns a different repo/file set; pair with worktree isolation and the TDD gate. Avoid two teammates editing one file. |
| PR set / merge | No | Merge rights + escalation are human gates. |

## Roles = Forge subagents (don't pre-author a team)

The team **config is auto-generated** under `~/.claude/teams/{session-name}/config.json`
and cleaned up when the session ends — **never hand-author or commit it** (Claude Code
overwrites it on the next state update), and there is **no project-level team config**.

The supported way to define reusable roles is **subagent definitions**, which Forge
already ships. Spawn a teammate *using* one by name:

```text
Spawn a teammate using the spec-reviewer agent type to verify the diff against
the frozen shared-dev-spec, and one using code-quality-reviewer for the quality pass.
Have them challenge each other's findings before reporting.
```

Forge roles available as teammates: **`agents/`** — `dev-implementer`, `spec-reviewer`,
`code-quality-reviewer`, `dreamer` — plus the reasoning skills (`reasoning-as-backend`,
`reasoning-as-web-frontend`, `reasoning-as-app-frontend`, `reasoning-as-infra`) and the
`contract-*` skills as lenses.

> A teammate honors a subagent definition's `tools` allowlist and `model`, and the body
> is appended to its system prompt. Note Claude Code does **not** apply a subagent
> definition's `skills`/`mcpServers` frontmatter to a teammate — but teammates load skills
> and MCP servers from your **project + user settings** anyway, so Forge's plugin skills
> and the [brain MCP](brain-mcp.md) are available to every teammate the same as a normal
> session.

## Enforcing Forge gates via team hooks

Forge's HARD-GATE philosophy maps directly onto the agent-team [hooks](https://code.claude.com/docs/en/hooks):

| Hook | Exit 2 effect | Forge use |
|---|---|---|
| `TaskCompleted` | Block marking the task done + send feedback | Refuse "done" until the eval/spec/QA gate for that task is satisfied (the conductor's State 4b discipline). |
| `TaskCreated` | Block creation + send feedback | Keep tasks task-scoped (one active task-id) and well-formed before they enter the shared list. |
| `TeammateIdle` | Keep the teammate working + send feedback | Don't let a reviewer go idle with an unverified claim or an unrun gate. |

**Shipped: [`.claude/hooks/forge-team-gates.cjs`](../.claude/hooks/forge-team-gates.cjs)**
(registered in [`hooks/hooks.json`](../hooks/hooks.json) for all three events). It runs
in two layers:

- **Audit (always, never blocks):** appends an append-only line to the brain's
  team-events log (`prds/<FORGE_TASK_ID>/team-events.log` when a task id is set, else
  `<brain>/team-events.log`), so Forge's auditable trajectory covers team activity too.
  No brain on disk → no-op.
- **Enforce (opt-in: `FORGE_TEAM_GATES=strict`):** conservatively blocks (exit 2 +
  stderr) a `TaskCompleted` that *claims* a merge/ship/release while the brain shows no
  `[P5…]` (PR-merged) marker, and a `TeammateIdle` while the active task's last eval is
  `[P4.4-EVAL-FAIL]`. OFF by default so it never surprises an experimental team.

> A hook **cannot fully adjudicate** a Forge gate from a task event — it sees the event
> payload, not the work. The strict checks are deliberately narrow (clear ship claims
> without brain evidence; idling on a RED eval). Treat them as a backstop, not a
> replacement for the conductor's gates. These events don't support
> `additionalContext`, so the lever is exit code only.

## Launching a team

With the experimental flag set, just describe the task and the roles in natural language —
Claude proposes/spawns teammates and you confirm:

```text
Review PR #142 as a team: a spec-reviewer teammate checking the diff against the frozen
shared-dev-spec, a code-quality-reviewer on maintainability/perf/security, and a
test-coverage teammate. Have them report findings and challenge overlaps. Require plan
approval before any teammate edits files.
```

Start with **research/review/debugging** spans (clear boundaries, no parallel writes)
before trying team-based implementation. See the upstream
[best practices](https://code.claude.com/docs/en/agent-teams#best-practices).
