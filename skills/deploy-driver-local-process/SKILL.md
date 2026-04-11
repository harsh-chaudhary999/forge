---
name: deploy-driver-local-process
description: Deploy local process. Functions: start(project_path, script), health_check(port, endpoint), stop(process_name).
type: rigid
requires: [brain-read, eval-driver-api-http]
---

# Deploy Driver for Local Process

Deploy and manage local Node.js processes via npm scripts. Tracks process IDs, performs HTTP health checks, and gracefully terminates processes. Supports rapid deployment cycles with proper resource cleanup and health verification.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Deploy Driver Local Process                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Process Fork │  │ PID Tracking │                │
│  │ (nohup)      │  │ (memory)     │                │
│  └──────────────┘  └──────────────┘                │
│         │                   │                       │
│         └───────┬───────────┘                       │
│                 ▼                                    │
│  ┌─────────────────────────────┐                   │
│  │  Process Lifecycle Mgmt     │                   │
│  │  • nohup background exec    │                   │
│  │  • pkill -f pattern match   │                   │
│  │  • SIGTERM → SIGKILL        │                   │
│  └─────────────────────────────┘                   │
│         │                                           │
│         ├─► [Start] Fork process, capture PID      │
│         ├─► [Health] HTTP GET to endpoint          │
│         └─► [Stop] Graceful shutdown sequence      │
│                                                      │
│  ┌─────────────────────────────┐                   │
│  │  Error Handling & Timeouts  │                   │
│  │  • Port conflict detection  │                   │
│  │  • Health check retry (3x)  │                   │
│  │  • Graceful shutdown (2s)   │                   │
│  └─────────────────────────────┘                   │
│                                                      │
│  ┌─────────────────────────────┐                   │
│  │  Resource Tracking          │                   │
│  │  • File descriptors         │                   │
│  │  • Process state validation │                   │
│  │  • Zombie cleanup           │                   │
│  └─────────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`start()` is called without verifying the port is free** — If another process is bound to the target port, `nohup` will succeed but the application will fail to bind and exit silently. STOP. Check port availability with `lsof -ti:<port>` before calling `start()`.
- **PID is captured from `$!` and not re-verified with `ps`** — On some systems `$!` returns the shell's job PID, not the actual application PID. STOP. Always confirm the correct PID via `ps aux | grep` after capture.
- **`health_check()` is skipped because `ps -p $PID` returned success** — Process running ≠ process ready. The application may be in initialization with the port bound but not yet serving requests. STOP. Always call `health_check()` after `start()`, never skip it.
- **`stop()` is not called when eval fails or scenario teardown runs** — A leaked process will hold the port across subsequent runs, causing the next `start()` to fail on port binding. STOP. `stop()` must be called in all teardown paths, success and failure.
- **Environment variables are inherited from the parent shell rather than set explicitly** — CI/CD environments do not have the same shell profile as a developer's local terminal. An env var that works locally will silently be absent in CI. STOP. All required environment variables must be explicitly set before `start()`.
- **Output logs from the process are not captured or linked in the eval report** — A process that silently fails or panics produces no assertion failure — the health check just times out. Without logs, diagnosis is blind. STOP. Always redirect stdout/stderr to a log file and link it in the scenario output.

## HARD-GATE: Anti-Pattern Preambles

The following rationalizations **WILL BLOCK** your deployment. These are not edge cases—they are guaranteed failure modes that will surface in production.

### 1. "nohup will always work if the command syntax is correct"

**Why This Fails:**
- `nohup` detaches from terminal but doesn't guarantee background execution on all systems. Script syntax correct ≠ environment correct.
- Process environment (PATH, NODE_ENV, LD_LIBRARY_PATH) inherited from parent shell may be incomplete in automated deployments. Your local shell works; CI/CD shell doesn't.
- `nohup` output redirection to file fails silently if directory lacks write permissions: process exits without visible error in deploy script.
- Exit code of nohup is exit code of spawned process, not nohup itself: `nohup npm run dev &` returns 0 even if npm not found (shell starts, then fails asynchronously).
- Process PID captured from `$!` refers to shell job control process, not actual child process on some systems.

**Enforcement:**
- MUST explicitly set all required environment variables before start() (no assumptions about parent shell state).
- MUST validate output redirection target exists and is writable before start().
- MUST wait 500ms after nohup, then verify process actually started: `ps -p $PID` must succeed.
- MUST not rely on `$!` alone for PID; capture from process tree or verify with `ps aux | grep`.
- MUST test start() in clean environment (fresh shell, no loaded ~/.bashrc) to match CI/CD conditions.

---

### 2. "Health checks are optional if the process starts successfully"

**Why This Fails:**
- Process appearing in `ps` output ≠ process ready to accept traffic. Process can fork and exit parent before child is ready (daemonization race).
- Application initialization is asynchronous: binds port, establishes DB connections, loads config—each can fail independently after fork.
- Health endpoint responds 200 OK but application is only partially initialized (workers still starting, cache warming incomplete).
- Health check timeout indicates overload or resource exhaustion that `ps` status never shows: memory pressure, CPU saturation, file descriptor limits.
- Skipping health check masks deployment race conditions: you report success, caller sends traffic, connection refused or 503.

**Enforcement:**
- MUST perform health_check() before returning deployment success, not optional.
- Health check MUST poll endpoint with exponential backoff: 100ms → 200ms → 400ms → 800ms (not fixed interval).
- MUST distinguish timeout (slow startup) from connection refused (port not bound) from error response (500, 503).
- MUST track latency trend: if latency increases 2x from baseline on deployment, escalate warning (indicates overload).
- MUST validate health endpoint response structure, not just status code (200 but malformed body indicates partial initialization).

---

### 3. "Process termination via SIGTERM always succeeds; SIGKILL is rarely needed"

**Why This Fails:**
- Process may ignore SIGTERM entirely (trapped but not handled, or no signal handler). Waiting 2 seconds then sending SIGKILL is necessary, not optional.
- Graceful shutdown takes longer than expected (flushing buffers, closing connections, persisting state). 2-second default grace period insufficient for real applications.
- Process in uninterruptible sleep state (waiting on kernel I/O, disk I/O hang) cannot be interrupted by SIGTERM. Only SIGKILL works.
- SIGKILL succeeds but process becomes zombie: parent process didn't reap child, zombie stays in process table consuming memory.
- Multiple processes match pkill pattern (main process + workers, main + background jobs). Killing main leaves children orphaned, then killing children fails (already dead).

**Enforcement:**
- MUST NOT assume SIGTERM succeeds; ALWAYS escalate to SIGKILL after grace period (default 2s).
- MUST verify process actually exits: `ps -p $PID` after SIGKILL must fail.
- MUST handle zombie processes: verify no `<defunct>` processes in `ps aux` output after stop().
- MUST be specific in pkill pattern to avoid killing unintended processes (use full command path, not just app name).
- MUST distinguish multiple process types: if app spawns workers, configure kill_timeout appropriately or kill children before parent.

