---
name: forge-brain-layout
description: Brain directory structure, file naming conventions, and query patterns. Look up when writing to or reading from the brain.
type: reference
---
# Brain Layout

## Directory Tree

```
~/forge/brain/
├── products/
│   └── {product-slug}/
│       ├── prd/
│       │   └── {prd-id}/
│       │       ├── PRD.md                    # Locked after intake gate
│       │       ├── council/
│       │       │   ├── backend.md            # Backend surface perspective
│       │       │   ├── web.md                # Web frontend perspective
│       │       │   ├── app.md                # App frontend perspective
│       │       │   └── infra.md              # Infrastructure perspective
│       │       ├── contracts/
│       │       │   ├── api-rest.md           # REST API contract
│       │       │   ├── events-kafka.md       # Kafka event contract
│       │       │   ├── cache-redis.md        # Redis cache contract
│       │       │   ├── schema-db.md          # MySQL schema contract
│       │       │   └── search-es.md          # Elasticsearch contract
│       │       ├── shared-dev-spec.md        # Locked after spec-freeze
│       │       ├── tech-plans/
│       │       │   ├── {repo-name}.md        # One plan per repo
│       │       │   └── ...
│       │       ├── evals/
│       │       │   ├── scenarios.md          # Eval scenario definitions
│       │       │   ├── run-{timestamp}.md    # Individual eval run results
│       │       │   └── verdict.md            # Final eval-judge verdict
│       │       ├── dreaming/
│       │       │   ├── inline-{timestamp}.md # Inline conflict resolutions
│       │       │   └── ...
│       │       └── learnings/
│       │           └── {prd-id}-retrospective.md  # Post-PR dreamer retrospective
│       └── patterns/
│           ├── warm/                         # Seen 1 time
│           ├── active/                       # Seen 2+ times (same product)
│           └── candidates/                   # Seen 3+ times (cross-product) → skill candidate
├── decisions/
│   ├── D001.md                              # Locked decision record
│   ├── D002.md
│   └── ...
└── links/
    └── {source}-to-{target}.md              # Cross-reference links between decisions
```

## File Naming Conventions

| Location | Pattern | Example |
|---|---|---|
| Product slug | lowercase, hyphenated | `my-saas-app` |
| PRD ID | `PRD-YYYYMMDD-NNN` | `PRD-20260410-001` |
| Tech plan | `{repo-name}.md` | `backend-api.md` |
| Eval run | `run-{ISO-timestamp}.md` | `run-2026-04-10T14-30-00.md` |
| Decision | `D{NNN}.md` (zero-padded) | `D005.md` |
| Retrospective | `{prd-id}-retrospective.md` | `PRD-20260410-001-retrospective.md` |
| Inline dream | `inline-{ISO-timestamp}.md` | `inline-2026-04-10T15-00-00.md` |

## Immutability Rules

| File | Locked After | Can Be Changed By |
|---|---|---|
| `PRD.md` | Intake gate passes | Full re-intake only |
| `shared-dev-spec.md` | `spec-freeze` skill runs | Full council re-negotiation only |
| `D{NNN}.md` | Decision is recorded | Never — append a new decision instead |
| Council surface files | Council gate passes | Re-negotiation only |
| Contract files | Spec freeze | Re-negotiation only |

## Query Patterns

**Find all decisions for a product:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/
```

**Find all eval results:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/evals/
```

**Find patterns promoted to skill candidates:**
```
~/forge/brain/products/{product-slug}/patterns/candidates/
```

**Find cross-references between decisions:**
```
~/forge/brain/links/{source}-to-{target}.md
```

**Find retrospective learnings:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/learnings/
```

## Commit Conventions

All brain writes are committed with structured messages:

| Action | Commit message format |
|---|---|
| Lock PRD | `brain: lock PRD {prd-id}` |
| Lock spec | `brain: freeze shared-dev-spec for {prd-id}` |
| Record decision | `brain: decision D{NNN} — {one-line summary}` |
| Eval result | `brain: eval run for {prd-id} — {GREEN/YELLOW/RED}` |
| Retrospective | `brain: retrospective for {prd-id} (score: X/25)` |
| Link decisions | `brain: link {source} → {target}` |
