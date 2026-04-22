---
name: eval-driver-api-http
description: "WHEN: Eval scenario requires HTTP API request/response verification. Minimal HTTP driver for eval. Functions: setup(config), call(method, path, body), verify(response, assertion), teardown()."
type: rigid
requires: [eval-scenario-format]
version: 1.0.0
preamble-tier: 3
triggers:
  - "eval HTTP API"
  - "run API eval"
  - "HTTP eval driver"
allowed-tools:
  - Bash
---

# eval-driver-api-http Skill

**Minimal HTTP Driver for Eval**

This skill provides a minimal HTTP driver for evaluating API endpoints. It handles HTTP request/response cycles for basic eval scenarios. Full multi-surface eval support will be implemented in later phases.

## Anti-Pattern Preamble

**DO NOT assume these falsehoods:**

1. **"HTTP tests are enough, no need multi-surface eval"** — HTTP tests verify only the happy path. Real production behavior involves connection failures, timeouts, SSL cert issues, rate limiting, and connection pooling exhaustion that HTTP mocks never expose. Always plan for multi-surface eval (web, mobile, cache, message bus).

2. **"We can mock HTTP responses"** — Mocking network behavior is dangerous. Mocks hide real failure modes: connection resets, partial reads, slow networks vs. timeouts, retry exhaustion, certificate validation failures. Eval must exercise real network conditions. Mock *data*, not *transport*.

3. **"Network timeouts don't matter for eval"** — Timeouts are performance contracts between client and server. Setting wrong timeouts creates false positives (tests pass locally, fail in production under load) or false negatives (tests timeout, production succeeds). Timeout configuration must be derived from observed P95 latency + buffer, not guesses.

## Iron Law

```
EVERY HTTP EVAL ASSERTION VERIFIES SPECIFIC STATUS CODE, RESPONSE BODY FIELDS, AND CONTENT-TYPE. NO ASSERTION IS "STATUS 2xx IS ENOUGH." TIMEOUTS ARE DERIVED FROM P95 LATENCY DATA, NOT DEFAULTS. teardown() IS CALLED IN ALL PATHS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Assertion checks only that status code is 2xx without verifying response body** — A 200 OK with an empty body or error payload in the body is not a passing eval. STOP. Every assertion must verify specific response body fields.
- **Timeout is set to the driver default without consulting P95 latency data** — Default timeouts (5000ms) may mask slow endpoints or cause false timeouts on valid but slower responses. STOP. Set timeout to observed P95 latency + 50% buffer for each endpoint.
- **`teardown()` is not called after scenario completes** — An HTTP driver with open keep-alive connections will prevent subsequent scenarios from connecting to the same port. STOP. Always call `teardown()` in all paths.
- **Eval sends requests against a live production URL** — Eval exercises edge cases and failure modes that can corrupt or modify production data. STOP. Eval must always target a dedicated eval environment.
- **Certificate validation is suppressed without documentation** — `rejectUnauthorized: false` silently disables SSL verification and hides certificate issues. STOP. Fix the certificate issue, not the check.
- **Response body is compared by stringification instead of field-by-field** — JSON field order and whitespace vary by serializer. String comparison produces false failures. STOP. Parse the response and assert on individual fields.

## Overview

The eval-driver-api-http skill enables:
- Setup of HTTP test environment
- Execution of HTTP requests against APIs
- Verification of HTTP responses
- Transient failure recovery and retry strategies
- Timeout management based on real latency data
- Teardown and cleanup

## API Reference

### setup(config)

Initializes the HTTP driver for eval.

**Parameters:**
- `config` (object): Configuration object
  - `baseUrl` (string): Base URL for HTTP requests (e.g., "http://localhost:3000")
  - `headers` (object, optional): Default headers to include in all requests (e.g., `{"Authorization": "Bearer token"}`)
  - `timeout` (number, optional): Request timeout in milliseconds (default: 5000)

**Returns:** 
- Object with status and initialized driver state

**Example:**
```javascript
const driver = setup({
  baseUrl: "http://localhost:8080",
  headers: { "Content-Type": "application/json" },
  timeout: 3000
});
```

### execute(request)

Executes an HTTP request.

**Parameters:**
- `request` (object): HTTP request specification
  - `method` (string): HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `path` (string): API endpoint path (appended to baseUrl)
  - `headers` (object, optional): Request-specific headers (merged with defaults)
  - `body` (object, optional): Request body (auto-stringified for JSON)
  - `query` (object, optional): Query parameters as key-value pairs

**Returns:**
- Object with response data:
  - `status` (number): HTTP status code
  - `headers` (object): Response headers
  - `body` (object|string): Response body
  - `duration` (number): Request duration in milliseconds
  - `success` (boolean): True if status in 2xx range

**Example:**
```javascript
const response = execute({
  method: "POST",
  path: "/api/users",
  body: { name: "John", email: "john@example.com" }
});
```

### verify(response, expectations)

Verifies HTTP response against expectations.

**Parameters:**
- `response` (object): Response object from execute()
- `expectations` (object): Verification rules
  - `status` (number|array): Expected status code(s)
  - `bodyContains` (object|string): Required content in response body
  - `headerExists` (array): Headers that must be present
  - `headerValues` (object): Headers with specific values to verify

**Returns:**
- Object with verification results:
  - `passed` (boolean): All checks passed
  - `failures` (array): List of failed checks with details
  - `duration` (number): Verification time in milliseconds

**Example:**
```javascript
const result = verify(response, {
  status: 200,
  bodyContains: { id: 1, name: "John" },
  headerExists: ["content-type"]
});
```

### teardown()

Cleans up resources and closes the driver.

**Returns:**
- Object with cleanup status

**Example:**
```javascript
teardown();
```

## Example Eval Scenario

This example demonstrates a complete eval workflow for a simple user API:

```javascript
// Step 1: Setup
const driver = setup({
  baseUrl: "http://localhost:8080",
  headers: { "Content-Type": "application/json" },
  timeout: 5000
});