---

### 4. "Port conflicts never happen if you use a standard port like 3000"

**Why This Fails:**
- Another process may be listening on port 3000 from previous failed deployment (zombie holding port, previous version not fully stopped).
- Development machine runs multiple services simultaneously: your test app on 3000, dev server on 3000, stray PM2 process on 3000.
- Port < 1024 requires root privileges; deployment script may not have permissions to bind (permission denied).
- Application changes port dynamically based on environment (PORT env var overrides). Deployment assumes 3000 but app binds 8000.
- Port binding races during rapid restart cycles: old process in TIME_WAIT state still occupies port, new process fails to bind (EADDRINUSE).

**Enforcement:**
- MUST check if port is already bound BEFORE starting process: `lsof -i :PORT -t` or `netstat -tulnp | grep :PORT`.
- If port occupied, MUST identify occupying process and decide: kill it (if stale) or use different port.
- MUST respect environment variable PORT overrides: verify app actually listening on configured port, not assumed port.
- MUST wait for TIME_WAIT to expire after previous stop() before restarting (2 seconds minimum, 30 seconds safer).
- MUST validate port is correct after start(): `curl -s http://localhost:PORT/health` to verify app actually listening.

---

### 5. "Signals are reliable; SIGTERM always means graceful shutdown"

**Why This Fails:**
- Application may not be signal-safe: handlers in async code paths, database transaction handling, file I/O mid-operation. SIGTERM in bad state = data corruption.
- Signal handler exceptions crash process immediately, leaving resources (file descriptors, locks, DB connections) un-cleaned. SIGKILL after SIGTERM cleans up, but brief window exists.
- Multiple signals queued (rapid restarts): process receives SIGTERM at t=0, receives SIGTERM again at t=100ms (queue limit 1). May handle both incorrectly.
- Process has opened file locks (FCT_LOCK) or IPC resources. SIGTERM doesn't release these; must be explicitly closed in handler. Zombie state holds locks.
- Application running under supervisor (PM2, systemd) complicates signal handling: supervisor forwards signal AND may auto-restart. Shutdown race.

**Enforcement:**
- MUST test application's signal handling locally: send SIGTERM, verify graceful shutdown, confirm resources released (no stale locks, DB connections closed).
- MUST implement timeout wrapper: send SIGTERM, wait grace period, verify process exit, then send SIGKILL. Do NOT assume SIGTERM works.
- MUST log signal handling: application should log when receiving SIGTERM and when it completes shutdown. Verify in logs post-deployment.
- MUST validate signal handler robustness: test in partial-initialization state (process received SIGTERM while starting up, not fully ready). Should not crash.
- MUST account for supervisor restarts: if using process supervisor, configure it to NOT auto-restart during manual stop(), or coordinate with supervisor.

---

## Function Signatures

### start(project_path, script) → {pid: number, status: "running"}

Start a local process in the background.

**Parameters:**
- `project_path` (string): Absolute path to project directory
- `script` (string): Command to run (e.g., "npm run dev" or custom script)

**Returns:**
- `pid` (number): Process ID of the spawned process
- `status` (string): "running" on success

**Implementation:**
1. Validate project_path exists and is directory
2. Verify script is not empty string
3. Check if port (from environment or config) is already in use
4. Build full command: `cd PROJECT_PATH && nohup SCRIPT > /tmp/nohup.PID.out 2>&1 &`
5. Execute command, capture shell output
6. Extract PID from shell job control ($!)
7. Wait 500ms, verify process exists: `ps -p PID`
8. Store PID in memory for later termination
9. Return {pid, status: "running"}

**Example:**
```javascript
const result = await start('/home/user/backend-api', 'npm run dev')
// { pid: 1234, status: "running" }
```

**Error Handling:**
- Throw if project_path does not exist
- Throw if script is empty
- Throw if port already in use
- Throw if process fails to start (ps -p PID fails)
- Throw if output redirection fails (permission denied on /tmp)

### health_check(port, endpoint) → {healthy: bool, latency_ms: number}

Perform HTTP health check against a running process.

**Parameters:**
- `port` (number): Port the process is listening on (e.g., 3000)
- `endpoint` (string): Health check endpoint path (e.g., "/health" or "/api/status")

**Returns:**
- `healthy` (boolean): true if HTTP 200 response received, false otherwise
- `latency_ms` (number): Round-trip latency in milliseconds

**Implementation:**
1. Construct URL: `http://localhost:{port}{endpoint}`
2. Send GET request with 5 second timeout (curl -m 5)
3. Check for 200 status code
4. Measure round-trip time (curl -w %{time_total})
5. Retry up to 3 times with exponential backoff: 100ms, 200ms, 400ms
6. On retry, check if timeout is due to app starting (connection refused = app not ready yet) vs. error (500 = app broken)
7. Return healthy status and measured latency
8. Log each attempt with latency and status for diagnostics

**Example:**
```javascript
const result = await health_check(3000, '/health')
// { healthy: true, latency_ms: 42 }
```

**Error Handling:**
- Return { healthy: false, latency_ms: 5000 } on timeout
- Return { healthy: false, latency_ms: 0 } on connection refused (app not started)
- Return { healthy: false, latency_ms: X } on non-200 status
- Distinguish between transient (retry) and permanent (escalate) failures

### stop(process_name) → {status: "stopped"}

Gracefully terminate a process.

**Parameters:**
- `process_name` (string): Process name pattern or PID to kill (e.g., "npm run dev" or "1234")

**Returns:**
- `status` (string): "stopped" on successful termination

**Implementation:**
1. Parse input: if numeric, treat as PID; if string, use pattern matching
2. First attempt SIGTERM (graceful shutdown): `kill -TERM PID` or `pkill -TERM -f PATTERN`
3. Wait 2 seconds
4. Check if process still exists: `ps -p PID`
5. If still exists, send SIGKILL: `kill -9 PID`
6. Wait 500ms for reaping
7. Verify process is gone: `ps -p PID` should fail
8. Check for zombie processes: `ps aux | grep <defunct>`
9. Return { status: "stopped" }

**Example:**
```javascript
const result = await stop('npm run dev')
// { status: "stopped" }
```

**Error Handling:**
- Throw if process cannot be killed after SIGTERM + SIGKILL
- Throw if zombie process remains (indicates child reaping failure)
- Warn if multiple processes matched pattern (indicate which PIDs were killed)

## Usage Pattern

