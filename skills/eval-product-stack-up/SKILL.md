---
name: eval-product-stack-up
description: "WHEN: Eval is about to run and the full product stack must be brought up first. Reads forge-product.md, starts services in dependency order, runs health checks, confirms stack is ready for eval scenarios."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 4
triggers: []
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
---

# Eval Product Stack Up

Orchestrates startup of the product stack for evaluation. Reads product topology from product.md, starts only the infrastructure and services that are **configured** in the product file, validates health checks, and reports readiness.

**Infrastructure is optional.** If no infra (DB, Redis, Kafka, Elasticsearch) is configured in product.md, stack-up skips infra startup and runs eval against services only. Eval scenarios that require unconfigured infra are automatically skipped and marked N/A — they do not cause an eval failure.

## Anti-Pattern Preamble: No Rationalizations

**Block these dangerous rationalizations immediately:**

1. **"We'll start services manually, this is overkill"**
   - Truth: One developer forgets to start a service, 45 minutes of debugging follow. The "overkill" is insurance against human error at scale.
   - Consequence: Eval failures attributed to code bugs when they're infrastructure failures. Entire sprint derailed.
   - Standard: Every service startup is automated and verified. No manual steps.

2. **"Stack is too complex to automate"**
   - Truth: Complexity is exactly why automation matters. Manual complexity is error-prone. Automated complexity is reproducible.
   - Consequence: Evals succeed for you locally, fail in CI. Blame infrastructure differences. Waste 3 hours diagnosing.
   - Standard: If it's in the stack, it's automated. If it can't be automated, it's not ready for eval.

3. **"We'll skip health checks to save time"**
   - Truth: You'll skip them once and debug for hours wondering why eval failed. Service appears "up" but isn't actually ready.
   - Consequence: API returns 503, scenario fails mysteriously. Logs show "connection refused" but port 3000 is listening. Service not fully initialized.
   - Standard: Health checks are non-negotiable. Default timeout: 5 seconds per service. Total stack startup < 30s.

4. **"Partial failures are fine, we can test what's up"**
   - Truth: There is a critical distinction between two types of partial stacks:
     - **By design** (infra not configured in product.md) → VALID. Skip that infra. Eval the rest. Mark dependent scenarios N/A.
     - **By failure** (infra configured but failed to start) → INVALID. This is a real failure. Fail fast.
   - Consequence of conflating the two: agents either block all eval because Redis isn't configured (too strict) or silently eval against a broken stack (too loose).
   - Standard: If infra is **absent from product.md**, skip it gracefully. If infra is **in product.md but fails to start**, fail fast with detailed error.

## Iron Law

```
EVERY STACK-UP READS product.md FRESH AND STARTS EXACTLY WHAT IS CONFIGURED — NO MORE, NO LESS.
CONFIGURED SERVICES THAT FAIL TO START = HARD FAILURE. UNCONFIGURED SERVICES = GRACEFUL SKIP.
HEALTH CHECKS ARE NEVER SKIPPED FOR CONFIGURED SERVICES.
EVAL SCENARIOS REQUIRING UNCONFIGURED INFRA ARE MARKED N/A, NOT FAILED.
```

**Infra tiers (all optional unless configured in product.md):**
- Tier 1 — Application services (backend, web, mobile): Always required if in product.md
- Tier 2 — Relational DB (MySQL, PostgreSQL, SQLite): Optional. Skip if not configured.
- Tier 3 — Cache (Redis, Memcached): Optional. Skip if not configured.
- Tier 4 — Message bus (Kafka, RabbitMQ): Optional. Skip if not configured.
- Tier 5 — Search (Elasticsearch, OpenSearch): Optional. Skip if not configured.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Eval scenarios begin before all service health checks have passed** — A service that accepted the start command may still be initializing (DB migrations running, cache warming, event consumer subscribing). STOP. All health checks must return healthy before the first scenario step executes.
- **Stack is started without reading the current `forge-product.md`** — Using a cached or remembered topology means missing newly added services or removed dependencies. STOP. Always read `forge-product.md` fresh at the start of each stack-up.
- **Services are started in alphabetical or arbitrary order instead of dependency order** — Service B depending on Service A will fail to connect if A is not yet healthy. STOP. Resolve the dependency graph and start in topological order: infrastructure first, then services that depend on it.
- **`stack-down` is not called when eval fails** — Services left running from a failed eval contaminate the next run with leftover data, open connections, and consumed offsets. STOP. `stack-down` must be called unconditionally in the cleanup path, whether eval passed or failed.
- **Health check is a TCP port probe only (port accepting connections)** — A port open means the OS socket is bound, not that the application is ready. STOP. Health checks must be HTTP endpoint checks (or equivalent application-level readiness probes) that verify the application is actually serving requests.
- **A configured service in `product.md` has no `deploy_doc` and no `start`+`health`** — There is nothing executable to automate. STOP. Return user to `/workspace` Step 3b or `/scan` Step 1 to add a runbook path or commands; do not pretend stack-up can proceed.
- **Stack-up is declared successful before every *configured* service is verified** — A stack missing a configured service will produce eval failures that look like code bugs. STOP. Every service listed in product.md must pass its health check. Services *not* listed in product.md are not started and not checked — that is correct behaviour, not a bug.

## Overview

This skill enables:
- Load and parse product topology from forge-product.md
- Validate project structure and dependency graph
- Start infrastructure services with health verification
- Start microservices in dependency-resolved order
- Execute health checks with retry logic
- Report complete stack status and readiness for eval
- Handle 7+ edge cases with clear fallback paths
- Pre-flight checks before any service startup
- Graceful and forceful shutdown patterns
- Comprehensive failure diagnostics

