---
name: eval-coordinate-multi-surface
description: "WHEN: A multi-surface eval scenario needs to be executed across web, API, DB, cache, search, and event bus layers. Coordinate multi-driver eval scenarios. Chain web (CDP) → API (HTTP) → DB (MySQL) → cache (Redis) → search (ES) → events (Kafka). Report pass/fail with evidence."
type: rigid
requires: [brain-read, eval-driver-web-cdp, eval-driver-api-http, eval-driver-db-mysql, eval-driver-cache-redis, eval-driver-search-es, eval-driver-bus-kafka]
version: 1.0.0
preamble-tier: 3
triggers:
  - "run multi-surface eval"
  - "coordinate eval drivers"
  - "run all eval drivers"
allowed-tools:
  - Bash
---

# eval-coordinate-multi-surface

Orchestration skill that chains eval drivers together to run cross-service scenarios. Validates data flows across the full tech stack: web UI → API → database → cache → search index → event bus.

## Anti-Pattern Preamble: Why Multi-Surface Coordination Matters

Teams rationalize away multi-surface eval, thinking single-layer testing is sufficient. These rationalizations are false:

**Rationalization #1: "We'll eval web separately, API separately, DB separately"**
- False belief: Services can be validated in isolation
- Reality: Integration breaks at service boundaries, not within them. A web test passes but the API never receives the request. An API test passes but the DB never wrote. You ship both "working" layers that don't work together.
- Cost of ignoring: Ship race condition between frontend and backend. Spend 4 hours in production debugging what 20 minutes of multi-surface eval would have caught.

**Rationalization #2: "Multi-surface eval is too slow, let's just test one layer"**
- False belief: Speed matters more than correctness
- Reality: You'll ship a race condition or missing event listener. The 10 minutes saved in eval becomes 8 hours in staging debugging, then a P1 incident. Multi-surface eval is not slower—it's faster ROI.
- Cost of ignoring: Race condition where web sends POST, API processes it, but cache never invalidates. Frontend reads stale data. Users see inconsistent state.

**Rationalization #3: "Services are independent, no need to coordinate"**
- False belief: Service boundaries are clean
- Reality: They're only independent until they interact (always). The moment web calls API, they're coupled. The moment API writes to DB, they're coupled. Coupling is invisible in unit tests but catastrophic in integration.
- Cost of ignoring: Service A succeeds, Service B fails silently. Orphaned data in DB. Inconsistent cache. Search index never refreshed.

**Rationalization #4: "We can debug integration issues in staging"**
- False belief: Staging catches what eval misses
- Reality: In eval you can recreate the bug in 20 minutes. In staging you'll spin up 6 services, wait for warm cache, reproduce race condition 1 in 20 tries, spend 8 hours. Multi-surface eval makes bugs reproducible.
- Cost of ignoring: Cascade failure: API timeout → web hangs → user refreshes → duplicate POST → orphaned transaction → data corruption.

## Iron Law

```
EVERY SURFACE IN THE SCENARIO MUST BE DRIVEN IN ORDER — NO SURFACE IS SKIPPED EVEN IF ALL PRIOR SURFACES PASSED. A SCENARIO THAT SKIPS ANY SURFACE IS NOT A MULTI-SURFACE EVAL.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A scenario step fails and subsequent steps are still executed** — A failed step means the system is in an unknown state. Running further steps against corrupted state produces meaningless results. STOP. Any step failure must abort the scenario and record the failure point.
- **DB and cache are not checked after a web action** — A web action completing does not mean the data persisted or the cache invalidated. These are separate layers that can silently fail. STOP. Every write action must be followed by DB and cache verification steps.
- **Services are health-checked at startup but not re-verified mid-scenario** — A service can degrade or crash during a long scenario. Health at start ≠ health at step 12. STOP. Re-check critical service health after any step that produces unexpected results.
- **Scenario reports PASS but evidence logs are empty or "N/A"** — A pass claim without evidence is a trust claim, not a verified claim. STOP. Every scenario step must produce a concrete evidence entry (query result, HTTP response, element screenshot, or event payload).
- **A surface is excluded from a scenario because "we didn't change it"** — Unchanged surfaces still process data from changed surfaces. A search index may break due to a schema change it didn't own. STOP. All surfaces must be driven in every end-to-end scenario.
- **Scenario timeout is set higher than the SLA for the user flow** — A scenario that passes after 45 seconds but the SLA is 3 seconds is a failing scenario, not a passing one. STOP. Scenario timeout must be set at or below the SLA specified in the shared-dev-spec.

## Edge Cases in Multi-Surface Coordination

Multi-surface scenarios expose edge cases that single-driver tests miss. Document these explicitly and provide fallback strategies:

### Edge Case 1: Service Startup Order Dependency
**Problem:** API depends on DB connectivity. Web depends on API. Starting them out of order causes cascading failures.
- Web starts, tries to call API
- API is not yet healthy
- Web gets 503, fails scenario
- DB is actually fine; the chain broke early

**Action:** 
- Document startup order in scenario metadata: `["db", "cache", "api", "web", "search", "events"]`
- Before scenario executes, verify all services healthy in dependency order
- Check: DB is writable → API responds → Web loads → Cache connected → Search accessible → Events broker reachable

**Fallback:**
- Wait with exponential backoff (100ms, 200ms, 400ms) for each service health check
- If service doesn't respond within 5 retries, fail scenario with clear error: "Startup order: DB healthy, API unhealthy (timeout after 3.1s). Scenario aborted."

### Edge Case 2: Cascade Failure (One Service Down Breaks Chain)
**Problem:** API times out, web UI waits forever, cache gets stale, search index never updates.
```
Web sends POST → API hangs (DB slow) → Web timeout not set → User refreshes → Duplicate POST → Race condition
```

**Action:**
- Set realistic timeouts per driver, not inherited from parent
- If API timeout is 30s but scenario timeout is 25s, scenario exceeds timeout waiting for unavailable service
- Configure per-driver failure_mode: `"stop"` (fail scenario if this service fails) vs `"continue"` (non-critical, skip and proceed)

**Example:**
```yaml
steps:
  - surface: api
    method: POST
    endpoint: /order/create
    timeout: 5s  # API must respond in 5s
    failure_mode: "stop"  # If API fails, stop everything
  - surface: db
    query: "SELECT * FROM orders WHERE id = ?"
    timeout: 2s  # DB must respond in 2s
    failure_mode: "continue"  # If DB slow, still check cache
  - surface: cache
    command: GET
    key: "order:123"
    failure_mode: "continue"  # Cache miss is OK, proceed to search
