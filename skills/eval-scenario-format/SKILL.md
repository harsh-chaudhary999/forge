---
name: eval-scenario-format
description: "Define YAML format for eval scenarios. Steps: driver action, target, expected result. Executable format for multi-surface eval."
type: rigid
requires: [brain-read]
---

# Eval Scenario Format

## Why Scenarios Matter: Blocking Rationalizations

Before skipping scenarios, understand what you're risking. The following rationalizations are red flags masking deeper engineering debt:

| Rationalization | The Truth |
|---|---|
| "Scenarios are flaky, let's skip eval and ship" | Flakiness in scenarios is a symptom, not a reason to skip. It's telling you something is timing-dependent or non-deterministic. Triage it: Is it a slow API? A race condition? Network timing? Fix the root cause, don't hide it. |
| "Our system is too complex for scenarios" | Complexity is exactly why scenarios matter. Scenarios catch integration breaks that unit tests miss. Without them, you discover bugs in production. Simple systems need unit tests; complex systems need scenarios. |
| "API tests are enough, we don't need UI scenarios" | API tests don't catch UI state mismanagement, race conditions, or timing issues that emerge only in the full stack. A 200 OK from your API doesn't prove the UI rendered correctly or that the user's browser event fired. |
| "Scenarios slow down development" | Without scenarios, you merge broken code and debug in production. Scenarios cost 2-5 hours upfront per feature; production firefighting costs 20+ hours. You're choosing between two time investments. Pick the one that pays you back. |
| "We'll add scenarios after launch" | You won't. Window of opportunity closes the moment code is live. Eval is only safe, fast, and useful during development. Post-launch, you're always one prod outage away from "ship now, test later." Don't set that trap. |

**Authority principle:** These truths come from 20+ years of post-mortems where "we skipped eval" was the root cause.

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A scenario `expected:` field contains prose description instead of concrete, assertable value** — "User sees their order" is not assertable. STOP. Every `expected:` must be a specific, machine-verifiable value: HTTP status code, exact element text, DB row count, Kafka message payload.
- **A scenario covers more than one distinct user journey** — Compound scenarios produce ambiguous failure signals: when the scenario fails, it's unclear which journey is broken. STOP. One scenario = one user journey. Split multi-journey scenarios into individual entries.
- **Scenario steps contain `wait: 5s` hardcoded delays instead of condition polling** — Fixed waits are timing-dependent and cause flakiness: too short on slow machines, too long in CI. STOP. Use explicit readiness conditions (HTTP health check, element visible, message received) instead of arbitrary sleep.
- **A scenario references a driver not listed in the product's eval stack** — A driver not in the product stack cannot be executed; the scenario will fail with "unknown driver" at runtime. STOP. Verify every `driver:` value in the scenario against `forge-product.md` before saving.
- **`on_failure:` field is absent from scenario steps that call external services** — Without a failure policy, a timed-out external call leaves the scenario in an undefined state. STOP. Every step calling an external service must specify `on_failure: stop` or `on_failure: continue` explicitly.
- **Scenario file is not committed to brain before eval runs** — An uncommitted scenario file may be modified between eval runs, making results non-reproducible. STOP. Commit the scenario file to `~/forge/brain/prds/<task-id>/` before invoking eval.

## Overview

The eval scenario format is a declarative YAML specification for defining multi-surface user journey tests. Each scenario describes a sequence of driver actions across web, API, database, cache, search, and message bus layers, with clear expected results and failure handling policies.

Scenarios are executable by `eval-coordinate-multi-surface` and support comprehensive validation across an entire system's execution surface.

## Schema

### Root Level

```yaml
scenario: string          # Scenario name (required)
description: string       # Human-readable description (required)
preconditions: string[]   # List of conditions that must be true before scenario execution
steps: Step[]             # Ordered list of driver actions (required, min 1)
postconditions: string[]  # List of expected conditions after successful execution
metadata:                 # Optional metadata
  timeout: number         # Timeout for entire scenario (seconds)
  tags: string[]          # Feature tags (e.g. "2fa", "critical", "smoke")
  priority: string        # Priority level: "critical", "high", "medium", "low"
  author: string          # Who defined this scenario
```

### Step Object

Each step represents a single driver action with expected outcomes.