## API Reference

### loadProductTopology(productPath)

Reads and parses forge-product.md to extract product configuration.

**Parameters:**
- `productPath` (string): Path to product directory or forge-product.md file (e.g., `~/forge/seed-product`)

**Returns:**
- Object with parsed topology:
  - `slug` (string): Product identifier
  - `description` (string): Product description
  - `projects` (object): Map of project name → project config
    - Each project includes: repo, role, language, framework, branch, start, stop, health, depends_on, deploy_strategy
  - `infrastructure` (object): Map of infra service → config
    - Each infra includes: driver, host, port, reset_command, migration (if applicable)
  - `contracts` (array): List of contract files
  - `mergeOrder` (array): Dependency-resolved startup order

**Example:**
```javascript
const topology = loadProductTopology("~/forge/seed-product");
// Returns:
// {
//   slug: "shopapp",
//   description: "E-commerce platform with web + mobile",
//   projects: {
//     "backend-api": {
//       repo: "~/forge/seed-product/backend-api",
//       role: "backend",
//       language: "node",
//       framework: "express",
//       health: "GET http://localhost:3000/health",
//       depends_on: "shared-schemas",
//       deploy_strategy: "pm2-local"
//     },
//     // ... other projects
//   },
//   infrastructure: {
//     mysql: { driver: "mysql-native", host: "localhost", port: 3306, ... },
//     redis: { driver: "redis-resp", host: "localhost", port: 6379, ... }
//   },
//   mergeOrder: ["shared-schemas", "backend-api", "web-dashboard", "app-mobile"]
// }
```

### resolveDependencies(projects)

Validates dependency graph and returns topologically sorted startup order.

**Parameters:**
- `projects` (object): Map of project name → project config with `depends_on` field

**Returns:**
- Object with dependency validation:
  - `order` (array): Projects in startup order (dependencies first)
  - `valid` (boolean): True if no circular dependencies
  - `cycles` (array): Any detected circular dependencies (empty if valid)
  - `missing` (array): Any dependencies not found in projects list

**Example:**
```javascript
const deps = resolveDependencies(topology.projects);
// Returns:
// {
//   order: ["shared-schemas", "backend-api", "web-dashboard", "app-mobile"],
//   valid: true,
//   cycles: [],
//   missing: []
// }
```

### startInfrastructure(topology)

Starts all infrastructure services (MySQL, Redis, Kafka, Elasticsearch) in correct order.

**Parameters:**
- `topology` (object): Product topology from loadProductTopology()

**Returns:**
- Object with startup results:
  - `status` (string): "success" | "partial" | "failed"
  - `services` (object): Map of service name → state
    - Each service: { status: "running"|"stopped"|"error", port: number, health: "healthy"|"unhealthy"|"unknown", error?: string, startedAt: timestamp }
  - `failures` (array): Any services that failed to start
  - `duration` (number): Total startup time in milliseconds

**Example:**
```javascript
const infraResult = startInfrastructure(topology);
// Returns:
// {
//   status: "success",
//   services: {
//     mysql: {
//       status: "running",
//       port: 3306,
//       health: "healthy",
//       startedAt: 1712700000000
//     },
//     redis: {
//       status: "running",
//       port: 6379,
//       health: "healthy",
//       startedAt: 1712700005000
//     }
//   },
//   failures: [],
//   duration: 8500
// }
```

### startServices(topology, dependencyOrder, deployDrivers)

Starts all application services in dependency order.

**Parameters:**
- `topology` (object): Product topology
- `dependencyOrder` (array): Sorted project names from resolveDependencies()
- `deployDrivers` (object): Map of deploy_strategy → driver implementation
  - Driver must implement: { start(project), stop(project), health(project, expectedStatus) }

**Returns:**
- Object with service startup results:
  - `status` (string): "success" | "partial" | "failed"
  - `services` (object): Map of service name → state
    - Each service: { status: "running"|"stopped"|"error", port?: number, health: "healthy"|"unhealthy"|"unknown", pid?: number, error?: string, startedAt: timestamp }
  - `failures` (array): Services that failed to start
  - `duration` (number): Total startup time in milliseconds

**Example:**
```javascript
const serviceResult = startServices(topology, deps.order, {
  "pm2-local": pm2Driver
});
// Returns:
// {
//   status: "success",
//   services: {
//     "shared-schemas": {
//       status: "ready",
//       health: "n/a" // No service to start
//     },
//     "backend-api": {
//       status: "running",
//       port: 3000,
//       health: "healthy",
//       pid: 12345,
//       startedAt: 1712700015000
//     },
//     "web-dashboard": {
//       status: "running",
//       port: 3001,
//       health: "healthy",
//       pid: 12346,
//       startedAt: 1712700025000
//     },
//     "app-mobile": {
//       status: "running",
//       port: undefined, // Mobile, no HTTP health
//       health: "unknown",
//       pid: 12347,
//       startedAt: 1712700035000
//     }
//   },
//   failures: [],
//   duration: 25000
// }
```

### healthCheck(service, healthEndpoint, maxRetries, retryInterval)

Executes health check for a single service with retry logic.

**Parameters:**
- `service` (string): Service name for logging
- `healthEndpoint` (string): Health check URL (e.g., "GET http://localhost:3000/health") or null for non-HTTP services
- `maxRetries` (number, optional): Maximum retry attempts (default: 5)
- `retryInterval` (number, optional): Wait between retries in milliseconds (default: 2000)

