---
name: forge-standards-reviewer
description: "WHEN: A PR or diff is ready for review and must be audited against Forge's own project rules (CLAUDE.md, AGENTS.md, skill format constraints). Runs AFTER spec-reviewer and code-quality-reviewer as the final enforcement gate."
type: rigid
requires: [brain-read]
---

# Forge Standards Reviewer (HARD-GATE)

Audits a code diff **exclusively against rules the Forge project wrote down**. Not generic best practices. Not style preferences. Only rules that appear in `CLAUDE.md`, `AGENTS.md`, or documented skill/agent format constraints.

Every finding must cite:
1. The **exact rule** (which file, which constraint ID or section)
2. The **exact violation** (file path + line number)
3. A **confidence tier** (HIGH / MODERATE — LOW is suppressed)

No evidence = finding is suppressed. No rule citation = finding is rejected.

---

## Anti-Pattern Preamble: Why Standards Reviews Fail

### Anti-Pattern 1: "I'll flag generic best-practice issues"

**Why This Fails:** Generic findings (naming conventions, comment style, abstraction choices) that aren't in the project's written rules are noise. They erode trust in the reviewer — developers start ignoring all findings because the signal-to-noise ratio is bad.

**Enforcement (MUST):**
1. MUST trace every finding to a specific rule in CLAUDE.md, AGENTS.md, or skill format docs
2. MUST suppress any finding that cannot be traced to a written rule
3. MUST NOT invent rules from "common sense" or personal preference
4. MUST NOT flag issues already covered by spec-reviewer or code-quality-reviewer
5. MUST prefix every finding with the exact rule ID or section (e.g., `D5:`, `Skill Format:`)

---

### Anti-Pattern 2: "I'll flag the issue without checking whether the rule actually applies"

**Why This Fails:** Rules have scope. D5 (no LangChain) applies to agent/skill code, not to a user's product code being built with Forge. HARD-GATE format applies to `rigid` skills, not `flexible` ones. Applying rules out of scope produces false positives and noise.

**Enforcement (MUST):**
1. MUST check whether the diff touches Forge internals (skills/, agents/, commands/, hooks/) vs user product code
2. MUST apply skill format rules only to files in `skills/` directories
3. MUST apply agent format rules only to files in `agents/` directories
4. MUST check `type: rigid | flexible` before requiring HARD-GATE and Anti-Pattern preamble
5. MUST NOT apply Forge internal rules to user-generated eval scenarios, PRDs, or brain files

---

### Anti-Pattern 3: "I know the rules from memory"

**Why This Fails:** Rules evolve. CLAUDE.md constraint list grows each sprint. A rule you remember from three sessions ago may have been updated, removed, or superseded. Memory-based reviews are stale reviews.

**Enforcement (MUST):**
1. MUST read `CLAUDE.md` and `AGENTS.md` fresh at the start of every review session
2. MUST NOT rely on cached knowledge of constraint IDs
3. MUST check current skill format frontmatter requirements (they evolve)
4. MUST re-read the anti-pattern preamble requirement from the skill anatomy docs
5. MUST treat your memory as a hint — the files are authoritative

---

### Anti-Pattern 4: "Low-confidence findings are better than nothing"

**Why This Fails:** Surfacing low-confidence findings trains developers to dismiss all findings. A reviewer that cries wolf is worse than no reviewer. Suppress uncertain findings — they create investigation debt without improving code quality.

**Enforcement (MUST):**
1. MUST apply confidence calibration to every finding before surfacing
2. MUST suppress all LOW confidence findings (< 0.60)
3. MUST mark MODERATE findings (0.60–0.79) with explicit uncertainty language
4. MUST only emit HIGH confidence findings (≥ 0.80) without caveat
5. MUST document suppressed findings count at end: `Suppressed N low-confidence findings`

---

### Anti-Pattern 5: "The diff is small, I'll skip the full standards check"

**Why This Fails:** Small diffs are where constraint violations hide. A one-line change to a skill that adds a new `requires:` dependency without the dependency chain being satisfied is a small diff with a large downstream impact. Size of diff is not correlated with severity of violation.

**Enforcement (MUST):**
1. MUST run the full rule checklist regardless of diff size
2. MUST check all touched file types (skill, agent, command, hook) against their respective format rules
3. MUST NOT skip any section of the checklist because "it's probably fine"
4. MUST scan for violations in both added and modified lines (not just added)
5. MUST explicitly confirm "no violations found" for each rule category if none are present

---

## Iron Law

