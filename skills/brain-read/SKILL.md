---
name: brain-read
description: "WHEN: You need to look up product topology, project metadata, past decisions, or contract details from the brain."
type: flexible
---

# Brain Read

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I remember what the decision said" | Memory drifts. The brain is the source of truth — read the actual file. |
| "I'll just grep for the keyword" | Grep finds text, not context. Follow the structured read patterns to get full decision provenance. |
| "The product topology hasn't changed" | Products evolve between PRDs. Always reload topology before assuming repo lists, stacks, or services. |
| "I'll read the spec from the working directory" | The working directory may have uncommitted changes. The brain's git-backed copy is the locked, canonical version. |
| "I only need one section of the decision" | Partial reads miss linked context: alternatives considered, evidence, constraints. Read the full record. |

**If you are thinking any of the above, you are about to violate this skill.**

The brain at `~/forge/brain/` is git-backed markdown. Read patterns:

## Product Topology
```bash
cd ~/forge/brain
cat products/<product-slug>/product.md
```

Gives you: repos, roles, tech stacks, deployment strategies, services, contracts.

## Project Metadata
```bash
cat projects/<project-slug>/overview.md
cat projects/<project-slug>/tech-stack.md
cat projects/<project-slug>/conventions.md
```

## Locked PRD
```bash
cat prds/<task-id>/prd-locked.md
```

## Shared Dev Spec
```bash
cat prds/<task-id>/shared-dev-spec.md
```

## Contract Details
```bash
cat products/<product-slug>/contracts/api-rest.md
cat products/<product-slug>/contracts/schema-mysql.md
```

## Search

If you don't know the exact path, search:

```bash
cd ~/forge/brain
grep -r "search term" . --include="*.md"
```

## Grep Pattern Examples

Real-world patterns for querying the decision brain:

### Pattern 1: Decisions by Product and Tag

**Use case:** Find all decisions for a product that relate to a specific domain (e.g., authentication).

```bash
cd ~/forge/brain
grep -r "tags.*auth" products/payment/decisions/ --include="*.md"
```

**What it finds:** All decisions in the payment product with "auth" tags.

**When to use:** Planning features that depend on past auth choices in a product.

**Example output:**
```
products/payment/decisions/2024-oauth-migration.md: tags: auth, security, deprecated
products/payment/decisions/2024-jwt-standards.md: tags: auth, standardization, api
```

### Pattern 2: API Versioning Decisions Across Products

**Use case:** Find all versioning strategies used across products to maintain consistency.

```bash
cd ~/forge/brain
grep -r "versioning\|api.*version\|v[0-9]\+.*deprecated" products/*/decisions/ --include="*.md" -i
```

**What it finds:** All decisions about API versioning, versioning strategies, and deprecation policies.

**When to use:** Planning a new API contract or deprecating an endpoint.

**Example output:**
```
products/payment/decisions/2024-api-versioning.md: **Versioning Strategy**: Semantic versioning (major.minor.patch)
products/auth/decisions/2023-rest-v2-sunset.md: API v1 deprecated in favor of v2 with 12-month sunset window
```

### Pattern 3: Performance-Related Patterns from Past Projects

**Use case:** Find lessons learned about performance across projects.

```bash
cd ~/forge/brain
grep -r "performance\|latency\|throughput\|optimization\|cache" projects/*/decisions/ --include="*.md" -i
```

**What it finds:** Performance-related decisions, benchmarks, and lessons learned across projects.

**When to use:** Planning optimizations or benchmarking new components.

**Example output:**
```
projects/search-optimization/decisions/2024-indexing-strategy.md: Reduced query latency from 500ms to 45ms
projects/checkout-perf/decisions/2024-connection-pooling.md: Connection pool size tuned from 10 to 50 for 3x throughput
```

### Pattern 4: Contract Specifications by Type

**Use case:** Find all contracts of a specific type (API, Database, Events).

```bash
cd ~/forge/brain
grep -r "contract-type.*api\|contract-type.*database\|contract-type.*events" products/*/contracts/ --include="*.md" -i
```

