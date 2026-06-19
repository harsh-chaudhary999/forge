# Relevance Ranking & Filtering Strategies

> Deep reference for brain-recall. The operational contract lives in
> [`../SKILL.md`](../SKILL.md). This file is the **single, canonical** ranking spec
> — the earlier duplicate ranking pseudocode (the `score + 30 / + 20 / + 15`
> variant keyed on `status: active`/`warm` only) has been collapsed into the
> status-tier algorithm below. Use this one.

## Ranking Criteria (descending priority)

Results are ranked by multiple factors to surface the most applicable decisions:

1. **Same product/project match** (heaviest, path-based)
   - If query includes a product/project filter, matching results (decision under
     `products/<slug>/`) rank far higher.

2. **Lifecycle status** (`active | warm | cold | archived`)
   - `status: active` ranks highest; `warm` (recently demoted, still relevant) next;
     `cold` (aging out) lower; `archived` (superseded/deprecated) lowest.
   - `LOCKED` decisions rank higher than `DRAFT` proposals.

3. **Recency** (weighted by status)
   - Decisions from the last 30/90/365 days get a recency bonus.
   - Within the same recency tier, more recent ranks higher.
   - Very old decisions (>730 days) that are **not** `active` get their score halved.

4. **Tag match count**
   - Results matching more query tags rank higher.
   - Exact tag match ranks higher than partial keyword match.

5. **Document type priority**
   - Patterns > Decisions > Learnings (for architectural queries)
   - Learnings > Decisions > Patterns (for gotchas/warnings)

## Scoring Algorithm (canonical, status-tier based)

```bash
#!/bin/bash
# Ranking pseudocode

KEYWORD="$1"
PRODUCT="${2:-}"  # Optional product filter

declare -A scores

# Find all matching files
for file in $(grep -r "$KEYWORD" ~/forge/brain --include="*.md" -l); do
  score=0
  
  # Factor 1: Lifecycle status multiplier (heaviest weight)
  if grep -q "^status: active" "$file"; then
    score=$((score + 50))  # Active
  elif grep -q "^status: warm" "$file"; then
    score=$((score + 30))  # Recently demoted, still relevant
  elif grep -q "^status: cold" "$file"; then
    score=$((score + 10))  # Aging out
  elif grep -q "^status: archived" "$file"; then
    score=$((score + 5))   # Superseded/deprecated
  fi
  
  # Factor 2: Product scope match (path-based, 3x multiplier)
  if [ -n "$PRODUCT" ] && [[ "$file" == *"/products/$PRODUCT/"* ]]; then
    score=$((score + 45))
  fi
  
  # Factor 3: Recency (weighted by status)
  date=$(grep -E "^date(_locked)?:" "$file" | head -1 | cut -d: -f2- | xargs)
  if [ -n "$date" ]; then
    days_old=$(( ($(date +%s) - $(date -d "$date" +%s 2>/dev/null || echo 0)) / 86400 ))
    if [ "$days_old" -lt 30 ]; then
      score=$((score + 20))
    elif [ "$days_old" -lt 90 ]; then
      score=$((score + 15))
    elif [ "$days_old" -lt 365 ]; then
      score=$((score + 10))
    fi
    # For very old decisions, apply decay unless still active
    if [ "$days_old" -gt 730 ] && ! grep -q "^status: active" "$file"; then
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

## Filtering by Status

**Status filter combinations:**

```bash
# Show only production-ready guidance
grep -l "#pattern\|#resolved" ~/forge/brain/decisions/*.md

# Show open discussions (in-progress decision-making)
grep -l "#open" ~/forge/brain/decisions/*.md

# Show gotchas and warnings
grep -l "#gotcha\|#urgent" ~/forge/brain/learnings/*.md

# Exclude experimental/draft
grep -v "#experimental\|#draft" ~/forge/brain/decisions/*.md

# Show only "warm" decisions (touched in last 6 months)
find ~/forge/brain/decisions -type f -mtime -180 -name "*.md"
```

---

## Filtering by Tag Combinations

**AND queries** (decision must have ALL tags):

```bash
# Find database decisions that are both patterns AND resolved
grep -l "#database" ~/forge/brain/ -r --include="*.md" | \
  xargs grep -l "#pattern" | \
  xargs grep -l "#resolved"
```

**OR queries** (decision has ANY of these tags):

```bash
# Find any consistency-related decision
grep -l "#eventual-consistency\|#strong-consistency\|#consistency" \
  ~/forge/brain/decisions/ -r --include="*.md"
```

**NOT queries** (exclude these tags):

```bash
# Cache patterns excluding Redis (find Memcached, in-memory strategies)
grep -l "#cache" ~/forge/brain/patterns/ -r --include="*.md" | \
  xargs grep -v "#redis"
```

**Complex combinations:**

```bash
# Find: (Database OR Cache) AND Pattern AND Resolved AND NOT Archived
grep -l "#database\|#cache" ~/forge/brain/ -r --include="*.md" | \
  xargs grep -l "#pattern" | \
  xargs grep -l "#resolved" | \
  xargs grep -v "#archived"
```

---

## Result Deduplication

**Scenario:** Same pattern exists in multiple products (shopapp, mobile, production).

**Deduplication strategy:**

```bash
#!/bin/bash
# Deduplicate results by semantic hash

declare -A seen_hashes

for file in $(grep -r "cache strategy" ~/forge/brain/ --include="*.md" -l); do
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

## Pagination Strategy

**For 100+ results:**

```bash
# Show top 5 with scores
top_results=$(grep -r "$KEYWORD" ~/forge/brain --include="*.md" -l | \
  head -5)

echo "Showing 1-5 of $(grep -r "$KEYWORD" ~/forge/brain --include="*.md" -l | wc -l) results"
echo ""
echo "Commands:"
echo "  show next     - show results 6-10"
echo "  show all api  - show all results tagged #api"
echo "  show top 20   - show top 20 results"
```