```yaml
- id: string              # Unique step identifier (required, format: "step_N")
  driver: string          # Driver type (required)
  action: string          # Driver-specific action (required)
  description: string     # Optional human-readable description
  timeout: number         # Step timeout in seconds (optional, inherits from metadata)
  retry:                  # Optional retry policy
    policy: string        # "none", "fixed", "exponential"
    max_attempts: number  # Maximum retry attempts
    delay_ms: number      # Base delay for fixed/exponential
    backoff_factor: number # For exponential (default: 2)
  failure_mode: string    # "stop", "continue", "log" (default: "stop")
  # Driver-specific fields follow...
  expected: object        # Driver-specific expected result (required)
```

## Driver Types and Actions

### 1. Web Driver (web-cdp)

Uses Chrome DevTools Protocol for browser automation.

#### Navigate Action
```yaml
- id: "step_1"
  driver: "web-cdp"
  action: "navigate"
  url: "http://localhost:3001/settings/security"
  wait_for: "document_ready"  # "document_ready", "network_idle", "selector"
  wait_selector: "button[data-testid=submit]"  # Required if wait_for="selector"
  expected:
    status: "loaded"  # "loaded", "error", "timeout"
    title_contains: "Security"
    url_matches: "/settings/security"
```

#### Click Action
```yaml
- id: "step_2"
  driver: "web-cdp"
  action: "click"
  selector: "button[data-testid=enable-2fa]"  # CSS selector
  wait_for_visible: true  # Wait for element to be visible before clicking
  expected:
    visible: true
    clickable: true
    title_changed: true  # Optional: verify DOM changed
```

#### Type Action
```yaml
- id: "step_3"
  driver: "web-cdp"
  action: "type"
  selector: "input[name=phone]"
  value: "+1234567890"
  clear_first: true  # Clear field before typing
  expected:
    value: "+1234567890"
    input_event_fired: true
```

#### Scroll Action
```yaml
- id: "step_4"
  driver: "web-cdp"
  action: "scroll"
  direction: "down"  # "up", "down", "left", "right"
  amount: 500  # pixels
  selector: "#section-id"  # Optional: scroll within element
  expected:
    scroll_position_changed: true
```

#### Screenshot Action
```yaml
- id: "step_5"
  driver: "web-cdp"
  action: "screenshot"
  selector: "#main-content"  # Optional: screenshot specific element
  expected:
    captured: true
    not_blank: true
```

#### GetDOM Action
```yaml
- id: "step_6"
  driver: "web-cdp"
  action: "getDOM"
  selector: "#results"  # CSS selector
  expected:
    element_count: 5
    has_text: "Success"
    html_contains: "<button"
    attribute_value:
      data-test-id: "results-container"
```

#### Wait Action
```yaml
- id: "step_7"
  driver: "web-cdp"
  action: "wait"
  condition: "selector"  # "selector", "attribute", "text"
  selector: ".loading-spinner"
  timeout_ms: 5000
  expected:
    condition_met: true
```

### 2. HTTP API Driver (api-http)

Makes HTTP requests and validates responses.

#### Call Action
```yaml
- id: "step_8"
  driver: "api-http"
  action: "call"
  method: "POST"  # GET, POST, PUT, PATCH, DELETE, HEAD
  url: "http://api.localhost:3000/auth/2fa/enable"
  headers:
    Authorization: "Bearer token123"
    Content-Type: "application/json"
  body:
    phone: "+1234567890"
    method: "sms"
  auth_type: "bearer"  # "none", "bearer", "basic", "apikey"
  auth_token: "token123"
  timeout_ms: 5000
  expected:
    status: 201
    status_in: [200, 201]  # Accept multiple statuses
    response_has_field: "secret"
    response_field_value:
      success: true
      code_length: 6
    content_type: "application/json"
    headers_contain:
      X-RateLimit-Remaining: /^\d+$/  # Regex validation
```

#### Verify Action
```yaml
- id: "step_9"
  driver: "api-http"
  action: "verify"
  method: "GET"
  url: "http://api.localhost:3000/users/123/2fa"
  expected:
    status: 200
    response_schema:  # JSON Schema validation
      type: "object"
      properties:
        enabled:
          type: "boolean"
        backup_codes:
          type: "array"
          minItems: 5
```

### 3. MySQL Database Driver (db-mysql)

Executes queries and verifies database state.

#### Execute Action
```yaml
- id: "step_10"
  driver: "db-mysql"
  action: "execute"
  query: |
    UPDATE user_2fa 
    SET enabled = 1, verified_at = NOW()
    WHERE user_id = 123
  timeout_ms: 5000
  expected:
    rows_affected: 1
    query_success: true
```