```

**Fallback:**
- Document which failures are cascade-triggers (stop) vs isolated (continue)
- Cascade-trigger: API failure → stop (web can't work without API)
- Isolated: Cache miss → continue (cache is optional, DB is source of truth)

### Edge Case 3: Cross-Service Race Condition
**Problem:** Web sends POST, DB writes successfully, but cache invalidation is async. Web reads cache before invalidation completes. User sees stale data.
```
T=0: Web sends POST /order/create
T=1: API processes, writes to DB ✓
T=2: API triggers async cache invalidation (event to Kafka)
T=3: Web assertion reads cache (checking if order is there)
     Cache still has old data (invalidation not yet processed)
     Assertion fails
T=5: Kafka message finally processes, cache invalidates (too late)
```

**Action:**
- Insert explicit wait-for-invalidation step before reading cache
- Don't assume async operations completed; verify them synchronously

**Example:**
```yaml
steps:
  - surface: api
    method: POST
    endpoint: /order/create
    body: {product_id: 123}
    expect_status: 201
  
  - surface: db
    query: "SELECT id FROM orders WHERE product_id = 123 LIMIT 1"
    assertions: [{column: "id", type: "exists"}]
  
  # WRONG: Would race on cache invalidation
  # - surface: cache
  #   command: GET
  #   key: "order:123"
  
  # RIGHT: Wait for cache TTL refresh or explicit verification
  - surface: api
    method: GET
    endpoint: /order/123
    assertions: [{field: "from_cache", expected: false}]  # Force refresh from DB
  
  - surface: cache
    command: GET
    key: "order:123"
    assertions: [{type: "exists"}]  # Now it should be there
```

**Fallback:**
- If cache read fails, wait 100ms and retry (eventual consistency)
- If still missing after 3 retries, document as expected behavior: "Cache invalidation eventual (P95: 200ms)"

### Edge Case 4: Inconsistent State Between Services
**Problem:** DB committed but search index not yet updated (eventual consistency). Scenario checks search immediately, finds nothing.

**Action:**
- For eventually-consistent services, add explicit wait and retry logic
- Add `refresh: true` directive to Elasticsearch to force immediate index refresh
- For cache: explicitly verify invalidation with `GET` after `DEL`
- For DB: check durability with explicit flush/sync if applicable

**Example:**
```yaml
steps:
  - surface: api
    method: POST
    endpoint: /user
    body: {name: "Alice", email: "alice@example.com"}
    expect_status: 201
  
  - surface: db
    query: "SELECT id FROM users WHERE email = 'alice@example.com'"
    assertions: [{column: "id", type: "exists"}]
  
  - surface: search
    query: {"query": {"match": {"email": "alice@example.com"}}}
    refresh: true  # Force index refresh before search
    retry: {max_attempts: 3, delay_ms: 100}  # Retry if still not found
    assertions: [{field: "email", expected: "alice@example.com"}]
```

**Fallback:**
- Document consistency window (P95 sync time) in scenario metadata: "Search index: eventual consistency, P95 = 200ms"
- If assertion fails, check: Is DB row actually there? If yes, wait and retry. If no, data never persisted.

### Edge Case 5: Service-Specific Timeout Cascades
**Problem:** Web step has 30s timeout, API has 30s timeout, DB has 30s timeout = 90s total. Scenario metadata timeout is 60s. Scenario times out before completion.

**Action:**
- Calculate cumulative timeout: sum of all service timeouts + network latency + buffer
- Set scenario timeout >= cumulative timeout
- Document timeout breakdown in metadata

**Example:**
```yaml
scenario_metadata:
  name: "User creates order and confirms"
  timeout: 90s  # CALCULATED from below
  timeout_breakdown:
    - web_navigate: 5s
    - api_create_order: 10s
    - db_insert: 2s
    - cache_invalidate: 1s (async)
    - search_index_refresh: 3s
    - events_consume: 30s (worst-case Kafka latency)
    - network_buffer: 20%
    - total: (5 + 10 + 2 + 1 + 3 + 30) * 1.2 = 69.6s → round to 90s
```

**Fallback:**
- If cumulative timeout exceeds 2 minutes, break scenario into sub-scenarios
- Example: "Create order" (45s) + "Confirm order" (45s) instead of one 120s scenario
- Rationale: Timeouts are contracts. If a contract is unrealistic, renegotiate by splitting work

### Edge Case 6: External Service Health Assumptions
**Problem:** Kafka broker is down. Scenario fails because events can't be consumed. But test assumes Kafka is up. Error is misleading: "Assertion failed: event not found" (true, but root cause is Kafka down, not code).

**Action:**
- Add precondition checks that verify all services are healthy before scenario executes
- Document preconditions clearly

**Example:**
```yaml
scenario:
  name: "User creates order"
  preconditions:
    - service: api
      check: "GET /health"
      expect_status: 200
    - service: db
      check: "SELECT 1"
      expect_query_time_ms: 1000
    - service: kafka
      check: "list-brokers"
      expect_count_gt: 0
    - service: cache
      check: "PING"
      expect_response: "PONG"
    - service: search
      check: "GET /"
      expect_status: 200
  on_precondition_fail: "abort_with_clear_error"
