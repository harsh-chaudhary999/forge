---
name: deploy-driver-docker-compose
description: "WHEN: Deployment target is Docker Compose. Provides up(compose_file), health_check(), and down() for multi-service orchestration."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.0
preamble-tier: 3
triggers:
  - "deploy with docker-compose"
  - "docker-compose deployment"
  - "spin up with compose"
allowed-tools:
  - Bash
  - Write
---

# Deploy Driver: Docker Compose

Deployment driver for Docker Compose-based service orchestration. Brings up services with `docker-compose up`, performs health checks via container inspection and HTTP endpoints, and tears down with `docker-compose down`. Handles multi-service startup ordering, dependency validation, and graceful cleanup.

## Anti-Pattern Preamble: Why Agents Skip Health Checks After docker-compose up

| Rationalization | The Truth |
|---|---|
| "docker ps shows all containers running, so the stack is ready" | Container running state means the process started. It does NOT mean the service is accepting requests. Always call `health_check()` after `up()`. |
| "depends_on in docker-compose handles startup ordering" | `depends_on` guarantees container start order, not readiness. Service B may try to connect to Service A before A finishes initialization. |
| "health checks slow down deployment — we can skip them in CI" | A deployment that skips health checks will report success while the stack is broken. CI failures caught late are 10x more expensive to diagnose. |
| "docker-compose down cleans everything up automatically" | Without `-v`, named volumes persist. Stale database volumes cause schema mismatch failures on the next `up()`. Always use `down -v`. |
| "container restart policy means transient crashes self-heal" | Restart policy helps long-term stability, not deployment correctness. A crash loop during deployment means the config is wrong — not transient. |
| "network timeouts don't happen between containers on the same bridge network" | Bridge network DNS resolution and iptables rules can cause connection timeouts under resource pressure. Retry logic is required for service-to-service calls. |

## Iron Law

```
EVERY docker-compose up() MUST BE FOLLOWED BY health_check() BEFORE DECLARING DEPLOYMENT COMPLETE. NEVER MARK A STACK HEALTHY BASED ON CONTAINER STATE ALONE.
```

## HARD-GATE: Anti-Pattern Preambles

The following rationalizations **WILL BLOCK** your deployment. These are not edge cases—they are guaranteed failure modes that will surface in production.

### 1. "docker-compose depends_on will automatically handle service startup ordering"

**Why This Fails:**
- `depends_on` in docker-compose.yml guarantees container START order, not READINESS. Service A starts before Service B, but A may not be accepting connections when B tries to connect.
- MySQL container starts but hasn't finished initialization (still loading data directory). Application tries to connect, gets "too many connections" or "database not ready" errors.
- Startup order != initialization completion. TCP port bound ≠ service ready to accept traffic.
- Multi-service dependency chains (A→B→C) fail if B isn't truly ready when C starts, causing cascading failures.
- Health checks are the ONLY reliable way to verify readiness; depends_on is necessary but not sufficient.

**Enforcement:**
- MUST implement explicit health checks for every service with external dependencies (databases, caches, message queues).
- MUST NOT assume depends_on guarantees readiness; always verify via health_check() before declaring deployment success.
- MUST implement wait logic: retry connections with exponential backoff, not immediate failure on first connection refused.
- MUST log startup sequencing: record when each service starts, when health check begins, when service becomes ready.
- MUST validate complete stack is healthy before deployment success, not just "containers are running".

---

### 2. "Health checks aren't needed if services are running; docker ps shows status"

**Why This Fails:**
- `docker ps` shows container state (running) but NOT service readiness. Container running ≠ service accepting traffic.
- Application may be in crash loop: starts, crashes at t=2s, restarts, crashes again. At t=1.5s, health check catches it; `docker ps` shows "Up 3 seconds".
- Health endpoint misconfigured or returns wrong status code (200 but "service initializing" in body). Container appears healthy; actual service not ready.
- Dependencies may have failed (database unreachable, cache timeout). Container running; service broken. Health check via HTTP reveals this; `docker ps` doesn't.
- Silent failures in initialization: service binds port but core threads haven't started (workers, async jobs). Health check catches, `docker ps` doesn't.

**Enforcement:**
- MUST perform HTTP health checks against every service with network endpoints (not just container status checks).
- Health check endpoint MUST verify service dependencies (database connected, cache accessible, workers running), not just "is process alive".
- MUST implement multi-step health check: 1) container running, 2) HTTP endpoint responds, 3) response includes dependency health.
- MUST poll health endpoint with exponential backoff (starting 100ms, capping at 1000ms), not single check.
- MUST escalate if health check timeout indicates cascading failures (one service unhealthy causes others to unhealthy).

---

### 3. "Container failures are transient; services will restart automatically"

**Why This Fails:**
- restart_policy in compose file helps LONG-TERM stability, but during deployment it masks immediate failures. Service crashes at t=3s, restarts at t=4s. Health check at t=2s succeeds (not yet crashed), deployment reports success. At t=3.5s, service crashes, caller traffic fails.
- Crash loops (permanent exit code 1 or 127) will repeat forever. restart_policy="unless-stopped" will keep restarting, consuming resources indefinitely.
- Bad configuration in environment variables causes permanent failure that restart_policy can't fix. Service needs CONFIGAPI to be set; if not, crashes every restart.
- Deployment monitoring is responsibility of DEPLOY DRIVER, not docker-compose. We cannot rely on docker's restart policy; we must detect and escalate immediately.
- Restart delays (exponential backoff) mean service unavailable for seconds/minutes. Caller doesn't know, sends traffic, gets 503.

**Enforcement:**
- MUST monitor container restart count for first 30 seconds post-up(). If restart_count > 2, escalate (not transient, permanent issue).
- MUST capture error logs from crashed containers: `docker logs <container_id>` to identify root cause (missing config, bad syntax, dependency failure).
- MUST NOT rely on restart_policy for deployment success; detect crashes and fail fast.
- MUST log crash details: exit code, signal, error logs. Distinguish "out of memory" (resource issue) from "connection refused" (dependency issue).
- MUST require explicit escalation path for restart loops: human review required, not silent restart forever.

---

### 4. "Volume cleanup is automatic; removing containers automatically cleans volumes"

**Why This Fails:**
- `docker-compose down` WITHOUT `-v` flag leaves volumes in place. Over time, volumes accumulate, consuming disk space. After 100 deployments, /var/lib/docker/volumes grows to terabytes.
- Volume mounted to host directory may not be cleaned by `docker-compose down -v` (external volumes, named volumes). Stale data persists.
- Database volumes especially problematic: old schema, data corruption, incompatible state. New deployment brings up with stale volume, database migration fails.
- Permissions on volume directory may prevent cleanup (volume owned by docker, deploy script running as different user). Cleanup silently fails.
- Cascading failures: cleanup fails silently, next deployment uses stale volume, data corruption, discovery only during real traffic (incident).

**Enforcement:**
- MUST use `docker-compose down -v` in down() function, NEVER `docker-compose down` without `-v`.
- MUST verify volume removal: after down(), run `docker volume ls | grep <compose_project>` and confirm empty.
- MUST validate volume mount paths before up(): confirm writable, sufficient disk space (check `df -h` for mounted paths).
- MUST check for stuck volumes: `docker volume ls` before down(), and if volume exists post-down(), escalate.
- MUST log what was removed: services, containers, volumes. Helps debug if data unexpectedly missing.

---

### 5. "Network timeouts never happen; services on same network reach each other instantly"

