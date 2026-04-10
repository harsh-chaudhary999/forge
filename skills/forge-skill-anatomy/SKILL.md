---
name: forge-skill-anatomy
description: Template, rigor checklist, and CSO guidelines for creating new Forge skills. Reference when writing or reviewing any skill.
type: reference
---
# Skill Anatomy

## Frontmatter (Required)

```yaml
---
name: {skill-name}
description: "WHEN: {trigger condition}. {What the skill does in one sentence}."
type: rigid | flexible | reference
requires: [other-skill-name]
---
```

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

## Rigor Checklist

Before a skill is considered complete, verify:

- [ ] Frontmatter has CSO-optimized `description` starting with WHEN
- [ ] `type` is explicitly `rigid`, `flexible`, or `reference`
- [ ] `requires` lists all skill dependencies
- [ ] Anti-Pattern Preamble has 5+ rationalizations (rigid/flexible)
- [ ] Edge Cases documented (5+ for rigid, 3+ for flexible)
- [ ] HARD-GATE tags on non-skippable steps (rigid)
- [ ] Iron Law stated in code block (rigid)
- [ ] Red Flags — STOP section present (rigid)
- [ ] Output format specified
- [ ] No placeholder text ("TBD", "TODO", "...")
- [ ] Cross-references to related skills included

## File Location

All skills live in `skills/{skill-name}/SKILL.md` at repo root. The `.claude/skills/` path is a symlink — never create skills there directly.