```

**Fallback:**
- If precondition fails, abort scenario with error: "Precondition failed: Kafka broker not accessible. Service dependencies unmet. Scenario aborted."
- Don't proceed; don't report false failures

### Edge Case 7: Partial Failure Recovery
**Problem:** Web step fails (button didn't click), but you want DB step to still run to verify rollback. If scenario stops on first failure, you never know if DB rolled back properly.

**Action:**
- Use `failure_mode: "continue"` for non-critical steps to allow execution to proceed
- Collect evidence (screenshots, logs) even if assertion fails
- Allow scenario to complete to verify state at each layer

**Example:**
```yaml
steps:
  - surface: web
    action: click
    selector: "#broken-button"
    failure_mode: "continue"  # Don't stop if click fails
    
  - surface: api
    method: GET
    endpoint: /order/123
    failure_mode: "continue"  # Check API state regardless
    
  - surface: db
    query: "SELECT status FROM orders WHERE id = 123"
    failure_mode: "continue"  # Verify DB rollback regardless
```

**Fallback:**
- Screenshot after every step, even if failed
- Logs from each service, even if assertion didn't match
- This evidence shows: "Web failed to click, API shows no order created, DB shows no order—rollback worked correctly"

## Service Orchestration Checklist

Before executing any multi-surface scenario, work through this checklist to verify coordination safety:

- [ ] **Service dependency map**: Draw which services depend on which. Minimum example:
  ```
  DB (leaf)
    ↑
  Cache (depends on DB for source of truth)
    ↑
  API (depends on Cache and DB)
    ↑
  Web (depends on API)
  
  Search (depends on API via async)
  Events (depends on API via async)
  ```

- [ ] **Health check order**: Verify services in dependency order (leaf nodes first). If DB is down, no point checking API.
  - DB: `SELECT 1` → expect response in <1s
  - Cache: `PING` → expect "PONG"
  - API: `GET /health` → expect 200
  - Web: Page loads → expect <5s
  - Search: `GET /` → expect 200
  - Events: List brokers → expect count > 0

- [ ] **Startup verification**: Before scenario, check: Is API responding? Is DB writable? Is cache connected?
  - Minimum: API responds, DB writable, Cache reachable
  - If any fail, abort scenario with precondition failure (not data failure)

- [ ] **Timeout calculation**: Sum all service timeouts. Add 20% buffer for network. Set scenario timeout >= sum.
  - Example: 5s (web) + 10s (api) + 2s (db) + 1s (cache) + 3s (search) + 30s (events) = 51s
  - With 20% buffer: 51s * 1.2 = 61.2s → set scenario timeout to 90s (round up)

- [ ] **State visibility**: Every state-changing action has verification step on target service.
  - Web clicks button → verify API endpoint called (via API logs or HTTP mock assertion)
  - API writes to DB → verify DB row exists (query assertion)
  - API invalidates cache → verify cache key missing (cache assertion with retry)
  - Async event published → verify Kafka message received (events assertion with timeout)

- [ ] **Cascade detection**: Identify which service failures can cascade. Use `failure_mode: "stop"` for those.
  - Cascade: API fails → Web can't function → mark as `stop`
  - Isolated: Cache miss → DB still readable → mark as `continue`
  - Example: If DB fails, API fails, Web fails (cascade). If search fails, DB still authoritative (isolated).

- [ ] **Evidence collection**: Screenshots after critical steps. Logs from each service. Query results at each layer.
  - Web: Screenshot after navigate, after click, after submit
  - API: Response body for every POST/PUT
  - DB: Query result for every SELECT after write
  - Cache: Key contents before and after invalidation
  - Search: Document contents before and after index
  - Events: Message contents after publish

- [ ] **Rollback testing**: If scenario uses `failure_mode: "continue"`, verify that failed scenarios don't leave orphaned data.
  - If web click fails, does API still have the half-written state?
  - If API fails mid-transaction, does DB have orphaned rows?
  - If cache invalidation fails, is DB still authoritative?
  - Verify cleanup or atomicity

## Service Coordination Patterns

Three patterns for orchestrating multi-surface scenarios. Choose based on assurance vs. speed tradeoff:

### Pattern 1: Sequential Verification (Safe but Slow)

Execute each service layer fully before moving to the next. Every action verified before proceeding. Safest pattern; slowest execution.

```yaml
scenario:
  name: "User creates order (sequential)"
  coordination: "sequential_verification"
  steps:
    # Layer 1: Web UI action
    - surface: web
      action: click
      selector: "#create-order"
      timeout: 5s
      failure_mode: "stop"
    
    # Layer 2: Verify API received it
    - surface: api
      method: GET
      endpoint: /order/last
      timeout: 5s
      assertions:
        - field: status
          expected: "pending"
      failure_mode: "stop"
    
    # Layer 3: Verify DB persisted
    - surface: db
      query: "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1"
      timeout: 2s
      assertions:
        - column: status
          expected: "pending"
        - column: total_amount
          type: "exists"
      failure_mode: "stop"
    
    # Layer 4: Verify cache invalidated
    - surface: cache
      command: DEL
      key: "user:123:orders:cached"
      timeout: 1s
      failure_mode: "continue"  # Cache miss is OK
    
    - surface: cache
      command: GET
      key: "user:123:orders:cached"
      timeout: 1s
      assertions:
        - type: "not_exists"
      failure_mode: "continue"
    
    # Layer 5: Verify search indexed
    - surface: search
      query: {"query": {"match": {"order_status": "pending"}}}
      timeout: 3s
      retry: {max_attempts: 5, delay_ms: 200}  # Search is eventually consistent
      assertions:
        - field: status
          expected: "pending"
      failure_mode: "continue"
    
    # Layer 6: Verify event published
    - surface: events
      topic: order-events
      timeout: 30s
      assertions:
        - field: event_type
          expected: "order.created"
        - field: order_id
          type: "exists"
      failure_mode: "stop"

timing_profile:
  total_expected: 50s  # Sequential, so sum of all timeouts
  profile: "safety_over_speed"