**Why This Fails:**
- Inter-container networking via docker network may have latency, packet loss, or timeout (especially in resource-constrained environments or under load).
- Service A pings Service B via DNS. DNS resolution may timeout or fail if docker DNS is overloaded (too many containers, rapid creation/deletion).
- TCP connection from Service A to B may timeout if Service B is in CPU throttling or memory pressure. Connection refused (can't accept) different from connection timeout (slow response).
- Network namespace issues: bridge network misconfiguration, iptables rules, hairpin mode disabled. Containers can't reach each other despite both running.
- Encryption/TLS overhead: if services using HTTPS, TLS handshake adds latency. Health check timeout too short for TLS setup.

**Enforcement:**
- MUST implement connection retry logic with exponential backoff for service-to-service communication (not just first attempt).
- MUST distinguish connection refused (service not listening) from timeout (service listening but slow/hung). Each requires different escalation.
- MUST configure appropriate health check timeout for service type: 5s for simple HTTP, 15s for services with TLS, 30s for slow databases.
- MUST validate network connectivity between services during health check: service B should verify it can reach dependent services (A, database, cache).
- MUST log network diagnostics if health check fails: `docker network inspect <network>` to verify network exists, `docker logs <container>` to check for network errors.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│          Deploy Driver Docker Compose               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ File Parse   │  │ Docker Cmds  │                │
│  │ (YAML)       │  │ (CLI)        │                │
│  └──────────────┘  └──────────────┘                │
│         │                   │                       │
│         └───────┬───────────┘                       │
│                 ▼                                    │
│  ┌─────────────────────────────┐                   │
│  │  Service Orchestration      │                   │
│  │  • docker-compose up        │                   │
│  │  • depends_on verification  │                   │
│  │  • container inspection     │                   │
│  └─────────────────────────────┘                   │
│         │                                           │
│         ├─► [Up] Parse YAML, start containers      │
│         ├─► [Health] HTTP + container checks       │
│         └─► [Down] Stop + remove with cleanup      │
│                                                      │
│  ┌─────────────────────────────┐                   │
│  │  Dependency & State Mgmt    │                   │
│  │  • startup order validation │                   │
│  │  • health check polling     │                   │
│  │  • graceful shutdown        │                   │
│  └─────────────────────────────┘                   │
│                                                      │
│  ┌─────────────────────────────┐                   │
│  │  Error Recovery             │                   │
│  │  • crash detection (30s)    │                   │
│  │  • restart count monitoring │                   │
│  │  • volume cleanup validation│                   │
│  └─────────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`depends_on` is used without health check conditions** — `depends_on` guarantees start order, not readiness. STOP. Add `condition: service_healthy` with `healthcheck` blocks for every dependent service.
- **`docker-compose up` is called without waiting for health checks** — Services may accept connections before they are ready to serve. STOP. Verify each service's health endpoint before proceeding.
- **`docker-compose down` is skipped after a failed test** — Orphaned containers consume ports and resources for subsequent runs. STOP. Always call `down()` in cleanup, even on failure.
- **Volume mounts use absolute paths instead of project-relative paths** — Absolute paths break on different developer machines and in CI. STOP. Use relative paths from the compose file location.
- **`latest` image tag is used in compose file** — `latest` produces non-deterministic builds. STOP. Pin to exact image digest or version tag.
- **Multiple `docker-compose up` calls run in parallel without port isolation** — Port conflicts will cause random failures. STOP. Assign unique ports per parallel run or use network-level isolation.

## Overview

This skill provides a unified interface for:
- **up()** - Start services defined in a docker-compose.yml file with dependency validation
- **health_check()** - Verify service health via container status and HTTP endpoints
- **down()** - Stop and remove all services with complete cleanup validation

## API Functions

### up(compose_file, env_vars?)

Start services defined in a docker-compose.yml file with optional environment variables.

**Parameters:**
- `compose_file` (string) - Absolute path to docker-compose.yml
- `env_vars` (object, optional) - Environment variables to pass (e.g., `{DATABASE_URL: 'mysql://...'}`)

**Returns:**
```javascript
{
  services: [
    {
      name: string,           // Service name from compose file
      container_id: string,   // Docker container ID (short hash)
      status: string,         // "running" | "exited" | "unhealthy"
      image: string,          // Image name and tag
      ports: [string]         // Published ports (e.g., ["3000:3000"])
    }
  ],
  compose_file: string,
  status: "started"
}
```

**Error Handling:**
- Throws if compose file does not exist
- Throws if docker-compose command fails
- Logs warnings for services that fail to start but doesn't block others
- Returns partial status if some services fail (status: "partial")

**Example:**
```javascript
const result = await up('/path/to/docker-compose.yml', {
  DATABASE_URL: 'mysql://localhost/shopapp',
  REDIS_URL: 'redis://localhost:6379',
  NODE_ENV: 'test'
});

console.log(result.services);
// [
//   { name: 'backend-api', container_id: 'abc123...', status: 'running', ... },
//   { name: 'mysql-db', container_id: 'def456...', status: 'running', ... }
// ]
```

---

### health_check(compose_file, service_name, port, endpoint, timeout?)

Check service health via container inspection, HTTP endpoint polling, and log verification.

**Parameters:**
- `compose_file` (string) - Absolute path to docker-compose.yml
- `service_name` (string) - Service name in compose file (e.g., 'backend-api')
- `port` (number) - Port to check (e.g., 3000)
- `endpoint` (string) - HTTP endpoint to poll (e.g., '/health', '/api/health')
- `timeout` (number, optional) - Max wait time in milliseconds (default: 30000)

**Returns:**
```javascript
{
  healthy: boolean,
  service_name: string,
  checks: {
    container_running: boolean,
    http_response_ok: boolean,
    status_code: number | null,
    response_time_ms: number | null,
    error_logs: [string]
  },
  timestamp: string (ISO 8601)
}
```

**Polling Strategy:**
1. Check container is running: `docker inspect <container_id> --format '{{.State.Running}}'`
2. Poll HTTP endpoint with exponential backoff (100ms → 500ms → 1000ms intervals)
3. Accept 2xx status codes as healthy
4. On persistent failure, capture last 10 error log lines: `docker logs <container_id>`

**Error Handling:**
- Returns `{healthy: false, ...}` if timeout exceeded (no throw)
- Captures and returns stderr/logs for debugging
- Handles connection refused gracefully during startup

**Example:**
```javascript
const health = await health_check(
  '/path/to/docker-compose.yml',
  'backend-api',
  3000,
  '/health',
  60000  // 60 second timeout
);

if (health.healthy) {
  console.log('Service ready at localhost:3000/health');
} else {
  console.log('Health check failed:', health.checks.error_logs);
}
```

---

### down(compose_file)

Stop all services and remove containers, networks, and volumes defined in the compose file.

**Parameters:**
- `compose_file` (string) - Absolute path to docker-compose.yml

**Returns:**
```javascript
{
  status: "stopped",
  compose_file: string,
  services_removed: number,
  volumes_removed: number,
  timestamp: string (ISO 8601)
}
```

**Behavior:**
- Runs: `docker-compose -f <file> down -v` (removes volumes)
- Waits for graceful shutdown (default 10s)
- Logs all removed resources
- No error if services already stopped

**Error Handling:**
- Logs warnings if some resources can't be removed
- Still succeeds even if partial cleanup fails
- Returns status: "stopped" on success

**Example:**
```javascript
const result = await down('/path/to/docker-compose.yml');
console.log(`Removed ${result.services_removed} services, ${result.volumes_removed} volumes`);
```

---

## Edge Cases with Concrete Scenarios

Edge cases that WILL occur in production. Each requires specific detection and recovery logic.

### Edge Case 1: Partial Service Startup (Some Containers Up, Some Down)

**Scenario:**
You call `up()` with a 3-service stack: web-api, mysql-db, redis-cache. docker-compose starts all three. Web-api and redis start successfully. But mysql fails to start because the default port 3306 is already in use (stale mysql container from previous failed deployment). docker-compose returns success (some services started), but the stack is incomplete. Web-api health check begins polling, tries to connect to mysql. Connection refused. Health check fails. But the root cause (port conflict, not web-api broken) is hidden in docker output.

**How to Detect:**
- `docker ps` shows 2 of 3 containers running, not all 3.
- `docker-compose ps` output shows some services with status "Up" and others with status "Error" or "Exited".
- Health check times out because dependency (mysql) is unreachable.
- docker-compose logs show port conflict: `port 3306 already in use` or similar.

**What Happens:**
- Deployment returns partial success (up() succeeds because some services started).
- Health check fails due to missing dependency, deployment fails.
- Operator debugs health check endpoint, finds "database unreachable", blames application code.
- Root cause (port conflict from stale container) not obvious without checking docker logs.
- Stale container remains running, consuming resources, blocking future deployments.

**Mitigation Steps:**
1. Detect: After up(), verify ALL services specified in compose file are running:
   ```javascript
   const result = await up('/path/docker-compose.yml')
   const all_running = result.services.every(s => s.status === 'running')
   if (!all_running) {
     const failed = result.services.filter(s => s.status !== 'running')
     throw new Error(`PARTIAL_STARTUP: services failed to start: ${failed.map(s => s.name).join(', ')}`)
   }
   ```
2. Escalate: Check docker logs for the failed services to identify root cause:
   ```javascript
   for (const service of failed) {
     const logs = exec(`docker-compose -f ${compose_file} logs ${service.name}`)
     if (logs.includes('Address already in use')) {
       throw new Error(`PORT_CONFLICT: ${service.name}`)
     }
   }
   ```
3. Recovery: For port conflicts, identify the stale container:
   ```bash
   docker ps | grep 3306
   docker rm -f <stale_container_id>
   # Retry deployment
   ```
4. Prevention: Before up(), check if ports are available: `lsof -i :3306 -i :6379 -i :3000` and fail if any are bound to unexpected processes.

---

### Edge Case 2: Dependency Ordering Issues (Service Startup Race)

**Scenario:**
Your compose file has Service A depends_on Service B. But Service B's database initialization is slow (migrations, data loading). depends_on guarantees A starts after B, but NOT that B is ready. A starts immediately when B's container is up, tries to connect to B's database, gets "Connection refused" (database still initializing). A crashes. Restart policy restarts A. B's database finally ready at t=5s. A retries, now succeeds. Health check at t=3s catches only the first failure, deployment fails (but only transiently—if we waited, it would succeed).

**How to Detect:**
- Service A shows high restart_count in `docker-compose ps` or `docker inspect`.
- A's logs show "Connection refused", "Database not ready", or similar early in startup.
- Multiple restart attempts visible: `docker logs <service_a> | grep -c "Connection refused"` > 1.
- Order of log messages shows A trying to connect before B logs "Ready to accept connections".

**What Happens:**
- Health check times out or fails due to A's crashes.
- If health check waits long enough, A recovers, health check eventually succeeds.
- But if health check timeout is too short, deployment fails even though stack would stabilize.
- Appears to be application bug (crashes on startup), but root cause is startup ordering.

**Mitigation Steps:**
1. Detect: Monitor restart count for each service during first 30 seconds:
   ```javascript
   for (const service of result.services) {
     const inspect = JSON.parse(exec(`docker inspect ${service.container_id}`))
     const restart_count = inspect[0].RestartCount
     if (restart_count > 2) {
       logger.warn(`SERVICE_RESTARTING: ${service.name} restart_count=${restart_count}`)
     }
   }
   ```
2. Escalate: If any service restarting, extend health check timeout:
   ```javascript
   const has_restarts = result.services.some(s => s.restart_count > 0)
   const timeout = has_restarts ? 60000 : 30000
   const health = await health_check(compose_file, service, port, endpoint, timeout)
   ```
3. Recovery: Check Service B's logs to verify initialization is actually progressing:
   ```bash
   docker logs <service_b> | tail -20
   # Look for "Ready to accept connections", "initialization complete", etc.
   ```
4. Prevention: Ensure every service has a proper health check endpoint. Service B should not report healthy until database is fully initialized. Add explicit wait logic in service startup script: `wait-for-it.sh <service_b>:3306 -- node app.js` before attempting connection.

---

### Edge Case 3: Container Health Check Timeout (Service Not Responding)

**Scenario:**
Your application's health endpoint is slow or broken. Health check polls `/health` endpoint with 30-second timeout. At t=25s, the health endpoint finally responds, but with a 500 error (Service initialization bug). Health check retries. At t=45s (total elapsed), health check times out, deployment fails. But the service is actually running fine; the health endpoint is just badly configured (too slow, or returns wrong status code). The service would work for real traffic, but deployment fails due to health check configuration mismatch.

**How to Detect:**
- Health check timeout consistently at 30+ seconds, not transient.
- Logs show `/health` endpoint responding with 500, 502, 503 errors.
- Container logs show no errors; service appears normal ("listening on port 3000", no exceptions).
- HTTP response time to health endpoint very high (5+ seconds per request), slowing down retries.

**What Happens:**
- Deployment fails even though service is actually functional (works for real traffic).
- Operator debugs application code, finds nothing wrong.
- Realizes health endpoint is misconfigured (too slow, wrong status code), not application.
- Manual restart/fix of health endpoint, then deployment succeeds.
- Lost time debugging, deployment blocked, SLA impact.

**Mitigation Steps:**
1. Detect: Log every health check attempt including response time:
   ```javascript
   for (let attempt = 0; attempt < max_retries; attempt++) {
     const start = Date.now()
     const response = await curl(`http://localhost:${port}${endpoint}`)
     const latency = Date.now() - start
     logger.info(`HEALTH_CHECK_ATTEMPT`, {
       attempt, 
       status: response.status, 
       latency_ms: latency,
       timeout_remaining: timeout - (Date.now() - start_time)
     })
   }
   ```
2. Escalate: If latency consistently > 5 seconds or status code not 2xx, escalate:
   ```javascript
   if (response.status !== 200 || latency > 5000) {
     logger.error(`HEALTH_CHECK_ISSUE: status=${response.status}, latency=${latency}ms`)
     // Consider increasing timeout or escalating
   }
   ```
3. Recovery: Verify health endpoint is working correctly:
   ```bash
   curl -v http://localhost:3000/health
   # Check response time, status code, body content
   docker logs <container> | grep -i "health"
   ```
4. Prevention: Test health endpoint before deployment: `curl -w "@time-format.txt"` to measure response time. Configure timeout as 3x observed latency, minimum 5 seconds. Ensure health endpoint is simple and fast (no DB queries if possible).

---

### Edge Case 4: Volume Mount Permission Errors

**Scenario:**
Your compose file mounts a host directory into a container: `volumes: ["./data:/app/data"]`. The `./data` directory exists on the host with permissions `0755` owned by user `app:app`. But docker-compose runs as `root` (or different user). Container volume mount fails with "Permission denied". docker-compose reports the service "Error" state or "Exited". Health check can't even start because container isn't running. Deployment fails with unclear error message ("container exited").

**How to Detect:**
- `docker-compose ps` shows service status "Exited" or "Error", not "Up".
- `docker logs <container_id>` shows "Permission denied" or "Read-only file system".
- `docker inspect <container_id>` shows Mounts section with read-only=true when expecting writable.
- Host directory permissions don't match container user (volume mounted but inaccessible).

**What Happens:**
- Container can't write to volume (database can't create tables, application can't write logs).
- Service crashes or hangs, health check fails.
- Operator doesn't realize it's a permission issue (error message not clear).
- Rebuilds container, changes code, restarts process—root cause still not fixed.
- Cascading: multiple volumes affected, multiple services fail.

**Mitigation Steps:**
1. Detect: After up(), verify all volume mounts succeeded:
   ```javascript
   for (const service of result.services) {
     const inspect = JSON.parse(exec(`docker inspect ${service.container_id}`))
     const mounts = inspect[0].Mounts || []
     for (const mount of mounts) {
       if (!mount.Source || !mount.Destination) {
         throw new Error(`VOLUME_MOUNT_FAILED: ${service.name} mount missing source or dest`)
       }
     }
   }
   ```
2. Escalate: If container exited, check logs for permission errors:
   ```bash
   docker logs <container_id> | grep -i "permission\|read-only"
   ```
3. Recovery: Fix permissions on host directory:
   ```bash
   chmod 777 ./data  # Make writable by all users
   # Or: chown <docker_user> ./data
   # Retry deployment
   ```
4. Prevention: Document volume requirements in compose file (required permissions). Before up(), verify host directories exist and are writable: `test -w ./data || mkdir -p ./data && chmod 777 ./data`. Use bind mounts with explicit permissions instead of relying on defaults.

---

### Edge Case 5: Network Namespace Issues (Services Can't Reach Each Other)

**Scenario:**
Your compose file defines multiple services on a custom docker network. Service A (web-api) needs to reach Service B (database) via hostname `db` on the docker network. But docker's DNS or network configuration is broken. Service A's DNS request for `db` fails (returns NXDOMAIN or times out). Service A can't connect to Service B even though both are running on the same network. Connection times out. Health check for Service A fails (can't reach database). Deployment fails.

**How to Detect:**
- Service A logs show "Cannot resolve hostname db", "getaddrinfo ENOTFOUND db", or "Connection timed out".
- `docker network inspect <network_name>` shows both services connected.
- Running `docker exec <service_a> nslookup db` returns "NXDOMAIN" or hangs.
- Pinging between containers fails: `docker exec <service_a> ping -c 1 db` times out.
- No iptables rules or network policies blocking traffic (verified with `iptables -L`).

**What Happens:**
- Service A can't connect to Service B, crashes or hangs.
- Health check times out waiting for service readiness.
- Deployment fails, but error message unclear ("connection refused" vs. "hostname resolution failed").
- Difficult to diagnose without examining docker network and DNS state.

**Mitigation Steps:**
1. Detect: Perform basic network connectivity check during health check:
   ```javascript
   // In health check, verify service can resolve dependencies
   const dns_check = exec(`docker exec ${service_a_id} nslookup ${service_b_hostname}`)
   if (dns_check.exit_code !== 0) {
     throw new Error(`DNS_RESOLUTION_FAILED: ${service_a_name} cannot resolve ${service_b_hostname}`)
   }
   ```
2. Escalate: Inspect docker network:
   ```bash
   docker network inspect <network_name>
   # Verify all services are connected
   docker network inspect <network_name> --format='{{json .Containers}}'
   ```
3. Recovery: Restart docker network or recreate network:
   ```bash
   docker-compose down
   docker network rm <network_name>
   docker-compose up  # Will recreate network
   ```
4. Prevention: Test network connectivity before deployment: `docker exec <service_a> ping -c 1 <service_b>` in a pre-flight check. Verify all services are connected to the network: `docker network inspect | grep <service_name>`. Use `networks` section in compose file to explicitly define network and service membership.

---

### Edge Case 6: Resource Exhaustion (Disk Space, Memory, CPU)

**Scenario:**
Your host machine is low on disk space (90% full). docker-compose attempts to start a large MySQL container. Docker image layers need to be extracted (20GB). Disk space runs out during extraction. Container creation fails with "No space left on device". Service doesn't start. Health check timeout. Deployment fails. Meanwhile, the partial image extraction consumes the remaining disk space, breaking other services.

**How to Detect:**
- `docker-compose up` logs show "No space left on device" or "read-only file system".
- `df -h` shows `/var/lib/docker` mounted partition > 95% full.
- `docker system df` shows large images or containers consuming space.
- docker logs show OOM (Out Of Memory) kills: `Killed` or `137` exit code.
- CPU usage constantly at 100%, services slow to start.

**What Happens:**
- Container startup fails due to resource constraints.
- Deployment fails, host system now in degraded state (low disk, high memory).
- Subsequent deployments also fail (resources still exhausted).
- May require host cleanup, disk space freeing, before deployment can retry.

**Mitigation Steps:**
1. Detect: Before up(), verify sufficient resources:
   ```javascript
   // Check disk space
   const disk = exec(`df -h /var/lib/docker | awk 'NR==2 {print $5}'`)
   const disk_percent = parseInt(disk.replace('%', ''))
   if (disk_percent > 80) {
     throw new Error(`DISK_FULL: ${disk_percent}% used on /var/lib/docker`)
   }
   
   // Check memory
   const memory = exec(`free -h | awk 'NR==2 {print $7}'`)
   const mem_available_gb = parseFloat(memory.split('G')[0])
   if (mem_available_gb < 2) {
     throw new Error(`INSUFFICIENT_MEMORY: only ${mem_available_gb}GB available`)
   }
   ```
2. Escalate: If resources insufficient, don't attempt deployment:
   ```javascript
   if (disk_percent > 80 || mem_available_gb < 2) {
     logger.error('RESOURCE_EXHAUSTION: cleanup required before deployment')
     // Don't proceed, escalate to operations
   }
   ```
3. Recovery: Free up disk space:
   ```bash
   docker system prune -a  # Remove unused images, containers, volumes
   docker image prune -a   # Remove unused images
   # Clear old volumes: docker volume rm <volume_id>
   ```
4. Prevention: Monitor disk usage continuously (separate from deployment). Set up alerts for > 80% disk usage. Configure resource limits in compose file: `mem_limit: 2g`, `cpus: 1.0` per service. Use smaller base images, multi-stage builds to reduce layer size.

---

### Edge Case 7: Cascading Failures (One Service Failure Causes Others to Fail)

**Scenario:**
Your stack has: API (depends on Redis), Redis (depends on network), Network (depends on docker daemon). Redis starts but can't connect to network (network namespace broken). Redis crashes. API starts, tries to connect to Redis via hostname. Connection refused. API crashes. Orchestration logs show both API and Redis failed. But root cause is network, not Redis or API. Operator fixes Redis restart policy, increases memory, changes Redis config—none of these fix the root cause (network broken). Time wasted debugging wrong service.

**How to Detect:**
- Restart count escalates through dependent services: Redis restarts, then API restarts, then other services.
- Logs show error cascade: Redis error at t=1s, API error at t=2s, dependent service error at t=3s.
- All failures appear related but root cause is single point of failure (network, parent service).
- Depends_on dependency chain shows ordering: if root service doesn't start, all dependents fail.

**What Happens:**
- Multiple services appear unhealthy, operator doesn't realize they're failing due to single root cause.
- Debugging unfocused, attempts to fix multiple services instead of root cause.
- Time to recovery extended, multiple escalations needed.

**Mitigation Steps:**
1. Detect: Identify root cause service by ordering dependency chain:
   ```javascript
   // Parse compose file YAML to extract depends_on relationships
   const depends_on = parse_compose_dependencies(compose_yaml)
   // Build dependency graph
   // When services fail, traverse graph to find root failures (no dependencies, or all dependencies healthy)
   const root_failures = result.services.filter(s => 
     s.status !== 'running' && !depends_on[s.name]
   )
   ```
2. Escalate: Focus debugging on root cause services:
   ```javascript
   if (root_failures.length > 0) {
     logger.error(`ROOT_CAUSE_FAILURES: ${root_failures.map(s => s.name).join(', ')}`)
     // Log detailed info for root services only
   }
   ```
3. Recovery: Fix root cause services first, then verify dependent services recover:
   ```bash
   # Fix the root service
   # Wait for it to be healthy
   docker-compose up <root_service>
   # Then retry dependent services
   docker-compose up <dependent_service>
   ```
4. Prevention: Implement proper health checks and startup sequencing. Use `wait-for-it` scripts or explicit health check logic to ensure dependencies are truly ready before dependent services start. Log startup sequence with timestamps to identify which service failed first.

---

## Common Pitfalls

Pitfalls that surface repeatedly across deployments. Each requires proactive prevention and detection.

### Pitfall 1: Assuming depends_on Guarantees Readiness (It Only Guarantees Start Order)

**The Problem:**
You configure `service_a` to `depends_on: [service_b]`. You assume this means service_a will only start after service_b is fully initialized (database ready, port accepting connections). But `depends_on` only guarantees start order, not readiness. Service_b starts, service_a starts immediately after (b may still be initializing). Service_a tries to connect to b's database, gets "connection refused". Service_a crashes.

**Why It Happens:**
- Docker-compose `depends_on` is purely a startup order mechanism, not a readiness wait.
- Confusion between "container started" (docker-compose definition) and "service ready" (application perspective).
- Many tutorials show `depends_on` as sufficient, without mentioning explicit wait logic or health checks.

**Prevention:**
- Never rely on `depends_on` alone. Always implement explicit health checks for services with dependencies.
- Use wrapper scripts or wait-for-it tools: `wait-for-it.sh db:3306 -- node app.js` to ensure database port is accepting connections before starting application.
- Implement readiness probes in service startup: don't return "ready" until dependencies verified.
- Log dependency verification: "Waiting for database", "Database ready", etc. Helps debug startup order issues.
- Test startup sequence locally: verify each service waits for dependencies before initializing.

---

### Pitfall 2: Health Check Endpoint Misconfiguration

**The Problem:**
Your health endpoint `/health` returns 200 OK immediately after process starts, but the endpoint doesn't actually verify service readiness. Application appears healthy, health check passes, deployment succeeds. Real traffic arrives, tries to use unavailable features (database not connected, cache not warmed), gets 500 errors.

**Why It Happens:**
- Health endpoint only checks "is web server running", not "is application functional".
- No verification of dependencies (database, cache, external APIs) in health check.
- Health endpoint is too shallow: simple response without checking service state.
- Different apps define "healthy" differently (web server running vs. all workers ready vs. cache warmed).

**Prevention:**
- Design health endpoint to verify ALL critical dependencies:
  ```javascript
  GET /health returns {
    status: "ok",
    database: { connected: true, latency_ms: 45 },
    cache: { connected: true, latency_ms: 12 },
    workers: 5,  // Number of background workers running
    uptime_ms: 3500
  }
  ```
- Don't return 200 OK until all dependencies verified. Return 503 if any dependency missing.
- Document health endpoint requirements in compose file: what it checks, what it doesn't.
- Test health endpoint locally: disable database, verify endpoint returns error (not 200). Disable cache, verify endpoint returns error.

---

### Pitfall 3: Environment Variable Interpolation Ambiguity

**The Problem:**
Your compose file uses `DATABASE_URL=${DATABASE_URL}` to interpolate environment variables. You set `DATABASE_URL=postgres://localhost/db` in `.env` file. Compose file is generated and deployed. But the interpolation happened at compose generation time, not at runtime. If `.env` file is missing on deployment machine, interpolation produces empty string or wrong value. Database connection fails.

