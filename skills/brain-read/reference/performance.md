# Performance Guidelines

### When Grep is Fast vs Slow

**Fast (< 500ms):**
- Searching within a single product: `grep -r "term" products/payment/decisions/`
- Searching a specific file type: `grep -r "term" . --include="*.md"`
- Simple patterns without alternation: `grep "exact phrase" file.md`
- Number of files: < 1000

**Slow (> 2 seconds):**
- Recursive search across entire brain: `grep -r "term" .`
- Complex regex patterns: `grep -r "pattern.*with.*alternation\|complex.*regex" .`
- Case-insensitive searches: `grep -ri "term" .`
- Number of files: > 5000 or deeply nested

### Optimization Tips

**Narrow the scope first:**
```bash
# BAD: Searches entire brain
grep -r "versioning" ~/forge/brain

# GOOD: Searches only decisions in one product
grep -r "versioning" ~/forge/brain/products/payment/decisions/
```

**Use --include to filter by filetype:**
```bash
# BAD: May search logs, temp files
grep -r "contract" ~/forge/brain

# GOOD: Only searches markdown
grep -r "contract" ~/forge/brain --include="*.md"
```

**Use --exclude to skip slow areas:**
```bash
# Exclude archived decisions to speed search
grep -r "status.*proposed" products/ --include="*.md" --exclude-dir="archived"
```

**Combine grep with other tools:**
```bash
# Search with grep, then count matches by file
grep -r "decision" products/ --include="*.md" | cut -d: -f1 | sort | uniq -c

# Search, then show only filenames
grep -r "API versioning" . --include="*.md" -l
```

### When to Use Grep vs Brain Skills

**Use `brain-read` (grep):**
- Exact phrase search ("REST API")
- File path known or guessable
- Quick lookup (< 1 second search)
- Structured data matching (tags, dates)

**Use `brain-recall` (ranked grep + tag/status search):**
- Conceptual search ("How do we handle backward compatibility?")
- Finding related decisions across products
- Fuzzy matching (misspellings, synonyms)
- "What did we learn about..." queries

**Use `brain-link` (semantic edges):**
- Finding decisions that depend on each other
- Tracing impact of a decision change
- Understanding decision graph (which decision blocks which)

**Use `brain-why` (provenance):**
- Tracing why a decision was made
- Finding who made a decision and when
- Audit trail for compliance

### Caching Strategy

Grep results can become stale if decisions are updated:

- **Cache validity:** 30 minutes (typical decision update frequency)
- **Invalidate cache if:** A related decision changes, dependencies shift, product topology changes
- **Re-check immediately if:** Decision is about-to-be-made, implementation is starting, or auditing for compliance

```bash
# Quick cache check: grep results from 30 minutes ago
find ~/forge/brain/products -name "*.md" -mmin -30
```

### Architecture: Grep Now, Indexing Later

**Current (Phase 1):**
- Grep-based read (no overhead)
- Linear scan through brain markdown
- Fast for small brains (< 1000 decisions)
- Sufficient for manual exploration

**Future (Phase 2 — not implemented today; see `forge-brain-layout` Phase-2 prep):**
- `brain-link` adds semantic edges between decisions
- full-text / embedding indexing over the brain
- `brain-why` adds provenance index
- Enables sub-100ms queries on large brains (> 10k decisions)
- Maintains markdown as source of truth