#### Verify Action
```yaml
- id: "step_11"
  driver: "db-mysql"
  action: "verify"
  query: |
    SELECT COUNT(*) as count, enabled 
    FROM user_2fa 
    WHERE user_id = 123
  expected:
    rows_returned: 1
    count: 1
    enabled: 1
    row_contains:
      enabled: 1
      verified_at: /\d{4}-\d{2}-\d{2}/  # Regex match
```

### 4. Redis Cache Driver (cache-redis)

Interacts with Redis key-value store.

#### Execute Action
```yaml
- id: "step_12"
  driver: "cache-redis"
  action: "execute"
  command: "SET"
  key: "user:123:2fa_codes"
  value: "123456,234567,345678"
  options:
    EX: 300  # Expire in 300 seconds
    NX: true  # Only if not exists
  expected:
    success: true
    response: "OK"
```

#### Verify Action
```yaml
- id: "step_13"
  driver: "cache-redis"
  action: "verify"
  key: "user:123:2fa_codes"
  expected:
    exists: true
    value_contains: "123456"
    ttl: 300
    ttl_range: [295, 305]  # TTL between 295-305 seconds
    type: "string"
```

### 5. Elasticsearch Search Driver (search-es)

Indexes and searches documents.

#### Index Action
```yaml
- id: "step_14"
  driver: "search-es"
  action: "index"
  index: "users"
  doc_id: "123"
  document:
    id: 123
    username: "alice"
    email: "alice@example.com"
    2fa_enabled: true
  refresh: true  # Immediately refresh index
  expected:
    indexed: true
    doc_id: "123"
```

#### Search Action
```yaml
- id: "step_15"
  driver: "search-es"
  action: "search"
  index: "users"
  query:
    bool:
      must:
        - term:
            id: 123
        - match:
            username: "alice"
  expected:
    found: true
    hits: 1
    result_has_field: "2fa_enabled"
    result_field_value:
      2fa_enabled: true
```

#### Verify Action
```yaml
- id: "step_16"
  driver: "search-es"
  action: "verify"
  index: "users"
  query:
    term:
      id: 123
  expected:
    found: true
    has_field: "2fa_enabled"
    field_value:
      2fa_enabled: true
```

### 6. Kafka Message Bus Driver (bus-kafka)

Produces and verifies messages on topics.

#### Produce Action
```yaml
- id: "step_17"
  driver: "bus-kafka"
  action: "produce"
  topic: "user-lifecycle"
  key: "user:123"
  message:
    event_type: "user.2fa_enabled"
    user_id: 123
    timestamp: "2025-02-10T14:30:00Z"
    source: "settings-service"
  partition: 0  # Optional: target specific partition
  expected:
    produced: true
    partition_assigned: 0
```

#### Consume Action
```yaml
- id: "step_18"
  driver: "bus-kafka"
  action: "consume"
  topic: "user-lifecycle"
  assertion:
    event_type: "user.2fa_enabled"
    user_id: 123
  timeout_ms: 5000
  max_messages: 10  # Max messages to consume before timeout
  expected:
    found: true
    message_count: 1
```

#### Verify Action
```yaml
- id: "step_19"
  driver: "bus-kafka"
  action: "verify"
  topic: "user-lifecycle"
  assertion:
    event_type: "user.2fa_enabled"
    user_id: 123
  expected:
    found: true
    message_matches:
      event_type: "user.2fa_enabled"
      source: "settings-service"
```

## Complete Example Scenario

