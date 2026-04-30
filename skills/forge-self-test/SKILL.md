---
name: forge-self-test
description: "WHEN: You need to validate the entire Forge pipeline works end-to-end on a real product. Run before declaring Forge production-ready or after major changes to skills/agents."
type: rigid
requires: [forge-intake-gate, forge-council-gate, forge-tdd, forge-eval-gate, forge-verification]
version: 1.0.0
preamble-tier: 3
triggers:
  - "test forge itself"
  - "forge self-check"
  - "validate forge setup"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Forge Self-Test (End-to-End Validation)

**HARD-GATE: Do NOT declare Forge production-ready without running this skill.**

---

## Anti-Pattern Preamble: Why Agents Skip Self-Test

| Rationalization | The Truth |
|---|---|
| "Individual skills work in isolation, the system must work end-to-end" | Integration is where systems fail. Individual skill correctness does not imply pipeline correctness. Run the full test. |
| "We've run partial tests, that's sufficient validation" | Partial tests only validate partial pipelines. The self-test is the only complete signal. Partial != sufficient. |
| "The seed product is synthetic, real products will differ" | The seed product is deliberately synthetic and adversarial. If Forge can't handle the seed, it can't handle real products. |
| "I just changed one skill, it shouldn't affect the pipeline" | Single-skill changes propagate through the pipeline via shared-dev-spec, contracts, and brain. Always revalidate end-to-end. |
| "Self-test takes too long, we'll trust incremental testing" | Incremental tests catch unit failures. Self-test catches integration, sequencing, and context failures. Both required. |
| "The seed product is old, it may not reflect current features" | Seed product is updated with Forge. It's the canonical test target. If it's stale, update it — don't skip the test. |
| "Output looks right from a spot check, I'll declare it working" | Spot checks miss 60% of pipeline failures (latent failures in downstream phases). Full self-test or BLOCKED. |
| "This is just a documentation change, no need to self-test" | Documentation errors in skills propagate to AI behavior. Self-test validates behavior, not just code. |

---

## Iron Law

```
FORGE IS NOT PRODUCTION-READY UNTIL SELF-TEST PASSES ALL 5 PHASES.
```

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Skipping phases** — If someone suggests running only phases 1-3 "because eval is slow", STOP. All 5 phases are required.
- **Using a non-canonical seed product** — If the test product is not the official ShopApp seed, STOP. Self-test must run on the canonical seed.
- **Claiming success from phase output alone** — If the claim is "phase X output looks right" without verifying acceptance criteria, STOP. Evidence required.
- **Bypassing brain persistence** — If brain decisions are not being written during the test run, STOP. Brain is part of the pipeline.
- **Accepting YELLOW eval verdict as pass** — If eval returns YELLOW, STOP. Self-test requires GREEN. YELLOW is a failure mode.
- **Running phases out of order** — If council is invoked before intake locks, STOP. Phases are strictly sequential.
- **Reusing brain state from a prior run** — If brain decisions from a previous self-test run are bleeding into the current run, STOP. Each run gets a fresh brain path.

---

## Introduction: Why Self-Test Matters

The self-test validates that Forge works end-to-end on a real product. Without it, individual skills may work in isolation, but the orchestration pipeline can fail catastrophically. The self-test:

1. **Validates all skills work in concert** — Proves that intake, council, build, eval, and brain operations don't conflict
2. **Pressure-tests against realistic scenarios** — Uses the seed product (ShopApp), a 4-repo e-commerce stack that exercises all Forge capabilities
3. **Detects regressions before plugin distribution** — Ensures no recent changes broke the pipeline
4. **Runs against canonical seed product** — Guarantees reproducible results and parity across all environments

**Self-test is not optional. It is the only complete validation signal.**

---

## Seed Product

**ShopApp** — A 4-repo e-commerce product used as the canonical self-test target.

| Repo | Role | Language | Key Files |
|---|---|---|---|
| `shared-schemas` | Protobuf definitions | Protobuf | `proto/products.proto`, `proto/orders.proto`, `proto/users.proto` |
| `backend-api` | REST API server | Node.js / Express | `src/api/favorites.js`, `src/db/migrations/`, `src/cache/` |
| `web-dashboard` | Admin dashboard | TypeScript / Next.js | `pages/favorites.tsx`, `components/FavoritesGrid.tsx` |
| `app-mobile` | Customer app | Kotlin / Android | `app/src/main/java/com/shopapp/favorites/`, `app/src/test/` |

**Location:** `seed-product/shopapp/` (relative to Forge root)

**PRD under test:** `seed/prds/01-favorites-cross-surface-sync.md`
— Cross-surface sync of user favorites (backend, web, mobile, shared schemas all touched).

---

## Test Data Setup (ShopApp Seed Product)

Before self-test begins, verify seed product is initialized with sample data.

### Database Schema (MySQL)

```sql
-- Users (100 records)
CREATE TABLE users (
  id INT PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  username VARCHAR(100),
  created_at TIMESTAMP,
  last_login TIMESTAMP
);

-- Products (50 records with variants)
CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(255),
  sku VARCHAR(100),
  price DECIMAL(10, 2),
  inventory INT,
  created_at TIMESTAMP
);

-- Favorites (user-product mappings)
CREATE TABLE favorites (
  id INT PRIMARY KEY,
  user_id INT,
  product_id INT,
  created_at TIMESTAMP,
  synced_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Orders (100 records at various stages)
CREATE TABLE orders (
  id INT PRIMARY KEY,
  user_id INT,
  total DECIMAL(10, 2),
  status ENUM('pending', 'paid', 'shipped', 'delivered'),
  created_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Inventory (variant stock levels)
CREATE TABLE inventory (
  product_id INT,
  size VARCHAR(10),
  color VARCHAR(50),
  quantity INT,
  warehouse VARCHAR(100),
  PRIMARY KEY (product_id, size, color, warehouse),
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### Sample Data Seed Script

```bash
# Location: seed-product/shopapp/scripts/seed-data.sh

# Load 100 test users
mysql shopapp < seed-product/shopapp/data/users-100.sql

# Load 50 products with variants
mysql shopapp < seed-product/shopapp/data/products-50.sql

# Load 100 orders at various stages
mysql shopapp < seed-product/shopapp/data/orders-100.sql

# Pre-populate cache with 10 hot products
redis-cli < seed-product/shopapp/data/cache-seeds.redis

# Initialize search index with product catalog
curl -X POST http://localhost:9200/_bulk \
  -H 'Content-Type: application/json' \
  -d @seed-product/shopapp/data/search-index.ndjson

# Verify all data loaded
mysql shopapp -e "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM products; SELECT COUNT(*) FROM orders;"
```

### Cache Entries (Redis)

```redis
# Hot products (cache key pattern: products:{id})
SET products:1 '{"id": 1, "name": "...", "price": 99.99}' EX 3600
SET products:2 '{"id": 2, "name": "...", "price": 49.99}' EX 3600
...

# User sessions (cache key pattern: session:{userId})
SET session:1 '{"userId": 1, "token": "...", "expires": 1234567890}' EX 86400
...

# Favorites (cache key pattern: favorites:{userId})
SET favorites:1 '[1, 5, 12, 34]' EX 3600
...
```

### Search Index (Elasticsearch)

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "index.queries.cache.enabled": true
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text", "analyzer": "standard" },
      "sku": { "type": "keyword" },
      "price": { "type": "float" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}
```

---

## Pre-Self-Test Checklist (15 Items)

Before running self-test, verify all prerequisites:

**Environment & Infrastructure:**
- [ ] Git working directory clean (`git status` shows no uncommitted changes)
- [ ] Seed product directory present (`seed-product/shopapp/` exists and is readable)
- [ ] Brain directory initialized (`brain/` exists, structure per `forge-brain-layout`)
- [ ] No stale processes running (`ps aux | grep -E 'node|python|java' | grep -v grep`)

**Forge Skills & Services:**
- [ ] Every directory under `skills/` has a `SKILL.md` (full catalog; or verify subset for partial test)
- [ ] All deployment drivers available (`deploy-driver-*` skills)
- [ ] All eval drivers available (`eval-driver-*` skills)
- [ ] All contract negotiators available (`contract-*` skills)

**External Services (test against seed product requirements):**
- [ ] MySQL running and accessible (`mysql -h localhost shopapp -e "SELECT 1"`)
- [ ] Redis running and accessible (`redis-cli PING` returns PONG)
- [ ] Elasticsearch running and accessible (`curl http://localhost:9200/_health`)
- [ ] Kafka running and accessible (`kafka-topics.sh --list --bootstrap-server localhost:9092`)
- [ ] Docker available (for docker-compose eval driver) (`docker version`)

**Configuration:**
- [ ] Environment variables set (SHOPAPP_DB_HOST, SHOPAPP_API_PORT, etc.)
- [ ] Git hooks configured (commit-msg, pre-commit in `.claude/hooks/`)

---

## Detailed Workflow

---

## Detailed Workflow

### Phase 0: Environment Setup

**HARD-GATE: Environment must be clean before starting.**

**Test Scenario:** Prepare a pristine environment for self-test with no contamination from prior runs.