```javascript
// Start ShopApp backend
const start_result = await start('/home/user/shopapp', 'npm run dev')
console.log(`Process started with PID: ${start_result.pid}`)

// Poll health until ready (timeout after 30s, max 30 attempts)
let healthy = false
let attempts = 0
const maxAttempts = 30
const startTime = Date.now()

while (!healthy && attempts < maxAttempts) {
  const check = await health_check(3000, '/health')
  console.log(`Health check attempt ${attempts + 1}: healthy=${check.healthy}, latency=${check.latency_ms}ms`)
  
  if (check.healthy) {
    // Verify health check is stable (not transient)
    const secondCheck = await health_check(3000, '/health')
    if (secondCheck.healthy) {
      healthy = true
      console.log(`Service ready after ${Date.now() - startTime}ms`)
      break
    }
  }
  
  attempts++
  if (attempts < maxAttempts) {
    // Wait before next attempt (exponential backoff)
    const delay = Math.min(100 * Math.pow(2, attempts), 5000)
    await new Promise(r => setTimeout(r, delay))
  }
}

if (!healthy) {
  throw new Error(`Service failed to become healthy after ${Date.now() - startTime}ms`)
}

// Run tests or other operations...

// Clean up
await stop('npm run dev')
```

## Edge Cases with Mitigation

Edge cases that WILL occur in production. Each requires specific detection and recovery logic.

### Edge Case 1: Process Startup Fails Due to Missing Dependencies or Permission Errors