```yaml
scenario: "User enables 2FA with email verification"
description: |
  Complete user journey for enabling two-factor authentication.
  Covers web UI, API, database, cache, search, and Kafka event bus.

preconditions:
  - "User is logged in with valid session"
  - "User is on settings/security page"
  - "2FA is not already enabled"

steps:
  # Step 1: Navigate to 2FA settings
  - id: "step_1"
    driver: "web-cdp"
    action: "navigate"
    url: "http://localhost:3001/settings/security"
    wait_for: "document_ready"
    timeout: 10
    expected:
      status: "loaded"
      title_contains: "Security Settings"

  # Step 2: Click enable 2FA button
  - id: "step_2"
    driver: "web-cdp"
    action: "click"
    selector: "button[data-testid=enable-2fa]"
    wait_for_visible: true
    timeout: 5
    expected:
      visible: true
      clickable: true

  # Step 3: Dialog appears and we input phone number
  - id: "step_3"
    driver: "web-cdp"
    action: "type"
    selector: "input[name=phone]"
    value: "+14155551234"
    clear_first: true
    timeout: 3
    expected:
      value: "+14155551234"
      input_event_fired: true

  # Step 4: Submit the form via API
  - id: "step_4"
    driver: "api-http"
    action: "call"
    method: "POST"
    url: "http://api.localhost:3000/auth/2fa/enable"
    headers:
      Authorization: "Bearer eyJhbGc..."
      Content-Type: "application/json"
    body:
      phone: "+14155551234"
      method: "sms"
    timeout_ms: 5000
    expected:
      status: 201
      response_has_field: "secret"
      response_field_value:
        success: true
        expires_in: 300

  # Step 5: Verify database record created
  - id: "step_5"
    driver: "db-mysql"
    action: "verify"
    query: |
      SELECT id, user_id, enabled, verified_at 
      FROM user_2fa 
      WHERE user_id = 123 
      AND method = 'sms'
    timeout_ms: 3000
    expected:
      rows_returned: 1
      enabled: 0  # Not verified yet
      verified_at: null

  # Step 6: Verify cache has temporary secret
  - id: "step_6"
    driver: "cache-redis"
    action: "verify"
    key: "2fa:setup:123:secret"
    timeout_ms: 2000
    expected:
      exists: true
      type: "string"
      ttl_range: [290, 300]  # Must expire within 300s

  # Step 7: Index user in search
  - id: "step_7"
    driver: "search-es"
    action: "verify"
    index: "users"
    query:
      term:
        id: 123
    timeout_ms: 3000
    expected:
      found: true
      has_field: "2fa_setup_in_progress"
      field_value:
        2fa_setup_in_progress: true

  # Step 8: Verify event published to Kafka
  - id: "step_8"
    driver: "bus-kafka"
    action: "verify"
    topic: "user-lifecycle"
    assertion:
      event_type: "user.2fa_setup_initiated"
      user_id: 123
    timeout_ms: 5000
    expected:
      found: true
      message_matches:
        user_id: 123
        event_type: "user.2fa_setup_initiated"
        phone: "+14155551234"

  # Step 9: Screenshot confirmation
  - id: "step_9"
    driver: "web-cdp"
    action: "screenshot"
    selector: "#2fa-setup-dialog"
    timeout: 2
    expected:
      captured: true
      not_blank: true

postconditions:
  - "2FA setup modal is displayed"
  - "SMS code was sent to +14155551234"
  - "User record is in database with pending verification"
  - "Event published to user-lifecycle topic"
  - "Cache entry has 5-minute TTL"

metadata:
  timeout: 60  # 60 seconds total scenario timeout
  tags: ["2fa", "critical", "registration-flow"]
  priority: "critical"
  author: "platform-team"
```

## Edge Cases in Scenario Execution

Scenarios operate in the real world: networks fail, caches get stale, timing is unpredictable. Know how to handle these six critical edge cases.

### Edge Case 1: Flaky Test (Timing-Dependent Assertion)
**What:** Web driver waits for element but the element appears after timeout due to slow network, slow JavaScript, or background rendering.

**Example:** You set `timeout: 3000` for a button to appear, but on a slow CI runner it takes 3100ms.

**Action:**
- Use `wait` action with realistic timeout based on P95 latency of your system, not P50
- Pair with exponential retry: `policy: "exponential"`, `max_attempts: 3`
- Timeout should account for network variance, not just happy-path rendering

```yaml
- id: "step_click_button"
  driver: "web-cdp"
  action: "wait"
  condition: "selector"
  selector: "button[data-testid=submit]"
  timeout_ms: 8000  # P95 latency, not P50
  retry:
    policy: "exponential"
    max_attempts: 3
    delay_ms: 500
    backoff_factor: 2
```

**Fallback:** If retry exhausted, fail step with diagnostic: capture screenshot, dump DOM, log network waterfall. This data is your evidence for why the flake happened.

---

### Edge Case 2: Async Operations Without Sync Point
**What:** API returns 200 OK but background job (event processing, cache invalidation, search indexing) hasn't completed yet. Eventual consistency is real; your scenario isn't.

**Example:** You POST `/users/123`, get 200, then immediately verify the user appears in search results. But Elasticsearch reindex is async and takes 500ms.

