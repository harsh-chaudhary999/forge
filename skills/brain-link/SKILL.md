---
name: brain-link
description: Create semantic edges between decisions. Link concepts across products/projects/time. Query: "All API versioning patterns" or "All eventual-consistency decisions".
type: rigid
requires: [brain-read]
---

# brain-link: Semantic Decision Linking

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "These decisions are obviously related, I don't need to link them" | Obvious to you now is invisible to future searchers. Explicit links are the only way brain-recall finds cross-references. |
| "I'll link them later when I have more context" | Links created at decision time capture the reasoning. Links added later are reconstructions — less accurate, often forgotten. |
| "One link type is enough" | Different link types (supersedes, depends-on, contradicts, implements) answer different questions. Wrong type = misleading graph. |
| "I'll link to the product, not the specific decision" | Product-level links are too coarse. Link to the specific decision ID so provenance traces are precise. |
| "Bidirectional links are redundant" | Forward and reverse links serve different queries. "What does D42 depend on?" vs "What depends on D42?" are both valid questions. |

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

## 11. Extending brain-link

Future enhancements:

- **Impact analysis**: "Which decisions would be affected if we change D42?"
- **Change impact**: "Which products would be affected by deprecating D89?"
- **Pattern suggestions**: "You're considering a saga pattern — here are similar decisions"
- **Cross-linking**: Link to code (commit SHAs, file paths, class definitions)
- **Timeline visualization**: Calendar view of decision evolution
- **Collaboration**: Decision committee tracking, approval chains
