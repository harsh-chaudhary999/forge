---
name: brain-recall
description: "WHEN: You are about to make a decision and need to check if prior art or past learnings exist. Recall decisions, patterns, and gotchas from the brain before proceeding."
type: rigid
requires: [brain-read]
---

# Brain Recall Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I already know what happened last time" | Past experience is filtered by recency bias. The brain stores evidence, not impressions. Search it. |
| "There's no prior art for this decision" | Cross-product patterns exist more often than you think. Search across products, not just the current one. |
| "The search didn't return results, so there's nothing" | Bad queries miss good results. Try synonyms, broader tags, and product-agnostic terms before concluding. |
| "I'll just use the most recent result" | Recency ≠ relevance. A pattern from 6 months ago on a similar product may be more applicable than yesterday's decision on a different domain. |
| "Recall is optional — I can decide without it" | Every decision that ignores prior learnings risks repeating gotchas. Recall is the cheapest way to avoid known failure modes. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
BEFORE ACTING ON ANY DECISION, SEARCH THE BRAIN FIRST. MEMORY IS NOT A SUBSTITUTE FOR EVIDENCE — THE BRAIN IS THE ONLY AUTHORITATIVE RECORD.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Search returns zero results and agent concludes "no prior art"** — Zero results means the query was too narrow, not that no prior art exists. STOP. Broaden query with synonyms, adjacent tags, and cross-product search before concluding.
- **Agent recalls from memory instead of searching brain files** — Memory is subjective and lossy. STOP. Always search the actual brain directory; never rely on recalled summaries of decisions.
- **Recall is skipped because "this is a new problem"** — Cross-domain patterns appear in unexpected places. STOP. Search even when the problem feels novel.
- **Only the most recent result is used without reviewing all matches** — Recency bias misses more applicable older patterns. STOP. Review all matches and select based on relevance, not date.
- **Recall query uses only the current product name** — Patterns recorded under a different product name will be missed. STOP. Search across all products with domain-level tags.
- **Brain path is wrong or outdated** — Searching the wrong brain path produces incomplete results. STOP. Verify brain path from forge-product.md before searching.

Hybrid retrieval from persistent brain. Searches past decisions, patterns, learnings using grep + tags + product/project filtering.

## Overview

The brain-recall skill enables agents and developers to:
- Search historical decisions and patterns stored in the brain
- Filter results by product, project, tags, and date
- Rank results by relevance (recency, resolution status, same project/product)
- Surface similar patterns from other products for cross-project learning
- Link back to original decision documents for context

## 1. Grep-Based Search

Search the brain knowledge base for keywords across decision records, patterns, and learnings.

**Locations:**
- `/home/lordvoldemort/Videos/forge/brain/decisions/` - decision records
- `/home/lordvoldemort/Videos/forge/brain/patterns/` - architectural patterns
- `/home/lordvoldemort/Videos/forge/brain/learnings/` - lessons learned
- `/home/lordvoldemort/Videos/forge/brain/contracts/` - API/schema/event contracts

**Search command template:**
```bash
grep -r "KEYWORD" ~/Videos/forge/brain/{decisions,patterns,learnings,contracts}/ \
  --include="*.md" -l | head -20
```

**Examples:**
- Search for API versioning decisions:
  ```bash
  grep -r "API versioning" ~/Videos/forge/brain/decisions/ --include="*.md" -l
  ```
- Search for cache patterns:
  ```bash
  grep -r "cache" ~/Videos/forge/brain/patterns/ --include="*.md" -l
  ```
- Search across all brain documents:
  ```bash
  grep -r "eventual consistency" ~/Videos/forge/brain/ --include="*.md" -A 2
  ```

**Ranking within grep results:**
- Files with most recent dates in filename/frontmatter rank higher
- Files with "resolved" status rank higher than "open"
- Files matching both search keyword and product/project rank higher

## 2. Tag-Based Filtering

Filter decisions, patterns, and learnings by structured tags. Tags enable cross-cutting queries across multiple decision types.

**Available Tags:**
- **Domain tags:** `#api`, `#database`, `#cache`, `#frontend`, `#mobile`, `#events`, `#search`, `#infra`
- **Status tags:** `#resolved`, `#open`, `#deprecated`, `#pattern`, `#gotcha`, `#urgent`
- **Category tags:** `#scaling`, `#migration`, `#versioning`, `#backward-compat`, `#performance`, `#observability`, `#security`

**Tag filtering strategies:**

### Single tag query
```bash
# Find all resolved API decisions
grep -r "#api" ~/Videos/forge/brain/decisions/ --include="*.md" | grep "#resolved"
```

### Multi-tag AND query
```bash
# Find database decisions that are both patterns AND resolved
grep -r "#database" ~/Videos/forge/brain/ --include="*.md" | grep "#pattern" | grep "#resolved"
```

### Tag extraction from frontmatter
```bash
# Extract tags from YAML frontmatter
grep -A 20 "^---" ~/Videos/forge/brain/decisions/*.md | grep "tags:" -A 10
```

**Example tag-based queries:**

- "Show me all #database decisions"
  ```bash
  grep -r "#database" ~/Videos/forge/brain/decisions/ --include="*.md" -l
  ```

- "What patterns exist for #cache AND #eventual-consistency?"
  ```bash
  grep -r "#cache" ~/Videos/forge/brain/patterns/ --include="*.md" | grep "#eventual-consistency"
  ```

- "Show #urgent #unresolved issues"
  ```bash
  grep -r "#urgent" ~/Videos/forge/brain/decisions/ --include="*.md" | grep -v "#resolved"
  ```

## 3. Product/Project Filtering