**Returns:**
- Object with health check results:
  - `service` (string): Service name
  - `healthy` (boolean): Health status after retries
  - `status` (number|string): HTTP status or "n/a" for non-HTTP
  - `response` (object|null): Full response from health endpoint
  - `attempts` (number): Retries needed before success (or max if failed)
  - `lastError` (string): Last error message if unhealthy
  - `duration` (number): Time spent on health checks in milliseconds

**Example:**
```javascript
const health = healthCheck("backend-api", "GET http://localhost:3000/health", 5, 2000);
// Returns:
// {
//   service: "backend-api",
//   healthy: true,
//   status: 200,
//   response: { status: "healthy", uptime: 15000 },
//   attempts: 2,
//   lastError: null,
//   duration: 4050
// }
```

### buildStackReport(topology, infraResult, serviceResult, allHealthChecks)

Generates comprehensive stack status report.

**Parameters:**
- `topology` (object): Product topology
- `infraResult` (object): Result from startInfrastructure()
- `serviceResult` (object): Result from startServices()
- `allHealthChecks` (array): Array of health check results from healthCheck()

**Returns:**
- Object with stack report:
  - `ready` (boolean): All services healthy and ready for eval
  - `timestamp` (number): Report generation timestamp
  - `product` (string): Product slug
  - `infrastructure` (object): Infra service states and health
  - `services` (object): Application service states and health
  - `summary` (object): Counts of running, healthy, failed services
  - `nextSteps` (array): Recommendations if not ready
  - `yaml` (string): YAML representation of stack state

**Example:**
```javascript
const report = buildStackReport(topology, infraResult, serviceResult, healthChecks);
// Returns full stack report suitable for output
```

## Implementation Workflow

1. **Load Product Topology**
   ```bash
   # Read forge-product.md from product directory
   cat <product-path>/forge-product.md
   ```
   Parse YAML/markdown to extract:
   - Projects with repo paths, start/stop commands, health endpoints, dependencies
   - Infrastructure with drivers, ports, reset commands
   - Merge order or compute via dependency resolution

2. **Validate Dependencies**
   - For each project, check that depends_on projects exist
   - Build directed graph and detect cycles
   - Topologically sort into startup order
   - Stop if circular dependencies found

3. **Start Infrastructure** (in order: MySQL → Redis → Kafka → ES)
   - For each infra service:
     - Check if already running (ps aux, netstat, or driver-specific check)
     - If not: execute start command (docker-compose, mysqld, redis-server, etc.)
     - Wait up to 10s for port to be open and respond
     - Verify connectivity (MySQL: SHOW DATABASES, Redis: PING, etc.)
     - Log port, PID, timestamp

4. **Start Services** (in resolved dependency order)
   - For each project in order:
     - If role is "shared" (shared-schemas): skip startup, mark as ready
     - Select deploy driver based on deploy_strategy
     - Change to repo directory
     - Execute start command: `npm run dev`, `docker run`, etc.
     - Capture PID if applicable
     - Wait for health endpoint to become ready
   - Stop and error if any service fails

5. **Health Checks** (concurrent where possible)
   - For each service with health endpoint:
     - Execute HTTP GET to health endpoint
     - Parse response (expect 200-299 and { status: "healthy" } or similar)
     - Retry up to 5 times with 2s interval
     - Record pass/fail and response time
   - For services without health endpoint:
     - Mark as "n/a"

6. **Report**
   Output YAML or JSON with:
   ```yaml
   product: shopapp
   timestamp: 2025-02-15T14:30:00Z
   ready: true
   
   infrastructure:
     mysql:
       status: running
       port: 3306
       health: healthy
       driver: mysql-native
       startedAt: 2025-02-15T14:30:00Z
       
     redis:
       status: running
       port: 6379
       health: healthy
       driver: redis-resp
       startedAt: 2025-02-15T14:30:05Z
       
   services:
     shared-schemas:
       status: ready
       role: shared
       health: n/a
       
     backend-api:
       status: running
       role: backend
       port: 3000
       health: healthy (status: 200)
       pid: 12345
       startedAt: 2025-02-15T14:30:10Z
       healthCheckDuration: 450ms
       
     web-dashboard:
       status: running
       role: web-frontend
       port: 3001
       health: healthy (status: 200)
       pid: 12346
       startedAt: 2025-02-15T14:30:20Z
       healthCheckDuration: 320ms
       
     app-mobile:
       status: running
       role: app-frontend
       port: null
       health: unknown
       pid: 12347
       startedAt: 2025-02-15T14:30:30Z
       
   summary:
     infrastructure: 2 running, 2 healthy
     services: 4 running, 3 healthy, 1 unknown
     
   nextSteps:
     - All services healthy. Ready for eval scenarios.
   ```

## Example: Full Stack Bringup (ShopApp)

### Prerequisites
- forge-product.md exists at ~/forge/seed-product/forge-product.md
- All project repos cloned to paths specified in forge-product.md
- Dependencies installed in each project (npm install, etc.)

### Execution

