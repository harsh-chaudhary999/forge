# One-step horizon (assistant dialogue)

**Scope:** This norm applies to **live assistant / agent messages** in Cursor, Claude Code, and other hosts — not to static reference docs (`README.md`, `commands/*.md` diagrams, brain templates), which may list full dependency order for verification.

**Canonical definition:** `skills/using-forge/SKILL.md` — **Horizon narration**, **Stage-local questioning**, **Multi-question elicitation** (item 5: speak only the immediate next dependency).

## Rule

In **chat**, name **only**:

1. The **single next** prerequisite, artifact, or skill the human must satisfy to move forward, **or**
2. A **downstream** step when the **current** question **cannot** be answered without it (rare), **or**
3. Later phases when the human **explicitly** asked “what happens after?” / “full roadmap.”

## Do not

- Preemptively enumerate whole pipelines (“then council, then tech plans, then merge …” or product-specific chains) while eliciting an **earlier** gate.
- Use **big-picture** runbooks **every turn** to motivate a single question — full order belongs in **README**, **commands/**, and this doc, **not** repeated in dialogue.

## Question-forward elicitation

**Use:** The human is mid-flow (e.g. one council fork, one intake lock, one planning judgment, one coverage dimension). **Your job in that turn is to get the answer** — not to re-teach what **`commands/`**, **`README`**, or a **named skill** does, which **gates** are “still open,” or which **later** artifacts are not produced yet.

**Forbidden in the same message as a simple confirm / single question:**

- Pasting or paraphrasing a **command file** or **skill summary** as a **preface** to the real question.
- **Status essays** (“gates 2–4 open”) unless the user **asked** *where are we?* / *what’s blocking?*
- **Pipeline micro-lectures** before “Confirm or correct: …”

**Allowed:** Minimal context **only** if the question cannot be stated without it (e.g. one line tying to a lock field). If the user wants the full map, they open **reference docs** or ask explicitly.

**No trailing later-stage reminders:** Do **not** end a message with *not ready for … yet*, *that needs … first*, or *gates … still open* — unless the user **explicitly** asked what remains, or **that one fact** is the **immediate** blocker for the **current** answer. **One** crisp **next** action when relevant is OK **without** dragging in unrelated downstream stages.

## No bundled unrelated decisions

**Problem:** One message presents **one** structured prompt (**`AskQuestion`** / numbered choices for **one** fork only) while burying **other mandatory decisions** in prose — or mixes **unrelated** meta-instructions (roadmap, waiver text from another phase) in the same turn.

That violates **`skills/using-forge/SKILL.md`** **Multi-question elicitation** (one primary dimension per message with **blocking** affordances for discrete forks; **no** prose-only *reply with (a)(b)…* for needle-moving fields).

**Required instead:**

- **Sequence:** resolve **one** fork **→** **then** the next — or a single **Confirm/Correct** batch **only** where the active skill allows it.
- **Do not** paste **phase-specific** waiver or ordering copy from a **later** gate while the human is still in an **earlier** skill — see **Phase-specific waivers (example)** below.

**Example (intake):** **task-id** or slug confirmation **must not** be the **only** **`AskQuestion`** while Q9 design authority, Figma locks, and similar **appear only in prose** in the same message — use **sequential** turns per **`intake-interrogate`**.

## Phase-specific waivers (example)

Some products include **manual QA CSV** before **eval YAML**. Instructions about **`csv_baseline_waiver_user_quote`**, “say so explicitly in your own words,” or **YAML-before-CSV** waivers belong **only** where the skill that owns that gate says — e.g. **`skills/qa-write-scenarios/SKILL.md`** **Step 0.0** when that skill is active and the artifact preconditions match.

**Forbidden in assistant chat:**

- Repeating that waiver script during **`qa-prd-analysis`** Step 0.5 (coverage Q1–Q8) — wrong gate.
- “Reminder” paragraphs about recording waiver keys while the human is still answering **earlier** questions — follow dependency order in the active skill.

*(Other products may use different waiver keys; the rule is always: **only** the active skill + this doc define **where** that copy may appear.)*

## Relation to command files

Slash command markdown under `commands/` may describe **full** flows. That is **reference material**. When **guiding** the user step-by-step in the same session, follow the **same** norms as the canonical **Assistant chat** paragraph below — not ad-hoc variants per command.

## Canonical `Assistant chat` paragraph for `commands/*.md`

**Every** file under **`commands/`** must use **this exact** assistant-facing block (optional **one** command-specific sentence *after* it). Keeps behavior consistent across **all** slash commands.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns); **one blocking affordance per unrelated fork** (no bundled prose obligations); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

Rigid skills with **`AskUserQuestion`** should add under **Human input (all hosts):** a **Cross-cutting assistant dialogue** one-liner pointing here + **`using-forge`** items **4–8** (see **`forge-skill-anatomy`**).

## Cursor project rule

`.cursor/rules/forge.mdc` mirrors this for Cursor sessions.