Filter brain records by specific products (shopapp, production, etc.) and projects (backend-api, web-dashboard, etc.).

**Frontmatter structure:**
```yaml
---
title: Decision title
date: 2025-11-15
product: shopapp
project: backend-api
tags: [#api, #versioning, #resolved]
---
```

**Filtering by product:**
```bash
# All decisions for shopapp product
grep -l "product: shopapp" ~/Videos/forge/brain/decisions/*.md

# All patterns for production
grep -l "product: production" ~/Videos/forge/brain/patterns/*.md
```

**Filtering by project:**
```bash
# All decisions for backend-api project
grep -l "project: backend-api" ~/Videos/forge/brain/decisions/*.md
```

**Combined product + keyword search:**
```bash
# API decisions for shopapp product
grep -l "product: shopapp" ~/Videos/forge/brain/decisions/*.md | xargs grep -l "API versioning"
```

**Example product/project queries:**

- "Show API decisions for shopapp"
  ```bash
  grep -l "product: shopapp" ~/Videos/forge/brain/decisions/*.md | xargs grep -l "#api"
  ```

- "Web-dashboard learnings"
  ```bash
  grep -l "project: web-dashboard" ~/Videos/forge/brain/learnings/*.md
  ```

- "Database migrations in production"
  ```bash
  grep -l "product: production" ~/Videos/forge/brain/decisions/*.md | xargs grep -l "migration"
  ```

## 4. Relevance Ranking

Results are ranked by multiple factors to surface the most applicable decisions:

**Ranking criteria (descending priority):**

1. **Same product/project match** (weight: 3x)
   - If query includes product/project filter, matching results rank 3x higher

2. **Resolution status** (weight: 2x)
   - Decisions tagged #resolved rank 2x higher than #open
   - Patterns tagged #pattern rank higher than ad-hoc decisions

3. **Recency** (weight: 1.5x)
   - Decisions from last 90 days rank 1.5x higher
   - Within same recency tier, more recent ranks higher

4. **Tag match count**
   - Results matching more query tags rank higher
   - Exact tag match ranks higher than partial keyword match

5. **Document type priority**
   - Patterns > Decisions > Learnings (for architectural queries)
   - Learnings > Decisions > Patterns (for gotchas/warnings)

**Ranking implementation:**
```bash
#!/bin/bash
# Pseudo-algorithm for ranking results

results=()

# 1. Find matching files
for file in $(grep -r "$KEYWORD" ~/Videos/forge/brain --include="*.md" -l); do
  score=0
  
  # Factor 1: Product/project match
  if grep -q "product: $PRODUCT" "$file"; then
    score=$((score + 30))
  fi
  
  # Factor 2: Resolution status
  if grep -q "#resolved" "$file"; then
    score=$((score + 20))
  elif grep -q "#pattern" "$file"; then
    score=$((score + 15))
  fi
  
  # Factor 3: Recency (extract date from frontmatter)
  date=$(grep "^date:" "$file" | cut -d: -f2 | xargs)
  days_old=$(( ($(date +%s) - $(date -d "$date" +%s)) / 86400 ))
  if [ "$days_old" -lt 90 ]; then
    score=$((score + 15))
  fi
  
  # Factor 4: Tag match count
  tag_matches=$(echo "$TAGS" | tr ' ' '\n' | while read tag; do
    grep -c "^tags:.*$tag" "$file" 2>/dev/null || echo 0
  done | awk '{s+=$1} END {print s}')
  score=$((score + tag_matches * 5))
  
  results+=("$score:$file")
done

# 2. Sort by score (descending)
printf '%s\n' "${results[@]}" | sort -rn | cut -d: -f2-
```

## 5. Output Format

Recalled decisions are formatted to provide context and traceability:

```markdown
## Result: [Decision Title]

**File:** `brain/decisions/YYYY-MM-DD-decision-name.md`

**Date:** YYYY-MM-DD  
**Product:** [product-name]  
**Project:** [project-name]  
**Status:** [resolved/open/deprecated]  
**Tags:** #tag1 #tag2 #tag3

**Context:**
[2-3 sentence summary of the problem/question that led to this decision]

**Decision/Pattern:**
[Key decision or pattern that was decided/discovered]

**Outcome/Rationale:**
[Why this decision worked or what we learned]

**Related Patterns:**
- [Link to related pattern in other product] (if applicable)
- [Link to related learnings]

**Conflicts Resolved:**
- [If decision resolved a conflict, list it here]

**Watch Out For:**
[Any gotchas or edge cases discovered]
```

**Example output:**

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

## 6. Query Examples & Workflows

### Query: "How did we solve API versioning?"

```bash
# 1. Grep for API versioning keywords
grep -r "API versioning\|API version\|api.*version" \
  ~/Videos/forge/brain/decisions/ --include="*.md" -l

# 2. Extract and rank results
# (use ranking algorithm from Section 4)

# 3. Format and output top 3-5 results with full context
```

**Expected recall:** API versioning decisions from across products, ranked by recency and resolution status.

---

### Query: "What patterns for eventual consistency?"

```bash
# 1. Tag-based search for #cache and #eventual-consistency
grep -r "#eventual-consistency" ~/Videos/forge/brain/patterns/ --include="*.md" -l | \
  xargs grep -l "#cache"

# 2. Alternative: keyword search in patterns
grep -r "eventual consistency" ~/Videos/forge/brain/patterns/ --include="*.md" -l

# 3. Rank by pattern status (#pattern tag) and recency
```

**Expected recall:** Caching and eventual consistency patterns from multiple products, suitable for architectural discussion.

---

### Query: "Database migration gotchas for big tables?"