**Action:**
- Never assert immediately after an async operation
- Use `wait` action to poll cache/search index until fresh
- Set timeout to reasonable SLA for that async operation (e.g., "messages publish within 5s", "search reindex within 2s")

```yaml
- id: "step_1_create_user"
  driver: "api-http"
  action: "call"
  method: "POST"
  url: "http://api.localhost:3000/users"
  body: { name: "Alice" }
  expected:
    status: 201

- id: "step_2_wait_for_search_index"
  driver: "web-cdp"
  action: "wait"  # Poll until search returns result
  condition: "selector"
  selector: "input[data-testid=search]"
  timeout_ms: 5000  # Elasticsearch SLA: reindex within 5s
  retry:
    policy: "exponential"
    max_attempts: 5

- id: "step_3_verify_search"
  driver: "search-es"
  action: "search"
  index: "users"
  query: { term: { name: "Alice" } }
  expected:
    found: true
```

**Fallback:** If wait times out, the async operation is not meeting SLA. Escalate as infrastructure issue, not flaky test. Record the timeout for observability.

---

### Edge Case 3: Multiple Valid Outcomes (Non-Deterministic)
**What:** System legitimately returns different valid outcomes. SMS vs email for 2FA code. Different payment processors. Multiple language translations.

**Example:** "Send 2FA code" might send via SMS on high load but via email on low load. Both are correct.

**Action:**
- Use `status_in: [200, 201]` for HTTP status flexibility
- Use `response_in: [value_a, value_b]` for response content flexibility
- Document in scenario description why multiple outcomes are valid

```yaml
- id: "step_send_2fa"
  driver: "api-http"
  action: "call"
  method: "POST"
  url: "http://api.localhost:3000/auth/2fa/send"
  expected:
    status_in: [200, 201]  # Both OK
    response_field_value:
      delivery_method_in: ["sms", "email"]  # Either method is valid
      code_length: 6
```

**Fallback:** If result is neither valid outcome, fail the step. Don't add more "valid" outcomes just to make scenario pass. Distinguish between "system is flexible" (good) and "test doesn't know what it's validating" (bad).

---

### Edge Case 4: External Service Timeout (Database Down, Kafka Down)
**What:** You call a critical service and it times out. Is this a transient network blip or permanent failure?

**Example:** Kafka broker is overloaded. Message produce times out. 500ms later, it succeeds. Or it's permanently down.

**Action:**
- Distinguish transient (retry) from permanent (escalate)
- Use `failure_mode: "log"` on non-critical verifies so one service down doesn't fail entire scenario
- Use `failure_mode: "stop"` on critical path (e.g., user creation must succeed)
- Use exponential retry for transient failures: backoff gives overwhelmed service time to recover

```yaml
- id: "step_publish_event"
  driver: "bus-kafka"
  action: "produce"
  topic: "user-lifecycle"
  message: { event_type: "user.created" }
  retry:
    policy: "exponential"
    max_attempts: 3
    delay_ms: 500
    backoff_factor: 2
  failure_mode: "stop"  # If Kafka is down, entire feature is broken

- id: "step_log_to_analytics"
  driver: "api-http"
  action: "call"
  method: "POST"
  url: "http://analytics.localhost:3000/log"
  body: { event: "user.created" }
  failure_mode: "log"  # If analytics is down, don't block user creation
```

**Fallback:** 
- If transient retry exhausted: escalate to ops. Log which service timed out, when, and how many retries failed.
- If permanent failure: scenario cannot validate that code path. Mark as "infrastructure unavailable" and skip.

---

### Edge Case 5: Race Condition (Concurrent Updates)
**What:** Two parallel requests update the same record. Which wins? What state do you verify?

**Example:** User clicks "enable 2FA" twice. Two concurrent POST requests. Both succeed. Is DB record duplicated? Is one an idempotent no-op?

**Action:**
- Document preconditions carefully: "User session is exclusive" or "API idempotent key prevents duplicates"
- For single-threaded scenarios: precondition should guarantee no concurrency
- For multi-threaded scenarios: use database locks or compare-and-set semantics

