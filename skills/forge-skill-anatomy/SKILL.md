---
name: forge-skill-anatomy
description: "WHEN: You are writing or reviewing a Forge skill and need the canonical template, rigor checklist, or CSO guidelines."
type: reference
version: 2.1.2
preamble-tier: 1
triggers:
  - "writing a new skill"
  - "reviewing a skill"
  - "what sections does a skill need"
allowed-tools:
  - Read
---
# Skill Anatomy

## Frontmatter (Required)

```yaml
---
name: {skill-name}
description: "WHEN: {trigger condition}. {What the skill does in one sentence}."
type: rigid | flexible | reference
requires: []
version: 1.0.0
preamble-tier: 2
triggers:
  - "natural phrase that should invoke this skill"
  - "another trigger phrase"
allowed-tools:
  - Bash
  - Read
  - Write
hooks:
  PreToolUse:
    - freeze-scope-check        # remove lines that don't apply
    - destructive-command-check
---
```

## Progressive Disclosure (HARD rule — Agent Skills standard)

The [Agent Skills standard](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
is **three-level**, and a SKILL.md that ignores it pays the full token cost on every
invocation:

| Level | What | Loaded |
|---|---|---|
| 1 | `name` + `description` frontmatter | always (cheap) |
| 2 | **SKILL.md body** — the operational contract | when the skill triggers |
| 3 | **`reference/*.md`** bundled files | only when the body points the agent to one |

**Rules:**

- **Keep SKILL.md ≤ ~400 lines.** It holds the operational contract: anti-pattern
  preamble, iron law, red flags, the decision/workflow logic, edge-case **summary**,
  and pointers. It is *behavior*, not a manual.
- **Move catalogs and depth to `reference/`.** API/command references, exhaustive
  examples, long detection/recovery code, per-target appendices → one or more files
  under the skill's `reference/` directory, linked from the body ("full detail in
  `reference/<file>.md`"). The agent reads the one it needs — this is a capability
  *gain*: you can go far deeper in a reference file than a flat SKILL.md ever allowed,
  at zero cost until it's needed.
- **Never delete to slim.** Relocation only. If you carve a SKILL.md, account for the
  lines (`wc -l` old vs new body + reference files) so nothing is lost.
- **Shared, repeated prose lives once under `skills/_shared/`.** The blocking
  human-input convention is [`skills/_shared/human-input.md`](../_shared/human-input.md);
  driver families share a contract file. Point to it — do not paste the boilerplate
  into every skill (the `_` prefix marks a non-skill support directory).
- **Ritual is by type.** The full Anti-Pattern + Iron Law + Red Flags ritual is
  **required for `rigid`** skills (D25). `reference`/lookup skills do **not** carry an
  Iron Law or Red Flags — keep them lean.

### `triggers` and `allowed-tools` status

- `description` (with the CSO rules below) is the **only** field the host uses to route
  invocation. `triggers` is **documentation of authoring intent**, not an invocation
  signal — keep it short and accurate or omit it; do not let it drift from `description`.
- `allowed-tools` documents the skill's tool contract and is read by
  `tools/dev/lint_skill_allowed_tools.py` (rigid skills must declare it). Treat it as the
  enforceable allowlist it is becoming under the standard — keep it truthful.

### CSO (Claude Search Optimization) for Descriptions

The `description` field is how the AI decides whether to invoke a skill. Optimize it:

- **Start with WHEN** — Describe the trigger, not the capability. "WHEN eval drivers return results and you need a verdict" not "Judges eval results."
- **Include the action verb** — "locks", "negotiates", "scores", "verifies", "dispatches"
- **Name the inputs/outputs** — "shared-dev-spec", "eval verdict", "tech plan"
- **Avoid generic words** — "handles", "manages", "processes" tell the AI nothing

| Bad | Good |
|---|---|
| `Manages cache contracts` | `WHEN: Two or more services share a Redis cache and you need to negotiate TTL, invalidation, and key ownership` |
| `Code review skill` | `WHEN: Implementation is complete and you need spec-compliance verification before merge` |
| `Brain operations` | `WHEN: A decision needs to be recorded with provenance (who, when, why, evidence) in the brain` |

### New Frontmatter Fields

Optional frontmatter fields for new skills. Existing skills do not need to be updated immediately — add them when a skill is touched.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `version` | Required for new skills | semver string | Track breaking changes. Bump: patch = content edits, minor = new workflow steps, major = breaking workflow changes (requires migration). |
| `preamble-tier` | Optional | integer 1–4 | Which shared preamble tier to inject. See Preamble Tier Guide below. Omit if the skill manages its own preamble entirely. |
| `triggers` | Optional | string list | Natural-language phrases that strongly suggest this skill should be invoked. Informational in the current implementation — helps skill authors document intent. |
| `allowed-tools` | Optional | string list | Tools this skill is permitted to use. Documents intent; not enforced at runtime currently. |
| `hooks` | Optional | object | Declares which `PreToolUse` enforcement checks this skill activates. Values correspond to named checks in `pre-tool-use.cjs` (`freeze-scope-check`, `destructive-command-check`). Purely declarative — hooks run automatically when their preconditions are met, but this field documents which ones are relevant to the skill's safety contract. |
| `effort` | Optional | `low`/`medium`/`high` | Native Claude Code subagent **reasoning-effort** hint, honored when this skill drives a subagent (the same field as on `agents/*.md` frontmatter). Set `high` on reasoning-heavy skills (council surfaces, contracts, tech-plan); omit to inherit the session/dispatch effort. Other native subagent fields (`model`, `maxTurns`, `disallowedTools`, `isolation`) may likewise appear on skills that map to subagents — standard hosts ignore unknown keys. |

### Human input (`AskUserQuestion` in `allowed-tools`)

If **`AskUserQuestion`** appears in **`allowed-tools`**, the skill body **must** include a short **`## Human input`** section (after the title is fine) that:

1. States that **`AskUserQuestion`** is the canonical blocking-input tool (Claude Code + **`tools/lint_skill_allowed_tools.py`**) and **points to [`skills/_shared/human-input.md`](../_shared/human-input.md)** for the convention — do **not** paste host boilerplate inline, and do **not** re-introduce per-IDE renames (this branch is Claude-only).
2. Keeps only **skill-specific** human-input rules inline (e.g. a verbatim blockquote a gate must show, a Questioning Protocol, stage-local rules); everything host-generic lives in `_shared/human-input.md`.
3. If the skill elicits **multiple** answers in sequence, follows **`using-forge`** **Multi-question elicitation** (transcript-first, one primary topic per turn, reconcile) — unless the skill documents a deliberate exception.
4. For live-dialogue norms (**one-step horizon**, **question-forward**, **no bundled** unrelated forks, **no trailing** later-stage reminders, **no defensive downstream-gate narration** mid-elicitation, **phase-specific** waivers), points to **`docs/forge-one-step-horizon.md`** and **`using-forge`** **Multi-question elicitation** items **4–8** — applies to **every** skill that guides chat behavior.

Gate and interrogation skills should **also** ensure chat-visible question text where **`using-forge`** or the skill already requires it — this section does not replace those HARD-GATEs.

### Preamble Tier Guide

Preamble tiers are cumulative — each tier includes all tiers below it. The tier files live in `skills/_preamble/`.
Directories under `skills/` prefixed with `_` are reserved for support artifacts (not behavioral skill units).

| Tier | Adds | Use for |
|------|------|---------|
| 1 | Writing style, tone, response length rules | Lightweight lookup/reference skills (glossaries, templates) |
| 2 | + Confusion protocol, escalation rules, ask-don't-assume | Most utility and technique skills |
| 3 | + Completeness principle, search-before-building, YAGNI, scope discipline | Implementation skills that write code or author specs |
| 4 | + Session tracking, context health, continuous checkpoint mode, operational self-improvement | Orchestration and ship skills (conductor, qa-live-app, health, retro) |

**Decision:** If unsure, use tier 2. It's the baseline for any skill that interacts with a user or makes decisions.

### Migration Pattern

When a skill introduces a breaking change (major version bump), create a `migrations/` subdirectory:

```
skills/
  my-skill/
    SKILL.md         (version: 2.0.0)
    migrations/
      v2.0.0.sh      (migration script from 1.x to 2.x)
```

Migration script format:
```bash
#!/usr/bin/env bash
# Migration: my-skill v1.x → v2.0.0
# Run this script to migrate brain files or config that this skill's change requires.
# If no migration is needed, this file documents the breaking change for reference.

echo "Migrating my-skill from v1.x to v2.0.0..."
# ... migration steps ...
echo "Done."
```

Migration scripts are not yet automated — they are run manually when upgrading. Document what changed and why.

## Skill Types

| Type | Rule | When to Use |
|---|---|---|
| **rigid** | Follow exactly. No adaptation. Zero tolerance for shortcuts. | Discipline-enforcing skills: TDD, gates, eval, review |
| **flexible** | Adapt principles to context. Core intent preserved. | Technique skills: negotiation, planning, pattern extraction |
| **reference** | Explain concepts. No prescription. | Glossaries, templates, layout guides |

## Required Sections by Type

### Rigid Skills (Discipline)

1. **Anti-Pattern Preamble** (REQUIRED — D25)
   - Rationalization table: 5+ rows minimum
   - Format: `| Rationalization | Why It Fails |`
   - Close every loophole. If someone could talk themselves out of following the skill, add a row.
   - End with: `**If you are thinking any of the above, you are about to violate this skill.**`

2. **Iron Law** (one non-negotiable rule in a code block)
   ```
   IRON LAW: {The single most important rule. If you remember nothing else, remember this.}
   ```

3. **HARD-GATE** tags on every non-skippable step (D24)

4. **Red Flags — STOP** section
   - 5+ warning signs that indicate the skill is being bypassed
   - Format: bullet list of "If you notice X, STOP — Y is happening"

5. **Edge Cases** — At least 5, each with:
   - Scenario description
   - Specific action to take
   - Why the naive approach fails

6. **Workflow** — Step-by-step, numbered, no ambiguity

7. **Output** — What the skill produces, in what format

### Flexible Skills (Technique)

1. **Anti-Pattern Preamble** (REQUIRED — D25) — Same format as rigid
2. **Principles** — Core intent that must be preserved
3. **Workflow** — Adaptable steps with decision points
4. **Edge Cases** — At least 3
5. **Output** — Expected deliverables

### Reference Skills (Clarity)

1. **Structured tables** — Organize information for quick lookup
2. **Naming conventions** — How things are named and why
3. **Cross-references** — Links to related skills and concepts
4. **Examples** — Concrete usage

## Persuasion Principles (D14 — Cialdini)

Apply per skill type:

| Principle | Rigid Skills | Flexible Skills | Reference Skills |
|---|---|---|---|
| **Authority** | "This gate exists because X failure happened" | "Industry standard practice" | N/A |
| **Commitment** | "You committed to this process at intake" | "The team agreed on this approach" | N/A |
| **Social Proof** | "Every shipped product follows this" | "Teams that do this ship faster" | N/A |
| **Clarity** | Step numbers, checklists, zero ambiguity | Decision trees, clear criteria | Tables, structured formats |
| **Unity** | "We don't skip gates" | "We adapt, we don't abandon" | N/A |

---

## Authoring deep dive (load on demand)

The per-type deep dive, the authoring anti-patterns, the skill-authoring edge cases, and
full GOOD/BAD worked examples live in **`reference/authoring-deep-dive.md`** — the same
progressive-disclosure rule this guide mandates. The sections above are the operational
contract; the validation + rigor checklists below are the quick pre-publish reference.

# Pre-Publish Skill Validation Checklist

Complete this checklist before merging a skill:

**Frontmatter & Metadata**
- [ ] `name` field present and matches directory name (kebab-case)
- [ ] `description` field present and starts with "WHEN:"
- [ ] `type` field is one of: rigid, flexible, reference
- [ ] `requires` field lists all dependencies (and each skill exists)
- [ ] YAML syntax is valid (test with `yq` or similar)

**Anti-Patterns (Rigid & Flexible Skills Only)**
- [ ] Anti-Pattern Preamble section present
- [ ] 5+ rationalizations documented (with rebuttals)
- [ ] Ends with "If you are thinking any of the above, you are about to violate this skill."
- [ ] Each rationalization has a "Why It Fails" explanation

**Edge Cases**
- [ ] 5-7 edge cases documented (rigid) or 3-5 (flexible)
- [ ] Each edge case: Scenario → Mitigation → Why Naive Fails → Escalation
- [ ] At least one BLOCKED escalation (where skill can't apply)
- [ ] At least one NEEDS_COORDINATION escalation
- [ ] At least one NEEDS_INFRA_CHANGE escalation

**Workflow & Steps (Rigid Skills)**
- [ ] Workflow is step-by-step, numbered, no ambiguity
- [ ] HARD-GATE tags on 2-5 critical steps
- [ ] HARD-GATE format: "HARD-GATE: [step]. If [condition], violation occurs."
- [ ] HARD-GATE conditions are testable

**Red Flags (Rigid Skills)**
- [ ] "Red Flags — STOP" section present
- [ ] 5+ warning signs documented
- [ ] Format: "If you notice X, STOP — Y is happening"

**Iron Law (Rigid Skills)**
- [ ] Iron Law present in code block
- [ ] One non-negotiable rule, clear and enforceable

**Output Specification**
- [ ] Output format specified (document type, structure, validation)
- [ ] Examples of good vs bad output included
- [ ] Validation criteria listed

**Examples & Scenarios**
- [ ] 3-4 worked examples included
- [ ] Examples show concrete scenarios (not abstract)
- [ ] For FLEXIBLE skills: 2+ approaches shown
- [ ] No placeholder code (no "// implement this", "TODO")

**Decision Trees**
- [ ] Present if skill has >1 major choice point
- [ ] ASCII format for plaintext readability
- [ ] Each branch has clear action or next skill

**Cross-References**
- [ ] 3+ related skills linked (prerequisite, follow-up, or sibling)
- [ ] Format: `[skill-name]: one-sentence-explaining-connection`
- [ ] Prerequisite skills listed
- [ ] Follow-up skills listed

**Checklists (Rigid & Flexible Skills)**
- [ ] Pre-invocation checklist: "Do I have the right skill?"
- [ ] Pre-implementation checklist: "Am I ready?"
- [ ] Post-implementation checklist: "Did I follow correctly?"
- [ ] Each checklist has 5-10 items, binary (YES/NO)

**Text Quality**
- [ ] No placeholder text ("TBD", "TODO", "implement later", "...")
- [ ] No vague instructions ("do X", "handle Y") without examples
- [ ] No broken links (cross-references are valid)
- [ ] No orphaned sections or headers without content

**Line Count & Structure**
- [ ] Skill is 400-1500 lines (appropriate for type)
- [ ] Major sections use H2 headers (##)
- [ ] Sub-sections use H3 headers (###)
- [ ] Tables are readable (not >10 columns)

**Git & Publishing**
- [ ] File path is `skills/{skill-name}/SKILL.md`
- [ ] Commit message includes "[skill-name]" tag
- [ ] No other files in the skill directory (unless reference files like examples/)
- [ ] Skill is mentioned in forge-glossary (if it's discoverable)

---

# File Location

All skills live in `skills/{skill-name}/SKILL.md` at repo root. The `.claude/skills/` path is a symlink — never create skills there directly.

---

# Rigor Checklist (Concise Version)

Before a skill is considered complete, verify:

- [ ] Frontmatter has CSO-optimized `description` starting with WHEN
- [ ] `type` is explicitly `rigid`, `flexible`, or `reference`
- [ ] `requires` lists all skill dependencies
- [ ] Anti-Pattern Preamble has 5+ rationalizations (rigid/flexible)
- [ ] Edge Cases documented (5-7 for rigid, 3-5 for flexible) with escalation keywords
- [ ] HARD-GATE tags on non-skippable steps (rigid)
- [ ] Iron Law stated in code block (rigid)
- [ ] Red Flags — STOP section present (rigid)
- [ ] Output format specified
- [ ] No placeholder text ("TBD", "TODO", "...")
- [ ] Cross-references to 3+ related skills included
- [ ] Decision trees present (if >1 major choice point)
- [ ] Checklists: pre-invocation, pre-implementation, post-implementation
- [ ] 3-4 worked examples included (showing concrete scenarios)