**Test Flow:**
```bash
# 1. Verify seed product repos exist
ls seed-product/backend-api seed-product/web-dashboard seed-product/app-mobile seed-product/shared-schemas

# 2. Set up a clean brain path for this test run
export SELF_TEST_RUN_ID="SELF-TEST-$(date +%Y%m%d-%H%M%S)"
mkdir -p brain/self-test/${SELF_TEST_RUN_ID}
export SELF_TEST_BRAIN=brain/self-test/${SELF_TEST_RUN_ID}

# 3. Verify eval infrastructure is running
# (MySQL, Redis, Kafka, Elasticsearch — per seed/product.md)
mysql -h localhost shopapp -e "SELECT 1" || { echo "MySQL FAILED"; exit 1; }
redis-cli PING || { echo "Redis FAILED"; exit 1; }
curl -s http://localhost:9200/_health | jq '.status' || { echo "ES FAILED"; exit 1; }
kafka-topics.sh --list --bootstrap-server localhost:9092 > /dev/null || { echo "Kafka FAILED"; exit 1; }

# 4. Seed test data
mysql shopapp < seed-product/shopapp/scripts/seed-data.sql
redis-cli < seed-product/shopapp/scripts/seed-cache.redis

# 5. Verify seed data loaded
echo "Users: $(mysql shopapp -e 'SELECT COUNT(*) FROM users\G' | grep COUNT)"
echo "Products: $(mysql shopapp -e 'SELECT COUNT(*) FROM products\G' | grep COUNT)"
echo "Orders: $(mysql shopapp -e 'SELECT COUNT(*) FROM orders\G' | grep COUNT)"
```

**Assertions:**
- ✅ All 4 seed repos exist and are readable
- ✅ Brain directory created (clean state, no prior run contamination)
- ✅ All 4 infrastructure services online (MySQL, Redis, Elasticsearch, Kafka)
- ✅ Sample data loaded (100 users, 50 products, 100 orders)
- ✅ Cache and search indices pre-populated

**Expected Output:**
```
Environment Status
===================
Seed Repos:    ✅ 4/4 accessible
Brain Path:    ✅ brain/self-test/SELF-TEST-{timestamp} (clean)
MySQL:         ✅ Online (100 users, 50 products, 100 orders)
Redis:         ✅ Online (cache seeds loaded)
Elasticsearch: ✅ Online (search index initialized)
Kafka:         ✅ Online (topics ready)

Ready to proceed to Phase 1.
```

**Duration:** 2-3 minutes (includes data seeding)

---

### Phase 1: Intake

**HARD-GATE: PRD must be locked before proceeding to Phase 2.**

**Test Scenario:** Receive and lock the ShopApp favorites feature PRD, ensuring all ambiguities are resolved before council negotiation.

**Test Flow:**
```
1. Invoke: /forge-intake-gate 
   Input: seed/prds/01-favorites-cross-surface-sync.md

2. Invoke: /intake-interrogate
   Complete intake (`intake-interrogate`): mandatory **prd-locked.md** fields, confidence-first (no TBD):
   ├─ Q1: Core user problem
   │  Expected: "Allow users to save favorite products and sync across web/mobile"
   ├─ Q2: Affected surfaces
   │  Expected: backend-api, web-dashboard, app-mobile, shared-schemas (all 4)
   ├─ Q3: Contract changes
   │  Expected: API v2 endpoint, DB favorites table, Redis cache key, Kafka topic
   ├─ Q4: Acceptance criteria
   │  Expected: Favorites appear in <500ms, no data loss, 99.9% sync success
   ├─ Q5: Anti-goals
   │  Expected: No changes to auth, no breaking API changes
   ├─ Q6: 3-month success
   │  Expected: 10K active users, <1% sync failure rate
   ├─ Q7: Hard constraints
   │  Expected: Backwards compatible, no schema breaks, mobile-offline capable
   └─ Q8: Assumptions
      Expected: Users have both web + mobile accounts, <100K concurrent users

3. Invoke: brain-write
   Record: PRD locked with decision ID PRDLK-SELF-TEST-{timestamp}
   Include: All 8 answers, surface list, contract list

4. Verify: PRD context locked in brain
   Check: PRDLK-SELF-TEST-{timestamp} exists, status=LOCKED
```

**Assertions:**
- ✅ PRD locked (decision ID recorded in brain at brain/self-test/{SELF_TEST_RUN_ID}/PRDLK-*)
- ✅ All mandatory intake lock fields satisfied (no "TBD" or "TK")
- ✅ All 4 surfaces enumerated (backend-api, web-dashboard, app-mobile, shared-schemas)
- ✅ 5 contracts identified (API, DB, Cache, Events, Search)
- ✅ Acceptance criteria quantified (not vague)
- ✅ Council context ready for Phase 2

**Expected Output:**
```
Phase 1: Intake ✅
====================
PRD Locked:        PRDLK-SELF-TEST-{timestamp}
Surfaces:          4/4 (backend-api, web-dashboard, app-mobile, shared-schemas)
Contracts:         5 (api-rest, schema-db, cache-redis, event-bus, search-es)
Questions:         8/8 answered

Acceptance Criteria:
├─ Sync latency: <500ms (99th percentile)
├─ Sync success: 99.9% (0.1% loss acceptable for cross-region)
├─ API version: v2 (backwards compatible with v1)
├─ Offline: Mobile can queue favorites, sync on reconnect
└─ Data integrity: No duplicates, all deletes respected

Decision ID:       PRDLK-SELF-TEST-{timestamp}
Status:            LOCKED ✅ Ready for Council

Duration: 5-10 minutes
```

**Failure Modes & Recovery:**
- If any question answered "TBD": ask clarifying questions via dreamer, re-answer
- If surfaces missing: intake-interrogate will require explicit confirmation of all 4
- If PRD doesn't lock: check brain-write skill, verify SELF_TEST_BRAIN env var set

---

### Phase 2: Council

**HARD-GATE: Shared-dev-spec must be locked before Phase 3.**

**Test Scenario:** Multi-surface council negotiates contracts for cross-surface favorites sync, resolving conflicts between backend, web, app, and infra surface needs.

**Test Flow:**
```
1. Invoke: /forge-council-gate
   Input: PRD locked from Phase 1 (PRDLK-SELF-TEST-*)

2. Invoke: /council-multi-repo-negotiate
   
   Backend Surface (reasoning-as-backend):
   ├─ Proposes: POST /api/v2/favorites (create), GET /api/v2/favorites (list)
   ├─ Strategy: Optimistic locking with version field
   ├─ Constraints: API must be backwards compatible with v1
   └─ Signals conflict? Wants push-based sync (backend initiates)
   
   Web Surface (reasoning-as-web-frontend):
   ├─ Proposes: Pagination (50 items/page), infinite scroll UI
   ├─ Constraints: Cache pagination state in Redis
   └─ Signals conflict? Prefers pull-based (web queries on demand)
   
   App Surface (reasoning-as-app-frontend):
   ├─ Proposes: Offline SQLite store, sync-on-reconnect
   ├─ Constraints: Queues writes when offline, replays on restore
   └─ Signals conflict? Needs pull-based for offline resilience
   
   Infra Surface (reasoning-as-infra):
   ├─ Proposes: Redis pub/sub for real-time cross-surface invalidation
   ├─ Alternative: Kafka topic `user.favorites.changed` for durability
   └─ Consensus: Kafka for durability + Redis for latency

3. Negotiate 5 Contracts:

   Contract 1 — REST API (contract-api-rest):
   ├─ POST /api/v2/favorites
   │  Request: { userId, productId, tags? }
   │  Response: { id, userId, productId, createdAt, syncedAt }
   │  Error: 409 if duplicate, 400 if invalid
   ├─ GET /api/v2/favorites?userId=X&page=1
   │  Response: { items: [...], page, totalPages, hasMore }
   └─ DELETE /api/v2/favorites/{id}

   Contract 2 — Database Schema (contract-schema-db):
   ├─ favorites table:
   │  - id (INT PK)
   │  - user_id (INT FK users.id)
   │  - product_id (INT FK products.id)
   │  - created_at (TIMESTAMP)
   │  - synced_at (TIMESTAMP)
   │  - version (INT, for optimistic locking)
   └─ Index: (user_id, created_at DESC)

   Contract 3 — Cache (contract-cache):
   ├─ Key pattern: favorites:{userId}
   ├─ Value: JSON array of product IDs
   ├─ TTL: 1 hour
   └─ Invalidation: On write (POST/DELETE), invalidate immediately

   Contract 4 — Event Bus (contract-event-bus):
   ├─ Topic: user.favorites.changed
   ├─ Payload schema:
   │  {
   │    userId: string,
   │    action: "add" | "remove",
   │    productId: number,
   │    timestamp: ISO8601
   │  }
   ├─ Retention: 7 days
   └─ Partition: By userId (ensures ordering per user)

   Contract 5 — Search (contract-search):
   └─ No changes (favorites not full-text searchable)

4. Conflict Resolution (if any):
   If backend (push) vs. web/app (pull) deadlock:
   ├─ Invoke: dream-resolve-inline
   ├─ Dreamer decides: Hybrid (backend pushes via Kafka, surfaces pull cache)
   └─ Record decision in brain: DREAMER-SYNC-STRATEGY-{timestamp}

5. Invoke: /spec-freeze
   Locks: shared-dev-spec with all 5 contracts

6. Invoke: brain-write
   Record: SPECLOCK-SELF-TEST-{timestamp}
   Include: All contracts, conflict resolutions, surface approvals
```

**Assertions:**
- ✅ All 4 surfaces attended (backend, web, app, infra responses recorded)
- ✅ All 5 contracts negotiated (no "TBD" values in spec)
- ✅ Shared-dev-spec frozen (decision ID: SPECLOCK-SELF-TEST-*)
- ✅ Conflicts resolved or escalated to dreamer with rationale
- ✅ Each surface approved final spec (or dreamer override recorded)

