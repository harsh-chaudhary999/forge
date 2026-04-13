---
name: brain-link
description: "Create semantic edges between decisions. Link concepts across products/projects/time. Query: \"All API versioning patterns\" or \"All eventual-consistency decisions\"."
type: rigid
requires: [brain-read]
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
- MUST create reverse links explicitly (if D42 `depends-on` D17, also create D17 `required-by` D42)
- MUST test traversal: "Show all decisions that replace D42" should return correct results, not reversed
- MUST document directionality in link metadata (mark forward-only links explicitly)
- MUST verify: one-directional `replaces` is correct; bidirectional `conflicts` is correct; variant should be directional (global → instance)

---

**If you are thinking any of the above, you are about to violate this skill.**

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A link is created without a declared `link_type`** — An untyped link is ambiguous: "related" means nothing specific when querying "what does D42 supersede?" or "what contradicts D42?". STOP. Every link must specify its type: `supersedes`, `depends-on`, `contradicts`, `implements`, `extends`, or `informs`.
- **Only a forward link is created without the reverse** — A one-directional link means queries from the target side return no results. STOP. Every link must be created in both directions: if D42 `depends-on` D17, D17 must also have a `required-by` link pointing to D42.
- **Links are created from memory of what decisions exist, not from brain-read** — Linking to a decision ID that doesn't exist creates dangling references that break provenance traces. STOP. Always query `brain-read` to verify both source and target decision IDs exist before creating any link.
- **A `supersedes` link is created without marking the superseded decision's status** — A supersedes link without a status update leaves the old decision appearing active. STOP. When creating a `supersedes` link, also update the superseded decision's status to `superseded` via brain-forget or brain-write.
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

Define how decisions relate to each other:

### **Related**
Decisions that influenced each other without formal ordering.
```
D40: REST design principles
  --related--> D41: Error handling strategy
  --related--> D42: Graduated API versioning
```
Use when decisions share context or emerged together.

### **Replaces**
Newer decision supersedes older decision. Tracks decision evolution.
```
D42: Graduated API versioning (2022-06)
  --replaces--> D89: Header-based versioning (2023-02)
  --replaces--> D127: Content-negotiation versioning (2024-01)
```
Use when a better approach emerges or constraints change.

### **Conflicts**
Mutually exclusive choices. Cannot both be true in same system.
```
D30: Cache-aside strategy
  --conflicts--> D31: Write-through caching
  --conflicts--> D32: Write-behind caching
```
Use when decisions represent alternative designs.

### **Complements**
Works together as a system. Neither sufficient alone.
```
D42: Graduated API versioning
  --complements--> D46: Error code taxonomy
  --complements--> D47: Deprecation timeline strategy
```
Use when decisions form a cohesive whole.

### **Variant**
Same pattern applied in different products/contexts. Allows "show all instances".
```
D42: Graduated API versioning (global decision)
  --variant--> D43 (shopapp instance)
  --variant--> D44 (production instance)
  --variant--> D45 (mobile instance)
```
Use when same pattern instantiated differently across products.

---

## 2. Semantic Tags

Tags enable cross-cutting queries and pattern discovery.

### Concept Tags
Abstract ideas and principles:
- `#api-versioning` — API evolution strategy
- `#eventual-consistency` — Consistency model
- `#cache-invalidation` — Cache freshness
- `#rate-limiting` — Traffic control
- `#observability` — Monitoring and tracing
- `#resilience` — Fault tolerance
- `#idempotency` — Repeated operation safety

### Pattern Tags
Proven design patterns:
- `#circuit-breaker` — Fault isolation
- `#bulkhead` — Resource isolation
- `#saga` — Distributed transaction
- `#bloom-filter` — Set membership
- `#backpressure` — Flow control
- `#exponential-backoff` — Retry strategy
- `#gossip` — Peer-to-peer sync

### Domain Tags
Business/feature areas:
- `#auth` — Authentication & authorization
- `#payments` — Payment processing
- `#search` — Search functionality
- `#notifications` — Messaging system
- `#inventory` — Stock management
- `#catalog` — Product data
- `#recommendations` — ML-based suggestions

