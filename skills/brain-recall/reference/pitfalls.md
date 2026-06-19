# Common Recall Pitfalls

> Deep reference for brain-recall. The operational contract lives in
> [`../SKILL.md`](../SKILL.md). Ranking references below point to
> [`ranking.md`](ranking.md) (the canonical ranking spec).

### Pitfall 1: Search Term Too Broad (Gets 100 Results, Unclear Which Is Relevant)

**Problem:** User searches "cache" and gets 150+ results across Redis, Memcached, HTTP caching, database query caching.

**Why it happens:** No automatic scoping; all products/projects treated equally.

**How to fix:**
```bash
# Instead of:
grep -r "cache" ~/forge/brain/

# Do:
grep -r "cache" ~/forge/brain/decisions/ | \
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
grep -r "API version" ~/forge/brain/decisions/ --include="*.md" | \
  grep -v "#archived" | grep -v "#deprecated"

# Check for "superseded_by" link
grep -A 20 "superseded_by" ~/forge/brain/decisions/*.md
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
     ~/forge/brain/ --include="*.md"
   ```

**Lesson:** If first search returns 0 results, try synonyms. Use `brain-link` for semantic relationships.

---

### Pitfall 4: No Ranking, First Result != Most Relevant

**Problem:** Grep returns results in filesystem order (alphabetical), not relevance order.

**Why it happens:** Raw grep has no ranking; no weighting for status/recency/product match.

**How to fix:** Always apply ranking algorithm ([`ranking.md`](ranking.md)) before presenting results.

```bash
# Don't just pipe to `head`:
grep -r "cache" ~/forge/brain/ --include="*.md" -l | head -5

# Instead, score and rank:
# (use ranking pseudocode from ranking.md)
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