```javascript
// Step 1: Load topology
const topology = loadProductTopology("~/forge/seed-product");
console.log("Loaded product:", topology.slug);
console.log("Projects:", Object.keys(topology.projects));

// Step 2: Validate dependencies
const deps = resolveDependencies(topology.projects);
if (!deps.valid) {
  console.error("Dependency validation failed:", deps.cycles);
  process.exit(1);
}
console.log("Startup order:", deps.order);

// Step 3: Start infrastructure (only what is configured)
if (topology.infrastructure && Object.keys(topology.infrastructure).length > 0) {
  console.log("Starting configured infrastructure...");
  const infraResult = startInfrastructure(topology);
  if (infraResult.status !== "success") {
    // Only fail if a CONFIGURED service failed to start
    console.error("Infrastructure startup failed:", infraResult.failures);
    process.exit(1);
  }
  console.log("Infrastructure started:", Object.keys(infraResult.services));
} else {
  console.log("No infrastructure configured — skipping infra startup.");
  console.log("Scenarios requiring DB/Redis/Kafka will be marked N/A.");
}

// Step 4: Start services in dependency order
console.log("Starting services...");
const pm2Driver = {
  start: (project) => {
    // pm2 start <project.repo>/package.json --name <project-name>
  },
  stop: (project) => {
    // pm2 stop <project-name>
  },
  health: async (project, expectedStatus) => {
    // HTTP GET to project.health endpoint
  }
};

const serviceResult = startServices(topology, deps.order, {
  "pm2-local": pm2Driver
});

if (serviceResult.status === "failed") {
  console.error("Service startup failed:", serviceResult.failures);
  process.exit(1);
}

// Step 5: Run health checks
console.log("Running health checks...");
const healthChecks = [];
for (const [name, service] of Object.entries(serviceResult.services)) {
  if (service.health !== "n/a" && topology.projects[name]?.health) {
    const health = healthCheck(name, topology.projects[name].health, 5, 2000);
    healthChecks.push(health);
  }
}

// Step 6: Build report
const report = buildStackReport(topology, infraResult, serviceResult, healthChecks);

if (report.ready) {
  console.log("SUCCESS: Stack is ready for eval");
  console.log(report.yaml);
} else {
  console.log("WARNING: Stack not fully ready");
  console.log("Issues:", report.nextSteps);
}
```

### Expected Output (Success)

```
Loaded product: shopapp
Projects: backend-api, web-dashboard, app-mobile, shared-schemas
Startup order: shared-schemas, backend-api, web-dashboard, app-mobile
Starting infrastructure...
Infrastructure started: mysql, redis
Starting services...
All services started successfully
Running health checks...
SUCCESS: Stack is ready for eval

product: shopapp
timestamp: 2025-02-15T14:30:45Z
ready: true

infrastructure:
  mysql:
    status: running
    port: 3306
    health: healthy
    startedAt: 2025-02-15T14:30:00Z
    
  redis:
    status: running
    port: 6379
    health: healthy
    startedAt: 2025-02-15T14:30:05Z
    
services:
  shared-schemas:
    status: ready
    role: shared
    health: n/a
    
  backend-api:
    status: running
    role: backend
    port: 3000
    health: healthy (GET /health → 200)
    pid: 12345
    startedAt: 2025-02-15T14:30:10Z
    healthCheckDuration: 450ms
    
  web-dashboard:
    status: running
    role: web-frontend
    port: 3001
    health: healthy (GET / → 200)
    pid: 12346
    startedAt: 2025-02-15T14:30:20Z
    healthCheckDuration: 320ms
    
  app-mobile:
    status: running
    role: app-frontend
    port: null
    health: unknown
    pid: 12347
    startedAt: 2025-02-15T14:30:30Z

summary:
  infrastructure: 2 running, 2 healthy
  services: 4 ready, 3 healthy, 1 unknown
  
nextSteps:
  - All services healthy. Ready for eval scenarios.
```

### Failure Scenarios

**Scenario 1: Missing Project Dependency**
```
ERROR: Dependency validation failed
Dependency "backend-api" not found in projects
Required by: web-dashboard
```

**Scenario 2: Infrastructure Startup Fails**
```
Starting infrastructure...
ERROR: Infrastructure startup failed
  - redis: ECONNREFUSED 127.0.0.1:6379 (Port already in use?)
Fix: redis-cli SHUTDOWN or choose different port
```

**Scenario 3: Service Health Check Timeout**
```
Starting services...
All services started, but health checks failed:
  - backend-api: Failed after 5 retries (GET /health → 503)
Logs: ~/forge/seed-product/backend-api/logs/err.log
```

**Scenario 4: Circular Dependency**
```
ERROR: Dependency validation failed
Circular dependency detected:
  backend-api → web-dashboard → backend-api
Fix forge-product.md: remove circular depends_on
```

## Pre-Flight Checks Checklist

Before starting any service, run this checklist. Fail fast if any check fails.

- [ ] **Ports available**: Check all required ports (3000, 3001, 5432, 6379, 9200, 9092, etc.) are not in use. Command: `lsof -i :PORT` or `netstat -tuln | grep PORT`. If port in use, kill old process: `lsof -ti :PORT | xargs kill -9`
- [ ] **Config files exist**: All required config files (.env, config.json, db.yml, etc.) present in each service directory. Missing config → service fails immediately.
- [ ] **Env vars set**: All REQUIRED env vars defined before service startup (DATABASE_URL, REDIS_URL, API_KEY, etc.). Use `.env` file or export before running.
- [ ] **Dependencies installed**: npm/pip/gradle/maven dependencies already installed in each project. Do NOT install during eval (adds 5-10min per service).
- [ ] **Database migrations ready**: Migration files present, executable, and tested. DB schema version matches service expectations.
- [ ] **Volumes writable**: Directories for logs, cache, data (e.g., /tmp/eval-stack-logs, /data/db) are writable by current user. `touch` test file to verify.
- [ ] **Network connectivity**: Can reach external services if scenario depends on them (e.g., payment gateway, SMS provider). Test with `curl` or `nc`.
- [ ] **Previous cleanup**: Old containers/processes from previous run cleaned up. Check: `docker ps -a | grep eval`, `ps aux | grep node`. Kill if found.

