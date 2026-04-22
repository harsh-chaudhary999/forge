---
name: deploy-driver-pm2-ssh
description: "WHEN: Deployment target is a remote server managed via PM2 over SSH. Provides connect(ssh_config), start(project_path, script), health_check(port, endpoint), and stop(project_name)."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers: []
allowed-tools:
  - Bash
  - Write
---

# Deploy Driver: PM2 over SSH

Deployment driver for PM2 over SSH on remote servers. Provides SSH connection management, process launching via PM2, HTTP-based health checks, and graceful shutdown via pkill.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **SSH connection is tested with `ping` or TCP port probe only** — A reachable host does not mean SSH is functional. Firewall rules can allow TCP but block the SSH daemon; a key mismatch will fail at authentication, not at connection. STOP. Test SSH by executing a no-op command (`echo ok`) over the connection before calling any deploy function.
- **PM2 process is claimed healthy because `pm2 start` exited 0** — PM2 start exit code reflects whether PM2 accepted the command, not whether the process is actually healthy. STOP. Always follow `start()` with `health_check()` against the application's HTTP health endpoint.
- **`stop()` is not called during cleanup when eval fails** — A process left running on the remote server will conflict with the next deployment's port binding or state. STOP. `stop()` must be called unconditionally in cleanup, not only on success paths.
- **SSH key fingerprint is not validated on first connect** — A changed host key (server reinstall, MitM) accepted silently means credentials may be sent to an unexpected host. STOP. Validate host key fingerprint against the known whitelist on every `connect()`.
- **Application logs are not retrieved after a failed health check** — When health check fails, the root cause is in the application logs on the remote server. Without fetching them, diagnosis is blind. STOP. On any health check failure, fetch and record the last 100 lines of the process log before reporting BLOCKED.
- **Deployment proceeds while a previous version's process is still running** — Two versions of the process running simultaneously can corrupt shared state (DB, cache, files). STOP. Always verify no previous process is running on the target port before `start()`.

## HARD-GATE: Anti-Pattern Preambles

The following rationalizations **WILL BLOCK** your deployment. These are not edge cases—they are guaranteed failure modes that will surface in production.

### 1. "SSH will always work if the host is reachable"

**Why This Fails:**
- Network reachability (ping) ≠ SSH port open. Firewalls, security groups, and jump hosts silently drop SSH packets.
- Host key changes (server reinstall, MitM) cause `SSH_HOST_KEY_MISMATCH` silently on first connection.
- SSH daemon crash on remote (kernel panic, systemd failure) leaves network layer intact but SSH unreachable.
- Connection pooling mask SSH state: a dropped connection may not fail until reuse, leaving stale state in memory.

**Enforcement:**
- MUST implement exponential backoff with jitter (not linear retry).
- MUST validate host key fingerprint against whitelist on first connect.
- MUST detect and clear stale connections: test connectivity before every command.
- MUST NOT assume a successful `connect()` call means the connection will survive 30+ seconds idle.

---

### 2. "Health checks are optional if the process starts"

**Why This Fails:**
- PM2 `start` reports PID while the process is still in initialization (socket binding, DB connection, TLS handshake).
- "Running" in PM2 status ≠ "accepting traffic". Process can bind port 3000 but hang on first request.
- Slow startup apps (Java, heavy frameworks) appear ready after 2s but don't respond until 10s.
- Health check timeouts indicate overload (resource exhaustion, cascading failures) that `pm2 status` never shows.
- Skipping health check masks deployment race conditions: you deploy, return success, caller sends traffic, connection refused.

**Enforcement:**
- MUST perform health_check() before returning deployment success.
- Health check MUST poll endpoint with exponential backoff until timeout OR success (not just once).
- MUST track latency trend: if latency increases 2x from baseline, escalate to monitoring (indicates load spike).
- MUST distinguish "timeout" (slow startup) from "connection refused" (not yet bound port) in health check response.

---

### 3. "Timeouts are edge cases; normal operations finish quickly"

**Why This Fails:**
- SSH commands over high-latency networks (transatlantic, satellite, VPN) routinely hit 2-5s command execution time.
- PM2 startup includes: npm install (if missing), node module resolution (large node_modules), script initialization.
- Health check first request always slower than subsequent (DNS, connection establishment, TLS handshake on HTTPS endpoints).
- Timeout values hardcoded (30s for exec, 5s for health) fail on slow networks or overloaded servers.
- Assuming "timeout means failure" masks real issues: timeout during rollback indicates the old version hung (not a network blip).

**Enforcement:**
- MUST make all timeouts configurable (no hardcoded values in production code).
- MUST distinguish timeout *cause*: SSH layer timeout vs. curl timeout vs. process exit before response.
- MUST extend timeout for first health check after start (minimum 2x normal, capped at 30s).
- MUST log timeout duration and retry count: reveals if issue is slowness (increase timeout) vs. hanging process (escalate).

---

### 4. "Process crashes are PM2's problem; we just start and move on"

**Why This Fails:**
- PM2 auto-restart on crash helps long-term, but deployment-phase crashes (bad config, missing deps) repeat forever.
- Crash loop: process exits in <2s, PM2 restarts, crashes again—after 5 loops PM2 gives up, but you've already returned success.
- Health check timeout masks crash loop: you health check at t=5s, process hasn't crashed yet (crashes at t=8s), you report success, caller gets 500 after 3s.
- Gradual failure: process starts, crashes after 30s (slow memory leak, connection pool exhaustion), health check window is 10s—never caught.

**Enforcement:**
- MUST monitor PM2 crash count and exit codes for 15-30 seconds post-start.
- IF crash count > 2 in 30s, MUST escalate: not a transient issue, requires human intervention (config review, dependency audit).
- MUST parse PM2 output for warnings (missing dependencies, permission errors, port conflicts).
- Health check polling interval MUST match expected startup time, not fixed 5s (e.g., 30s for Java apps).

---

### 5. "Rollback is just starting the previous version; stateless services don't need rollback planning"

**Why This Fails:**
- Previous version may not be running (stopped for space, replaced), or its PM2 config lost.
- Database migrations break rollback: if v2 added columns, v1 code crashes when those columns appear (cannot be unread).
- Port conflicts during rollback: new version crashes, you try to start old version on same port, port still held by zombie process.
- Traffic still flowing to new version during rollback: DNS cache, client-side load balancer, connection pools hold new-version connections.
- Rollback success criteria undefined: "old version running" ≠ "old version handling traffic correctly" ≠ "old version metrics normal".

