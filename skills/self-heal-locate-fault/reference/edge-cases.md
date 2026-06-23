# Edge Cases (Critical Scenarios)

## Edge Case 1: No Logs for the Failure Window

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

## Edge Case 2: Multiple Services Log Same Error at Same Timestamp

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

## Edge Case 3: Error Fingerprint Missing from Pattern Library

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

## Edge Case 4: Log Timestamps Not Synchronized Across Services

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

## Edge Case 5: Silent Fault (No Error Logged, Eval Fails)

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