**Scenario:**
You deploy an application. The start() command executes nohup successfully, process fork appears successful, PID is captured. Health check begins polling. But the process immediately exits because npm modules are missing (npm install wasn't run) or because the script file is not executable (permissions 0644 instead of 0755). Health check timeout and retries occur. After 3 retries, deployment fails. But the root cause (missing deps) is hidden in nohup output file which you forgot to check.

**How to Detect:**
- Process appears to start (PID captured) but exits within 1 second: `ps -p PID` succeeds at t=500ms, fails at t=1500ms.
- Health check times out consistently (ECONNREFUSED) for all 3 retries, not transient.
- nohup output file contains error messages: `cat /tmp/nohup.PID.out | grep -i "error\|cannot\|permission"`.
- Application log files show error at startup (if app writes logs before binding port).

**What Happens:**
- Process exits immediately, health check never succeeds.
- Deployment fails, but error message unclear (generic "health check failed").
- Operator doesn't check nohup output, blames networking or app code.
- Cascades: subsequent deployments fail with same hidden error.

**Mitigation Steps:**
1. Detect: After start(), wait 1 second then re-verify process still running:
   ```javascript
   const result = await start(path, script)
   await sleep(1000)
   const still_running = ps -p ${result.pid}`
   if (!still_running) {
     const output = fs.readFileSync(`/tmp/nohup.${result.pid}.out`, 'utf8')
     if (output.includes('not found') || output.includes('Permission denied')) {
       throw new Error(`STARTUP_FAILED: ${output}`)
     }
   }
   ```
2. Escalate: Log full nohup output for debugging: `logger.error('PROCESS_EXIT_EARLY', { pid, output })`.
3. Recovery: Operator reviews nohup output, identifies missing deps (run npm install), fixes permissions (chmod +x), and redeploys.
4. Prevention: In CI, run `npm install` before deploy. Validate script file is executable: `stat SCRIPT | grep -c 0755`.

---

### Edge Case 2: Port Conflict During Deployment (Previous Process Still Holding Port)

**Scenario:**
You stop a process via stop() call. The process receives SIGTERM and begins graceful shutdown. But it has open DB connections and takes longer than 2 seconds to close them. Your stop() call sends SIGKILL after 2 seconds, process dies, but port is still in TIME_WAIT state. Your deployment immediately calls start() on the same port. The new process fails to bind: `EADDRINUSE: Address already in use`. start() fails. Deployment fails. Operator doesn't realize the issue is port TIME_WAIT lingering from previous deployment.

**How to Detect:**
- start() fails with error containing `EADDRINUSE` or `Address already in use`.
- `lsof -i :PORT -t` returns a PID different from what we're trying to start.
- `netstat -an | grep :PORT` shows `TIME_WAIT` state (not LISTEN, but port still reserved).
- Previous stop() call occurred < 30 seconds ago.

**What Happens:**
- Rapid restart cycle fails (deployment → stop → start → fails → retry → fails).
- Operator force-kills processes to free port, but TIME_WAIT still lingers.
- Deployment blocked for 30+ seconds until kernel releases port.

**Mitigation Steps:**
1. Detect: When start() fails with EADDRINUSE, check port status:
   ```javascript
   const pidResult = exec(`lsof -i :${port} -t 2>/dev/null || netstat -tulnp | grep :${port}`)
   if (pidResult) {
     logger.error('PORT_CONFLICT', { port, status: 'TIME_WAIT or LISTEN' })
   }
   ```
2. Escalate: Wait before retrying start():
   ```javascript
   if (startFailed && error.includes('EADDRINUSE')) {
     logger.warn('PORT_CONFLICT_DETECTED: waiting 5s for TIME_WAIT to expire')
     await sleep(5000)
     // Retry start()
   }
   ```
3. Recovery: If TIME_WAIT persists, operator can: increase TIME_WAIT reduction in kernel (`net.ipv4.tcp_tw_reuse=1` on Linux), or use different port temporarily.
4. Prevention: Configure application to use SO_REUSEADDR socket option (Node.js http server does this by default). In graceful shutdown, explicitly close all connections: `server.close()` then `connections.forEach(c => c.destroy())`.

---

### Edge Case 3: Health Check Succeeds But Application Not Actually Ready (Race Condition)

**Scenario:**
Your application's health endpoint returns 200 OK immediately after binding port. But the app is still initializing workers, loading config, warming cache. Health check succeeds at t=1s. Deployment reports success. Real traffic arrives at t=2s. App is now ready but was briefly not-ready at t=1.5s. Some requests timeout. Caller doesn't realize this is a deployment timing issue, blames application code.

**How to Detect:**
- Health check succeeds (200 OK), latency is low (< 50ms).
- But error rates spike in the 5-10 seconds after deployment.
- Application logs show "worker started" or "cache warming complete" at t=3s (after health check).
- Second health check 1 second later shows degraded latency (200ms instead of 50ms), indicating load.

**What Happens:**
- Deployment appears successful, but application is in partial-ready state.
- Early requests timeout or get 503, appear to be traffic spike (not deployment issue).
- Difficult to correlate with deployment (health check passed, so deployment successful, right?).

**Mitigation Steps:**
1. Detect: Perform health check twice, separated by 1 second:
   ```javascript
   const check1 = await health_check(port, endpoint)
   await sleep(1000)
   const check2 = await health_check(port, endpoint)
   
   if (check1.healthy && check2.latency_ms > check1.latency_ms * 2) {
     logger.warn('HEALTH_CHECK_LATENCY_REGRESSION', {
       first_ms: check1.latency_ms,
       second_ms: check2.latency_ms
     })
     // Application may not be fully ready, escalate
   }
   ```
2. Escalate: Wait longer before declaring deployment success. Health check should pass consistently (3x in a row) before confirming readiness.
3. Recovery: Configure application to not return 200 on health endpoint until all initialization complete. Or delay health endpoint binding until fully ready.
4. Prevention: Application should log all initialization steps. Wrapper script should wait for specific log message ("Service ready") instead of relying on health endpoint alone.

---

### Edge Case 4: Rapid Restart Cycle Causes Process Resource Limits (File Descriptor Exhaustion)

**Scenario:**
You deploy v1, it fails. You redeploy v2 within 1 second. Each process fork consumes file descriptors (stdin, stdout, stderr, plus app file handles). If processes don't fully exit before new ones start, file descriptor table fills up. At FD limit (default 1024 per process), new process fork fails with `EMFILE: too many open files`. Deployment fails. System is now in bad state: processes stuck, can't start new ones, can't even kill existing ones (kill command needs FDs).

**How to Detect:**
- start() fails with error `EMFILE: too many open files`.
- `lsof | wc -l` shows FD count near ulimit (e.g., 1020 of 1024).
- Multiple processes in zombie state: `ps aux | grep <defunct>` shows many.
- Kernel logs show "file table overflow" or similar.

**What Happens:**
- Deployment fails with cryptic error ("too many open files").
- Subsequent deployments also fail (FDs still exhausted).
- System requires manual intervention to reap zombies and free FDs.
- Service unavailable during recovery.

**Mitigation Steps:**
1. Detect: Before start(), check current FD usage:
   ```javascript
   const fdsResult = exec(`lsof | wc -l`)
   const fdsUsed = parseInt(fdsResult.stdout.trim())
   const fdsLimit = exec(`ulimit -n`).stdout.trim()
   if (fdsUsed > fdsLimit * 0.8) {
     throw new Error(`FD_EXHAUSTION: ${fdsUsed}/${fdsLimit} FDs in use`)
   }
   ```
2. Escalate: If FD approaching limit, do NOT attempt start(). Require manual cleanup first.
3. Recovery: Operator runs `lsof | grep <defunct>` to find zombies, then `kill -9 PID` to reap them. Or increase ulimit: `ulimit -n 4096`.
4. Prevention: Configure process supervisor to not fork if FD count > 80% limit. In stop(), explicitly close all file handles before SIGKILL. In nohup redirection, use `/dev/null` instead of file: `nohup CMD > /dev/null 2>&1 &`.

---

### Edge Case 5: Graceful Shutdown Timeout Insufficient for Application Cleanup

**Scenario:**
Your application is a web service with persistent connections (WebSockets, long-polling). During stop(), process receives SIGTERM. App starts closing connections gracefully (flushing buffers, sending close frames). But the process needs 10 seconds to fully shutdown. Your stop() function waits only 2 seconds (default grace period), then sends SIGKILL. App dies mid-shutdown, clients receive connection resets, some data in flight is lost. It appears the new deployment (v2) caused data loss, but actually it was the stop of v1 that cut off connections.

**How to Detect:**
- Error logs show connection reset errors at time of deployment.
- Application logs in v1 show "Graceful shutdown started" but not "Graceful shutdown complete" (killed mid-shutdown).
- Clients report connection refused or reset right after deployment.
- Latency spike at deployment time (TCP re-connection overhead).

**What Happens:**
- In-flight requests are dropped (connection resets).
- Data loss if application was persisting state (partially written records).
- Appears to be new version's fault (timing of incident matches deployment).
- Cascading failures if clients don't handle connection resets gracefully.

**Mitigation Steps:**
1. Detect: After graceful shutdown, verify process actually exited cleanly (didn't need SIGKILL):
   ```javascript
   const needsSigkill = !processExited(pid) after SIGTERM + grace_period
   if (needsSigkill) {
     logger.warn('GRACEFUL_SHUTDOWN_TIMEOUT', {
       grace_period_ms,
       required_sigkill: true
     })
   }
   ```
2. Escalate: If SIGKILL was needed, investigate why. Application may need longer grace period or may have shutdown bugs.
3. Recovery: Increase grace period in stop(): `const gracePeriodMs = 10000` instead of 2000. Monitor if app still needs SIGKILL after increase.
4. Prevention: Test application's graceful shutdown locally: send SIGTERM, measure actual shutdown time, configure grace period to 2x that. Log when shutdown begins and completes. Document expected shutdown time.

---

### Edge Case 6: Health Check Endpoint Exists But Application Core Broken

**Scenario:**
Your application has a `/health` endpoint that returns 200 OK if the web server is running. But the application's core logic (database connection, cache initialization, worker threads) is broken or not yet initialized. Health check passes. Deployment succeeds. Real traffic arrives and hits endpoints that depend on database. All requests fail with 500 errors. Incident fires immediately. Investigation reveals the health endpoint was too shallow: it only checked if the web server was running, not if the application was functional.

**How to Detect:**
- Health check returns 200 OK with very fast response time (< 10ms) immediately after start().
- But subsequent requests to application endpoints fail (500, 503, timeout).
- Application logs show database connection errors or initialization failures that occurred after health check.
- Other services depending on this application report failures.

**What Happens:**
- Deployment passes all checks, but application is non-functional.
- Real traffic discovers the failure, causes incidents.
- Developers blame new code, but root cause is insufficient health check.
- Cascading failures in dependent services.

**Mitigation Steps:**
1. Detect: Health check endpoint should be comprehensive, not shallow:
   ```javascript
   // Good health check: verify all critical dependencies
   GET /health returns:
   {
     status: "ok",
     database: "connected",
     cache: "ready",
     workers: 5
   }
   ```
2. Escalate: If health check response doesn't include dependency health, escalate. Require application to expose detailed health info.
3. Recovery: Implement comprehensive health endpoint that checks all critical dependencies before returning 200 OK.
4. Prevention: In application code, ensure health endpoint is last to initialize (after all dependencies). Test health endpoint against failing dependencies: disable database, health should return 500, not 200.

---

### Edge Case 7: Process Remains in Zombie State After SIGKILL (Parent Process Didn't Reap)

**Scenario:**
You call stop() on a process. SIGTERM sent, grace period waits, SIGKILL sent. Process disappears from `ps -p PID` output (ps says process not found). But `ps aux` still shows the process in `<defunct>` state (zombie). Process is dead but not reaped by parent. Zombie consumes PID table entry. After many deployments with failing stops, PID table fills up. System cannot fork new processes. New deployments cannot start even basic processes like `/bin/sh`. System requires manual intervention (reboot or manual parent reaping).

**How to Detect:**
- `ps -p PID` fails (process not found), but `ps aux | grep PID | grep defunct` succeeds.
- `ps aux` shows `<defunct>` or `Z` state in the STAT column.
- PID table filling up: `ps aux | wc -l` approaching kernel limit (often 32768).
- New process fork fails: `ENOMEM: Cannot allocate memory` or similar.

**What Happens:**
- Zombies accumulate over time (one per failed deployment).
- PID table fills up, system cannot fork new processes.
- All deployments fail (even basic shell commands fail to fork).
- System requires reboot or manual parent reaping.

**Mitigation Steps:**
1. Detect: After SIGKILL, verify process is not in zombie state:
   ```javascript
   const psOutput = exec(`ps aux | grep ${pid}`)
   if (psOutput.includes('<defunct>') || psOutput.includes(' Z ')) {
     logger.error('ZOMBIE_PROCESS_DETECTED', { pid })
     // Parent process didn't reap child
   }
   ```
2. Escalate: If zombie detected, parent process may be stuck. Investigate parent PID and why it didn't reap.
3. Recovery: Kill parent process (if safe), which triggers reaping of children. Or manually reap: `wait` command on parent shell.
4. Prevention: Ensure parent process installs signal handlers for SIGCHLD to reap dead children. In shell scripts, use `set -m` (job control on) and periodically call `jobs -l` to reap. In Node.js, child_process automatically reaps, but custom fork() calls must handle SIGCHLD.

---

## Common Pitfalls

Pitfalls that surface repeatedly across deployments. Each requires proactive prevention and detection.

### Pitfall 1: nohup Output Redirection Gotchas

**The Problem:**
You use nohup to detach process, but redirect stdout/stderr to a file: `nohup npm run dev > /tmp/app.log 2>&1 &`. Over time, the log file grows unbounded. After a few days, the log file is 1GB and takes 30 seconds to write to. Application startup is blocked waiting for log write to complete. Deployment times out. Operator doesn't realize the root cause is log file size.

**Why It Happens:**
- No log rotation configured on `/tmp/app.log`. Application logs aggressively (100 lines/second).
- File write I/O slow on full filesystem (kernel cache pressure, disk thrashing).
- nohup blocks on stdout write, blocking process startup.

**Prevention:**
- Redirect to `/dev/null` for ephemeral logs: `nohup CMD > /dev/null 2>&1 &`.
- If logs needed, use log rotation: `nohup CMD | rotatelogs /tmp/app.%Y%m%d.log 1M &` (rotate at 1MB).
- Monitor log file size: if growing > 10MB/hour, investigate application logging verbosity.
- Use application's built-in logging (not stdout), which typically includes rotation and cleanup.

---

### Pitfall 2: Process ID Tracking Lost Across Restarts

**The Problem:**
You call start(), get back PID 1234. You store this PID in memory for later stop(). Later, the process crashes and is restarted by systemd or supervisor. New process gets different PID (5678). Your stored PID 1234 is now stale. When you call stop(1234), you kill the wrong process (or nothing), and the actual application (PID 5678) keeps running.

**Why It Happens:**
- PID tracking assumes process never restarts. Real applications crash and get restarted by supervisors.
- No persistence of PID mapping (stored in memory, lost on script termination).
- Process restart changes PID, invalidating all tracking.

**Prevention:**
- Don't rely on PID alone. Use process pattern matching: `stop('npm run dev')` instead of `stop(1234)`.
- For critical applications, maintain explicit PID file: app writes its PID to `/var/run/app.pid` at startup. Stop script reads this file before killing.
- Periodically re-verify process ID: `ps aux | grep PATTERN` immediately before kill, confirm PID still matches pattern.
- Log all PID changes: if process restarts, log new PID for audit trail.

---

### Pitfall 3: Health Check Timing Assumptions for Startup

**The Problem:**
You health check with default exponential backoff (100ms, 200ms, 400ms). Application takes 2 seconds to startup. First 3 health checks fail (app not ready). At t=0.7s, you've exhausted all retries and deployment fails. But if you had waited 1 second before first check, health checks would succeed.

**Why It Happens:**
- Health check retry strategy assumes fast startup (< 1 second).
- No distinction between app types (Node.js vs. Java startup times differ 10x).
- Fixed initial retry logic doesn't adapt to app startup time.

**Prevention:**
- Configure initial delay based on app startup time: `initial_delay_ms = expected_startup_ms * 0.8`.
- For unknown apps, use conservative initial delay: 2 seconds minimum.
- Log expected startup time in deployment config, then verify actual vs. expected.
- If health check takes longer than expected, extend timeout (don't assume timeout = failure).

---

### Pitfall 4: SIGTERM vs. SIGKILL Escalation Pattern Misunderstanding

**The Problem:**
Your stop() function sends SIGTERM, waits 2 seconds, sends SIGKILL. But application's signal handler for SIGTERM hangs (bad code, deadlock). App doesn't actually exit. At t=2s, SIGKILL is sent, app dies. But now the operator wonders: did SIGTERM fail, or did it succeed but take 2+ seconds? No clear indication of which signal was effective.

**Why It Happens:**
- No logging of signal handling. Application doesn't log when it receives/handles signals.
- Timeout between SIGTERM and SIGKILL fixed, not tied to actual shutdown time needed.
- Operator can't distinguish "SIGTERM successful but slow" from "SIGTERM failed, SIGKILL saved us".

**Prevention:**
- Log signal handling in application: "Received SIGTERM, starting graceful shutdown", "Graceful shutdown complete".
- Log in stop() function which signal was sent and when: `logger.info('Sent SIGTERM', { pid, time: t0 })`, `logger.info('Sent SIGKILL', { pid, time: t2 })`.
- Monitor shutdown time: if consistent > 5s, increase grace period rather than relying on SIGKILL.
- Test signal handling locally: send SIGTERM, monitor logs, verify shutdown completes in reasonable time.

---

### Pitfall 5: Port Detection Failures Due to Environment Variable Mismatches

**The Problem:**
Your deployment assumes application listens on port 3000 (hardcoded in health_check call). But application reads PORT environment variable: `const port = process.env.PORT || 3000`. You deploy with `PORT=8000` env var set. App binds port 8000. Your health check queries port 3000, connection refused. Health check fails. Deployment fails. But root cause is environment variable mismatch, not app failure.

**Why It Happens:**
- Health check port hardcoded, doesn't read from same config as application.
- Environment variables not synchronized between deployment and health check.
- No validation that app is actually listening on expected port.

**Prevention:**
- Make health check port a parameter, not hardcoded: `await health_check(config.port, '/health')` where config is shared.
- After start(), verify app is listening on expected port: `lsof -i :PORT | grep PROCESS_NAME`.
- Log the port application is actually listening on, not assumed port.
- In health check failure, do `netstat -tulnp` to reveal what port the process is actually listening on.

---

### Pitfall 6: Environment Variable Inheritance Issues in CI/CD

**The Problem:**
Your deployment script starts with `npm run dev`. In your local shell, `npm run dev` reads `.env` file and sets NODE_ENV=production. In CI/CD container, `.env` file is missing (not copied into container), NODE_ENV defaults to development. Application runs in dev mode (verbose logs, no optimization). Health check passes. Deployment succeeds. Real traffic gets non-optimized version. Performance is degraded.

**Why It Happens:**
- Assumption that environment setup (`.env` file) exists in deployment environment.
- No validation of environment variables before start().
- Different behavior in dev vs. CI/CD not caught by health check (health check just checks port, not performance).

**Prevention:**
- Explicitly set all required environment variables in deployment: `NODE_ENV=production npm run dev` instead of relying on `.env`.
- Validate required env vars before start(): check `process.env.NODE_ENV`, `process.env.DATABASE_URL`, etc.
- Log environment variables at deployment time (sanitized, no credentials): helps debug env mismatches.
- Test deployment in CI/CD container locally (use Docker), not just on local machine.

---

### Pitfall 7: Concurrent Start Attempts Cause Race Conditions

**The Problem:**
Deployment script calls start(). While waiting for health check, deployment script is killed (timeout, user interrupt). Another deployment process starts (retry, or parallel deployment). Now two start() calls are running simultaneously, both trying to bind the same port. First one succeeds, second one fails with EADDRINUSE. Both deployments think they succeeded/failed respectively, leading to inconsistent state.

**Why It Happens:**
- No locking mechanism to prevent concurrent starts.
- Multiple deployment agents can run simultaneously (parallel CI/CD jobs, manual retries).
- No idempotency check (start is not idempotent, starting twice = error).

**Prevention:**
- Implement lock file: `start()` creates `/var/run/app.lock`. If lock exists, fail with "already starting". Remove lock after start succeeds.
- Check if process already running before start: `if (ps -p $(cat /var/run/app.pid)) { throw 'already running' }`.
- Ensure deployment orchestration prevents concurrent deployments to same service (coordinator, queue).
- Log concurrent attempt detection: helps debug why deployments are failing intermittently.

---

## Decision Trees & Patterns

### Decision Tree 1: Health Check Retry Strategy (Based on Application Startup Characteristics)

```
START: Application has been started, now verify readiness via health check
│
├─ What is the expected application startup time?
│  ├─ < 1 second (lightweight, fast startup): ExpressJS, Go, PHP-FPM
│  │   └─ initial_delay_ms = 200, polling_interval_ms = 500, max_wait_ms = 3000
│  │   └─ rationale: app ready almost immediately, short total wait time
│  │
│  ├─ 1-5 seconds (medium startup): FastAPI, Spring Boot Lite, Flask
│  │   └─ initial_delay_ms = 2000, polling_interval_ms = 1000, max_wait_ms = 10000
│  │   └─ rationale: wait before first check (app still starting), poll every second
│  │
│  ├─ 5-30 seconds (heavy startup): Spring Boot, Laravel, Rails, Django
│  │   └─ initial_delay_ms = 10000, polling_interval_ms = 2000, max_wait_ms = 30000
│  │   └─ rationale: long initial wait, infrequent polling to avoid overload
│  │
│  └─ > 30 seconds (very heavy): Java with large heap, complex initialization
│       └─ initial_delay_ms = 20000, polling_interval_ms = 5000, max_wait_ms = 60000
│       └─ rationale: very long initial wait, infrequent polling, extended total timeout
│
├─ Check process status immediately (before health endpoint):
│  ├─ If ps -p PID fails: process already exited
│  │   └─ Escalate immediately (process dead, not starting)
│  │
│  ├─ If pm2/ps shows restart_time > 2: process crashed and restarted
│  │   └─ Escalate immediately (app broken during startup, not transient)
│  │
│  └─ If process running and restart_time = 0: process just started
│       └─ Continue to health endpoint polling
│
├─ Wait initial_delay_ms before first health endpoint poll
│
├─ Poll health endpoint every polling_interval_ms:
│  ├─ If 200 OK with normal latency (< baseline * 2): SUCCESS
│  │   └─ Verify with second health check (confirm stable, not transient)
│  │
│  ├─ If timeout (no response in 5s): app still starting or hung
│  │   └─ Continue polling (app may still be initializing)
│  │
│  ├─ If connection refused: port not yet bound
│  │   └─ Continue polling (app hasn't started listening yet)
│  │
│  ├─ If 500/503 error: app started but broken or overloaded
│  │   └─ Log error, continue polling (might recover as initialization continues)
│  │
│  └─ If latency spike (> baseline * 3): app responding but degraded
│       └─ Log latency regression, continue polling but prepare escalation
│
├─ Stop polling when:
│  ├─ 200 OK returned twice in a row: SUCCESS (app ready)
│  ├─ Total polling time > max_wait_ms: TIMEOUT
│  ├─ Error pattern detected (e.g., 503 consistently for > 10s): ESCALATE
│  └─ Process crashed (ps -p PID fails): ESCALATE
│
└─ END: App ready, health check failed, or escalation required
```

**Implementation Guidance:**
- Measure actual startup time in dev environment: run app, time until health endpoint responds.
- Use 1.5x measured startup time for initial_delay_ms (account for slower environments).
- For unknown apps, default to medium startup time (5s).
- Log every health check attempt: `{ attempt, time_elapsed, latency_ms, status, action }`.
- If health checks consistently exceed expected time, increase initial_delay_ms in production config.

---

### Decision Tree 2: Graceful Shutdown Decision Tree (When to Escalate from SIGTERM to SIGKILL)

```
START: Process termination required
│
├─ Is the process configured to handle SIGTERM gracefully?
│  ├─ YES (application logs signal handling, has shutdown handler):
│  │   └─ Send SIGTERM first (preferred)
│  │
│  └─ NO (process ignores SIGTERM, or not known):
│       └─ Consider direct SIGKILL (if shutdown state not critical)
│       └─ Or send SIGTERM anyway with knowledge SIGKILL will follow
│
├─ Send SIGTERM: kill -TERM PID or pkill -TERM -f PATTERN
│
├─ What is the application's graceful shutdown time?
│  ├─ < 2 seconds (fast shutdown): HTTP servers, stateless services
│  │   └─ grace_period_ms = 5000 (2.5x expected time)
│  │
│  ├─ 2-10 seconds (normal shutdown): services with connection cleanup
│  │   └─ grace_period_ms = 10000 (conservative)
│  │
│  ├─ 10-30 seconds (slow shutdown): DB connection pool cleanup
│  │   └─ grace_period_ms = 30000 (or longer if known)
│  │
│  └─ > 30 seconds (very slow): data flush, batch operations
│       └─ grace_period_ms = 60000 (or configured timeout)
│
├─ Wait grace_period_ms
│
├─ Check if process still running: ps -p PID
│  ├─ If process exited: SUCCESS
│  │   └─ Verify no zombie: ps aux | grep <defunct> should not show PID
│  │
│  └─ If process still running:
│       └─ SIGTERM didn't work or shutdown took too long
│       └─ Continue to forceful termination
│
├─ Send SIGKILL: kill -9 PID (forced termination)
│
├─ Wait 500ms for reaping
│
├─ Verify process is gone:
│  ├─ If ps -p PID fails: SUCCESS (process terminated)
│  ├─ If ps -p PID succeeds: FAILURE (process still running, escalate)
│  └─ If ps aux shows <defunct>: ZOMBIE (parent didn't reap, escalate)
│
├─ Log the termination sequence for diagnostics:
│  {
│    pid,
│    sigterm_sent: true,
│    sigterm_grace_ms: grace_period_ms,
│    sigkill_sent: (if SIGTERM didn't work),
│    final_status: 'terminated|zombie|still_running'
│  }
│
└─ END: Process terminated or escalation required
```

**Implementation Guidance:**
- ALWAYS escalate from SIGTERM to SIGKILL (don't assume SIGTERM works).
- Grace period should match application type: stateless services 5s, stateful services 10-30s.
- Test graceful shutdown locally: send SIGTERM, measure actual shutdown time, set grace period to 2x that time.
- Verify application logs signal handling (important for debugging).
- If SIGKILL was needed, investigate why: application may have shutdown bugs or need longer grace period.

---

### Decision Tree 3: Port Conflict Resolution (Detection and Recovery)

```
START: Process needs to bind to a port
│
├─ Is the port already in use?
│  └─ Check: lsof -i :PORT -t or netstat -tulnp | grep :PORT
│
├─ If port is free:
│  ├─ Attempt to start process
│  └─ Monitor startup for EADDRINUSE errors
│
├─ If port is occupied:
│  ├─ What is the state of the occupying process?
│  │
│  ├─ Is it the process we're about to start (restart scenario)?
│  │   ├─ YES: Kill occupying process first, then start new one
│  │   │   └─ Determine kill strategy: graceful (SIGTERM) or forceful (SIGKILL)
│  │   │   └─ If graceful: allow 2-5s grace period
│  │   │   └─ If forceful: kill immediately, accept connection interruption
│  │   │
│  │   └─ NO: Determine if occupying process should be killed
│  │       ├─ If process is from previous deployment (stale): KILL (stop() should have cleaned up)
│  │       ├─ If process is unrelated service: FAIL (don't kill unrelated processes)
│  │       └─ If process is partial restart (TIME_WAIT): WAIT (kernel will release port soon)
│  │
│  ├─ Determine port state:
│  │   ├─ LISTEN state: process actively listening, won't release port soon
│  │   │   └─ MUST kill before starting new process
│  │   │
│  │   ├─ TIME_WAIT state: old connection waiting to close (kernel TCP state)
│  │   │   └─ WAIT 5-10 seconds, port will be released automatically
│  │   │   └─ If must start immediately, use SO_REUSEADDR socket option
│  │   │
│  │   └─ CLOSE_WAIT state: process has closed, waiting for remote to close
│  │       └─ WAIT a few seconds, should transition to TIME_WAIT then released
│  │
│  ├─ Recovery actions:
│  │   ├─ If graceful kill: send SIGTERM, wait grace period, verify process exited
│  │   ├─ If forceful kill: send SIGKILL, wait 500ms, verify process exited
│  │   ├─ If TIME_WAIT: wait 5-10 seconds, retry start
│  │   └─ If none work: escalate, require manual intervention
│  │
│  ├─ Escalation:
│  │   ├─ Log conflicting PID, command, and port state
│  │   ├─ Alert operator if port still occupied after recovery attempts
│  │   └─ Provide diagnostic info: `lsof -i :PORT`, `netstat -an | grep :PORT`
│  │
│  └─ Retry start:
│       ├─ After killing old process: retry immediately
│       ├─ After TIME_WAIT expiry: retry after 5-10 second wait
│       └─ Cap retry attempts to avoid infinite loops
│
└─ END: Port bound successfully or escalation required
```

**Implementation Guidance:**
- Always check port before starting, don't assume it's free.
- On EADDRINUSE error, use `lsof` to identify occupying process and its state.
- For development, use SO_REUSEADDR or change port if TIME_WAIT conflicts occur.
- For production, implement proper shutdown sequence to avoid lingering processes.
- Document expected port and how to override via environment variable.

---

### Decision Tree 4: Process State Verification (How to Detect Running vs. Crashed vs. Zombie)

```
START: Verify actual state of process
│
├─ Primary check: ps -p PID
│  ├─ If succeeds (exit code 0): process exists and running
│  │   └─ Continue to secondary verification
│  │
│  └─ If fails (exit code 1): process does not exist
│       ├─ Is this expected (process was stopped)?
│       │   └─ Return "stopped" status
│       │
│       └─ Is this unexpected (process should be running)?
│           └─ Escalate: process crashed and wasn't restarted
│
├─ Secondary check: ps aux | grep PID (detailed process info)
│  ├─ Look at STAT column:
│  │   ├─ R (running): process is actively running
│  │   ├─ S (sleeping): process sleeping (normal for idle services)
│  │   ├─ Z (zombie): process dead but parent not reaped (ESCALATE)
│  │   └─ T (traced): process is stopped or being debugged (ESCALATE)
│  │
│  ├─ Look at command line:
│  │   ├─ Should match expected command
│  │   ├─ If different command, wrong process found (mismatch in PID tracking)
│  │   └─ If command includes garbage characters, process corrupted
│  │
│  └─ Look at CPU/memory usage:
│       ├─ 0% CPU for idle service: normal
│       ├─ 100% CPU: possible runaway loop or intensive operation
│       └─ Unusually high memory: possible memory leak
│
├─ Tertiary check: Health endpoint or process output
│  ├─ If ps says running but health check fails:
│  │   ├─ Process may be hung/deadlocked (stuck but not terminated)
│  │   └─ May need SIGKILL even though ps shows running
│  │
│  └─ If health check passes:
│       ├─ Assume process is functional (not just existing, but working)
│       └─ Additional checks only needed if health check degraded
│
├─ Final status determination:
│  ├─ "running": ps -p succeeds, ps aux shows R/S, health check passes
│  ├─ "slow": ps -p succeeds, health check slow but succeeds
│  ├─ "unhealthy": ps -p succeeds, health check fails (500/503 error)
│  ├─ "unresponsive": ps -p succeeds, health check times out (process hung)
│  ├─ "zombie": ps -p fails but ps aux shows Z state (parent not reaped)
│  ├─ "stopped": ps -p fails, ps aux doesn't show process
│  └─ "error": ambiguous state (escalate for manual review)
│
└─ END: Actual process state determined
```

**Implementation Guidance:**
- Use multiple checks (ps -p, ps aux, health endpoint) for reliable verification.
- Zombie detection is critical: if zombie found, escalate (parent process issue).
- Distinguish between "process exited" (expected, OK to restart) and "process hung" (problem, needs investigation).
- Log detailed process state for diagnostics: STAT, command line, CPU/memory, age.
- If process state unclear, default to safe action: don't restart without investigation.

---

## Cross-References

This skill interacts with:

- **eval-driver-api-http**: Health check implementation uses HTTP protocol and timeout patterns (see "Health Check Polling Strategy" in Decision Tree 1).
- **deploy-driver-pm2-ssh**: Similar patterns for graceful shutdown and health checks, but over SSH to remote servers. Compare anti-patterns (e.g., "SIGTERM always works" vs. "Timeouts are optional").
- **deploy-driver-docker-compose**: Container-based deployment; both use health checks and graceful shutdown. Compare port conflict resolution (containers have own port namespace).
- **reasoning-as-infra**: Resource management patterns (file descriptor limits, process quotas, timezone considerations) relate to Edge Case 4 and resource constraint section.
- **brain-read/brain-write**: Deployment decisions (rollback criteria, post-deployment monitoring) should be logged using brain-write for audit trail and later recall via brain-read.

---

## Resource Constraints & Performance Considerations

### File Descriptor Limits

**The Issue:**
Each process consumes file descriptors (stdin, stdout, stderr, plus application file handles, sockets, pipes). Default system limit is often 1024 per process. If you spawn many processes rapidly (rapid restart cycles), FD table fills up, new processes fail to fork.

**Mitigation:**
1. Check current FD usage before start():
   ```
   lsof | wc -l   # total FDs in use
   ulimit -n       # current process FD limit
   ```
2. Increase system FD limit if approaching capacity:
   ```bash
   # Per-process: ulimit -n 4096
   # System-wide: /etc/security/limits.conf
   ```
3. Minimize FD waste:
   - Redirect nohup output to `/dev/null` instead of files (saves FDs)
   - In stop(), explicitly close file handles before SIGKILL
   - Reap zombie processes: `ps aux | grep <defunct> | wc -l` should be 0

### Resource Exhaustion During Rapid Restarts

**The Issue:**
Rapid deployment cycles (kill old, start new) can exhaust resources: port TIME_WAIT, file descriptors, process table entries, memory from process overhead.

**Mitigation:**
1. Implement minimum delay between stop() and start(): 1-2 seconds.
2. Batch cleanup: after multiple deployments, force cleanup of zombies and TIME_WAIT states.
3. Monitor resource usage:
   ```
   # Check zombie processes
   ps aux | grep <defunct> | wc -l
   
   # Check TIME_WAIT connections
   netstat -an | grep TIME_WAIT | wc -l
   
   # Check FD usage trend
   lsof | wc -l
   ```
4. Set resource limits on deployment process itself: `ulimit -n 1024 -u 100` to prevent single deployment from consuming system resources.

### Performance Considerations

**Health Check Overhead:**
- Each health check makes HTTP request (network round-trip, ~10-100ms).
- Exponential backoff 3 retries = ~0.7s total.
- If health check every 5 seconds for monitoring, 144 health checks per hour = small overhead.
- Batch health checks: check multiple services with one operation to reduce latency impact.

**Process Startup Overhead:**
- Process fork/exec is expensive on slow systems (embedded devices, VMs with limited resources).
- nohup + output redirection adds ~50-100ms overhead.
- Node.js startup can take 100-500ms (module loading, V8 optimization).
- To optimize: pre-warm process before deployment, use process recycling (keep alive, reuse), or containerize.

**Graceful Shutdown Wait Time:**
- Grace period of 10-30 seconds blocks deployment flow.
- Can parallelize: start health check for new process while waiting for old process to shutdown.
- Or implement health check on both old and new process simultaneously, switch once new is ready.

---

## Debugging Section

### Troubleshooting Common Failures

**Problem: start() succeeds but health check always times out**

Possible causes and diagnostics:
1. Process not listening on expected port:
   ```bash
   lsof -i :3000  # Is process actually listening?
   netstat -tulnp | grep 3000
   ```
2. Application failing during initialization:
   ```bash
   cat /tmp/nohup.*.out  # Check startup errors
   ps -ef | grep npm     # Is process still running?
   ```
3. Health endpoint broken or unresponsive:
   ```bash
   curl -v http://localhost:3000/health  # Test endpoint directly
   ```
4. Firewall or localhost binding issue:
   ```bash
   curl http://127.0.0.1:3000/health  # Try loopback
   ```

**Problem: stop() fails with EADDRINUSE when trying to restart**

Possible causes and diagnostics:
1. Port still in TIME_WAIT state:
   ```bash
   netstat -an | grep 3000
   ```
   Solution: wait 5-10 seconds or use SO_REUSEADDR socket option.

2. Process didn't fully exit:
   ```bash
   ps aux | grep npm  # Is old process still running?
   lsof -i :3000 -t   # What PID is holding port?
   ```
   Solution: verify SIGKILL was sent, check for zombies.

**Problem: Process becomes zombie after stop()**

Possible causes and diagnostics:
1. Parent process not reaping children:
   ```bash
   ps aux | grep <defunct>  # Confirm zombie exists
   ps -o ppid= -p <zombie_pid>  # Who is parent?
   ```
2. Shell script not using job control:
   ```bash
   # Parent shell needs: set -m (job control on)
   # Or manually call: wait $! to reap
   ```

**Problem: Health check succeeds but real traffic fails**

Possible causes:
1. Health endpoint too shallow (doesn't check all dependencies).
2. Application not fully initialized (workers still starting, cache warm incomplete).
3. Network latency degraded (health check fast from localhost, but real traffic slower).

Solutions:
1. Enhance health endpoint to check database, cache, critical dependencies.
2. Add initialization logging, wait for "ready" message before health check success.
3. Monitor latency trend: health check latency should match pre-deployment baseline.

### Logging Best Practices

Log format for all operations:
```
{
  timestamp: "2026-04-10T10:30:45.123Z",
  operation: "start|health_check|stop",
  project_path: "/home/user/app",
  port: 3000,
  pid: 1234,
  status: "success|error",
  duration_ms: 1234,
  error?: "ERROR_CODE",
  details: {
    // operation-specific details
    nohup_output: "...",
    health_latency_ms: 42,
    attempt: 1
  }
}
```

Examples:
```javascript
// start() success
{ operation: 'start', pid: 1234, status: 'success', duration_ms: 150 }

// health_check() failure with details
{ operation: 'health_check', status: 'error', error: 'TIMEOUT', details: { attempt: 3, latency_ms: 5000 } }

// stop() partial failure (SIGKILL needed)
{ operation: 'stop', pid: 1234, status: 'success', details: { sigterm_sent: true, sigkill_sent: true } }
```

This enables:
- Post-deployment analysis (why did deployment take 45 seconds?)
- Trend analysis (health check latency increasing?)
- Troubleshooting (log shows which operation failed)
- Audit trail (who deployed, when, what happened)

---

## Summary

Deploy Driver for Local Process provides reliable, safe process management with proper error handling, resource tracking, and health verification. Key principles:

1. **Never assume**: verify at each step (process started, port bound, app healthy).
2. **Escalate gracefully**: SIGTERM first, SIGKILL if needed, log and alert.
3. **Health check is mandatory**: not optional, must be comprehensive and adaptive.
4. **Resource awareness**: track file descriptors, port TIME_WAIT, zombie processes.
5. **Observability**: log every operation with timing and errors.
6. **Testability**: all functions must work in clean environment (CI/CD containers).

Use this driver for development, testing, and light production workloads. For heavy production with strict availability requirements, consider deploy-driver-pm2-ssh or deploy-driver-docker-compose.