**Expected Output:**
```
Phase 2: Council ✅
====================
Surfaces:          4/4 (backend, web, app, infra)
├─ Backend:   ✅ API design approved
├─ Web:       ✅ Pagination approved
├─ App:       ✅ Offline strategy approved
└─ Infra:     ✅ Event bus + cache approved

Contracts:         5/5 frozen
├─ REST API:      POST/GET/DELETE /api/v2/favorites
├─ DB Schema:     favorites table (userId, productId, createdAt, syncedAt, version)
├─ Cache:         favorites:{userId}, 1h TTL, invalidate-on-write
├─ Events:        user.favorites.changed Kafka topic (7-day retention)
└─ Search:        No changes

Conflicts:         1 (RESOLVED)
├─ Issue:         Push vs. Pull sync strategy
├─ Decision:      Hybrid (push via Kafka, pull for offline)
└─ Decision ID:   DREAMER-SYNC-STRATEGY-{timestamp}

Spec Locked:       SPECLOCK-SELF-TEST-{timestamp}
Status:            FROZEN ✅ Ready for Build

Duration: 15-20 minutes
```

**Failure Modes & Recovery:**
- If surfaces disagree: invoke dream-resolve-inline inline (dreamer mediates)
- If contract negotiation stalls: check that all 4 surface reasoning skills completed
- If spec won't freeze: verify all 5 contract IDs recorded in brain

---

### Phase 3: Tech Plans + Build

**HARD-GATE: Each repo must have a tech plan before dev-implementer is dispatched. TDD enforced.**

**Test Scenario:** Convert locked shared-dev-spec into per-project tech plans, then build in isolated worktrees with strict TDD discipline (RED → GREEN → REFACTOR).

**Test Flow:**

```
1. Invoke: /tech-plan-write-per-project
   Input: shared-dev-spec locked from Phase 2 (SPECLOCK-SELF-TEST-*)

   Task 1 — shared-schemas:
   ├─ Description: Add Protobuf definition for favorites
   ├─ Changes:
   │  ├─ New file: proto/favorites.proto
   │  │  message Favorite {
   │  │    int32 user_id = 1;
   │  │    int32 product_id = 2;
   │  │    string created_at = 3;
   │  │    string synced_at = 4;
   │  │    int32 version = 5;
   │  │  }
   │  └─ Generate protoc bindings for Node.js, Kotlin, TypeScript
   └─ Tests:
      ├─ Protobuf compiles without errors
      └─ Generated bindings include all fields with correct types

   Task 2 — backend-api:
   ├─ Description: Implement REST API v2 for favorites + cache + events
   ├─ Changes:
   │  ├─ New file: src/api/v2/favorites.js (routes)
   │  │  - POST /api/v2/favorites (create)
   │  │  - GET /api/v2/favorites (list with pagination)
   │  │  - DELETE /api/v2/favorites/{id} (delete)
   │  ├─ New file: src/db/migrations/001-create-favorites-table.sql
   │  ├─ New file: src/cache/favorites-cache.js (Redis operations)
   │  ├─ New file: src/events/favorites-events.js (Kafka producer)
   │  └─ Integration with existing auth middleware
   └─ Tests:
      ├─ Unit: Each route handler (8+ tests)
      ├─ Integration: Full request → DB → Cache → Event flow (5+ tests)
      └─ Edge cases: Duplicates, missing auth, invalid product IDs (4+ tests)

   Task 3 — web-dashboard:
   ├─ Description: Add UI for favorites with pagination
   ├─ Changes:
   │  ├─ New file: pages/favorites.tsx (main page)
   │  ├─ New file: components/FavoritesGrid.tsx (grid component)
   │  ├─ New file: hooks/useFavorites.ts (React hook for API + cache)
   │  ├─ Styling: Tailwind CSS classes
   │  └─ Query: pages=limit of 50, infinite scroll
   └─ Tests:
      ├─ Unit: useFavorites hook (3+ tests)
      ├─ Component: FavoritesGrid renders items, handles pagination (4+ tests)
      └─ Integration: Page loads, fetches data, displays (2+ tests)

   Task 4 — app-mobile:
   ├─ Description: Add offline favorites store + sync-on-reconnect
   ├─ Changes:
   │  ├─ New file: app/src/main/java/com/shopapp/favorites/FavoritesActivity.kt
   │  ├─ New file: app/src/main/java/com/shopapp/favorites/FavoritesRepository.kt
   │  │  ├─ SQLite for offline store
   │  │  ├─ Retrofit API client
   │  │  └─ Sync-on-reconnect logic
   │  ├─ New file: app/src/main/assets/favorites.sql (schema)
   │  └─ Integration: NetworkStateMonitor triggers sync
   └─ Tests:
      ├─ Unit: FavoritesRepository (offline queuing, sync) (6+ tests)
      ├─ Integration: Activity lifecycle, network changes (3+ tests)
      └─ Edge cases: Network loss mid-sync, duplicate syncs (2+ tests)

2. Invoke: /tech-plan-self-review
   Validate each plan:
   ├─ Correctness: Does it satisfy spec?
   ├─ Feasibility: Can it be done in one sprint?
   ├─ Testability: Are tests clear and specific?
   └─ All 4 plans approved (or iterate with AI)

3. Dispatch: worktree-per-project-per-task
   
   For each of 4 repos:
   ├─ Create isolated worktree (1 per task)
   ├─ Dispatch: dev-implementer {task}
   │
   │  Dev-Implementer Workflow (TDD):
   │  ├─ Step 1 (RED): Write test first (must fail)
   │  │  └─ Verify test fails with expected error
   │  ├─ Step 2 (GREEN): Implement minimal code to pass test
   │  │  └─ Verify test passes
   │  ├─ Step 3 (REFACTOR): Clean up code, extract utilities
   │  │  └─ Verify all tests still pass
   │  ├─ Step 4 (COMMIT): Commit with message "feat: {description}"
   │  │  └─ Verify commit includes test + implementation
   │  └─ Repeat for next test
   │
   └─ Report: DONE or DONE_WITH_CONCERNS

   Worktree 1 — shared-schemas (5 minutes):
   ├─ Test: Protobuf compiles
   ├─ Implementation: proto/favorites.proto + codegen
   └─ Commit: "feat(proto): add Favorite message and bindings"

   Worktree 2 — backend-api (45 minutes, 12 tasks):
   ├─ Task 2a: POST /api/v2/favorites creates favorite + cache hit
   ├─ Task 2b: POST /api/v2/favorites rejects duplicates (409)
   ├─ Task 2c: GET /api/v2/favorites returns paginated list (50/page)
   ├─ Task 2d: GET /api/v2/favorites returns from cache if available
   ├─ Task 2e: DELETE /api/v2/favorites/{id} deletes + invalidates cache
   ├─ Task 2f: Events published to Kafka on create/delete
   ├─ Task 2g: Favorites synced_at updated on successful write
   ├─ Task 2h: Optimistic locking rejects stale writes (version mismatch)
   ├─ Task 2i: API auth required (403 if missing token)
   ├─ Task 2j: Invalid product IDs rejected (400)
   ├─ Task 2k: DB migration runs cleanly on first deploy
   └─ Task 2l: Rollback migration reverts schema cleanly

   Worktree 3 — web-dashboard (30 minutes):
   ├─ Test: useFavorites hook fetches from API
   ├─ Test: FavoritesGrid renders 50 items per page
   ├─ Test: Pagination UI shows correct page count
   ├─ Test: Infinite scroll loads next page on scroll
   ├─ Test: Favorites page integrates with navigation
   └─ Report: DONE (no concerns)

   Worktree 4 — app-mobile (40 minutes):
   ├─ Test: SQLite schema creates favorites table
   ├─ Test: FavoritesRepository inserts offline
   ├─ Test: Sync queues offline inserts and posts to API
   ├─ Test: Network loss pauses sync
   ├─ Test: Network restore resumes sync
   ├─ Test: Activity displays local favorites while syncing
   └─ Report: DONE (minor concern: sync ordering on network flaps)

4. Verify All Tasks Completed:
   ├─ Total tasks: 4 repos, ~24 tasks
   ├─ All tasks: DONE or DONE_WITH_CONCERNS
   ├─ No BLOCKED tasks
   └─ No NEEDS_CONTEXT remaining
```

**Assertions:**
- ✅ Tech plans written for all 4 repos
- ✅ All tech plans reviewed and approved
- ✅ All tasks dispatched in isolated worktrees
- ✅ All tasks report DONE (or concerns documented)
- ✅ TDD cycle verifiable: test commit before implementation commit (check git log)
- ✅ All tests passing (no failing tests in final state)

**Expected Output:**
```
Phase 3: Build ✅
=================
Tech Plans:        4/4 written and reviewed
├─ shared-schemas  ✅
├─ backend-api     ✅
├─ web-dashboard   ✅
└─ app-mobile      ✅

Build Tasks:       24 (4 repos)
├─ Completed:      23 DONE + 1 DONE_WITH_CONCERNS
├─ BLOCKED:        0
└─ NEEDS_CONTEXT:  0

TDD Discipline:    ✅ Enforced
├─ RED steps:      All test commits precede implementation
├─ GREEN steps:    All tests passing
└─ REFACTOR:       Code cleaned, no regressions

Worktrees:         4 created, 4 completed, 0 abandoned
Git Commits:       24 (1 per task, all TDD-verified)

Concerns Logged:
├─ app-mobile: Sync ordering fragile if network flaps >2x
└─ Action: Add test for multi-flap scenario, improve state machine

Duration: 30-45 minutes

Ready for Phase 4 (Eval)
```

