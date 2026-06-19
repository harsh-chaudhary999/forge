---
name: brain-read
description: "WHEN: You need to look up product topology, project metadata, past decisions, or contract details from the brain."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "read the brain"
  - "load brain context"
  - "what does the brain say"
  - "look up brain"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Brain Read

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I remember what the decision said" | Memory drifts. The brain is the source of truth — read the actual file. |
| "I'll just grep for the keyword" | Grep finds text, not context. Follow the structured read patterns to get full decision provenance. |
| "The product topology hasn't changed" | Products evolve between PRDs. Always reload topology before assuming repo lists, stacks, or services. |
| "I'll read the spec from the working directory" | The working directory may have uncommitted changes. The brain's git-backed copy is the locked, canonical version. |
| "I only need one section of the decision" | Partial reads miss linked context: alternatives considered, evidence, constraints. Read the full record. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
ALWAYS READ FROM THE BRAIN PATH DIRECTLY — MEMORY IS NOT AUTHORITY, THE BRAIN IS.
NEVER INFER OR ASSUME BRAIN CONTENT FROM CHAT CONTEXT — READ THE FILE.
IF THE BRAIN FILE DOES NOT EXIST, STOP AND FLAG MISSING — DO NOT PROCEED WITH ASSUMED DATA.
```

The brain at `~/forge/brain/` is git-backed markdown.

> **Preferred read path: the brain MCP** (read-only) — `brain_read`, `brain_list`,
> `brain_recall`, `brain_why`, `brain_conductor_status` (the last is exactly the
> Task Scope HARD-GATE check below). It resolves the brain root itself, so it can't
> hit a wrong-path bug. See the MCP query map in [`forge-brain-layout`](../forge-brain-layout/SKILL.md)
> and [`docs/brain-mcp.md`](../../docs/brain-mcp.md). Caveat: enable it with
> `claude mcp add forge-brain` (bundled `.mcp.json` ships `mcpServers: {}`); the
> `cat`/`grep` patterns below are the live fallback.

Read patterns:

## Task Scope Verification (HARD-GATE)

Before reading any `prds/<task-id>/` path, verify you are reading the correct task:

```bash
# Confirm active task-id from environment or conductor.log
echo "${FORGE_TASK_ID:-${FORGE_PRD_TASK_ID:-UNSET}}"
# If UNSET, derive from the most recent conductor.log entry:
ls -t ~/forge/brain/prds/*/conductor.log 2>/dev/null | head -1
```

**HARD-GATE:** If `FORGE_TASK_ID` is unset and multiple `prds/*/conductor.log` files exist, confirm the task-id with the user before reading. Reading from the wrong task's brain silently poisons context — wrong contracts, wrong decisions, wrong spec.

Acceptable: reading from `products/<slug>/` (product config is shared across tasks).
Not acceptable: reading from `prds/<other-task-id>/` when the active task is different.

## Product Topology
```bash
cd ~/forge/brain
cat products/<product-slug>/product.md
```

Gives you: repos, roles, tech stacks, deployment strategies, services, contracts.

## Project Metadata
```bash
cat projects/<project-slug>/overview.md
cat projects/<project-slug>/tech-stack.md
cat projects/<project-slug>/conventions.md
```

## Locked PRD
```bash
cat prds/<task-id>/prd-locked.md
```

## Shared Dev Spec
```bash
cat prds/<task-id>/shared-dev-spec.md
```

## Contract Details
```bash
cat products/<product-slug>/contracts/api-rest.md
cat products/<product-slug>/contracts/schema-db.md
```

## Search

If you don't know the exact path, search:

```bash
cd ~/forge/brain
grep -r "search term" . --include="*.md"
```

## Grep Pattern Examples

See [reference/query-patterns.md](reference/query-patterns.md) for the full catalog of 8 real-world grep patterns (decisions by product/tag, API versioning across products, performance patterns, contract specs by type, lessons learned, cross-product standards, lifecycle tracking, time-based search) — each with use case, command, and example output.

## Performance Guidelines

See [reference/performance.md](reference/performance.md) for when grep is fast vs slow, scope/`--include`/`--exclude` optimization tips, grep-vs-brain-skill selection, caching strategy, and the grep-now/index-later architecture note.

## Search Strategies by Use Case

See [reference/search-strategies.md](reference/search-strategies.md) for the 5 use-case workflows (finding past decisions, locating a service contract, cross-product patterns, tracing decision history, validating against a contract before implementation) — each with recommended grep pattern, complementary brain skills, and step-by-step workflow.

## Common Search Pitfalls

See [reference/pitfalls.md](reference/pitfalls.md) for the 5 pitfalls (case-sensitivity, exact paths/no filename wildcards, stale decision references, slow full-brain grep, mixed content types) — each with problem, solution, and example.

## Edge Cases

### Edge Case 1: Brain not initialized (empty brain/ directory)

**Symptom:** Brain directory exists but contains no decisions, contracts, or products.

**Do NOT:** Proceed with grep search expecting results. Do NOT create decisions in arbitrary locations.

**Mitigation:** Check for brain directory structure before search:
```bash
ls -la ~/forge/brain/products/ ~/forge/brain/prds/ ~/forge/brain/decisions/
# If empty, brain is uninitialized
```

**Escalation:** NEEDS_INFRA_CHANGE — Brain initialization required before reading. Contact platform team to bootstrap brain with seed decisions and product topology.

---

### Edge Case 2: Decision file not found (grep returns nothing)

**Symptom:** Grep search returns no results or grep reports "No such file or directory".

**Do NOT:** Assume decision doesn't exist. Do NOT search with incorrect paths or typos.

**Mitigation:** 
1. Verify search path exists: `ls ~/forge/brain/products/<product>/decisions/`
2. Try broader search: `grep -r "keyword" ~/forge/brain --include="*.md"`
3. Check for archived decisions: `grep -r "keyword" ~/forge/brain/archive --include="*.md"`

**Escalation:** NEEDS_CONTEXT — Decision may not exist yet, be archived, or be named differently. Use `brain-recall` (ranked keyword + tag/status search) or the brain MCP `brain_recall` tool instead.

---

### Edge Case 3: Multiple decisions match query (ambiguous results)

**Symptom:** Grep returns 5+ matching decisions; unclear which is authoritative.

**Do NOT:** Pick the first match. Do NOT assume most recent is most relevant.

**Mitigation:**
1. Narrow search: `grep -r "exact phrase" products/<product>/decisions/ --include="*.md"`
2. Filter by status: `grep -r "status.*active" products/<product>/decisions/ --include="*.md"`
3. Check frontmatter for `decision_id:` field to identify canonical versions
4. Use `brain-why <ID>` to trace provenance if ID is clear

**Escalation:** NEEDS_COORDINATION — Multiple decisions on same topic. Consult brain-link to understand decision graph and relationships. May need decision review/consolidation.

---

### Edge Case 4: Corrupted decision file (invalid YAML or markdown)

**Symptom:** Grep finds file, but file fails to parse (missing frontmatter, broken YAML delimiters).

**Do NOT:** Edit the file without understanding corruption. Do NOT delete file.

**Mitigation:**
1. Check YAML syntax: `head -20 <file> | grep -E "^---"`
2. Verify file has opening `---` and closing `---` on separate lines
3. Use `cat -A <file> | head -20` to check for non-standard characters
4. Use `brain-read` to validate file structure before proceeding

**Escalation:** BLOCKED — Corrupted decision file cannot be reliably read. Escalate to codebase maintenance team to repair YAML or restore from git history.

---

### Edge Case 5: Brain in wrong repository location

**Symptom:** Grep or cat commands fail with "No such file or directory" or return unexpected results (wrong product).

**Do NOT:** Assume brain paths are relative. Do NOT use different brain locations without explicit verification.

**Mitigation:**
1. Resolve the brain root via the real precedence chain: `${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}` (the same order the brain MCP uses).
2. Confirm it is a git repo: `git -C "$BRAIN" rev-parse --is-inside-work-tree`.
3. Explicit path in all commands: `grep -r "term" ~/forge/brain --include="*.md"`.

**Escalation:** NEEDS_INFRA_CHANGE — Brain root is missing or not a git repo. Set `FORGE_BRAIN`/`FORGE_BRAIN_PATH`, or initialize the brain (`/workspace`). (There is no `git config forge.brain-path` or `.claude/brain` symlink mechanism — the env-precedence chain above is authoritative.)

---

## Decision Tree: Query Strategy

```
Need to read from brain?
    ↓
