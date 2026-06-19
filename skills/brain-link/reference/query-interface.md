# brain-link — Query Interface

> Extracted from `SKILL.md` §5 (Query Interface). Standard query syntax for
> decision graph traversal. The inline SKILL.md keeps the common-case queries;
> this file is the full catalog (basic + advanced).

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