## Error Handling

- **Missing forge-product.md:** Stop with error message showing expected path
- **Invalid project repo:** Report which project and its configured path
- **Circular dependencies:** List full cycle path
- **Infrastructure startup failure:** Report service name, driver, error, and recovery steps
- **Service startup failure:** Report service name, error output from start command, available logs
- **Health check timeout:** Report service name, last HTTP response (if any), and logs
- **Port already in use:** Suggest killing existing process or reconfiguring port

All errors are recoverable with user intervention (kill process, fix config, etc.).

## Performance Considerations

- **Parallel startup:** Infrastructure services can start concurrently after dependencies
- **Sequential services:** Services must start in dependency order (cannot parallelize)
- **Health check timeout:** Default 5 retries × 2s = 10s per service (tunable)
- **Full stack startup:** Typically 20-60s depending on infrastructure and service startup times
- **Progress logging:** Report progress every 5 seconds or after each major step

## Best Practices

### 1. Health Checks Are Not Optional
- **Truth**: Health check is not a convenience, it's insurance
- **Standard**: Every service MUST have a health check endpoint (or equivalent)
- **No exceptions**: "I'll assume it's up" is how debugging takes 3 hours
- **Verification**: Poll health until response indicates readiness, not just "port open"
- **Pattern**: `curl -f http://localhost:3000/health | jq '.status' == "healthy"`

### 2. Startup Order Is a Specification
- **Truth**: Dependency order is not a suggestion, it's a contract
- **Standard**: Document startup order in forge-product.md with explicit `depends_on` fields
- **Testing**: Run stack bringup in CI/CD before every eval. If it changes, catch it early
- **Enforcement**: Code refuses to start service if dependencies aren't healthy
- **Pattern**: Topology.mergeOrder defines order. Enforce it. Don't skip it.

### 3. Failures Must Fail Fast
- **Truth**: Slow failure is worse than instant failure
- **Standard**: 5-second timeout per service startup. Total stack < 30 seconds
- **Rationale**: If API takes 45s to start, you want to know within 10s it won't, not wait 45s
- **Implementation**: Parallel health checks. If any critical service fails, stop immediately
- **Pattern**: Fail in 5s → identify issue → fix → retry (3 min total cycle), not 45s → debug → fix → retry

### 4. Cleanup Is a Safety Measure, Not Optional
- **Truth**: Skipping cleanup once causes cascading failures
- **Standard**: Always shutdown stack after eval, whether eval passed or failed
- **Enforcement**: Shutdown runs in finally block. Use graceful pattern (code above)
- **Verification**: Post-shutdown validation: `ps aux | grep eval` returns nothing
- **Pattern**: Graceful shutdown with 30s timeout. If timeout, forceful shutdown. Either way, clean slate.

### 5. Partial Failures Are Your Enemy
- **Truth**: Partial stack looks like bugs in code. It's not.
- **Standard**: All critical services must be healthy before eval proceeds
- **Mechanism**: Define "critical" per scenario. API scenario: API + DB critical. Non-critical: monitoring, logging
- **Failure**: If critical service unhealthy, report which service and why, then stop
- **Pattern**: Health check all services. Filter by critical. If any critical unhealthy, error with clear message.

### 6. Configuration Management Is Non-Negotiable
- **Truth**: Missing config file causes 30-minute "why doesn't it work?" debugging session
- **Standard**: Pre-flight checks verify all config files exist before startup
- **Enforcement**: For each service in forge-product.md, specify `required_files` and `required_env`
- **Verification**: Startup fails with clear message: "Missing /app/config.json. Copy from template: cp config.example.json config.json"
- **Pattern**: Pre-flight check failures prevent service startup (good), not silent failures after startup (bad)

### 7. Database Migrations Are Critical Path
- **Truth**: "DB schema not migrated" looks like app bug when it's infra issue
- **Standard**: After DB starts, immediately run migrations. Wait for completion before starting services that depend on DB
- **Verification**: Query DB schema to verify migration completed: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'mydb'`
- **Timeout**: 60s per migration file max. If timeout, show migration logs and error
- **Pattern**: Infra → Migrations complete → Services start (not: Infra + Services start in parallel → race condition on migrations)

### 8. Network Connectivity Must Be Verified
- **Truth**: Service "up" but unreachable is not the same as service "ready"
- **Standard**: Health checks verify both port open AND service responding to requests
- **Scope**: If eval depends on external services (payment API, SMS gateway), verify connectivity before eval starts
- **Fallback**: Pre-flight check: `curl -f https://external-api/health || error "Cannot reach external API"`
- **Pattern**: External services = requirements, not assumptions

### 9. Logs Are Debugging Gold
- **Standard**: Every service startup includes logging to file and stdout
- **Retention**: Keep logs from all eval attempts for 24h (helps with debugging)
- **Accessibility**: Report log path in error messages: "Service failed. See logs: /tmp/eval-logs/api-2025-02-15-143000.log"
- **Content**: Include: startup command, environment vars (sanitized), port binding, health check responses
- **Pattern**: Future-you will thank present-you for detailed logs

---

## Edge Cases & Fallback Paths

### Edge Case 1: Partial startup (some services up, some down)

**Problem**: API started, DB failed to start. Scenario runs, fails mysteriously. Looks like API bug but it's infrastructure.

