# Caching & Performance

> Deep reference for brain-recall. The operational contract lives in
> [`../SKILL.md`](../SKILL.md).

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
for file in ~/forge/brain/decisions/*.md; do
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
