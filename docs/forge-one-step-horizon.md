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

## Elicitation mode — no command tutorial (question-forward)

**Use:** The human is mid-flow (e.g. finishing **`prd-locked`**, answering **Q9**, or one **Step 0.5** coverage dimension). **Your job in that turn is to get the answer** — not to re-teach what **`/qa-write`**, **`/forge`**, or **`qa-write-scenarios`** “actually does,” which **gates** are “still open,” or that **eval YAML** is not on disk yet.

**Forbidden in the same message as a simple confirm / single question:**

- Pasting or paraphrasing **`commands/qa-write.md`** (or any command) as a **preface** to “So eval YAML isn’t written yet…”
- **Status essays** (“gates 2–3 open”) unless the user **asked** *where are we?* / *what’s blocking?*
- **Pipeline micro-lectures** before “Confirm or correct: …”

**Allowed:** Minimal context **only** if the question cannot be stated without it (e.g. one line: *we need this for `design_intake_anchor`.*). If the user wants the full map, they open **`README`**, **`commands/`**, or ask *what does `/qa-write` do?*

## YAML-before-manual-CSV waiver (where it belongs)

Instructions about **`csv_baseline_waiver_user_quote`**, “say so explicitly in your own words,” or YAML-before-CSV waivers belong **only** in **`skills/qa-write-scenarios/SKILL.md`** **Step 0.0** — when **`qa-write-scenarios`** is invoked and **`manual-test-cases.csv`** is missing **and** you must STOP or offer the waiver **`AskQuestion`** path.

**Forbidden in assistant chat:**

- Repeating that waiver script during **`qa-prd-analysis`** Step 0.5 (Q1–Q8 coverage interrogation).
- “Reminder” paragraphs about recording waiver keys in **`qa-analysis.md`** while the human is still answering coverage questions — **`qa-analysis.md`** must exist first; waiver wording is **scenario-generation** gate, not **coverage elicitation**.

## Bundled intake turns (fake “one prompt”)

**Problem:** One message presents **one** structured prompt (**`AskQuestion`** / numbered choices for **task-id** only) while burying **other mandatory decisions** in prose: **Q9 design source-of-truth** (verbatim blockquote answer), net-new vs reuse, Figma **`figma_file_key` / node IDs**, ownership — plus optional **downstream roadmap** and **YAML-before-CSV waiver** copy.

That violates **`skills/using-forge/SKILL.md`** **Multi-question elicitation** (one primary dimension per message with **blocking** affordances for discrete forks; **no** prose-only *reply with (a)(b)…* for needle-moving fields).

**Required instead:**

- **Sequence:** resolve **task-id** (or confirm slug) **→** **then** show **`intake-interrogate`** Q9 **verbatim blockquote** and collect design authority **→** **then** remaining open doubts **one turn at a time** (or a single **Confirm/Correct** batch only where **`intake-interrogate`** allows pre-fill).
- **Do not** attach **QA→CSV→eval** narration or **CSV waiver** script to intake turns — wrong phase (**YAML-before-CSV** waiver lives in **`qa-write-scenarios`** Step 0.0 only).

Same anti-bundle rule applies to **any** phase: one **`AskQuestion`** must not stand in for multiple unrelated needle-moving decisions hidden in the same message’s prose.

## Relation to command files

Slash command markdown under `commands/` may describe **full** flows and comparisons (`/forge` vs `/intake`, etc.). That is **reference material**. When **guiding** the user step-by-step in the same session, still follow the **one-step horizon** above.

## Cursor project rule

`.cursor/rules/forge.mdc` mirrors this for Cursor sessions.