// Step 2: Execute - Create user
const createResponse = execute({
  method: "POST",
  path: "/api/users",
  body: {
    name: "Alice Johnson",
    email: "alice@example.com",
    role: "admin"
  }
});

// Step 3: Verify creation
const createVerification = verify(createResponse, {
  status: 201,
  bodyContains: { name: "Alice Johnson" },
  headerExists: ["content-type"]
});

// Step 4: Extract user ID for next request
const userId = createResponse.body.id;

// Step 5: Execute - Fetch created user
const getResponse = execute({
  method: "GET",
  path: `/api/users/${userId}`
});

// Step 6: Verify fetch
const getVerification = verify(getResponse, {
  status: 200,
  bodyContains: {
    id: userId,
    name: "Alice Johnson",
    email: "alice@example.com"
  }
});

// Step 7: Execute - Update user
const updateResponse = execute({
  method: "PUT",
  path: `/api/users/${userId}`,
  body: { role: "user" }
});

// Step 8: Verify update
const updateVerification = verify(updateResponse, {
  status: 200,
  bodyContains: { role: "user" }
});

// Step 9: Execute - Delete user
const deleteResponse = execute({
  method: "DELETE",
  path: `/api/users/${userId}`
});

// Step 10: Verify deletion
const deleteVerification = verify(deleteResponse, {
  status: 204
});

// Step 11: Teardown
teardown();

// Summary
console.log("Eval Results:");
console.log("- Create user:", createVerification.passed ? "PASS" : "FAIL");
console.log("- Get user:", getVerification.passed ? "PASS" : "FAIL");
console.log("- Update user:", updateVerification.passed ? "PASS" : "FAIL");
console.log("- Delete user:", deleteVerification.passed ? "PASS" : "FAIL");
```

## Implementation Notes

This is Phase 1 of the eval driver framework:
- **Scope:** Basic HTTP request/response handling
- **Out of scope:** 
  - Multi-surface evaluation (GraphQL, gRPC, WebSocket, etc.)
  - Advanced response matching (regex, custom validators)
  - Concurrent request execution
  - Load testing capabilities
  - Performance profiling
  - Integration with external monitoring/tracing systems

## Usage

To use this skill in eval scenarios:

1. Import/require the driver module
2. Call `setup()` with your API configuration
3. Use `execute()` for each request you want to test
4. Use `verify()` to validate responses
5. Call `teardown()` when finished

The driver maintains state between calls, allowing you to extract data from one response and use it in subsequent requests (as shown in the example scenario above).

## Error Handling

All functions return status objects. Check the `success`/`passed` fields to determine if operations completed successfully. The `failures` array in verify results contains detailed error information.

```javascript
if (!response.success) {
  console.error("Request failed:", response.error);
}