```
EVERY FINDING MUST CITE AN EXACT RULE AND AN EXACT VIOLATION LINE.
NO CITATION = FINDING IS SUPPRESSED.
LOW CONFIDENCE = FINDING IS SUPPRESSED.
SCOPE MISMATCH = FINDING IS REJECTED.
```

---

## Step 1: Discover Standards Files

Before reading the diff, collect the authoritative rule sources. Use paths, not content — read what you need, skip what you don't.

```bash
# Find CLAUDE.md files in ancestor directories (project rules)
find . -name "CLAUDE.md" -not -path "*/node_modules/*" | sort

# Find AGENTS.md files (agent/skill authoring rules)
find . -name "AGENTS.md" -not -path "*/node_modules/*" | sort

# Skill format reference
ls skills/forge-skill-anatomy/SKILL.md 2>/dev/null
ls skills/forge-subagent-anatomy/SKILL.md 2>/dev/null
```

Read only the sections relevant to the file types touched by the diff. If the diff only touches `skills/`, read the skill format rules. If it touches `agents/`, read the agent format rules. Do NOT read all standards files in full if only a subset applies.

---

## Step 2: Classify Diff Scope

Identify which Forge subsystem(s) the diff touches:

| Files Changed | Applicable Rule Sets |
|---|---|
| `skills/**` | Skill format (frontmatter, type, requires), Anti-pattern preamble requirement (rigid), HARD-GATE requirement (rigid), Checklist requirement |
| `agents/**` | Agent format (frontmatter, role, when-to-invoke, inputs, outputs), subagent isolation rules |
| `commands/**` | Command format (frontmatter, trigger, step structure) |
| `hooks/**` | Hook format, session injection rules |
| `install.sh` | No third-party deps (D13), platform support |
| User product code (`brain/`, `seed-product/`) | Not subject to Forge internal rules — skip standards review |

**If diff touches only user product files:** emit `SCOPE: No Forge internals touched — standards review not applicable` and exit.

---

## Step 3: Extract Forge Constraint Rules

Read the relevant sections from the discovered standards files. Extract rules as a numbered list. For each rule, note:
- Constraint ID (e.g., `D5`, `D13`, `D15`, `D24`, `D25`)
- What it requires
- What it prohibits
- Which file types it applies to

**Core Forge constraints to always check (from CLAUDE.md):**

| ID | Rule | Applies To |
|---|---|---|
| D5 | No third-party agent frameworks — no LangChain, Playwright, Puppeteer | All skills, agents, hooks |
| D13 | No runtime dependency on any external plugin at runtime | install.sh, hooks, skills |
| D15 | Skills are TDD'd — developed via pressure scenarios against seed product | New skills |
| D24 | HARD-GATE tag required on every non-skippable step | Rigid skills |
| D25 | Anti-Pattern preamble required on every discipline-enforcing skill | Rigid skills |

**Skill format rules (from forge-skill-anatomy):**

| Field | Requirement |
|---|---|
| Frontmatter | Must include: `name`, `description`, `type` |
| `description` | Must say WHEN to invoke — not what the skill does |
| `type` | Must be `rigid` or `flexible` — no other values |
| `requires` | Must list all dependency skills; omit if none |
| Anti-Pattern Preamble | Required for `rigid` type skills |
| Iron Law | Required for `rigid` type skills |
| Checklist | Required for `rigid` type skills |
| Edge Cases | Required for all skills (min 3) |

**Agent format rules (from forge-subagent-anatomy):**

| Field | Requirement |
|---|---|
| Frontmatter | Must include: `name`, `description` |
| `description` | Must say WHEN to invoke |
| Role section | Must describe what the agent is and is not responsible for |
| Inputs section | Must list all required inputs |
| Output section | Must define status codes: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED |
| Isolation note | Must include SUBAGENT-STOP block if agent receives session context |

---

## Step 4: Scan Diff for Violations

For each rule extracted in Step 3, scan the diff for violations. Check **both added lines (`+`) and modified context lines**.

For each potential violation found:

### Confidence Calibration (apply before surfacing)

**HIGH confidence (≥ 0.80) — surface as finding:**
- Violation is unambiguous from the code alone
- Rule explicitly prohibits the pattern (e.g., `import LangChain` violates D5)
- File type is confirmed in scope
- Line number is exact

**MODERATE confidence (0.60–0.79) — surface with caveat:**
- Rule likely applies but the pattern is indirect (e.g., a wrapper around a prohibited library)
- Scope is uncertain (e.g., file could be user code or forge internal)
- State it explicitly: `"Possible violation of D5 — verify this import doesn't transitively use LangChain"`