**Failure Modes & Recovery:**
- If TDD not enforced: dev-implementer will reject (test commit required before impl)
- If test fails: review test expectations vs. spec, rewrite test if spec misunderstood
- If task BLOCKED: diagnose blocker (missing dependency? spec ambiguity?), resolve, retry
- If worktree corrupted: remove worktree, create fresh, retry task

---

### Phase 4: Review + Eval

**HARD-GATE: Eval must return GREEN before Phase 5. YELLOW = FAIL.**

**Test Scenario:** Code review validates spec compliance and quality, then end-to-end eval tests the entire stack through 6+ drivers covering API, DB, Cache, Events, Web UI, and Mobile UI.

**Test Flow:**

```
1. Invoke: forge-trust-code (spec-reviewer)
   Per repo (shared-schemas, backend-api, web-dashboard, app-mobile):
   
   Task 1a — Spec Review (shared-schemas):
   ├─ Read: proto/favorites.proto
   ├─ Check spec:
   │  ├─ ✓ Favorite message has user_id, product_id, timestamps, version
   │  ├─ ✓ Protoc compiles to Node.js, Kotlin, TypeScript bindings
   │  └─ ✓ Generated code includes all fields with correct types
   └─ Verdict: PASS

   Task 1b — Spec Review (backend-api):
   ├─ Read: src/api/v2/favorites.js
   ├─ Check spec:
   │  ├─ ✓ POST /api/v2/favorites accepts {userId, productId, tags?}
   │  ├─ ✓ Returns {id, userId, productId, createdAt, syncedAt} with 201
   │  ├─ ✓ GET /api/v2/favorites?userId=X&page=1 returns paginated {items, page, totalPages}
   │  ├─ ✓ DELETE /api/v2/favorites/{id} removes and returns 204
   │  ├─ ✓ POST rejects duplicates with 409
   │  └─ ✓ Requires auth, returns 403 if missing
   ├─ Read: src/db/migrations/001-create-favorites-table.sql
   ├─ Check schema:
   │  ├─ ✓ favorites table has all required columns (user_id, product_id, version, timestamps)
   │  ├─ ✓ Indexes present (user_id, created_at)
   │  └─ ✓ Foreign keys enforce referential integrity
   ├─ Read: src/cache/favorites-cache.js
   ├─ Check cache contract:
   │  ├─ ✓ Key pattern: favorites:{userId}
   │  ├─ ✓ TTL: 1 hour
   │  └─ ✓ Invalidated on POST/DELETE
   ├─ Read: src/events/favorites-events.js
   ├─ Check events contract:
   │  ├─ ✓ Publishes to user.favorites.changed topic
   │  ├─ ✓ Payload includes userId, action, productId, timestamp
   │  └─ ✓ Partitioned by userId
   └─ Verdict: PASS

   Task 1c — Spec Review (web-dashboard):
   ├─ Read: pages/favorites.tsx
   ├─ Check spec:
   │  ├─ ✓ Calls GET /api/v2/favorites with pagination
   │  ├─ ✓ Displays 50 items per page (spec limit)
   │  ├─ ✓ Shows pagination controls (page, totalPages)
   │  └─ ✓ Supports infinite scroll
   ├─ Read: components/FavoritesGrid.tsx
   ├─ Check implementation:
   │  ├─ ✓ Renders items in grid layout
   │  ├─ ✓ Handles loading state
   │  └─ ✓ Handles error state
   └─ Verdict: PASS

   Task 1d — Spec Review (app-mobile):
   ├─ Read: app/src/main/java/com/shopapp/favorites/FavoritesRepository.kt
   ├─ Check spec:
   │  ├─ ✓ Stores favorites in SQLite offline
   │  ├─ ✓ Syncs to API on network restore
   │  ├─ ✓ Queues writes while offline
   │  └─ ✓ Respects optimistic locking (version check)
   ├─ Read: app/src/main/java/com/shopapp/favorites/FavoritesActivity.kt
   ├─ Check UI:
   │  ├─ ✓ Displays local favorites immediately
   │  ├─ ✓ Shows sync status (syncing, synced, offline)
   │  └─ ✓ Handles network changes gracefully
   └─ Verdict: PASS

2. Invoke: code-quality-reviewer
   11-point quality framework per repo:
   
   ├─ 1. Tests: All public functions covered (unit + integration)
   ├─ 2. Error handling: All error paths tested
   ├─ 3. Edge cases: Null checks, boundary conditions tested
   ├─ 4. Code clarity: No cryptic variable names, logic clear
   ├─ 5. DRY principle: No duplicated code blocks
   ├─ 6. Naming: Functions/variables have clear, descriptive names
   ├─ 7. Documentation: Comments on complex logic, JSDoc/docstrings
   ├─ 8. Performance: No O(n²) loops, queries indexed
   ├─ 9. Security: No SQL injection, proper auth checks, input validation
   ├─ 10. Consistency: Code style matches repo conventions
   └─ 11. Dependencies: No unnecessary dependencies, versions pinned
   
   All 4 repos score PASS (no critical issues)

3. If any FAIL: Dispatch dev-implementer to fix, re-review

4. Invoke: /eval-product-stack-up
   Bring up entire ShopApp stack:
   ├─ Start MySQL: `docker-compose up -d mysql`
   ├─ Start Redis: `docker-compose up -d redis`
   ├─ Start Kafka: `docker-compose up -d kafka`
   ├─ Start Elasticsearch: `docker-compose up -d elasticsearch`
   ├─ Seed data: Load 100 users, 50 products, 100 orders
   ├─ Run migrations: Apply all DB migrations
   ├─ Start API server: `node backend-api/src/server.js`
   ├─ Start web dashboard: `npm run dev` (Next.js)
   ├─ Verify all services online
   └─ Log startup summary

5. Invoke: qa-semantic-csv-orchestrate (or `run_semantic_csv_eval.py` per docs/semantic-eval-csv.md)
   Run scenarios across 6 drivers:

   Driver 1 — API HTTP (eval-driver-api-http):
   ├─ Scenario 1: POST /api/v2/favorites
   │  ├─ Request: {userId: 1, productId: 5}
   │  ├─ Expected: 201 Created, response includes id + createdAt
   │  └─ Assert: ✅ 201, body has all required fields
   ├─ Scenario 2: POST duplicate
   │  ├─ Request: Same {userId: 1, productId: 5} again
   │  ├─ Expected: 409 Conflict
   │  └─ Assert: ✅ 409
   ├─ Scenario 3: GET /api/v2/favorites?userId=1&page=1
   │  ├─ Expected: 200 OK, items array, page=1, totalPages=N
   │  └─ Assert: ✅ 200, pagination metadata present
   ├─ Scenario 4: DELETE /api/v2/favorites/{id}
   │  ├─ Expected: 204 No Content
   │  └─ Assert: ✅ 204
   ├─ Scenario 5: GET after DELETE
   │  ├─ Expected: Item no longer in list
   │  └─ Assert: ✅ Item removed from GET results
   └─ Result: PASS (5/5 scenarios)

   Driver 2 — Database MySQL (eval-driver-db-mysql):
   ├─ Scenario 1: INSERT via API propagates to DB
   │  ├─ Action: POST /api/v2/favorites {userId: 2, productId: 10}
   │  ├─ Query: SELECT * FROM favorites WHERE user_id=2 AND product_id=10
   │  ├─ Expected: 1 row with createdAt, syncedAt, version=1
   │  └─ Assert: ✅ Row exists with correct values
   ├─ Scenario 2: version field increments on update
   │  ├─ Action: Update syncedAt timestamp
   │  ├─ Query: SELECT version FROM favorites WHERE id=X
   │  ├─ Expected: version=2 (incremented)
   │  └─ Assert: ✅ version incremented
   ├─ Scenario 3: Foreign key constraint enforced
   │  ├─ Action: Try INSERT with invalid user_id (99999)
   │  ├─ Expected: FK error (constraint violation)
   │  └─ Assert: ✅ FK error, row not inserted
   ├─ Scenario 4: Index scan efficient
   │  ├─ Action: EXPLAIN SELECT * FROM favorites WHERE user_id=1
   │  ├─ Expected: Index on user_id used
   │  └─ Assert: ✅ Index scan (no full table scan)
   └─ Result: PASS (4/4 scenarios)

   Driver 3 — Cache Redis (eval-driver-cache-redis):
   ├─ Scenario 1: Cache populated after API call
   │  ├─ Action: GET /api/v2/favorites?userId=3 (first time)
   │  ├─ Command: KEYS favorites:3*
   │  ├─ Expected: Key exists with TTL ~3600s
   │  └─ Assert: ✅ Key present, TTL correct
   ├─ Scenario 2: Second request hits cache
   │  ├─ Action: GET /api/v2/favorites?userId=3 (second call)
   │  ├─ Expected: Response time <50ms (cache hit)
   │  └─ Assert: ✅ <50ms latency (vs. ~200ms DB query)
   ├─ Scenario 3: Cache invalidated on write
   │  ├─ Action: POST /api/v2/favorites {userId: 3, productId: X}
   │  ├─ Command: EXISTS favorites:3
   │  ├─ Expected: Key deleted (TTL expired immediately)
   │  └─ Assert: ✅ Key gone
   ├─ Scenario 4: Stale cache doesn't serve
   │  ├─ Action: Wait TTL expiry, then GET /api/v2/favorites?userId=3
   │  ├─ Expected: Cache miss, fresh DB query
   │  └─ Assert: ✅ Fresh data fetched (not stale)
   └─ Result: PASS (4/4 scenarios)

   Driver 4 — Event Bus Kafka (eval-driver-bus-kafka):
   ├─ Scenario 1: Event published on POST
   │  ├─ Action: POST /api/v2/favorites {userId: 4, productId: 15}
   │  ├─ Listen: user.favorites.changed topic
   │  ├─ Expected: Message with action='add', userId=4, productId=15
   │  └─ Assert: ✅ Message received with correct payload
   ├─ Scenario 2: Event published on DELETE
   │  ├─ Action: DELETE /api/v2/favorites/{id}
   │  ├─ Listen: user.favorites.changed topic
   │  ├─ Expected: Message with action='remove'
   │  └─ Assert: ✅ Message received with action='remove'
   ├─ Scenario 3: Partition by userId (ordering)
   │  ├─ Action: POST 5 favorites for userId=5
   │  ├─ Listen: All 5 messages on same topic
   │  ├─ Expected: Messages in order (add 1, add 2, add 3, add 4, add 5)
   │  └─ Assert: ✅ All 5 messages in order
   └─ Result: PASS (3/3 scenarios)

   Driver 5 — Web UI Chrome DevTools (eval-driver-web-cdp):
   ├─ Scenario 1: Favorites page loads
   │  ├─ Action: Navigate to /favorites
   │  ├─ Expected: Page renders, no JS errors
   │  └─ Assert: ✅ Page loaded, console clean
   ├─ Scenario 2: API call made
   │  ├─ Monitor: Network tab
   │  ├─ Expected: GET /api/v2/favorites request
   │  └─ Assert: ✅ API request successful (200)
   ├─ Scenario 3: Favorites grid displays
   │  ├─ Action: Wait for data load
   │  ├─ Query: .favorite-item elements in DOM
   │  ├─ Expected: 50 items visible
   │  └─ Assert: ✅ 50+ items rendered
   ├─ Scenario 4: Pagination controls visible
   │  ├─ Query: .pagination-controls in DOM
   │  ├─ Expected: "Page 1 of N" text visible
   │  └─ Assert: ✅ Pagination UI present
   ├─ Scenario 5: Infinite scroll loads more
   │  ├─ Action: Scroll to bottom
   │  ├─ Expected: Second page loads (request made)
   │  └─ Assert: ✅ New items loaded via scroll
   └─ Result: PASS (5/5 scenarios)

   Driver 6 — Mobile UI Android ADB (eval-driver-android-adb):
   ├─ Scenario 1: App launches
   │  ├─ Action: adb shell am start com.shopapp/.FavoritesActivity
   │  ├─ Expected: Activity starts, no crashes
   │  └─ Assert: ✅ Activity running
   ├─ Scenario 2: Local favorites loaded
   │  ├─ Query: SQLite favorites table
   │  ├─ Expected: Pre-populated with test data
   │  └─ Assert: ✅ SQLite contains favorites
   ├─ Scenario 3: UI displays local favorites
   │  ├─ Action: Inspect view hierarchy
   │  ├─ Query: RecyclerView items
   │  ├─ Expected: 10+ favorite items rendered
   │  └─ Assert: ✅ RecyclerView populated
   ├─ Scenario 4: Sync button present
   │  ├─ Query: Button with "sync" text
   │  ├─ Expected: Button exists
   │  └─ Assert: ✅ Sync button visible
   └─ Result: PASS (4/4 scenarios)

6. Invoke: /eval-judge
   Evaluate all results:
   
   Summary:
   ├─ API driver:     PASS (5/5 scenarios)
   ├─ DB driver:      PASS (4/4 scenarios)
   ├─ Cache driver:   PASS (4/4 scenarios)
   ├─ Events driver:  PASS (3/3 scenarios)
   ├─ Web driver:     PASS (5/5 scenarios)
   └─ Mobile driver:  PASS (4/4 scenarios)
   
   Verdict: 🟢 GREEN (25/25 scenarios passed, 0 failures)
```

