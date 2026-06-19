---
name: brain-recall
description: "WHEN: You are about to make a decision and need to check if prior art or past learnings exist. Recall decisions, patterns, and gotchas from the brain before proceeding."
type: flexible
requires: [brain-read]
version: 1.0.1
preamble-tier: 2
triggers:
  - "search brain"
  - "find past decisions"
  - "recall brain"
  - "what did we decide about"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Brain Recall Skill

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** and uses it for any blocking human decision (task-scope confirmation, decision-vs-pattern disambiguation). Canonical convention: **[`skills/_shared/human-input.md`](../_shared/human-input.md)**.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I already know what happened last time" | Past experience is filtered by recency bias. The brain stores evidence, not impressions. Search it. |
| "There's no prior art for this decision" | Cross-product patterns exist more often than you think. Search across products, not just the current one. |
| "The search didn't return results, so there's nothing" | Bad queries miss good results. Try synonyms, broader tags, and product-agnostic terms before concluding. |
| "I'll just use the most recent result" | Recency ≠ relevance. A pattern from 6 months ago on a similar product may be more applicable than yesterday's decision on a different domain. |
| "Recall is optional — I can decide without it" | Every decision that ignores prior learnings risks repeating gotchas. Recall is the cheapest way to avoid known failure modes. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
BEFORE ACTING ON ANY DECISION, SEARCH THE BRAIN FIRST. MEMORY IS NOT A SUBSTITUTE FOR EVIDENCE — THE BRAIN IS THE ONLY AUTHORITATIVE RECORD.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Search returns zero results and agent concludes "no prior art"** — Zero results means the query was too narrow, not that no prior art exists. STOP. Broaden query with synonyms, adjacent tags, and cross-product search before concluding.
- **Agent recalls from memory instead of searching brain files** — Memory is subjective and lossy. STOP. Always search the actual brain directory; never rely on recalled summaries of decisions.
- **Recall is skipped because "this is a new problem"** — Cross-domain patterns appear in unexpected places. STOP. Search even when the problem feels novel.
- **Only the most recent result is used without reviewing all matches** — Recency bias misses more applicable older patterns. STOP. Review all matches and select based on relevance, not date.
- **Recall query uses only the current product name** — Patterns recorded under a different product name will be missed. STOP. Search across all products with domain-level tags.
- **Brain path is wrong or outdated** — Searching the wrong brain path produces incomplete results. STOP. Verify brain path from forge-product.md before searching.

Hybrid retrieval from persistent brain. Searches past decisions, patterns, learnings using grep + tags + product/project filtering.

## Task Scope Check (HARD-GATE)

Before recalling from `prds/<task-id>/`, confirm the active task-id:

```bash
echo "${FORGE_TASK_ID:-${FORGE_PRD_TASK_ID:-UNSET}}"
```

If `UNSET` and multiple tasks exist under `prds/`, ask the user which task is active before reading task-scoped paths. Product-level paths (`products/<slug>/`) are shared and safe to read without task scoping.

**HARD-GATE:** Do not search across all `prds/*/` when you need task-specific data — you will return results from other tasks and mix contexts.

## Overview

The brain-recall skill enables agents and developers to:
- Search historical decisions and patterns stored in the brain
- Filter results by product, project, tags, and date
- Rank results by relevance (recency, resolution status, same project/product)
- Surface similar patterns from other products for cross-project learning
- Link back to original decision documents for context

## 1. Grep-Based Search

Search the brain knowledge base for keywords across decision records, patterns, and learnings.

**Locations:**
- `~/forge/brain/decisions/` - decision records
- `~/forge/brain/patterns/` - architectural patterns
- `~/forge/brain/learnings/` - lessons learned
- `~/forge/brain/contracts/` - API/schema/event contracts

**Search command template:**
```bash
grep -r "KEYWORD" ~/forge/brain/{decisions,patterns,learnings,contracts}/ \
  --include="*.md" -l | head -20
```

**Examples:**
- Search for API versioning decisions:
  ```bash
  grep -r "API versioning" ~/forge/brain/decisions/ --include="*.md" -l
  ```
- Search for cache patterns:
  ```bash
  grep -r "cache" ~/forge/brain/patterns/ --include="*.md" -l
  ```
- Search across all brain documents:
  ```bash
  grep -r "eventual consistency" ~/forge/brain/ --include="*.md" -A 2
  ```

**Ranking within grep results:**
- Files with most recent dates in filename/frontmatter rank higher
- Files with "resolved" status rank higher than "open"
- Files matching both search keyword and product/project rank higher

