# Grep Pattern Examples

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
products/payment/contracts/schema-db.md
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
