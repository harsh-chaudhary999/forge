---
name: self-heal-locate-fault
description: "WHEN: An eval scenario has failed. Parse eval output, trace the failure chain backwards to the root service, and collect logs and state as evidence."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "locate the fault"
  - "find where eval failed"
  - "which service failed"
allowed-tools:
  - Bash
---

# Self-Heal: Locate Fault

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The error message says which service failed" | Error messages report symptoms, not causes. A 500 from the API may be caused by a cache miss, a DB timeout, or a Kafka lag. |
| "It's probably the service I just changed" | Confirmation bias. The change you made may have exposed a pre-existing bug in a different service. Follow the evidence. |
| "I'll just re-run the eval and see if it passes" | Flaky passes hide real bugs. Diagnose first, fix, then verify. A green re-run without diagnosis is a time bomb. |
| "The logs are too noisy, I'll guess" | Guessing wastes self-heal loop iterations. Filter logs by timestamp and request ID to find the actual failure chain. |
| "Multiple services failed, so it's an environment issue" | Multi-service failures often have a single root cause (e.g., one service returning bad data that cascades). Find the first failure in the chain. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
FAULT LOCATION TRACES THE FAILURE CHAIN BACKWARDS TO THE FIRST FAILURE IN THE TIMELINE. THE LAST SERVICE TO LOG AN ERROR IS NOT THE ROOT. FOLLOW REQUEST IDs AND TIMESTAMPS — NOT INTUITION.
```

## HARD-GATE Anti-Patterns (Critical Enforcement)

### Anti-Pattern 1: "The Last Service in the Eval Output is the Fault Source"

**Why It Fails:** Last output often reflects a downstream cascade effect, not the root cause. The root cause is almost always upstream—the service that failed first, which caused the downstream failures.

**Enforcement (5 MUST bullets):**

- **MUST trace failure chain backwards** — Start from failing assertion, work backwards through call graph using request IDs and timestamps
- **MUST check timing across all services** — Root cause has the earliest failure timestamp; downstream cascades happen later
- **MUST follow causality arrows** — Identify which service's failure triggered the next service's failure (e.g., null response → downstream NullPointerException)
- **MUST compare log patterns** — Root cause produces logs that precede all other error logs by 100+ ms; cascades produce simultaneous logs
- **MUST verify with request ID trace** — Use correlation IDs to follow a single request through the call chain; the first service that logged the error is the fault source

**Example of failure:** Eval output shows cache service error last. Tracing backwards finds API service returned stale data 500ms earlier. Cache was responding normally but to poisoned data from API. API is the root cause.

---

### Anti-Pattern 2: "Just Read the Top-Level Error Message"

**Why It Fails:** Top-level error messages are user-facing abstractions designed for readability, not diagnosis. Root cause is buried in nested exception chains, caused_by fields, or stack trace context layers.

**Enforcement (5 MUST bullets):**

- **MUST unwrap full exception stack** — Do not stop at the first error message. Extract complete nested exceptions: error.cause, error.caused_by, error.inner_exception
- **MUST parse error chain completely** — Read from outermost (user-facing) to innermost (root technical cause). Example: "Request failed" → "Connection timeout" → "ECONNREFUSED" → "Port not listening"
- **MUST extract root exception type** — Innermost exception type is most specific. "NullPointerException at line 156" beats "Internal Server Error"
- **MUST check for wrapped exceptions** — Many frameworks wrap errors; unwrap at least 3 layers deep. Search for keywords: "caused by", "inner exception", "nested error", "error chain"
- **MUST correlate message with stack trace** — Match the error message to a specific file:line in the stack trace. If no match, error message is user-facing abstraction; dig deeper into stack

**Example of failure:** Top-level says "Database error". Unwrapping finds "Connection pool exhausted" → "Max connections (10) reached" → actual root is connection leak in another service. Top-level hid the real cause.

---

### Anti-Pattern 3: "If Logs Are Empty, the Fault is in the Code"

**Why It Fails:** Empty logs for the failure window typically indicate the service never received the request (routing failure), not a code bug. Code always produces logs when it executes; silence means the request never arrived.

**Enforcement (5 MUST bullets):**

- **MUST check network connectivity** — Before concluding code fault, verify service received traffic: check network interfaces, routing tables, firewall rules, load balancer logs
- **MUST trace request routing** — Use request ID to track request through ingress → API gateway → load balancer → service. If request doesn't appear in any layer, routing failed
- **MUST verify service is listening** — Service may not be bound to the correct port, or the address may be 127.0.0.1 instead of 0.0.0.0. Check service logs from startup, netstat output, lsof
- **MUST examine network layer logs** — If app logs are empty, check infrastructure logs: Docker logs, Kubernetes logs, network device logs, reverse proxy logs
- **MUST expand log time window** — Logs may be rotated or buffered. Expand window to ±60s from failure time, check log rotation timestamps, check buffering in place

**Example of failure:** Web-to-API call produces no API logs. "Code must be broken." Actually: API binding to localhost only; web (in different container) cannot reach it. Networking issue, not code.

---

### Anti-Pattern 4: "Pattern Matching Against a Single Error is Sufficient"

**Why It Fails:** Identical error messages can occur from completely different code paths and faults. Error string alone is not unique; full context (stack trace, code location, surrounding logs) is required to distinguish root causes.

**Enforcement (5 MUST bullets):**

- **MUST collect full call stack context** — Do not diagnose from error message only. Extract stack trace showing exactly which file:line threw the error
- **MUST compare complete stack traces** — Same error string from two different stack traces = two different root causes. Example: "NullPointerException" from auth middleware vs database layer are different bugs
- **MUST fingerprint by code location** — Use file:line as primary identifier, not error message. Build fingerprint from: (filename, line_number, function_name, error_type)
- **MUST cross-reference surrounding logs** — Look at logs 5-10 seconds before the error for setup context. Different setup paths → different root causes despite identical error message
- **MUST archive new patterns** — If error message doesn't match known patterns, collect full context and archive as new pattern for future lookups

**Example of failure:** "Connection refused" is seen in both outbound database connection and external service API call. Same message; completely different roots. Stack trace reveals one is in db.connect() and other is in webhooks.post(). Two different faults.

---

### Anti-Pattern 5: "Infrastructure Faults Don't Produce Application Logs"

**Why It Fails:** Infrastructure failures always produce application-level logs. When infrastructure fails (network down, disk full, OOM), the application always logs the effect: connection timeout, ECONNREFUSED, disk write failure, memory allocation error. Infra faults are observable through app logs.

**Enforcement (5 MUST bullets):**

- **MUST search for secondary indicators** — Infra faults manifest as: ECONNREFUSED, ETIMEDOUT, ENOBUFS, "No space left on device", "Out of memory", "Too many open files", DNS resolution failures
- **MUST check system timestamps** — Infra faults often have precise timestamp markers: disk/memory spikes, network packet loss, CPU throttling. Cross-reference app error timestamp with system metrics
- **MUST trace cascading effects** — Infra failure in one service produces timeout in dependent services. Look for: first service logs infra symptom (e.g., ECONNREFUSED), downstream services log timeout waiting for it
- **MUST examine resource limits** — Check kernel limits, container limits, process limits at fault timestamp. Many "mysterious failures" are actually hitting hard limits set at deployment
- **MUST correlate with infrastructure events** — Check load balancer health checks, container orchestration logs, auto-scaler events, deployment logs at exact error timestamp

**Example of failure:** "Service X is buggy" based on error logs. Actually: node running low on disk, kernel killing processes, service never even got to run user code. Infra fault, observable through "too many open files" in logs, but misattributed to service code.

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Fault is attributed to the most recently changed service without log evidence** — Confirmation bias. STOP. Trace the failure chain from the failing assertion back through the call graph using actual logs.
- **"Multiple services failed" is used to conclude "environment issue" without finding the root** — Multi-service cascades have a single root cause. STOP. Find the first failure in the chain by timestamp.
- **Fault location is stated as "probably Service X" without a request ID trace** — Probability without evidence is a guess. STOP. Find the request ID in the failing eval output and follow it through logs.
- **Only the last log line is examined** — Failures log their cause before their effect. STOP. Search logs 30+ seconds before the failure time for the root event.
- **Fault is declared "unknown" after one log search** — Unknown fault = insufficient log collection. STOP. Expand log collection to all services, not just the reported failing one.
- **Re-running eval before completing fault location** — Passing on re-run hides intermittent bugs. STOP. Complete fault location and triage before re-running eval.

When an eval scenario fails, this skill diagnoses which service caused the failure and collects evidence for remediation.

## Overview

The skill performs three sequential operations:
1. **Parse Eval Output** — Extract failure step, error message, and context
2. **Identify Fault** — Determine which service/component failed
3. **Collect Evidence** — Gather logs, stack traces, request/response bodies, and state

## Algorithm

### Parse Eval Output

Read the eval scenario output and extract:
- **Scenario name**: Which eval scenario failed
- **Failed step**: Which step in the scenario triggered the failure
- **Error type**: HTTP status, exception, timeout, assertion failure
- **Error message**: Full error text
- **Context**: Request payload, expected result, actual result
- **Timeline**: When the error occurred relative to other steps

```
Input: eval-output.log or eval-result.json
├── Check for HTTP errors (4xx, 5xx responses)
├── Check for exception stack traces
├── Check for timeout errors
├── Check for assertion/validation failures
└── Extract error context and surrounding steps
```

### Identify Fault

Map the failure to a service or component using causal reasoning:

#### Pattern 1: HTTP Error Codes
```
Status Code → Service
400, 401, 403 → Client error or auth service
404 → API routing or endpoint not found
422 → Validation service or input processor
500, 502, 503 → Backend API service
504 → Gateway timeout, likely upstream service
```

#### Pattern 2: Data Inconsistency
```
Scenario                          → Fault
API returned 200 but DB didn't    → Database service
  update row