### Architectural Tags
System design dimensions:
- `#async` — Asynchronous pattern
- `#sync` — Synchronous pattern
- `#hybrid` — Mixed sync/async
- `#event-driven` — Event-based architecture
- `#request-reply` — RPC-style communication
- `#publish-subscribe` — Pub/sub messaging
- `#database` — Data persistence
- `#cache` — In-memory storage

### Metadata Tags
Decision properties:
- `#breaking-change` — Client-incompatible
- `#deprecation` — Phased retirement
- `#rollback-plan` — Can unwind if needed
- `#tech-debt` — Known limitation
- `#performance-critical` — SLO-impacting
- `#security-critical` — Security-relevant

---

## 3. Cross-Product Linking

Link same decisions across product instances to enable cross-product queries.

### Product Inventory
Products in the system:
- `shopapp` — Customer shopping app
- `production` — Admin/operations dashboard
- `mobile` — Native mobile app
- `future-product` — Planned product

### Linking Strategy

**Global decision** → **Product instances**:
```
D42: Graduated API versioning (global, 2022-06)
  --variant--> D43 (shopapp, 2022-07)
       Product: shopapp
       Status: stable
       Notes: v1, v2, v3 endpoints active
  
  --variant--> D44 (production, 2022-08)
       Product: production
       Status: stable
       Notes: v1, v2 active; v0 deprecated
  
  --variant--> D45 (mobile, 2023-01)
       Product: mobile
       Status: stable
       Notes: v1 only (reduced API surface)
```

### Query Examples
- "Show D42 instances across all products"
- "Show all decisions on product=shopapp"
- "Show decisions tagged #api-versioning AND product=shopapp"

---

## 4. Cross-Time Linking

Track how decisions evolve and change over time.

### Evolution Chains
Show progression from original to current:
```
D42: Graduated API versioning (2022-06, REST endpoints)
  Status: stable
  Details: /v1/users, /v2/products, etc.
  
  --replaces--> D89: Header-based versioning (2023-02)
    Trigger: Reduced URL clutter, easier load balancing
    Details: X-API-Version: 2 header
    Status: stable
    
    --replaces--> D127: Content-negotiation versioning (2024-01)
      Trigger: GraphQL adoption, unified versioning strategy
      Details: Accept: application/vnd.api+json;version=2
      Status: current
```

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

Standard query syntax for decision graph traversal.

### Basic Queries

**By Decision ID**:
```
show decisions linked to D42
show D42 variants
show D42 successors
show D42 predecessors
```

**By Tag**:
```
show all decisions tagged #api-versioning
show decisions tagged #api-versioning AND #breaking-change
show decisions tagged (#circuit-breaker OR #bulkhead)
```

**By Product**:
```
show all decisions on product=shopapp
show decisions on product=shopapp AND tag=#async
show product=shopapp AND status=current
```

**By Domain**:
```
show decisions on domain=auth
show decisions on domain=auth AND tag=#resilience
```

### Advanced Queries

**Evolution Tracking**:
```
show evolution chain: D42 → current
show all replacements: D42 → D89 → D127 → ?
show change history: D42 (when/why/impact)
```

**Cross-Product Patterns**:
```
show all products using #api-versioning
show product=shopapp using pattern=#circuit-breaker
show decisions varying by product (D42 variants)
```

**Graph Traversal**:
```
show neighbors: D42 (depth=1)
show closure: D42 (depth=2)
show related-decisions: tag=#eventual-consistency (depth=all)
```

**Aggregations**:
```
count decisions by tag
count decisions by product
count decisions by status
show decisions created in Q2-2023
```

---

## 6. Data Model

### Decision Node
```
{
  id: "D42",
  title: "Graduated API versioning",
  created: "2022-06-15",
  product: ["shopapp", "production"],
  domain: "api",
  tags: ["#api-versioning", "#sync", "#breaking-change"],
  status: "stable" | "current" | "deprecated" | "retired",
  summary: "Support multiple API versions via URL path (/v1, /v2)",
  details: { ... },
  link_refs: ["D40", "D41", "D89"]
}
```

### Link Edge
```
{
  from: "D42",
  to: "D89",
  type: "replaces",
  when: "2023-02-20",
  why: "Reduce URL clutter, improve load balancing",
  status: "stable",
  impact: {
    products: ["shopapp", "production"],
    breaking: true,
    migration_timeline: "6 months"
  }
}
```