**LOW confidence (< 0.60) — suppress:**
- Requires runtime context to confirm
- Pattern matches the rule superficially but probably doesn't apply
- Add to suppressed count at end, do NOT surface

---

## Step 5: Format Findings

Each finding follows this exact format:

```
[SEVERITY] [RULE-ID] — [file:line]
Rule: "<exact quoted rule text from CLAUDE.md or format doc>"
Violation: "<exact quoted line from diff>"
Confidence: HIGH | MODERATE
Action: <what must be changed>
```

**Severity tiers:**
- **P0 — BLOCKER:** Violates a hard architectural constraint (D5, D13). Must fix before merge.
- **P1 — REQUIRED:** Missing required format element (frontmatter field, HARD-GATE, Iron Law). Must fix before merge.
- **P2 — RECOMMENDED:** Format present but incomplete (edge cases too thin, checklist missing items). Fix preferred, YELLOW if skipped.
- **P3 — ADVISORY:** Minor format gap (description phrasing, wikilinks missing). Note only.

**Example finding:**

```
[P0] D5 — skills/my-new-skill/SKILL.md:14
Rule: "No third-party agent frameworks. No LangChain, Playwright, Puppeteer." (CLAUDE.md)
Violation: `import { AgentExecutor } from 'langchain/agents'`
Confidence: HIGH
Action: Remove LangChain import. Use native Claude Code tool calls instead.
```

```
[P1] Skill Format — skills/my-new-skill/SKILL.md:1-6
Rule: "Every rigid skill must include an Anti-Pattern Preamble section." (forge-skill-anatomy)
Violation: Frontmatter shows `type: rigid` but no `## Anti-Pattern Preamble` section found in file.
Confidence: HIGH
Action: Add Anti-Pattern Preamble with minimum 3 anti-patterns before the Overview section.
```

---

## Step 6: Check for Missing Requirements

Beyond scanning for violations, also check for **required elements that are absent**:

For each **new or modified rigid skill** in the diff:
- [ ] `## Anti-Pattern Preamble` section present?
- [ ] `## Iron Law` section with fenced code block present?
- [ ] `HARD-GATE` label on at least one enforcement step?
- [ ] `## Edge Cases` section with minimum 3 cases?
- [ ] Checklist at end of skill?
- [ ] `description:` frontmatter says WHEN, not WHAT?
- [ ] `requires:` field present (even if empty array)?

For each **new or modified agent** in the diff:
- [ ] `name:` and `description:` frontmatter present?
- [ ] Role section defines what agent is NOT responsible for?
- [ ] Output status codes (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED) documented?
- [ ] `<SUBAGENT-STOP>` block present if agent receives parent session context?

---

## Step 7: Emit Report

Structure the report as:

```
## Forge Standards Review

**Scope:** [list of files reviewed and which rule sets applied]
**Standards read:** [CLAUDE.md, AGENTS.md, forge-skill-anatomy, etc.]

### P0 Blockers (must fix before merge)
[findings or "None"]

### P1 Required (must fix before merge)
[findings or "None"]

### P2 Recommended (fix preferred)
[findings or "None"]

### P3 Advisory (note only)
[findings or "None"]

### Summary
- Files audited: N
- Rules checked: N
- Findings: N (P0: N, P1: N, P2: N, P3: N)
- Suppressed (low confidence): N

### Verdict
PASS — No P0 or P1 violations found. Ready for merge.
FAIL — N blocker(s) found. Fix required before merge.
YELLOW — No blockers, N recommended fixes. Explicit dreamer acknowledgment required.
```

**Verdict rules:**
- Any P0 → **FAIL**
- Any P1 → **FAIL**
- P2 or P3 only → **YELLOW** (requires dreamer acknowledgment)
- No findings → **PASS**

---

## Edge Cases

### Edge Case 1: CLAUDE.md Not Found

**Symptom:** `find . -name "CLAUDE.md"` returns empty. No authoritative rule source.

**Do NOT:** Invent rules from memory or proceed without rules.

**Action:**
1. Check parent directories up to home
2. Check `~/forge/CLAUDE.md` explicitly
3. If not found: emit `NEEDS_CONTEXT — Cannot locate CLAUDE.md. Standards review cannot proceed without authoritative rule source.`
4. Do NOT run the review against remembered constraints

**Escalation:** NEEDS_CONTEXT

---

### Edge Case 2: Diff Touches Both Forge Internals and User Code

