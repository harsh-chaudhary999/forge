---
name: deploy-driver-local-process
description: "WHEN: Deployment target is a local process (any runtime — Node.js, Python, Go, Java, etc.). Provides start(project_path, script), health_check(port, endpoint), and stop(process_name)."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.1
preamble-tier: 3
triggers:
  - "deploy locally"
  - "start local process"
  - "run local deployment"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Deploy Driver for Local Process

## Anti-Pattern Preamble: Why Agents Skip health_check() After start()

| Rationalization | The Truth |
|---|---|
| "ps shows the process running, so it's ready" | Process in `ps` means the shell forked successfully. It does NOT mean the application bound its port or is accepting traffic. Always call `health_check()` after `start()`. |
| "health checks add latency — we'll skip them in quick eval cycles" | A skipped health check reports deployment success while the process is still initializing or has already crashed. Silent failures cost 10x more to debug. |
| "nohup guarantees the process stays up" | `nohup` detaches from terminal but does not guarantee execution. Missing env vars, wrong PATH, or write-permission failures cause silent exit after nohup returns. |
| "stop() can be skipped if the eval already failed" | A leaked process holds its port. The next `start()` call will fail with EADDRINUSE, causing a confusing failure that looks like a different bug. |
| "environment variables from the dev shell will be present" | CI/CD shells do not source `~/.bashrc` or `~/.profile`. Env vars that work locally are silently absent in CI. All required env vars must be set explicitly before `start()`. |
| "SIGTERM always terminates the process cleanly" | Processes can trap SIGTERM and ignore it, or be in uninterruptible sleep. SIGKILL must always be the fallback after a grace period. |

## Iron Law

```
EVERY local process MUST BE VERIFIED ALIVE VIA health_check() AGAINST ITS HTTP ENDPOINT BEFORE DECLARING DEPLOYMENT COMPLETE. A PROCESS APPEARING IN ps IS NOT SUFFICIENT.
```

Deploy and manage local processes via shell commands. Tracks process IDs, performs HTTP health checks, and gracefully terminates processes. Supports rapid deployment cycles with proper resource cleanup and health verification.

> **Runtime note:** Code examples below use Node.js (`npm run …`) as a concrete illustration. The underlying pattern — `nohup` + PID capture + `health_check()` poll + SIGTERM/SIGKILL cleanup — applies equally to Python (`uvicorn`, `gunicorn`), Go (`go run .`), Java (`java -jar`), Ruby (`bundle exec`), or any process that exposes an HTTP health endpoint. Substitute the start command for your runtime; everything else is identical.

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

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`start()` is called without verifying the port is free** — If another process is bound to the target port, `nohup` will succeed but the application will fail to bind and exit silently. STOP. Check port availability with `lsof -ti:<port>` before calling `start()`.
- **PID is captured from `$!` and not re-verified with `ps`** — On some systems `$!` returns the shell's job PID, not the actual application PID. STOP. Always confirm the correct PID via `ps aux | grep` after capture.
- **`health_check()` is skipped because `ps -p $PID` returned success** — Process running ≠ process ready. The application may be in initialization with the port bound but not yet serving requests. STOP. Always call `health_check()` after `start()`, never skip it.
- **`stop()` is not called when eval fails or scenario teardown runs** — A leaked process will hold the port across subsequent runs, causing the next `start()` to fail on port binding. STOP. `stop()` must be called in all teardown paths, success and failure.
- **Environment variables are inherited from the parent shell rather than set explicitly** — CI/CD environments do not have the same shell profile as a developer's local terminal. An env var that works locally will silently be absent in CI. STOP. All required environment variables must be explicitly set before `start()`.
- **Output logs from the process are not captured or linked in the eval report** — A process that silently fails or panics produces no assertion failure — the health check just times out. Without logs, diagnosis is blind. STOP. Always redirect stdout/stderr to a log file and link it in the scenario output.

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

## Reference (load on demand)

The function/API catalog, edge cases, common pitfalls, decision trees, implementation
details, usage examples, and operational deep-dives live in **`reference/local-process-reference.md`**
(Agent Skills progressive disclosure). This SKILL.md is the operational contract:
dispatch, discipline (anti-pattern / iron law / red flags), and the deploy decision logic.

## Cross-References

This skill interacts with:

- **eval-driver-api-http**: Health check implementation uses HTTP protocol and timeout patterns (see "Health Check Polling Strategy" in Decision Tree 1).
- **deploy-driver-pm2-ssh**: Similar patterns for graceful shutdown and health checks, but over SSH to remote servers. Compare anti-patterns (e.g., "SIGTERM always works" vs. "Timeouts are optional").
- **deploy-driver-docker-compose**: Container-based deployment; both use health checks and graceful shutdown. Compare port conflict resolution (containers have own port namespace).
- **reasoning-as-infra**: Resource management patterns (file descriptor limits, process quotas, timezone considerations) relate to Edge Case 4 and resource constraint section.
- **brain-read/brain-write**: Deployment decisions (rollback criteria, post-deployment monitoring) should be logged using brain-write for audit trail and later recall via brain-read.

---

## Checklist

Before claiming completion:

- [ ] Port availability verified with `lsof` before `start()` — no silent bind failures
- [ ] All required environment variables set explicitly before `start()` — no shell inheritance assumed
- [ ] `health_check()` called after `start()` and returned HTTP 200 — not just ps success
- [ ] Process stdout/stderr redirected to a log file and path recorded in scenario output
- [ ] `stop()` called unconditionally in teardown — both success and failure paths covered
- [ ] No zombie processes remain after `stop()` — verified with `ps aux` check
- [ ] Process PID verified via `ps` after capture from `$!` — not relying on shell job PID alone