## 2. Tag-Based Filtering

Filter decisions by structured tags. **Tags are a YAML array of bare words** in the
decision's frontmatter — `tags: [api, versioning, breaking-change]` — **not**
`#hashtags`. Lifecycle is a separate `status:` field (`active | warm | cold |
archived` per brain-write/brain-forget), **not** a tag like `#resolved`/`#open`.

**Common tag values** (bare words, domain/category): `api`, `database`, `cache`,
`frontend`, `mobile`, `events`, `search`, `infra`, `scaling`, `migration`,
`versioning`, `backward-compat`, `performance`, `observability`, `security`.

**Tag filtering strategies** (match inside the YAML `tags:` array):

### Single tag query
```bash
# Find all active API decisions
grep -rlE "^tags:.*\bapi\b" ~/forge/brain/decisions/ --include="*.md" \
  | xargs grep -l "^status: active"
```

### Multi-tag AND query
```bash
# Find database decisions tagged both 'migration' and 'performance'
grep -rlE "^tags:.*\bdatabase\b" ~/forge/brain/decisions/ --include="*.md" \
  | xargs grep -lE "^tags:.*\bmigration\b" | xargs grep -lE "^tags:.*\bperformance\b"
```

### Tag + status extraction from frontmatter
```bash
# Show the tags and status of each decision
grep -A 25 "^---" ~/forge/brain/decisions/**/*.md | grep -E "^(tags|status):"
```

**Example tag-based queries:**

- "Show me all database decisions"
  ```bash
  grep -rlE "^tags:.*\bdatabase\b" ~/forge/brain/decisions/ --include="*.md"
  ```

- "Which decisions are tagged both 'cache' and 'eventual-consistency'?"
  ```bash
  grep -rlE "^tags:.*\bcache\b" ~/forge/brain/decisions/ --include="*.md" \
    | xargs grep -lE "^tags:.*\beventual-consistency\b"
  ```

- "Show active decisions tagged 'security' (exclude archived)"
  ```bash
  grep -rlE "^tags:.*\bsecurity\b" ~/forge/brain/decisions/ --include="*.md" \
    | xargs grep -l "^status: active"
  ```

> The shipped read-only **brain MCP** `brain_recall` tool does this scan for you
> (case-insensitive substring over the brain) and computes the brain root itself —
> prefer it when configured; the greps above are the live fallback. See
> [`docs/brain-mcp.md`](../../docs/brain-mcp.md).

## 3. Product/Project Filtering

Filter brain records by product (slug under `products/<slug>/`) and the repos/projects in that product's `product.md`.

**Canonical decision frontmatter** (see `forge-brain-layout` / `brain-write`):
```yaml
---
title: Decision title
date_locked: 2026-04-10T14:30:00Z
status: active          # active | warm | cold | archived
category: product       # architecture | product | engineering | ops
decision_number: D102
tags: [api, versioning]
relates_to: [D001, D050]
---
```

Global decisions live at `decisions/<category>/D<NNN>_<topic>.md`; product-scoped
context lives under `products/<slug>/`. There is no top-level `product:`/`project:`
frontmatter pair on a global decision — scope comes from the path.

**Filtering by product:**
```bash
# All decisions for shopapp product
grep -l "product: shopapp" ~/forge/brain/decisions/*.md

# All patterns for production
grep -l "product: production" ~/forge/brain/patterns/*.md
```

**Filtering by project:**
```bash
# All decisions for backend-api project
grep -l "project: backend-api" ~/forge/brain/decisions/*.md
```

**Combined product + keyword search:**
```bash
# API decisions for shopapp product
grep -l "product: shopapp" ~/forge/brain/decisions/*.md | xargs grep -l "API versioning"
```

See [reference/examples.md](reference/examples.md) for more example product/project queries (API decisions for shopapp, web-dashboard learnings, production migrations).

## 4. Relevance Ranking

Results are ranked by multiple factors (descending priority): same product/project
match → lifecycle status (`active` > `warm` > `cold` > `archived`) → recency
(status-weighted, with decay for >730-day non-active decisions) → tag match count →
document-type priority. Archived/deprecated are de-prioritized by default.

See [reference/ranking.md](reference/ranking.md) for the full ranking criteria, the canonical status-tier scoring algorithm (the single source — the older duplicate has been collapsed into it), worked scoring examples, and all status/tag-combination filtering and deduplication recipes.

## 5. Output Format

Recalled decisions are formatted to provide context and traceability:

