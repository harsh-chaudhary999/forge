# Evidence Collection — Sources, Decision Tree, Notes

For the identified fault service, gather the evidence categories below, then use
the decision tree to pick which log/state sources to query for a given fault
fingerprint.

## Evidence Categories

### Logs
- Last 50 lines of service logs
- Filter for ERROR, FATAL, WARN levels
- Include timestamps and context
- Identify repeating patterns or cascading failures

### Stack Traces
- Full exception stack trace if available
- File names, line numbers, function names
- Call stack showing where error originated
- Any nested exceptions

### Request/Response Data
- Full HTTP request (method, URL, headers, body)
- Full HTTP response (status, headers, body)
- Query parameters and path variables
- Authentication headers (redacted if sensitive)

### Database State
- Last N rows affected by the failed operation
- Query that failed
- Constraint violations or data type mismatches
- Transaction state (committed, rolled back, pending)
- Locks or deadlocks

### Cache State
- Cache key that was accessed
- Expected vs actual cached value
- Cache TTL and expiration
- Hit/miss ratio for the scenario
- Invalidation events

### Service State
- Service health status (up/down/degraded)
- Resource usage (CPU, memory, connections)
- Active connections or pending requests
- Configuration values relevant to the error

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

## Implementation Notes

- Use `/brain-read` to access service definitions and dependencies
- Cross-reference service names with forge-product.md
- Include file paths and line numbers for code-level faults
- Redact sensitive data (passwords, tokens, PII) from logs and request bodies
- Preserve timestamps for timeline reconstruction
- Maintain chain of evidence for audit trails