**Enforcement:**
- MUST require explicit rollback plan in deployment spec (not implicit "restart prev version").
- IF database version mismatch possible, MUST include schema rollback step or declare rollback unavailable.
- MUST implement 30-60s waiting period post-rollback before returning success (allows old version to stabilize, catch lingering issues).
- MUST verify rollback metrics (latency, error rate) against baseline before declaring rollback complete.

---

## Iron Law

```
EVERY PM2 SSH DEPLOYMENT VALIDATES SSH CONNECTIVITY WITH A NO-OP COMMAND, VERIFIES THE HOST KEY FINGERPRINT, CONFIRMS NO PRIOR VERSION IS RUNNING, STARTS THE PROCESS, AND FOLLOWS WITH A HEALTH CHECK. stop() IS CALLED IN ALL PATHS. CONFIDENCE THAT IT WORKED IS NOT A HEALTH CHECK.
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│            Deploy Driver PM2 SSH                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ SSH Connect  │  │ SSH Commands │                │
│  │ (key/passwd) │  │  (exec)      │                │
│  └──────────────┘  └──────────────┘                │
│         │                   │                       │
│         └───────┬───────────┘                       │
│                 ▼                                    │
│  ┌─────────────────────────────┐                   │
│  │  PM2 Process Management     │                   │
│  │  • pm2 start                │                   │
│  │  • pm2 delete               │                   │
│  │  • pkill -f                 │                   │
│  └─────────────────────────────┘                   │
│         │                                           │
│         ├─► [Start] Run script via PM2             │
│         ├─► [Health] HTTP GET to endpoint          │
│         └─► [Stop] Kill process via pkill          │
│                                                      │
│  ┌─────────────────────────────┐                   │
│  │  Error Handling & Timeout   │                   │
│  │  • SSH connection retry     │                   │
│  │  • Health check timeout (5s)│                   │
│  │  • Command execution timeout│                   │
│  └─────────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

## Function Signatures

### connect(ssh_config) → SSH Connection Object

Establish SSH connection to remote server.

**Parameters:**
- `ssh_config: Object`
  - `host: string` - Remote server hostname or IP
  - `port: number` - SSH port (default: 22)
  - `username: string` - SSH username
  - `privateKey?: string | Buffer` - Path to private key or key buffer (for key-based auth)
  - `password?: string` - SSH password (for password-based auth)
  - `readyTimeout: number` - Connection timeout in ms (default: 10000)
  - `retries: number` - Connection retry attempts (default: 3)

**Returns:**
- SSH connection object with methods: `exec()`, `close()`, `isReady()`

**Error Cases:**
- `SSH_CONNECT_FAILED` - Connection refused, network unreachable
- `SSH_AUTH_FAILED` - Invalid credentials or key
- `SSH_TIMEOUT` - Connection timeout exceeded

**Example:**
```javascript
const ssh = await connect({
  host: '192.168.1.100',
  port: 22,
  username: 'deploy',
  privateKey: '/home/user/.ssh/id_rsa'
})
```

---

### start(ssh, project_path, script) → {pid: number, status: string}

Launch application via PM2 on remote server.

**Parameters:**
- `ssh: Object` - SSH connection object from `connect()`
- `project_path: string` - Absolute path to project directory on remote
- `script: string` - Script/command to run (default: 'npm run dev')

**Execution Steps:**
1. SSH into remote server
2. Change to project directory: `cd {project_path}`
3. Start via PM2: `pm2 start "{script}" --name "{project_name}"`
4. Save PM2 config: `pm2 save`
5. Capture PID from PM2 output

**Returns:**
```javascript
{
  pid: 12345,
  status: "running",
  name: "backend-api",
  command: "npm run dev",
  uptime_ms: 1250
}
```

**Error Cases:**
- `PM2_NOT_INSTALLED` - PM2 not found in PATH
- `PROJECT_PATH_NOT_FOUND` - Directory does not exist
- `SCRIPT_FAILED` - Script execution failed (non-zero exit)
- `COMMAND_TIMEOUT` - Command execution exceeded 30s timeout

**Example:**
```javascript
const result = await start(ssh, '/home/deploy/backend-api', 'npm run dev')
// { pid: 12345, status: "running", name: "backend-api", ... }
```

---

### health_check(ssh, port, endpoint) → {healthy: boolean, latency_ms: number, status_code: number}

Verify application health via HTTP GET.

**Parameters:**
- `ssh: Object` - SSH connection object
- `port: number` - Application port (e.g., 3000)
- `endpoint: string` - Health endpoint path (e.g., '/health')
- `timeout_ms?: number` - HTTP timeout (default: 5000)
- `retries?: number` - Retry attempts (default: 3)

**Execution Steps:**
1. Construct URL: `http://localhost:{port}{endpoint}`
2. Execute curl via SSH: `curl -s -w "%{http_code}" -o /dev/null http://localhost:{port}{endpoint}`
3. Capture HTTP status code
4. Measure latency using curl's `-w` flag
5. Retry on non-200 responses with exponential backoff

**Returns:**
```javascript
{
  healthy: true,
  status_code: 200,
  latency_ms: 42,
  endpoint: "/health",
  timestamp: 1649234567890
}
```

**Error Cases:**
- `HEALTH_CHECK_FAILED` - HTTP status not 200
- `HEALTH_CHECK_TIMEOUT` - Request timeout exceeded
- `CONNECTION_REFUSED` - Port not listening
- `INVALID_RESPONSE` - Non-HTTP response

**Example:**
```javascript
const health = await health_check(ssh, 3000, '/health')
// { healthy: true, status_code: 200, latency_ms: 42, ... }
```

---

### stop(ssh, project_name) → {status: string, stopped_at: number}

Gracefully stop PM2 process.

**Parameters:**
- `ssh: Object` - SSH connection object
- `project_name: string` - PM2 app name
- `force?: boolean` - Force kill if graceful shutdown fails (default: false)
- `timeout_ms?: number` - Wait timeout before force kill (default: 10000)

**Execution Steps:**
1. Attempt graceful stop via PM2: `pm2 delete "{project_name}"`
2. If graceful fails and `force: true`, use pkill: `pkill -f "{project_name}"`
3. Verify process is stopped via `ps aux | grep`
4. Clear PM2 logs: `pm2 logs --lines 0`
5. Update PM2 config: `pm2 save`

