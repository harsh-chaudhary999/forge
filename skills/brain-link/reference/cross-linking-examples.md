# brain-link — Cross-Product & Cross-Time Linking Examples

> Extracted illustrative blocks from `SKILL.md` §3 (Cross-Product Linking) and
> §4 (Cross-Time Linking). The operational guidance (product inventory, linking
> strategy bullets, change-rationale fields, query examples) stays inline in
> SKILL.md; these are the worked illustrations.

## Cross-Product Linking — Linking Strategy

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

## Cross-Time Linking — Evolution Chains

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