### Tag Index
```
{
  tag: "#api-versioning",
  decisions: ["D40", "D42", "D43", "D44", "D45", "D89", "D127"],
  count: 7,
  products: ["shopapp", "production", "mobile"],
  domains: ["api"]
}
```

---

## 7. Example Graph

Complete decision graph showing all relationship types:

```
D40: REST design principles (2022-04)
  tags: #sync, #api
  ├─→ (complements) D41: Error handling strategy
  │    └─→ (variant) D41a (shopapp), D41b (production)
  │
  └─→ (complements) D42: Graduated API versioning
       tags: #api-versioning, #sync, #breaking-change
       ├─→ (variant) D43 (shopapp, 2022-07)
       │    tags: product=shopapp
       │    ├─→ (complements) D46: Error code taxonomy
       │    │    tags: #error-handling, #api
       │    │    ├─→ (variant) D46a (shopapp), D46b (production)
       │    │    └─→ (related) D47: Deprecation timeline
       │    │
       │    └─→ (replaces) D89: Header-based versioning (2023-02)
       │         tags: #api-versioning, #sync
       │         migration_timeline: "6 months"
       │         ├─→ (variant) D89a (shopapp), D89b (production)
       │         └─→ (replaces) D127: Content-negotiation (2024-01)
       │              tags: #api-versioning, #async-ready
       │              status: current
       │
       ├─→ (variant) D44 (production, 2022-08)
       │    tags: product=production
       │    └─→ (complements) D46: Error code taxonomy
       │
       └─→ (variant) D45 (mobile, 2023-01)
            tags: product=mobile, #mobile

D30: Cache-aside strategy (2021-11)
  tags: #cache, #eventual-consistency
  ├─→ (conflicts) D31: Write-through caching
  ├─→ (conflicts) D32: Write-behind caching
  ├─→ (complements) D20: Cache invalidation
  │    tags: #eventual-consistency, #cache-invalidation
  │    └─→ (related) D70: Search freshness SLO
  │         tags: #search, #eventual-consistency
  │
  └─→ (variant) D30a (shopapp), D30b (production)

D50: Kafka for events (2023-06)
  tags: #event-driven, #async, #resilience
  ├─→ (complements) D51: Dead-letter queue strategy
  │    tags: #error-handling, #resilience
  ├─→ (complements) D52: Event versioning
  │    tags: #api-versioning, #event-driven
  │    └─→ (replaces) D100: Header-based event versioning
  │
  └─→ (variant) D50a (shopapp), D50b (production)

Tag: #api-versioning
  Decisions: D40, D42, D43, D44, D45, D46, D89, D127, D52
  Concepts: API evolution, backward compatibility
  Products: shopapp, production, mobile

Tag: #eventual-consistency
  Decisions: D20, D30, D30a, D30b, D70
  Concepts: Consistency model, cache freshness
  Domains: search, notifications

Product: shopapp
  Decisions: D1-D100 (full product topology)
  Tags: #api-versioning, #async, #cache, #resilience
  Status: production
```

---

## 8. Usage Examples

### Query: "Show all API versioning patterns"
```
brain-link: query tag=#api-versioning

Results:
├─ D40: REST design principles (2022-04) [related decisions]
├─ D42: Graduated API versioning (2022-06) [anchor]
│  ├─ D43 (shopapp variant, 2022-07)
│  ├─ D44 (production variant, 2022-08)
│  ├─ D45 (mobile variant, 2023-01)
│  ├─ D46: Error code taxonomy (complements)
│  ├─ D47: Deprecation timeline (related)
│  └─ D89: Header-based versioning (replaces, 2023-02)
│     └─ D127: Content-negotiation (replaces, 2024-01) [current]
├─ D52: Event versioning (2023-08)
│  └─ D100: Header-based event versioning (replaces)
└─ (7 total decisions)

Insights:
- Evolution: URL → Headers → Content-negotiation
- Pattern adopted across 3 products
- 2 generations, 1 current approach
- Related: error handling, deprecation, domain-based strategy
```