**Alternative (by filename):**
```bash
cd ~/forge/brain/products
find . -path "*/contracts/api-*.md" -o -path "*/contracts/schema-*.md" -o -path "*/contracts/events-*.md"
```

**What it finds:** All API, database, and event contracts.

**When to use:** Negotiating a new contract or validating a service boundary.

**Example output:**
```
products/payment/contracts/api-rest.md
products/payment/contracts/schema-mysql.md
products/events/contracts/events-kafka.md
```

### Pattern 5: Lessons Learned on a Specific Topic

**Use case:** Find all retrospectives and lessons about a topic (e.g., database migrations).

```bash
cd ~/forge/brain
grep -r "lesson\|retrospective\|learned\|pitfall\|gotcha" projects/*/decisions/ --include="*.md" -i | grep -i "migration\|database"
```

**What it finds:** Documented lessons and pitfalls about database work.

**When to use:** Planning a migration or learning from past experience.

**Example output:**
```
projects/schema-migration-2024/decisions/2024-zero-downtime-strategy.md: **Lessons Learned**: Always test rollback path first
projects/auth-db-migration/decisions/2023-dual-write-period.md: **Pitfall**: Leaving dual-write running too long causes data skew
```

### Pattern 6: Cross-Product Patterns and Standards

**Use case:** Find standards and patterns used consistently across multiple products.

```bash
cd ~/forge/brain
grep -r "standard\|convention\|pattern" products/*/decisions/ --include="*.md" -i | cut -d: -f1 | sort | uniq -c | sort -rn
```

**What it finds:** Patterns that appear across multiple products (indicating shared standards).

**When to use:** Evaluating whether to propose a new cross-product standard.

**Example output:**
```
5 products/payment/decisions/2024-error-response-format.md
5 products/auth/decisions/2024-error-response-format.md
5 products/events/decisions/2024-error-response-format.md
```

### Pattern 7: Decision Lifecycle Tracking

**Use case:** Find all decisions for a feature area from proposal through implementation.

```bash
cd ~/forge/brain
grep -r "status.*proposed\|status.*approved\|status.*deprecated\|archived" products/*/decisions/ --include="*.md" -i
```

**What it finds:** Decision status across the lifecycle (proposed → approved → deprecated → archived).

**When to use:** Understanding which decisions are active vs archived.

**Example output:**
```
products/payment/decisions/2024-old-gateway.md: status: archived (replaced by 2024-new-gateway.md)
products/auth/decisions/2024-oauth-flow.md: status: approved, implemented
```

### Pattern 8: Time-Based Decision Search

**Use case:** Find all decisions made in a specific quarter or year.

```bash
cd ~/forge/brain
grep -r "^date.*202[34]-Q[1-4]\|decided.*202[34]" products/*/decisions/ --include="*.md" | head -20
```

**What it finds:** Decisions grouped by decision date.

**When to use:** Understanding decision velocity or tracing what was decided during a specific period.

**Example output:**
```
products/payment/decisions/2024-q2-gateway-choice.md: date: 2024-Q2
products/auth/decisions/2024-q2-oauth-migration.md: date: 2024-Q2
```

## Performance Guidelines

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
grep -r "status.*proposed" products/ --include="*.md" --exclude-dir="archive"
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

**Use `brain-recall` (semantic search):**
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

**Future (Phase 2):**
- `brain-link` adds semantic tags to decisions
- `brain-recall` adds full-text indexing
- `brain-why` adds provenance index
- Enables sub-100ms queries on large brains (> 10k decisions)
- Maintains markdown as source of truth

## Search Strategies by Use Case

Decision tree: For each use case, which grep pattern and brain skill combination to use.

### Use Case 1: Finding Past Decisions on Topic X

**Example:** "We've handled database migrations before. What did we decide?"

**Recommended grep pattern:**
```bash
grep -r "database.*migration\|schema.*change" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-recall`: For fuzzy semantic search ("How have we upgraded databases?")
- `brain-why`: To trace why old approaches were deprecated