**Why It Happens:**
- Confusion between compose-time interpolation (when compose file is read) vs. runtime environment.
- `.env` file assumed to exist in deployment directory, but it's not copied or is out of date.
- Variable precedence unclear: which source is authoritative (compose file, .env, passed env vars, defaults).

**Prevention:**
- Document explicitly where each environment variable comes from.
- Use explicit defaults in compose file: `${DATABASE_URL:-postgres://localhost/db}` to provide fallback.
- Validate all required environment variables before `up()`: check DATABASE_URL, API_KEY, etc. are set correctly.
- Log interpolated values (sanitized) at deployment time: helps debug if wrong values used.
- Don't rely on `.env` file for critical deployments. Pass environment variables explicitly: `docker-compose -f compose.yml -e DATABASE_URL=... up`.

---

### Pitfall 4: Network Isolation Assumptions

**The Problem:**
You assume services on the same docker network are isolated from host and external networks. But a misconfigured service binds port 0.0.0.0:3000 (instead of 127.0.0.1:3000), making it accessible from outside the container network. Security boundary broken, service exposed to unexpected traffic.

**Why It Happens:**
- Port mapping `"3000:3000"` or `"0.0.0.0:3000:3000"` in compose file exposes service externally.
- Service binds wildcard address (0.0.0.0) instead of loopback (127.0.0.1), making it accessible from host and external networks.
- Assumption that docker network isolation is automatic, without explicit verification.