### Query: "Show all decisions linked to D42"
```
brain-link: show D42 closure (depth=all)

Results:
Direct links (depth=1):
  ← D40: REST design (related)
  ← D41: Error handling (related)
  → D43, D44, D45 (variants)
  → D46: Error codes (complements)
  → D47: Deprecation (related)
  → D89: Header versioning (replaces)

Transitive links (depth=2):
  → D46 → D46a, D46b (variants)
  → D47 → D48: Sunset strategy (related)
  → D89 → D89a, D89b (variants)
  → D89 → D127: Content-negotiation (replaces)

Full closure: [D40, D41, D42, D43, D44, D45, D46, D46a, D46b, 
              D47, D48, D89, D89a, D89b, D127]
(15 decisions in full closure)
```

### Query: "Show evolution chain: D42 → current"
```
brain-link: evolution D42

Timeline:
┌─────────────────────────────────────────────────────┐
│ D42: Graduated API versioning (2022-06)             │
│ Pattern: URL path versioning (/v1, /v2)              │
│ Status: stable, active in shopapp, production       │
│ Products: shopapp, production, mobile               │
└─────────────────────────────────────────────────────┘
                        ↓ (replaces)
          Why: Reduce URL clutter, simpler
          When: 2023-02
          Migration: 6 months
┌─────────────────────────────────────────────────────┐
│ D89: Header-based versioning (2023-02)              │
│ Pattern: X-API-Version header                       │
│ Status: stable, active in shopapp, production       │
│ Benefits: Cleaner URLs, better load balancing       │
└─────────────────────────────────────────────────────┘
                        ↓ (replaces)
          Why: Unified strategy for GraphQL
          When: 2024-01
          Migration: 3 months
┌─────────────────────────────────────────────────────┐
│ D127: Content-negotiation versioning (2024-01)      │
│ Pattern: Accept header (application/vnd.api+...)   │
│ Status: current                                     │
│ Benefits: GraphQL + REST unified, W3C standard      │
└─────────────────────────────────────────────────────┘

Change drivers:
- Load balancing constraints → headers
- GraphQL adoption → content negotiation
- Operational simplification → unified strategy
```

### Query: "Show decisions on product=shopapp AND tag=async"
```
brain-link: query product=shopapp tag=#async

Results:
├─ D50: Kafka for events (2023-06)
│  ├─ D50a (shopapp variant)
│  └─ D51: Dead-letter queue strategy (complements)
├─ D70: Search freshness SLO (2023-09)
│  └─ D71: Search async indexing (relates)
└─ D85: Background job processing (2024-02)
   └─ D86: Retries + exponential backoff (complements)

(3 decisions)

Insights:
- All async decisions involve event/messaging
- All include resilience/error handling complements
- Timeline: 2023-2024, recent additions
```

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

### Edge Case 1: Circular Link Graph

**Symptom**: D001 complements D002, D002 replaces D001, creating a cycle.

**Do NOT**: Silently accept the cycle. Circular dependencies in a decision graph indicate unresolved conflicts or miscategorized relationships.

**Action**:
1. Detect cycle before write (graph validation during link creation)
2. Reject with error message listing the cycle: "Cannot create link D002 replaces D001: would create cycle D001 → D002 → D001"
3. Prompt user: "Did you mean variant relationship instead of replaces? Or does this indicate two conflicting decisions that should both be marked?"

**Escalation**: NEEDS_CONTEXT
- User must clarify: Is this variant instantiation? Bidirectional conflict? Misclassified relationship?
- If true circular dependency exists, both decisions need status review (cannot both be active)

---

### Edge Case 2: Decision Superseded by Multiple Heirs

**Symptom**: D003 replaces D001 AND D007 replaces D001 (parallel supersession).

**Do NOT**: Treat as invalid — this is valid in parallel supersession scenarios (e.g., different products adopt different successors).

**Action**:
1. Accept link creation (this is valid)
2. Mark D001 status = `superseded` (not `deprecated`)
3. Reference both successors in D001's metadata: `succeeded_by: [D003, D007]`
4. Ensure each heir has `replaces: D001` link explicitly
5. Document why parallel supersession occurred (product divergence, feature split, etc.)

**Escalation**: NEEDS_COORDINATION
- When multiple heirs exist, council should document the split point
- Each heir must have clear domain/product scope so they don't create false conflicts

---

### Edge Case 3: Link Target Not Found

**Symptom**: `brain-link create D042 replaces D099` but D099.md doesn't exist in the brain.

**Do NOT**: Create dangling link pointing to non-existent decision.

