# Navigation Patterns

> Moved verbatim from `SKILL.md` for progressive disclosure (forge-skill-anatomy v2.1.0). The exhaustive navigation + query-pattern catalog. The quick-reference card and common-queries table remain inline in `../SKILL.md`.

### Navigate by Product Area

To find all decisions and context for a specific product:

```
brain/products/{product-slug}/prd/{prd-id}/
├── PRD.md                          # Problem and acceptance criteria
├── council/                         # How each surface team sees it
├── contracts/                       # Service boundaries
├── shared-dev-spec.md              # Implementation specification
├── tech-plans/                      # Per-repo implementation
├── evals/                           # Test results
└── learnings/                       # Retrospective analysis
```

**Example:** To understand all decisions for auth-service PRD-20260410-001:
```bash
ls -la brain/products/auth-service/prd/PRD-20260410-001/
```

### Navigate by Decision Category

Architecture decisions (foundational system design):
```
brain/decisions/architecture/D001.md through D099.md
```

Product decisions (feature and UX choices):
```
brain/decisions/product/D100.md through D199.md
```

Engineering decisions (implementation approach):
```
brain/decisions/engineering/D200.md through D299.md
```

Operations decisions (deployment, infrastructure, observability):
```
brain/decisions/ops/D300.md and above
```

### Navigate by Decision Status

**LOCKED decisions** (auditable, immutable):
```
brain/decisions/{category}/D{NNN}.md
```

**Drafts awaiting review** (not yet decided):
```
brain/drafts/pending/{topic}.md
```

**Drafts ready to lock** (approved by council):
```
brain/drafts/resolved/{topic}.md
```

**Archived decisions** (superseded or deprecated):
```
brain/archived/D{NNN}_{topic}.md
```

### Navigate by Keyword/Relationship

To find related decisions, check the `relates_to` field in decision files:

```markdown
---
relates_to: [D001, D050, D085]
---
```

Use brain-recall skill to search by keyword:
```
brain-recall: "session timeout"
```

Use brain-why skill to trace provenance of a decision:
```
brain-why: D102
```

### Query Patterns (Specific Examples)

**Find all decisions for a product:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/
```

**Find all eval results for a PRD:**
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

**Find all architecture decisions:**
```
~/forge/brain/decisions/architecture/
```

**Find the latest decisions:**
```
ls -lt ~/forge/brain/decisions/**/*.md | head -20
```

**Find all decisions about authentication:**
```
grep -r "authentication" ~/forge/brain/decisions/ --include="*.md"
```

**Find decisions archived in last 30 days:**
```
find ~/forge/brain/archived/ -mtime -30 -name "*.md"
```