**Assertions:**
- ✅ spec-reviewer: PASS for all 4 repos
- ✅ code-quality-reviewer: PASS for all 4 repos
- ✅ All 6 eval drivers completed (no skipped drivers)
- ✅ All scenarios passed (no failures)
- ✅ eval-judge: GREEN verdict (not YELLOW or RED)

**Expected Output:**
```
Phase 4: Review + Eval ✅
========================
Code Review Results:
├─ spec-reviewer:           ✅ PASS (4/4 repos)
├─ code-quality-reviewer:   ✅ PASS (4/4 repos)
└─ Issues found:            0 (no rework needed)

Stack Status:
├─ MySQL:         ✅ Running, migrations applied
├─ Redis:         ✅ Running
├─ Kafka:         ✅ Running, topics created
├─ Elasticsearch: ✅ Running
├─ API server:    ✅ Running, healthy
├─ Web dashboard: ✅ Running, no JS errors
└─ Mobile app:    ✅ Running, no crashes

Eval Results (6 drivers, 25 scenarios):
├─ API HTTP:      ✅ PASS (5/5)
├─ Database:      ✅ PASS (4/4)
├─ Cache:         ✅ PASS (4/4)
├─ Events:        ✅ PASS (3/3)
├─ Web UI:        ✅ PASS (5/5)
└─ Mobile UI:     ✅ PASS (4/4)

Verdict: 🟢 GREEN
├─ All critical scenarios: PASS
├─ All drivers operational
├─ No blocking issues
└─ Ready for Phase 5 (Ship)

Duration: 20-30 minutes
```