**Workflow:**
1. Start with grep pattern above
2. If results are sparse, use brain-recall for semantic matching
3. If decision exists, use brain-why to understand rationale

### Use Case 2: Locating Contract for Specific Service

**Example:** "What's the API contract for the payment service?"

**Recommended grep pattern:**
```bash
cat products/payment/contracts/api-rest.md
# OR search if unsure:
grep -r "payment" products/*/contracts/ --include="*.md"
```

**Also use:**
- `brain-link`: To find dependent contracts (payment API → auth API)
- `brain-read`: Direct file access (contracts are well-organized)

**Workflow:**
1. Use direct file access if you know the service name
2. Use grep only if service name is ambiguous
3. Use brain-link to validate contract dependencies

### Use Case 3: Identifying Patterns Used Across Products

**Example:** "How do multiple products handle API versioning? Are we consistent?"

**Recommended grep pattern:**
```bash
grep -r "versioning\|version.*strategy" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-recall`: For semantic clustering ("version management approaches")
- `brain-link`: To show pattern relationships across products

**Workflow:**
1. Use grep to find all versioning decisions
2. Use brain-recall to cluster similar approaches
3. Use brain-link to show cross-product edges

### Use Case 4: Tracing Decision History (When Changed, Why)

**Example:** "We moved to a new payment gateway. When was that decided? What was the old approach?"

**Recommended grep pattern:**
```bash
grep -r "payment.*gateway\|deprecated.*gateway" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-why`: To trace decision provenance (who decided, when, rationale)
- `brain-link`: To find related decisions (new gateway depends on auth changes)

**Workflow:**
1. Use grep to find decision(s)
2. Use brain-why for full audit trail (when, who, rationale)
3. Use brain-link to show decision dependencies

### Use Case 5: Validating Against Contract Before Implementation

**Example:** "Before coding, verify: what's the API schema we promised?"

**Recommended path:**
```bash
cat products/payment/contracts/api-rest.md
```

**Also use:**
- `brain-read`: Direct file access (contracts are versioned)
- No grep needed (exact path is known)

**Workflow:**
1. Read contract directly
2. Cross-reference against related decisions (grep)
3. Use brain-link to confirm dependencies haven't changed

## Common Search Pitfalls

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

## Edge Cases

### Edge Case 1: Brain not initialized (empty brain/ directory)

**Symptom:** Brain directory exists but contains no decisions, contracts, or products.

**Do NOT:** Proceed with grep search expecting results. Do NOT create decisions in arbitrary locations.

**Mitigation:** Check for brain directory structure before search:
```bash
ls -la ~/forge/brain/products/ ~/forge/brain/prds/ ~/forge/brain/decisions/
# If empty, brain is uninitialized
```

**Escalation:** NEEDS_INFRA_CHANGE — Brain initialization required before reading. Contact platform team to bootstrap brain with seed decisions and product topology.

---

### Edge Case 2: Decision file not found (grep returns nothing)

**Symptom:** Grep search returns no results or grep reports "No such file or directory".

**Do NOT:** Assume decision doesn't exist. Do NOT search with incorrect paths or typos.

**Mitigation:** 
1. Verify search path exists: `ls ~/forge/brain/products/<product>/decisions/`
2. Try broader search: `grep -r "keyword" ~/forge/brain --include="*.md"`
3. Check for archived decisions: `grep -r "keyword" ~/forge/brain/archive --include="*.md"`

**Escalation:** NEEDS_CONTEXT — Decision may not exist yet, be archived, or be named differently. Use `brain-recall` for fuzzy semantic search instead.

---

### Edge Case 3: Multiple decisions match query (ambiguous results)

**Symptom:** Grep returns 5+ matching decisions; unclear which is authoritative.

**Do NOT:** Pick the first match. Do NOT assume most recent is most relevant.

