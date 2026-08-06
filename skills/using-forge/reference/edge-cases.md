# using-forge — Edge Cases

## Edge Cases

### Edge Case 1: Skill Not Found in Catalog

**Symptom:**
Skill tool returns "not found" or skill is referenced but doesn't exist in `~/.claude/skills/` (the installed plugin's skill catalog — the Forge repo's own copy lives at `skills/` in the plugin root, not under `~/forge/`, which is reserved for the brain).

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
forge-eval-gate and qa-semantic-csv-orchestrate both seem relevant. forge-council-gate and reasoning-as-web-frontend overlap. Ambiguous ordering.

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