Do you know the exact path or filename?
├─ YES → Use `cat ~/forge/brain/<path>/<file>.md` (direct read)
└─ NO → Continue below

Do you know the product, service, or contract type?
├─ YES → Scope grep to that directory: `grep -r "term" ~/forge/brain/products/<product>/ --include="*.md"`
└─ NO → Continue below

Are you searching for a concept or pattern (not exact phrase)?
├─ YES → Use `brain-recall` for ranked keyword + tag/status search (grep-based, returns ranked decisions)
└─ NO → Continue below

Is the phrase common across multiple files (decision, contract, spec)?
├─ YES → Add --include filter: `grep -r "term" --include="*decision*.md"` OR `--include="*contract*.md"`
└─ NO → Use plain `grep -r "term" ~/forge/brain/products --include="*.md"`

Do you need to find decisions by metadata (status, owner, tag)?
├─ YES → Use grep pattern for YAML fields: `grep -r "^tags:.*auth" ~/forge/brain/products --include="*.md"`
└─ NO → Continue with phrase search

Are you searching across multiple products or years?
├─ YES → Expect slow grep (scope to decade first): `grep -r "term" ~/forge/brain/products/*/decisions/202[34]* --include="*.md"`
└─ NO → Scope to product/type and search

Result: Use the narrowest scope that includes your target. Always use --include="*.md" to avoid logs/temp files.
If grep is slow or ambiguous, escalate to brain-recall or brain-link.
```

---

## Cross-References

This skill works with other brain skills:

- **brain-write:** Decisions are recorded to the brain via `brain-write`. This skill reads what was written.
- **brain-recall:** Semantic search complement. Use `brain-read` for exact matches, `brain-recall` for conceptual search.
- **brain-why:** Traces provenance—who decided, when, and why. Use this after `brain-read` finds a decision.
- **brain-link:** Creates semantic edges between decisions. Shows decision dependencies found by `brain-read` grep patterns.
- **brain-forget:** Archives deprecated decisions. Use `brain-read` to find candidates for archival.
