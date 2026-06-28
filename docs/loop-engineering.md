# Loop engineering in Forge

Loop engineering ([Steinberger & Osmani, *The Architecture of Autonomous Iteration*, 2026](https://datasciencedojo.com/blog/agentic-loops-explained-from-react-to-loop-engineering-2026-guide/))
treats the LLM as **one component inside a self-correcting state machine**: Reason → Act →
Observe → Evaluate → auto-correct → repeat, until an explicit stopping condition. The unit
of value is the **trajectory, not the response** — a bug on turn 1 doesn't matter if the loop
detects it, runs a test, and fixes it by turn 4.

A loop without **explicit termination logic** is the single most expensive mistake. Every
Forge loop must satisfy all five controls:

| Control | Rule | Forge mechanism |
|---|---|---|
| **Iteration cap** | hard max cycles | `self-heal-loop-cap` (3); `/forge-council` workflow (16 concurrent / 1,000 total) |
| **Budget** | token / wall-clock ceiling | `forge_loop_guard --max-seconds`; `/workflows` per-agent token view |
| **Verifiable goal** | a *checked* success condition, never self-assessment | eval GREEN (`[P4.4-EVAL-GREEN]`); `forge-verification` (real command output) |
| **No-progress detection** | bail when state stops changing | `forge_loop_guard` (repeated failure signature) |
| **Circuit breaker** | escalate when the problem resists | self-heal → `BLOCKED`; eval-driver timeout / poll caps |

## Forge's loops

| Loop | Cycle | Termination |
|---|---|---|
| **Self-heal** (`self-heal-*`) | locate → triage → fix → verify → re-eval | cap 3 **+ no-progress + budget + Reflexion** (below) |
| **Eval** | run → RED → self-heal → re-eval | inherits self-heal termination; DONE on GREEN |
| **Conductor** | phase state machine P1→P5 | gates + non-decreasing phase ordering (`forge_trajectory_eval`) |
| **Council** (`/forge-council`) | fan out 4 surfaces × 5 contracts → cross-check → synthesize | gate-free span; 16/1,000 agent caps; no mid-run human input |

## The guard — `tools/forge_loop_guard.py`

Run it **before each self-heal retry** (and in CI as a pre-retry gate). It reads the task's
`[P4.4-EVAL-FAIL]` attempts and returns one of
**DONE | CONTINUE | ESCALATE_NO_PROGRESS | ESCALATE_CAP | ESCALATE_BUDGET**:

```bash
python3 tools/forge_loop_guard.py --task-id <id> [--max-attempts 3] [--max-seconds 0] [--strict]
```

For no-progress detection, self-heal logs a **failure signature** on each attempt:

```
[P4.4-EVAL-FAIL] task_id=<id> signature=<root-cause-id> outcome=<RED|YELLOW>
```

Two consecutive attempts with the **same signature** mean the root-cause diagnosis is wrong —
escalate now rather than spend the 3rd retry on a fix that addresses the wrong fault.

## Reflexion (critique-carry)

A capped loop that re-guesses each turn wastes the cap. After a failed attempt, write a
critique to the brain — `prds/<task-id>/heal/attempt-<n>.md`: what was tried, the failure
`signature`, and why it failed. The **next attempt MUST read the prior critiques** and may
not repeat a tried-and-failed fix. This is the [Reflexion](https://datasciencedojo.com/blog/loop-engineering-design-patterns/)
pattern — the loop *learns across iterations* instead of re-deriving the same wrong fix.

## Verifiable goals — good vs bad

"Make the semantic eval GREEN" is a good loop goal: success is **checkable**. "Improve the
code" is a bad one: the loop never knows when to stop. Every Forge loop's stop condition is an
automated check (`eval-judge`, `tools/verify_forge_task.py`, a test run) — **never the agent's
own "looks done" judgment** (`forge-verification` is the iron rule here).

## Where this is enforced

- `self-heal-loop-cap` — the cap, the signature logging, the guard call, and Reflexion.
- `tools/forge_loop_guard.py` — deterministic termination verdict (CI-testable, `--strict`).
- `forge_trajectory_eval` — scores `heal_efficiency` from the `[P4.4-EVAL-FAIL]` count.
- `conductor-orchestrate` — documents the P4.4 GREEN/FAIL/RED-INFRA markers the loop turns on.

## Sources
- [Agentic Loops: From ReAct to Loop Engineering (2026)](https://datasciencedojo.com/blog/agentic-loops-explained-from-react-to-loop-engineering-2026-guide/)
- [10 Loop Engineering Design Patterns (2026)](https://datasciencedojo.com/blog/loop-engineering-design-patterns/)
- [Loop Engineering for coding agents (2026)](https://explainx.ai/blog/loop-engineering-coding-agents-claude-code-guide-2026)