if (!verification.passed) {
  verification.failures.forEach(failure => {
    console.error("Verification failed:", failure.message);
  });
}
```

## Edge Cases

Production HTTP eval must handle these failure modes. Each requires different recovery strategies.

### 1. Timeout vs. Slow Network

**Problem:** A slow network (P99 latency = 4s) vs. a hung server (no response) both trigger timeout errors. Distinguishing them determines retry strategy.

**Signals:**
- **Transient slow network:** Request eventually succeeds after 3-5s; subsequent requests on same connection are normal speed.
- **Real timeout (server hung):** All requests on connection timeout; new connections also timeout or return connection refused.

**Eval handling:**
```javascript
const response = execute({
  method: "GET",
  path: "/api/status",
  timeout: 8000  // P95 latency (5s) + buffer (3s)
});

// If timeout occurred, check if it's transient
if (response.error && response.error.code === "ETIMEDOUT") {
  // Retry once after 500ms backoff
  const retryResponse = execute({
    method: "GET",
    path: "/api/status",
    timeout: 8000
  });
  
  // If second attempt succeeds, first was transient slow network
  if (retryResponse.success) {
    console.log("Transient latency spike detected and recovered");
  } else {
    // Both attempts failed → likely server issue
    console.error("Server unresponsive - multiple timeouts");
  }
}
```

### 2. Retryable Errors vs. Non-Retryable

**Retryable (transient failures—retry safely):**
- 5xx errors (500, 502, 503, 504)
- Connection reset / ECONNRESET
- Connection refused (server restarting)
- EHOSTUNREACH (temporary DNS/routing issue)
- ENETUNREACH (temporary network partition)

**Non-retryable (permanent failures—fail fast):**
- 4xx errors (400, 401, 403, 404, 409)
- ENOTFOUND (DNS resolution failed permanently)
- SSL certificate validation errors
- Protocol errors (malformed request)

**Eval handling:**
```javascript
function isRetryableError(error) {
  const retryableErrors = [
    "ECONNRESET",
    "ECONNREFUSED",
    "EHOSTUNREACH",
    "ENETUNREACH",
    "ETIMEDOUT"
  ];
  
  const retryableStatuses = [500, 502, 503, 504];
  
  return retryableErrors.includes(error.code) || 
         retryableStatuses.includes(error.status);
}

const response = execute({
  method: "POST",
  path: "/api/data",
  body: { payload: "data" }
});

if (!response.success && isRetryableError(response.error)) {
  console.log("Retrying transient error:", response.error.code);
  // Retry with exponential backoff (see section below)
} else if (!response.success) {
  console.log("Permanent failure - no retry:", response.error.code);
  throw response.error;
}
```

### 3. Rate Limiting (429 Responses)

**Problem:** API returns 429 Too Many Requests. The `Retry-After` header tells you when to retry.

**Signals:**
- Status code 429
- `Retry-After` header (seconds to wait, or HTTP-date)
- `X-RateLimit-*` headers (remaining quota, reset time)

**Eval handling:**
```javascript
function parseRetryAfter(retryAfterHeader) {
  // Retry-After can be: "120" (seconds) or "Fri, 31 Dec 1999 23:59:59 GMT"
  const seconds = parseInt(retryAfterHeader);
  if (!isNaN(seconds)) return seconds * 1000;
  
  const date = new Date(retryAfterHeader);
  const delay = date.getTime() - Date.now();
  return Math.max(0, delay);
}

let response = execute({
  method: "GET",
  path: "/api/expensive-operation"
});

if (response.status === 429) {
  const retryAfter = parseRetryAfter(
    response.headers["retry-after"] || "5"
  );
  console.log(`Rate limited. Waiting ${retryAfter}ms`);
  
  // Sleep and retry
  await new Promise(r => setTimeout(r, retryAfter));
  response = execute({
    method: "GET",
    path: "/api/expensive-operation"
  });
}