```

**When to use:**
- High assurance needed (production-critical flow)
- Scenario time is not critical
- Need to debug integration issues step-by-step
- New, untrusted service integration

**Cost:** 50-90 seconds per scenario

---

### Pattern 2: Parallel Verification with Waits (Balanced)

Web action, then parallel verification of independent services, then sequential for dependent ones. Balanced speed and assurance.

```yaml
scenario:
  name: "User creates order (parallel balanced)"
  coordination: "parallel_with_waits"
  steps:
    # Single action point (cannot parallelize)
    - surface: web
      action: click
      selector: "#create-order"
      timeout: 5s
      failure_mode: "stop"
    
    # Parallel—API and DB are independent after API writes
    - parallel:
        - surface: api
          method: GET
          endpoint: /order/last
          timeout: 5s
          assertions:
            - field: status
              expected: "pending"
          failure_mode: "stop"
        
        - surface: db
          query: "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1"
          timeout: 2s
          assertions:
            - column: status
              expected: "pending"
          failure_mode: "stop"
    
    # Sequential—Cache depends on DB write completing
    - surface: cache
      command: DEL
      key: "user:123:orders:cached"
      timeout: 1s
      failure_mode: "continue"
    
    # Sequential—Search depends on cache invalidation (for now)
    - surface: search
      query: {"query": {"match": {"order_status": "pending"}}}
      timeout: 3s
      retry: {max_attempts: 3, delay_ms: 100}
      failure_mode: "continue"
    
    # Sequential—Events are last (async from API)
    - surface: events
      topic: order-events
      timeout: 30s
      assertions:
        - field: event_type
          expected: "order.created"
      failure_mode: "continue"

timing_profile:
  total_expected: 45s  # Parallel phase reduces time
  profile: "balanced"
```

**When to use:**
- Speed and assurance both important
- Services have proven consistency guarantees
- Need to detect integration bugs but within reasonable time
- Stable, well-tested service boundaries

**Cost:** 30-50 seconds per scenario

---

### Pattern 3: Cascade Verification (Fast but Assumes Chain)

Assume services are correctly chained. Verify only the final state, not intermediate layers. Fastest pattern; assumes services work.

```yaml
scenario:
  name: "User creates order (cascade)"
  coordination: "cascade_verification"
  preconditions:
    # Document assumptions: services MUST be correctly integrated
    - "API correctly writes to DB (already tested in API unit tests)"
    - "DB writes trigger cache invalidation (via trigger or worker)"
    - "Cache invalidation triggers search refresh (via pub-sub)"
    - "Search refresh triggers Kafka publish (via webhook)"
  steps:
    # Action: Just web click
    - surface: web
      action: click
      selector: "#create-order"
      timeout: 5s
      failure_mode: "stop"
    
    # Checkpoint 1: DB is fastest verifiable persistence point
    - surface: db
      query: "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1"
      timeout: 2s
      assertions:
        - column: status
          expected: "pending"
      failure_mode: "stop"
    
    # Assume cache invalidation (don't verify, just wait)
    - wait_ms: 100  # Cache invalidation window
    
    # Assume search refresh (don't verify, just wait)
    - wait_ms: 200  # Search indexing window
    
    # Final verification: Event published (earliest place to verify whole chain)
    - surface: events
      topic: order-events
      timeout: 30s
      assertions:
        - field: event_type
          expected: "order.created"
      failure_mode: "stop"

timing_profile:
  total_expected: 35s
  profile: "speed_over_details"
  tradeoff: "Skips intermediate verification; fails fast if chain breaks"
```

**When to use:**
- Services have proven, tested integration
- Speed is critical (CI/CD gate on every commit)
- Intermediate failures are rare; focus on end-to-end
- Trust the contract tests (separate from integration eval)

**Cost:** 25-40 seconds per scenario

---

## 1. Load Drivers

Import and initialize all 6 eval drivers. Each driver exports a client and assertion functions.

```python
import sys
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Import all eval drivers
from eval_driver_web_cdp import CDPClient, launch_browser, navigate, interact, take_screenshot
from eval_driver_api_http import HTTPClient, request, verify_status, verify_json
from eval_driver_db_mysql import MySQLClient, execute_query, verify_rows, verify_value
from eval_driver_cache_redis import RedisClient, execute_command, verify_key, verify_ttl
from eval_driver_search_es import ESClient, index_document, search_query, verify_document
from eval_driver_bus_kafka import KafkaClient, produce_message, consume_message, verify_published

class MultiSurfaceEvaluator:
    """Coordinates multi-driver scenarios across web, API, DB, cache, search, events."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize all drivers from config.
        
        config = {
            'web': {'cdp_endpoint': 'http://localhost:9222'},
            'api': {'base_url': 'http://localhost:3000'},
            'db': {'host': 'localhost', 'user': 'root', 'password': '...'},
            'cache': {'host': 'localhost', 'port': 6379},
            'search': {'host': 'localhost', 'port': 9200},
            'events': {'brokers': ['localhost:9092']}
        }
        """
        self.config = config
        self.drivers = {}
        self.scenario_steps = []
        self.evidence = {
            'screenshots': [],
            'api_responses': [],
            'db_results': [],
            'cache_state': [],
            'search_results': [],
            'event_messages': []
        }
        self.timings = {}
        self.start_time = datetime.now()
