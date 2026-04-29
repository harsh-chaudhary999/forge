# One-step horizon (assistant dialogue)

**Scope:** This norm applies to **live assistant / agent messages** in Cursor, Claude Code, and other hosts — not to static reference docs (`README.md`, `commands/*.md` diagrams, brain templates), which may list full dependency order for verification.

**Canonical definition:** `skills/using-forge/SKILL.md` — **Horizon narration**, **Stage-local questioning**, **Multi-question elicitation** (item 5: speak only the immediate next dependency).

## Rule

In **chat**, name **only**:

1. The **single next** prerequisite, artifact, or skill the human must satisfy to move forward, **or**
2. A **downstream** step when the **current** question **cannot** be answered without it (rare), **or**
3. Later phases when the human **explicitly** asked “what happens after?” / “full roadmap.”

## Do not

- Preemptively enumerate pipelines (“then CSV, then `eval/*.yaml`, then `/qa-run`, then merge …”) while eliciting intake, QA interrogation, tech-plan rounds, or any **earlier** gate.
- Use “big picture” runbooks **every turn** to motivate coverage questions — full order belongs in **README**, **commands**, and this doc, **not** repeated in dialogue.

## Relation to command files

Slash command markdown under `commands/` may describe **full** flows and comparisons (`/forge` vs `/intake`, etc.). That is **reference material**. When **guiding** the user step-by-step in the same session, still follow the **one-step horizon** above.

## Cursor project rule

`.cursor/rules/forge.mdc` mirrors this for Cursor sessions.
