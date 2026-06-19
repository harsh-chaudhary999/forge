# Common Search Pitfalls

### Pitfall 1: Grep is Case-Sensitive, Misses Variations

**Problem:** `grep "API"` won't find "api" or "Api".

**Solution:**
```bash
# Use -i for case-insensitive search
grep -ri "api" products/payment/decisions/

# Or be explicit about variations
grep -r "API\|api\|Api" products/payment/decisions/
```

**Example:**
```bash
# Misses lowercase variants
grep -r "REST" products/ --include="*.md"

# Catches all variations
grep -ri "rest" products/ --include="*.md"
```

### Pitfall 2: Brain Paths Must Be Exact (No Wildcards in Filenames)

**Problem:** `cat products/payment/contracts/*.md` may not work as expected in scripts.

**Solution:**
```bash
# Use find for wildcard expansion
find products/payment/contracts -name "*.md"

# Or specify exact filename
cat products/payment/contracts/api-rest.md
```

**Example of failure:**
```bash
# May fail if filename has spaces or special chars
cat products/*/contracts/api-*.md

# Safer approach
find products -path "*/contracts/api-*.md" -type f
```

### Pitfall 3: Decision References May Be Stale (Decisions Get Archived)

**Problem:** A decision might reference another decision that was archived or renamed.

**Solution:**
```bash
# Search for archived decisions too
grep -r "archived\|deprecated\|superseded" products/*/decisions/ --include="*.md"

# Verify references still exist
grep -r "See decision: " products/*/decisions/ --include="*.md" -h | while read ref; do
  [ -f "$ref" ] && echo "OK: $ref" || echo "BROKEN: $ref"
done
```

**Example:**
```bash
# Old decision might say: "See decision: 2023-old-approach.md"
# But file may have been archived to: archive/2023-old-approach.md
grep -r "See decision" products/ --include="*.md"
```

### Pitfall 4: Large Grep Across Entire Brain is Slow (Scope Narrowly)

**Problem:** `grep -r "database" ~/forge/brain` scans 10,000+ files.

**Solution:**
```bash
# Scope to product, then to decision type
grep -r "database" products/payment/decisions/ --include="*.md"

# Further optimize with --include
grep -r "database" products/payment/decisions/ --include="*2024*.md"
```

**Benchmark:**
```
Entire brain:        ~2 seconds
Single product:      ~200ms
Single year:         ~400ms
Single decision dir: ~50ms
```

### Pitfall 5: Mixed Content Types (Decisions, PRDs, Specs) Need Different Patterns

**Problem:** `grep -r "versioning" .` finds decisions, specs, AND PRDs—hard to filter signal.

**Solution:**
```bash
# Search only decisions
grep -r "versioning" products/*/decisions/ --include="*.md"

# Search only PRDs
grep -r "versioning" prds/*/prd-locked.md

# Search contracts separately
grep -r "versioning" products/*/contracts/ --include="*.md"
```

**Example:**
```bash
# Mixed results (hard to interpret)
grep -ri "api version" ~/forge/brain | head -20

# Targeted results
grep -ri "api.*version" products/*/decisions/ | head -20
```