**Mitigation:**
1. Narrow search: `grep -r "exact phrase" products/<product>/decisions/ --include="*.md"`
2. Filter by status: `grep -r "status.*active" products/<product>/decisions/ --include="*.md"`
3. Check frontmatter for `decision_id:` field to identify canonical versions
4. Use `brain-why <ID>` to trace provenance if ID is clear

**Escalation:** NEEDS_COORDINATION — Multiple decisions on same topic. Consult brain-link to understand decision graph and relationships. May need decision review/consolidation.

---

### Edge Case 4: Corrupted decision file (invalid YAML or markdown)

**Symptom:** Grep finds file, but file fails to parse (missing frontmatter, broken YAML delimiters).

**Do NOT:** Edit the file without understanding corruption. Do NOT delete file.

**Mitigation:**
1. Check YAML syntax: `head -20 <file> | grep -E "^---"`
2. Verify file has opening `---` and closing `---` on separate lines
3. Use `cat -A <file> | head -20` to check for non-standard characters
4. Use `brain-read` to validate file structure before proceeding

**Escalation:** BLOCKED — Corrupted decision file cannot be reliably read. Escalate to codebase maintenance team to repair YAML or restore from git history.

---

### Edge Case 5: Brain in wrong repository location

**Symptom:** Grep or cat commands fail with "No such file or directory" or return unexpected results (wrong product).

**Do NOT:** Assume brain paths are relative. Do NOT use different brain locations without explicit verification.

**Mitigation:**
1. Verify correct brain path: `echo ~/forge/brain`
2. Confirm location matches git config: `cd ~/forge && git config forge.brain-path`
3. Check symlinks: `ls -l .claude/brain` (should link to `~/forge/brain`)
4. Explicit path in all commands: `grep -r "term" ~/forge/brain --include="*.md"`

**Escalation:** NEEDS_INFRA_CHANGE — Brain location is wrong or symlink is broken. Check environment setup or contact platform team to fix path configuration.

---

## Decision Tree: Query Strategy

```
Need to read from brain?
    ↓
Do you know the exact path or filename?
├─ YES → Use `cat ~/forge/brain/<path>/<file>.md` (direct read)
└─ NO → Continue below

Do you know the product, service, or contract type?
├─ YES → Scope grep to that directory: `grep -r "term" ~/forge/brain/products/<product>/ --include="*.md"`
└─ NO → Continue below

Are you searching for a concept or pattern (not exact phrase)?
├─ YES → Use `brain-recall` for semantic search (returns ranked, related decisions)
└─ NO → Continue below

Is the phrase common across multiple files (decision, contract, spec)?
├─ YES → Add --include filter: `grep -r "term" --include="*decision*.md"` OR `--include="*contract*.md"`
└─ NO → Use plain `grep -r "term" ~/forge/brain/products --include="*.md"`

Do you need to find decisions by metadata (status, owner, tag)?
├─ YES → Use grep pattern for YAML fields: `grep -r "^tags:.*auth" ~/forge/brain/products --include="*.md"`
└─ NO → Continue with phrase search

Are you searching across multiple products or years?
├─ YES → Expect slow grep (scope to decade first): `grep -r "term" ~/forge/brain/products/*/decisions/202[34]* --include="*.md"`
└─ NO → Scope to product/type and search

Result: Use the narrowest scope that includes your target. Always use --include="*.md" to avoid logs/temp files.
If grep is slow or ambiguous, escalate to brain-recall or brain-link.
```

---

## Cross-References

This skill works with other brain skills:

- **brain-write:** Decisions are recorded to the brain via `brain-write`. This skill reads what was written.
- **brain-recall:** Semantic search complement. Use `brain-read` for exact matches, `brain-recall` for conceptual search.
- **brain-why:** Traces provenance—who decided, when, and why. Use this after `brain-read` finds a decision.
- **brain-link:** Creates semantic edges between decisions. Shows decision dependencies found by `brain-read` grep patterns.
- **brain-forget:** Archives deprecated decisions. Use `brain-read` to find candidates for archival.
