# Retrieval Performance Edge Cases

> Deep reference for brain-recall. The operational contract (Iron Law, Red Flags,
> core workflow, edge-case SUMMARY, decision tree, checklist) lives in
> [`../SKILL.md`](../SKILL.md). This file holds the full edge-case catalog.

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
COUNT=$(grep -r "cache" ~/forge/brain/decisions/ --include="*.md" -l | wc -l)
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
grep -r "cache" ~/forge/brain/ --include="*.md" -l > /dev/null
time_end=$(date +%s%N)
duration_ms=$(( (time_end - time_start) / 1000000 ))

if [ "$duration_ms" -gt 1000 ]; then
  echo "EDGE CASE: Grep took ${duration_ms}ms. Consider indexing."
fi

# Check brain file count
DECISION_COUNT=$(find ~/forge/brain/decisions -type f | wc -l)
if [ "$DECISION_COUNT" -gt 5000 ]; then
  echo "WARNING: Brain has $DECISION_COUNT decisions. Indexing recommended."
fi
```

**How to mitigate?** (using what exists today)
1. **Index-first via OKF `index.md`:** read the scope's `decisions/<category>/index.md` (a one-row-per-file table — see `forge-brain-layout`) before grepping bodies; it's the cheap table of contents.
2. **Prefer the brain MCP `brain_recall`** (read-only substring scan that computes the brain root itself) over hand-rolled greps; see [`docs/brain-mcp.md`](../../../docs/brain-mcp.md).
3. **Lazy-load for ranking:** read only frontmatter (first ~20 lines) per file, not the full body.
4. **Parallel search:** `grep -rl ... | xargs -P 4 ...` on multi-core systems.
5. **Archive old decisions:** move decisions >2 years old to `~/forge/brain/archived/` to shrink the active set.

**When to escalate?**
- Use `brain-why` for provenance/lineage (frontmatter + git history; the MCP `brain_why` tool does this in one call).

> **Not implemented today (design-intent only):** a precomputed `brain/index.json`,
> embedding/vector search, and an Elasticsearch backend do **not** exist in Forge and
> are **not** how recall works — do not instruct an operator to build or query them.
> Forward-looking retrieval (FTS/embeddings) is tracked once, optionally, in
> `forge-brain-layout` ("Phase 2 prep"); treat that as the single source for futures.

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
grep -r "#archived\|#deprecated" ~/forge/brain/decisions/ --include="*.md" -l

# Check if recent search includes old decisions
grep -r "API version" ~/forge/brain/decisions/ --include="*.md" | \
  grep -E "2024|2025-01|2025-02"  # Find old dates
```

**How to mitigate?**
1. **Exclude archived by default:**
   ```bash
   # Standard search (exclude archived)
   grep -r "API version" ~/forge/brain/decisions/ --include="*.md" | \
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
for file in ~/forge/brain/decisions/*.md; do
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
grep -r "^tags:" ~/forge/brain/ --include="*.md" | \
  sed 's/.*tags: //g' | tr ',' '\n' | tr -d '[]" ' | sort | uniq | wc -l

# If > 80, tag explosion likely
# Show tag frequency to identify unused tags
grep -r "^tags:" ~/forge/brain/ --include="*.md" | \
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
for file in ~/forge/brain/decisions/*.md; do
  tail -n +5 "$file" | head -3 | sha256sum | awk '{print $1}' > "${file}.hash"
done
# Group by hash to find similar content with different titles

# Or manually: check for decision titles with different terminology
grep "^title:" ~/forge/brain/decisions/*.md | grep -i "saga\|transaction\|orchestration\|workflow"
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
grep -r "^date: 2025-04" ~/forge/brain/decisions/ --include="*.md" | \
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