```bash
# 1. Search learnings for migration + database
grep -r "migration\|migrate" ~/Videos/forge/brain/learnings/ --include="*.md" | \
  grep -i "database\|table\|schema"

# 2. Extract gotcha/warning tags (#gotcha)
grep -r "#gotcha" ~/Videos/forge/brain/learnings/ --include="*.md" | \
  grep -i "migration\|database"

# 3. Rank by recency (since gotchas improve over time)
```

**Expected recall:** Real migration failures, table size thresholds, tools that worked/failed, rollback strategies.

---

### Query: "Show me all #database decisions for web-dashboard"

```bash
# 1. Filter by project
grep -l "project: web-dashboard" ~/Videos/forge/brain/decisions/*.md

# 2. Filter by tag
... | xargs grep -l "#database"

# 3. Sort by date (most recent first)
... | xargs ls -1t
```

**Expected recall:** All database-related decisions (schema, migration, caching, etc.) for web-dashboard project.

---

## 7. Implementation Notes

### Integration with brain-read skill
- brain-recall **builds on** brain-read (requires: [brain-read])
- brain-read handles artifact retrieval and basic queries
- brain-recall adds search, filtering, ranking, and cross-product pattern matching

### Brain directory structure (assumed)
```
~/Videos/forge/brain/
├── decisions/              # Decision records (YYYY-MM-DD-*.md)
├── patterns/               # Architectural patterns
├── learnings/              # Lessons learned & gotchas
├── contracts/              # API/schema/event contracts
└── README.md               # Brain metadata
```

### Performance notes
- Grep searches are O(n) across all files; consider indexing for >1000 files
- Tag-based queries can be optimized with a tag index file
- Relevance ranking should be computed at query time (not pre-cached)

### Error handling
- If no results found: suggest broader search or list available tags
- If multiple products match: show results grouped by product
- If query is ambiguous: ask for clarification (e.g., "Decision or Pattern?")

### Caching strategy
- Do NOT cache search results (brain updates frequently)
- Cache only brain metadata (directory structure, available products/projects)
- Invalidate cache on each brain-write operation

## 8. Integration with Forge Skills

### When to use brain-recall
- **During design phase:** "What patterns did we use for versioning?"
- **Before implementation:** "What gotchas exist for this pattern?"
- **During code review:** "How did we solve this in shopapp?"
- **Post-implementation:** "What did we learn from this decision?"

### Related skills
- **brain-read:** Basic artifact retrieval (use when you know the specific file)
- **brain-write:** Record new decisions (use after resolving a conflict)
- **contract-*:** Negotiate contracts (use before implementation)

## 9. Examples of Brain Recall in Action

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

## 10. Success Criteria

A brain-recall query is successful when:

- [x] **Relevance:** Top result directly answers the question
- [x] **Context:** Result includes decision date, product, project, status
- [x] **Traceability:** Link to original brain file is provided
- [x] **Completeness:** Related patterns from other products are surfaced
- [x] **Ranking:** Results are ranked by relevance (not random order)
- [x] **Speed:** Query completes in <2 seconds for <1000 brain files

---

## 11. Troubleshooting

**Q: No results found for my query**
- A: Try broader keywords or check available tags with `grep -r "^tags:" ~/Videos/forge/brain/`
- A: Search in a specific section (decisions/ vs patterns/ vs learnings/)
- A: Check if the brain file exists for your product/project

**Q: Too many results returned**
- A: Add product/project filter to narrow scope
- A: Add tag filter (e.g., `#resolved` to exclude open issues)
- A: Add date filter (e.g., "last 6 months")

**Q: Result seems outdated**
- A: Check the decision date and #resolved status
- A: Look for superseding decisions (often linked in "Related" section)
- A: Ask brain-read for the latest version of that file

**Q: Can't find the exact pattern I'm looking for**
- A: Try searching with different keywords (synonyms)
- A: Check brain/contracts/ if you're looking for API/schema patterns
- A: Create a new pattern in brain-write if this is a novel solution

---

## 12. Retrieval Performance Edge Cases

### Edge Case 1: Search Returns 100+ Results, User Needs Ranking/Filtering

**What happens?**
- User searches for a common term (e.g., "cache", "database", "API") and gets 50-200 matching files
- Top result may not be relevant to user's product/project or current problem
- User must manually scan results to find applicable decision
- Time-to-insight increases from seconds to minutes

**Why?**
- Brain is large (1000+ decisions across multiple products)
- Keyword is general and matches many unrelated contexts
- No automatic filtering applied (all products, all statuses shown)
- Ranking by recency alone doesn't account for product/project specificity

**How to detect it?**
```bash
# Count results for a broad keyword
COUNT=$(grep -r "cache" ~/Videos/forge/brain/decisions/ --include="*.md" -l | wc -l)
if [ "$COUNT" -gt 100 ]; then
  echo "EDGE CASE: $COUNT results found. Apply filters."
fi
```

**How to mitigate?**
1. **Mandatory product/project filter:** If results >50, require `--product shopapp` or `--project backend-api` flag
2. **Auto-filter to active decisions:** Exclude #archived and #deprecated unless explicitly requested
3. **Show ranked top-5 only:** Display top 5 results with scores; user can request "show next 5"
4. **Suggest narrowing filters:** "50 results for 'cache'. Suggest adding: --product shopapp OR --tag #redis"
5. **Pagination strategy:**
   - Return top 5 results with scores
   - User can request: "show results 6-10", "show all #backend results", "show shopapp #cache"

**When to escalate?**
- Escalate to `brain-why` if user needs to understand why a specific decision was made (not which decision)
- Escalate to `brain-link` if user needs to map semantic relationships between decisions (all cache decisions, including eventual consistency patterns)
- Escalate to `brain-read` if user already knows the file path and just needs to read it