**Diagnosis**: 
- API healthy check passes (port 3000 responds)
- DB health check fails (port 5432 doesn't respond)
- Services are in mixed states: some ready, some broken

**Action**:
- Health check ALL services in parallel. Collect results.
- Define "critical": Services in dependency chain for eval scenario
  - Example: For web eval scenario: API MUST be up, DB MUST be up. Redis is optional.
  - Example: For mobile eval scenario: Auth service MUST be up. Analytics service is optional.
- If ANY critical service fails: STOP. Do not proceed with partial stack.
- If only non-critical services fail: Log warning and proceed with degradation note.

**Fallback**:
```
PARTIAL FAILURE DETECTED
API started ✅, DB failed ❌, Redis failed ❌
Critical services for this eval: API ✅, DB ❌

Result: Cannot proceed. DB is critical.
Error: Database startup failed. Check logs: docker logs db-container | tail -30
Fix: Restart database, verify port 5432 is not in use, check /data/db is writable
```

---

### Edge Case 2: Resource exhaustion (port already in use)

**Problem**: Port 3000 in use by old process from previous eval. New API service fails to bind.

**Diagnosis**:
- Service startup command runs
- Logs show: "EADDRINUSE: address already in use :::3000"
- Port scan shows: 3000 is listening (old process)

**Action**:
- Before starting any service: check if port is available
- Command: `lsof -ti :3000` (returns PID if in use)
- If port in use:
  - Check if safe to kill: `ps aux | grep $(lsof -ti :3000)` - is it an old eval process?
  - If old process: kill it: `lsof -ti :3000 | xargs kill -9`
  - If unknown process: ask user before killing
- Retry service startup after port is free

**Fallback**:
```
Port 3000 already in use.
Current process: node /app/backend-api/server.js (PID 4521)
Started: 2025-02-15 12:30:15 (3 hours ago)

Action: Kill old process
$ lsof -ti :3000 | xargs kill -9

Retry: npm run dev (this eval)
```

---

### Edge Case 3: Slow startup (services take >10s to be ready)

**Problem**: Health check succeeds but service not actually ready. First eval request fails with 503.

**Diagnosis**:
- Health check: GET /health → 200 OK (marks as healthy)
- First eval request: GET /api/products → 503 Service Unavailable
- Service is up but not initialized (DB connections warming up, cache loading, etc.)

**Action**:
- Add "wait-until-ready" logic beyond health check endpoint
- For HTTP services: Check /health AND verify response time < 100ms (service not overloaded)
- For DB services: Check port responding AND verify test query (SELECT 1) succeeds
- For cache services: Check port responding AND verify SET/GET cycle works
- Polling: Retry up to 10 times with 1s interval (10s total)

**Fallback**:
```
Health check passed but service initialization slow.
Service: backend-api
Port: 3000 responding
Health endpoint: GET /health → 200
Service readiness: Polling initialization...

Attempt 1: test query failed (DB warming up)
Attempt 2: test query failed 
Attempt 3: test query succeeded (service ready)

Result: Backend API is fully initialized and ready for eval
```

---

### Edge Case 4: Missing dependencies (service depends on file, env var)

**Problem**: Service needs config file, it's not there. Service starts but fails immediately with cryptic error.

**Diagnosis**:
- Service startup: starts process (no error from start command)
- Service health check: fails to connect (port never opened)
- Logs show: "Error: ENOENT: no such file or directory /app/config.json"

**Action**:
- Pre-flight check: Verify all config files exist before starting service
- Pre-flight check: Verify all REQUIRED env vars set
- For each service, define required files and env vars in forge-product.md
- Example:
  ```yaml
  backend-api:
    required_files:
      - /app/config.json
      - /app/.env
    required_env:
      - DATABASE_URL
      - API_KEY
  ```
- Before startup, verify all required files exist: `test -f $file || fail`

**Fallback**:
```
Pre-flight check failed: Missing required config
Service: backend-api
Missing file: /app/config.json

Solution: Copy from template
$ cp /app/config.example.json /app/config.json
$ # Edit config.json with your settings
$ # Retry startup
```

---

### Edge Case 5: Database migrations incomplete

**Problem**: DB is up but schema not migrated. Queries fail with "table doesn't exist".

**Diagnosis**:
- MySQL service: health check passes (port 3306 responds)
- Service startup: starts but queries fail with "Error: Table 'users' doesn't exist"
- Migration script: not run or failed silently

**Action**:
- After DB starts, immediately run migrations
- Check migration status: Query database for schema version or check migration log file
- Wait for migrations to complete (timeout: 60s per migration file)
- Verify critical tables exist: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'mydb'`
- Only proceed to next service after migrations complete

**Fallback**:
```
Database migrations failed
Service: mysql
DB is running but schema incomplete

Log output:
[2025-02-15 14:30:15] Running migration 001_create_users_table.sql
[2025-02-15 14:30:15] ERROR: Cannot add foreign key constraint

Solution: Check migration file
$ cat migrations/001_create_users_table.sql | grep FOREIGN KEY
Fix constraint issue and retry
$ docker-compose down mysql
$ docker-compose up -d mysql
$ npm run db:migrate
```

---

### Edge Case 6: Eventual consistency windows

**Problem**: DB up, cache up, but they're not synced yet. Cache sync is async every 30s. Eval tests against stale cache.

**Diagnosis**:
- Both services healthy: DB ✅, Redis ✅
- Service writes to DB
- Service reads from Redis
- Redis has old data (sync hasn't happened yet)
- Test fails: expected data not in cache

**Action**:
- Document sync windows in service metadata
- For services with eventual consistency, add explicit "wait for cache sync" step
- Example: After data write, poll cache until it returns latest data (max 30s wait)
- Use cache version or timestamp to verify cache is synced to DB

**Fallback**:
```
Service has eventual consistency window
Service: product-cache-sync
Sync interval: 30 seconds (async)

When eval depends on fresh cache:
1. Write data to DB
2. Wait for cache to sync: poll /cache/sync-status until version matches DB version
3. Only then run eval

Timeout: 35s (30s sync + 5s buffer)
If timeout: fail with "Cache sync timeout. Possible infrastructure issue."
```

---

### Edge Case 7: Cleanup from previous run

**Problem**: Previous eval didn't shut down cleanly. Old containers/volumes still exist. New stack can't start.

**Diagnosis**:
- Docker: `docker ps -a | grep eval` shows stopped containers from yesterday
- Volumes: `docker volume ls | grep eval` shows orphaned volumes
- PM2: `pm2 list | grep eval` shows stopped processes with old PIDs
- Ports: `lsof -ti :3000` shows process from previous run
- Start command fails: "Bind address already in use" or "Container already exists"

**Action**:
- Before starting fresh stack: attempt graceful shutdown of old services
- Sequence:
  1. Check for running eval processes/containers: `docker ps | grep eval`, `pm2 list`
  2. Gracefully stop them: `docker-compose down` (from previous stack dir), `pm2 stop [id]`
  3. Wait 3s for cleanup
  4. Verify nothing still running: `lsof -ti :3000` should return nothing
  5. Only then start fresh stack
- If graceful shutdown fails, use forceful cleanup (see Shutdown Patterns section)

**Fallback**:
```
Cleanup from previous run
Found old eval containers: backend-api (exited 2h ago), mysql (exited 2h ago)

Attempting graceful shutdown...
$ cd /home/eval/previous-run
$ docker-compose down

Waiting 3 seconds for cleanup...

Verifying ports free...
Port 3000: free ✅
Port 5432: free ✅
Port 6379: free ✅

Ready to start fresh stack
```

---

## Stack Startup Patterns

Choose one pattern based on your stack requirements:

### Pattern 1: Sequential Startup with Cascading Health Checks

**Use when**: Strict ordering required (e.g., migrations before API, DB before cache sync)

**Process**:
```
1. Start leaf services (no dependencies): MySQL, Redis, Kafka, Elasticsearch
   - For each: execute start command, wait for port open, health check
   - Timeout: 10s per service
   - If any fails: STOP, error out with detailed message

2. Health check each leaf service until responding
   - Verify connectivity (MySQL PING, Redis PING, Kafka topic list)
   - If health check fails after 5 retries: STOP

3. Run database migrations (if applicable)
   - For each migration file: execute it
   - Timeout: 60s per file
   - Verify migration completed: check DB schema version
   - If migration fails: STOP, show logs

4. Start mid-tier services (depend on infra): API, cache-sync, workers
   - For each: execute start command, wait for port open, health check
   - Timeout: 15s per service
   - If any fails: STOP

5. Start top-tier services (depend on mid-tier): Web UI, mobile app
   - For each: execute start command, health check
   - Timeout: 15s per service
   - If any fails: STOP

6. Final integration health check
   - Web → API → DB flow: simulate real request path
   - If fails: STOP

7. Status: If all green, ready for eval. If any red, rollback all and error.
```

**Example**: ShopApp (MySQL → Redis → API → Web)
```
[14:30:00] Starting MySQL...
[14:30:05] MySQL health check: PING → PONG ✅
[14:30:05] Running migrations (3 files)...
[14:30:15] Migrations complete ✅
[14:30:15] Starting API...
[14:30:20] API health check: GET /health → 200 ✅
[14:30:20] Starting Web...
[14:30:25] Web health check: GET / → 200 ✅
[14:30:25] Integration check: Web → API → DB ✅
[14:30:25] SUCCESS: Stack ready for eval
```

---

### Pattern 2: Parallel Startup with Health Tolerance

**Use when**: Services have no strict ordering and partial degradation is acceptable

**Process**:
```
1. Start all services in parallel (no deps)
   - Fire off start commands for all services immediately
   - Don't wait for one to finish before starting next

2. Health check with timeout (30s max per service)
   - Poll all services in parallel
   - Record health for each: healthy|unhealthy|timeout

3. Evaluate: Is failed service critical for this scenario?
   - Critical services: must be healthy (e.g., API for API scenarios)
   - Optional services: can be unhealthy (e.g., Analytics for core flow)
   - Define criticality per scenario in forge-product.md

4. Logic:
   - If critical service unhealthy: Rollback all and error
   - If optional service unhealthy: Log warning and proceed with degradation
   - If all critical services healthy: Proceed

5. Output includes degradation note: "Stack started with warnings: Analytics offline"
```

**Example**: Analytics platform (API, Analytics, Reporting all independent)
```
[14:30:00] Starting services in parallel...
  - API: starting
  - Analytics: starting
  - Reporting: starting

[14:30:10] Health checks...
  - API: healthy ✅
  - Analytics: unhealthy (timeout) ❌
  - Reporting: healthy ✅

[14:30:10] Evaluating...
  - API: CRITICAL → healthy ✅
  - Analytics: optional → unhealthy but OK
  - Reporting: CRITICAL → healthy ✅

[14:30:10] SUCCESS: Stack ready with degradation
Warning: Analytics service offline. Core eval will proceed.
```

---

### Pattern 3: Docker Compose (All or Nothing)

**Use when**: Services are containerized and fully defined in compose file

**Process**:
```
1. Execute: docker-compose up -d
   - Starts all containers defined in compose file
   - Docker handles ordering based on depends_on

2. Wait until all services healthy
   - Poll each service's health check endpoint
   - Use docker health check status: `docker ps --filter "health=healthy"`
   - Timeout: 30s total (services should be up by then)

3. Verify with integration check
   - Simulate real request flow (optional)
   - If passes: ready for eval
   - If fails: error out with logs from docker-compose logs

4. All or nothing: Either all services up and healthy, or fail completely
   - No partial stacks
   - If one service fails, `docker-compose down` and error
```

**Example**: docker-compose.yml with health checks
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    ports:
      - 5432:5432
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 2s
      retries: 5
  
  api:
    image: my-api:latest
    depends_on:
      mysql:
        condition: service_healthy
    ports:
      - 3000:3000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 5s
      timeout: 2s
      retries: 5
```

**Execution**:
```
[14:30:00] $ docker-compose up -d
Creating mysql... done
Creating api... done

[14:30:05] Waiting for health checks...
mysql: starting
api: starting (waiting for mysql)

[14:30:15] Health status check:
mysql: healthy ✅
api: healthy ✅

[14:30:15] SUCCESS: All services healthy and ready
```

---

## Shutdown Patterns

### Graceful Shutdown

**Use for normal eval completion or controlled shutdown**

```
1. Stop accepting new requests (if applicable)
   - API: Stop accepting new connections, close listen socket

2. Wait for in-flight requests to complete (timeout: 30s)
   - Track requests in progress
   - Log warning if requests still in flight after 30s
   - Force close if still pending after 30s

3. Flush caches/queues
   - Redis: Flush all keys or selective flush
   - Message queue: Drain unprocessed messages to database
   - Temporary storage: Clean up temp files

4. Close connections cleanly
   - Database: Close connection pools gracefully
   - Cache: Close connection gracefully
   - File descriptors: Close all open files

5. Stop containers/processes
   - PM2: pm2 stop <service-name>
   - Docker: docker-compose down (with timeout)
   - Systemd: systemctl stop <service>

6. Clean up volumes (optional, keep for debugging)
   - Keep docker volumes for post-eval diagnostics
   - Delete temp directories created during startup
   - Keep logs for debugging
```

**Example sequence** (Docker Compose):
```bash
#!/bin/bash

echo "Stopping eval stack gracefully..."

# 1. Signal services to stop (SIGTERM)
docker-compose stop --timeout=30

# 2. Wait for graceful shutdown (verify logs)
echo "Waiting for clean shutdown..."
sleep 5

# 3. Verify all stopped
RUNNING=$(docker-compose ps --services --filter "status=running")
if [ -n "$RUNNING" ]; then
  echo "Warning: Some services still running: $RUNNING"
fi

# 4. Remove containers (keep volumes)
docker-compose down

# 5. Clean temp directories
rm -rf /tmp/eval-stack-*

echo "Graceful shutdown complete"
```

---

### Forceful Shutdown (Recovery from stuck state)

**Use when graceful shutdown failed or stack is in broken state**

```
1. Kill all running processes/containers
   - docker-compose down -v (kill containers, remove volumes)
   - pkill -f "npm run dev" (kill node processes)
   - pm2 kill (kill all pm2 managed processes)

2. Clean up all resources
   - Remove docker volumes: docker volume rm $(docker volume ls -q)
   - Clean temp directories: rm -rf /tmp/eval-*
   - Clear port bindings: lsof -ti :PORT | xargs kill -9 (for each port)

3. Verify clean slate
   - ps aux | grep eval (should show nothing)
   - lsof -i :3000 (should show nothing)
   - docker ps (should show nothing)

4. Ready for fresh start
```

**Example sequence** (forced):
```bash
#!/bin/bash

echo "Forcing shutdown of eval stack (may lose data)..."

# Nuclear option
docker-compose down -v
pkill -9 -f "eval-product"
pm2 kill

# Clean up all traces
rm -rf /tmp/eval-stack-*
rm -rf /tmp/forge-eval-*

# Kill any lingering processes on eval ports
lsof -ti :3000 | xargs kill -9 2>/dev/null || true
lsof -ti :5432 | xargs kill -9 2>/dev/null || true
lsof -ti :6379 | xargs kill -9 2>/dev/null || true

echo "Forced shutdown complete. Slate cleaned."
```

---

## Integration with Eval Framework

After this skill completes:
- Stack is running and healthy
- All service endpoints are reachable
- Databases are initialized and healthy
- All critical services verified and ready
- Pre-flight checks passed
- Ready for eval-driver-* skills to run test scenarios
- Use eval-driver-api-http for REST API tests
- Use eval-driver-db-mysql for database verification
- Use eval-driver-cache-redis for cache tests
- Use eval-driver-bus-kafka for event bus tests

On eval completion or failure:
- Use graceful or forceful shutdown patterns (above)
- Preserve logs and volumes for debugging
- Clean up temp directories and processes

## Checklist

Before declaring stack ready for eval:

- [ ] `forge-product.md` read fresh at start of this stack-up (not cached from prior run)
- [ ] Services started in topological dependency order (infra before services)
- [ ] All service health checks returned healthy (no skipped checks)
- [ ] Total stack startup completed under 30 seconds
- [ ] No partial stack — all critical services verified ready
- [ ] Stack-up log available for debugging if any eval scenario fails
