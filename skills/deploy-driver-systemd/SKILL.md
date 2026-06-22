---
name: deploy-driver-systemd
description: "WHEN: Deployment target is a Linux server managed by systemd. Functions: start(service_name), health_check(service_name), stop(service_name). Requires systemd unit files."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.1
preamble-tier: 3
triggers:
  - "deploy with systemd"
  - "systemd service deploy"
  - "register systemd service"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Deploy Driver: Systemd Services

Production deployment driver for systemd-managed services on Linux systems. Manages service lifecycle via systemctl, validates readiness through health checks, and enforces proper unit file configuration with strict error handling and version compatibility.

## HARD-GATE: Anti-Pattern Preambles

The following rationalizations **WILL BLOCK** your deployment. These are not edge cases—they are guaranteed failure modes that will surface in production.

## Iron Law

```
EVERY SYSTEMD SERVICE IS VERIFIED HEALTHY VIA HEALTH CHECK AFTER START. A SERVICE THAT IS "ACTIVE" IN SYSTEMD IS NOT A SERVICE THAT IS READY TO SERVE TRAFFIC.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`systemctl start` is called without a preceding `daemon-reload`** — Systemd will start the previously loaded unit file, ignoring the newly deployed one. STOP. Always run `systemctl daemon-reload` after writing a new or modified unit file and before calling `start()`.
- **Service is claimed healthy because `systemctl start` returned exit code 0** — A zero exit from `start` means systemd accepted the instruction, not that the service is running. STOP. Always follow `start` with `is-active` and application-level health check before declaring healthy.
- **Unit file contains directives not supported by the target systemd version** — Unsupported directives are silently ignored or cause load failure depending on systemd version. STOP. Run `systemd-analyze verify` against the actual unit file before deploying.
- **`stop()` is not called in cleanup after eval fails** — A running service from a failed eval run will conflict with the next run's port binding or state. STOP. Cleanup must call `stop()` unconditionally, regardless of eval outcome.
- **Deployment proceeds while system is in `degraded` state** — A degraded system has one or more failed units that may be dependencies of the service being deployed. STOP. `systemctl is-system-running` must return `running` (not `degraded`) before any deployment action.
- **Restart policy is absent from unit file for a critical service** — Without a `Restart=` directive, a crashed service stays down until manual intervention. STOP. All production services must have an explicit restart policy in their unit file.

### 1. "systemctl will always work if the unit file is valid"

**Why This Fails:**
- Unit file syntax valid ≠ systemd can load it. Systemd version mismatches, unsupported directives (e.g., `ExecStartPost` on systemd 219) cause load failures.
- Unit file in `/etc/systemd/system/` requires `daemon-reload` before systemd notices it. Deploying unit file, then immediately `systemctl start` fails with "unit not found" (reload not done).
- Systemd daemon may be in restart/reload state from concurrent operations. `systemctl` commands queue or timeout waiting for daemon to become ready.
- Unit dependencies not met (unit requires another unit that doesn't exist). `systemctl start` returns success but unit stays in "inactive" state pending dependencies.
- DBus connection needed for systemctl commands. DBus socket full or daemon unresponsive silently fails all systemctl calls.

**Enforcement:**
- MUST validate unit file syntax BEFORE deployment: `systemd-analyze verify /path/unit.service` (not just check file exists).
- MUST execute `systemctl daemon-reload` after unit file installation. Wait 500ms, verify it completes.
- MUST check systemd version at deploy time: `systemctl --version` must support all directives used in unit file. Reject if version too old.
- MUST verify unit dependencies exist before starting: `systemctl list-units --all | grep DEPENDENCY_UNIT` must succeed.
- MUST validate DBus connectivity before start(): `systemctl is-system-running` must return "running" (not "degraded" or "offline").

---

### 2. "Unit Restart policy is optional if the service is critical"

**Why This Fails:**
- Without `Restart=on-failure`, service crash leaves unit in "failed" state. Next systemctl status reports failure, but unit doesn't restart automatically.
- Restart policy `always` without `RestartSec` causes tight restart loop: service crashes at t=0s, restarts at t=0.1s, crashes at t=0.2s, 100 restarts/second.
- Restart limit (systemd default: max 5 restarts in 10s window) silently stops restarting after threshold. Service stops restarting but unit still marked "active" (misleading status).
- `Restart=on-failure` with exit code configuration `RestartForceExitStatus=0` causes infinite restart if application exits with code 0 (success). Restart policy inverted.
- No `StartLimitIntervalSec` means restart limit applies to service lifetime, not time window. One crash per week never hits restart limit (misleading "unlimited restarts").

**Enforcement:**
- MUST set explicit `Restart=on-failure` or `Restart=never` (no implicit defaults). If neither, unit will not auto-restart on crash.
- MUST set `RestartSec=5` minimum (no restarts faster than 5s). Never less than 2s unless specific reason (documented with justification).
- MUST understand restart limit: `StartLimitBurst=5` (max 5 restarts) within `StartLimitIntervalSec=10` (per 10 seconds). Document expected behavior if exceeded.
- MUST test restart behavior: manually kill process, verify systemctl status shows "active" and process restarted within 6-7 seconds.
- MUST configure `RestartForceExitStatus` only if explicitly needed (rare). Default behavior is: non-zero exit = restart, zero exit = no restart.

---

### 3. "Status checks are unnecessary; systemctl is-active is enough"

**Why This Fails:**
- `systemctl is-active SERVICE` returns "active" while unit is in "activating" state (still starting). Real-time window where unit appears active but is not.
- Status output depends on systemd version and locale (date format changes). Parsing `ActiveEnterTimestamp` fails on non-US locale or old systemd version (no timestamps).
- Service health ≠ systemd state. Unit can be "active" while actual process is hung, looping, or deadlocked. Systemd only tracks pid existence, not process behavior.
- Journalctl log parsing for error messages is locale-dependent. Error keywords differ between systemd versions (e.g., "failed" vs "errored" vs "abnormal termination").
- Uptime calculation depends on monotonic clock, not wall clock. If system clock skewed (NTP adjustment), uptime calculation wrong or negative.

**Enforcement:**
- MUST NOT rely solely on `systemctl is-active` for health. MUST perform application-level health check (HTTP GET to /health or similar).
- MUST validate timestamp parsing works on target systemd version: test `systemctl show -p ActiveEnterTimestamp SERVICE` output parsing in CI.
- MUST handle locale-aware timestamp parsing: test on LC_TIME=de_DE.UTF-8, en_US.UTF-8, etc. Use systemd-parseable format instead (JSON or key=value).
- MUST distinguish unit state vs. process health: healthy = (unit active) AND (process responds to health check) AND (no errors in journal).
- MUST use monotonic clock for uptime calculation if available (systemd 220+: `ActiveEnterTimestampMonotonic`). Fallback to wall clock with validation.

---

### 4. "Unit file syntax is forgiving; minor errors are caught at runtime"

**Why This Fails:**
- Typos in directives silently ignored: `ExecStrat=/bin/echo` (typo, missing 't') is not an error—systemd just ignores unknown directive. Unit starts but without the intended ExecStart.
- Quotes matter: `ExecStart=/bin/sh -c "echo hello"` requires proper escaping. Missing quotes causes systemd to parse as multiple arguments, breaking command.
- Environment variable expansion happens at parse time in some directives, at runtime in others. `ExecStart=/bin/echo $HOME` may fail (HOME not set) or succeed (depends on systemd version).
- Circular dependencies and conflicts allowed in unit file. Systemd detects cycle at load time but doesn't prevent deployment (just marks as broken, doesn't fail deploy).
- Unit file encoding matters: non-UTF8 files cause parse errors. Mixing tabs and spaces in some contexts fails (looks like formatting, is actually syntax error).

**Enforcement:**
- MUST validate unit file syntax before deployment using `systemd-analyze verify /path/unit.service`. This catches typos, quotes, and encoding issues.
- MUST check for circular dependencies: `systemd-analyze --unit SERVICE` must not show cycles.
- MUST test unit file loading explicitly: `systemctl cat SERVICE` (after daemon-reload) must show the unit you deployed.
- MUST NOT assume minor syntax errors are caught. Set strict validation: parse output of systemd-analyze and fail if warnings present.
- MUST test environment variable expansion: set expected env vars, start service, verify values used (check via systemctl show or process environment).

---

### 5. "Systemd handles all failure cases; just check status"

**Why This Fails:**
- Permission errors buried in unit file interpretation: user specified doesn't exist, working directory not accessible. `systemctl start` may succeed but service exits immediately (permission denied) or fails to start at all.
- DynamicUser=yes creates users on-the-fly, but race condition exists if multiple units with DynamicUser start simultaneously. One unit fails because username already claimed.
- Mounted filesystems not ready when unit starts: `After=local-fs.target` specifies dependency, but if NFS mount is slow, service starts before mount completes. ExecStart fails (path not found).
- Resource limits (memory, file descriptors, processes) enforced by cgroup. Service hits memory limit silently: process OOMed without systemd reporting OOM kill (must read cgroup events or kernel logs).
- Mask conflicts: if another tool masked the unit (systemctl mask), your deployment doesn't unmask it. Start fails with "unit is masked".

**Enforcement:**
- MUST check unit file User/Group before deployment: verify user exists or DynamicUser=yes is set. `id SPECIFIED_USER` must succeed (or systemd >= 235 for DynamicUser).
- MUST validate Working Directory: `test -d WORKING_DIR` must succeed before starting unit.
- MUST check if unit is masked: `systemctl is-enabled SERVICE` must not return "masked". Unmask if needed: `systemctl unmask SERVICE`.
- MUST verify dependent units/mount points are ready. For NFS mounts, use `After=network-online.target` and wait for network-online (not just network).
- MUST monitor resource limits post-start: check `systemctl status SERVICE` for cgroup limits, verify process memory < limit. Watch journal for OOMkill messages.

---

## Reference (load on demand)

The function/API catalog, edge cases, common pitfalls, decision trees, implementation
details, usage examples, and operational deep-dives live in **`reference/systemd-reference.md`**
(Agent Skills progressive disclosure). This SKILL.md is the operational contract:
dispatch, discipline (anti-pattern / iron law / red flags), and the deploy decision logic.

## Cross-References

This skill integrates with other Forge skills for complete deployment reasoning:

### Related Deploy Drivers
- **deploy-driver-pm2-ssh**: Deploy via PM2 over SSH on remote servers. Use when managing Node.js apps with PM2 across network.
- **deploy-driver-local-process**: Deploy local processes without systemd. Use for development or single-process deployments.
- **deploy-driver-docker-compose**: Deploy containerized services via Docker Compose. Use when apps run in containers.

### Health Check & Evaluation
- **eval-driver-api-http**: Evaluates HTTP-based health checks and endpoints. Use for defining and testing health endpoint contracts.
- **reasoning-as-infra**: Infrastructure reasoning for deployment targets, resource management, and lifecycle decisions.

### Multi-Service Coordination
- **eval-product-stack-up**: Brings up entire product stack for evaluation. Use when deploying services that depend on other services.
- **conductor-orchestrate**: Orchestrates complex multi-service deployments with dependency tracking.

### Decision Tracking & Auditability
- **brain-read**: Load product topology, service dependencies, and deployment history.
- **brain-write**: Record deployment decisions, post-mortems, and configuration rationale.

---

## Checklist

Before claiming deployment complete:

- [ ] systemd unit file exists and passes `systemd-analyze verify`
- [ ] `start()` completed without errors
- [ ] `health_check()` returned healthy response from application HTTP endpoint
- [ ] Application logs checked for startup errors (`journalctl -u <service>`)
- [ ] `stop()` called during cleanup (even on failure paths)
- [ ] No previous version of the service left running on the target port
