# brain-link — Decision Trees

> Extracted from `SKILL.md` §12 (Decision Trees). Two trees: choosing the link
> type, and choosing directionality. The inline SKILL.md keeps a one-line
> selection summary; these are the full walkthroughs.

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