Web displayed data but DB shows   → Database service or
  different value                   cache consistency
Request accepted but notification → Event bus or
  not delivered                     notification service
Cache hit but data was stale      → Cache invalidation
                                    or TTL service
```

#### Pattern 3: Service Chain Failures
```
Web → API → DB
├── Web error (render, CDN, routing) → Web service
├── API error (500, exception) → Backend API service
├── DB error (constraint, timeout) → Database service
├── No response from API → API service or network
└── Slow response (timeout) → Slowest service in chain
```

#### Pattern 4: External Dependencies
```
Error                         → Fault
Third-party API timeout       → External service
Rate limit exceeded           → External service quota
Authentication token invalid  → Auth/token service
Webhook delivery failed       → Event bus or
                               notification service
Cache connection refused      → Cache service
Search index not responding   → Search service
```

### Collect Evidence

For the identified fault service, gather:

#### Logs
- Last 50 lines of service logs
- Filter for ERROR, FATAL, WARN levels
- Include timestamps and context
- Identify repeating patterns or cascading failures

#### Stack Traces
- Full exception stack trace if available
- File names, line numbers, function names
- Call stack showing where error originated
- Any nested exceptions

#### Request/Response Data
- Full HTTP request (method, URL, headers, body)
- Full HTTP response (status, headers, body)
- Query parameters and path variables
- Authentication headers (redacted if sensitive)

#### Database State
- Last N rows affected by the failed operation
- Query that failed
- Constraint violations or data type mismatches
- Transaction state (committed, rolled back, pending)
- Locks or deadlocks

#### Cache State
- Cache key that was accessed
- Expected vs actual cached value
- Cache TTL and expiration
- Hit/miss ratio for the scenario
- Invalidation events

#### Service State
- Service health status (up/down/degraded)
- Resource usage (CPU, memory, connections)
- Active connections or pending requests
- Configuration values relevant to the error

### Output Fault Diagnosis

Format the diagnosis clearly with these sections:

```yaml
fault_diagnosis:
  service: "<service-name>:<port>"
  status: "failed"
  
  error:
    type: "<exception-type or http-status>"
    message: "<error-message>"
    step: "<scenario-step-that-failed>"
    
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "<log-line>"
        file: "<source-file>:<line>"
      
    stack_trace:
      - function: "<function-name>"
        file: "<filename>"
        line: <line-number>
        context: "<code-context>"
    
    request:
      method: "POST"
      url: "/endpoint"
      headers: { ... }
      body: { ... }
    
    response:
      status: 500
      headers: { ... }
      body: { ... }
    
    db_state:
      query: "<failed-query>"
      error: "<constraint-or-syntax-error>"
      affected_rows: <count>
      transaction_state: "rolled_back"
    
    cache_state:
      key: "<cache-key>"
      expected_value: "..."
      actual_value: "..."
      ttl_remaining: <seconds>
      was_hit: false
  
  actionable:
    root_cause: "<what-actually-broke>"
    immediate_fix: "<how-to-fix-now>"
    prevention: "<how-to-prevent-next-time>"
    affected_flows: ["<flow-1>", "<flow-2>"]