```yaml
preconditions:
  - "User session is exclusive (no concurrent requests)"
  - "API supports idempotent keys (POSTs use Idempotency-Key header)"

steps:
  - id: "step_enable_2fa_first"
    driver: "api-http"
    action: "call"
    method: "POST"
    url: "http://api.localhost:3000/users/123/2fa/enable"
    headers:
      Idempotency-Key: "req-uuid-1"  # Same UUID = idempotent
    expected:
      status: 201

  - id: "step_enable_2fa_duplicate"
    driver: "api-http"
    action: "call"
    method: "POST"
    url: "http://api.localhost:3000/users/123/2fa/enable"
    headers:
      Idempotency-Key: "req-uuid-1"  # Same UUID = should return cached 201
    expected:
      status: 201  # Idempotent response, not error
```

**Fallback:** If outcomes differ (first succeeds, second fails), race condition exists. Escalate to backend team. Scenario cannot validate concurrent access; that needs separate load-test scenarios.

---

### Edge Case 6: Stale Cache Invalidation
**What:** You update a record in database. Cache wasn't invalidated. Scenario reads stale data.

**Example:** POST /users/123 to update email. API succeeds. Then GET /cache/user:123 returns old email.

**Action:**
- Use `wait` action to poll cache until fresh (poll until new value appears or TTL refresh completes)
- Set timeout to cache invalidation SLA (e.g., "cache must refresh within 2s")
- Verify cache version/timestamp, not just presence

```yaml
- id: "step_update_user"
  driver: "api-http"
  action: "call"
  method: "PUT"
  url: "http://api.localhost:3000/users/123"
  body: { email: "newemail@example.com" }
  expected:
    status: 200

- id: "step_wait_cache_refresh"
  driver: "cache-redis"
  action: "verify"
  key: "user:123"
  timeout_ms: 3000  # Cache invalidation SLA: 3 seconds
  retry:
    policy: "exponential"
    max_attempts: 5
    delay_ms: 200
  expected:
    exists: true
    value_contains: "newemail@example.com"  # Must be fresh value
```

**Fallback:** If cache never refreshes, it's an infrastructure issue (cache invalidation broken). Escalate to platform team. Scenario passes if you successfully polled and found fresh value within SLA.

---

## Validation Rules

### Step ID Format
- Must match pattern: `step_\d+`
- Must be unique within scenario
- Recommended to use sequential numbering: step_1, step_2, etc.

### Driver and Action Combinations
Valid combinations:

| Driver | Actions |
|--------|---------|
| web-cdp | navigate, click, type, scroll, screenshot, getDOM, wait |
| api-http | call, verify |
| db-mysql | execute, verify |
| cache-redis | execute, verify |
| search-es | index, search, verify |
| bus-kafka | produce, consume, verify |

### Expected Result Fields

**Common across all drivers:**
- `success: boolean` - Generic success indicator
- `error: string` - Optional error message if assertion fails

**Web (web-cdp):**
- `status: string` - "loaded", "error", "timeout"
- `visible: boolean` - Element visibility
- `value: string` - Input field value
- `attribute_value: object` - Element attributes
- `element_count: number` - Count of matched elements
- `html_contains: string` - HTML substring match

**HTTP (api-http):**
- `status: number` - HTTP status code
- `response_has_field: string` - Response JSON field
- `content_type: string` - Response MIME type

**Database (db-mysql):**
- `rows_affected: number` - Rows modified by execute
- `rows_returned: number` - Rows returned by query
- `[column_name]: value` - Direct column assertions

**Cache (cache-redis):**
- `exists: boolean` - Key exists
- `value: string` - Key value
- `ttl: number` - TTL in seconds
- `type: string` - Redis data type

**Search (search-es):**
- `found: boolean` - Document found
- `hits: number` - Number of hits
- `has_field: string` - Field exists

**Message Bus (bus-kafka):**
- `found: boolean` - Message found
- `message_count: number` - Number of matching messages
- `partition_assigned: number` - Partition assignment

### Retry Policies

```yaml
retry:
  policy: "fixed"        # "none", "fixed", "exponential"
  max_attempts: 3        # Total attempts
  delay_ms: 1000         # Base delay
  backoff_factor: 2      # For exponential only
```

**none:** No retries
**fixed:** Retry with constant delay
**exponential:** Retry with exponential backoff

### Failure Modes

- `stop`: Halt scenario execution, report failure
- `continue`: Log failure, continue with next step
- `log`: Log only, no explicit failure tracking

## Usage

Scenarios are executed by `eval-coordinate-multi-surface`:

```bash
eval-coordinate-multi-surface scenario.yaml
```

