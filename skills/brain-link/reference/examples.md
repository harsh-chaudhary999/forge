# brain-link — Usage Examples

> Extracted from `SKILL.md` §8 (Usage Examples). Four detailed example queries
> showing the brain-link query interface and the shape of results.

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