```

## Example Diagnoses

### Example 1: Backend API Fault
```yaml
fault_diagnosis:
  service: "backend-api:3000"
  status: "failed"
  
  error:
    type: "InternalServerError"
    message: "POST /auth/2fa/enable returned 500"
    step: "Enable 2FA on user account"
  
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "Error: 2FA secret generation failed"
        file: "auth.js:123"
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "Cannot read property 'base32' of undefined"
        file: "auth.js:125"
    
    stack_trace:
      - function: "generateSecret"
        file: "auth.js"
        line: 123
        context: "const encoded = speakeasy.totp.base32Encode(secret)"
      - function: "enableTwoFactor"
        file: "auth.js"
        line: 156
    
    request:
      method: "POST"
      url: "/auth/2fa/enable"
      body: { phone: "+1234567890", method: "sms" }
    
    response:
      status: 500
      body: { error: "Internal Server Error" }
  
  actionable:
    root_cause: "speakeasy library not imported or undefined"
    immediate_fix: "Add: const speakeasy = require('speakeasy')"
    prevention: "Add unit tests for auth.js, check imports in CI"
    affected_flows: ["2FA setup", "login with 2FA"]
```

### Example 2: Database Fault
```yaml
fault_diagnosis:
  service: "mysql:3306"
  status: "failed"
  
  error:
    type: "ConstraintViolation"
    message: "Duplicate entry for user_id in profile table"
    step: "Update user profile after registration"
  
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:16Z"
        level: "ERROR"
        message: "Duplicate entry '12345' for key 'uk_user_id'"
    
    db_state:
      query: "INSERT INTO user_profile (user_id, name) VALUES (?, ?)"
      error: "ER_DUP_ENTRY: Duplicate entry '12345' for key 'uk_user_id'"
      affected_rows: 0
      transaction_state: "rolled_back"
  
  actionable:
    root_cause: "Unique constraint violation—profile already exists for user"
    immediate_fix: "Check if profile exists before INSERT, use UPSERT instead"
    prevention: "Add integration tests for duplicate profile scenarios"
    affected_flows: ["User registration", "Profile updates"]
