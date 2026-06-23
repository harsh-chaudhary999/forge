# forge-standards-reviewer — Edge Cases

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
