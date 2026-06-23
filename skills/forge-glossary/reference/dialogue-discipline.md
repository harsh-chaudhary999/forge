# Glossary — Human Input & Dialogue Discipline

Terms governing blocking interactive prompts, per-task product terminology, and the assistant-dialogue rules (one-step horizon, no defensive downstream narration, no bundled decisions, question-forward elicitation).

---

### Blocking interactive prompt

**Definition:** The mechanism that gathers a human answer without advancing until answered — the **`AskUserQuestion`** tool (declared in a skill's **`allowed-tools`**), used for every task-id / doubt / waiver / fork decision instead of a prose-only "reply if…". Canonical convention: **[`skills/_shared/human-input.md`](../../_shared/human-input.md)**.

**Cross-References:** **`using-forge`** (**Interactive human input**, **Stage-local questioning**).

### Product terminology (`terminology.md`) — not this glossary

**Definition:** The **per-task** product term sheet at **`~/forge/brain/prds/<task-id>/terminology.md`** (table of **canonical** names, disallowed variants, **open_doubts** in frontmatter). Authored in **intake** / aligned at **council**; used by **planning**, **QA**, and **assertion** text so **human-facing** copy matches **contracts** and the **PRD lock**.

**Usage context:** This **forge-glossary** skill documents **Forge plugin** and **pipeline** terms only. For **branded** or **product** vocabulary, read **`terminology.md`** and [docs/terminology-review.md](../../../docs/terminology-review.md) — not this file.

**Cross-References:** [intake-interrogate](../../intake-interrogate/SKILL.md), [council-multi-repo-negotiate](../../council-multi-repo-negotiate/SKILL.md), [docs/terminology-review.md](../../../docs/terminology-review.md), [docs/templates/terminology.md](../../../docs/templates/terminology.md).

### One-step horizon (horizon narration)

**Definition:** In **assistant dialogue** (not static README/commands), name **only** the **immediate** next prerequisite, artifact, or skill — or a downstream step when the **current** question truly depends on it, or when the human asked “what comes next.” Do **not** preemptively enumerate full pipelines (council → tech plans → merge → …, or product-specific chains) during intake, council, planning, QA, or other **upstream** gates.

**Usage Context:** Reduces confusion when the user is mid-interrogation and the model front-loads later phases. Complements **Stage-local questioning** in **`using-forge`**.

**What It's NOT:** Not a ban on **documentation** — `README.md`, `commands/forge.md`, and brain templates may list full order. Not “never mention a later stage” — only **don’t** narrate it **before** the user is on that gate without cause.

**Cross-References:** **`using-forge`** (**Horizon narration**, **Multi-question elicitation** item 5). Canonical doc: **`docs/forge-one-step-horizon.md`** — also **No defensive downstream-gate narration (repo-wide)**.

### Defensive downstream-gate narration

**Definition:** Assistant prose whose **primary job** is to explain why a **later** gate or artifact does not exist yet (*semantic manifest isn’t ready yet*, *orphan automation*, pasting a full **State 4b** chain, merge previews) **while** the human is still answering **earlier** phase questions.

**Usage Context:** **Forbidden** as default filler **between** sequential elicitation turns — **any** Forge phase (**intake**, **`qa-prd-analysis`**, council, planning, …). **Allowed:** static **`commands/`** / **`README`** / **`SKILL.md`** tables; **skip-ahead refusal** (first missing prerequisite + next action); user **explicitly** asked *why* or *full order*.

**Cross-References:** **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**; **`using-forge`** **Multi-question elicitation** items **7–8**.

### Bundled unrelated decisions (example: “bundled intake”)

**Definition:** One assistant message uses **one** **blocking interactive** affordance (e.g. **`AskUserQuestion`** for a single fork) while treating **other** needle-moving choices as **prose** *“also answer…”* without their own **blocking** turn — or pastes **phase-specific** waiver/roadmap copy from a **later** gate — or stacks **two different primaries** (e.g. **`Questions`** widget for **task-id** approval **and** a **long markdown** **Q1** checklist in the **same** message). **Intake example:** **task-id** modal while Q9 design authority, net-new vs reuse, or Figma locks appear **only** in prose in the same turn.

**Usage Context:** Violates **`using-forge`** **Multi-question elicitation** item **6**. Correct shape: **one fork per turn** (or a **Confirm/Correct** batch only where the active skill allows).

**Cross-References:** **`docs/forge-one-step-horizon.md`** **No bundled unrelated decisions**; **`commands/intake.md`**; **`intake-interrogate`**.

### Question-forward elicitation (no reference-doc preface mid-answer)

**Definition:** In **live chat**, when the next message’s **job** is to get **one** human answer, the assistant **does not** prefix with what **`commands/`** or **named skills** do, which **gates** are open, or which **later** artifacts do not exist — unless the user **asked** for status. **Does not** paste **defensive downstream-gate** essays between normal Q→Q turns (**forge-one-step-horizon** **No defensive downstream-gate narration**). **Does not** suffix with *not ready for …* / *needs … first* unless that is the **immediate** blocker or the user asked. Reference material stays in **`commands/`** and **README**.

**Cross-References:** **`using-forge`** **Multi-question elicitation** items **7**–**8**; **`docs/forge-one-step-horizon.md`** **Question-forward elicitation** and **No defensive downstream-gate narration (repo-wide)**.