**Failure Modes & Recovery:**
- If code review FAIL: dev-implementer fixes, re-review (don't proceed)
- If eval returns YELLOW: diagnose non-critical failures, document, fix or document as known limitation
- If any driver fails: use self-heal-systematic-debug to diagnose, fix service, re-run driver
- If stack won't start: check infrastructure logs, restart missing service, re-run stack-up

---

### Phase 5: Ship + Retrospective

**HARD-GATE: All PRs must be coordinated and merged in dependency order. No cherry-picking.**

**Test Scenario:** Raise coordinated PRs in dependency order, merge with enforced sequencing, run retrospective, and record patterns for future products.

**Test Flow:**
```
1. Invoke: /pr-set-coordinate
   Raise PRs in dependency order:
   
   PR 1 — shared-schemas (no dependencies)
   ├─ Title: "feat: add Favorite protobuf message"
   ├─ Changes: proto/favorites.proto
   ├─ Status: OPEN
   └─ Depends-on: (none)
   
   PR 2 — backend-api (depends on shared-schemas)
   ├─ Title: "feat(api): add /api/v2/favorites REST endpoints"
   ├─ Changes: src/api/v2/favorites.js, migrations, cache, events
   ├─ Status: OPEN
   └─ Depends-on: shared-schemas PR#123
   
   PR 3 — web-dashboard (depends on backend-api)
   ├─ Title: "feat(ui): add favorites page with pagination"
   ├─ Changes: pages/favorites.tsx, components/FavoritesGrid.tsx, hooks/useFavorites.ts
   ├─ Status: OPEN
   └─ Depends-on: backend-api PR#124
   
   PR 4 — app-mobile (depends on backend-api)
   ├─ Title: "feat(app): add offline favorites with sync-on-reconnect"
   ├─ Changes: src/main/java/com/shopapp/favorites/*, SQLite schema
   ├─ Status: OPEN
   └─ Depends-on: backend-api PR#124

2. Invoke: /pr-set-merge-order
   Enforce merge sequence:
   ├─ Step 1: Approve & merge PR#123 (shared-schemas) ✅
   ├─ Step 2: Approve & merge PR#124 (backend-api) ✅
   ├─ Step 3: Approve & merge PR#125 (web-dashboard) ✅
   └─ Step 4: Approve & merge PR#126 (app-mobile) ✅
   
   Verify:
   ├─ Each PR merged only after dependencies merged
   ├─ No parallel merges (sequential only)
   └─ All 4 PRs in master branch

3. Invoke: /dream-retrospect-post-pr
   Retrospective phase:
   
   Score Decisions (1-5 scale):
   ├─ Correctness: Does the feature work as specified? (5/5 ✓)
   │  └─ All scenarios pass, no bugs found in eval
   ├─ Robustness: How well does it handle edge cases? (4/5)
   │  └─ Handles offline sync well, minor concern on network flaps
   ├─ Efficiency: Does it scale? Performance acceptable? (5/5 ✓)
   │  └─ Cache hits <50ms, pagination efficient, no N+1 queries
   ├─ Reversibility: Can we roll back safely? (5/5 ✓)
   │  └─ Migration reversible, no data loss on rollback
   └─ Confidence: How confident are we in this feature? (5/5 ✓)
   
   Extract Patterns:
   ├─ Pattern 1: "Cross-surface event invalidation"
   │  └─ When one surface modifies shared state (favorites), publish event on bus,
   │     other surfaces subscribe and invalidate local caches
   ├─ Pattern 2: "Offline-first mobile with server sync"
   │  └─ Store locally first (SQLite), queue operations, sync on network restore,
   │     handle conflicts with version field + optimistic locking
   ├─ Pattern 3: "Pagination with cache-aware infinite scroll"
   │  └─ Cache full result set per user/page combo, invalidate on write, lazy-load
   │     next page only when requested
   └─ Pattern 4: "Protobuf as contract layer"
      └─ Use Protobuf definitions as single source of truth for shared schemas,
         generate bindings for all languages, ensures type safety cross-repo
   
   Record Gotchas:
   ├─ Gotcha 1: "Duplicate favorites race condition"
   │  └─ Two simultaneous API calls can both think the favorite doesn't exist,
   │     both insert, causing constraint violation. Fix: Unique constraint + 409
   │     handling, or use optimistic locking with SELECT-for-update
   ├─ Gotcha 2: "Cache invalidation timing"
   │  └─ If event-driven invalidation fails, stale cache serves old data.
   │     Fix: TTL-based expiry as safety net, event-based invalidation as optimization
   └─ Gotcha 3: "Mobile sync ordering fragile on network flaps"
      └─ If network drops mid-sync, local queue can have out-of-order operations.
         Fix: State machine + version checks to ensure idempotent re-sync
   
   Record Opportunities:
   ├─ Opportunity 1: "Batch API for favorites (POST multiple at once)"
   │  └─ Current: One favorite at a time. Future: POST /api/v2/favorites/batch
   │     with [{ productId }, ...] to reduce round-trips
   ├─ Opportunity 2: "Favorites search (find favorites by tag)"
   │  └─ Current: No search. Future: Add search index on tags, provide
   │     search endpoint
   ├─ Opportunity 3: "Favorites sharing (share your list with others)"
   │  └─ Current: Private. Future: Add shareKey, public favorites endpoint
   └─ Opportunity 4: "Collaborative curation (Favorites as shared collections)"
      └─ Current: Individual only. Future: Team/shared list support
   
   Write to brain:
   ├─ Decision ID: RETROSPECT-SHOPAPP-FAVORITES-{timestamp}
   ├─ File: brain/self-test/{SELF_TEST_RUN_ID}/RETROSPECT-*.md
   ├─ Includes: All scores, patterns, gotchas, opportunities
   └─ Status: RECORDED

4. Verify All PRs Merged:
   ├─ master branch: all 4 commits present
   ├─ Tags created: v2.0-favorites (release candidate)
   └─ Brain: Retrospective recorded
```

**Assertions:**
- ✅ All 4 PRs raised with correct dependency links
- ✅ Merge order enforced (no out-of-order merges)
- ✅ All 4 PRs merged to master
- ✅ Dreamer retrospective completed
- ✅ Patterns extracted and recorded (4+ patterns)
- ✅ Gotchas documented (3+ gotchas)
- ✅ Opportunities identified (4+ opportunities)

**Expected Output:**
```
Phase 5: Ship + Retrospective ✅
===============================
PRs Raised:        4/4 with dependency links
├─ shared-schemas     PR#123 ✅
├─ backend-api        PR#124 ✅ (depends on PR#123)
├─ web-dashboard      PR#125 ✅ (depends on PR#124)
└─ app-mobile         PR#126 ✅ (depends on PR#124)

Merge Order:       ENFORCED (sequential, no parallel)
├─ PR#123 merged   ✅
├─ PR#124 merged   ✅
├─ PR#125 merged   ✅
└─ PR#126 merged   ✅

Retrospective:     COMPLETED
├─ Decisions scored: Correctness (5), Robustness (4), Efficiency (5),
                    Reversibility (5), Confidence (5)
├─ Patterns extracted: 4
├─ Gotchas documented: 3
├─ Opportunities identified: 4
└─ Decision ID: RETROSPECT-SHOPAPP-FAVORITES-{timestamp}

Release Tag:       v2.0-favorites
Status:            READY FOR PRODUCTION

Duration: 5-10 minutes
```

**Failure Modes & Recovery:**
- If PR merge blocked: check dependencies, verify prerequisite PR merged first
- If retrospective incomplete: invoke dream-retrospect manually with full context
- If patterns unclear: review tech decisions in brain, synthesize cross-repo patterns

---

## Pass/Fail Criteria Per Phase (Summary Table)

| Phase | Component | Pass Criteria | Fail If | Blocker |
|-------|-----------|--------------|---------|---------|
| **0** | Environment | All 4 infrastructure services online, seed data loaded, brain initialized | Any service offline, seed data missing, brain not writable | NEEDS_INFRA_CHANGE |
| **1** | Intake | PRD locked (PRDLK-* decision in brain), mandatory lock fields complete, no TBD | PRD not locked, any mandatory field TBD, surfaces not enumerated | BLOCKED (cannot proceed to Phase 2) |
| **1** | Contracts | All 5 contracts identified (API, DB, Cache, Events, Search) | Any contract missing or incomplete | BLOCKED |
| **2** | Council | All 4 surfaces reviewed (backend, web, app, infra), all contract terms negotiated | Any surface missing, any contract term TBD, unresolved conflicts | BLOCKED |
| **2** | Spec Freeze | Shared-dev-spec locked (SPECLOCK-* decision in brain) | Spec not frozen, lock file missing | BLOCKED (cannot proceed to Phase 3) |
| **3** | Tech Plans | 4 tech plans written and reviewed (1 per repo) | Plan missing, unreviewed, or fails self-review | BLOCKED |
| **3** | Build | All tasks DONE or DONE_WITH_CONCERNS, 0 BLOCKED tasks | Any task BLOCKED or NEEDS_CONTEXT | BLOCKED (cannot proceed to Phase 4) |
| **3** | TDD | Every task has test-first commit followed by impl commit, all tests passing | Implementation before test, failed tests, no clear TDD cycle | BLOCKED |
| **4** | Code Review | spec-reviewer PASS for all 4 repos, code-quality-reviewer PASS for all 4 repos | Any reviewer FAIL, critical issues found | BLOCKED (rework required) |
| **4** | Stack Up | All 4 services running (MySQL, Redis, Kafka, ES), stack healthy | Any service failed to start, health check failed | BLOCKED (cannot proceed to eval) |
| **4** | Eval | All 6 drivers completed, eval-judge returns GREEN verdict | Any driver skipped, YELLOW verdict, any scenario failed | BLOCKED (cannot proceed to Phase 5) |
| **5** | PRs | All 4 PRs raised with dependency links, merge order enforced, all merged | PR missing dependency link, merge order violated, merge failed | BLOCKED (cannot release) |
| **5** | Retrospective | Dreamer retrospective completed, score + patterns recorded in brain | Retrospective incomplete, no patterns extracted | WARNING (log but allow) |

---

## Recovery Guide: Troubleshooting Per Phase

### Phase 0 Failure: Environment Setup

**Symptom:** One or more infrastructure services won't start (MySQL, Redis, Kafka, Elasticsearch)

**Diagnosis:**
```bash
# Check MySQL
mysql -h localhost -u root -e "SELECT 1" || echo "MySQL FAILED"

# Check Redis
redis-cli PING || echo "Redis FAILED"

# Check Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092 || echo "Kafka FAILED"

# Check Elasticsearch
curl -s http://localhost:9200/_health || echo "ES FAILED"

# Check Docker volumes
docker volume ls | grep shopapp
```

**Recovery Actions:**
1. Start missing services: `docker-compose up -d {service}`
2. Wait for health checks: `docker-compose ps` (all Status=healthy)
3. If service crashes: check logs (`docker-compose logs {service}`), fix root cause
4. If port conflict: check what's using the port, stop conflicting process or change port
5. If data missing: reseed test data from `seed-product/shopapp/scripts/seed-data.sql`
6. **If unrecoverable:** Escalate NEEDS_INFRA_CHANGE, update CI/CD infrastructure setup

**Proceed to Phase 1 only when:** All 4 services online + health checks pass

---

### Phase 1 Failure: PRD Won't Lock

**Symptom:** Brain won't create PRDLK-* decision, or PRD context shows status != LOCKED

**Diagnosis:**
```bash
# Check brain directory exists
ls -la brain/self-test/${SELF_TEST_RUN_ID}/

# Check PRDLK decision file
ls -la brain/self-test/${SELF_TEST_RUN_ID}/PRDLK*

# Check decision status
grep "status:" brain/self-test/${SELF_TEST_RUN_ID}/PRDLK-*.md
```

**Recovery Actions:**
1. Verify PRD file exists: `cat seed/prds/01-favorites-cross-surface-sync.md` (not empty)
2. Verify SELF_TEST_BRAIN env var set: `echo $SELF_TEST_BRAIN` (should output path)
3. Verify brain-write skill available: `cat skills/brain-write/SKILL.md` (check exists)
4. Check for TBD values in `prd-locked.md` (run `intake-interrogate` again; elicit remaining doubts)
5. Manually create decision file if skill fails:
   ```bash
   cat > brain/self-test/${SELF_TEST_RUN_ID}/PRDLK-SHOPAPP-FAVORITES.md <<'EOF'
   # PRD Lock: ShopApp Favorites Cross-Surface Sync
   status: LOCKED
   timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
   questions_answered: 8/8
   surfaces: [backend-api, web-dashboard, app-mobile, shared-schemas]
   contracts: [api-rest, schema-db, cache-redis, event-bus, search-es]
   EOF
   ```
6. **If still fails:** Escalate BLOCKED, review brain-write skill error logs

**Proceed to Phase 2 only when:** PRDLK-* decision exists with status=LOCKED

---

### Phase 2 Failure: Surfaces Don't Agree

**Symptom:** Council negotiation deadlocks (e.g., backend wants push, app wants pull), no resolution

**Diagnosis:**
```bash
# Check council output
brain-recall "council conflict sync strategy" | grep -i "backend\|app\|resolution"

# Check which surface didn't approve
grep -i "conflict\|blocked\|unresolved" brain/self-test/${SELF_TEST_RUN_ID}/SPECLOCK*.md
```

**Recovery Actions:**
1. Review the specific conflict (which surfaces? what terms?)
2. Invoke dreamer manually: `dream-resolve-inline` with conflict details
3. Dreamer mediates: proposes a hybrid approach or picks one surface's approach with rationale
4. Record dreamer decision in brain: `DREAMER-CONFLICT-RESOLUTION-{timestamp}`
5. Update shared-dev-spec with resolved terms
6. Re-run council negotiation with resolved spec
7. **If dreamer can't resolve:** Escalate BLOCKED, may need PRD clarification from product

**Proceed to Phase 3 only when:** All 4 surfaces approved (or dreamer override recorded)

---

### Phase 3 Failure: Build Task Blocked

**Symptom:** dev-implementer reports task BLOCKED (e.g., "Missing DB migration template")

**Diagnosis:**
```bash
# Check which task is blocked
git log --oneline | grep -i "BLOCKED\|ERROR"

# Check dev-implementer output
brain-recall "task blocked" | head -20

# Check worktree status
ls -la .claude/worktrees/

# Check test status
cd {repo-worktree} && npm test 2>&1 | tail -30
```

**Recovery Actions:**
1. Identify the blocking issue (missing file? spec ambiguity? dependency not available?)
2. If missing file: add it to seed product or update tech plan to not require it
3. If spec ambiguous: clarify with brain-read (look up related decisions) or invoke dreamer
4. If dependency missing: install/configure it, then retry task
5. Fix the root cause (not the symptom)
6. Retry the failed task in its worktree
7. Verify test passes and commit is created
8. **If unresolvable:** Escalate BLOCKED, may indicate Forge skill issue (e.g., dev-implementer skill bug)

**Proceed to Phase 4 only when:** All tasks DONE (or DONE_WITH_CONCERNS with documented reason)

---

### Phase 4 Failure: Code Review Finds Issues

**Symptom:** spec-reviewer or code-quality-reviewer reports FAIL for one or more repos

**Diagnosis:**
```bash
# Check spec-reviewer report
brain-recall "spec review fail" | head -30

# Check which repo and which criteria failed
grep -i "fail\|error\|issue" brain/self-test/${SELF_TEST_RUN_ID}/REVIEW-*.md
```

**Recovery Actions:**
1. Read the reviewer feedback (which spec term violated? which quality issue?)
2. Dispatch dev-implementer to fix the issue in the failing repo
3. Dev-implementer: TDD workflow (write test for the issue, fix code, verify test passes)
4. Create new commit with fix
5. Re-run code review on fixed repo
6. **Proceed to eval only when:** All repos PASS code review

---

### Phase 4 Failure: Eval Returns YELLOW (Not GREEN)

**Symptom:** eval-judge returns YELLOW verdict (all critical passed, some non-critical failed)

**Diagnosis:**
```bash
# Check eval output
eval-judge verdict YELLOW

# Which driver failed? Which scenario?
brain-recall "eval yellow scenario" | grep -i "failed\|passed\|critical"
```

**Recovery Actions:**
1. Read eval report details (which scenarios failed? critical or non-critical?)
2. If critical failure: this is a bug, requires fix (see Phase 3 recovery)
3. If non-critical failure: 
   a. Determine if it's a Forge skill issue or seed product limitation
   b. If skill issue: fix skill, re-run eval
   c. If seed product limitation: document as known limitation, create issue for future work
4. **Self-test requires GREEN.** YELLOW is not acceptable. Either fix to GREEN or escalate BLOCKED.

---

### Phase 4 Failure: Stack Won't Start

**Symptom:** eval-product-stack-up fails (services start but stack unhealthy)

**Diagnosis:**
```bash
# Check stack status
docker-compose ps

# Check service logs
docker-compose logs -f {failing-service} | tail -50

# Check connectivity
curl http://localhost:3000/health || echo "API unhealthy"
redis-cli PING
mysql shopapp -e "SELECT 1"
```

**Recovery Actions:**
1. Check which service failed to start (read docker-compose logs)
2. Fix the service issue (missing env var? port conflict? bad config?)
3. Restart stack: `docker-compose down && docker-compose up -d`
4. Wait for health checks: `docker-compose ps` (all healthy)
5. If data not loaded: reseed from `seed-product/shopapp/scripts/`
6. If migrations not applied: `docker-compose exec mysql mysql shopapp < migrations.sql`
7. **If unrecoverable:** May need infrastructure fix (see Phase 0 recovery)

**Proceed to eval drivers only when:** All services healthy, stack passes health check

---

### Phase 5 Failure: PR Merge Blocked

**Symptom:** PR won't merge (dependency check failed, or merge conflict)

**Diagnosis:**
```bash
# Check PR merge order
git log --oneline --graph | head -20

# Check which PR is blocked
brain-recall "PR merge blocked" | head -20

# Check merge conflicts
git status | grep "CONFLICT"
```

**Recovery Actions:**
1. If dependency PR not merged yet: merge dependencies first (enforce order)
2. If merge conflict: resolve conflict (code review findings may indicate why)
3. If merge validation failed: address the validation error (lint, test, etc.)
4. Retry merge in correct order
5. **If unrecoverable:** May indicate a coordination issue between repos (escalate BLOCKED)

---

## Expected Execution Times (Per Phase)

| Phase | Duration | Notes |
|-------|----------|-------|
| **Phase 0** | 2-3 min | Environment setup, data seeding |
| **Phase 1** | 5-10 min | PRD intake, mandatory lock fields, lock decision |
| **Phase 2** | 15-20 min | Multi-surface council, contract negotiation, conflict resolution (if any) |
| **Phase 3** | 30-45 min | Tech plans for 4 repos, build 4 repos in parallel worktrees (4 tasks each), TDD cycle per task |
| **Phase 4** | 20-30 min | Code review (2 reviewers per repo), eval stack up (5 min), 6 drivers (6 scenarios each, ~25 total) |
| **Phase 5** | 5-10 min | Raise & merge 4 PRs (enforced order), retrospective decision write |
| **TOTAL** | **90-120 min** | ~1.5-2 hours for full self-test (no blockers) |

**Note:** Actual time varies based on:
- Infrastructure startup time (add 10 min if services cold-start)
- Conflict resolution in council (add 5-10 min per conflict)
- Rework if code review finds issues (add 10-20 min)
- Eval driver failures and debugging (add 10-30 min per failure)

---

## Anti-Patterns for Self-Test (Avoid These)

### Anti-Pattern 1: "Skip phases because other phases work"

**What someone might say:** "Individual skills all work in isolation, and we tested phase 2 separately last week. Let's just run phase 2 and call it a day."

**Why this fails:** Integration failures happen at phase boundaries. Skipping phases misses:
- Context carryover bugs (phase 2 output → phase 3 input bugs)
- Dependency failures (phase 3 relies on phase 2 decision, decision was wrong)
- Cumulative state corruption (by phase 4, brain has stale decisions from early phases)

**Enforcement:** All 5 phases required. Sequential execution only. No cherry-picking.

---

### Anti-Pattern 2: "Use production brain for self-test"

**What someone might say:** "Self-test will write decisions to brain/. Let's just use the production brain directory to save space."

**Why this fails:** Self-test modifications pollute production decision history:
- Self-test decisions remain in brain after test completes
- Real product features inherit stale decisions from self-test runs
- Decision IDs collide (PRDLK-SHOPAPP-FAVORITES written by test, then real feature tries same ID)

**Enforcement:** Use clean brain path: `brain/self-test/${SELF_TEST_RUN_ID}/`. Delete or archive after test completes.

---

### Anti-Pattern 3: "Partial self-test = self-test passed"

**What someone might say:** "We ran phases 1-4 and they passed. Eval is slow, let's skip phase 5 (ship/retrospective) for now."

**Why this fails:** Partial success masks regressions:
- Phase 5 (ship) reveals merge conflicts that phases 1-4 didn't catch
- Retrospective (phase 5) records patterns that influence future work
- PR coordination issues only show up during merge

**Enforcement:** All 5 phases pass OR self-test fails. Partial != sufficient.

---

## Edge Cases & Fallback Paths (The 3 Trickiest Scenarios)

### Edge Case 1: Seed Product Not Found

**Symptom:** Phase 0 fails with `seed-product/shopapp/` doesn't exist

**Root Cause:** Seed product directory missing or wrong path

**Action:**
1. Verify seed product exists: `ls -la seed-product/shopapp/`
2. If missing: initialize from template: `make init-seed-product` (or manual setup)
3. Load sample data: `bash seed-product/shopapp/scripts/seed-data.sh`
4. Verify data loaded: `mysql shopapp -e "SELECT COUNT(*) FROM users;"`
5. Retry Phase 0

**Escalation:** If seed product can't be initialized → NEEDS_INFRA_CHANGE

---

### Edge Case 2: Brain Not Initialized or Corrupted

**Symptom:** Phase 1 fails with `brain/` doesn't exist, or decisions won't write

**Root Cause:** Brain directory structure malformed or missing

**Action:**
1. Verify brain structure: `brain-read --show-layout` (per forge-brain-layout)
2. If missing: initialize: `brain-init {product-name}`
3. If corrupted: backup old brain and start fresh: `rm -rf brain/ && brain-init shopapp`
4. Verify write works: `brain-write "test decision" --title "TEST"`
5. Retry Phase 1

**Escalation:** If brain won't initialize → NEEDS_INFRA_CHANGE

---

### Edge Case 3: Eval Fails at Random Point (Network/Infrastructure Flake)

**Symptom:** Phase 4 (eval) passes most drivers but one driver fails randomly (timing-dependent)

**Root Cause:** Infrastructure flaky (service timeout, network delay, race condition)

**Action:**
1. Identify flaky driver: read eval-judge output (which driver failed?)
2. Diagnose: is it timing-sensitive? (check driver logs)
3. Increase timeout or improve test stability (e.g., add retry logic to scenario)
4. Re-run eval from flaky driver: don't restart entire phase if unrelated drivers passed
5. If consistently fails: likely a real bug (not flake), treat as Phase 3 rework

**Escalation:** If flakiness unresolvable → BLOCKED (infrastructure instability)

---

### Edge Case 4: Self-Test Passes but Seed Product Doesn't Match Real-World Complexity

**Symptom:** All 5 self-test phases pass against the ShopApp seed product, but when Forge is applied to a real product (e.g., a multi-repo fintech app with 5 services), it fails at the council or eval phase.

**Do NOT:** Treat a seed product pass as a guarantee that Forge handles all product shapes correctly.

**Action:**
1. Identify which real-world aspect caused failure: multi-repo coordination? Missing driver? Contract negotiation complexity?
2. Add a pressure scenario to the seed product that covers the failing pattern
3. Re-run self-test with the new scenario before declaring Forge healthy
4. Document the gap: what class of products does the current self-test NOT cover?
5. Escalation: DONE_WITH_CONCERNS — Forge works for the tested shape; coverage gaps must be documented

---

### Edge Case 5: Phase N Passes in Self-Test but Phase N+1 Has Wrong Input

**Symptom:** Phase 2 (Council) passes self-test. Phase 3 (Build) fails because the shared-dev-spec.md produced by Phase 2 is malformed or missing a required field that Phase 3 depends on.

**Do NOT:** Debug Phase 3 in isolation — the root cause is Phase 2's output format.

**Action:**
1. Read the shared-dev-spec.md produced by Phase 2 — verify it contains all required fields for Phase 3
2. Identify the schema mismatch: which field is missing or malformed?
3. Fix Phase 2's output format (not Phase 3's input parsing)
4. Re-run Phase 2 → Phase 3 sequence to verify the fix is end-to-end
5. Add an assertion to the self-test that validates Phase 2 output before Phase 3 starts
6. Escalation: NEEDS_CONTEXT — provide the malformed spec and expected schema to the dreamer