if (response.success) {
  console.log("Recovered from rate limit");
}
```

### 4. Connection Pooling Exhaustion

**Problem:** Client connection pool is empty (all connections busy or stuck). New requests get ECONNREFUSED or "socket hang up".

**Signals:**
- ECONNREFUSED or "connect ECONNREFUSED"
- Error happens on normally-working server
- Error stops after pool drains (timeout + cleanup)
- Duration pattern: error spikes then disappears

**Causes:**
- Requests not ending (missing response.end(), body not fully read)
- Server-side slow processing (requests queue up, pool exhausts)
- Slow network (connections kept open waiting for data)

**Eval handling:**
```javascript
// WRONG: Doesn't consume response body
execute({
  method: "GET",
  path: "/api/large-file"
  // Response body never read → connection not released
});

// CORRECT: Always consume response body
const response = execute({
  method: "GET",
  path: "/api/large-file"
});
if (response.body) {
  const size = JSON.stringify(response.body).length;
  console.log(`Downloaded ${size} bytes`);
}

// If pool exhaustion occurs despite consuming bodies:
// - Increase pool size in setup()
// - Reduce concurrent requests
// - Add backoff between requests

const driver = setup({
  baseUrl: "http://localhost:3000",
  maxConnections: 50,  // Increase if needed
  timeout: 30000       // Give slow servers time
});
```

### 5. SSL/TLS Certificate Issues

**Problem:** Self-signed cert, expired cert, hostname mismatch, or CA bundle missing causes UNABLE_TO_VERIFY_LEAF_SIGNATURE or CERT_HAS_EXPIRED.

**When to ignore (dev/test only):**
- Local eval with self-signed certs
- Use `rejectUnauthorized: false` **only in test** environments

**When to fix (production eval):**
- Invalid hostname (mismatch between cert CN and request hostname)
- Expired certificates (update CA bundle or cert)
- Missing root CA in cert chain

**Eval handling:**
```javascript
// For local dev with self-signed certs:
const driver = setup({
  baseUrl: "http://localhost:8443",  // Use https://
  headers: { "Content-Type": "application/json" },
  timeout: 5000,
  httpsOptions: {
    rejectUnauthorized: false  // NEVER in production
  }
});

// For production eval (correct approach):
// 1. Ensure server cert is valid and not expired
// 2. Ensure CA bundle includes server's root CA
// 3. Ensure hostname in URL matches cert CN or SAN

const response = execute({
  method: "GET",
  path: "/api/secure"
});

if (response.error && response.error.code === "UNABLE_TO_VERIFY_LEAF_SIGNATURE") {
  throw new Error(
    "SSL cert verification failed. " +
    "Check: (1) cert expiry, (2) hostname match, (3) CA bundle. " +
    "Never suppress this in production."
  );
}
```

### 6. Request Body Encoding Errors

**Problem:** JSON encoding fails (circular references, BigInt), or charset mismatch between Content-Type header and body encoding causes 400 Bad Request.

**Signals:**
- 400 Bad Request with "Unexpected token" or similar
- Content-Type: application/json; charset=utf-8 but body is ISO-8859-1
- Body contains non-serializable values

**Eval handling:**
```javascript
// WRONG: BigInt not JSON-serializable
const response = execute({
  method: "POST",
  path: "/api/ids",
  body: { userId: 12345678901234567890n }  // BigInt → error
});

// CORRECT: Convert to string
const response = execute({
  method: "POST",
  path: "/api/ids",
  body: { userId: "12345678901234567890" }
});

// WRONG: Circular reference
const circular = { a: 1 };
circular.self = circular;
execute({
  method: "POST",
  path: "/api/data",
  body: circular  // TypeError on stringify
});

// CORRECT: Use deep clone and remove problematic refs
const clean = JSON.parse(JSON.stringify({ a: 1, b: { c: 2 } }));
const response = execute({
  method: "POST",
  path: "/api/data",
  body: clean
});