**Action**:
1. Search brain for near-match (similar ID range, similar creation date, similar tags)
2. Return candidates: "Did you mean D098 (similar era) or D109 (similar domain)?"
3. If no match found, reject with error: "D099 not found in brain. Create decision first, then link."
4. Store as tombstone link if D099 is confirmed deleted: `replaces: D099 [ARCHIVED]`

**Escalation**: NEEDS_CONTEXT
- If target is confirmed deleted (in brain archive), document as superseded by archive
- If target never existed, return error: user must verify ID before linking

---

### Edge Case 4: Conflicting Links Between Active Decisions

**Symptom**: D010 conflicts D015, both status=active, both in production across multiple products.

**Do NOT**: Silently coexist. Active conflicting decisions indicate unresolved architectural choice.

**Action**:
1. Detect conflict during link creation
2. Query both decisions: confirm both are status=active
3. Escalate with warning: "Creating conflict between two active decisions. One must be deprecated."
4. Force user to: mark one as deprecated OR verify they serve different products
5. If product-divergent, update link metadata: `applies_to: {D010: [product_a, product_b], D015: [product_c, product_d]}`

**Escalation**: NEEDS_COORDINATION
- Active conflicts require council decision to resolve
- Document resolution in both decisions: "Conflict resolved Q3-2024: D010 for product_a, D015 for product_c"
- Set timeline for convergence (if applicable)

---

### Edge Case 5: Graph Traversal Timeout on Large Brain

**Symptom**: `brain-link query tag=#api-versioning depth=all` returns partial results after 5-second timeout on brain with >500 decisions.

**Do NOT**: Use partial results for analysis. Partial graph closure gives false negatives.

**Action**:
1. Detect timeout during query execution
2. Return partial results with warning: "Query incomplete (timeout). 287 of ~400 decisions returned."
3. Suggest narrowing: "Add filter: `tag=#api-versioning AND product=shopapp` (returns in <1s)"
4. Suggest depth limit: "Use `depth=2` instead of `depth=all` (returns immediate neighbors)"
5. Recommend indexing: "For >500 decisions, enable tag index via brain-read config"

**Escalation**: NEEDS_CONTEXT
- User should narrow query using product/tag filters
- If full graph traversal required, may need to optimize brain structure (split by domain)
- For production brains >1000 decisions, graph indexing becomes mandatory

---

## 12. Decision Trees

### Decision Tree 1: Which Link Type to Use?

```
START: You need to link two decisions

├─ Are these decisions equivalent across products/contexts?
│  ├─ YES → Use VARIANT
│  │        (D42 global → D43 shopapp instance)
│  │        Direction: global → instance
│  │        Query: "Show all instances of D42"
│  │
│  └─ NO → Continue

├─ Does one decision replace/supersede the other?
│  ├─ YES → Use REPLACES
│  │        (D42 v1 → D89 v2)
│  │        Direction: old → new (required)
│  │        Query: "Evolution chain: D42 → current"
│  │        Also mark old as status=deprecated/superseded
│  │
│  └─ NO → Continue

├─ Are these decisions mutually exclusive?
│  ├─ YES → Use CONFLICTS
│  │        (cache-aside vs write-through)
│  │        Direction: bidirectional (both directions okay)
│  │        Query: "Alternatives to D30"
│  │        Note: Both active only if they apply to different products
│  │
│  └─ NO → Continue

├─ Do these decisions work together to form a system?
│  ├─ YES → Use COMPLEMENTS
│  │        (API versioning + deprecation strategy)
│  │        Direction: bidirectional (both directions okay)
│  │        Query: "What goes with D42?"
│  │        Note: Neither sufficient alone
│  │
│  └─ NO → Continue

└─ Do these decisions share context but no formal relationship?
   └─ YES → Use RELATED
            (REST principles ← → Error handling)
            Direction: bidirectional (both directions okay)
            Query: "Related to D40"
            Note: Weakest link type; use sparingly

END: Link created with correct type
```

---

### Decision Tree 2: Bidirectional vs Directional Link

