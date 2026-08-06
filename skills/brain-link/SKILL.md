---
name: brain-link
description: "WHEN: You are writing a new decision, superseding an old one, or querying relationships across decisions. Create semantic edges between decisions and link concepts across products/projects/time."
type: flexible
requires: [brain-read]
version: 1.0.0
preamble-tier: 2
triggers:
  - "link brain files"
  - "cross-reference decisions"
  - "connect brain entries"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
---

# brain-link: Semantic Decision Linking

## Anti-Pattern Preamble

**CRITICAL: Read this section before creating any link. These anti-patterns corrupt the decision graph.**

### 1. "Just link everything to D001 (the founding decision)"

**Why it fails**: Star topology with single hub creates fake dependency chains, obscures real influence patterns, makes graph traversal meaningless.

**Enforcement — MUST:**
- MUST distribute links across the graph; no decision should have >10 inbound links from unrelated siblings
- MUST use semantic link types (replaces, conflicts, complements, variant); never use "related" as a catch-all
- MUST avoid hub topology; instead, organize by domain/product/pattern
- MUST validate that links reflect actual dependency, not just temporal proximity to founding decision
- MUST test: if you delete D001, should the graph still be coherent? If not, you've over-linked

### 2. "A 'related' link covers all semantic relationships"

**Why it fails**: Using only `related` destroys graph's traversal value. `replaces`/`conflicts`/`complements`/`variant` enable different query paths. A brain-recall query for "all decisions that replaced D42" returns nothing if you used `related`.

**Enforcement — MUST:**
- MUST specify exact link type; "related" is only for decisions with shared context but no formal relationship
- MUST use `replaces` for supersession chains (enables evolution queries)
- MUST use `conflicts` for mutually-exclusive choices (enables consistency analysis)
- MUST use `complements` for decisions that form a system (enables cohesion queries)
- MUST use `variant` for pattern instances across products (enables cross-product queries)

### 3. "Link creation is low-cost, do it retroactively"

**Why it fails**: Retroactive links lack provenance. When was relationship known? Who made decision knowing about the other? Retroactive links are reconstructions, not records.

**Enforcement — MUST:**
- MUST create links at decision time, immediately after writing decision
- MUST document provenance: when was the link created, who created it, what was the context
- MUST timestamp every link (not just decisions)
- MUST refuse to batch-create links after multiple decisions are written
- MUST attach rationale: if D005 replaces D002, include "why" in link metadata

### 4. "I can infer what's linked from the content"

**Why it fails**: Without explicit links, brain-recall and brain-why cannot traverse the graph. Inferences don't persist. Future searchers see isolated decisions, not patterns.