```markdown
## Result: [Decision Title]

**File:** `brain/decisions/YYYY-MM-DD-decision-name.md`

**Date:** YYYY-MM-DD  
**Product:** [product-name]  
**Project:** [project-name]  
**Status:** [resolved/open/deprecated]  
**Tags:** #tag1 #tag2 #tag3

**Context:**
[2-3 sentence summary of the problem/question that led to this decision]

**Decision/Pattern:**
[Key decision or pattern that was decided/discovered]

**Outcome/Rationale:**
[Why this decision worked or what we learned]

**Related Patterns:**
- [Link to related pattern in other product] (if applicable)
- [Link to related learnings]

**Conflicts Resolved:**
- [If decision resolved a conflict, list it here]

**Watch Out For:**
[Any gotchas or edge cases discovered]
```

See [reference/examples.md](reference/examples.md) for a fully filled-in example of this output template (API Versioning Strategy for shopapp).

## 6. Query Examples & Workflows

See [reference/examples.md](reference/examples.md) for the full query-and-workflow catalog (API versioning, eventual-consistency patterns, migration gotchas, project-scoped tag queries) plus end-to-end "brain recall in action" walkthroughs.

## 7. Implementation Notes

### Integration with brain-read skill
- brain-recall **builds on** brain-read (requires: [brain-read])
- brain-read handles artifact retrieval and basic queries
- brain-recall adds search, filtering, ranking, and cross-product pattern matching

### Brain directory structure (assumed)
```
~/forge/brain/
├── decisions/              # Decision records (YYYY-MM-DD-*.md)
├── patterns/               # Architectural patterns
├── learnings/              # Lessons learned & gotchas
├── contracts/              # API/schema/event contracts
└── README.md               # Brain metadata
```

### Performance notes
- Grep searches are O(n) across all files; consider indexing for >1000 files
- Tag-based queries can be optimized with a tag index file
- Relevance ranking should be computed at query time (not pre-cached)

### Error handling
- If no results found: suggest broader search or list available tags
- If multiple products match: show results grouped by product
- If query is ambiguous: ask for clarification (e.g., "Decision or Pattern?")

### Caching strategy
- Do NOT cache search results (brain updates frequently)
- Cache only brain metadata (directory structure, available products/projects)
- Invalidate cache on each brain-write operation

## 8. Integration with Forge Skills

### When to use brain-recall
- **During design phase:** "What patterns did we use for versioning?"
- **Before implementation:** "What gotchas exist for this pattern?"
- **During code review:** "How did we solve this in shopapp?"
- **Post-implementation:** "What did we learn from this decision?"

### Related skills
- **brain-read:** Basic artifact retrieval (use when you know the specific file)
- **brain-write:** Record new decisions (use after resolving a conflict)
- **contract-*:** Negotiate contracts (use before implementation)

## 9. Examples of Brain Recall in Action

See [reference/examples.md](reference/examples.md) for full worked examples (new engineer onboarding to caching, migrating a large table, designing API versioning for a new product).

## 10. Success Criteria

A brain-recall query is successful when:

- [x] **Relevance:** Top result directly answers the question
- [x] **Context:** Result includes decision date, product, project, status
- [x] **Traceability:** Link to original brain file is provided
- [x] **Completeness:** Related patterns from other products are surfaced
- [x] **Ranking:** Results are ranked by relevance (not random order)
- [x] **Speed:** Query completes in <2 seconds for <1000 brain files

---

## 11. Troubleshooting