**Symptom:** PR modifies `skills/my-skill/SKILL.md` AND `brain/products/myapp/prds/prd-001.md`.

**Do NOT:** Apply Forge internal rules to brain files.

**Action:**
1. Split the diff: extract Forge internal files separately from user product files
2. Run standards review on Forge internal files only
3. Note explicitly in report: `brain/products/... files excluded from Forge standards review (user product files, not subject to internal constraints)`

**Escalation:** None — handle cleanly

---

### Edge Case 3: `requires:` Dependency Not Found in Skill Catalog

**Symptom:** Skill frontmatter says `requires: [brain-read, nonexistent-skill]` — `nonexistent-skill` not in catalog.

**Do NOT:** Ignore the dangling requires reference.

**Action:**
1. Grep skills/ for the referenced skill name
2. If not found: flag as P1 finding — `requires: references nonexistent skill 'nonexistent-skill'`
3. Suggest: check for typo, or remove the requirement if the dependency was deleted

**Escalation:** NEEDS_CONTEXT if the skill might exist under a different name

---

### Edge Case 4: Rule in CLAUDE.md Is Ambiguous

**Symptom:** Rule says "No runtime dependency on external plugins" (D13) but the diff uses a package that could be build-time or runtime.

**Do NOT:** Make a high-confidence finding on an ambiguous rule interpretation.

**Action:**
1. Downgrade confidence to MODERATE
2. State the ambiguity: `"D13 may apply — this import could be runtime. Verify: is this package bundled into the deployed artifact or only used during build?"`
3. Mark as P2 (recommended) not P0 (blocker) when confidence is MODERATE

**Escalation:** NEEDS_CONTEXT — ask the author to clarify whether the dependency is runtime or build-time

---

### Edge Case 5: Skill Has `type: flexible` but Looks Discipline-Enforcing

**Symptom:** Skill file has `type: flexible` but its content is a rigid enforcement workflow (e.g., "you MUST always do X before Y").

**Do NOT:** Override the author's type declaration without evidence.

**Action:**
1. Flag as MODERATE confidence P2: `"Skill content reads as rigid (enforcement workflow) but type is set to flexible. Consider changing to rigid — rigid skills get Anti-Pattern Preamble, Iron Law, and HARD-GATE enforcement."`
2. Do NOT auto-fail — type choice may be intentional
3. Require author acknowledgment

**Escalation:** NEEDS_CONTEXT — let the author confirm intent

---

## Decision Tree: Which Rules Apply

```
Diff touches skills/**?
  → YES: Apply skill format rules (frontmatter, preamble, iron law, edge cases, checklist)
        Is type: rigid?
          → YES: Require Anti-Pattern Preamble, Iron Law, HARD-GATE, Checklist
          → NO (flexible): Require frontmatter and edge cases only
  → NO: Skip skill format rules

Diff touches agents/**?
  → YES: Apply agent format rules (role, inputs, outputs, isolation, status codes)
  → NO: Skip agent format rules

Diff touches skills/, agents/, commands/, hooks/, install.sh?
  → YES: Apply Forge architectural constraints (D5, D13, D24, D25)
  → NO (brain/, seed-product/, user PRDs): SKIP — not subject to Forge internal rules

New skill being added (file didn't exist before)?
  → YES: Also check D15 (TDD requirement) — is there evidence of pressure scenarios?
  → NO: Skip D15

Type: rigid AND no Anti-Pattern Preamble found?
  → YES: P1 finding (required, blocks merge)
  → NO: Continue
```

---

## Checklist

Before emitting the report:

- [ ] Standards files discovered and read (not from memory)
- [ ] Diff scope classified — Forge internals vs user code clearly separated
- [ ] All constraint IDs from CLAUDE.md checked against diff
- [ ] All skill format rules checked for every modified/added skill file
- [ ] All agent format rules checked for every modified/added agent file
- [ ] Confidence calibration applied — LOW findings suppressed
- [ ] Every finding has: rule citation, file:line, exact quoted violation, confidence tier
- [ ] Missing required sections checked (not just violations scanned)
- [ ] Suppressed finding count reported
- [ ] Verdict emitted with clear reasoning

## Cross-References

| Related Skill | Relationship |
|---|---|
| `forge-skill-anatomy` | Authoritative source for skill format rules |
| `forge-subagent-anatomy` | Authoritative source for agent format rules |
| `forge-trust-code` | Upstream spec-reviewer — runs before this skill |
| `forge-eval-gate` | Parent gate — standards review is one step in the eval gate |
| `brain-write` | Used to record FAIL verdicts with evidence |
