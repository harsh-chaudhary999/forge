# Product terminology and interactive review

This document is the **v1** norm for **per-task product terminology** (`~/forge/brain/prds/<task-id>/terminology.md`) and for **turn-based** review of that file and of planning artifacts. It applies to the **full** `/forge` / `conductor` path and to **independent** slash-command slices (`/qa`, `/intake`, `/council`, `/plan`, …) that use the same task brain folder. **`docs/terminology-review-protocol.md`** is a **symlink** to this file (stable name for tools/links; **one** canonical body).

## What is what

| Artifact | Purpose |
|----------|---------|
| **[skills/forge-glossary/SKILL.md](../skills/forge-glossary/SKILL.md)** | **Forge** process vocabulary (Council, eval gate, brain, …). |
| **`terminology.md`** (per task) | **Product / domain** entities, roles, metrics, and flags for **one** `task-id`. |

Do not merge the two. In skills and commands, refer to **“product terminology”** or **`terminology.md`** when you mean domain terms.

## File location and template

- **Path:** `~/forge/brain/prds/<task-id>/terminology.md`
- **Template:** [docs/templates/terminology.md](templates/terminology.md)

## Precedence (reducing drift)

1. **Code and wire contracts:** Field names, paths, and event types in **`shared-dev-spec.md`** and **`contracts/*.md`** are authoritative for **implementation**.
2. **Human-facing copy in QA and eval:** Prefer **locked** rows in **`terminology.md`** for customer-visible nouns, button labels, and scenario wording—**after** council renames, **update** `terminology.md` and add a **Revision** row.
3. **`prd-locked.md`:** Success criteria text is authoritative for **scope**; if council **renames** a concept, reflect the final name in `terminology.md`.

## Interactive review protocol (all hosts)

1. **Publish:** Write or update `terminology.md` under the task `qa/` sibling path’s parent (`prds/<task-id>/`). Show a **short excerpt** in chat (table header + 1–2 rows) or the **absolute path** so the transcript is auditable.
2. **Review turn (blocking):** Use **`AskUserQuestion`** / **`AskQuestion`** / **numbered options + stop** per [using-forge](../skills/using-forge/SKILL.md) **Blocking interactive prompts**. **One primary topic per message** for approval—do not bundle unrelated tech-plan or branch decisions in the same turn ([docs/forge-one-step-horizon.md](forge-one-step-horizon.md)).
3. **Merge:** Apply edits to the file; set frontmatter `status: review` or `locked` and `open_doubts: none` when resolved. Unresolved items may go to `planning-doubts.md` (see [forge-brain-layout](../skills/forge-brain-layout/SKILL.md)) with a back-link.

Optional: **PR/MR** review on the brain repo, or **Cursor Canvas** for a one-off snapshot (optional; not required for Forge).

## Planning docs, comments, and checklists

- **Authoritative** task breakdown remains in **`tech-plans/<repo>.md`** (Section 2) and **`planning-doubts.md`** for long Q&A. The brain is an **immutable decision record**, not a generic ticket system—see [forge-brain-layout](../skills/forge-brain-layout/SKILL.md).
- **“Real-time” threaded comments** inside the chat widget are **not** guaranteed; use **structured comment rounds** (batch of bullets → user reply → agent merges into `planning-doubts.md` or a `### Review thread` section in a tech plan).
- **v1 — no `task-progress.md`:** Process “todos” are **Section 2** checklists in each `tech-plans/<repo>.md` plus **`planning-doubts.md`**; do **not** add a second parallel **task tracker** file unless a future decision explicitly adopts one (see **Post-v1 triage** below).

## Entrypoint matrix — commands + slice skills (v1)

