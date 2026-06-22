---
name: deploy-driver-docker-compose
description: "WHEN: Deployment target is Docker Compose. Provides up(compose_file), health_check(), and down() for multi-service orchestration."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.1
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

## Reference (load on demand)

The function/API catalog, edge cases, common pitfalls, decision trees, implementation
details, usage examples, and operational deep-dives live in **`reference/docker-compose-reference.md`**
(Agent Skills progressive disclosure). This SKILL.md is the operational contract:
dispatch, discipline (anti-pattern / iron law / red flags), and the deploy decision logic.

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
- **qa-semantic-csv-orchestrate** — Multi-service eval coordination via **`qa/semantic-automation.csv`** (for testing entire stacks)

### Related Brain Documents
- **brain-read** - Product topology and project metadata (for understanding service dependencies)
- **brain-write** - Recording deployment decisions (log successful deployments, failure patterns)
- **brain-recall** - Accessing deployment learnings and failure history (for diagnosis and prevention)

---

## Checklist

Before claiming completion:

- [ ] `up()` called with explicit compose file path — no default file assumed
- [ ] `health_check()` called for every service after `up()` — not skipped for "simple" stacks
- [ ] Health check verified service readiness via HTTP endpoint, not just container state
- [ ] Container restart count monitored for first 30 seconds — no silent crash loops
- [ ] `down()` called with `-v` flag — named volumes removed, no stale state persists
- [ ] All services confirmed healthy before deployment success reported
- [ ] Log output captured from failed health checks — diagnosis not blind