---

## Cross-References: Skills & Concepts Used in Self-Test

**Core Pipeline Skills:**
- `/forge-intake-gate` — Phase 1 (PRD locking)
- `/forge-council-gate` — Phase 2 (multi-surface negotiation)
- `/forge-tdd` — Phase 3 (TDD discipline enforcement)
- `/forge-eval-gate` — Phase 4 (eval orchestration)
- `/dream-retrospect-post-pr` — Phase 5 (retrospective)

**Surface Reasoning Skills (Phase 2):**
- `reasoning-as-backend` — Backend API design
- `reasoning-as-web-frontend` — Web UI design
- `reasoning-as-app-frontend` — Mobile app design
- `reasoning-as-infra` — Infrastructure & deployment design

**Contract Negotiation Skills (Phase 2):**
- `contract-api-rest` — REST API terms
- `contract-schema-db` — Database schema terms
- `contract-cache` — Cache layer terms
- `contract-event-bus` — Event bus/Kafka terms
- `contract-search` — Search index terms

**Build & Review Skills (Phase 3-4):**
- `worktree-per-project-per-task` — Isolated task environments
- `dev-implementer` — Implementation & self-review
- `tech-plan-write-per-project` — Per-repo planning
- `forge-trust-code` / `spec-reviewer` — Spec compliance review
- `code-quality-reviewer` — 11-point quality framework