// Charset mismatch detection:
if (response.status === 400 && response.body.message?.includes("Unexpected")) {
  console.error(
    "Body encoding error. Check: " +
    "(1) Content-Type charset matches body encoding, " +
    "(2) JSON is valid (no circular refs, BigInt, symbols)"
  );
}
```

## Retry Guidance

### When to Retry

Retry **only** on transient failures (see section 2 above). Retrying permanent failures wastes time and resources.

**Transient failure checklist:**
- [ ] Error is in retryable set (5xx, connection reset, EHOSTUNREACH)
- [ ] Already waited for Retry-After header (if 429)
- [ ] Have not exceeded max retry count (see below)
- [ ] Request is idempotent (GET, DELETE, PUT with correct semantics) **or** server accepts duplicate requests safely

**Non-idempotent operations (POST without idempotency key):**
- Cannot safely retry—risk duplicate record creation
- Use idempotency key header to enable safe retry (requires server support)

### Exponential Backoff with Jitter

**Why:** Thundering herd. If all clients retry at the same time, they overload the server again. Jitter spreads retries across time.

**Formula:**
```
delay = min(maxDelay, baseDelay * (2 ^ attempt) + random(0, jitter))
```

**Eval example:**
```javascript
async function executeWithRetry(
  request,
  maxRetries = 3,
  baseDelayMs = 100,
  maxDelayMs = 10000
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = execute(request);
    
    if (response.success) {
      return response;
    }
    
    if (!isRetryableError(response.error) || attempt === maxRetries) {
      throw response.error;
    }
    
    // Calculate delay with exponential backoff + jitter
    const exponentialDelay = baseDelayMs * Math.pow(2, attempt);
    const jitter = Math.random() * exponentialDelay;
    const delay = Math.min(maxDelayMs, exponentialDelay + jitter);
    
    console.log(
      `Attempt ${attempt + 1} failed. ` +
      `Retrying after ${Math.round(delay)}ms`
    );
    
    await new Promise(r => setTimeout(r, delay));
  }
}

// Usage:
const response = await executeWithRetry(
  {
    method: "POST",
    path: "/api/data",
    body: { message: "test" }
  },
  maxRetries = 3,
  baseDelayMs = 100
);
```

### Retry Limits

**Why limits matter:** 
- Without limits, transient failures cause unbounded delays (3 retries with exponential backoff can delay 1-30 seconds)
- Circuit breakers detect cascading failures faster than retry loops
- After N failures, assume permanent issue and fail fast

**Recommended settings:**
- **Interactive requests (user-facing):** 2 retries, 5s max delay
- **Background jobs:** 5 retries, 30s max delay
- **Batch operations:** 3 retries, 10s max delay

```javascript
const retryConfig = {
  interactive: { maxRetries: 2, maxDelayMs: 5000 },
  background: { maxRetries: 5, maxDelayMs: 30000 },
  batch: { maxRetries: 3, maxDelayMs: 10000 }
};
```

## Timeout Calculation

### The Problem with Guesses

**Common mistake:** "Set timeout to 5 seconds—seems reasonable."

**Reality check:** 
- Local network: 10-50ms (P95)
- Same datacenter: 100-500ms (P95)
- Cross-region: 1-5s (P95)
- Internet (3G/4G): 1-10s (P95)
- Load-tested server: Add 2-3x latency under load

**Symptom of wrong timeout:**
- Too short: Tests timeout locally but work in production (different latency profile)
- Too long: Tests hide real performance issues; slow endpoints cause slow test suites

### Correct Approach: Measure P95, Add Buffer

**Step 1: Baseline the API**

Run 100+ requests in test environment and record response times:
```javascript
const latencies = [];
for (let i = 0; i < 100; i++) {
  const start = Date.now();
  const response = execute({
    method: "GET",
    path: "/api/status"
  });
  latencies.push(Date.now() - start);
}

const p95 = latencies.sort((a, b) => a - b)[Math.floor(latencies.length * 0.95)];
console.log(`P95 latency: ${p95}ms`);
```

**Step 2: Calculate timeout as P95 + buffer**

```javascript
// Buffer factors:
// - Development/test server: +2x (less powerful, fewer resources)
// - Production-like: +1.5x (accounts for variability)
// - Load-tested: +1x (already includes load impact)

