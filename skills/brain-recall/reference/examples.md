# Query Examples, Workflows & Brain Recall in Action

> Deep reference for brain-recall. The operational contract lives in
> [`../SKILL.md`](../SKILL.md). Ranking references below point to
> [`ranking.md`](ranking.md).

## Query Examples & Workflows

### Query: "How did we solve API versioning?"

```bash
# 1. Grep for API versioning keywords
grep -r "API versioning\|API version\|api.*version" \
  ~/forge/brain/decisions/ --include="*.md" -l

# 2. Extract and rank results
# (use ranking algorithm from reference/ranking.md)

# 3. Format and output top 3-5 results with full context
```

**Expected recall:** API versioning decisions from across products, ranked by recency and resolution status.

---

### Query: "What patterns for eventual consistency?"

```bash
# 1. Tag-based search for #cache and #eventual-consistency
grep -r "#eventual-consistency" ~/forge/brain/patterns/ --include="*.md" -l | \
  xargs grep -l "#cache"

# 2. Alternative: keyword search in patterns
grep -r "eventual consistency" ~/forge/brain/patterns/ --include="*.md" -l

# 3. Rank by pattern status (#pattern tag) and recency
```

**Expected recall:** Caching and eventual consistency patterns from multiple products, suitable for architectural discussion.

---

### Query: "Database migration gotchas for big tables?"

```bash
# 1. Search learnings for migration + database
grep -r "migration\|migrate" ~/forge/brain/learnings/ --include="*.md" | \
  grep -i "database\|table\|schema"

# 2. Extract gotcha/warning tags (#gotcha)
grep -r "#gotcha" ~/forge/brain/learnings/ --include="*.md" | \
  grep -i "migration\|database"

# 3. Rank by recency (since gotchas improve over time)
```

**Expected recall:** Real migration failures, table size thresholds, tools that worked/failed, rollback strategies.

---

### Query: "Show me all #database decisions for web-dashboard"

```bash
# 1. Filter by project
grep -l "project: web-dashboard" ~/forge/brain/decisions/*.md

# 2. Filter by tag
... | xargs grep -l "#database"

# 3. Sort by date (most recent first)
... | xargs ls -1t
```

**Expected recall:** All database-related decisions (schema, migration, caching, etc.) for web-dashboard project.

---

## Example Product/Project Queries

- "Show API decisions for shopapp"
  ```bash
  grep -l "product: shopapp" ~/forge/brain/decisions/*.md | xargs grep -l "#api"
  ```

- "Web-dashboard learnings"
  ```bash
  grep -l "project: web-dashboard" ~/forge/brain/learnings/*.md
  ```

- "Database migrations in production"
  ```bash
  grep -l "product: production" ~/forge/brain/decisions/*.md | xargs grep -l "migration"
  ```

## Examples of Brain Recall in Action

### Example 1: New engineer starting on caching

**Query:** "Show me all #cache patterns and #eventual-consistency decisions"

**Workflow:**
1. Run brain-recall with tags `#cache` and `#eventual-consistency`
2. Returns patterns from shopapp, production, and mobile projects
3. Engineer learns: TTL strategy, stampede prevention, consistency model
4. Engineer links to most relevant pattern for their current task

---

### Example 2: Migrating a large table

**Query:** "Database migration gotchas for big tables?"

**Workflow:**
1. Run brain-recall searching learnings for "migration" + "big table"
2. Filter by product (if applicable)
3. Returns: past migration failures, downtime incidents, tool comparisons
4. Engineer extracts actionable lessons (e.g., "use gh-ost, not ALTER TABLE directly")

---

### Example 3: Designing API versioning for new product

**Query:** "How did we handle API versioning last time?"

**Workflow:**
1. Run brain-recall searching decisions for "API versioning"
2. Rank by #resolved status and #api tag
3. Returns shopapp decision (URL path versioning) and mobile decision (header versioning)
4. Design council reviews both, discusses trade-offs
5. Selects path versioning for consistency with shopapp
6. Links to shopapp decision as rationale

---

## Example Output (filled-in result template)

This is a fully populated example of the output template defined in
[`../SKILL.md`](../SKILL.md) Section 5:

```markdown
## Result: API Versioning Strategy for shopapp

**File:** `brain/decisions/2025-11-15-api-versioning-shopapp.md`

**Date:** 2025-11-15  
**Product:** shopapp  
**Project:** backend-api  
**Status:** resolved  
**Tags:** #api #versioning #backward-compat #resolved

**Context:**
As shopapp scaled to multiple clients, we faced breaking API changes. Different clients deploy on different schedules, so we needed a versioning strategy that supported multiple API versions in parallel.

**Decision/Pattern:**
Implemented URL path versioning (`/api/v1/`, `/api/v2/`) with header-based client identification. New features go to v2; v1 remains stable for 6 months before deprecation. Clients explicitly declare which API version they support.

**Outcome/Rationale:**
- No client breakage during major feature releases
- Clear deprecation timeline (180 days notice)
- Minimal code duplication via shared service layer
- Monitoring shows 85% adoption of v2 within 3 months

**Related Patterns:**
- `brain/patterns/backward-compatibility-layers.md` (production product)
- `brain/learnings/api-deprecation-gotchas.md` (mobile project)

**Watch Out For:**
- Legacy clients on v1 may not implement new retry logic → monitor error rates
- Documentation drift between v1 and v2 → audit quarterly
```