```
START: You've chosen a link type. Create forward or reverse link too?

├─ Link type is REPLACES?
│  ├─ YES → DIRECTIONAL ONLY
│  │        Create: D42 --replaces--> D89
│  │        Do NOT create: D89 --replaces--> D42
│  │        Reason: Direction matters for evolution queries
│  │        Test: "Show what replaced D42" should find D89, not vice versa
│  │
│  └─ NO → Continue

├─ Link type is VARIANT?
│  ├─ YES → DIRECTIONAL ONLY
│  │        Create: D42_global --variant--> D43_shopapp
│  │        Direction: abstract/global → concrete/instance
│  │        Do NOT reverse (instance → global doesn't make sense)
│  │        Test: "Show instances of D42" finds D43, D44, D45
│  │
│  └─ NO → Continue

├─ Link type is CONFLICTS?
│  ├─ YES → BIDIRECTIONAL
│  │        Create: D30 <--conflicts--> D31
│  │        Reason: Conflict is symmetric
│  │        Test: "What conflicts with D30" finds D31, and vice versa
│  │
│  └─ NO → Continue

├─ Link type is COMPLEMENTS?
│  ├─ YES → BIDIRECTIONAL
│  │        Create: D42 <--complements--> D46
│  │        Reason: Complementary relationship is mutual
│  │        Test: "What goes with D42" finds D46, and vice versa
│  │
│  └─ NO → Continue

└─ Link type is RELATED?
   └─ YES → BIDIRECTIONAL
            Create: D40 <--related--> D41
            Reason: Related is symmetric
            Test: "Related to D40" finds D41, and vice versa

END: Link created with correct directionality
     Verify: Can you traverse from both directions?
```

---

## 13. Extending brain-link

Future enhancements:

- **Impact analysis**: "Which decisions would be affected if we change D42?"
- **Change impact**: "Which products would be affected by deprecating D89?"
- **Pattern suggestions**: "You're considering a saga pattern — here are similar decisions"
- **Cross-linking**: Link to code (commit SHAs, file paths, class definitions)
- **Timeline visualization**: Calendar view of decision evolution
- **Collaboration**: Decision committee tracking, approval chains

---

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
- Important: Mark `status=superseded` before archival to preserve provenance in the graph

**Usage Flow**:
```
1. brain-write: Create new decision D100
2. brain-link: Link D100 to related decisions (D42, D89, etc.)
3. brain-recall: Query to find all related decisions and verify links
4. brain-why: Trace decision history and link provenance
5. brain-forget: Archive old decisions after marking with replaces link
```

---

## 15. Glossary

**Bidirectional Link**: A link that travels in both directions. Used for CONFLICTS, COMPLEMENTS, RELATED. Query "What conflicts with D30?" finds D31 and vice versa.

**Circular Dependency**: A cycle in the link graph (D1 → D2 → D1). Invalid in decision graphs; indicates unresolved conflicts or miscategorization.

**Closure** (graph closure): The set of all reachable decisions from a starting decision, following all link types up to a specified depth.

**Decision Node**: A single decision (D42) with metadata: ID, title, creation date, product, domain, tags, status, summary.

**Directional Link**: A link with a source and target that are not interchangeable. Used for REPLACES and VARIANT. "D42 replaces D89" ≠ "D89 replaces D42".

**Provenance**: The history of when and why a link was created. Essential for understanding decision rationale.

**Supersession**: When one decision replaces another. Created with `replaces` link. Old decision marked `status=superseded`.

**Variant**: An instance of a pattern applied in a different product or context. Created with `variant` link. Used for cross-product queries.

---

## 16. Index

- **Link Types**: Related, Replaces, Conflicts, Complements, Variant (Section 1)
- **Semantic Tags**: Concept, Pattern, Domain, Architectural, Metadata (Section 2)
- **Cross-Product Linking**: Strategy for global → instance links (Section 3)
- **Cross-Time Linking**: Evolution chains and change rationale (Section 4)
- **Query Interface**: Basic and advanced query syntax (Section 5)
- **Data Model**: Decision nodes, link edges, tag indexes (Section 6)
- **Example Graph**: Complete decision graph with all relationship types (Section 7)
- **Usage Examples**: Four detailed example queries (Section 8)
- **Integration with brain-read**: Complementary skills and workflow (Section 9)
- **Best Practices**: When to link, link hygiene, tag strategy, query strategy (Section 10)
- **Edge Cases**: 5 edge cases with escalation paths (Section 11)
- **Decision Trees**: Link type selection and directionality (Section 12)
- **Related Skills**: brain-write, brain-why, brain-recall, brain-forget (Section 14)