See [reference/troubleshooting.md](reference/troubleshooting.md) for the Q&A catalog (no results, too many results, outdated result, can't find the exact pattern).

---

## 12. Retrieval Performance Edge Cases

These seven edge cases bite at scale (large brains, broad keywords, stale or
duplicated decisions, tag/terminology drift). Detect them, then mitigate or
escalate to `brain-why` / `brain-link` / `brain-write`:

| # | Edge case | One-line signal |
|---|---|---|
| 1 | Search returns 100+ results | Broad keyword, no product/status filter applied |
| 2 | Brain grown large (10k+), grep slow | `grep -r` >1s; multi-pipe queries >5s |
| 3 | Stale results (archived still returned) | `#archived`/`#deprecated` hit with no `superseded_by` |
| 4 | Cross-product duplication | Same title/pattern in 2+ products |
| 5 | Tag explosion (100+ tags) | `#cache` vs `#caching` vs `#redis` ambiguity |
| 6 | Semantic drift (same concept, different terms) | Zero hits for term that exists under a synonym |
| 7 | Recency over-weights drafts | Newest `#experimental` outranks proven `#pattern` |

See [reference/edge-cases.md](reference/edge-cases.md) for each edge case's full What/Why/How-to-detect/How-to-mitigate/When-to-escalate detail.

## 13. Ranking & Filtering Strategies

See [reference/ranking.md](reference/ranking.md) for the canonical ranking spec — the status-tier scoring algorithm (with worked scoring example), status filtering, AND/OR/NOT tag-combination recipes, result deduplication, and the pagination strategy.


## 14. Hybrid Search Decision Tree

**Use this flowchart to choose the right brain-recall strategy:**

```
START: I need to find something in the brain
│
├─→ "I know the exact file path"
│   └─→ USE: brain-read (faster, direct retrieval)
│       (brain/decisions/2025-01-15-api-versioning.md)
│
├─→ "I want to understand WHY a decision was made"
│   └─→ USE: brain-why (full provenance, decision history)
│       (traces decision back to original problem, context, alternatives)
│
├─→ "I want to map RELATIONSHIPS between decisions"
│   └─→ USE: brain-link (semantic edges, related patterns)
│       (shows: "Cache decisions are related to eventual-consistency patterns")
│
├─→ "I'm searching for something general (keyword/tag)"
│   │
│   ├─→ "Search is simple (1-2 keywords, no filters)"
│   │   └─→ USE: grep alone
│   │       grep -r "API versioning" ~/forge/brain/decisions/
│   │
│   ├─→ "I want to filter by product/status/tags"
│   │   └─→ USE: brain-recall with filters
│   │       product=shopapp tag=#pattern tag=#resolved
│   │       (grep + tag filtering + ranking)
│   │
│   ├─→ "Results exceed 50, need to narrow down"
│   │   └─→ USE: brain-recall with filters
│   │       Re-run with: product=X OR tag=#pattern OR date_range
│   │
│   └─→ "I need semantic search (similar concepts, synonyms)"
│       └─→ USE: brain-link (index-based, slow but semantic)
│           (finds: saga ≈ orchestration ≈ distributed transaction)
│
└─→ "I'm exploring brain structure/metadata"
    └─→ USE: brain-read (list products, projects, available tags)
        (brain/README.md, brain/TAG-GUIDE.md)
```

---

## 15. Common Recall Pitfalls

See [reference/pitfalls.md](reference/pitfalls.md) for the five common pitfalls (broad term, archived-still-returned, terminology mismatch, no ranking, tag spam) with the why-it-happens, how-to-fix command, and lesson for each.


## 16. Caching & Performance

See [reference/caching-performance.md](reference/caching-performance.md) for the search-result vs metadata caching strategy, when-to-re-search heuristics, the brain-growth-vs-grep-latency projection table, and the brain-link indexing migration path.


## 17. Production Readiness Checklist

See [reference/production-readiness.md](reference/production-readiness.md) for the one-time authoring-completeness checklist (search, filtering, ranking, edge cases, pitfalls, caching, growth projections).

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The query returned at least one file path (not an empty result set) — confirmed by the grep command outputting a line before piping to ranking
- [ ] The returned content was spot-checked against the original brain write: at least one field (e.g., `decision_id:`, `title:`, or `status:`) matches the source file to confirm no stale/overwritten content was returned
- [ ] The search was not limited to the current product — at least one cross-product or domain-level tag search was run to surface patterns from other products
- [ ] Archived and deprecated decisions were explicitly excluded from the primary results (grep includes `| grep -v "#archived" | grep -v "#deprecated"`) unless archived results were specifically requested
- [ ] The recall findings were documented (written out as output or fed into the next skill) before the downstream decision proceeded — not left only in chat

## Checklist

Before claiming recall is complete:

- [ ] Brain directory searched with at least 3 distinct query terms
- [ ] Cross-product search performed (not limited to current product)
- [ ] All matches reviewed by relevance, not just the most recent
- [ ] Zero-result queries retried with broader synonyms and domain-level tags
- [ ] Hybrid search used where applicable (grep → brain-read → brain-why for deep provenance)
- [ ] Recall findings documented before the decision proceeds


## Cross-References

- `brain-read`: Low-level reader used by brain-recall to load matching decision files from the brain.
- `brain-write`: Records new decisions; always run brain-recall first to avoid duplicating existing art.
- `brain-why`: Traces full provenance of a specific decision found by brain-recall.
- `brain-forget`: Archives superseded decisions; run brain-recall before forgetting to check for dependents.
- `brain-link`: Creates semantic edges between decisions; pair with brain-recall to find related decisions to link.
