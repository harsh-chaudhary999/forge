---
name: forge-glossary
description: "WHEN: You encounter an unfamiliar Forge term and need its canonical definition."
type: reference
version: version: 1.0.15
preamble-tier: 1
triggers:
  - "what does X mean"
  - "forge glossary"
  - "define forge term"
  - "forge terminology"
  - "product terminology"
  - "terminology.md"
  - "per-task terminology"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---
# Forge Glossary

The canonical catalog of **Forge plugin** and **pipeline** terms — the single source of truth for naming and definition of every Forge process concept (pipeline stages, artifacts, subagents, decision tokens, eval classifications, conductor markers).

## How to use this glossary

1. **Find the group** in the index below that owns the term you are looking up, then **Read** that reference file. Each `reference/*.md` holds the full `### Term` entries (Definition / Usage Context / What It's NOT / Cross-References) **verbatim** — load on demand.
2. **The glossary is authoritative for naming and definition.** The **source skill** (`<name>/SKILL.md`) is always authoritative for **behavior**. If they conflict on the **name** of a concept, the glossary wins; if they conflict on **behavior**, the skill wins (see Edge Case 2).
3. This skill documents **Forge** terms only. For **branded** or **product** vocabulary, read the per-task `terminology.md` — not this file (see *Product terminology* in [`reference/dialogue-discipline.md`](reference/dialogue-discipline.md)).
4. Optional disambiguation via **`AskUserQuestion`** (**`allowed-tools`**) — see *Blocking interactive prompt* in [`reference/dialogue-discipline.md`](reference/dialogue-discipline.md) and the convention in [`skills/_shared/human-input.md`](../_shared/human-input.md).

## Iron Law

> **Never invent a definition.** If a term is in this glossary, use the canonical entry verbatim. If a term is **not** here, do not silently treat it as undefined and do not propagate it into brain decisions — grep `skills/` and `agents/` for canonical usage, derive from context, or escalate `NEEDS_CONTEXT` (see Edge Case 3). The glossary is git-backed and immutable in meaning; entries evolve through dreamer retrospectives but a definition is never guessed.

## Index — term groups (each links to its reference file)

| Group | Reference file | Terms covered |
|---|---|---|
| **Human input & dialogue discipline** | [`reference/dialogue-discipline.md`](reference/dialogue-discipline.md) | Blocking interactive prompt; Product terminology (`terminology.md`) — not this glossary; One-step horizon (horizon narration); Defensive downstream-gate narration; Bundled unrelated decisions; Question-forward elicitation |
| **Pipeline stages** | [`reference/pipeline-stages.md`](reference/pipeline-stages.md) | Intake; Council; Spec Freeze; Tech Plan; Build; Eval; Self-Heal; Review; Dream; PR Set |
| **Eval artifacts, conductor markers, classifications & verdicts** | [`reference/eval-and-conductor-markers.md`](reference/eval-and-conductor-markers.md) | Semantic eval path; semantic-automation.csv; semantic-eval-manifest.json; semantic-csv-eval (`kind`); `[P4.0-QA-CSV]`; `[P4.0-SEMANTIC-EVAL]`; `[P4.0-TDD-RED]`; `[P4.2-DESIGN-PARITY]`; RED_INFRA; CONTEXT_GAP; BLOCKED_DEPENDENCY; Eval Verdicts table |
| **Core concepts** | [`reference/core-concepts.md`](reference/core-concepts.md) | shared-dev-spec.md; forge-product.md; worktree-per-project-per-task (D30); Brain Directory Structure; prd-locked.md; terminology.md; Skill; Rigid Skill; Flexible Skill; Red Flag; Anti-Pattern; HARD-GATE; Superpowers; Phase; Batch; P0/P1/P2/P3; Seed Product; Surface; Discipline; Contract; Driver; Escalation |
| **Subagents, status codes & preamble-tier** | [`reference/subagents-and-roles.md`](reference/subagents-and-roles.md) | dev-implementer; spec-reviewer; code-quality-reviewer; dreamer; Subagent Status Codes table; preamble-tier; design_new_work |
| **Decision references (D1–D30)** | [`reference/decisions.md`](reference/decisions.md) | D5; D13; D14; D15; D24; D25; D30 (externally visible locked decisions) |

---

## Quick Reference: Pipeline Flow

1. **Intake** (HARD-GATE) → lock PRD
2. **Council** (HARD-GATE) → negotiate contracts, produce shared-dev-spec
3. **Spec Freeze** → lock shared-dev-spec
4. **Tech Plan** → break spec into per-project tasks
5. **Build** (HARD-GATE: TDD) → dev-implementer executes tasks
6. **Review** (two-stage: spec + quality) → spec-reviewer, code-quality-reviewer
7. **PR Set** → coordinate PRs across repos in merge order
8. **Eval** (HARD-GATE) → multi-driver product test
9. **Self-Heal** (if RED) → locate fault, triage, fix, re-test (max 3 retries)
10. **Dream** → retrospective, learnings to brain

---

## Quick Reference: Key Skills by Category

**HARD-GATE Skills:**
`forge-intake-gate`, `forge-council-gate`, `forge-eval-gate`, `forge-tdd`, `forge-worktree-gate`, `forge-trust-code`, `forge-verification`, `forge-letter-spirit`

**Reasoning Skills (Council):**
`reasoning-as-backend`, `reasoning-as-web-frontend`, `reasoning-as-app-frontend`, `reasoning-as-infra`

**Contract Skills (Council):**
`contract-api-rest`, `contract-event-bus`, `contract-cache`, `contract-schema-db`, `contract-search`

**Eval Drivers:**
`eval-driver-api-http`, `eval-driver-db-mysql`, `eval-driver-cache-redis`, `eval-driver-bus-kafka`, `eval-driver-search-es`, `eval-driver-web-cdp`, `eval-driver-ios-xctest`, `eval-driver-android-adb`

**Deploy Drivers:**
`deploy-driver-pm2-ssh`, `deploy-driver-docker-compose`, `deploy-driver-local-process`, `deploy-driver-systemd`

**Brain Skills:**
`brain-read`, `brain-write`, `brain-recall`, `brain-why`, `brain-forget`, `brain-link`

**Self-Heal Skills:**
`self-heal-locate-fault`, `self-heal-triage`, `self-heal-systematic-debug`, `self-heal-loop-cap`

---

## Edge Cases

### Edge Case 1: Term Used with a Different Meaning Outside Forge

**Symptom:** A user asks about "council" expecting a human committee or a governance process, not the Forge contract-negotiation phase between domain reasoning surfaces.

**Do NOT:** Explain the Forge term without acknowledging the ambiguity.

**Action:** When a term from the glossary collides with a common industry term (Council, Surface, Driver, Dream, Conductor), clarify the Forge-specific meaning upfront: "In Forge, 'Council' refers to the multi-surface contract negotiation phase — not a human committee. It's executed by 4 AI reasoning surfaces negotiating 5 service contracts."

**Escalation:** If the user's intent is genuinely unclear (asking about a human council process vs. the Forge phase), ask once: "Do you mean the Forge council phase, or are you asking about a governance process outside Forge?"

---

### Edge Case 2: Term Appears in Brain Files or SKILL.md with Slightly Different Phrasing

**Symptom:** A brain decision file says "negotiation round" where this glossary says "Council." A skill says "triage phase" where the glossary says "Self-Heal Triage." The user asks which is authoritative.

**Do NOT:** Guess or arbitrarily prefer the glossary over the source file.

**Action:** The source skill (`self-heal-triage/SKILL.md`, `forge-council-gate/SKILL.md`) is always authoritative for behavior. The glossary is authoritative for naming and definition. If they conflict on behavior, the skill wins. If they conflict on the name of a concept, the glossary wins. Document the discrepancy and suggest it be reconciled.

**Escalation:** NEEDS_CONTEXT if the phrasing difference implies a behavioral difference (e.g., glossary says "max 3 retries" but a skill says "max 5 retries" — that is a real conflict, not just a naming difference).

---

### Edge Case 3: New Forge Term Encountered That Is Not in This Glossary

**Symptom:** A skill, agent, or brain file uses a term like "pressure scenario," "seeder," or "gate bypass" that does not appear in this glossary.

**Do NOT:** Invent a definition or silently treat it as undefined.

**Action:**
1. Search for the term in `skills/` and `agents/` with grep to find the canonical context in which it's used
2. If found in a SKILL.md, derive the definition from the usage context
3. If not found anywhere, treat it as a candidate for a missing glossary entry and surface it to the dreamer
4. Do not propagate undefined terminology into brain decisions without clarifying its meaning first

**Escalation:** NEEDS_CONTEXT — request a definition from the skill author before proceeding with work that depends on this term.

---

### Edge Case 4: Council Is Requested to Be Skipped Due to Time Pressure

**Symptom:** "We already know the contracts, can we skip council and go straight to implementation?"

**Do NOT:** Accept the skip request and proceed to tech plans without running `forge-council-gate`.

**Action:**
1. STOP. Council is a HARD-GATE — it is not optional even when contracts appear pre-negotiated.
2. If contracts are documented elsewhere (prior PRD, wiki, existing spec), load them as the starting position for council, not as a substitute for it.
3. Run `forge-council-gate` with the existing contract proposals as input — surfaces still negotiate, verify compatibility, and sign off.
4. If the human insists on skipping: do not proceed. Log BLOCKED. Explain that council prevents integration bugs that surface during eval; skipping council means those bugs are discovered when they are expensive to fix.
5. The only valid "skip" is `[ABORT_TASK]` logged to `conductor.log` by the human — which cancels the whole pipeline, not just council.

**Escalation:** BLOCKED — council is non-negotiable per `forge-council-gate` Iron Law.

---

## Cross-References

- **Human input convention:** [`skills/_shared/human-input.md`](../_shared/human-input.md)
- **Per-task product terms (not this glossary):** [docs/terminology-review.md](../../docs/terminology-review.md), [docs/templates/terminology.md](../../docs/templates/terminology.md)
- **Dialogue discipline canon:** `docs/forge-one-step-horizon.md`; `using-forge` (Horizon narration, Multi-question elicitation)
- **Semantic eval canon:** [docs/semantic-eval-csv.md](../../docs/semantic-eval-csv.md), [docs/forge-task-verification.md](../../docs/forge-task-verification.md), [docs/conductor-log-format.md](../../docs/conductor-log-format.md), [docs/semantic-eval-schema.md](../../docs/semantic-eval-schema.md)
- **Brain layout:** `forge-brain-layout`, `brain-read`, `brain-write`, `brain-recall`
- **Phase progress tracking:** `/home/lordvoldemort/.claude/projects/-home-lordvoldemort-Videos-forge/memory/MEMORY.md`