**Returns:**
```javascript
{
  status: "stopped",
  project_name: "backend-api",
  stopped_at: 1649234567890,
  signal: "SIGTERM",
  force_kill: false
}
```

**Error Cases:**
- `PROCESS_NOT_FOUND` - PM2 app not registered
- `STOP_TIMEOUT` - Process did not stop within timeout
- `PERMISSION_DENIED` - Insufficient permissions for pkill

**Example:**
```javascript
const result = await stop(ssh, 'backend-api')
// { status: "stopped", project_name: "backend-api", ... }
```

---

## Implementation Guidelines

### SSH Protocol & Security

- Use SSH2 protocol with key-based auth as primary method
- Support password-based fallback with warning
- Validate private key permissions (must be 0600)
- Implement connection pooling to reuse SSH connections
- Set `StrictHostKeyChecking=no` with explicit host key verification
- Encrypt password in transit; never log credentials

### PM2 Process Management

- Always use named processes: `pm2 start ... --name "project-name"`
- Enable auto-restart on reboot: `pm2 startup`
- Log outputs to `~/.pm2/logs/` with rotation
- Use `pm2 save` to persist process list across restarts
- Support custom scripts via shebang (#!/usr/bin/env node)

### Health Check Strategy

- Implement exponential backoff: 100ms → 200ms → 400ms → 800ms
- Tolerate timeouts on first 2 attempts, fail on 3rd
- Parse HTTP status code from curl `-w` output
- Support custom headers via `health_check_headers` config
- Track latency as key metric for performance regression detection

### Error Handling & Timeouts

| Operation | Timeout | Retries | Backoff |
|-----------|---------|---------|---------|
| SSH Connect | 10s | 3 | Linear 2s |
| Command Exec | 30s | 1 | N/A |
| Health Check | 5s | 3 | Exponential |
| Process Stop | 10s | 1 | N/A |

### Logging & Debugging

```javascript
// All operations log:
{
  timestamp: ISO8601,
  operation: "start|stop|health_check|connect",
  host: "192.168.1.100",
  duration_ms: 1234,
  status: "success|error",
  error?: "ERROR_CODE",
  details: {}
}
```

### Configuration Example

```javascript
// Complete deployment workflow
const config = {
  ssh: {
    host: '192.168.1.100',
    port: 22,
    username: 'deploy',
    privateKey: fs.readFileSync('/home/user/.ssh/id_rsa'),
    readyTimeout: 10000
  },
  deployment: {
    project_path: '/home/deploy/backend-api',
    script: 'npm run dev',
    pm2_name: 'backend-api'
  },
  health: {
    port: 3000,
    endpoint: '/health',
    timeout_ms: 5000,
    retries: 3
  }
}

// Deploy flow
const ssh = await connect(config.ssh)
const startResult = await start(ssh, config.deployment.project_path, config.deployment.script)
const healthResult = await health_check(ssh, config.health.port, config.health.endpoint)
const stopResult = await stop(ssh, config.pm2_name)
```

### Testing & Verification

1. **Unit Tests**
   - Mock SSH connections
   - Verify error handling paths
   - Test timeout behavior

2. **Integration Tests**
   - Use test VM or Docker container
   - Verify SSH key auth and password auth
   - Test PM2 process lifecycle
   - Validate health check with both healthy and unhealthy responses

3. **End-to-End Tests**
   - Deploy real application to staging
   - Verify PM2 auto-restart on crash
   - Test graceful shutdown sequence
   - Verify PM2 persistence across VM restarts

### Performance Considerations

- SSH connection pooling (reuse connections within 5 min window)
- Parallel health checks across multiple services
- Cache PM2 process list for 10 seconds
- Use `curl -m 2` (max time) for fast timeout response

### Common Patterns

**Full Deployment Cycle:**
```javascript
const ssh = await connect(sshConfig)
await start(ssh, '/home/deploy/app', 'npm run dev')
await new Promise(r => setTimeout(r, 2000)) // Wait for startup
const health = await health_check(ssh, 3000, '/health')
if (!health.healthy) {
  await stop(ssh, 'app')
  throw new Error('Health check failed')
}
// Deployment successful
```

**Graceful Restart:**
```javascript
await stop(ssh, 'app')
await new Promise(r => setTimeout(r, 1000))
await start(ssh, '/home/deploy/app', 'npm run dev')
```

**Health Monitoring Loop:**
```javascript
setInterval(async () => {
  const health = await health_check(ssh, 3000, '/health')
  console.log(`App health: ${health.healthy ? 'UP' : 'DOWN'}`)
  if (!health.healthy) {
    // Alert or auto-restart
  }
}, 30000)
```

## Edge Cases with Mitigation

Edge cases that WILL occur in production. Each requires specific detection and recovery logic.

### Edge Case 1: SSH Host Key Changed (Server Reinstall or MitM)

**Scenario:**
You deploy to a production server. Between deployments, the server is reinstalled (new SSH keypair). Your next deploy SSH connection fails with `Host key verification failed`. Your automated deployment stops, no alert fired, and the service remains on old version.

**How to Detect:**
- SSH client returns error containing `Offending ECDSA key` or `known_hosts` conflict
- SSH library throws `SSH_HOST_KEY_MISMATCH` error code
- Connection attempt hangs for 30s then timeout (remote SSH daemon missing, firewall blocking)

**What Happens:**
- If StrictHostKeyChecking=yes: connection refused immediately (safe but requires manual key rotation).
- If StrictHostKeyChecking=no: connection allowed but unverified (vulnerable to MitM, acceptable only on private networks with host key whitelist).
- Subsequent deployments fail with same error, cascading across entire fleet.

**Mitigation Steps:**
1. Detect: Wrap connect() in try-catch, inspect error message for "host key" keywords.
2. Escalate immediately: Log with ERROR severity and include the fingerprint. Example:
   ```javascript
   catch (err) {
     if (err.message.includes('host key')) {
       logger.error('HOST_KEY_MISMATCH', {
         host: config.host,
         fingerprint: extractFingerprint(err),
         action: 'MANUAL_ROTATION_REQUIRED'
       })
       throw new Error('Deploy blocked: host key mismatch. Run `ssh-keyscan -t rsa HOST >> ~/.ssh/known_hosts` manually.')
     }
   }
   ```
3. Recovery: Do NOT auto-rotate keys. Require on-call to SSH manually and verify: `ssh-keyscan -t rsa HOSTNAME | ssh-keygen -l -f -` to get fingerprint.
4. Prevention: Use host key pinning in config: `expectedFingerprints: ['SHA256:abc123...']` validated at connect time.

---

### Edge Case 2: SSH Authentication Fails Due to Key Permissions (0644 instead of 0600)

**Scenario:**
Your deploy script references a private key with incorrect permissions (world-readable). SSH library silently rejects the key because "key is too permissive". Your automation doesn't detect this, assumes key-based auth will work, but falls back to password auth (if configured, revealing password in logs).

**How to Detect:**
- SSH client returns `SSH_AUTH_FAILED` with message containing "permission denied" or "key not found"
- `stat /path/to/key` returns permissions not equal to `0600` (rw-------)
- Auth attempt takes 1-2s (indicates multiple auth method attempts before failure)

**What Happens:**
- If password fallback configured: uses password (potential credential exposure).
- If no fallback: deployment fails, but without clear indication *why* auth failed.
- Cascades on all deploys until manually fixed.
- Becomes security vulnerability if key is in shared deployment container.

**Mitigation Steps:**
1. Detect: Before connect(), verify key file permissions:
   ```javascript
   const fs = require('fs')
   const stats = fs.statSync(keyPath)
   const perms = (stats.mode & parseInt('777', 8)).toString(8)
   if (perms !== '600') {
     throw new Error(`SSH_KEY_PERMISSIONS_INVALID: expected 0600, found 0${perms}`)
   }
   ```
2. Escalate: If key permissions invalid, refuse deployment entirely. No fallback to password.
3. Recovery: Ops must run `chmod 600 /path/to/key` and verify: `stat /path/to/key` should show `-rw-------`.
4. Prevention: Bake permission check into CI pipeline before deploy stage: fail fast if keys misconfigured.

---

### Edge Case 3: PM2 Process Enters Crash Loop (Crash Count > 2 in 30s)

**Scenario:**
Your deployment starts a Node.js app via PM2. The app crashes immediately due to missing environment variable. PM2 auto-restarts it (restart 1, 2, 3...). After 5 crashes, PM2 disables auto-restart to prevent resource exhaustion. You health check at t=10s, process is restarting, health check times out. You assume transient issue and retry. By t=30s, PM2 has given up and the process is stopped. Your health check succeeds eventually (after 20 retries), you report deployment success, but the app is actually stopped.

**How to Detect:**
- Parse PM2 output for "max restart count exceeded" or similar
- `pm2 describe APP_NAME` returns `restart_time > 5` and `status: "errored"`
- Health check succeeds BUT process list shows status other than "online" (e.g., "stopped", "one-launch-status")

**What Happens:**
- Crash loop → PM2 gives up → process stopped → health check timeout initially → eventual recovery misleads operator.
- Metric drift: error rates spike 30 minutes after deployment (by which time you've moved on).
- Rollback required but blamed on new code (instead of missing config/deps).

**Mitigation Steps:**
1. Detect: After start(), run `pm2 describe APP_NAME` and check restart_time and status:
   ```javascript
   const result = await exec(ssh, `pm2 describe ${name} --update 0`)
   const pmInfo = parseJson(result.stdout)
   if (pmInfo.restart_time > 2 || pmInfo.status !== 'online') {
     throw new Error(`PM2_CRASH_LOOP: app restarted ${pmInfo.restart_time} times, status ${pmInfo.status}`)
   }
   ```
2. Escalate: If crash loop detected, do NOT proceed with health check. Fail deployment and surface PM2 error logs:
   ```javascript
   const logs = await exec(ssh, `tail -n 50 ~/.pm2/logs/${name}-error.log`)
   logger.error('PROCESS_CRASH_LOOP', { logs })
   ```
3. Recovery: Operator reviews error logs (usually missing env var, missing dependency, or syntax error). Fix root cause and redeploy.
4. Prevention: In CI, run the same start command in a test container and capture first 30s of logs. Fail if restart_time > 1.

---

### Edge Case 4: Health Check Endpoint Returns 200 But Endpoint Unreachable Due to Network Partition

**Scenario:**
Your health endpoint is `/health` and returns `200 OK`. You deploy to server in region A. During health check, a network partition occurs between your deploy agent and the server. The curl command times out silently. Your health check logic retries 3 times with exponential backoff (100ms, 200ms, 400ms), total 700ms. By t=1s, network partition heals. Health check retries succeed at t=1.5s, you get `200 OK`, deployment succeeds. But the actual application never served traffic successfully to real clients—it was isolated from the region B load balancer. Incident fires 5 minutes later when production traffic tries to route to the new version.

**How to Detect:**
- Health check returns `200 OK` but latency spikes (baseline 50ms, suddenly 3000ms) on every attempt
- Network partition detected at container/VM network layer (dropped packets, intermittent timeouts)
- Health check latency variance > 5x baseline (indicates network instability)

**What Happens:**
- Deployment succeeds, passes all checks, but connectivity is marginal/degraded.
- Real-world traffic encounters dropped connections, slow responses, timeout cascades.
- Appears as sporadic 5xx errors to end users, not a deployment issue.

**Mitigation Steps:**
1. Detect: Track latency percentiles in health check response, not just success/failure:
   ```javascript
   const result = await health_check(ssh, 3000, '/health')
   if (result.latency_ms > baseline * 3 && result.latency_ms > 500) {
     logger.warn('HEALTH_CHECK_LATENCY_SPIKE', {
       expected_ms: baseline,
       actual_ms: result.latency_ms,
       status: 'SUSPECT'
     })
     // Escalate or retry health check
   }
   ```
2. Escalate: If latency spike detected, do NOT proceed. Trigger network diagnostics: `traceroute`, `ping`, connectivity test to load balancer.
3. Recovery: Wait for network partition to heal or manually verify connectivity to dependent services. Redeploy only after network stability confirmed.
4. Prevention: Health check should verify not just endpoint availability but also downstream dependencies (DB connection, cache, upstream API). Return `500` if dependencies unavailable.

---

### Edge Case 5: Port Conflict During Rollback (Old Process Consuming Same Port)

**Scenario:**
You deploy v2 of an app to port 3000. After 5 minutes, you discover a critical bug. You stop v2 (pm2 delete), then start v1 on the same port. But v1 fails to bind with `EADDRINUSE`. Investigation reveals the v2 process never fully exited—it was in graceful shutdown (sending data over persistent connections) and still held the port. Your rollback fails. You run `pkill -f` to force-kill, but this cuts off active connections abruptly. Clients receive connection resets, temporary outage occurs during rollback (should be transparent).

**How to Detect:**
- `pm2 start` returns error containing `EADDRINUSE` or `Address already in use`
- `lsof -i :3000` shows process still listening with PID != new PM2 PID
- Rollback start() fails but process status check shows no running process (zombie state)

**What Happens:**
- Rollback start fails, blocking manual recovery attempts.
- Forced pkill during rollback cuts off live connections (outage).
- Cascades if services depend on this app (connection timeout cascade).

**Mitigation Steps:**
1. Detect: When start() fails with EADDRINUSE, inspect current port holders:
   ```javascript
   const pidResult = await exec(ssh, `lsof -i :${port} -t`)
   const existingPid = pidResult.stdout.trim()
   if (existingPid) {
     logger.error('PORT_CONFLICT', { port, existing_pid: existingPid })
   }
   ```
2. Escalate: Do NOT auto-force-kill. Instead, check if the process is actually dead or in graceful shutdown:
   ```javascript
   const statusResult = await exec(ssh, `ps aux | grep -v grep | grep ${existingPid}`)
   if (statusResult.stdout.includes('graceful') || statusResult.stdout.includes('exiting')) {
     // Process in graceful shutdown, wait
     await new Promise(r => setTimeout(r, 5000))
     // Retry start after grace period
   } else {
     throw new Error('PORT_CONFLICT_UNRESOLVED: unknown process holding port')
   }
   ```
3. Recovery: If grace period expires, then force-kill with warning: `kill -9 PID`, accept brief outage.
4. Prevention: Configure PM2 with kill_timeout (graceful shutdown timeout): `pm2 start --kill-timeout 10000`. If process doesn't exit in 10s, force-kill automatically.

---

### Edge Case 6: Health Check Succeeds But Request Body Partially Received (Slow Client Network)

**Scenario:**
Your health endpoint returns `200 OK` with a JSON body. Health check curl command receives the status code quickly (fast) but takes 10+ seconds to fully read the response body (slow client network). Health check timeout is 5s, so the status code arrives (success) but the body read times out. You report deployment success, but the actual application is on a slow network path. Real-world traffic (heavier payloads) times out after a few requests due to network latency. Incident fires 10 minutes later when steady-state traffic hits.

**How to Detect:**
- curl `-w` flag reports success but curl process itself times out during read
- Health check latency spikes but status code reported as 200
- Client network metrics show packet loss or jitter > 100ms (should be < 10ms on same region)

**What Happens:**
- Deployment succeeds, health check reports success, but network path is degraded.
- Real traffic encounters timeouts on larger payloads (not health endpoint).
- Appears as sporadic timeouts to end users, not correlated to deployment.

**Mitigation Steps:**
1. Detect: Use curl `-m` (max time) parameter to enforce timeout on entire operation, not just connection:
   ```javascript
   const cmd = `curl -m 5 -s -w "%{http_code}\\n%{time_total}" http://localhost:3000/health`
   // time_total includes entire operation: connection + header + body read
   ```
2. Escalate: If curl reports non-zero exit code (timeout during body read), escalate network diagnostics.
3. Recovery: Run network diagnostics (ping latency, packet loss, jitter) to dependent services. If marginal, accept slightly higher deployment risk or wait for network to stabilize.
4. Prevention: Health endpoint should return minimal body (e.g., `{ status: 'ok' }`, not full dependency list). Separate lightweight health check from detailed status endpoint.

---

### Edge Case 7: PM2 Logs Fill Disk, Preventing New Process Start

**Scenario:**
Your application is chatty—logs 100 lines/second. PM2 logs are set to rotate at 10MB but not clean up old rotations. After 3 days of uptime, `/home/deploy/.pm2/logs/` contains 5GB of logs. A new deployment tries to start a process, PM2 initialization fails because it cannot write to log files (disk 100% full). Your start() returns failure, but the error message is ambiguous: "PM2 initialization failed" (doesn't indicate disk full). You retry and fail again. The process never starts, but you don't realize the root cause is disk space.

**How to Detect:**
- `pm2 start` fails with error about writing logs or PM2 initialization
- `df -h` shows filesystem 100% full
- PM2 logs directory (`~/.pm2/logs/`) consumes > 50% of available disk space

**What Happens:**
- Process fails to start, deployment fails.
- Root cause not obvious (logs say "initialization failed", not "disk full").
- Cascades: if you don't fix disk space, *every* subsequent deployment fails, even rollback fails.
- System stability compromised: if app crashes and PM2 tries to write error logs, it fails silently.

**Mitigation Steps:**
1. Detect: Before start(), check available disk space:
   ```javascript
   const dfResult = await exec(ssh, `df -h / | awk 'NR==2 {print $5}' | sed 's/%//'`)
   const usagePercent = parseInt(dfResult.stdout.trim())
   if (usagePercent > 80) {
     throw new Error(`DISK_SPACE_LOW: ${usagePercent}% used, cleanup required`)
   }
   ```
2. Escalate: If disk usage > 80%, require manual cleanup before proceeding. Do NOT auto-delete logs (may erase audit trail).
3. Recovery: Operator runs `pm2 logs --lines 0` to clear log file pointers, then `find ~/.pm2/logs -mtime +7 -delete` to remove old rotations. Verify disk space, then retry deployment.
4. Prevention: Configure PM2 log rotation with max files and cleanup: `pm2 start --max-restarts 10 --exp-backoff-restart-delay 100 --output /path/logs/app-out.log --error /path/logs/app-err.log` with external logrotate job configured:
   ```bash
   /home/deploy/.pm2/logs/*.log {
     daily
     rotate 7
     compress
     notifempty
   }
   ```

---

## Common Pitfalls

Pitfalls that surface repeatedly across deployments. Each requires proactive prevention and detection.

### Pitfall 1: SSH Connection Pooling Creates Stale Connections

**The Problem:**
You implement connection pooling to reuse SSH connections across multiple operations. Pool holds a connection for 5 minutes before closing. Between operations, the SSH server or network drops the connection (firewall timeout, server restart). Your code doesn't detect the dropped connection and reuses it. The next command hangs forever (connection is dead but client doesn't know) or returns garbled output.

**Why It Happens:**
- SSH protocol doesn't automatically detect dead connections on idle channels.
- Connection pool doesn't ping/validate connections before reuse.
- SSH client library queues commands on dead connections without error.

**Prevention:**
- Add connection validation before reuse:
  ```javascript
  async function getConnection(host) {
    let conn = pool.get(host)
    if (conn) {
      // Validate with low-cost command
      try {
        await conn.exec('echo "alive"', { timeout: 1000 })
      } catch (e) {
        conn.close()
        conn = null // Force reconnect
      }
    }
    return conn || (await connect(host))
  }
  ```
- Set shorter pool TTL for high-latency networks (1 minute instead of 5).
- Add connection heartbeat: `setInterval(() => conn.exec('echo'), 30000)` to detect drops early.

---

### Pitfall 2: Health Check Polling Interval Doesn't Match Application Startup Time

**The Problem:**
Your app takes 15 seconds to fully startup. Health check polling interval is 1 second (default exponential backoff: 100ms, 200ms, 400ms). First three polls at t=100ms, 300ms, 700ms all timeout. You retry immediately at t=1s (still startup). Health check succeeds at t=16s, but you've spent 16 seconds waiting when you could've waited more intelligently.

**Why It Happens:**
- Health check defaults assume fast apps (startup < 1s).
- No distinction between "app starting" (wait more) vs. "app broken" (fail fast).
- Exponential backoff has low maximum (400ms), leading to high-frequency retries on slow apps.

**Prevention:**
- Configure health check with app startup time awareness:
  ```javascript
  const config = {
    health: {
      initial_delay_ms: app.startup_time_ms * 0.8, // Wait 80% of expected startup before first check
      polling_interval_ms: 1000,
      max_attempts: (app.startup_time_ms * 2) / polling_interval_ms, // Double startup time as max wait
      timeout_ms: 5000
    }
  }
  ```
- Add app-specific metadata to health check: `{ app_type: 'node', expected_startup_ms: 5000 }`.
- Log all health check attempts with timing: reveals if polling strategy matches app behavior.

---

### Pitfall 3: PM2 State Synchronization Issues When Processes Share Names

**The Problem:**
You have two applications deployed to different servers, both named "api" in PM2. When you query `pm2 status`, the response includes process details. If you parse the response incorrectly, you might update the wrong "api" process. Or, if you deploy to multiple servers in parallel and both servers have a process named "api", your health check targets the wrong server (wrong port, wrong version).

**Why It Happens:**
- PM2 identifiers are local to each server (name "api" can exist on 5 different servers).
- PM2 output parsing is fragile (assumes specific format, breaks on different PM2 versions or locale).
- Multi-server deployments don't maintain server-to-process mapping.

**Prevention:**
- Include server hostname in PM2 process name: `pm2 start ... --name "api-server-a"` instead of just "api".
- Always verify PM2 response includes server identity:
  ```javascript
  const pmInfo = await exec(ssh, `pm2 describe ${name}`)
  const parsed = parseJson(pmInfo.stdout)
  if (parsed.hostname !== expectedHostname) {
    throw new Error(`PM2_HOSTNAME_MISMATCH: expected ${expectedHostname}, got ${parsed.hostname}`)
  }
  ```
- Maintain explicit mapping: `{ server: 'prod-a', port: 3000, pm2_name: 'api-prod-a', version: 'v2.3.1' }`.

---

### Pitfall 4: Error Recovery Patterns Don't Distinguish Transient vs. Permanent Failures

**The Problem:**
Your deploy script encounters an error (e.g., `ECONNREFUSED` during health check). You retry immediately. The error might be transient (network blip) or permanent (process crashed, port not bound). For transient errors, retry helps. For permanent errors, retry wastes time. Your script can't distinguish, so it retries on permanent failures, accumulating delay and confusing diagnostics.

**Why It Happens:**
- Network errors look similar: timeout, connection refused, host unreachable—all could be transient or permanent.
- Retry logic uses same strategy for all errors (exponential backoff).
- Error codes/messages inconsistent across libraries and platforms.

**Prevention:**
- Classify errors into transient (retry) vs. permanent (escalate):
  ```javascript
  const TRANSIENT_ERRORS = ['ECONNREFUSED', 'ETIMEDOUT', 'EHOSTUNREACH', 'ENETUNREACH']
  const PERMANENT_ERRORS = ['SSH_AUTH_FAILED', 'PM2_NOT_INSTALLED', 'EACCES']
  
  function isTransientError(err) {
    return TRANSIENT_ERRORS.some(e => err.code?.includes(e) || err.message?.includes(e))
  }
  
  async function deployWithRetry(config) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await deploy(config)
      } catch (err) {
        if (!isTransientError(err)) {
          throw err // Permanent failure, don't retry
        }
        // Transient, retry with backoff
        await sleep(Math.pow(2, attempt) * 100)
      }
    }
  }
  ```
- Log error classification: `{ error_code, is_transient, action: 'retry|escalate' }` for diagnostics.

---

### Pitfall 5: Performance Degradation Not Detected Until End of Deployment Window

**The Problem:**
Your deployment takes 2 minutes: 30s SSH connect, 30s npm install (slow network), 30s PM2 start, 20s health check polling. Everything succeeds, deployment succeeds. But halfway through, network latency spiked (10x normal). SSH commands took 3x longer than baseline. You didn't notice because you have 5-minute timeout on the entire deploy. If that timeout were 2 minutes, deploy would fail. Worse, the deployed app experienced the same network spike during startup—it's running on degraded network conditions. Real traffic will experience the same issues.

**Why It Happens:**
- Timeouts are set per-operation, not end-to-end.
- Latency spikes during deployment go unnoticed if within timeout bounds.
- Health check succeeds even on degraded network (if latency < timeout).
- No baseline latency comparison (deployed app could be running slower than previous version).

**Prevention:**
- Track operation latencies and compare against baseline:
  ```javascript
  const baseline = { ssh_exec: 500, health_check: 200 }
  const actual = await operation()
  if (actual.latency_ms > baseline.operation_ms * 2) {
    logger.warn('LATENCY_REGRESSION', { operation, baseline_ms: baseline, actual_ms: actual.latency_ms })
    // Could escalate or proceed with warning
  }
  ```
- Set end-to-end timeout on entire deployment (fail if total time > 5 minutes).
- Verify deployed app latency post-deployment: health check latency should match pre-deployment baseline, not spike.

---

### Pitfall 6: Graceful Shutdown Timeout Misconfigured, Leading to Abrupt Disconnections

**The Problem:**
You configure PM2 kill_timeout to 5 seconds (graceful shutdown grace period). Your app needs 15 seconds to flush in-flight requests and close DB connections gracefully. When you deploy v2 and stop v1, PM2 force-kills v1 after 5 seconds. Your app doesn't complete in-flight requests; clients receive connection resets. Some data is lost (partial writes, uncommitted transactions). It appears the new deployment caused data loss (it's actually the stop operation that did).

**Why It Happens:**
- Graceful shutdown timeout is app-dependent (different apps need different times).
- Default PM2 kill_timeout is often too short (5-10s).
- Mismatch between config and actual app requirements goes undetected.

**Prevention:**
- Configure kill_timeout conservatively:
  ```javascript
  // In PM2 ecosystem.config.js
  {
    name: 'api',
    script: 'server.js',
    kill_timeout: 30000, // 30 seconds for graceful shutdown
    listen_timeout: 10000 // Wait 10s for app to listen before considering it started
  }
  ```
- Test graceful shutdown locally: Send SIGTERM, measure time until process exits. Set kill_timeout to 2x that time.
- Log graceful shutdown: App should log when receiving SIGTERM and when it fully exits, confirming graceful shutdown worked.

---

## Decision Trees & Patterns

### Decision Tree 1: SSH Authentication Strategy (Key vs. Password)

```
START: Deploy to remote host via SSH
│
├─ Is host in trusted, private network (VPC, internal datacenter)?
│  ├─ YES: Continue to next decision
│  └─ NO: MUST use key-based auth (password never leaves client)
│
├─ Do you have SSH private key available (CI/CD pipeline, local machine)?
│  ├─ YES: Use key-based auth (preferred)
│  │   └─ Verify key permissions: chmod 600
│  │   └─ Validate key format (OpenSSH or PEM)
│  │   └─ Optional: pin host key fingerprint (prevent MitM)
│  │   └─ Optional: use SSH agent or hardware key
│  │
│  └─ NO: Can you safely store SSH password in CI/CD secrets or encrypted config?
│       ├─ YES: Use password-based auth (fallback)
│       │   └─ MUST use HTTPS for all auth transmissions
│       │   └─ Log password-auth usage for audit trail
│       │   └─ Implement password rotation policy
│       │
│       └─ NO: FAIL deployment. Resolve authentication method first.
│
└─ END: Use selected auth strategy
```

**Implementation Guidance:**
- Prefer key-based auth: more secure, easier to rotate, works in CI/CD.
- Password-based auth: acceptable for dev/staging, not production.
- If rotating SSH keys: deploy new key first, maintain old key for 30 days, then remove old key.
- Store auth secrets in CI/CD vault (GitHub Secrets, AWS Secrets Manager), never in code.

---

### Decision Tree 2: SSH Retry Strategy (Connection Timeouts)

```
START: SSH connection attempt fails
│
├─ Was this the first attempt?
│  └─ YES: Check error type (see next decision)
│  └─ NO: Proceed to attempt count check
│
├─ Has this error occurred on every attempt (all N retries failed)?
│  ├─ YES: Permanent failure (host down, auth broken, firewall)
│  │   └─ Log error details (SSH diagnostics: ssh -vvv)
│  │   └─ Escalate: manual verification required
│  │   └─ STOP: Do NOT retry further
│  │
│  └─ NO: Transient failure (network blip, rate limiting)
│       └─ Proceed to backoff strategy
│
├─ What is the remaining attempt count (retries left)?
│  ├─ 0 attempts remaining: FAIL, escalate
│  ├─ 1-2 attempts remaining: Use short backoff (100-500ms), retry once more
│  └─ 3+ attempts remaining: Use longer backoff (1-5s), retry
│
├─ Backoff strategy selection:
│  ├─ Linear backoff: retry_delay = attempt_number * 100ms
│  │   └─ Use for: low-latency networks (< 50ms), when speed important
│  │
│  ├─ Exponential backoff: retry_delay = 100ms * (2 ^ attempt_number)
│  │   └─ Use for: high-latency networks (> 50ms), production deployments
│  │
│  └─ Exponential + jitter: retry_delay = 100ms * (2 ^ attempt_number) + random(0, 1000ms)
│       └─ Use for: distributed systems, prevent thundering herd
│
├─ Sleep for calculated backoff duration, then retry
│
└─ END: Connection succeeded or max attempts exhausted
```

**Implementation Guidance:**
- Default: exponential backoff with jitter, 3 retries, 10-second total timeout.
- For high-latency links (VPN, satellite): increase backoff (1s initial instead of 100ms).
- For fast networks: shorter backoff ok, but ensure at least 1 retry with 100ms delay.
- Log each attempt with duration and error: helps diagnose network issues post-deployment.

---

### Decision Tree 3: Health Check Polling Strategy (App Startup Time)

```
START: Application has been started, now verify readiness
│
├─ What is the expected application startup time?
│  ├─ < 1 second (lightweight, fast startup): ExpressJS, Go
│  │   └─ initial_delay_ms = 100, polling_interval_ms = 500, max_wait_ms = 3000
│  │
│  ├─ 1-5 seconds (medium startup): FastAPI, Spring Boot Lite
│  │   └─ initial_delay_ms = 2000, polling_interval_ms = 1000, max_wait_ms = 10000
│  │
│  ├─ 5-30 seconds (heavy startup): Spring Boot, Laravel, Rails
│  │   └─ initial_delay_ms = 10000, polling_interval_ms = 2000, max_wait_ms = 30000
│  │
│  └─ > 30 seconds (very heavy): Java with large heap, complex initialization
│       └─ initial_delay_ms = 20000, polling_interval_ms = 3000, max_wait_ms = 60000
│
├─ Check PM2 process status immediately (fast path):
│  ├─ Status is "online" and restart_time = 0:
│  │   └─ Process just started, good sign
│  │   └─ Proceed to health endpoint polling
│  │
│  └─ Status is not "online" or restart_time > 0:
│       └─ Process crashed or restarted (likely broken)
│       └─ Skip health polling, escalate immediately with PM2 error logs
│
├─ Wait initial_delay_ms before first health endpoint poll
│
├─ Poll health endpoint with polling_interval_ms between attempts
│  ├─ If healthy (200 OK, low latency): SUCCESS
│  ├─ If timeout or slow (latency spike): continue polling (app still starting)
│  └─ If error (non-200 status): continue polling, but log for diagnostics
│
├─ Stop polling when:
│  ├─ Health endpoint returns 200 OK: SUCCESS (app ready)
│  ├─ Total polling time > max_wait_ms: TIMEOUT (app not responding)
│  └─ Error pattern detected (e.g., 503 consistently): ESCALATE (app broken, not starting)
│
└─ END: App ready or health check failed
```

**Implementation Guidance:**
- Measure actual startup time in dev environment, use 1.5x that for initial_delay_ms.
- Never set initial_delay too short (< app startup time): wastes retries on guaranteed failures.
- Never set max_wait too long (> 60s): deployment takes forever, blocks other deployments.
- Log each health check attempt: helps diagnose slow startup patterns post-deployment.

---

### Decision Tree 4: Rollback Decision Tree (When to Rollback vs. Troubleshoot)

```
START: Deployment completed, monitoring detects issue
│
├─ What is the severity of the issue?
│  ├─ CRITICAL (error rate > 50%, latency spike > 10x, core service down):
│  │   └─ Immediate rollback required (no time to troubleshoot)
│  │   └─ Proceed to rollback check
│  │
│  ├─ HIGH (error rate 20-50%, latency spike 5-10x):
│  │   └─ Rollback likely required, but quick troubleshoot ok
│  │   └─ Check deployment logs for obvious issues (missing env var, syntax error)
│  │   └─ If obvious issue found: troubleshoot instead of rollback
│  │   └─ If no obvious issue: rollback (safer than guessing)
│  │
│  └─ MEDIUM/LOW (error rate < 20%, isolated errors):
│       └─ Troubleshoot first (might be transient)
│       └─ Monitor for 5 minutes, if error rate > 10%, escalate to rollback consideration
│
├─ Can rollback be executed safely (previous version is stable)?
│  ├─ YES: Previous version running, tested, metrics normal
│  │   └─ Proceed to rollback
│  │
│  └─ NO: Previous version unknown, not running, or database migration incompatible
│       └─ CANNOT rollback automatically
│       └─ Escalate to on-call for manual intervention
│       └─ Options: kill new version (if critical), wait for fix, manual rollback with downtime
│
├─ Are database migrations reversible?
│  ├─ YES: New version added optional columns, removed nothing critical
│  │   └─ Rollback safe (new version won't crash on old schema)
│  │   └─ Proceed to rollback
│  │
│  └─ NO: New version requires schema changes (added required columns, removed columns)
│       └─ CANNOT rollback to old version without manual migration rollback
│       └─ Escalate to DBA for manual intervention
│       └─ Rollback blocked until migrations are validated as reversible
│
├─ Are all dependent services compatible with previous version?
│  ├─ YES: No breaking API changes, message format same, no hard dependencies on new features
│  │   └─ Rollback safe
│  │   └─ Proceed to rollback
│  │
│  └─ NO: New version introduced breaking changes, other services depend on new API
│       └─ CANNOT rollback without coordinating dependent services
│       └─ Escalate to coordination (might require rolling back dependent services too)
│       └─ Or, accept downtime and rollback all services together
│
├─ Execute rollback:
│  ├─ Step 1: Stop new version (pm2 delete, stop monitoring alarms)
│  ├─ Step 2: Start previous version (pm2 start, verify PM2 status)
│  ├─ Step 3: Health check previous version (5-10 attempts over 30s)
│  ├─ Step 4: Verify traffic routed back to previous version (via load balancer logs)
│  ├─ Step 5: Monitor error rate for 5 minutes (should return to baseline)
│  └─ Step 6: If metrics stable, declare rollback successful; else escalate further
│
└─ END: Rollback succeeded or escalation required
```

**Implementation Guidance:**
- Rollback decision should be automated if severity is CRITICAL, but manual confirm for HIGH/MEDIUM.
- Before deploying, prepare rollback plan: "old version stable", "database migrations reversible", "dependent services compatible".
- Test rollback in staging: deploy v2, rollback to v1, verify v1 works (catches surprises).
- Have runbook for common rollback scenarios (missing env var, port conflict, etc.).

---

## Cross-References

This skill integrates with other Forge skills for complete deployment reasoning:

### Related Deploy Drivers
- **deploy-driver-local-process**: Alternative for local machine deployment (single server, no SSH required). Use when deploying to localhost in dev/test environments.
- **deploy-driver-docker-compose**: Alternative for containerized deployment (Docker + docker-compose). Use when app runs in containers instead of bare process.
- **deploy-driver-systemd**: Alternative using systemd service manager (no PM2 required). Use for system-level service management.

### Health Check & Evaluation
- **eval-driver-api-http**: Evaluates HTTP-based health checks and API responses. Use for defining health endpoint contract and testing various HTTP status codes and response formats.
- **reasoning-as-infra**: Infrastructure reasoning skill. Consult for network topology, firewall rules, jump host routing, and deployment target selection.

### Multi-Service Coordination
- **eval-product-stack-up**: Brings up entire product stack (all services) for evaluation. Use when deploying a service that depends on other services (database, cache, other microservices). Ensures dependent services are running before starting new service.

### Decision Tracking & Auditability
- **brain-read**: Look up product topology and deployment history. Use to find previous deployments, decision logs, and what worked before.
- **brain-write**: Record deployment decisions and post-mortems. Use to log why rollback was executed, what issue was found, and actions taken for future reference.

---

## Dependencies

- `ssh2` (Node.js SSH2 client)
- `curl` (on remote server for HTTP requests)
- `pm2` (on remote server)
- Node.js 14+ with async/await support

## References

- PM2 Documentation: https://pm2.keymetrics.io/
- SSH2 Protocol: RFC 4254
- HTTP Health Check Best Practices: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

## Checklist

Before declaring deployment complete:

- [ ] SSH connectivity validated with a no-op `echo ok` command before any deploy step
- [ ] Host key fingerprint validated against known whitelist on `connect()`
- [ ] No prior version running on target port (verified before `start()`)
- [ ] `start()` followed immediately by `health_check()` against application HTTP endpoint
- [ ] Application logs retrieved if health check fails
- [ ] `stop()` called unconditionally in cleanup (success and failure paths)