```

### Example 3: Cache Fault
```yaml
fault_diagnosis:
  service: "redis:6379"
  status: "failed"
  
  error:
    type: "StaleDataError"
    message: "Cache verification failed—expected '{role:admin}' but got '{role:user}'"
    step: "Verify admin cache after role upgrade"
  
  evidence:
    cache_state:
      key: "user:12345:roles"
      expected_value: { role: "admin" }
      actual_value: { role: "user" }
      ttl_remaining: 3599
      was_hit: true
  
  actionable:
    root_cause: "Cache not invalidated when user role was updated"
    immediate_fix: "Add cache.delete('user:12345:roles') to role update handler"
    prevention: "Implement cache invalidation triggers on role changes"
    affected_flows: ["Permission checks", "Authorization"]
```

## Edge Cases (Critical Scenarios)

### Edge Case 1: No Logs for the Failure Window

**Symptom:** Eval timestamps present (failure occurred at 14:32:15Z), but no log entries exist within ±30 seconds of failure time.

**Why This Happens:**
- Log rotation occurred between failure and diagnosis
- Service restarted and lost in-memory logs
- Logging level set too high (only FATAL, not ERROR)
- Logs directed to stdout but service was backgrounded
- Time synchronization issue across services

**Do NOT:**
- Assume "no logs" = "code is fine, must be infra"
- Skip to next service without checking
- Conclude fault is unknown

**Action Steps:**
1. Check log file timestamps — when was the most recent log written?
2. Run: `ls -la /var/log/SERVICE` to see log rotation schedule
3. Check if service was restarted during eval window (check process start time)
4. Expand time window to ±60 seconds, then ±120 seconds
5. Check if logs are being written to different destination (stdout, cloud logging, syslog)
6. Search for ERROR patterns across all services in expanded window

**When to Escalate:** If logs remain empty after expansion:
- **NEEDS_INFRA_CHANGE** — Log configuration or disk space issue
- Next action: Check disk space, log rotation policy, logging level configuration
- Escalate to: Infrastructure team if space issue; development team if configuration issue

---

### Edge Case 2: Multiple Services Log Same Error at Same Timestamp

**Symptom:** api-service, backend-service, and db-service all log "ECONNREFUSED" at exactly 14:32:15.123Z

**Why This Happens:**
- Root cause in one service (e.g., db-service crashes)
- All dependent services simultaneously get connection refused
- All attempt to log the error in parallel, timestamps align
- This is cascading failure, not multiple independent failures

**Do NOT:**
- Blame all three services
- Assume distributed system failure (Consul, Etcd, service mesh)
- Conclude it's a network partition

**Action Steps:**
1. Sort all ERROR logs by service by exact timestamp (include milliseconds)
2. Find the service with the earliest log timestamp — this is likely the root
3. If timestamps are identical (to the millisecond), find which service logged first in chronological order (file write order)
4. Check the log message content: which error is most fundamental? (e.g., "process crashed" vs "connection refused")
5. Trace the request ID: which service was first to receive the request?
6. Build causal chain: Service A fails → triggers failure in Service B → triggers failure in Service C

**When to Escalate:** If timeline is ambiguous:
- **NEEDS_COORDINATION** — Determine true causal chain across services
- Next action: Implement distributed tracing (OpenTelemetry, Jaeger) to get precise ordering
- Escalate to: Platform/SRE team for tracing infrastructure

---

### Edge Case 3: Error Fingerprint Missing from Pattern Library

**Symptom:** Error message encountered: "Error: handle_json_decode failed" — does not match any known pattern in fault library

**Why This Happens:**
- New code path not seen before
- Third-party library updated and produces new error format
- Unusual combination of conditions (e.g., corrupted file + concurrent access)
- Custom error thrown by recent change

**Do NOT:**
- Emit diagnosis with empty root cause
- Skip this error in favor of "known" errors
- Assume it's a one-off flake

**Action Steps:**
1. Parse full error message and stack trace (even though pattern unknown)
2. Extract error type, file path, line number, function name
3. Use generic stack trace parsing to identify fault service and code location
4. Annotate diagnosis with: `"pattern_status": "NEW_PATTERN"`
5. Log the complete error context to pattern library for future reference
6. Proceed with diagnosis based on code location and surrounding logs

**When to Escalate:** If diagnosis is unclear from stack trace alone:
- **NEEDS_CONTEXT** — Cannot determine root cause from code location alone
- Next action: Inspect the code at the error location; check git blame to see what changed
- Escalate to: Developer who last modified the code at that location

---

### Edge Case 4: Log Timestamps Not Synchronized Across Services

**Symptom:** Service A logs failure at 09:00:01.000Z, Service B logs ECONNREFUSED at 09:00:05.000Z for the same logical event. Should be simultaneous but 4-second gap.

**Why This Happens:**
- Service clocks are not synchronized via NTP
- One service's clock is drifting (clock skew)
- Docker containers have different system times
- Kubernetes nodes have different time sources
- CI/test environment with synthetic time advancement

**Do NOT:**
- Use log order as causal order (Service A first → Service A is root cause)
- Assume the gap is the time for request transit
- Assume clocks are correct

**Action Steps:**
1. Check NTP/time sync status on all hosts: `timedatectl status`, `ntpq -p`
2. Compare system time across all services: `date` from each service's logs or host
3. Calculate clock skew: (Service B timestamp) - (Service A timestamp)
4. Apply skew correction when ordering events (add ± margin of ±2 seconds to all timestamps)
5. Re-order events using adjusted timestamps
6. Identify root cause using corrected timeline

**When to Escalate:** If clock skew is large (>5 seconds):
- **NEEDS_CONTEXT** — System clocks not synchronized, cannot trust log order
- Next action: Enable NTP on all hosts, restart services, re-run eval
- Escalate to: Infrastructure/DevOps team to fix time synchronization

---

### Edge Case 5: Silent Fault (No Error Logged, Eval Fails)

**Symptom:** Eval assertion fails (returns wrong data) but all services log "200 OK" or "Request processed successfully". No errors in any log.

**Why This Happens:**
- Business logic bug (code runs without crashing but produces wrong output)
- Data corruption in database (stale or incorrect data returned)
- Cache serving stale/poisoned data
- Race condition that only manifests under specific timing
- Validation layer skipped, allowing bad data through

**Do NOT:**
- Blame infra ("infra faults don't produce silent errors")
- Conclude "logs are clean, so no fault"
- Assume eval scenario is wrong

**Action Steps:**
1. Compare database state before eval and after eval failure
2. Run: `SELECT * FROM TABLE WHERE id=X` before/after eval to see if data changed incorrectly
3. Trace data flow through logic layers: Which transformation produces wrong output?
4. Check cache contents: Is stale data being served? (use Redis: `GET key`)
5. Check for race conditions: Did multiple requests modify same row simultaneously?
6. Add debug logging to logic layers to trace data transformations
7. Check for validation bugs: Did validation layer let invalid data through?

**When to Escalate:** If data flow and logic are correct but output is still wrong:
- **BLOCKED** — Silent failure requires application-level investigation, not log analysis
- Next action: Add detailed logging to identify which business logic layer produces wrong data; run eval with additional instrumentation
- Escalate to: Development team for code-level debugging

---

## Decision Tree: Evidence Collection Strategy

Use this tree to determine which log/state sources to query based on fault fingerprint type.

```
START: Fault Fingerprint Type Identified?
│
├─ HTTP Status Code Error (4xx, 5xx, timeout)
│  │
│  ├─ 400, 401, 403, 422
│  │  └─ Query: API request logs, auth service logs, validation service logs
│  │     Collect: Request body, auth headers, validation rules
│  │     Evidence Type: Request/Response Data + Logs
│  │
│  ├─ 404, 405, 406
│  │  └─ Query: API routing logs, endpoint definitions, CDN logs
│  │     Collect: Request URL, available endpoints, routing rules
│  │     Evidence Type: Request/Response Data + Service State
│  │
│  ├─ 500, 502, 503
│  │  └─ Query: Backend service logs, exception traces, upstream service logs
│  │     Collect: Full stack trace, request payload, downstream responses
│  │     Evidence Type: Logs + Stack Traces + Request/Response Data
│  │
│  └─ 504, timeout
│     └─ Query: Upstream service logs, network logs, resource usage at timeout moment
│        Collect: Service response times, resource exhaustion signs, connection states
│        Evidence Type: Logs + Service State
│
├─ Exception / Stack Trace Error
│  │
│  ├─ NullPointerException / TypeError / ReferenceError
│  │  └─ Query: Service logs for the file/line, code context around error location
│  │     Collect: Stack trace, variable states, recent code changes
│  │     Evidence Type: Stack Traces + Code Context
│  │
│  ├─ Network Error (ECONNREFUSED, ENOTFOUND, ETIMEDOUT)
│  │  └─ Query: Downstream service logs, network configuration, connectivity checks
│  │     Collect: Service up/down status, routing rules, firewall rules
│  │     Evidence Type: Service State + Network Logs
│  │
│  ├─ Constraint Violation / Database Error
│  │  └─ Query: Database logs, transaction logs, schema definitions
│  │     Collect: Failed query, constraint rules, data state
│  │     Evidence Type: DB State + Logs
│  │
│  └─ Out of Memory / Too Many Open Files / Disk Full
│     └─ Query: System resource logs, container logs, process resource limits
│        Collect: Memory usage, file descriptor count, disk space
│        Evidence Type: Service State + System Metrics
│
├─ Data Inconsistency (200 OK but wrong data)
│  │
│  ├─ Cache stale / Cache poisoned
│  │  └─ Query: Cache hit/miss logs, cache invalidation logs, upstream data source
│  │     Collect: Cache key, expected vs actual value, TTL, data source state
│  │     Evidence Type: Cache State + Request/Response Data
│  │
│  ├─ Database inconsistency
│  │  └─ Query: Database transaction logs, concurrent update logs, replication logs
│  │     Collect: Row state before/after, concurrent modifications, transaction boundaries
│  │     Evidence Type: DB State + Logs
│  │
│  └─ Business logic bug
│     └─ Query: Application logic logs, transformation logs, data flow logs
│        Collect: Input data, transformation steps, output data
│        Evidence Type: Logs + Request/Response Data
│
├─ External Service Failure
│  │
│  ├─ Third-party API timeout
│  │  └─ Query: Outbound request logs, external service status page, network logs
│  │     Collect: Request to external service, response time, service status
│  │     Evidence Type: Logs + Request/Response Data
│  │
│  ├─ Rate limit exceeded
│  │  └─ Query: API call frequency logs, rate limit configuration
│  │     Collect: Call count in time window, rate limit threshold
│  │     Evidence Type: Logs + Service State
│  │
│  └─ Authentication token invalid
│     └─ Query: Auth service logs, token validation logs, token expiry logs
│        Collect: Token payload, expiry time, auth validation rules
│        Evidence Type: Logs + Request/Response Data
│
└─ Unknown / No Clear Fingerprint
   └─ Query: All service logs in eval window, cross-service timing correlation
      Collect: Aggregate errors, timeline reconstruction, log patterns
      Evidence Type: Logs + Timeline Analysis
