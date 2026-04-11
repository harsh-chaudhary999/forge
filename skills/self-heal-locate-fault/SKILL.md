---
name: self-heal-locate-fault
description: Diagnose which service failed in eval. Parse eval output, identify failure point, collect logs. Output: fault diagnosis with evidence.
type: rigid
requires: [brain-read]
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

## Usage

This skill is invoked automatically by the `self-heal` conductor when an eval scenario fails.

**Input**: Eval failure output (logs, exceptions, response bodies)

**Output**: YAML fault diagnosis with actionable remediation steps

**Next Step**: Pass fault diagnosis to `self-heal-remediate` skill to apply fixes.

## Implementation Notes

- Use `/brain-read` to access service definitions and dependencies
- Cross-reference service names with forge-product.md
- Include file paths and line numbers for code-level faults
- Redact sensitive data (passwords, tokens, PII) from logs and request bodies
- Preserve timestamps for timeline reconstruction
- Maintain chain of evidence for audit trails