**How to read:** **Command** = user-facing `/slash` entry; **Primary skill** = the skill the command invokes (or the skill if invoked without a command). **Review / process** = [Interactive review protocol (all hosts)](#interactive-review-protocol-all-hosts) + [Planning docs, comments, and checklists](#planning-docs-comments-and-checklists).

### Slash commands

| Entry | Primary skill(s) | `terminology.md` | Review / process checklist |
|--------|------------------|--------------------|-----------------------------|
| `/intake` | [intake-interrogate](../skills/intake-interrogate/SKILL.md), [forge-intake-gate](../skills/forge-intake-gate/SKILL.md) | **Create / extend** draft (PRD entities) | Publish → blocking turn → merge; [terminology](templates/terminology.md) + **`planning-doubts.md`** for unresolved threads |
| `/council` | [council-multi-repo-negotiate](../skills/council-multi-repo-negotiate/SKILL.md), [forge-council-gate](../skills/forge-council-gate/SKILL.md) | **Align** with contracts; **no** freeze with **`open_doubts: pending`** when policy says block | User confirm on renames; [forge-council-gate](../skills/forge-council-gate/SKILL.md) red flags |
| `/plan` | [tech-plan-write-per-project](../skills/tech-plan-write-per-project/SKILL.md), [tech-plan-self-review](../skills/tech-plan-self-review/SKILL.md) (review) | **Reference** canonical rows in Section 0/1b/2 | Section 0 **outcomes** in chat, not pasted walls; **Section 2** = bite-sized **todo** list; **HUMAN_SIGNOFF** + [tech-plan-human-signoff](tech-plan-human-signoff.template.md) |
| `/qa` | [qa-pipeline-orchestrate](../skills/qa-pipeline-orchestrate/SKILL.md) (chains downstream) | **Read**; may add terms if analysis finds new entities | **`qa-write-scenarios` Step −1** order; **Phase QA-P7** optional `terminology_*` in run report (see skill); same dialogue norms as [forge-one-step-horizon](forge-one-step-horizon.md) |
| `/qa-write` | [qa-write-scenarios](../skills/qa-write-scenarios/SKILL.md) | **Read** before bulk **`eval/*.yaml`** | **Warn** if missing; canonical **`expected`** strings; see skill Step 0 / 0.1 |
| `/qa-run` | [qa-pipeline-orchestrate](../skills/qa-pipeline-orchestrate/SKILL.md) (from QA-P3) | **Read-only** for labels in reports | **Log DRIFT** if copy conflicts; optional **`terminology_*`** frontmatter in **`qa/qa-run-report-*.md`** (Phase QA-P7) |
| `/build` | (worktree + TDD; no single skill name in command) | **Read** for user-visible strings | N/A — implementation follows tech plan; align copy with term sheet |
| `/eval` | [forge-eval-gate](../skills/forge-eval-gate/SKILL.md) | **Read** when asserting visible copy | N/A — run only; see command text |
| `/heal` | `self-heal-locate-fault` → triage / debug (see **`skills/self-heal-*.md`**) | **Read** on copy/assertion failures | N/A — fix with evidence in brain or repo |
| `/forge` | [conductor-orchestrate](../skills/conductor-orchestrate/SKILL.md) | Full path + **`[TERMINOLOGY]`** at council entry | State 4b QA CSV / eval order per [commands/forge.md](../commands/forge.md) |

### Slice skills (often reached via `/qa` chain)

| Skill | Role | `terminology.md` | Review / process |
|-------|------|------------------|-----------------|
| [qa-pipeline-orchestrate](../skills/qa-pipeline-orchestrate/SKILL.md) | Standalone QA-P1…P7 | **QA-P1** read; **QA-P7** optional report frontmatter | This doc **§ Entrypoint matrix** + `using-forge` **Stage-local questioning**; do **not** **blocking-prompt** CSV/YAML before **`qa-write-scenarios` Step −1** |
| [qa-write-scenarios](../skills/qa-write-scenarios/SKILL.md) | Writes **`eval/*.yaml`** | **Step 0** `cat`; **Step 0.1** table | Step **−1** prerequisite order; [forge-glossary](../skills/forge-glossary/SKILL.md) ≠ product terms |
| [qa-branch-env-prep](../skills/qa-branch-env-prep/SKILL.md) | QA-P3 env / branches | Optional for **manifest** wording | [using-forge](../skills/using-forge/SKILL.md) for **AskUserQuestion** mapping |

**Slice-before-intake / hotfix:** If `terminology.md` is **absent**, **warn** and offer to generate a minimal draft; do not silently invent domain definitions. **`CONTEXT_GAP`** or explicit waiver is acceptable for time-critical paths.

## Post-v1 triage (non-blocking for first ship)

The following are **backlog / optional** — they do **not** block shipping **core** terminology + this protocol in v1:

| Topic | Status |
|-------|--------|
| **Brain “not a task tracker” vs `task-progress.md`** | **Decide in product teams:** v1 uses **Section 2** + **`planning-doubts.md` only** (see [forge-brain-layout](../skills/forge-brain-layout/SKILL.md)). If a team adds **`task-progress.md`**, document it in brain-layout with strict **audit** semantics — not ad hoc daily todos. |
| **`verify_forge_task.py` / CI mandatory `terminology.md`** | **Only if** the team adds **machine-enforced** checks; update [docs/forge-task-verification.md](forge-task-verification.md) and flags — avoid breaking every historical **task** on day one (optional cutover). |
| **[migrations](../skills/migrations/SKILL.md)** | Register **cross-skill breaking** changes to terminology/QA/conductor when you **tighten** gates — not required for the first **documentation + skill text** land. |
| Hooks, seed self-test, §11 “whole project” table | Triage as **follow-up issues** per plan self-review; **not** a v1 merge gate. |

## English-only v1

Product terms in `terminology.md` are **English** unless the PRD is explicitly bilingual; add a **locale** column in a later revision if needed.

## See also

- [docs/tech-plan-human-signoff.template.md](tech-plan-human-signoff.template.md) — may include a terminology checkbox in frontmatter.
- [docs/forge-one-step-horizon.md](forge-one-step-horizon.md) — dialogue norms for review turns.