```

---

## Quick Reference Card

| Evidence Type | Where to Find | Fault Category Indicator | Query Command |
|---|---|---|---|
| **HTTP Status Logs** | API gateway, reverse proxy, service HTTP handler | Client errors (4xx) indicate API layer; server errors (5xx) indicate backend | `grep "POST\|GET" /var/log/api.log \| grep "200\|4[0-9]{2}\|5[0-9]{2}"` |
| **Exception Stack Traces** | Application error logs, exception handlers, APM tools | File:line shows exact code location; exception type shows error category | `grep -A 10 "Exception\|Error\|Traceback" /var/log/app.log` |
| **Network Errors** | System logs, service logs for connection attempts | ECONNREFUSED = port not listening; ENOTFOUND = DNS failure; ETIMEDOUT = unreachable | `grep "ECONNREFUSED\|ENOTFOUND\|ETIMEDOUT\|EAGAIN" /var/log/*.log` |
| **Database Errors** | Database logs, application logs from DB driver | Constraint violations indicate schema/data issues; timeouts indicate resource exhaustion | `grep "Duplicate\|Constraint\|deadlock\|timeout" /var/log/mysql.log` |
| **Request ID Trace** | All service logs filtered by correlation ID | Follow a single request through call chain; first error is root cause | `grep -r "request_id=ABC123" /var/log/ \| sort` |
| **Cache State** | Redis/Memcache logs, cache client logs, cache monitoring | Cache miss = not cached; stale = TTL expired but not refreshed; poisoned = cached wrong value | `redis-cli GET key; redis-cli TTL key` |
| **Timestamp Alignment** | Log timestamps from all services | Clock skew >100ms indicates NTP issue; aligned timestamps enable causal ordering | `grep "2026-04-10T14:32:15" /var/log/*/service.log` |
| **Resource Exhaustion** | System metrics, container metrics, process resource limits | OOM, ENOBUFS, "too many open files" = resource limits hit | `free -h; ulimit -a; du -sh /var/log/` |
| **Dependency Status** | Health check endpoints, service discovery logs, circuit breaker logs | Circuit breaker OPEN = downstream service failing; health check FAIL = service not ready | `curl -s http://service:port/health; grep "circuit\|health" /var/log/app.log` |
| **Concurrent Access Patterns** | Transaction logs, lock logs, concurrent request logs | Same resource accessed simultaneously → race condition or deadlock | `grep "UPDATE.*WHERE\|SELECT.*FOR UPDATE" /var/log/mysql.log` |