```

## 2. Execute Scenario

Run step-by-step through all 6 services in sequence. Each step builds on previous state.

```python
    def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a multi-surface scenario.
        
        scenario = {
            'name': 'User enables 2FA',
            'steps': [
                {
                    'surface': 'web',
                    'action': 'navigate',
                    'target': '/2fa/setup'
                },
                {
                    'surface': 'web',
                    'action': 'type',
                    'selector': '#phone-input',
                    'value': '+1234567890'
                },
                {
                    'surface': 'web',
                    'action': 'click',
                    'selector': '#send-code-btn'
                },
                {
                    'surface': 'api',
                    'method': 'POST',
                    'endpoint': '/auth/2fa/enable',
                    'body': {'phone': '+1234567890'},
                    'expect_status': 201
                },
                {
                    'surface': 'db',
                    'query': 'SELECT * FROM users WHERE id = ?',
                    'params': [123],
                    'assertions': [
                        {'column': '2fa_enabled', 'expected': True},
                        {'column': 'phone', 'expected': '+1234567890'}
                    ]
                },
                {
                    'surface': 'cache',
                    'command': 'GET',
                    'key': 'user:123:2fa_codes',
                    'assertions': [
                        {'type': 'exists'},
                        {'type': 'ttl_gt', 'value': 300}
                    ]
                },
                {
                    'surface': 'search',
                    'query': {'query': {'match': {'user_id': 123}}},
                    'assertions': [
                        {'field': '2fa_enabled', 'expected': True},
                        {'field': 'indexed_at', 'type': 'exists'}
                    ]
                },
                {
                    'surface': 'events',
                    'topic': 'user-events',
                    'assertion': {'event_type': 'user.2fa_enabled', 'user_id': 123}
                }
            ]
        }
        """
        results = []
        failed = False
        
        # Step 1: Web actions via CDP
        for step in scenario['steps']:
            if step['surface'] == 'web':
                result = self._execute_web_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        # Step 2: API verification
        for step in scenario['steps']:
            if step['surface'] == 'api':
                result = self._execute_api_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        # Step 3: DB verification
        for step in scenario['steps']:
            if step['surface'] == 'db':
                result = self._execute_db_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        # Step 4: Cache verification
        for step in scenario['steps']:
            if step['surface'] == 'cache':
                result = self._execute_cache_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        # Step 5: Search verification
        for step in scenario['steps']:
            if step['surface'] == 'search':
                result = self._execute_search_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        # Step 6: Event verification
        for step in scenario['steps']:
            if step['surface'] == 'events':
                result = self._execute_event_step(step)
                results.append(result)
                if not result['success']:
                    failed = True
                    break
        
        return {
            'scenario': scenario['name'],
            'overall': 'FAIL' if failed else 'PASS',
            'steps': results
        }

    def _execute_web_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web action via CDP."""
        start = datetime.now()
        try:
            if step['action'] == 'navigate':
                result = navigate(self.drivers['web'], step['target'])
                screenshot = take_screenshot(self.drivers['web'])
                self.evidence['screenshots'].append({
                    'step': step['action'],
                    'target': step['target'],
                    'data': screenshot
                })
            elif step['action'] == 'type':
                result = interact(self.drivers['web'], 'type', step['selector'], step['value'])
            elif step['action'] == 'click':
                result = interact(self.drivers['web'], 'click', step['selector'])
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"web_{step['action']}"] = duration
            
            return {
                'surface': 'web',
                'action': step['action'],
                'success': True,
                'duration': duration,
                'result': result
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'web',
                'action': step['action'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def _execute_api_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call via HTTP."""
        start = datetime.now()
        try:
            response = request(
                self.drivers['api'],
                method=step['method'],
                endpoint=step['endpoint'],
                body=step.get('body')
            )
            
            success = response.status_code == step.get('expect_status', 200)
            
            self.evidence['api_responses'].append({
                'endpoint': step['endpoint'],
                'method': step['method'],
                'status': response.status_code,
                'body': response.json() if response.text else None
            })
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"api_{step['method']}_{step['endpoint']}"] = duration
            
            return {
                'surface': 'api',
                'method': step['method'],
                'endpoint': step['endpoint'],
                'success': success,
                'duration': duration,
                'status': response.status_code
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'api',
                'method': step['method'],
                'endpoint': step['endpoint'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def _execute_db_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query and verify results."""
        start = datetime.now()
        try:
            rows = execute_query(
                self.drivers['db'],
                step['query'],
                step.get('params', [])
            )
            
            assertions_passed = True
            assertion_results = []
            
            for assertion in step.get('assertions', []):
                if rows:
                    actual = rows[0].get(assertion['column'])
                    expected = assertion['expected']
                    passed = actual == expected
                    assertions_passed = assertions_passed and passed
                    assertion_results.append({
                        'column': assertion['column'],
                        'expected': expected,
                        'actual': actual,
                        'passed': passed
                    })
            
            self.evidence['db_results'].append({
                'query': step['query'],
                'rows': rows,
                'assertions': assertion_results
            })
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"db_query"] = duration
            
            return {
                'surface': 'db',
                'query': step['query'],
                'success': assertions_passed,
                'duration': duration,
                'rows_affected': len(rows),
                'assertions': assertion_results
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'db',
                'query': step['query'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def _execute_cache_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cache command and verify state."""
        start = datetime.now()
        try:
            value = execute_command(
                self.drivers['cache'],
                step['command'],
                step['key']
            )
            
            assertions_passed = True
            assertion_results = []
            
            for assertion in step.get('assertions', []):
                if assertion['type'] == 'exists':
                    passed = value is not None
                    assertion_results.append({
                        'type': 'exists',
                        'passed': passed
                    })
                    assertions_passed = assertions_passed and passed
                elif assertion['type'] == 'ttl_gt':
                    ttl = verify_ttl(self.drivers['cache'], step['key'])
                    passed = ttl > assertion['value']
                    assertion_results.append({
                        'type': 'ttl_gt',
                        'expected_gt': assertion['value'],
                        'actual': ttl,
                        'passed': passed
                    })
                    assertions_passed = assertions_passed and passed
            
            self.evidence['cache_state'].append({
                'key': step['key'],
                'value': value,
                'assertions': assertion_results
            })
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"cache_{step['command']}"] = duration
            
            return {
                'surface': 'cache',
                'command': step['command'],
                'key': step['key'],
                'success': assertions_passed,
                'duration': duration,
                'assertions': assertion_results
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'cache',
                'command': step['command'],
                'key': step['key'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def _execute_search_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search query and verify indexed document."""
        start = datetime.now()
        try:
            results = search_query(
                self.drivers['search'],
                step['query']
            )
            
            assertions_passed = True
            assertion_results = []
            
            if results:
                doc = results[0]
                for assertion in step.get('assertions', []):
                    if assertion['type'] == 'exists':
                        passed = assertion['field'] in doc
                    else:
                        actual = doc.get(assertion['field'])
                        expected = assertion.get('expected')
                        passed = actual == expected
                    
                    assertion_results.append({
                        'field': assertion.get('field'),
                        'expected': assertion.get('expected'),
                        'actual': doc.get(assertion.get('field')),
                        'passed': passed
                    })
                    assertions_passed = assertions_passed and passed
            else:
                assertions_passed = False
                assertion_results.append({'passed': False, 'reason': 'no_documents_found'})
            
            self.evidence['search_results'].append({
                'query': step['query'],
                'results': results,
                'assertions': assertion_results
            })
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"search_query"] = duration
            
            return {
                'surface': 'search',
                'query': step['query'],
                'success': assertions_passed,
                'duration': duration,
                'documents_found': len(results),
                'assertions': assertion_results
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'search',
                'query': step['query'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def _execute_event_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Verify event published to message bus."""
        start = datetime.now()
        try:
            messages = consume_message(
                self.drivers['events'],
                step['topic'],
                timeout=10
            )
            
            found = False
            for msg in messages:
                if all(msg.get(k) == v for k, v in step['assertion'].items()):
                    found = True
                    break
            
            self.evidence['event_messages'].append({
                'topic': step['topic'],
                'expected': step['assertion'],
                'messages_received': len(messages),
                'found': found
            })
            
            duration = (datetime.now() - start).total_seconds()
            self.timings[f"events_consume"] = duration
            
            return {
                'surface': 'events',
                'topic': step['topic'],
                'success': found,
                'duration': duration,
                'messages_checked': len(messages)
            }
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return {
                'surface': 'events',
                'topic': step['topic'],
                'success': False,
                'duration': duration,
                'error': str(e)
            }
```

## 3. Error Propagation

Identify failures, collect context, and decide whether to stop or retry.

```python
    def handle_failure(self, step_result: Dict[str, Any], step_index: int, scenario: Dict[str, Any]):
        """
        Handle step failure: identify, report, collect logs, decide action.
        """
        surface = step_result['surface']
        error = step_result.get('error', 'Unknown error')
        
        failure_report = {
            'step_index': step_index,
            'step_definition': scenario['steps'][step_index],
            'failed_service': surface,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'context': self._collect_failure_context(surface)
        }
        
        return failure_report
    
    def _collect_failure_context(self, surface: str) -> Dict[str, Any]:
        """Collect logs and state from failed service."""
        context = {}
        
        if surface == 'web':
            context['browser_logs'] = self.drivers['web'].get_logs()
            context['page_source'] = self.drivers['web'].get_page_source()
            context['screenshot'] = take_screenshot(self.drivers['web'])
        
        elif surface == 'api':
            context['last_response'] = self.evidence['api_responses'][-1] if self.evidence['api_responses'] else None
        
        elif surface == 'db':
            context['query_logs'] = self.drivers['db'].get_error_log()
            context['last_query'] = self.evidence['db_results'][-1] if self.evidence['db_results'] else None
        
        elif surface == 'cache':
            context['cache_stats'] = execute_command(self.drivers['cache'], 'INFO')
        
        elif surface == 'search':
            context['cluster_health'] = self.drivers['search'].get_cluster_health()
        
        elif surface == 'events':
            context['broker_info'] = self.drivers['events'].get_broker_info()
        
        return context
    
    def decide_retry(self, failure: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Decide whether to retry based on failure type.
        
        Returns: (should_retry, reason)
        """
        error = failure['error']
        
        # Transient errors: retry
        if 'timeout' in error.lower() or 'connection refused' in error.lower():
            return (True, 'transient_network_error')
        
        # Service unavailable: retry with backoff
        if 'service unavailable' in error.lower() or '503' in error:
            return (True, 'service_unavailable')
        
        # Data errors: don't retry
        if 'assertion' in error.lower() or 'expected' in error.lower():
            return (False, 'data_mismatch_no_retry')
        
        # Other errors: stop
        return (False, 'hard_failure')
```

## 4. Evidence Collection

Capture artifacts from each step: screenshots, responses, query results, cache state, search results, event messages.

```python
    def collect_all_evidence(self, scenario_name: str) -> Dict[str, Any]:
        """
        Gather all evidence across all steps.
        
        Returns dict with arrays of:
        - screenshots: {step, target, data}
        - api_responses: {endpoint, method, status, body}
        - db_results: {query, rows, assertions}
        - cache_state: {key, value, assertions}
        - search_results: {query, results, assertions}
        - event_messages: {topic, expected, messages_received, found}
        """
        evidence = {
            'scenario': scenario_name,
            'collected_at': datetime.now().isoformat(),
            'screenshots': self.evidence['screenshots'],
            'api_responses': self.evidence['api_responses'],
            'db_results': self.evidence['db_results'],
            'cache_state': self.evidence['cache_state'],
            'search_results': self.evidence['search_results'],
            'event_messages': self.evidence['event_messages']
        }
        return evidence
    
    def save_evidence(self, evidence: Dict[str, Any], output_dir: str):
        """Save all evidence artifacts to disk."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON evidence
        with open(f'{output_dir}/evidence.json', 'w') as f:
            json.dump(evidence, f, indent=2, default=str)
        
        # Save screenshots
        for i, screenshot in enumerate(evidence['screenshots']):
            with open(f'{output_dir}/screenshot_{i}.png', 'wb') as f:
                f.write(screenshot['data'])
        
        # Save response bodies
        with open(f'{output_dir}/api_responses.json', 'w') as f:
            json.dump(evidence['api_responses'], f, indent=2)
        
        # Save query results
        with open(f'{output_dir}/db_results.json', 'w') as f:
            json.dump(evidence['db_results'], f, indent=2, default=str)
```

## 5. Report Generation

Output overall pass/fail, per-step results, evidence, and timing metrics.

```python
    def generate_report(self, scenario_results: Dict[str, Any], evidence: Dict[str, Any]) -> str:
        """
        Generate human-readable evaluation report.
        
        Shows:
        - Scenario name and overall result (PASS/FAIL)
        - Per-step result: success/failure/reason
        - Evidence: screenshots, logs, responses
        - Timing: how long each step took
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"SCENARIO: {scenario_results['scenario']}")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall result
        overall = scenario_results['overall']
        symbol = "✅" if overall == "PASS" else "❌"
        lines.append(f"OVERALL: {overall} {symbol}")
        lines.append("")
        
        # Per-step results
        lines.append("STEP RESULTS:")
        lines.append("-" * 80)
        
        total_duration = 0
        for i, step in enumerate(scenario_results['steps'], 1):
            surface = step['surface']
            success = step['success']
            duration = step.get('duration', 0)
            total_duration += duration
            
            status = "✅ PASS" if success else "❌ FAIL"
            
            if surface == 'web':
                lines.append(f"{i}. WEB {step['action'].upper()}")
                if success:
                    lines.append(f"   {status} | {duration:.2f}s")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            elif surface == 'api':
                lines.append(f"{i}. API {step['method']} {step['endpoint']}")
                if success:
                    lines.append(f"   {status} | Status {step['status']} | {duration:.2f}s")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            elif surface == 'db':
                lines.append(f"{i}. DB QUERY")
                if success:
                    lines.append(f"   {status} | {step['rows_affected']} rows | {duration:.2f}s")
                    for assertion in step['assertions']:
                        check = "✓" if assertion['passed'] else "✗"
                        lines.append(f"      {check} {assertion['column']}: {assertion['expected']}")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            elif surface == 'cache':
                lines.append(f"{i}. CACHE {step['command']} {step['key']}")
                if success:
                    lines.append(f"   {status} | {duration:.2f}s")
                    for assertion in step['assertions']:
                        check = "✓" if assertion['passed'] else "✗"
                        lines.append(f"      {check} {assertion}")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            elif surface == 'search':
                lines.append(f"{i}. SEARCH QUERY")
                if success:
                    lines.append(f"   {status} | {step['documents_found']} docs | {duration:.2f}s")
                    for assertion in step['assertions']:
                        check = "✓" if assertion['passed'] else "✗"
                        lines.append(f"      {check} {assertion['field']}")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            elif surface == 'events':
                lines.append(f"{i}. EVENTS {step['topic']}")
                if success:
                    lines.append(f"   {status} | {step['messages_checked']} msgs checked | {duration:.2f}s")
                else:
                    lines.append(f"   {status} | Error: {step['error']}")
            
            lines.append("")
        
        # Timing summary
        lines.append("-" * 80)
        lines.append(f"TOTAL EXECUTION TIME: {total_duration:.2f}s")
        lines.append("")
        
        # Evidence summary
        lines.append("EVIDENCE COLLECTED:")
        lines.append("-" * 80)
        lines.append(f"  Screenshots: {len(evidence['screenshots'])}")
        lines.append(f"  API Responses: {len(evidence['api_responses'])}")
        lines.append(f"  DB Results: {len(evidence['db_results'])}")
        lines.append(f"  Cache State: {len(evidence['cache_state'])}")
        lines.append(f"  Search Results: {len(evidence['search_results'])}")
        lines.append(f"  Event Messages: {len(evidence['event_messages'])}")
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def print_report(self, scenario_results: Dict[str, Any], evidence: Dict[str, Any]):
        """Print report to stdout."""
        report = self.generate_report(scenario_results, evidence)
        print(report)
    
    def save_report(self, scenario_results: Dict[str, Any], evidence: Dict[str, Any], filepath: str):
        """Save report to file."""
        report = self.generate_report(scenario_results, evidence)
        with open(filepath, 'w') as f:
            f.write(report)


# Example usage
if __name__ == '__main__':
    config = {
        'web': {'cdp_endpoint': 'http://localhost:9222'},
        'api': {'base_url': 'http://localhost:3000'},
        'db': {'host': 'localhost', 'user': 'root', 'password': 'password'},
        'cache': {'host': 'localhost', 'port': 6379},
        'search': {'host': 'localhost', 'port': 9200},
        'events': {'brokers': ['localhost:9092']}
    }
    
    evaluator = MultiSurfaceEvaluator(config)
    
    # Load and run scenario
    with open('scenario.json') as f:
        scenario = json.load(f)
    
    results = evaluator.run_scenario(scenario)
    evidence = evaluator.collect_all_evidence(scenario['name'])
    
    # Output
    evaluator.print_report(results, evidence)
    evaluator.save_report(results, evidence, 'report.txt')
    evaluator.save_evidence(evidence, 'evidence/')
```

## Usage Pattern

```bash
# Run a scenario file
eval-coordinate-multi-surface scenario.json

# Run with custom output directory
eval-coordinate-multi-surface scenario.json --output ./results/

# Run and generate report
eval-coordinate-multi-surface scenario.json --report report.txt

# Run with evidence collection
eval-coordinate-multi-surface scenario.json --save-evidence ./evidence/
```

## Scenario Example

```json
{
  "name": "User enables 2FA",
  "steps": [
    {
      "surface": "web",
      "action": "navigate",
      "target": "/2fa/setup"
    },
    {
      "surface": "web",
      "action": "type",
      "selector": "#phone-input",
      "value": "+1234567890"
    },
    {
      "surface": "web",
      "action": "click",
      "selector": "#send-code-btn"
    },
    {
      "surface": "api",
      "method": "POST",
      "endpoint": "/auth/2fa/enable",
      "body": {"phone": "+1234567890"},
      "expect_status": 201
    },
    {
      "surface": "db",
      "query": "SELECT * FROM users WHERE id = ?",
      "params": [123],
      "assertions": [
        {"column": "2fa_enabled", "expected": true},
        {"column": "phone", "expected": "+1234567890"}
      ]
    },
    {
      "surface": "cache",
      "command": "GET",
      "key": "user:123:2fa_codes",
      "assertions": [
        {"type": "exists"},
        {"type": "ttl_gt", "value": 300}
      ]
    },
    {
      "surface": "search",
      "query": {"query": {"match": {"user_id": 123}}},
      "assertions": [
        {"field": "2fa_enabled", "expected": true},
        {"field": "indexed_at", "type": "exists"}
      ]
    },
    {
      "surface": "events",
      "topic": "user-events",
      "assertion": {"event_type": "user.2fa_enabled", "user_id": 123}
    }
  ]
}
```

## Report Output

```
================================================================================
SCENARIO: User enables 2FA
================================================================================

OVERALL: PASS ✅

STEP RESULTS:
--------------------------------------------------------------------------------
1. WEB NAVIGATE
   ✅ PASS | 0.34s

2. WEB TYPE
   ✅ PASS | 0.12s

3. WEB CLICK
   ✅ PASS | 0.15s

4. API POST /auth/2fa/enable
   ✅ PASS | Status 201 | 0.08s

5. DB QUERY
   ✅ PASS | 1 rows | 0.02s
      ✓ 2fa_enabled: true
      ✓ phone: +1234567890

6. CACHE GET user:123:2fa_codes
   ✅ PASS | 0.01s
      ✓ exists
      ✓ ttl_gt: 300

7. SEARCH QUERY
   ✅ PASS | 1 docs | 0.03s
      ✓ 2fa_enabled
      ✓ indexed_at

8. EVENTS user-events
   ✅ PASS | 1 msgs checked | 0.45s

--------------------------------------------------------------------------------
TOTAL EXECUTION TIME: 1.20s

EVIDENCE COLLECTED:
--------------------------------------------------------------------------------
  Screenshots: 3
  API Responses: 1
  DB Results: 1
  Cache State: 1
  Search Results: 1
  Event Messages: 1

================================================================================
```

## Best Practices: Service Coordination

Apply these principles to every multi-surface scenario:

### Principle 1: Timeouts Are Service Contracts
Every timeout value should be justified, not guessed. Each timeout represents a promise: "This service will respond in X milliseconds under normal load."

- Measure P95 latency from monitoring
- Add 20% buffer for variance
- Document the contract: `"API timeout 5s = P95 latency 4s + 20% variance buffer"`
- If measured P95 exceeds contract, renegotiate timeout or split work

Example:
```yaml
api_timeout: 5s  # Contract: API responds within 5s
# Justification: Measured P95 latency = 4.1s (from 7-day monitoring), 
#                + 20% buffer = 4.92s, rounded to 5s
```

### Principle 2: Services Fail Independently
Assume any service can be down or slow. Don't assume one service being slow means it's overloaded; it could be a network partition affecting only that service.

- Plan for: API slow but DB fast (API bottleneck)
- Plan for: DB slow but API fast (DB bottleneck)
- Plan for: Both slow (cascade)
- Plan for: One down entirely (health check failure)
- Test both happy path and degraded paths

Example test matrix:
```
[ ] API fast, DB fast → should pass
[ ] API slow (5s), DB fast → should still pass (within timeout)
[ ] API fast, DB slow (2s) → should still pass
[ ] API down, DB fast → should fail gracefully (precondition)
[ ] API fast, DB down → should fail gracefully (precondition)
```

### Principle 3: Integration Is Where Bugs Hide
Unit tests pass. Integration tests fail. This is normal and expected.

- Unit test: API endpoint returns 200 ✓
- Integration test: Web calls API, API calls DB, DB is down ✗

Coordination catches these bugs:
- Unit test: API writes to DB ✓
- Integration test: API writes to DB, cache doesn't invalidate ✗
- Coordination test: Web → API → DB → Cache → Search → Events all correct ✓

### Principle 4: State Visibility Is Evidence
Screenshots, logs, and database snapshots prove what happened. They are not nice-to-have; they are mandatory for debugging.

For every critical step:
- Web: Before and after screenshot
- API: Request and response body
- DB: Query result (actual rows)
- Cache: Key contents before and after
- Search: Indexed document before and after
- Events: Message body and topic

Never report failure without evidence. "DB assertion failed" is useless without showing: "Query returned 0 rows, expected [row data]."

Example evidence requirement:
```yaml
steps:
  - surface: api
    method: POST
    endpoint: /order
    body: {product_id: 123, quantity: 2}
    
  - collect_evidence:  # Mandatory
      - api_response_body
      - api_response_headers
      - api_response_timing
  
  - surface: db
    query: "SELECT * FROM orders WHERE product_id = 123"
    
  - collect_evidence:  # Mandatory
      - query_result
      - query_execution_time
      - row_count
```

### Principle 5: Cascade Failures Are the Enemy
One service failing should not bring down the entire scenario unless it's designed to.

- Use `failure_mode: "stop"` for critical paths (web → API → DB → Events)
- Use `failure_mode: "continue"` for optional paths (cache, search)
- Document which failures are optional and why

Example:
```yaml
steps:
  - surface: api
    failure_mode: "stop"  # If API fails, everything fails
  
  - surface: db
    failure_mode: "stop"  # If DB fails, cascade to search/cache failure
  
  - surface: cache
    failure_mode: "continue"  # Cache miss is OK, DB is source of truth
  
  - surface: search
    failure_mode: "continue"  # Search not available? OK, DB still queryable
```

### Principle 6: Async Operations Need Explicit Waits
Never assume async operations are complete. Kafka, cache invalidation, search indexing—all are eventually consistent.

- Wait explicitly with timeout and retry
- Never assume "it should be done by now"
- Document the consistency window (P95 time to consistent)

Example:
```yaml
- surface: api
  method: POST
  endpoint: /order
  
# WRONG: No wait for async operations
# - surface: search
#   query: order-search  # Might not be indexed yet

# RIGHT: Explicit wait with retry
- wait_for_consistency:
    service: search
    check: "Search index contains new order"
    timeout: 3s
    retry:
      max_attempts: 5
      delay_ms: 100  # 100ms, 200ms, 300ms, 400ms, 500ms
```

## Dependencies

- **eval-driver-web-cdp**: CDP client for browser automation
- **eval-driver-api-http**: HTTP client for API testing
- **eval-driver-db-mysql**: MySQL client for database verification
- **eval-driver-cache-redis**: Redis client for cache verification
- **eval-driver-search-es**: Elasticsearch client for search verification
- **eval-driver-bus-kafka**: Kafka client for event verification

## Checklist

Before claiming completion:

- [ ] All surfaces listed in the scenario YAML have been driven (none skipped)
- [ ] Surfaces were executed in scenario-defined order (not reordered or short-circuited)
- [ ] Every step produced a concrete evidence entry (not empty or "N/A")
- [ ] DB and cache verified after every write-triggering web or API action
- [ ] Scenario timeout is at or below the SLA defined in shared-dev-spec
- [ ] All service health checks passed before first scenario step executed
- [ ] stack-down called unconditionally after scenario completes (pass or fail)
- [ ] Multi-surface result payload passed to eval-judge for final verdict