**Eval Driver Skills (Phase 4):**
- `eval-product-stack-up` — Start all services
- `eval-driver-api-http` — REST API testing
- `eval-driver-db-mysql` — Database validation
- `eval-driver-cache-redis` — Cache verification
- `eval-driver-bus-kafka` — Event bus validation
- `eval-driver-web-cdp` — Web UI testing (Chrome DevTools)
- `eval-driver-android-adb` — Mobile UI testing (ADB)
- `eval-judge` — Aggregate verdicts

**Brain & Decision Skills (All Phases):**
- `brain-write` — Record decisions
- `brain-read` — Inspect decisions
- `brain-recall` — Search decisions
- `brain-link` — Connect decisions

**Troubleshooting Skills (All Phases):**
- `self-heal-systematic-debug` — 4-phase debugging (investigate, localize, fix, verify)
- `self-heal-locate-fault` — Identify which service failed
- `dream-resolve-inline` — Conflict resolution

**Seed Product:**
- Location: `seed-product/shopapp/`
- 4 repos: shared-schemas, backend-api, web-dashboard, app-mobile
- Test PRD: `seed/prds/01-favorites-cross-surface-sync.md`

**Brain Layout:**
- Location: `brain/self-test/{SELF_TEST_RUN_ID}/`
- Decision format per `forge-brain-layout`
- IDs: PRDLK-*, SPECLOCK-*, DREAMER-*, RETROSPECT-*

---

## Edge Cases & Fallback Paths

### Case 1: Phase Fails Mid-Run
- **Symptom:** Phase 3 fails at task 7 of 12 (4 tasks left)
- **Do NOT:** Skip failed tasks and continue to Phase 4
- **Action:**
  1. Record failure in brain (which task, which error, which repo)
  2. Diagnose: skill bug? seed product issue? infrastructure issue?
  3. Fix the root cause (not the symptom)
  4. Re-run the failed phase from the failed task (not from Phase 1 unless brain state is corrupted)
  5. Continue forward only when phase passes completely

### Case 2: Eval Returns YELLOW
- **Symptom:** eval-judge returns YELLOW (all critical passed, some non-critical failed)
- **Do NOT:** Accept YELLOW as self-test pass
- **Action:**
  1. Read YELLOW verdict details (which scenarios failed, why)
  2. Determine: is this a Forge skill bug or a seed product limitation?
  3. If skill bug: fix skill, re-run eval
  4. If seed product limitation: document as known limitation, update seed product
  5. Self-test requires GREEN

### Case 3: Infrastructure Unavailable (MySQL, Kafka, etc.)
- **Symptom:** `eval-product-stack-up` fails because Redis or Kafka not running
- **Do NOT:** Skip drivers that depend on unavailable infrastructure
- **Action:**
  1. Start the missing infrastructure
  2. Re-run `eval-product-stack-up`
  3. If infrastructure cannot be started: escalate BLOCKED
  4. Do NOT run partial eval and claim success

### Case 4: Dreamer Cannot Resolve Council Conflict During Test
- **Symptom:** Backend and app surfaces deadlock on sync strategy (push vs. pull)
- **Do NOT:** Skip conflict resolution and proceed with one surface's proposal
- **Action:**
  1. Record the conflict in brain
  2. Invoke dreamer inline
  3. Dreamer decides: push (lower app battery drain) or pull (simpler backend)
  4. Record dreamer decision with rationale
  5. Continue council with resolved conflict

### Case 5: Self-Test Reveals a Skill Bug
- **Symptom:** `forge-tdd` skill is not enforcing RED step (allowing implementation before test failure is confirmed)
- **Do NOT:** Patch around the skill bug, mark self-test as passed
- **Action:**
  1. Record the skill bug in brain (which skill, what behavior)
  2. STOP self-test
  3. Fix the skill (per `forge-writing-skills` TDD-for-skills workflow)
  4. Re-run self-test from Phase 1 (skill change may affect all phases)

---

## Self-Test Checklist

Before declaring Forge production-ready, verify all items:

**Phase 0:**
- [ ] Seed product repos accessible
- [ ] Brain path initialized (clean state, no prior run contamination)
- [ ] Infrastructure running (MySQL, Redis, Kafka, Elasticsearch)

**Phase 1 (Intake):**
- [ ] `/forge-intake-gate` invoked
- [ ] All mandatory intake lock fields satisfied
- [ ] PRD locked in brain (decision ID recorded)

**Phase 2 (Council):**
- [ ] `/forge-council-gate` invoked
- [ ] All 4 surfaces attended
- [ ] All 5 contracts negotiated
- [ ] Shared-dev-spec frozen (SPECLOCK decision ID)

**Phase 3 (Build):**
- [ ] Tech plans written for all 4 repos
- [ ] Tech plans self-reviewed
- [ ] All tasks dispatched to dev-implementer in isolated worktrees
- [ ] All tasks report DONE (no BLOCKED remaining)
- [ ] TDD cycle verifiable in commit history

**Phase 4 (Review + Eval):**
- [ ] spec-reviewer: PASS for all repos
- [ ] code-quality-reviewer: PASS for all repos
- [ ] eval-product-stack-up succeeded
- [ ] All 6 drivers ran (no skipped drivers)
- [ ] eval-judge: GREEN verdict

**Phase 5 (Ship):**
- [ ] All PRs raised with dependency links
- [ ] Merge order enforced
- [ ] Dreamer retrospective complete
- [ ] Score and patterns recorded in brain

**Output:** `FORGE IS PRODUCTION-READY` or `FORGE NOT READY — [specific failure]`