---

## Implementation Notes

- Use `/brain-read` to access service definitions and dependencies
- Cross-reference service names with forge-product.md
- Include file paths and line numbers for code-level faults
- Redact sensitive data (passwords, tokens, PII) from logs and request bodies
- Preserve timestamps for timeline reconstruction
- Maintain chain of evidence for audit trails

---

## Checklist

Before handing fault diagnosis to self-heal-triage:

- [ ] Failure chain traced backwards from failing assertion to root service (not just last log entry)
- [ ] Request ID used to correlate logs across services
- [ ] Exception stack unwrapped to root cause (not stopped at user-facing error message)
- [ ] Timestamps compared across services (clock skew corrected if >100ms gap detected)
- [ ] Evidence collected: logs, stack trace, request/response, DB state, cache state as applicable
- [ ] Fault diagnosis written in structured YAML format

## Cross-References

### Related Skills

1. **self-heal-triage**
   - When to use: After fault has been located, use triage to classify failure type
   - Purpose: Determines whether failure is flaky (timing), bad test, or reproducible bug
   - Input: Fault diagnosis from self-heal-locate-fault
   - Output: Classification (FLAKY, TEST_BUG, or REPRODUCIBLE) with confidence score

2. **self-heal-loop-cap**
   - When to use: To ensure healing loop doesn't spin infinitely on the same failure
   - Purpose: Enforces max 3 retries per failure; after 3 attempts, escalates to human review
   - Input: Failure count, fault location
   - Output: Continue healing or escalate decision

3. **self-heal-systematic-debug**
   - When to use: When fault diagnosis is incomplete or unclear, and deeper investigation needed
   - Purpose: Runs 4-phase debugging workflow: investigate → hypothesis → test → verdict
   - Input: Fault diagnosis with uncertainty markers (NEEDS_CONTEXT, BLOCKED)
   - Output: Root cause with high confidence, ready for remediation

---

## Skill Execution Flow

```
Eval Fails
    │
    └──> self-heal-locate-fault (THIS SKILL)
            Output: Fault diagnosis with evidence
    │
    └──> self-heal-triage
            Output: Failure classification
    │
    ├──> IF FLAKY: re-run with instrumentation
    │
    ├──> IF TEST_BUG: skip test, file issue
    │
    └──> IF REPRODUCIBLE:
            │
            └──> self-heal-systematic-debug (if needed for complex faults)
                    Output: Confirmed root cause
            │
            └──> self-heal-remediate
                    Output: Fix applied, eval re-run
```
