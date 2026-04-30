---
name: using-forge
description: "Bootstrap skill — inlined by session-start hook for every Forge-supported host (Claude Code, Cursor, Gemini CLI, JetBrains AI, Codex, Copilot CLI, IDX, Antigravity, OpenCode, etc.)"
type: rigid
version: 1.0.20
preamble-tier: 4
triggers:
  - "how to use forge"
  - "forge bootstrap"
  - "start forge session"
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Using Forge

## Invocation Model

This skill is auto-loaded by the session-start hook. Do not manually invoke it as a task skill; treat it as baseline session policy context.

## Blocking interactive prompts (host mapping — all IDEs)

Rigid skills declare the canonical tool name **`AskUserQuestion`** in **`allowed-tools`** (Claude Code policy + repo lint). **Semantics are host-agnostic:** every supported Forge IDE must obtain human answers through a **blocking interactive prompt** — never prose-only handoffs.

| Host / surface | Use this for discrete choices |
|----------------|-------------------------------|
| **Claude Code** | **`AskUserQuestion`** (matches skill `allowed-tools`) |
| **Cursor** | **`AskQuestion`** — same payload as `AskUserQuestion`; project **`.cursor/rules/forge.mdc`** documents the alias (**do not** mass-rename skills) |
| **Gemini CLI, OpenAI Codex, GitHub Copilot CLI, Google Antigravity, JetBrains AI, Project IDX, OpenCode,** and other hosts **without** a named blocking tool | **Numbered options** in the assistant message **plus stop and wait** — identical semantics to a blocking prompt |
| **Any host** when the blocking UI is unavailable | Same **numbered list** fallback |

**Do not** fork **SKILL.md** files per IDE to rename **`AskUserQuestion`** in prose — hosts map at runtime per this table.

### Interactive human input — project standard (all hosts, all doubts / choices)

**Whenever** the workflow needs something only the human can supply — **question, doubt, confirmation, prioritization, naming (`task-id`), waiver, branch strategy, “what next,” or any fork in the road** — deliver it **interactively** per **Blocking interactive prompts** above, not only as narrative.

**Required pattern:**

1. Prefer the host’s **blocking interactive prompt** (`AskUserQuestion`, `AskQuestion`, or host-native equivalent) with explicit options when the skill allows or the decision fits discrete choices.
2. If none: **numbered options** in the assistant message **plus** **stop and wait**.
3. When more than one human answer is needed across a workflow phase, follow **Multi-question elicitation** below (skill-specific **what** to ask stays in each **`SKILL.md`**). **Exceptions:** verbatim one-shot gates (**`intake-interrogate` Q9** blockquote — still **chat-visible** before relying on **`AskQuestion`** alone).

**Forbidden as the *only* way to decide:**

- Long **“What to do next”** / **runbook** sections (e.g. *pick task-id → /intake → qa-prd-analysis → CSV → /qa-write → …*) that end with *“if you reply with task-id / confirm you’ve started intake…”* **without** a same-turn **blocking interactive prompt** or **numbered list** the user can click or answer in one step. **That is not interactive** — it is documentation disguised as a question. The user did not get **`AskQuestion`**, **`AskUserQuestion`**, or **numbered options + stop**.
- Any **multi-step fork** (continue vs run prerequisite vs waive) presented **only** as prose + “tell me in chat” — **invalid**. Replace with **one** blocking prompt whose options encode those forks (or **numbered list** + stop).
- **Questions only in brain files** or only in a UI surface the user might miss — the **transcript** must show what was asked (**chat-visible**), then the interactive affordance.
- **Rhetorical** “let me know” buried in paragraphs — if an answer changes behavior, it must be **blocking** and **structured**.
- **Horizon narration** — naming **later** pipeline stages (**eval YAML**, **manual CSV**, **council**, **merge**, **dream**, **P4.4**, whole **`/forge`** chain, …) **when they are not** the **immediate** next dependency for what you are doing **now**. That confuses humans (“why are we talking about eval while I’m on Q2?”). **Allowed:** (a) name **only** the **single next** prerequisite or artifact the user must satisfy next; (b) cite a downstream step **only** when the **current** question directly depends on it (rare); (c) if the user **asks** “what happens after.” **Forbidden:** preemptive runbooks in chat **during** intake / QA interrogation / tech-plan rounds unless the skill explicitly requires that disclosure. **Repo-wide standard:** **`docs/forge-one-step-horizon.md`** — especially **No defensive downstream-gate narration (repo-wide)** (no essays justifying later gates **between** normal elicitation turns — **any** phase).

**Required in the same assistant turn as any runbook text:**

1. Right after the shortest necessary context, **`AskQuestion`** / **`AskUserQuestion`** **or** **1–N numbered options** for the **immediate** decision (e.g. *task-id known?* / *run `/intake` vs paste PRD for draft lock?* / *stop*).
2. **Wait** — do not imply the user must free-form reply unless the skill explicitly requires free text **after** a structured choice.