Output includes:
- Overall pass/fail status
- Per-step execution results
- Assertion failures with details
- Retry history
- Total execution time
- Screenshots (if captured)

## Best Practices

1. **Preconditions must be testable:** Every precondition must be verifiable in a setup step. "User is authenticated" is vague; "User has valid session token matching auth database" is testable. Vague preconditions hide bugs.

2. **Scenario completeness is non-negotiable:** Don't ship code without end-to-end scenario coverage. Use `failure_mode: "stop"` for all critical assertions. If a scenario passes 9/10 steps then fails on the critical assertion, it's a failed scenario. You don't get partial credit in production.

3. **Flakiness is a data point, not an excuse:** If a scenario fails intermittently, DON'T disable it. Triage it. Does it fail on Friday afternoons (resource contention)? On CI but not local (environment difference)? During load (scaling issue)? The flakiness is telling you something. Transient? Use exponential retry. Permanent bug? Fix the bug, not the test.

4. **Timeouts are evidence of performance claims:** Every timeout value is a claim about your system's performance. 500ms means "this endpoint responds in P95 < 500ms." If scenario times out, investigate: Is the endpoint slow? Is the network slow? Is the database slow? Don't increase the timeout; fix the system. Document why each timeout value exists.

5. **Screenshots prove execution:** Always include screenshot actions on critical UI assertions. They're your evidence when you need to triage a failure. A screenshot showing "form never appeared" tells you more than "visible: false" alone.

6. **IDs:** Use meaningful step identifiers for debugging
7. **Failure Modes:** Use `continue` strategically for non-critical validations (e.g., analytics logging), never for critical path
8. **Assertions:** Be specific in expected results; avoid overly broad checks
9. **Metadata:** Tag scenarios for easy filtering and reporting (critical vs smoke, regression vs new feature)
10. **Documentation:** Use `description` fields for clarity on why each assertion matters
11. **Cross-Surface:** Leverage multiple drivers to validate full system behavior—don't stop at API success

## Debugging Failed Scenarios

When a scenario fails, you have evidence. Use it systematically.

### Step 1: Check Screenshots
If your scenario includes `action: "screenshot"` steps (and critical UI assertions should), examine them first.
- Is the DOM rendered at all?
- Are form fields visible?
- Is the error message displayed?
- Screenshots are your first evidence of whether the UI behaved as expected.

### Step 2: Review Retry History
If a step has `retry` configured, check how many attempts it took to pass (or how many times it failed).
- Passed on attempt 1? No flakiness.
- Passed on attempt 3? Step is timing-dependent. Increase timeout or investigate why system is slow.
- Failed all attempts? Permanent failure, not flakiness. This is a real bug.

### Step 3: Check Logs for External Service Timeouts
Scenarios often call external services (databases, caches, Kafka, Elasticsearch). When a step fails:
- Was there a timeout from a downstream service?
- Is Kafka broker down? Redis unreachable? Database locked?
- External service down = infrastructure issue. Escalate to ops, don't blame code.
- Code bug = fix the code, then re-run scenario to confirm fix.

Example failure signatures:
- `timeout: true, service: "kafka"` = Message bus is slow or down
- `timeout: true, service: "db-mysql"` = Database query is slow or connection pool exhausted
- `timeout: true, driver: "web-cdp"` = Browser is slow or network is slow

### Step 4: Escalate or Fix
- **Infrastructure issue (service down, slow):** Escalate to ops. Scenario correctly failed because system can't run. Re-run after ops fixes the service.
- **Code bug (assertion failure, wrong status code):** Fix the code. Re-run scenario to confirm fix.
- **Flaky test (intermittent timing):** Add `wait` action with realistic timeout, or increase retry attempts.

### Step 5: Document the Root Cause
Record what you found:
- "Database query was N+1, took 5 seconds instead of 500ms. Fixed query. Scenario now passes in 500ms."
- "Kafka broker was out of disk. Ops cleaned up. Scenario passes."
- "Race condition in cache invalidation. Added lock to write path. Scenario consistently passes."

This data feeds back into your observability and helps future developers avoid the same trap.

---

## Migration Guides

### From Manual Test Cases
Replace manual steps with driver actions and expected assertions in YAML format.

### From Puppeteer/Playwright Scripts
Convert JavaScript automation to declarative `web-cdp` actions with structured expected results.

### From Postman Collections
Map Postman requests to `api-http` call/verify actions with response validation.