---

### Edge Case 2: Brain Has Grown Large (10k+ Decisions), Grep Becomes Slow

**What happens?**
- As brain grows beyond 5000 decisions, grep searches slow from <100ms to >2 seconds
- Combining multiple grep pipes (keyword + tag + product) can take 5+ seconds
- User experiences poor responsiveness when searching iteratively
- Ranking algorithm with multiple passes becomes bottleneck

**Why?**
- `grep -r` is O(n) across all files in brain/
- Each pipe (keyword → tag → product) is a full scan of results
- Filesystem I/O dominates for large file counts
- Frontmatter parsing (extracting date, tags) requires reading entire files

**How to detect it?**
```bash
# Measure grep performance
time_start=$(date +%s%N)
grep -r "cache" ~/Videos/forge/brain/ --include="*.md" -l > /dev/null
time_end=$(date +%s%N)
duration_ms=$(( (time_end - time_start) / 1000000 ))

if [ "$duration_ms" -gt 1000 ]; then
  echo "EDGE CASE: Grep took ${duration_ms}ms. Consider indexing."
fi

# Check brain file count
DECISION_COUNT=$(find ~/Videos/forge/brain/decisions -type f | wc -l)
if [ "$DECISION_COUNT" -gt 5000 ]; then
  echo "WARNING: Brain has $DECISION_COUNT decisions. Indexing recommended."
fi
```

**How to mitigate?**
1. **Build a brain index file** (update weekly):
   ```bash
   # brain/index.json: {filename, title, product, project, tags, date, type}
   # Query against JSON instead of grepping all files
   jq '.[] | select(.product == "shopapp" and .tags[] == "#cache")' brain/index.json
   ```
2. **Use filename conventions:** Encode metadata in filename
   - `YYYY-MM-DD_PRODUCT_PROJECT_TYPE_TITLE.md`
   - Query filenames before content grep
3. **Lazy load file contents:** For ranking, read only frontmatter (first 20 lines), not full file
4. **Parallel search:** Use `grep -r` with `xargs -P 4` for multi-core systems
5. **Archive old decisions:** Move decisions >2 years old to `brain/archive/` to reduce active brain size

**When to escalate?**
- Escalate to `brain-link` if you need full-text semantic search (requires pre-computed embeddings)
- Escalate to `brain-why` if you need provenance/lineage (may require different indexing strategy)
- Consider moving to dedicated search backend (Elasticsearch) for brains >10k decisions

---

### Edge Case 3: Stale Results (Decision Was Archived 6 Months Ago, Search Still Returns It)

**What happens?**
- User searches for "API versioning" and gets back a decision marked #archived from 6 months ago
- Decision contradicts newer approach (now using gRPC instead of REST)
- User implements based on outdated decision, wastes engineering effort
- Discovery happens in code review or testing phase

**Why?**
- Archived decisions are still in grep search results
- No automatic filtering of #archived or #deprecated status
- No "superseded by" or "see instead" links in old decision
- Recency ranking doesn't exclude old decisions with recent timestamps

**How to detect it?**
```bash
# Find decisions with #archived or #deprecated
grep -r "#archived\|#deprecated" ~/Videos/forge/brain/decisions/ --include="*.md" -l

# Check if recent search includes old decisions
grep -r "API version" ~/Videos/forge/brain/decisions/ --include="*.md" | \
  grep -E "2024|2025-01|2025-02"  # Find old dates
```

**How to mitigate?**
1. **Exclude archived by default:**
   ```bash
   # Standard search (exclude archived)
   grep -r "API version" ~/Videos/forge/brain/decisions/ --include="*.md" | \
     grep -v "#archived" | grep -v "#deprecated"
   ```
2. **Show replacement decision:** If result is #archived, include link to newer decision
   - Frontmatter should include: `superseded_by: YYYY-MM-DD-new-decision.md`
   - Display: "⚠ This decision is archived. See [newer approach](path) instead"
3. **Archive with date-based filtering:**
   - Archived decisions older than 1 year are not shown by default
   - User must explicitly request `--include-archived` to see them
4. **Regular brain audits:** Monthly task to find orphaned decisions (no superseding decision) and update them

**When to escalate?**
- Escalate to `brain-write` if you're recording a new decision that supersedes an old one
- Escalate to `brain-why` to understand why the old decision was archived
- Escalate to `brain-link` to create semantic relationship between old and new approach

---

### Edge Case 4: Cross-Product Patterns Need Deduplication (Same Decision Exists in 2 Products)

**What happens?**
- Query "How do we handle API versioning?" returns 3 results:
  - `shopapp/api-versioning-v1.md` (path-based versioning, 2025-01-15)
  - `production/api-versioning-strategy.md` (header-based versioning, 2025-02-20)
  - `mobile/api-versioning.md` (path-based versioning, 2025-01-10, copy of shopapp)
- User now has 3 results for same pattern, unsure which to follow
- Maintenance burden: if shopapp updates approach, need to update mobile copy too

**Why?**
- Patterns are documented per-product for context
- Knowledge duplication is easier than cross-product coordination
- No deduplication logic in brain-recall
- No "canonical" vs "copy" metadata

**How to detect it?**
```bash
# Find similar decisions across products
# Compare title + first 3 sentences to detect likely duplicates
for file in ~/Videos/forge/brain/decisions/*.md; do
  title=$(grep "^title:" "$file" | cut -d: -f2-)
  product=$(grep "^product:" "$file" | cut -d: -f2-)
  echo "$title | $product"
done | sort | uniq -d | grep -v '^$'
```