**Enforcement — MUST:**
- MUST create explicit links; inference is not an alternative
- MUST understand that semantic graph traversal requires edge metadata, not just decision content
- MUST verify links exist before querying (don't assume the graph knows what you know)
- MUST tag decisions with concept tags; then query by tag to find patterns
- MUST use brain-link commands to verify links before relying on them in analysis

### 5. "Link is bidirectional by default"

**Why it fails**: `replaces` is directional. D005 replaces D002 ≠ D002 replaces D005. Incorrect direction corrupts supersession queries.

**Enforcement — MUST:**
- MUST check directionality before creating link; test: "Does A → B express the relationship correctly? What about B → A?"
- MUST record the reverse side explicitly (a `replaces` link sets `superseded_by: D42` on D17; a `related`/`conflicts`/`complements`/`variant` link is written on both decisions' `related_decisions`)
- MUST test traversal: "Show all decisions that replace D42" should return correct results, not reversed
- MUST document directionality in link metadata (mark forward-only links explicitly)
- MUST verify: one-directional `replaces` is correct; bidirectional `conflicts` is correct; variant should be directional (global → instance)

---

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EVERY SEMANTIC EDGE MUST INCLUDE A DECLARED LINK TYPE, DIRECTIONALITY, AND PROVENANCE (WHEN IT WAS CREATED AND WHY). A LINK WITHOUT THESE THREE ELEMENTS IS NOT A LINK — IT IS NOISE THAT CORRUPTS THE DECISION GRAPH.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A link is created without a declared link type** — An untyped link is ambiguous: "related" means nothing specific when querying "what does D42 replace?" or "what conflicts with D42?". STOP. Every link must specify one of the canonical types defined in §1: `related`, `replaces`, `conflicts`, `complements`, or `variant`.
- **Only a forward link is created without the reverse** — A one-directional link means queries from the target side return no results. STOP. Record both sides: a `replaces` link sets `superseded_by:` on the older decision; the reciprocal types (`related`/`conflicts`/`complements`/`variant`) are written on both decisions' `related_decisions` frontmatter.
- **Links are created from memory of what decisions exist, not from brain-read** — Linking to a decision ID that doesn't exist creates dangling references that break provenance traces. STOP. Always query `brain-read` to verify both source and target decision IDs exist before creating any link.
- **A `replaces` link is created without marking the superseded decision** — leaving the old decision appearing active. STOP. When creating a `replaces` link, also set `superseded_by: D<new>` on the older decision and demote its status (`active` → `warm` → `cold`) via brain-forget/brain-write. There is no `superseded` status value — the canonical lifecycle is `active | warm | cold | archived`.
- **Links are batched and created after multiple decisions are written** — Links created after the fact are reconstructions — they lose the reasoning that was present at decision time. STOP. Create links immediately when writing each decision.
- **Link target is a product or project ID instead of a specific decision ID** — Coarse-grained links don't support precise provenance queries. STOP. Links must always point to specific decision IDs (e.g., `D42`), never to product slugs or repo names.

Link decisions across products, projects, and time. Create a queryable graph of decision relationships, patterns, and evolution.

## Overview

The brain-link skill enables semantic connections between decisions, allowing you to:
- Trace decision lineage and evolution
- Find related decisions across products and projects
- Discover pattern instances (e.g., all circuit-breaker implementations)
- Answer cross-domain queries (e.g., "All eventual-consistency patterns")

Built on top of brain-read, which provides decision metadata and history.

---

## 1. Link Types

Define how decisions relate to each other. These five are canonical — every link
declares exactly one:

- **Related** — decisions that influenced each other without formal ordering. Use
  when decisions share context or emerged together. Bidirectional.
- **Replaces** — newer decision supersedes older; tracks decision evolution. Use
  when a better approach emerges or constraints change. Directional (old → new).
- **Conflicts** — mutually exclusive choices; cannot both be true in same system.
  Use when decisions represent alternative designs. Bidirectional.
- **Complements** — works together as a system; neither sufficient alone. Use
  when decisions form a cohesive whole. Bidirectional.
- **Variant** — same pattern applied in different products/contexts; allows "show
  all instances". Use when a pattern is instantiated differently across products.
  Directional (global → instance).

Worked example notation for each type:
```
related:     D40 --related--> D41 --related--> D42
replaces:    D42 (2022-06) --replaces--> D89 (2023-02) --replaces--> D127 (2024-01)
conflicts:   D30 --conflicts--> D31 ; D30 --conflicts--> D32
complements: D42 --complements--> D46 ; D42 --complements--> D47
variant:     D42 (global) --variant--> D43 (shopapp) / D44 (production) / D45 (mobile)
```
See [reference/example-graph.md](reference/example-graph.md) for these types
composed into a full graph.

---

## 2. Semantic Tags

Tags enable cross-cutting queries and pattern discovery. Stored as a YAML array
in each decision's frontmatter (`tags: [...]`, no `#` on disk); the `#` prefix is
the query/display convention.

See [reference/tags.md](reference/tags.md) for the full tag catalog (concept,
pattern, domain, architectural, and metadata tags).

---

## 3. Cross-Product Linking

Link same decisions across product instances to enable cross-product queries.

### Product Inventory
Product slugs are **per-operator** — read the real list from `~/forge/brain/products/*/forge-product.md`
before linking; do not assume these. The names below are **illustrative only**:
- `shopapp` — (example) customer shopping app
- `production` — (example) admin/operations dashboard
- `mobile` — (example) native mobile app

### Linking Strategy

**Global decision** → **product instances**: write one `variant` link per product
(global → instance), recording each instance's product, status, and notes. See
[reference/cross-linking-examples.md](reference/cross-linking-examples.md) for a
worked global→instance illustration.

### Query Examples
- "Show D42 instances across all products"
- "Show all decisions on product=shopapp"
- "Show decisions tagged #api-versioning AND product=shopapp"

---

## 4. Cross-Time Linking

Track how decisions evolve and change over time.

### Evolution Chains
Show progression from original to current by chaining `replaces` links
(old → new), recording trigger, details, and status at each hop. See
[reference/cross-linking-examples.md](reference/cross-linking-examples.md) for a
worked three-hop evolution chain.

### Tracking Change Rationale
Include in each link:
- **When**: Timeline
- **Why**: Trigger/justification (constraints, learnings, new tech)
- **Status**: current, stable, deprecated, retired
- **Impact**: affected products/services

### Query Examples
- "Show evolution chain: D42 → ... → current"
- "Show all decisions that replaced D42"
- "Show all deprecated decisions on product=shopapp"

---

## 5. Query Interface

Standard query syntax for decision graph traversal. Common cases:

```
show decisions linked to D42        # neighbors
show D42 closure (depth=2)          # bounded traversal
show all decisions tagged #api-versioning
show all decisions on product=shopapp AND status=current
show evolution chain: D42 → current
```

See [reference/query-interface.md](reference/query-interface.md) for the full
query catalog (by decision ID / tag / product / domain, plus advanced evolution,
cross-product, graph-traversal, and aggregation queries).

---

## 6. Data Model

The link data model (entity/edge schema, storage representation, fields) is in [reference/data-model.md](reference/data-model.md).

## 7. Example Graph

See [reference/example-graph.md](reference/example-graph.md) for a complete
decision graph showing all relationship types plus tag/product rollups.

---

## 8. Usage Examples

See [reference/examples.md](reference/examples.md) for four worked query
examples (tag query, closure, evolution chain, product+tag) with result shapes
and insight summaries.

---

## 9. Integration with brain-read

Use brain-link alongside brain-read:

```
1. brain-read: Look up decision D42
2. brain-link: Query "show D42 closure"
3. brain-read: Load each linked decision for full context
4. brain-link: Query evolution chain
5. brain-read: Load specific variants by product
```

The two skills are complementary:
- **brain-read**: Metadata, history, rationale for a single decision
- **brain-link**: Relationships, patterns, cross-product/cross-time discovery

---

## 10. Best Practices

### When to Create Links

1. **After recording a decision**: Link it to related decisions immediately
2. **During decision evolution**: Create replaces link + document change driver
3. **Cross-product adoption**: Create variant links for each product instance
4. **Pattern discovery**: Tag decisions, then query to find all instances

### Link Hygiene

- Keep link descriptions short and specific
- Include "when" and "why" for replaces links
- Tag consistently (use canonical tag names)
- Document migration timelines for breaking changes
- Update status as decisions age

### Tag Strategy

- Use both specific and general tags (e.g., both #api-versioning and #sync)
- Create domain tags for each product/feature area
- Reserve pattern tags for established patterns
- Use metadata tags (#breaking-change, #deprecation) sparingly and intentionally

### Query Strategy

- Start with tag queries for pattern discovery
- Use product queries to understand product topology
- Use evolution queries to learn decision history
- Use depth-limited closure queries for manageable subgraphs

---

## 11. Edge Cases

Summary (full symptom / Do-NOT / action / escalation in the reference):

| # | Edge case | First move | Escalation |
|---|---|---|---|
| 1 | Circular link graph (D1↔D2 cycle) | Detect + reject before write; list the cycle | NEEDS_CONTEXT |
| 2 | Decision superseded by multiple heirs | Accept; mark old superseded, `succeeded_by: [..]` | NEEDS_COORDINATION |
| 3 | Link target not found | Search near-match; reject if none; no dangling link | NEEDS_CONTEXT |
| 4 | Conflicting links between active decisions | Warn; deprecate one or scope by product | NEEDS_COORDINATION |
| 5 | Graph traversal timeout on large brain | Don't use partial results; narrow filter / limit depth | NEEDS_CONTEXT |

See [reference/edge-cases.md](reference/edge-cases.md) for the full detail on all
five edge cases.

---

## 12. Decision Trees

Quick selection summary (full walkthroughs in the reference):

| If the two decisions are… | Use | Directionality |
|---|---|---|
| equivalent across products/contexts | `variant` | directional (global → instance) |
| one supersedes the other | `replaces` | directional (old → new); mark old superseded |
| mutually exclusive | `conflicts` | bidirectional |
| working together as a system | `complements` | bidirectional |
| sharing context, no formal relationship | `related` | bidirectional (use sparingly) |

See [reference/decision-trees.md](reference/decision-trees.md) for the two full
decision trees (link-type selection and bidirectional-vs-directional).

---

## 13. Extending brain-link

See [reference/glossary-index.md](reference/glossary-index.md) for planned
future enhancements (impact analysis, change impact, pattern suggestions,
code cross-linking, timeline visualization, collaboration).

---

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The link file (or link metadata embedded in the decision file) exists at the expected brain path and is readable via `cat` or `Read`
- [ ] The target decision the link points to exists — verified with `grep -r "^decision_id: <target-id>" ~/forge/brain --include="*.md"` returning a result
- [ ] The git commit includes the link file (or the updated decision file containing the link), confirmed via `git -C ~/forge/brain log --oneline -1 -- <path>`
- [ ] No broken link — for `replaces`/`variant` directional links, the reverse link was also created and verified to exist
- [ ] The link type is explicitly declared (`replaces`, `conflicts`, `complements`, `variant`, or `related`) — not left untyped or defaulting to a catch-all

## 14. Cross-References

### Related Skills

**brain-write**: Create decisions that brain-link will connect
- Use when: Recording a new decision that will become a node in the decision graph
- Integration: After writing a decision with `brain-write`, immediately use `brain-link` to connect it to related decisions
- Link at write time: Don't batch link creation after multiple decisions

**brain-why**: Trace provenance of any decision
- Use when: You need to understand why a link exists and who created it
- Integration: Use `brain-why` to trace link creation, revision history, and rationale
- Example: "Why does D42 replace D89? When was this decision made? What was the context?"

**brain-recall**: Search for patterns in the decision graph
- Use when: You want to find decisions by tag, product, or domain
- Integration: `brain-recall` provides full-text search; `brain-link` provides graph traversal
- Example: Search for `#api-versioning`, then use `brain-link` to find evolution chain

**brain-forget**: Archive deprecated decisions
- Use when: A decision is superseded and should be retired
- Integration: Use `brain-link` to create the `replaces` link, then `brain-forget` to archive the old decision
- Important: Mark `status=cold` (there is no `superseded` status value — see Red Flags above) and set `superseded_by:` before archival to preserve provenance in the graph

**Usage Flow**:
```
1. brain-write: Create new decision D100
2. brain-link: Link D100 to related decisions (D42, D89, etc.)
3. brain-recall: Query to find all related decisions and verify links
4. brain-why: Trace decision history and link provenance
5. brain-forget: Archive old decisions after marking with replaces link
```

---

## 15. Glossary & Index

See [reference/glossary-index.md](reference/glossary-index.md) for term
definitions (bidirectional/directional link, closure, supersession, variant,
etc.) and the section-by-section topic index mapping each topic to its inline
section or `reference/*.md` file.

## Checklist

Before claiming completion:

- [ ] Both source and target decision IDs verified to exist in the brain via brain-read before creating any link
- [ ] Every link has an explicit `link_type` — never left as untyped or defaulting to "related"
- [ ] Directionality is correct — `replaces` and `variant` are directional; `conflicts`, `complements`, `related` are bidirectional (reverse link created)
- [ ] Link includes provenance: `when` it was created and `why` the relationship exists
- [ ] If a `supersedes` link was created, the superseded decision's status was updated to `cold` (not `superseded` — no such status value) via brain-forget or brain-write
- [ ] No graph cycles introduced — traversal from source does not loop back to source
- [ ] Links were created immediately at decision time, not batched after multiple decisions were written