const timeout = Math.round(p95 * 2);  // Dev/test
const timeout = Math.round(p95 * 1.5);  // Prod-like
const timeout = Math.round(p95 + 2000);  // At least 2s buffer
```

**Step 3: Verify timeout empirically**

Run eval suite repeatedly and measure timeout hit rate (should be < 0.1%):
```javascript
const driver = setup({
  baseUrl: "http://localhost:3000",
  timeout: 5000  // Your calculated timeout
});

const timeoutCount = 0;
const totalCount = 0;

for (let i = 0; i < 1000; i++) {
  const response = execute({
    method: "GET",
    path: "/api/users"
  });
  
  totalCount++;
  if (response.error?.code === "ETIMEDOUT") {
    timeoutCount++;
  }
}

const timeoutRate = timeoutCount / totalCount;
if (timeoutRate > 0.001) {  // >0.1%
  console.warn(
    `High timeout rate: ${(timeoutRate * 100).toFixed(2)}%. ` +
    `Consider increasing timeout or investigating server performance.`
  );
}
```

**Example configurations:**

```javascript
// Development (local server, fast network)
const devConfig = {
  baseUrl: "http://localhost:3000",
  timeout: 3000  // P95=500ms, local latency, buffer=2.5x
};

// Staging (cloud server, varied latency)
const stagingConfig = {
  baseUrl: "https://staging-api.example.com",
  timeout: 8000  // P95=5000ms observed, buffer=1.6x
};

// Production eval (measured P95)
const prodConfig = {
  baseUrl: "https://api.example.com",
  timeout: 10000  // P95=6000ms observed, buffer=1.67x
};
```

## Best Practices

### 1. Network is Unreliable—Plan for It

Never assume a request will succeed on the first try. Always:
- [ ] Implement retry logic for transient failures
- [ ] Set timeouts based on measured latency, not guesses
- [ ] Log failures with enough detail to debug (error code, duration, attempt number)
- [ ] Monitor timeout rates and latency spikes in eval results

### 2. Timeouts are Performance Contracts

Timeouts define the maximum acceptable latency for your eval:
- Too high: Slow tests, hidden performance issues
- Too low: False timeouts, brittle tests
- [ ] Measure baseline latency before setting timeout
- [ ] Increase timeout gradually if you observe transient failures
- [ ] If timeout exceeds 30s, investigate underlying performance issue instead

### 3. Rate Limits are Real

APIs have quota limits. Eval scenarios must respect them:
- [ ] Check for 429 responses in eval output
- [ ] Parse `Retry-After` header—it's not a suggestion
- [ ] Add delays between requests if eval makes many calls
- [ ] Use idempotency keys for non-GET requests if retrying is needed

### 4. Connection Pool Management

HTTP connection reuse is critical for performance:
- [ ] Always consume response body (even if ignoring data)
- [ ] Don't hold connections open indefinitely
- [ ] Set reasonable pool size (usually 10-50 connections)
- [ ] Monitor for "socket hang up" errors (indicates pool exhaustion)

### 5. Certificate Validation in Eval

SSL/TLS security matters even in eval:
- [ ] Never suppress `rejectUnauthorized` in production eval
- [ ] Fix cert issues at the source: expiry, hostname mismatch, missing CA
- [ ] Use self-signed certs only in isolated dev environments
- [ ] Document why any cert validation is disabled

### 6. Request Body Validation Before Send

Catch encoding errors early:
- [ ] Validate JSON serializable (no circular refs, BigInt, symbols)
- [ ] Check Content-Type charset matches actual encoding
- [ ] Test with edge case payloads (empty objects, null, large strings)
- [ ] Log request body on 4xx errors for debugging

## Checklist

Before running an HTTP API eval scenario:

- [ ] Target URL points to eval environment (not production)
- [ ] Timeout derived from P95 latency data, not default value
- [ ] Assertions verify specific status code AND specific response body fields
- [ ] Response body compared field-by-field, not by string equality
- [ ] Certificate validation is enabled (not suppressed with rejectUnauthorized: false)
- [ ] `teardown()` called in all paths (success, failure, timeout)