**How to mitigate?**
1. **Create canonical decision:** Instead of copying, reference original
   - Canonical: `brain/decisions/2025-01-15-api-versioning-canonical.md` (product: shared)
   - Product-specific variant: Include frontmatter link `based_on: 2025-01-15-api-versioning-canonical.md`
   - Query shows canonical first, then product-specific variants
2. **Deduplication in search results:**
   - Hash decision content (title + key sentences)
   - If hash collision, show one result + "Also found in: [product2, product3]"
3. **Cross-product pattern catalog:** Separate brain section
   - `brain/patterns-shared/` for patterns used by 2+ products
   - Query searches shared patterns first, then product-specific

**When to escalate?**
- Escalate to `brain-link` to create relationships between canonical and product-specific versions
- Escalate to `brain-write` if creating a new canonical pattern
- Escalate to `brain-why` to understand why pattern was duplicated

---

### Edge Case 5: Tag Explosion (100+ Tags, User Doesn't Know Which to Use)

**What happens?**
- Brain accumulates tags: #api, #database, #cache, #redis, #memcached, #eventual-consistency, #strong-consistency, #versioning, #backward-compat, #migration, #schema-evolution...
- New user searches and doesn't know: Should I search #cache or #redis? #eventual-consistency or #strong-consistency?
- Tag-based query returns inconsistent results (some decisions use #eventual-consistency, others say "eventually consistent" in text)
- Maintainability issue: multiple tags for same concept

**Why?**
- Tags grow organically as decisions are written
- No central tag registry or governance
- Domain/specific tag duplication (#cache, #caching, #caches)
- Tag inconsistency: #backward-compat vs #backward-compatibility

**How to detect it?**
```bash
# List all unique tags in brain
grep -r "^tags:" ~/Videos/forge/brain/ --include="*.md" | \
  sed 's/.*tags: //g' | tr ',' '\n' | tr -d '[]" ' | sort | uniq | wc -l

# If > 80, tag explosion likely
# Show tag frequency to identify unused tags
grep -r "^tags:" ~/Videos/forge/brain/ --include="*.md" | \
  sed 's/.*tags: //g' | tr ',' '\n' | tr -d '[]" ' | sort | uniq -c | sort -n | tail -20
```

**How to mitigate?**
1. **Establish canonical tag registry:** `brain/TAG-GUIDE.md`
   - Lists all approved tags with definitions
   - Includes aliases: `#cache → use this`, `#caching, #caches → deprecated, use #cache`
   - Maps domain tags to status tags: `#cache (domain) + #pattern (status) + #redis (implementation)`
2. **Normalize tags in old decisions:** Automated script to replace non-canonical tags
3. **Tag query suggestions:** When user enters tag, suggest similar tags
   - User searches `#cach`: suggest `#cache, #redis, #memcached, #eventual-consistency`
4. **Tag usage guide in output:**
   - When showing results, highlight which tags were query filters
   - Suggest related tags: "Results tagged #redis. Related: #cache, #distributed-systems"

**When to escalate?**
- Escalate to `brain-write` to document tag governance policy
- Escalate to `brain-link` to create semantic relationships between tag concepts

---

### Edge Case 6: Semantic Drift (Same Concept, Different Terminology)

**What happens?**
- User searches "How do we handle distributed transactions?"
- Gets no results (decisions use term "saga pattern", "orchestration", "eventual consistency workflow")
- User believes brain has no guidance, duplicates effort
- Alternative: User searches "saga" and misses "distributed transaction" nomenclature

**Why?**
- Different products/teams use different terminology for same pattern
- Engineers from different backgrounds (academic vs industry) use different vocabulary
- Terminology evolves (yesterday's "saga" is today's "distributed workflow")
- Grep is literal text matching, doesn't understand semantic equivalence

**How to detect it?**
```bash
# Find decisions with similar content but different keywords
# Calculate content hash of first 3 sentences
for file in ~/Videos/forge/brain/decisions/*.md; do
  tail -n +5 "$file" | head -3 | sha256sum | awk '{print $1}' > "${file}.hash"
done
# Group by hash to find similar content with different titles

# Or manually: check for decision titles with different terminology
grep "^title:" ~/Videos/forge/brain/decisions/*.md | grep -i "saga\|transaction\|orchestration\|workflow"
```

**How to mitigate?**
1. **Add "Also called" section to decisions:**
   ```markdown
   **Also called:** distributed transactions, saga pattern, orchestration, workflow choreography
   ```
2. **Create taxonomy file:** `brain/TERMINOLOGY.md`
   - Maps concepts to alternative names
   - Example: "Saga Pattern" → see also "distributed transactions", "orchestration", "long-running transactions"
3. **Semantic search layer (future):** When search count is low and grep alone fails, use term expansion
   - Look up query term in TERMINOLOGY.md
   - Re-search with all aliases: `grep -r "saga|orchestration|distributed transaction|workflow"`
4. **Add keywords section to frontmatter:**
   ```yaml
   keywords: [saga, orchestration, distributed-transaction, workflow]
   ```

**When to escalate?**
- Escalate to `brain-link` to create semantic relationships between different terminology
- Escalate to `brain-why` to understand how terminology evolved over time

---

### Edge Case 7: Time-Based Recency Weighting (Recent Decisions Override Old Patterns)

**What happens?**
- User searches "How do we do caching?"
- Gets back newest decision (2 weeks ago) which is team experiment with new cache strategy
- Misses authoritative pattern decision (2 years ago) that established company standard
- Engineer implements experimental approach in production

**Why?**
- Recency ranking assumes newer = better
- Doesn't distinguish between "updated decision" and "experimental/draft decision"
- No status-based weighting (draft/experimental vs production-proven)
- Time decay can obscure timeless patterns

**How to detect it?**
```bash
# Find mismatches: recent decisions without #resolved tag
grep -r "^date: 2025-04" ~/Videos/forge/brain/decisions/ --include="*.md" | \
  while read file; do
    if ! grep -q "#resolved\|#pattern" "$file"; then
      echo "EDGE CASE: Recent draft decision: $file"
    fi
  done
```

**How to mitigate?**
1. **Separate status tiers in ranking:**
   - #pattern (proven): score ×5
   - #resolved (confirmed decision): score ×3
   - #open (in discussion): score ×1
   - #experimental (try this, share results): score ×0.5
2. **Apply time decay selectively:**
   - Only decay #open decisions (half-life: 30 days)
   - Keep #pattern and #resolved decisions at full weight
3. **Show confidence in ranking:**
   ```
   Result 1: API Versioning Strategy (2025-02-15, #pattern, 95% confidence)
   Result 2: New Header Versioning Experiment (2025-04-01, #experimental, 40% confidence)
   ```
4. **Suggest deeper search:** "Found 1 #pattern and 3 #experimental results. Show only patterns? (Y/n)"

**When to escalate?**
- Escalate to `brain-why` to trace evolution of approach and understand why older pattern is still valid
- Escalate to `brain-link` to create explicit "supersedes" relationship if newer decision is confirmed

---

## 13. Ranking & Filtering Strategies

### Ranking by Relevance

**Scoring algorithm** (multi-factor ranking):

```bash
#!/bin/bash
# Ranking pseudocode

KEYWORD="$1"
PRODUCT="${2:-}"  # Optional product filter

declare -A scores

# Find all matching files
for file in $(grep -r "$KEYWORD" ~/Videos/forge/brain --include="*.md" -l); do
  score=0
  
  # Factor 1: Status multiplier (heaviest weight)
  if grep -q "#pattern" "$file"; then
    score=$((score + 50))  # Proven pattern
  elif grep -q "#resolved" "$file"; then
    score=$((score + 30))  # Confirmed decision
  elif grep -q "#open" "$file"; then
    score=$((score + 10))  # In discussion
  elif grep -q "#experimental" "$file"; then
    score=$((score + 5))   # Try this
  fi
  
  # Factor 2: Product/project match (3x multiplier)
  if [ -n "$PRODUCT" ]; then
    if grep -q "product: $PRODUCT" "$file"; then
      score=$((score + 45))
    fi
  fi
  
  # Factor 3: Recency (weighted by status)
  date=$(grep "^date:" "$file" | cut -d: -f2 | xargs)
  if [ -n "$date" ]; then
    days_old=$(( ($(date +%s) - $(date -d "$date" +%s 2>/dev/null || echo 0)) / 86400 ))
    if [ "$days_old" -lt 30 ]; then
      score=$((score + 20))
    elif [ "$days_old" -lt 90 ]; then
      score=$((score + 15))
    elif [ "$days_old" -lt 365 ]; then
      score=$((score + 10))
    fi
    # For very old decisions, apply decay only if not #pattern
    if [ "$days_old" -gt 730 ] && ! grep -q "#pattern" "$file"; then
      score=$((score / 2))
    fi
  fi
  
  # Factor 4: Exclude archived by default
  if grep -q "#archived\|#deprecated" "$file"; then
    score=$((score - 100))  # De-prioritize archived
  fi
  
  scores["$file"]="$score"
done

# Sort by score (descending) and output
for file in "${!scores[@]}"; do
  echo "${scores[$file]} $file"
done | sort -rn | cut -d' ' -f2-
```

**Ranking example (API Versioning query):**

| File | Status | Product | Days Old | Score | Rank |
|------|--------|---------|----------|-------|------|
| `shopapp/api-versioning-strategy.md` | #pattern | shopapp | 45 | 50+45+15 = 110 | 1 |
| `mobile/api-versioning.md` | #resolved | mobile | 30 | 30+0+20 = 50 | 2 |
| `production/header-versioning.md` | #experimental | production | 7 | 5+0+20 = 25 | 3 |
| `shopapp/api-v2-upgrade.md` | #open | shopapp | 200 | 10+45+10 = 65 | 2 (tie-break: newer) |

---

### Filtering by Status

**Status filter combinations:**

```bash
# Show only production-ready guidance
grep -l "#pattern\|#resolved" ~/Videos/forge/brain/decisions/*.md

# Show open discussions (in-progress decision-making)
grep -l "#open" ~/Videos/forge/brain/decisions/*.md

# Show gotchas and warnings
grep -l "#gotcha\|#urgent" ~/Videos/forge/brain/learnings/*.md

# Exclude experimental/draft
grep -v "#experimental\|#draft" ~/Videos/forge/brain/decisions/*.md

# Show only "warm" decisions (touched in last 6 months)
find ~/Videos/forge/brain/decisions -type f -mtime -180 -name "*.md"
```

---

### Filtering by Tag Combinations

**AND queries** (decision must have ALL tags):

```bash
# Find database decisions that are both patterns AND resolved
grep -l "#database" ~/Videos/forge/brain/ -r --include="*.md" | \
  xargs grep -l "#pattern" | \
  xargs grep -l "#resolved"
```

**OR queries** (decision has ANY of these tags):

```bash
# Find any consistency-related decision
grep -l "#eventual-consistency\|#strong-consistency\|#consistency" \
  ~/Videos/forge/brain/decisions/ -r --include="*.md"
```

**NOT queries** (exclude these tags):

```bash
# Cache patterns excluding Redis (find Memcached, in-memory strategies)
grep -l "#cache" ~/Videos/forge/brain/patterns/ -r --include="*.md" | \
  xargs grep -v "#redis"
```

**Complex combinations:**

```bash
# Find: (Database OR Cache) AND Pattern AND Resolved AND NOT Archived
grep -l "#database\|#cache" ~/Videos/forge/brain/ -r --include="*.md" | \
  xargs grep -l "#pattern" | \
  xargs grep -l "#resolved" | \
  xargs grep -v "#archived"
```

---

### Result Deduplication

**Scenario:** Same pattern exists in multiple products (shopapp, mobile, production).

**Deduplication strategy:**

```bash
#!/bin/bash
# Deduplicate results by semantic hash

declare -A seen_hashes

for file in $(grep -r "cache strategy" ~/Videos/forge/brain/ --include="*.md" -l); do
  # Extract content hash from title + first 3 sentences
  hash=$(cat "$file" | head -10 | sha256sum | cut -d' ' -f1)
  
  if [ -z "${seen_hashes[$hash]}" ]; then
    # First occurrence: show full result
    echo "PRIMARY: $file"
    seen_hashes[$hash]="$file"
  else
    # Duplicate: show as "Also found in"
    primary="${seen_hashes[$hash]}"
    echo "ALSO_IN: $file (primary: $primary)"
  fi
done
```

**Output format for deduplicated results:**

```markdown
## Result: Cache Strategy Pattern

**Primary:** brain/patterns/cache-strategy-canonical.md
**Also found in:**
- brain/decisions/shopapp-cache-2025-01-15.md
- brain/decisions/mobile-cache-2025-01-10.md

**Summary:** URL path-based versioning with 180-day deprecation window...
```

---

### Pagination Strategy

**For 100+ results:**

```bash
# Show top 5 with scores
top_results=$(grep -r "$KEYWORD" ~/Videos/forge/brain --include="*.md" -l | \
  head -5)

echo "Showing 1-5 of $(grep -r "$KEYWORD" ~/Videos/forge/brain --include="*.md" -l | wc -l) results"
echo ""
echo "Commands:"
echo "  show next     - show results 6-10"
echo "  show all api  - show all results tagged #api"
echo "  show top 20   - show top 20 results"
```

---

## 14. Hybrid Search Decision Tree

**Use this flowchart to choose the right brain-recall strategy:**

```
START: I need to find something in the brain
│
├─→ "I know the exact file path"
│   └─→ USE: brain-read (faster, direct retrieval)
│       (brain/decisions/2025-01-15-api-versioning.md)
│
├─→ "I want to understand WHY a decision was made"
│   └─→ USE: brain-why (full provenance, decision history)
│       (traces decision back to original problem, context, alternatives)
│
├─→ "I want to map RELATIONSHIPS between decisions"
│   └─→ USE: brain-link (semantic edges, related patterns)
│       (shows: "Cache decisions are related to eventual-consistency patterns")
│
├─→ "I'm searching for something general (keyword/tag)"
│   │
│   ├─→ "Search is simple (1-2 keywords, no filters)"
│   │   └─→ USE: grep alone
│   │       grep -r "API versioning" ~/Videos/forge/brain/decisions/
│   │
│   ├─→ "I want to filter by product/status/tags"
│   │   └─→ USE: brain-recall with filters
│   │       product=shopapp tag=#pattern tag=#resolved
│   │       (grep + tag filtering + ranking)
│   │
│   ├─→ "Results exceed 50, need to narrow down"
│   │   └─→ USE: brain-recall with filters
│   │       Re-run with: product=X OR tag=#pattern OR date_range
│   │
│   └─→ "I need semantic search (similar concepts, synonyms)"
│       └─→ USE: brain-link (index-based, slow but semantic)
│           (finds: saga ≈ orchestration ≈ distributed transaction)
│
└─→ "I'm exploring brain structure/metadata"
    └─→ USE: brain-read (list products, projects, available tags)
        (brain/README.md, brain/TAG-GUIDE.md)
```

---

## 15. Common Recall Pitfalls

### Pitfall 1: Search Term Too Broad (Gets 100 Results, Unclear Which Is Relevant)

**Problem:** User searches "cache" and gets 150+ results across Redis, Memcached, HTTP caching, database query caching.

**Why it happens:** No automatic scoping; all products/projects treated equally.

**How to fix:**
```bash
# Instead of:
grep -r "cache" ~/Videos/forge/brain/

# Do:
grep -r "cache" ~/Videos/forge/brain/decisions/ | \
  grep "product: shopapp" | \
  grep "#pattern\|#resolved" | \
  head -5  # Top 5 results only
```

**Lesson:** Always add at least one filter: product, tag, or date range. If results > 20, add another filter.

---

### Pitfall 2: Archived Decisions Still in Grep Results (Outdated Guidance)

**Problem:** Old decision from 2023 is still returned, contradicts current approach (learned in 2025).

**Why it happens:** Archived decisions are in grep results; no automatic filtering.

**How to fix:**
```bash
# Exclude archived by default
grep -r "API version" ~/Videos/forge/brain/decisions/ --include="*.md" | \
  grep -v "#archived" | grep -v "#deprecated"

# Check for "superseded_by" link
grep -A 20 "superseded_by" ~/Videos/forge/brain/decisions/*.md
```

**Lesson:** Exclude #archived/#deprecated unless explicitly requested. Look for "superseded_by" links.

---

### Pitfall 3: Same Concept, Different Terminology (Searches Miss Related Decisions)

**Problem:** User searches "distributed transaction" but all decisions use "saga" or "orchestration".

**Why it happens:** Grep is literal text matching; no synonym handling.

**How to fix:**
1. Add "Also called" or "keywords" section to frontmatter:
   ```yaml
   keywords: [saga, orchestration, distributed-transaction, workflow]
   ```
2. Search with multiple terms:
   ```bash
   grep -r "saga\|orchestration\|distributed.transaction\|distributed.workflow" \
     ~/Videos/forge/brain/ --include="*.md"
   ```

**Lesson:** If first search returns 0 results, try synonyms. Use `brain-link` for semantic relationships.

---

### Pitfall 4: No Ranking, First Result != Most Relevant

**Problem:** Grep returns results in filesystem order (alphabetical), not relevance order.

**Why it happens:** Raw grep has no ranking; no weighting for status/recency/product match.

**How to fix:** Always apply ranking algorithm (Section 13) before presenting results.

```bash
# Don't just pipe to `head`:
grep -r "cache" ~/Videos/forge/brain/ --include="*.md" -l | head -5

# Instead, score and rank:
# (use ranking pseudocode from Section 13)
```

**Lesson:** Implement ranking by: status (#pattern > #resolved > #open), product match, recency.

---

### Pitfall 5: Tag Spam (Too Many Tags, Hard to Use for Filtering)

**Problem:** Brain has 150+ unique tags; user doesn't know if to search #cache or #redis or #caching.

**Why it happens:** Tags grow organically; no governance; synonyms allowed.

**How to fix:**
1. Create canonical tag registry: `brain/TAG-GUIDE.md`
2. Normalize old decisions (one-time migration)
3. Show tag suggestions in UI:
   ```
   Query: #cach
   Did you mean: #cache, #redis, #memcached, #caching (deprecated, use #cache)
   ```

**Lesson:** Maintain a TAG-GUIDE.md. Allow aliases (#cache → primary, #caching → deprecated alias).

---

## 16. Caching & Performance

### Search Result Caching

**Cache duration strategy:**
- **Do NOT cache search results** (brain updates frequently with new decisions)
- **DO cache brain metadata:**
  - List of available products: 24 hours
  - List of available tags: 12 hours (tags added more frequently)
  - Brain index (filename → title/date/product/tags): 6 hours

**Cache invalidation:**
```bash
# Invalidate cache when brain is updated
# (triggered by brain-write skill)

# When brain-write completes:
# 1. Invalidate search results cache (already empty)
# 2. Invalidate metadata cache (24h TTL reset)
# 3. Rebuild brain index (if using index strategy)
```

---

### When to Re-Search

**Re-run brain-recall when:**
1. **New decisions added:** Use cache; re-search only if user requested "updated results"
2. **Decision status changed:** If decision went from #open → #resolved, it now ranks higher; suggest re-search
3. **Large time gap:** If last search was >1 day ago, suggest re-search (brain may have grown)

**Heuristic:**
```bash
# After each brain-write, notify searcher:
# "New decision added: 'API Versioning for new product'.
#  Your previous search 'API versioning' may have new results."
```

---

### Brain Growth Projections

**Grep performance degradation:**

| Brain Size | Search Time | Recommendation |
|-----------|-------------|---|
| <500 decisions | <50ms | Grep sufficient |
| 500-2000 | 50-200ms | Grep acceptable, consider filtering |
| 2000-5000 | 200-500ms | Require filters; consider index |
| 5000-10000 | 500-2000ms | Index essential |
| >10000 | >2000ms | Migrate to Elasticsearch/similar |

**Current status (2025-04):** Brain ~500 decisions. No optimization needed yet. Plan index at 2000.

---

### When to Migrate to Brain-Link Indexing

**Migrate when:**
1. **Grep searches consistently >1 second** (brain >5000 decisions)
2. **Semantic search needed** (same concept, different terminology)
3. **Complex multi-dimensional queries** (product × tag × status × recency simultaneously)

**Migration path (product “Phase 2” — after grep-first brain + scan layout are stable):**
1. Use `brain-link` / a dedicated indexer to build an embedding or hybrid (BM25 + dense) index
2. Query against the index instead of grepping all files
3. Fall back to grep for simple filename-based queries

**Implementation sketch:**
```bash
# Phase 1: Build embeddings for all decisions
for file in ~/Videos/forge/brain/decisions/*.md; do
  title=$(grep "^title:" "$file")
  content=$(tail -n +5 "$file" | head -20)
  embedding=$(call_claude_api "$title\n$content")
  # Store: filename → embedding in index
done

# Phase 2: Query against embeddings
query_embedding=$(call_claude_api "API versioning")
# Find nearest neighbors in embedding space
# Return top-5 by cosine similarity
```

---

## 17. Production Readiness Checklist

- [x] Grep-based search with examples
- [x] Tag filtering (AND, OR, NOT combinations)
- [x] Product/project filtering
- [x] Relevance ranking algorithm (multi-factor)
- [x] Output formatting with traceability
- [x] Query examples and workflows
- [x] 7 edge cases with detection, mitigation, escalation
- [x] Ranking & filtering strategies with examples
- [x] Hybrid search decision tree (grep vs brain-read vs brain-why vs brain-link)
- [x] 5 common pitfalls with fixes
- [x] Caching & performance section
- [x] Brain growth projections and migration path
- [x] No placeholders or draft language
- [x] Production-ready guidance

## Checklist

Before claiming recall is complete:

- [ ] Brain directory searched with at least 3 distinct query terms
- [ ] Cross-product search performed (not limited to current product)
- [ ] All matches reviewed by relevance, not just the most recent
- [ ] Zero-result queries retried with broader synonyms and domain-level tags
- [ ] Hybrid search used where applicable (grep → brain-read → brain-why for deep provenance)
- [ ] Recall findings documented before the decision proceeds

