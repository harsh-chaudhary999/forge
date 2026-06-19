# brain-link — Example Graph

> Extracted from `SKILL.md` §7 (Example Graph). A complete decision graph
> showing all relationship types (`related`, `replaces`, `conflicts`,
> `complements`, `variant`) and tag/product rollups.

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
