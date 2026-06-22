---
name: deploy-driver-pm2-ssh
description: "WHEN: Deployment target is a remote server managed via PM2 over SSH. Provides connect(ssh_config), start(project_path, script), health_check(port, endpoint), and stop(project_name)."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.1
preamble-tier: 3
triggers:
  - "deploy via PM2"
  - "PM2 SSH deploy"
  - "remote PM2 deployment"
allowed-tools:
  - Bash
  - Write
---

# Deploy Driver: PM2 over SSH

Deployment driver for PM2 over SSH on remote servers. Provides SSH connection management, process launching via PM2, HTTP-based health checks, and graceful shutdown via pkill.

## SSH Security Requirements (Non-Optional)

- Use key-based authentication only (no interactive password auth in automation flows).
- Enforce strict host verification (`StrictHostKeyChecking=yes`) with pre-populated `known_hosts`.
- Do not use agent forwarding unless explicitly required and documented for this task.
- Keep private keys permission-restricted (`chmod 600`) and outside repo paths.

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
- MUST verify schema version matches deployed code version after rollback. The standard pattern:
  1. Query schema version table (e.g., `SELECT version FROM schema_migrations ORDER BY run_at DESC LIMIT 1`) or run `db:migrate:status`.
  2. Compare to the expected version recorded in `deployment-manifest.json` for the target commit.
  3. If mismatch: DO NOT declare rollback complete. Run `db:migrate:down` to the target version, then re-check.
  4. Log result: `[ROLLBACK-VERIFY] schema_version=<actual> expected=<target> match=<true|false>`.

---

## Iron Law

```
EVERY PM2 SSH DEPLOYMENT VALIDATES SSH CONNECTIVITY WITH A NO-OP COMMAND, VERIFIES THE HOST KEY FINGERPRINT, CONFIRMS NO PRIOR VERSION IS RUNNING, STARTS THE PROCESS, AND FOLLOWS WITH A HEALTH CHECK. stop() IS CALLED IN ALL PATHS. CONFIDENCE THAT IT WORKED IS NOT A HEALTH CHECK.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **SSH connection is tested with `ping` or TCP port probe only** — A reachable host does not mean SSH is functional. Firewall rules can allow TCP but block the SSH daemon; a key mismatch will fail at authentication, not at connection. STOP. Test SSH by executing a no-op command (`echo ok`) over the connection before calling any deploy function.
- **PM2 process is claimed healthy because `pm2 start` exited 0** — PM2 start exit code reflects whether PM2 accepted the command, not whether the process is actually healthy. STOP. Always follow `start()` with `health_check()` against the application's HTTP health endpoint.
- **`stop()` is not called during cleanup when eval fails** — A process left running on the remote server will conflict with the next deployment's port binding or state. STOP. `stop()` must be called unconditionally in cleanup, not only on success paths.
- **SSH key fingerprint is not validated on first connect** — A changed host key (server reinstall, MitM) accepted silently means credentials may be sent to an unexpected host. STOP. Validate host key fingerprint against the known whitelist on every `connect()`.
- **Application logs are not retrieved after a failed health check** — When health check fails, the root cause is in the application logs on the remote server. Without fetching them, diagnosis is blind. STOP. On any health check failure, fetch and record the last 100 lines of the process log before reporting BLOCKED.
- **Deployment proceeds while a previous version's process is still running** — Two versions of the process running simultaneously can corrupt shared state (DB, cache, files). STOP. Always verify no previous process is running on the target port before `start()`.

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

## Reference (load on demand)

The function/API catalog, edge cases, common pitfalls, decision trees, implementation
details, usage examples, and operational deep-dives live in **`reference/pm2-ssh-reference.md`**
(Agent Skills progressive disclosure). This SKILL.md is the operational contract:
dispatch, discipline (anti-pattern / iron law / red flags), and the deploy decision logic.

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

## Checklist

Before declaring deployment complete:

- [ ] SSH connectivity validated with a no-op `echo ok` command before any deploy step
- [ ] Host key fingerprint validated against known whitelist on `connect()`
- [ ] No prior version running on target port (verified before `start()`)
- [ ] `start()` followed immediately by `health_check()` against application HTTP endpoint
- [ ] Application logs retrieved if health check fails
- [ ] `stop()` called unconditionally in cleanup (success and failure paths)