**Allowed:** Explanatory prose **together with** the interactive step (context + blocking prompt / numbered list in the **same** turn). Playbooks in docs/commands stay valid; **agents** still must surface **live** decisions interactively — commands describe workflow; **sessions** must still offer **buttons or numbered choices**.

### Multi-question elicitation — project standard (where + how; all skills)

Use this **whenever** the human must answer **more than one** distinct thing before an artifact can be locked — intake doubts, council forks, tech-plan **Section 0.1** rounds, QA coverage (**`qa-prd-analysis`**), CSV sample approvals, branch/env choices, etc. **Skill files** define **what** to ask; **this section** defines **where** it appears and **how** the dialogue runs.

**Where (visibility):**

- **Transcript-first:** the **assistant message** (markdown) must show **what** is being asked **before** or **with** the interactive affordance — not only a modal, not only `~/forge/brain/` (**chat-visible**). Auditable approval lives in the thread; brain files are the durable record **after** that.
- **Chat vs widget deduplication (same fork — Cursor / `AskQuestion`):** The **long** context (Q4 feature list, Q1 checklist, etc.) belongs **in chat** **once**. **`AskQuestion`** / **Questions** should pass a **short** title + **discrete options** — **not** a **verbatim** second copy of the entire same prompt (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**). Reading the **same** paragraph in **both** panes is invalid UX; **empty** chat + **only** modal still fails transcript-first.

**How (dialogue mechanics — skill-agnostic):**