**Prevention:**
- Be explicit about port exposure: if service should only be internal, don't publish port in compose file.
- Use `localhost:3000:3000` or `127.0.0.1:3000:3000` to bind only to host loopback, not all interfaces.
- Verify network connectivity is as expected: test that service is NOT accessible from outside if not intended.
- Document network topology: which services communicate internally, which are exposed externally.
- Use network policies if available (docker labels, service mesh) to enforce isolation.

---

### Pitfall 5: Cleanup Failures Leaving Zombie Containers/Volumes

**The Problem:**
Your `down()` command runs `docker-compose down -v`. But one of the containers has a child process that's holding file lock on volume. Volume removal fails (resource busy). Error is logged but not escalated. Next deployment reuses stale volume with old data (database schema mismatch, files from previous version). Data corruption or startup failure.

**Why It Happens:**
- Cleanup assumed to succeed silently. Error logged but not propagated (down() returns success despite cleanup failure).
- Child processes (workers, background jobs) may still be holding resources even after parent process exits.
- Volume permissions or locks prevent removal (owned by different user, process still accessing).

**Prevention:**
- Always verify cleanup succeeded: after `down()`, run `docker-compose ps` and confirm all stopped. Run `docker volume ls` and confirm volume removed.
- Check for stuck containers: `docker ps -a | grep <compose_project>` should be empty after down().
- If cleanup fails, escalate (don't silently ignore): throw error, require manual intervention.
- Use `docker-compose down -v --remove-orphans` to clean up any orphaned containers/networks.
- Log what was removed: "Removed containers: web, db", "Removed volumes: data, cache". Helps verify cleanup completeness.

---

### Pitfall 6: Restart Policy Mismatches with Recovery Strategy

**The Problem:**
Your compose file specifies `restart_policy: always` for a service with permanent configuration error. Service crashes at t=0, restarts at t=1, crashes again, restarts at t=2, repeat forever. Health check succeeds early (before first crash), deployment reports success. At t=3, service crashes, customer traffic fails. Appears to be deployment success followed by service failure, but root cause is restart policy masking permanent error.

**Why It Happens:**
- Restart policy helps long-term stability but masks immediate startup failures during deployment.
- Health check window is too short; doesn't catch crash loop (check passes at t=2s, crash loop starts at t=5s).
- Permanent errors (bad config, missing dependency) are different from transient errors (race condition, temporary network blip). restart_policy handles transient well, ignores permanent.

**Prevention:**
- Monitor restart count for first 30 seconds post-up(). If restart_count > 2, escalate (indicates permanent issue, not transient).
- Use `restart_policy: on-failure` (not `always`), limits restart attempts: `restart_policy: on-failure:3` stops after 3 failures.
- Verify root cause if service restarting: check logs, don't rely on restart policy to magically fix it.
- Health check timeout should be long enough to catch early crashes: minimum 30-60 seconds, not 5 seconds.
- Log restart count as part of deployment success criteria: include in result, escalate if > 0.

---

### Pitfall 7: Port Mapping Conflicts Between Local Services

**The Problem:**
Your deployment assumes port 3000 is available. You publish port mapping `"3000:3000"` in compose file. But another service on the host (dev server, stray PM2 process, previous deployment) is already listening on 3000. docker-compose start fails with `bind: address already in use`. Deployment fails.

**Why It Happens:**
- Port availability assumed without checking.
- Multiple deployments running simultaneously (parallel CI/CD jobs, manual retries).
- Previous deployment or service not fully cleaned up (zombie holding port, TIME_WAIT state).
- Port hardcoded in compose file, no environment variable override.

**Prevention:**
- Always check port availability before deployment: `lsof -i :3000 -t` or `netstat -tulnp | grep 3000`.
- If port already in use, identify the process: `lsof -i :3000` shows which process is listening.
- Use configurable ports: `${PORT:-3000}` in compose file to allow override.
- In down(), ensure port is fully released before next deployment (check for TIME_WAIT, wait 5+ seconds if needed).
- Use dynamic port allocation if possible: `"3000"` (no host port, dynamic) instead of `"3000:3000"` (specific port).

---

## Decision Trees & Patterns

### Decision Tree 1: Service Startup Sequencing (When to Use depends_on, Health Checks, Wait Logic)

```
START: Deploying a docker-compose stack with multiple services
│
├─ Are services interdependent? (Does service A require service B to be running?)
│  ├─ NO: Services are independent
│  │   └─ No depends_on needed, can start all services in parallel
│  │
│  └─ YES: Service A depends on Service B
│       └─ Continue to readiness determination
│
├─ What defines "Service B is ready"?
│  ├─ Port binding: B must have port open (TCP, listening)
│  │   └─ Use `wait-for-it.sh b:PORT` or curl retry loop
│  │
│  ├─ Protocol ready: B accepts connections and responds
│  │   └─ Use HTTP health check (GET /health), check response status
│  │
│  ├─ Full initialization: B has loaded data, warmed caches, etc.
│  │   └─ Use comprehensive health endpoint checking all dependencies
│  │
│  └─ Custom condition: B logs "ready", or file exists, or API call succeeds
│       └─ Use custom wait script (poll log, check file, curl endpoint)
│
├─ Should you use compose `depends_on`?
│  ├─ YES, but ONLY as startup order hint:
│  │   ├─ Add to compose file: `depends_on: [service_b]`
│  │   └─ This guarantees A starts after B's container, NOT after B is ready
│  │
│  └─ You MUST ALSO add explicit wait logic:
│       ├─ Wrap startup: `wait-for-it.sh b:3306 -- node app.js`
│       ├─ Or add health check polling before returning success
│       └─ Or add startup script that retries connection to B with backoff
│
├─ After service startup, perform health check:
│  ├─ Initial delay: wait before first check (let app initialize)
│  │   └─ Lightweight apps: 500ms, Medium apps: 2s, Heavy apps: 10s
│  │
│  ├─ Polling: check service health repeatedly with exponential backoff
│  │   └─ 100ms → 200ms → 400ms → 800ms → 1000ms (cap at max interval)
│  │
│  ├─ Timeout: maximum wait time for health check to succeed
│  │   └─ Short apps: 10s, Medium apps: 30s, Heavy apps: 60s
│  │
│  └─ Success criteria: health endpoint returns 200, latency < baseline * 2, stable (2 checks in a row)
│
├─ Monitor for cascading failures:
│  ├─ If service B fails to start, A's startup fails (expected)
│  ├─ If B starts but fails health check, A's startup should fail too
│  ├─ Don't start dependent services if dependencies unhealthy
│  └─ Fail fast, don't mask failures with restart policies
│
└─ END: Stack either fully healthy, or deployment failed with identified root cause
```

**Implementation Guidance:**
- Use `docker-compose` `depends_on` for order, explicit health checks for readiness.
- Every service with external dependencies must have health check before deployment success.
- Distinguish connection errors (port not open) from response errors (port open, but service broken).
- Log startup timeline: "Service B starting", "Service B port open", "Service B health OK", "Service A starting", etc.
- If any health check fails, immediately check logs and dependency status before escalating.

---

### Decision Tree 2: Health Check Strategy by Service Type

```
START: Determining health check approach for service
│
├─ What type of service is this?
│  ├─ Stateless HTTP API (Express, FastAPI, Nginx, etc.)
│  │   ├─ Health endpoint: GET /health or /api/health
│  │   ├─ Check: HTTP 200 OK response
│  │   ├─ Timeout: 10 seconds (include TLS if HTTPS)
│  │   ├─ Latency baseline: < 100ms
│  │   └─ Dependency check: Verify backend/cache if API proxies them
│  │
│  ├─ Database service (MySQL, PostgreSQL, MongoDB)
│  │   ├─ Health check: TCP port open (no HTTP endpoint usually)
│  │   ├─ Check: Connection succeeds, query succeeds (SELECT 1)
│  │   ├─ Timeout: 15 seconds (includes initialization, schema load)
│  │   ├─ Latency baseline: < 50ms per query
│  │   └─ Initialization: Migrations completed, schema ready
│  │
│  ├─ Cache service (Redis, Memcached)
│  │   ├─ Health check: TCP port open, ping succeeds
│  │   ├─ Check: PING command returns PONG, set/get works
│  │   ├─ Timeout: 10 seconds
│  │   ├─ Latency baseline: < 10ms per operation
│  │   └─ No dependencies (cache service is leaf)
│  │
│  ├─ Message queue (RabbitMQ, Kafka)
│  │   ├─ Health check: HTTP management endpoint, or TCP port open
│  │   ├─ Check: Management API responds 200, queue/topic creation succeeds
│  │   ├─ Timeout: 20 seconds (includes cluster startup if clustered)
│  │   ├─ Latency baseline: < 100ms per operation
│  │   └─ Dependency: verify broker is leader (if clustered)
│  │
│  ├─ Background worker (Celery, Bull, Sidekiq)
│  │   ├─ Health check: HTTP endpoint or direct process check
│  │   ├─ Check: Worker process running, queue connection OK, can accept job
│  │   ├─ Timeout: 15 seconds
│  │   ├─ Latency baseline: < 100ms per check
│  │   └─ Dependency: verify queue service (Redis/RabbitMQ) is accessible
│  │
│  └─ Custom/Unknown service
│       ├─ Health check: Infer from service type (check logs, documentation)
│       ├─ Start with TCP port open, then HTTP if available
│       ├─ Timeout: 30 seconds (conservative)
│       └─ Document assumption: "Assuming service is ready when port accepts connection"
│
├─ Implement health check:
│  ├─ Use simple check if available: TCP connection, port binding
│  ├─ Use HTTP check if health endpoint exists: GET /health, expect 200
│  ├─ Use native protocol check if HTTP unavailable: PING (Redis), SELECT 1 (MySQL)
│  └─ Combine checks: port open AND (HTTP 200 OR protocol ping)
│
├─ Handle check failures:
│  ├─ Connection refused: service port not yet bound, retry
│  ├─ Connection timeout: service hung or not responding, escalate after max retries
│  ├─ HTTP error (500, 503): service running but broken, log and possibly escalate
│  ├─ Slow response (> baseline * 3): indicate overload/degradation, monitor but continue
│  └─ Each failure type requires different action
│
└─ END: Health check configured appropriately for service type
```

**Implementation Guidance:**
- Database health checks may require initialization verification (migrations completed).
- Cache health checks should verify data is accessible (not just port open).
- Queue health checks should verify broker can accept messages (not just process running).
- Worker health checks should verify connection to queue (not just process running).
- Document expected latency baseline for each service (for regression detection).
- If health check endpoint doesn't exist, implement one in the service (best practice).

---

### Decision Tree 3: Multi-Service Failure Recovery (Retry vs. Rollback vs. Escalation)

```
START: Deployment failed, one or more services unhealthy
│
├─ Identify which service(s) failed:
│  ├─ Parse health check results, identify unhealthy services
│  ├─ Check docker logs for crashed containers
│  ├─ Identify if failure is in root service or dependent service
│  └─ Determine if failure is permanent (bad config) or transient (network blip)
│
├─ Is failure transient (network blip, race condition)?
│  ├─ YES: Connection refused, timeout on first attempt, service crashed once then recovered
│  │   └─ Action: RETRY
│  │       ├─ Wait 5-10 seconds (allow transient condition to clear)
│  │       ├─ Run health check again
│  │       ├─ If successful, deployment succeeds
│  │       └─ If fails again, escalate (transient became permanent)
│  │
│  └─ NO: Permanent error (bad config, missing dependency, port conflict)
│       └─ Continue to rollback/escalation determination
│
├─ Is rollback possible? (Do we have a previous working version?)
│  ├─ YES: Previous version still available, can restart it
│  │   └─ Action: ROLLBACK
│  │       ├─ Stop new version (partial deployment)
│  │       ├─ Start previous version
│  │       ├─ Verify previous version health checks pass
│  │       ├─ If successful, incident resolved (with degraded version)
│  │       └─ Escalate for root cause analysis (why did new version fail?)
│  │
│  └─ NO: No previous version, or restart not possible
│       └─ Continue to escalation
│
├─ Should we attempt recovery (fix and redeploy)?
│  ├─ Only if root cause identified and fix straightforward:
│  │   ├─ Missing port publication: add to compose file, redeploy
│  │   ├─ Wrong environment variable: correct value, redeploy
│  │   ├─ Port conflict: kill conflicting process, redeploy
│  │   └─ Volume permission: fix directory permissions, redeploy
│  │
│  ├─ If root cause requires code/config changes:
│  │   └─ Action: ESCALATE (not immediate recovery)
│  │
│  └─ If root cause unclear:
│       └─ Action: ESCALATE (for diagnosis)
│
├─ Log comprehensive failure information:
│  {
│    deployment_time: timestamp,
│    services_failed: [list],
│    root_service: "which service failed first",
│    error_logs: "last 50 lines from docker logs",
│    environment: "compose file, env vars (sanitized)",
│    action: "retry|rollback|escalate",
│    escalation_reason: "if escalating"
│  }
│
└─ END: Either recovery attempted, rollback executed, or escalation with diagnostics
```

**Implementation Guidance:**
- Always capture error logs before taking recovery action (needed for root cause analysis).
- Distinguish transient (retry) from permanent (escalate) by checking restart count and error pattern.
- Rollback should only restore last known good state, not arbitrary previous version.
- Each recovery action (retry, rollback, escalate) should be logged with reason and timestamp.
- If escalating, include all diagnostics to help operator (logs, compose file, env vars, timestamps).

---

### Decision Tree 4: Cleanup Safety Checks (Before down -v)

```
START: Preparing to stop and remove stack
│
├─ Verify all containers belong to this stack (not accidentally shared):
│  ├─ Get all containers: docker-compose ps
│  ├─ Cross-check against compose file services (should match exactly)
│  └─ If mismatch, escalate (may have orphaned containers, but don't delete)
│
├─ Verify volumes are not shared with other stacks:
│  ├─ Get volumes: docker volume ls | grep <project_name>
│  ├─ Check if any volume used by containers outside this compose file
│  ├─ Use: docker ps -a --format='{{json .Mounts}}' | grep <volume_name>
│  └─ If volume used by other container, escalate (don't delete, may be shared)
│
├─ Back up or verify important data (if applicable):
│  ├─ For databases: consider dump or snapshot
│  ├─ For persistent data: verify backed up elsewhere if needed for recovery
│  └─ Log: "Removing stack with volumes: data, cache" for audit trail
│
├─ Are all services stopped or in error state?
│  ├─ If services still running: gracefully stop them first (via SIGTERM in health check)
│  ├─ If services already exited: safe to remove
│  └─ Log which services are being removed
│
├─ Check disk space after cleanup:
│  ├─ After down -v: verify volumes actually removed (docker volume ls)
│  ├─ Check disk usage: df -h /var/lib/docker
│  └─ If cleanup failed, log error (volumes not removed)
│
├─ Run cleanup:
│  └─ Command: docker-compose down -v --remove-orphans
│
├─ Verify cleanup succeeded:
│  ├─ docker-compose ps should show no containers
│  ├─ docker volume ls should not show project volumes
│  ├─ docker network ls should not show project networks
│  └─ If any remain, log cleanup failure and escalate
│
└─ END: Stack removed, or cleanup failure escalated
```

**Implementation Guidance:**
- Always verify safety before removing volumes (especially if data important).
- Use `down -v --remove-orphans` to catch any orphaned containers from previous failed deployments.
- Log what was removed (services, volumes, networks) for audit trail.
- Check disk space impact: verify volumes actually freed disk space.
- If cleanup fails (volumes not removed), escalate—next deployment may use stale state.

---

## Docker Compose Version Compatibility

This skill supports:
- **docker-compose v2.0+** - Recommended, includes newer features
- **docker-compose v1.29.x** - Supported with limitations (some YAML features unavailable)
- **compose in Docker CLI** - `docker compose` (v2.0+, Docker Desktop/Engine 20.10+)

**Version-Specific Behavior:**
- **v1.29.x**: `docker-compose` command prefix required
- **v2.0+**: Both `docker-compose` and `docker compose` work
- **Compose specification v3.8+**: Recommended for modern features (depends_on with condition, resource limits, healthcheck section)

**Compatibility Notes:**
- Some YAML features (healthcheck, depends_on condition) not available in v3.0-3.7
- Use `version: '3.8'` or higher in compose file for full feature support
- Test compose file syntax: `docker-compose -f file.yml config` before deployment

---

## Performance Considerations

### Build Time Optimization
- Use `.dockerignore` to exclude unnecessary files from build context (reduce build time by 30-50%)
- Multi-stage builds to reduce final image size (especially for Node, Java, Go projects)
- Layer caching: order Dockerfile commands to maximize cache hit rate (dependencies before source code)
- Test build time locally before deployment: `time docker-compose build`

### Image Size Impact
- Smaller base images (alpine, distroless) reduce pull time and startup time
- Remove unnecessary dependencies from images
- Use `docker image ls` to verify image sizes before deployment

### Resource Efficiency
- Configure resource limits per service:
  ```yaml
  services:
    api:
      deploy:
        resources:
          limits:
            cpus: '1.0'
            memory: 512M
  ```
- Monitor resource usage during deployment: `docker stats` to verify no OOM or CPU throttling

---

## Production Deployment Concerns

### Logging Management
- Configure log drivers to prevent unbounded log growth:
  ```yaml
  services:
    api:
      logging:
        driver: "json-file"
        options:
          max-size: "10m"
          max-file: "3"
  ```
- Centralize logs: forward to ELK, Splunk, CloudWatch before containers stop
- Capture logs on health check failure: `docker logs <container>` before down()

### Secrets Management
- Never embed credentials in compose file or environment variables
- Use Docker secrets (swarm mode) or external secret management (Vault, AWS Secrets Manager)
- Pass secrets via separate .env.prod file (not in version control)
- Log deployment without exposing secrets: sanitize DATABASE_URL to "***" before logging

### Resource Limits
- Set memory limits to prevent OOM kills and cascading failures
- Set CPU limits to prevent resource contention between services
- Monitor actual resource usage: adjust limits based on baseline metrics

### Health Check Configuration
- Ensure health check endpoint exists and is production-ready (doesn't slow down under load)
- Configure conservative timeouts for production (slower networks, higher load)
- Log health check latency trends: if increasing, indicates degradation

---

## Cross-References

### Related Deploy Drivers
- **deploy-driver-pm2-ssh** - Deploy on remote servers via PM2 (compare: PM2 vs Docker Compose startup overhead, SSH requirements)
- **deploy-driver-local-process** - Deploy local Node.js process (compare: local vs containerized, testing vs production)
- **deploy-driver-systemd** - Deploy via systemd service (compare: systemd isolation vs Docker, configuration complexity)
- **deploy-driver-k8s** - Kubernetes orchestration (compare: K8s vs Compose, scaling, multi-host)

### Related Eval Drivers
- **eval-driver-db-mysql** - MySQL evaluation driver (for database service health checks)
- **eval-driver-cache-redis** - Redis evaluation driver (for cache service health checks)
- **eval-driver-api-http** - HTTP API evaluation (for health endpoint testing, response validation)
- **eval-coordinate-multi-surface** - Multi-service eval coordination (for testing entire stacks)

### Related Brain Documents
- **brain-read** - Product topology and project metadata (for understanding service dependencies)
- **brain-write** - Recording deployment decisions (log successful deployments, failure patterns)
- **brain-recall** - Accessing deployment learnings and failure history (for diagnosis and prevention)

---

## Notes

- All timestamps are ISO 8601 format (UTC)
- Container IDs are short hashes (12 characters) unless full ID specified
- Logs are captured on failure for debugging
- Graceful shutdown timeout is 10 seconds (configurable)
- Volume cleanup is mandatory on `down()` to prevent stale state accumulation
- Health check retries use exponential backoff: 100ms → 200ms → 400ms → 800ms → 1000ms (cap at max interval)
- Service startup order guaranteed by `depends_on`, but readiness requires health checks
- All error codes logged for traceability and debugging

### Command Execution

All commands run via subprocess with:
- Shell: `/bin/bash`
- Timeout: 120 seconds (configurable per call)
- Environment: Inherits process.env, merged with provided `env_vars`
- Working directory: Directory containing compose file

### Container Inspection

Health checks use Docker CLI commands:
```bash
# Get container ID from service name
docker-compose -f <file> ps -q <service_name>

# Check if running
docker inspect <container_id> --format '{{.State.Running}}'

# Get logs
docker logs <container_id>
```

### Network Access

HTTP health checks assume:
- Docker desktop or local Docker daemon
- Containers accessible at `localhost:<port>` (port-forwarding via docker-compose)
- Network namespace allows inter-container DNS (service_name:port from other containers)

For remote Docker hosts, use `docker context use <context>` before calling this skill.

---

## Usage Examples

### Single Service Deployment

```javascript
// Start a single API service
const up_result = await up('/app/docker-compose.yml', {
  PORT: '3000',
  DATABASE_URL: 'postgresql://localhost/myapp'
});

console.log(`API started: ${up_result.services[0].container_id}`);

// Poll for health
const health = await health_check(
  '/app/docker-compose.yml',
  'api',
  3000,
  '/health'
);

if (health.healthy) {
  console.log('API is ready');
}

// Cleanup
await down('/app/docker-compose.yml');
```

### Multi-Service Stack

```javascript
// Start entire stack (API + DB + Cache)
const stack = await up('/project/docker-compose.yml', {
  MYSQL_ROOT_PASSWORD: 'test_password',
  REDIS_PASSWORD: 'cache_password'
});

// Wait for each service
const api_health = await health_check(
  '/project/docker-compose.yml',
  'backend',
  8080,
  '/api/status',
  30000
);

const db_health = await health_check(
  '/project/docker-compose.yml',
  'mysql',
  3306,
  null,  // No HTTP endpoint, just container check
  15000
);

if (api_health.healthy && db_health.healthy) {
  console.log('Stack fully operational');
} else {
  console.log('Stack startup failed');
  await down('/project/docker-compose.yml');
}
```

### Test Teardown

```javascript
// Always cleanup in finally block
try {
  await up('/test/docker-compose.yml');
  // ... run tests ...
} finally {
  const cleanup = await down('/test/docker-compose.yml');
  console.log(`Test environment torn down, removed ${cleanup.services_removed} services`);
}
```

---

## Error Codes & Messages

| Error | Meaning | Recovery |
|-------|---------|----------|
| `COMPOSE_FILE_NOT_FOUND` | docker-compose.yml does not exist | Check file path and create if needed |
| `DOCKER_NOT_INSTALLED` | Docker daemon unavailable | Install Docker or check service status |
| `CONTAINER_START_TIMEOUT` | Service failed to start | Check compose file syntax, logs |
| `HEALTH_CHECK_TIMEOUT` | Service not responding to health check | Check logs, verify port mapping |
| `PORT_ALREADY_IN_USE` | Port conflict on host | Change port in compose file or stop other services |
| `VOLUME_MOUNT_FAILED` | Volume binding error | Check path permissions, disk space |

---

## Environment Integration

This skill works with:
- **docker** - Container runtime (v20.10+)
- **docker-compose** - Orchestration tool (v2.0+)
- **localhost** - Default network (requires Docker Desktop on macOS/Windows)

For production deployments, see related skills:
- `deploy-driver-k8s` - Kubernetes orchestration
- `eval-product-stack-up` - Full product stack coordination

## Checklist

Before claiming completion:

- [ ] `up()` called with explicit compose file path — no default file assumed
- [ ] `health_check()` called for every service after `up()` — not skipped for "simple" stacks
- [ ] Health check verified service readiness via HTTP endpoint, not just container state
- [ ] Container restart count monitored for first 30 seconds — no silent crash loops
- [ ] `down()` called with `-v` flag — named volumes removed, no stale state persists
- [ ] All services confirmed healthy before deployment success reported
- [ ] Log output captured from failed health checks — diagnosis not blind
