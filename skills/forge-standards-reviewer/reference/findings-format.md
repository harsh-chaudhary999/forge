# Step 5: Format Findings — template

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
Rule: "No LangChain-style agent frameworks in Forge plugin code." (CLAUDE.md)
Violation: `from langchain.agents import AgentExecutor` (bundled skill-side Python)
Confidence: HIGH
Action: Remove LangChain from Forge-shipped code paths; use native tool orchestration or document host-only eval deps outside the plugin tree.
```

```
[P1] Skill Format — skills/my-new-skill/SKILL.md:1-6
Rule: "Every rigid skill must include an Anti-Pattern Preamble section." (forge-skill-anatomy)
Violation: Frontmatter shows `type: rigid` but no `## Anti-Pattern Preamble` section found in file.
Confidence: HIGH
Action: Add Anti-Pattern Preamble with minimum 3 anti-patterns before the Overview section.
```

---