1. **One primary dimension per assistant message** when multiple questions remain — not Q1–Q8 in one turn. **A single dimension may include a long structured checklist** (e.g. **`qa-prd-analysis` Q1** full test-type menu) — that is still **one** topic; do **not** collapse it to presets-only **without** showing the full menu when the canonical skill template is a checklist (**see `qa-prd-analysis` Q1 HARD-GATE**). **In that same turn, do not** also fire **`AskUserQuestion`** / **`AskQuestion`** / a **Questions** widget for a **different** topic (e.g. **task-id** / **prd-locked** approval while Q1 is in the message body) — **two competing primaries**; **sequence** prerequisite **→** **then** Q1 on the **next** message (**`docs/forge-one-step-horizon.md`** **No bundled unrelated decisions**, Cursor example).
2. **Blocking interactive** for discrete forks: **`AskUserQuestion`** / **`AskQuestion`** / **numbered 1–N + stop** per **Blocking interactive prompts** above.
3. **Reconcile after each reply:** if the answer **already settles** a later planned prompt, **skip** it and **state** *skipped — covered by …*; if the answer **surfaces new doubts**, ask **those** before advancing a rigid checklist.
4. **Forbidden:** dumping **all** prompts for a phase in one message **plus** a **second** unrelated meta-prompt in the same turn; **prose-only** “reply with all answers”; **questions only** in brain files or tool payloads the user never saw in chat.
5. **No downstream roadmap in dialogue:** While eliciting answers for **this** phase, **do not** enumerate later phases (“then **`council-multi-repo-negotiate`**, then tech plans, then merge …”). Same rule as **Stage-local questioning** — **one-step horizon** for the human unless they asked for the big picture.
6. **No bundled unrelated decisions:** Do **not** use **one** **`AskQuestion`** (e.g. task-id **A vs B**) as the **only** blocking affordance while demanding **other** needle-moving answers **only** in **prose** in the **same** message. **Each** discrete fork needs **its own** turn with **`AskQuestion`** / **numbered options + stop**, or **strict sequential** follow-ups — not a prose *“Reply with (a) and (b)…”* wall. **Do not** paste **phase-specific** waiver or ordering copy from a **later** skill’s gate while the human is still in an **earlier** phase — **`docs/forge-one-step-horizon.md`** **No bundled unrelated decisions** and **Phase-specific waivers (example)**.
7. **Question-forward elicitation:** When the **purpose** of the message is to obtain **one** human answer, **do not** prefix with a tutorial on what **`commands/`**, **`README`**, or **named skills** do, which **gates** are open, or which **later** artifacts do not exist yet — and **do not** paste **defensive downstream-gate** essays (*why eval YAML / CSV / merge isn’t ready yet*, full Step −1 chains, *orphan automation*) **between** sequential questions; that norm is **repo-wide** (**`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**). The user is in flow; reference docs are for when they choose to read them. **Exceptions:** user asked for status, “what’s blocking,” or the full order; or you are **refusing** a premature skip-ahead (**first missing** prerequisite + next action). **Norm:** **`docs/forge-one-step-horizon.md`** **Question-forward elicitation**.
8. **No trailing stage reminders:** Do **not** suffix messages with reminders about **later** pipeline stages (*not ready for X*, *needs Y first*) unless the user asked for status or **that one fact** is the **immediate** blocker for the **current** question — same distraction as a prefix (**`docs/forge-one-step-horizon.md`** **Question-forward elicitation**, trailing-reminder bullet).

This pattern is **not** QA-specific — it applies on **every** Forge-supported IDE.

### QA PRD analysis (`qa-prd-analysis` Step 0.5) — specialization

**Implements** **Multi-question elicitation** for **coverage** dimensions (templates **Q1–Q8**). **Canonical detail:** `skills/qa-prd-analysis/SKILL.md` **Step 0.5**.

- Same **where / how** as above; plus **forbidden** in this phase: full Q1–Q8 wall in one message; **Q1 in markdown + unrelated `AskQuestion`** (e.g. task-id / **prd-locked** approve) in the **same** turn — **dual prompt** (**`docs/forge-one-step-horizon.md`**); **full Qn text in chat + identical full Qn in `AskQuestion`** — **deduplicate** (**short** widget title + options **only**); “single bulk / approve all” shortcuts; **CSV / eval-YAML-only waiver** choices (**wrong gate** — use **`qa-write-scenarios`** / **`qa-manual-test-cases-from-prd`** **after** `qa-analysis.md`). **Q1** must show the **full** test-type checklist (not preset-only **Full/Lean** — see **`qa-prd-analysis`** Q1 **HARD-GATE**).

**Downstream references** to “Step 0.5” or “real interrogation” mean: **`qa-analysis.md`** after **Multi-question elicitation** completed for coverage — **`qa-write-scenarios`**, **`qa-manual-test-cases-from-prd`**, **`qa-pipeline-orchestrate`**, **`conductor-orchestrate`**, **`eval-scenario-format`**.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, you absolutely must invoke it. This is not negotiable.

## Automation ≠ assumption / human loop at needle-moving decisions

Forge **automates** repeatable work: structured artifacts under **`~/forge/brain/`**, eval YAML shape, scans, verification CLIs, coordinated phases. It **does not** grant permission to **guess** scope, design authority, waivers, prioritization, or “confirmed” interrogation answers.

**Needle-moving decisions** — anything that would change what ships, what is tested, what is locked, or what the human thinks they approved — require an **explicit human turn** via **blocking interactive prompts** (host mapping above) or **numbered list + wait** — see **Interactive human input** and **Multi-question elicitation** above. Examples: intake locks, council conflict resolution, **`qa-prd-analysis`** Step 0.5 (**Multi-question elicitation** for Q1–Q8 — see **`qa-prd-analysis`**), cutting surfaces or test types, signing off samples/count for **`manual-test-cases.csv`**. **YAML-before-manual-CSV** waiver (**verbatim quote** in **`qa-analysis.md`**): **`qa-write-scenarios`** **Step 0.0** **only** — **never** paste that waiver script during **`qa-prd-analysis`** coverage rounds (**`docs/forge-one-step-horizon.md`**).

**Forbidden:** Filling frontmatter or brain files with “confirmed,” waivers, or design sources **inferred** from Confluence/PRD/Figma metadata **without** the user having answered or approved in this workflow. **Verbose automation without that loop is worse than slow manual review** — it ships false confidence.

### Stage-local questioning — respect process order (not YAML-specific)

This applies to **every** Forge phase (intake, council, tech plans, QA, eval, PR set, …), not only automation artifacts.

1. **Know where you are.** Before any **blocking interactive prompt** or heavy prompting, infer the task’s **current stage**: brain paths (`prd-locked.md`, `shared-dev-spec.md`, `tech-plans/`, `qa/`, `eval/`, `conductor.log` tail). If there is **no** started task or **no** lock yet, you are **not** in downstream phases — treat later topics as **out of scope** until prerequisites exist.

2. **Ask only what unblocks *this* stage.** Questions must be **stage-relevant**: they resolve ambiguity or supply inputs needed to **start or finish the phase you are actually in** (or the single **next** prerequisite in documented order). **Forbidden:** Opening with choices about **later** pipeline stages — merge order, eval drivers, council contract picks, tech-plan sign-off, QA CSV sample approval, design ingest — while upstream work is **still missing** or the pipeline **has not started**. That wastes the user’s time and signals you ignored dependency order.

3. **First gap wins.** If several prerequisites are missing, surface and fix the **earliest** failure in dependency order (per **`conductor-orchestrate`**, the active skill, or **`qa-write-scenarios`** **Step −1** for the QA→eval slice). Do not **jump ahead** to “how should we proceed on step 5?” when steps **1–4** are not satisfied.

4. **Same rule for waivers and exceptions:** Do not use a **blocking interactive prompt** about waiving or reordering **downstream** gates while **upstream** gates are still open — secure the **current** stage first; only then discuss exceptions relevant to the **next** stage.

**Why:** The user should not be interrogated about Phase **N+k** while Phase **N** prerequisites are pending. Maintain **respect** for sequential process: one coherent stage at a time.

5. **Speak only the immediate next dependency.** In **assistant messages** (not static README/docs), **do not** mention downstream process steps unless **(i)** they are the **very next** artifact/skill after the current step, **(ii)** the **current** prompt cannot be answered without naming them, or **(iii)** the user explicitly asked what comes later. Listing **`eval/*.yaml`**, CSV waivers, merge order, PR set, etc. **before** the user is on that gate **confuses** and reads like pressure — **forbidden**.

**Multi-question elicitation** is the **project-standard envelope** for **any** sequence of human answers; skills add **what** to ask and **exceptions** (e.g. **`intake-interrogate` Q9** verbatim blockquote). Skipping **transcript-visible** questioning invalidates those gates.

### Coupling, prerequisites, and alternatives (what breaks vs what helps)

This is **not** “everything depends on everything.” Separate **hard prerequisites** from **quality boosters**.

| Relationship | Meaning |
|--------------|---------|
| **Tightly coupled (hard for automation)** | Anything that must live **on disk under `~/forge/brain/`** for skills and subagents to read — especially **`prd-locked.md`**, **`qa/qa-analysis.md`**, and **`manual-test-cases.csv`** (or documented waiver) **before** bulk **`eval/*.yaml`** per **`qa-write-scenarios`** **Step −1**. Chat and external wiki URLs **alone** are not substitutes; **brain files are the transport layer.** |
| **Loosely coupled (recommended, not Step −1 blockers for `/qa-write`)** | **Council**, **`shared-dev-spec.md`**, **tech plans** — they make scenarios **precise** (routes, contracts, task IDs) but are **not** required to *start* the QA analysis → CSV → YAML chain if **`prd-locked`** + **`qa-prd-analysis`** can run. |
| **Full pipeline only** | **`/forge`**, **State 4b ordering**, **merge** — orthogonal to “I only want scenarios in brain this week.” |

**When the human can’t or won’t run the “primary” step (e.g. `/intake`):** do **not** treat the pipeline as all-or-nothing. Use a **blocking interactive prompt** to pick an **alternative** that still produces a real brain artifact with **human approval** — e.g. user **pastes** PRD/wiki sections → you **draft** **`prd-locked.md`** for review → user confirms → **Write** to brain. Or user **confirms** copying a prior task’s lock if scope is identical. **Invalid:** inventing `prd-locked` without a human-visible approval path, or claiming “wiki is enough” with **no** file under **`prds/<task-id>/`**.

**Auto-chaining** one command into the next (run intake, then auto-run QA) is **not** default — the human chooses commands — but **recommending** the next prerequisite after confirmation **is** correct.

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, user direct requests) — highest priority
2. **Forge skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

## Information transport (parallel agents, minimal human back-and-forth)

Council and subagents **do not** share your live chat. They only see **what is written** under `~/forge/brain/` (e.g. `prd-locked.md`, `shared-dev-spec.md`). The **first** human pass on a PRD should therefore pack **maximum durable signal**: repos, contracts, rollback — and for web/app, the intake **Design / UI** lock (**Q9**: `design_new_work`, plus **implementable** inputs: **`design_brain_paths`** under `~/forge/brain/prds/<task-id>/design/` and/or **`lovable_github_repo`** (+ pinned ref) for **Lovable → GitHub** UI per **`docs/platforms/lovable.md`**, and/or **`figma_file_key` + `figma_root_node_ids`** for MCP/REST — not wiki-only or bare Figma/Lovable URLs). Prefer **Figma MCP** (when available) to pull nodes and save `design/MCP_INGEST.md`. If new design exists but nothing is on disk in brain, autonomous reasoning will **not** discover it; you will get invented UI or stalled gates. **Chat is not the transport layer; the brain files are.**

**Non-negotiable for agents:** (1) When web/app/user-visible UI is in scope, **never complete intake** without the user having seen the **verbatim blockquote** design-source-of-truth question from **`intake-interrogate` Q9** in an assistant message (you may add PRD summary + “confirm” after it — you may **not** infer from the PRD alone and skip showing that line). (2) **Never open Phase 4.1 / dispatch feature implementation** until **`[P4.0-EVAL-YAML]`** is logged with **at least one** scenario file under `~/forge/brain/prds/<task-id>/eval/` and **`[P4.0-TDD-RED]`** per policy — see **`conductor-orchestrate` State 4b**. (3) Require **`[P4.0-QA-CSV]`** after approved **`qa/manual-test-cases.csv`** when **`forge_qa_csv_before_eval: true`** in **`product.md`** **or** when the user invoked **full `/forge`** (`commands/forge.md`) — same acceptance alignment for **TDD** and **eval**; see **`qa-manual-test-cases-from-prd`**. Procedural text is not a CI bot: **you** must refuse to skip these steps.

**Optional machine layer (teams):** Run **`python3 tools/verify_forge_task.py --task-id <id> --brain ~/forge/brain`** in CI or pre-push on the **brain** repo so missing **`eval/*.yaml`** or bad **`conductor.log`** ordering fails the build — see **`docs/forge-task-verification.md`**. Add **`pip install -r tools/verify/requirements-verify.txt`** then **`--validate-eval-yaml`** so CI rejects malformed or empty-`expected` scenarios, not only “≥1 yaml file exists.” Use **`--strict-tech-plans`** once **`tech-plans/*.md`** exist to fail **`REVIEW_PASS`** without FORGE-GATE Section 0c / recross anchors or misplaced **`### 1b.2a`** (**`tools/verify_tech_plans.py`**). Enable **`--check-shared-spec`** (frozen shared spec checklist + TBD scan) and **`--validate-phase-ledger`** / **`--phase-ledger-verify-hashes`** when you use **`phase-ledger.jsonl`** (see **`tools/append_phase_ledger.py`**). The tool also **warns on stderr** when several **`prds/*/conductor.log`** files exist — keep **`FORGE_TASK_ID`** set in CI and locally so hooks and warnings align with the active task. Use **`--strict-single-task-brain`** in CI when exactly one active task is guaranteed. **`tools/forge_drift_check.py`** compares **Success Criteria** bullets to eval/QA text for obvious drift. On the **Forge** repo, CI runs **`tools/lint_skill_allowed_tools.py`** so rigid skills keep **`allowed-tools`** and **`tools/dev/skill-tool-policy.json`** stays in sync (**`pre-tool-use.cjs`** loads **`tools/dev/`** first, with legacy fallback **`tools/skill-tool-policy.json`**). Forge **`tools/`** is grouped (**`verify/`**, **`scan/`**, **`dev/`**, **`ops/`**, **`js/`**); stable **`python3 tools/<name>.py`** paths at the **`tools/`** root are thin shims — see **`tools/README.md`**. **`FORGE_BRAIN`** and **`FORGE_BRAIN_PATH`** are both accepted as the brain root for Python CLIs and hooks. The IDE still does not compile-check sessions; this checks **committed** artifacts.

**Session style (all hosts):** Forge cannot toggle your editor’s **planning vs execution** mode (or permissions) programmatically. Convention: **planning-style** for intake, council, and tech-plan **review**; **execution-style** for build, eval, heal. Instruct the user to switch style or permissions when the Forge phase changes — see **`docs/platforms/session-modes-forge.md`** (each platform doc links the same rules to local UI names).

## Agent reliability (diversion, hallucination, context collapse)

1. **Pin the task** — If more than one `prds/*/conductor.log` exists under the brain, set **`FORGE_TASK_ID`** (or **`FORGE_PRD_TASK_ID`**) before relying on stage injection or “next gate” hints; otherwise the hook may pick the **wrong** log by mtime.
2. **Brain over chat** — Subagents and later sessions **do not** see this chat. **Decisions, scope changes, and URLs** must land under **`~/forge/brain/prds/<task-id>/`** (and related paths). If it is only in chat, assume it **will be lost** or **hallucinated** later.
2b. **Written evidence (what / where / how)** — Anything you write for humans or subagents (plan digests, scan summaries, QA notes, eval rationales, test descriptions) must be **checkable**: **what** (path, id, symbol), **where** (repo or brain path), **how** (command + cwd, `Read`/`rg`, artifact field). Headline counts and **"N+"** scale without identifiers violate **AGENTS.md** — *Written artifacts — precision*; counts are optional, not a substitute for paths.
2c. **Volume is not a skip lever** — Multi‑thousand‑line files, full export extractions, or large brain writes are **not** blockers you may self‑waive. **Execute every required step** (batched `Read`, incremental `Write`, streaming Shell). Only **BLOCKED** (with evidence) or the **explicit** stop rules **inside the invoked skill** can halt work — not “too large” as a discretionary excuse (**AGENTS.md** Core rule **6**).
3. **Re-anchor after compact / clear** — After context compaction or a new session, **read** `prd-locked.md`, `shared-dev-spec.md` (if present), and the **tail** of `conductor.log` before big moves. Ask the human to restate **goal + non-negotiables** in one message if anything is ambiguous.
4. **One objective per thread** — Vague “keep going” invites the wrong skill path (e.g. council when the user wanted a bugfix). State **what** and **what not to touch**.
5. **Stubs are not specs** — Scan output and `modules/*.md` stubs are **hypotheses**. Confirm behavior with **real source**, APIs, or tests before implementing.
6. **Subagent handoff** — When dispatching work that will not see this chat, write a **short handoff file** under the task brain (what was decided, what to do, links) so the parent does not **collapse** child context into a wrong summary.

**Claude Code `session-start` hook (stage + preamble):** Optional env vars (export in shell or IDE env before launching Claude):

| Variable | Purpose |
|----------|---------|
| **`FORGE_TASK_ID`** or **`FORGE_PRD_TASK_ID`** | Use **`~/forge/brain/prds/<id>/conductor.log`** for stage detection. **Recommended** when multiple tasks exist; otherwise the hook picks the **newest mtime** among `prds/*/conductor.log`, which can be the wrong task. |
| **`FORGE_BRAIN`** or **`FORGE_BRAIN_PATH`** | Brain root if not **`~/forge/brain`** (either name; same semantics). |
| **`FORGE_PREAMBLE_TIER`** | `1`–`4`: which **`skills/_preamble/tier-N.md`** is prepended (default **`2`**). |
| **`FORGE_HOOKS_DEBUG=1`** | Log conductor.log path + resolved stage to stderr (hook diagnostics). |
| **`FORGE_DISABLE_CANARY=1`** | Skip writing **`~/.forge/.canary`** and skip canary-in-command checks in **`pre-tool-use`** (trusted local only). |

Stage resolution uses the **last** `[P…]` marker in the chosen log; implementation: **`.claude/hooks/forge-stage-detect.cjs`**. Run **`node .claude/hooks/test-forge-stage-detect.cjs`** (from repo root) to verify mapping after edits.

## Anti-Pattern Enforcement (HARD-GATE)

### Anti-Pattern 1: "This is a simple question, I don't need a skill"

**Why This Fails:**
Simple feels deceptive. You assume you understand scope, but the skill catalog surfaces edge cases you didn't anticipate. Small tasks hide correctness gaps that compound downstream.

**Enforcement (MUST):**
1. MUST check skill catalog before proceeding
2. MUST read edge case section of any potentially applicable skill
3. MUST verify no skill requires pre-work (e.g., brain-read before eval-*)
4. MUST follow skill discipline even for 1-line tasks
5. MUST reject the rationalization "I'll skip this one time"

---

### Anti-Pattern 2: "I need more context before I can pick a skill"

**Why This Fails:**
Skills provide the context-gathering process itself. Waiting for clarity before invoking a skill means you skip the intake or intake-interrogate phase. Skills are designed to surface context gaps, not assume they're pre-filled.

**Enforcement (MUST):**
1. MUST invoke the process skill (intake, intake-interrogate, brain-read) FIRST
2. MUST let the skill ask questions; don't pre-answer
3. MUST allow the skill to surface hidden context dependencies
4. MUST NOT invent context from memory and skip skill invocation
5. MUST escalate NEEDS_CONTEXT if skill reveals missing information

---

### Anti-Pattern 3: "I know this skill's content from memory"

**Why This Fails:**
Skills evolve. Your memory is stale from context collapse or prior session. The skill may have new enforcement gates, edge cases, or dependency chains. Running old logic from memory causes silent failures.

**Enforcement (MUST):**
1. MUST always read current skill file, never rely on memory alone
2. MUST check the skill's requires field for dependencies
3. MUST verify no HARD-GATE changes since last session
4. MUST re-read edge cases even if you've seen the skill before
5. MUST treat memory as a hint, not truth; let the skill be authoritative

---

### Anti-Pattern 4: "Multiple skills apply, I'll pick one and infer the rest"

**Why This Fails:**
Each skill has a priority order. Picking one arbitrarily and inferring the rest causes gaps. forge-eval-gate and forge-council-gate both apply to PRDs — but council must run BEFORE eval. Skipping one leaves your work unchecked.

**Enforcement (MUST):**
1. MUST invoke all applicable skills in priority order (process → implementation → reference)
2. MUST NOT skip a skill because you think you understand its output
3. MUST NOT infer skill behavior from a prior skill's result
4. MUST trace skill dependencies via the requires field
5. MUST explicitly report if a skill is deliberately omitted and why

---

### Anti-Pattern 5: "The user just wants a quick answer"

**Why This Fails:**
Quick answers that skip skills cause correctness failures. These failures are then discovered in eval or production, turning a 2-minute skill invocation into a 2-hour debugging session. Skill invocation IS the faster path long-term.

**Enforcement (MUST):**
1. MUST run the skill even if user asks for speed
2. MUST show user the skill output, not a summarized guess
3. MUST explain why the skill is necessary (e.g., "eval catches 60% of bugs")
4. MUST NOT override skill requirement for speed; user preference = override only for explicit exceptions
5. MUST log the exception if user explicitly waives skill invocation

## Edge Cases

### Edge Case 1: Skill Not Found in Catalog

**Symptom:**
Skill tool returns "not found" or skill is referenced but doesn't exist in `~/forge/skills/`.

**Do NOT:**
Invent behavior from memory. Proceed as if a missing skill is equivalent to running it.

**Action:**
1. Check using-forge skill catalog (this file, "Where Things Live")
2. Search for nearest skill by name prefix or similar function
3. Report the gap: "Skill X missing from catalog"
4. Identify workaround or escalate

**Escalation:**
`NEEDS_CONTEXT` — Forge skill catalog incomplete

---

### Edge Case 2: Two Skills Both Apply

**Symptom:**
forge-eval-gate and eval-coordinate-multi-surface both seem relevant. forge-council-gate and reasoning-as-web-frontend overlap. Ambiguous ordering.

**Do NOT:**
Pick one arbitrarily. Assume one subsumes the other.

**Action:**
1. Check skill requires field — one may depend on the other
2. Invoke process skill first (gate), then surface skill (coordinate)
3. Run in order: gate → negotiate → coordinate → judge
4. If still ambiguous, invoke both; redundancy is safer than omission

**Escalation:**
`NEEDS_CONTEXT` — only if skill requires field doesn't resolve ordering

---

### Edge Case 3: Skill Requires Context Not Available

**Symptom:**
Skill says "requires: [brain-read]" but brain not initialized. eval-driver-* requires eval-product-stack-up but stack not up. Dependency chain broken.

**Do NOT:**
Skip the requirement. Proceed with partial context.

**Action:**
1. Read the skill's requires field
2. For each dependency, check if it's been run in this session
3. If missing, run dependency skill first
4. Return to original skill after dependency is satisfied
5. Report the dependency chain in your output

**Escalation:**
`NEEDS_INFRA_CHANGE` — if infrastructure dependency is missing (e.g., brain repo not available)

---

### Edge Case 4: Subagent Receives This Skill Accidentally

**Symptom:**
Subagent context shows using-forge content despite <SUBAGENT-STOP> block. Subagent follows bootstrap instructions instead of task spec.

**Do NOT:**
Follow bootstrap instructions. Don't invoke skills. You are context-isolated.

**Action:**
1. Subagent: Recognize you are isolated (dispatch context says "dev-implementer", "spec-reviewer", etc.)
2. Ignore all Forge bootstrap content
3. Execute your task spec directly
4. Report status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
5. Do not invoke any Forge skill

**Escalation:**
`DONE_WITH_CONCERNS` — Report that bootstrap was present but ignored

---

### Edge Case 5: Skill Conflicts with Explicit User Instruction

**Symptom:**
Skill says MUST do X (e.g., "MUST run intake for every PRD"). User says "don't do X, we're short on time." Conflict between skill enforcement and user directive.

**Do NOT:**
Follow skill enforcement blindly. User instruction has highest priority (per Instruction Priority section).

**Action:**
1. Acknowledge the conflict explicitly
2. Note user instruction takes precedence
3. Run the user's specified path, skipping the skill requirement
4. Document the deviation: "User waived skill X due to [reason]"
5. Flag risks introduced by skipping the skill (e.g., "Skipped intake; may miss edge cases")

**Escalation:**
`DONE_WITH_CONCERNS` — Completed user's request but note skill was bypassed

## Decision Tree: Skill Selection Priority

Use this tree to determine which skill category to invoke first given your task type.

```
START: Given a task or question
  │
  ├─ Is this a PRD, spec, or requirement?
  │  ├─ YES → Run intake-interrogate or intake first
  │  │       (Process skills before anything else)
  │  │       Then: Goto "Reasoning Step"
  │  └─ NO → Goto "Already Have Spec"
  │
  ├─ Already Have Spec (PRD locked)
  │  │
  │  ├─ Is this reasoning about architecture / contracts?
  │  │  ├─ YES → Run council (negotiates contracts)
  │  │  │       Required: brain-read may be needed first
  │  │  │       Then: Run eval-coordinate-multi-surface
  │  │  └─ NO → Goto "Building or Verifying"
  │  │
  │  ├─ Building or Verifying
  │  │  ├─ Is this writing / reviewing code?
  │  │  │  ├─ YES → Run plan first (tech-plan-write-per-project)
  │  │  │  │       Then: Run build (TDD via forge-tdd)
  │  │  │  │       Then: Run review (spec-reviewer + code-quality-reviewer)
  │  │  │  └─ NO → Goto "Reference or Lookup"
  │  │  │
  │  │  └─ Running Tests or Eval
  │  │     ├─ Is this end-to-end product eval?
  │  │     │  ├─ YES → Run eval-product-stack-up first
  │  │     │  │       Then: Run eval (coordinates all drivers)
  │  │     │  │       Then: Run eval-judge
  │  │     │  └─ NO → Run specific eval-driver-*
  │  │
  │  └─ Reference or Lookup
  │     ├─ Looking up decisions / brain?
  │     │  ├─ YES → Run brain-read
  │     │  │       If tracing decision: brain-why
  │     │  │       If recording decision: brain-write
  │     │  └─ NO → Generic forge skill?
  │     │
  │     └─ Check forge-glossary or status
  │        Run forge-status for pipeline state
  │
  └─ DONE: Invoke identified skill(s) in order
```

**Priority Rule:**
Process (intake/council) → Implementation (plan/build/review) → Reference (brain/glossary)

**Key Check:**
If two skills apply and order is ambiguous, check the `requires` field in both skill files. The skill with no requires often runs first.

## Iron Law

```
WHEN THERE IS A 1% CHANCE A SKILL APPLIES, INVOKE IT BEFORE ANY RESPONSE. PROCESS SKILLS FIRST. IMPLEMENTATION SKILLS SECOND. SUBAGENTS EXECUTE THEIR TASK AND REPORT STATUS — THEY DO NOT RE-RUN THE BOOTSTRAP.
```

## Where Things Live

- **Brain:** `~/forge/brain/` (git repo, source of truth)
- **Product config:** `~/forge/brain/products/<slug>/product.md` (repos, roles, infra)
- **Codebase scan:** `~/forge/brain/products/<slug>/codebase/` (module map, patterns, API surface)
- **Manual QA baseline (CSV):** `~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv` — skills **`qa-prd-analysis`** then **`qa-manual-test-cases-from-prd`** (not a slash command). Same folder: **`qa-analysis.md`**, **`TEST_SUITE_REPORT.md`** when used.
- **Automated eval (YAML):** `~/forge/brain/prds/<task-id>/eval/*.yaml` — for driver execution; generated by **`qa-write-scenarios`** via **`/qa-write`** or **`/qa`**. **`scenarios-manifest.md`**, **`branch-env-manifest.md`**, **`qa-run-report-<ts>.md`** come from the standalone eval pipeline (**`/qa`**, **`/qa-write`**, **`/qa-run`**).
- **Skills:** `~/.claude/skills/<skill-name>/SKILL.md`
- **Subagents:** `~/.claude/agents/<agent-name>.md`

## Onboarding an Existing Project

If you are starting Forge on a **codebase that already exists** (not greenfield):

1. Run `/workspace` to register repos and create `product.md` — scan runs automatically
2. If scan was skipped or is stale, run `/scan <slug>` before council
3. `product-context-load` will warn you if the scan is absent or >7 days old
4. `forge-council-gate` will check scan freshness before each council session

The codebase scan gives surface agents architecture context they cannot derive from the PRD alone. Skipping it means council will produce tech plans that may conflict with the existing structure.

**Scan staleness rule:** <7 days = fresh. 7-30 days = warn. >30 days = prompt to refresh before council.

## Brain-first routing (then open product sources)

When deciding **where** in a product repo work belongs — council arguments, tech-plan file lists, eval targets, or exploratory reads before a plan exists — **use the brain codebase scan first**, then open repo files.

1. **Read** `~/forge/brain/products/<slug>/codebase/index.md`, `SCAN.json`, and relevant `codebase/modules/*.md`, `api-surface.md`, `patterns.md` as needed.
2. **From that**, extract real paths and module boundaries (Tier‑1 hubs, dependents).
3. **Only then** open paths under the cloned repos for deeper reads or edits.

Do **not** replace step 1–2 with ad‑hoc `find` / tree walks / “let me explore the Android app” through source when scan data exists and is fresh. If scan is missing or stale, run **`/scan <slug>`** (or refresh) before inventing filenames. The scan runner already walked the tree; the LLM’s job is to **route** from brain output, not rediscover structure from scratch.

## Subagent STOP

If you are a dispatched subagent (dev-implementer, spec-reviewer, code-quality-reviewer, dreamer):

<SUBAGENT-STOP>
Skip the bootstrap. You are isolated. Execute your task. Report your status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.
</SUBAGENT-STOP>

## Skills Priority

Process skills first (intake, conductor), then implementation skills (council, eval).

## Four Subagents (Locked)

1. **dev-implementer** — Context-isolated builder. TDD. Self-reviews. Commits.
2. **spec-reviewer** — Skeptical adversary. Reads code. Verifies spec compliance.
3. **code-quality-reviewer** — Code quality, patterns, naming, test quality.
4. **dreamer** — Inline conflict resolution + retrospective scoring.

Everything else is skills.

## Checklist

Before responding to any user message:

- [ ] Checked if any skill applies (even at 1% probability)
- [ ] Process skills invoked before implementation skills
- [ ] Skill file read fresh — not relying on memory
- [ ] All applicable skills in requires chain satisfied before invoking target skill
- [ ] If subagent: bootstrap instructions ignored, task spec executed directly
- [ ] If user waived a skill: deviation documented and risks flagged
