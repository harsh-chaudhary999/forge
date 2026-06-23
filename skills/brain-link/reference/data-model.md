# Link Data Model

## 6. Data Model

> **Storage of record is YAML frontmatter in the decision file** — not a separate
> edge store or JSON node database. The JSON below is a **conceptual** view; the
> authority for the on-disk shape is `brain-write` (frontmatter) and
> `forge-brain-layout` (paths/naming/status). Links live as `related_decisions:`
> and `superseded_by:` fields inside each `decisions/<category>/D<NNN>_<topic>.md`.

### Canonical on-disk shape (what you actually write)
```yaml
# in ~/forge/brain/decisions/architecture/D042_graduated-api-versioning.md
---
decision_id: D042
title: Graduated API versioning
status: active            # active | warm | cold | archived
tags: [api-versioning, sync, breaking-change]   # YAML array, no '#'
related_decisions:
  parent: [D040]
  children: []
  related: [D041]
superseded_by:            # set to D<new> when a `replaces` link is created
---
```

### Conceptual node/edge view (illustration only — NOT a stored file)
```
node  { id: "D042", type: "decision", status: "active", related_decisions: {...}, superseded_by: null }
edge  { from: "D042", to: "D089", type: "replaces", when: "2023-02-20", why: "Reduce URL clutter" }
```
An edge of type `replaces` is realized on disk as `superseded_by: D042` on the
older decision (D089); `related`/`conflicts`/`complements`/`variant` edges are
realized as entries under `related_decisions.related` on both decisions.

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
