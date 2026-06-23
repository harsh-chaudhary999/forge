# Fault Identification Patterns

Map the failure to a service or component using causal reasoning. Use these
pattern tables to translate a symptom (HTTP code, data mismatch, chain position,
external error) into a candidate fault service.

## Pattern 1: HTTP Error Codes
```
Status Code → Service
400, 401, 403 → Client error or auth service
404 → API routing or endpoint not found
422 → Validation service or input processor
500, 502, 503 → Backend API service
504 → Gateway timeout, likely upstream service
```

## Pattern 2: Data Inconsistency
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

## Pattern 3: Service Chain Failures
```
Web → API → DB
├── Web error (render, CDN, routing) → Web service
├── API error (500, exception) → Backend API service
├── DB error (constraint, timeout) → Database service
├── No response from API → API service or network
└── Slow response (timeout) → Slowest service in chain
```

## Pattern 4: External Dependencies
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
