---
name: deploy-driver-systemd
description: "WHEN: Deployment target is a Linux server managed by systemd. Functions: start(service_name), health_check(service_name), stop(service_name). Requires systemd unit files."
type: rigid
requires: [brain-read, eval-driver-api-http]
version: 1.0.0
preamble-tier: 3
triggers: []
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

## Architecture

```
┌──────────────────────────────────────────────────────┐
│         Deploy Driver Systemd                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────┐  ┌──────────────────┐           │
│  │ Unit File      │  │ Systemctl Cmd    │           │
│  │ Validation     │  │ Execution        │           │
│  └────────────────┘  └──────────────────┘           │
│         │                   │                        │
│         └───────┬───────────┘                        │
│                 ▼                                     │
│  ┌──────────────────────────────────┐               │
│  │  Systemd Service Lifecycle       │               │
│  │  • daemon-reload                 │               │
│  │  • systemctl start/stop/status   │               │
│  │  • dependency verification       │               │
│  └──────────────────────────────────┘               │
│         │                                            │
│         ├─► [Start] Load unit, verify active       │
│         ├─► [Health] Check service + health        │
│         │                endpoint                   │
│         └─► [Stop] Stop unit, verify inactive      │
│                                                      │
│  ┌──────────────────────────────────┐               │
│  │  Version & Compatibility Check   │               │
│  │  • systemd version validation    │               │
│  │  • Directive support check       │               │
│  │  • Locale handling               │               │
│  └──────────────────────────────────┘               │
│                                                      │
│  ┌──────────────────────────────────┐               │
│  │  Status Parsing & Journal        │               │
│  │  • State extraction              │               │
│  │  • Timestamp parsing             │               │
│  │  • Error log analysis            │               │
│  └──────────────────────────────────┘               │
└──────────────────────────────────────────────────────┘
```

## Overview

This skill provides reliable service management for production deployments on systemd-enabled Linux systems. It handles:

- **Service startup** with verification of active state and health checks
- **Health checks** with status parsing, uptime calculation, and application-level verification
- **Service shutdown** with verification of inactive state
- **Error handling** for missing units, permission issues, version mismatches, and service failures
- **Unit file validation** ensuring correct syntax and configuration before deployment
- **Version compatibility** checking for systemd feature support

## Prerequisites

- Linux system with systemd version 220+ (released 2015)
- Systemd unit files properly configured and validated
- Sufficient permissions to manage services (typically requires sudo or capabilities)
- Service unit must be enabled: `systemctl enable {service_name}`
- DBus daemon must be running and responsive
- Application-level health endpoint (recommended for verification)

## Function Signatures

### start(service_name) → Promise<{status: string, unit_loaded: boolean, active_time_ms: number}>

Start a systemd service and verify it reaches active state with application readiness verification.

**Parameters:**
- `service_name` (string, required): Name of the systemd service unit (without .service extension)
- `options?` (object):
  - `timeout_ms?: number` - Maximum time to wait for service activation (default: 30000)
  - `health_check_config?` - Optional HTTP health endpoint config for app-level verification
  - `systemd_version_check?: boolean` - Validate systemd version before start (default: true)

**Execution Steps:**
1. Validate systemd version: `systemctl --version` must support directives in unit file
2. Verify unit file loaded: `systemctl cat {service_name}` must succeed
3. Check DBus connectivity: `systemctl is-system-running` must return "running"
4. Check dependencies: `systemctl list-dependencies {service_name} --reverse` all active or met
5. Execute `systemctl daemon-reload` to load any updated unit files
6. Execute `systemctl start {service_name}`
7. Poll `systemctl is-active {service_name}` with exponential backoff (100ms, 200ms, 400ms, 800ms)
8. Verify no restart loops: `systemctl show -p NRestarts {service_name}` must be 0-1
9. Optional: Perform HTTP health check if config provided
10. Return success with metrics

**Returns:**
```javascript
{
  status: "active",
  unit_loaded: true,
  active_time_ms: 1234,
  main_pid: 12345,
  timestamp: 1649234567890
}
```

**Error Cases:**
- Unit not found: "Unit {service_name}.service not found"
- Version incompatible: "Systemd version does not support required directives (need 220+, have 219)"
- DBus unavailable: "DBus connection failed; systemd daemon may be unresponsive"
- Dependency failed: "Unit {dependency} failed to activate; cannot proceed"
- Permission denied: "Insufficient permissions to start {service_name} (requires root or systemd-run)"
- Restart loop: "Service entered restart loop after {N} restarts (likely configuration error)"
- Timeout: "Service did not reach active state within {timeout_ms}ms"
- Health check failed: "Service active but health check failed (app not responding)"

**Example:**
```javascript
const result = await start('backend-api', {
  timeout_ms: 30000,
  health_check_config: { port: 3000, endpoint: '/health', timeout_ms: 5000 }
});
// result = { status: "active", unit_loaded: true, active_time_ms: 2500, main_pid: 12345 }
```

---

### health_check(service_name, options?) → Promise<{healthy: boolean, status: string, uptime_seconds: number, main_pid?: number, latency_ms?: number}>

Check service health via systemd status and optional HTTP health endpoint verification.

**Parameters:**
- `service_name` (string, required): Name of the systemd service unit (without .service extension)
- `options?` (object):
  - `include_http_check?: boolean` - Also perform HTTP health check (default: false)
  - `http_config?` - HTTP endpoint config: `{port, endpoint, timeout_ms}`
  - `allow_activating?: boolean` - Consider "activating" state as healthy (default: false)

**Execution Steps:**
1. Execute `systemctl is-active {service_name}` to get current state
2. Execute `systemctl show -p ActiveEnterTimestampMonotonic,NRestarts,MainPID {service_name}`
3. Parse monotonic timestamp (systemd 220+) or fallback to wall-clock timestamp (older versions)
4. Calculate uptime: current_monotonic_time - ActiveEnterTimestampMonotonic
5. Check restart count: if NRestarts > 0, service has crashed and restarted
6. Optional: Perform HTTP GET to health endpoint if config provided (with exponential backoff)
7. Classify health: (status == active) AND (http_healthy OR no_http_check) AND (latency acceptable)
8. Return structured health data

**Returns:**
```javascript
{
  healthy: true,
  status: "active",
  uptime_seconds: 3600,
  main_pid: 12345,
  restart_count: 0,
  latency_ms: 25,  // Only if HTTP check performed
  timestamp: 1649234567890
}
```

**Status Values:**
- `active` - Service is running and has met all conditions
- `inactive` - Service is stopped (not running)
- `failed` - Service crashed or failed to start (will not auto-restart)
- `activating` - Service is starting up (may not be ready for traffic)
- `deactivating` - Service is shutting down
- `reloading` - Service is reloading configuration

**Health Classification:**
- **Healthy**: status == "active" AND (no HTTP check OR HTTP check passes) AND latency acceptable
- **Unhealthy**: status != "active" OR HTTP returns non-200 OR latency spike > 3x baseline OR restart_count > 0
- **Degraded**: status == "active" but latency spike indicates load/issue

**Error Cases:**
- Unit not found: Throws "Unit {service_name}.service not found"
- Timestamp parse error: Returns {healthy: false, status: "unknown", uptime_seconds: 0}
- HTTP check timeout: Returns {healthy: false, status: "active", issue: "health_endpoint_timeout"}
- Locale issue on timestamp: Uses fallback parsing or systemd-parseable format

**Example:**
```javascript
const health = await health_check('backend-api', {
  include_http_check: true,
  http_config: { port: 3000, endpoint: '/health', timeout_ms: 5000 }
});
// health = { healthy: true, status: "active", uptime_seconds: 3600, latency_ms: 25 }
```

---

### stop(service_name, options?) → Promise<{status: string, stopped_at_seconds: number, force_used?: boolean}>

Stop a running systemd service and verify it reaches inactive state.

**Parameters:**
- `service_name` (string, required): Name of the systemd service unit (without .service extension)
- `options?` (object):
  - `timeout_ms?: number` - Max time to wait for graceful stop (default: 30000)
  - `force_after_timeout?: boolean` - Force-kill with KillMode=control-group if timeout exceeded (default: true)
  - `check_journal?: boolean` - Verify no error messages in journal post-stop (default: true)

**Execution Steps:**
1. Check current service status: `systemctl is-active {service_name}`
2. If already inactive, return immediately
3. Execute `systemctl stop {service_name}` to initiate graceful shutdown
4. Poll `systemctl is-active {service_name}` with exponential backoff until timeout
5. If timeout and force_after_timeout=true: execute `systemctl kill -s SIGKILL {service_name}`
6. Wait for KillMode timeout (typically 30s) and re-poll
7. Optional: Check journal for errors: `journalctl -u {service_name} -n 20 --pager=off | grep -i error`
8. Return final status with metrics

**Returns:**
```javascript
{
  status: "inactive",
  stopped_at_seconds: 1234,
  duration_ms: 2500,
  force_used: false,
  timestamp: 1649234567890
}
```

**Error Cases:**
- Unit not found: "Unit {service_name}.service not found"
- Permission denied: "Insufficient permissions to stop {service_name}"
- Stop timeout (force_after_timeout=false): "Service did not stop gracefully within {timeout_ms}ms"
- Force-kill timeout: "Service did not respond to SIGKILL; may be in uninterruptible sleep state"
- Post-stop journal errors: Returns success but includes error_messages array with journal entries

**Example:**
```javascript
const result = await stop('backend-api', {
  timeout_ms: 30000,
  force_after_timeout: true,
  check_journal: true
});
// result = { status: "inactive", stopped_at_seconds: 1234, duration_ms: 2500, force_used: false }
```

---

## Edge Cases with Mitigation

Production scenarios requiring specific detection and recovery logic.

### Edge Case 1: Unit File Syntax Error Not Caught Until Runtime

**Scenario:**
Your deployment includes a new unit file with typo: `ExecStrat=/bin/false` (missing 't'). The typo is silently ignored by systemd (unknown directive). You execute `daemon-reload` (succeeds), then `systemctl start service` (succeeds because systemd loaded the unit). But the service has no ExecStart directive (the typo'd one was ignored), so systemd starts the service but immediately exits with "no executable specified". Service goes to "inactive" state immediately. Health check times out. You've reported deployment failure for a syntax error that wasn't caught.

**How to Detect:**
- `systemd-analyze verify /path/unit.service` fails with detailed error messages about typos
- `systemctl show -p ExecStart SERVICE` returns empty or default value (no command set)
- `systemctl start` succeeds but immediately transitions to "inactive" (no ExecStart)
- Journal contains "no executable specified" or similar

**What Happens:**
- Deployment fails silently: unit loads but has no command.
- Error message vague: "service did not reach active state" (actual cause: no ExecStart).
- Cascades on all deployments using this unit file until fixed.

**Mitigation Steps:**
1. Detect: Before deployment, run `systemd-analyze verify /path/unit.service`. MUST pass with no errors or warnings.
2. Escalate: If verify fails, reject deployment immediately. Include output in error message.
3. Recovery: Review unit file for typos, unknown directives, or missing required fields (ExecStart, Type, etc.).
4. Prevention: In CI/CD, validate all unit files before deploying them: `systemd-analyze verify` must exit 0.

---

### Edge Case 2: Service Restart Loop (Crash Count > 2 in 30 Seconds)

**Scenario:**
Your service specifies `Restart=on-failure` with `RestartSec=1`. The service starts, but crashes immediately due to missing environment variable. Systemd restarts it at t=1s (crash 1), t=2s (crash 2), t=3s (crash 3), etc. After 5 crashes in 10 seconds, systemd hits the restart limit (default: StartLimitBurst=5 per StartLimitIntervalSec=10s) and stops auto-restarting. Unit stays in "active" state but process is stopped. Your health check at t=15s polls, gets no response, retries, and eventually times out. You assume network issue and retry deployment. By t=30s, the restart limit resets, systemd auto-restarts the service again (but it crashes again). Cycle repeats.

**How to Detect:**
- `systemctl show -p NRestarts SERVICE` > 2 immediately after start
- `systemctl show -p StateChangeTimestamp SERVICE` shows very recent (< 5s) state changes
- Journal shows repeated crash messages: "process crashed", "signal 11", "exit code 1", etc. in quick succession
- `systemctl is-active SERVICE` returns "active" but `ps aux | grep SERVICE_PID` shows no process

**What Happens:**
- Service crashes repeatedly, restart loop enters.
- After restart limit hit, service stops restarting but unit stays "active" (misleading).
- Health check fails due to no process running.
- Operator reruns deployment thinking it's a network issue, but root cause (missing env var, bad config) never addressed.

**Mitigation Steps:**
1. Detect: After start(), immediately run `systemctl show -p NRestarts SERVICE`. If > 1, potential crash loop.
2. Escalate: Do NOT proceed if NRestarts > 1. Log severity ERROR and include tail of journal:
   ```bash
   journalctl -u SERVICE -n 50 --pager=off | grep -E "crash|signal|exit"
   ```
3. Recovery: Operator reviews error logs and fixes root cause (missing env var, bad config file, missing dependency).
4. Prevention: In pre-deployment validation, run unit file through `systemd-analyze condition` to check if any conditions fail. Test service startup in isolation before deploying.

---

### Edge Case 3: Timestamp Parsing Fails on Non-US Locale

**Scenario:**
You deploy to a system with LC_TIME=de_DE.UTF-8 (German locale). Health check calls `systemctl show -p ActiveEnterTimestamp SERVICE`, which returns:
```
ActiveEnterTimestamp=Mi 2026-04-10 14:30:45 UTC
```
(Note: "Mi" is Wednesday in German). Your timestamp parser expects English day names (Mon, Tue, Wed, etc.) and fails to parse. Uptime calculation fails. Health check returns `{healthy: false, status: "unknown", uptime_seconds: 0}`. You assume service is broken and rollback. Actually, service is fine, just locale parsing failed.

**How to Detect:**
- Timestamp parsing throws exception or returns invalid date
- Health check returns `status: "unknown"` or `uptime_seconds: 0` despite service being active
- `systemctl show -p ActiveEnterTimestamp SERVICE` output contains non-English text (day names in other languages)
- Different parsing results depending on system locale

**What Happens:**
- Health check fails on non-US locales despite service being healthy.
- Deployment fails intermittently depending on system locale.
- Rollback triggered unnecessarily.
- Cascades if deployment environment has varied locales (CI/CD runners in different regions).

**Mitigation Steps:**
1. Detect: Use systemd-parseable format instead of human-readable timestamps. Request `systemctl show -p ActiveEnterTimestampMonotonic SERVICE` (monotonic timestamp, locale-independent, systemd 220+).
2. Escalate: If monotonic timestamp unavailable (old systemd), fallback to parsing but use ISO8601 format: force locale to C via `LC_TIME=C systemctl show ...`.
3. Recovery: Explicitly set locale: `LC_TIME=C` before systemctl commands.
4. Prevention: Always use monotonic timestamps (systemd 220+) or ISO8601 format. Never rely on human-readable day names for parsing.

---

### Edge Case 4: Unit Masked After Deployment (Masked Conflicts with Start)

**Scenario:**
Another team manually masked your service using `systemctl mask service-name` to prevent it from starting during system startup (due to transient issue). Your deployment doesn't check if service is masked. You execute `systemctl start service-name`, which succeeds at the systemctl API level (command returns 0), but the actual start is blocked by the mask. Service remains stopped. Your `systemctl is-active` polling times out. Deployment fails. But the root cause is masked unit, not your code or configuration. You spent debugging time before discovering the mask.

**How to Detect:**
- `systemctl is-enabled SERVICE` returns "masked" (not "enabled" or "disabled")
- `systemctl start SERVICE` succeeds (returns 0) but service doesn't start
- `ls -la /etc/systemd/system/SERVICE.service` shows symlink pointing to `/dev/null` (mask indicator)
- Journal shows "unit is masked" or similar message

**What Happens:**
- Start command succeeds but service doesn't actually start (blocking behavior).
- Deployment times out waiting for service to become active.
- Operator confused: systemctl says "succeeded" but service not running.
- Recovery requires unmask: `systemctl unmask SERVICE`, then retry.

**Mitigation Steps:**
1. Detect: Before start(), check: `systemctl is-enabled SERVICE` must NOT return "masked".
2. Escalate: If masked, refuse to proceed. Include message: "Unit is masked. Run `systemctl unmask SERVICE_NAME` to proceed."
3. Recovery: Operator unmasks unit and retries deployment.
4. Prevention: In pre-flight checks, validate unit is not masked. Document why masking would block deployment.

---

### Edge Case 5: Journal Log Rotation Causes Log Loss and Disk Full

**Scenario:**
Your service is very chatty: logs 1000 lines/second. Journalctl log retention is set to 100MB max (default: /var/log/journal/ grows unbounded). After 1 day of uptime, journals consume 50GB of disk. New deployments fail during start because systemd cannot write logs (disk full). You see error: "systemctl start failed: device or resource busy" (vague, doesn't indicate disk full). You retry (fails again). You check disk space and discover 100% full. You manually delete old journals, free space, and retry. By then, service has been down for 30 minutes.

**How to Detect:**
- `df /var/log/journal` or `df /` shows usage > 90%
- `journalctl --disk-usage` shows large size (multiple GBs)
- `systemctl start SERVICE` fails with "device or resource busy" or "no space left on device"
- System performance degraded (slow I/O due to journal writes)

**What Happens:**
- Deployment fails due to disk full, not deployment configuration.
- Service unavailable until disk is manually cleaned.
- If multiple services run on same host, all fail simultaneously (cascading failure).
- Production outage lasting 30+ minutes (time to detect + time to fix + time to redeploy).

**Mitigation Steps:**
1. Detect: Before start(), check disk space: `df /var/log/journal | awk 'NR==2 {print $5}' | sed 's/%//'` must be < 80%.
2. Escalate: If disk usage > 80%, refuse deployment. Require manual cleanup before retry.
3. Recovery: Operator runs `journalctl --vacuum-size=500M` to clean old journals, freeing space.
4. Prevention: Configure journal rotation in `/etc/systemd/journald.conf`:
   ```ini
   SystemMaxUse=1G
   RuntimeMaxUse=500M
   MaxFileSec=1week
   ```
   Test in CI/CD with simulated heavy logging to validate rotation works.

---

### Edge Case 6: Dependent Unit Not Started or Failed

**Scenario:**
Your service specifies `After=mysql.service` (waits for MySQL to start first). MySQL unit fails to start due to data corruption (corrupted InnoDB files). Your service's start command succeeds (unit loads), but service doesn't actually start because dependency is not met. Systemd marks your service as "active (waiting)" or "inactive (dead)" depending on version. Your health check polls and gets "inactive", deployment fails. But actual issue is MySQL failure, not your service code. You waste debugging time before realizing dependency failure.

**How to Detect:**
- `systemctl list-dependencies SERVICE --reverse` shows dependent units with "inactive (dead)" status
- `systemctl is-active DEPENDENCY_UNIT` returns "failed" or "inactive"
- `systemctl start SERVICE` succeeds but service doesn't reach "active" state
- Journal shows "dependency not satisfied" or "condition failed" messages

**What Happens:**
- Service blocked from starting due to dependency failure.
- Deployment fails with unclear error message (looks like service issue, is dependency issue).
- Requires investigating dependent units to find root cause.

**Mitigation Steps:**
1. Detect: Before start(), verify all dependent units: `systemctl list-dependencies SERVICE | grep -E "Requires|After"` and validate each is "active" or "loaded".
2. Escalate: If any dependency is not "active", refuse to proceed. Include dependency status in error message.
3. Recovery: Operator starts dependent units first, fixes any issues (e.g., MySQL corruption), then retries your service.
4. Prevention: Document service dependencies in deployment documentation. In CI/CD, start dependent services first, validate they're active, then start your service.

---

### Edge Case 7: Graceful Shutdown Timeout Too Short (Lost Connections)

**Scenario:**
Your service has `TimeoutStopSec=5` (5 seconds to gracefully shutdown). Service receives SIGTERM but needs 15 seconds to flush in-flight requests, commit pending transactions, close DB connections gracefully. After 5 seconds, systemd force-kills the process (SIGKILL) without waiting. In-flight requests are dropped, clients receive connection resets. Transactions are rolled back (uncommitted writes lost). From a systems perspective, deployment "succeeded" (service stopped cleanly via systemctl). From application perspective, data loss occurred.

**How to Detect:**
- Service logs show truncated shutdown: "received SIGTERM" but no "graceful shutdown complete" message
- `systemctl show -p TimeoutStopUSec SERVICE` is much less than actual shutdown time needed
- Application logs show connection resets or transaction rollbacks at shutdown time
- Post-deployment data loss or inconsistencies reported by users

**What Happens:**
- Service stops but not gracefully: in-flight work lost.
- Appears as deployment success, but causes data loss.
- May not be detected until post-deployment testing (integration tests fail due to lost data).

**Mitigation Steps:**
1. Detect: Measure actual graceful shutdown time: start service, send SIGTERM, measure time until exit. Should see "graceful shutdown complete" log message.
2. Escalate: Set `TimeoutStopSec` to 2x measured shutdown time (capped at 60s). If service needs > 60s, escalate to architecture review (consider split into multiple smaller services).
3. Recovery: Update unit file with appropriate TimeoutStopSec, redeploy.
4. Prevention: Document service shutdown time. In integration tests, verify graceful shutdown leaves no orphaned connections or pending transactions. Test restart cycles: stop -> verify clean -> start -> repeat.

---

## Common Pitfalls

Pitfalls that surface repeatedly in systemd deployments.

### Pitfall 1: Unit File Changes Not Reflected After Deployment

**The Problem:**
You update a unit file (e.g., change ExecStart command or environment variables). You copy the updated file to `/etc/systemd/system/SERVICE.service`. You deploy and start the service, but the service runs using the *old* command. The updated unit file was deployed but systemd daemon hasn't reloaded it. You forgot to run `systemctl daemon-reload` after updating the file.

**Why It Happens:**
- Systemd caches unit files in memory. File changes on disk don't automatically refresh.
- `daemon-reload` must be explicitly run after any unit file changes.
- No warning or error if you skip daemon-reload; service just uses old cached version.

**Prevention:**
- Always run `systemctl daemon-reload` immediately after updating unit files.
- Verify unit file change took effect: `systemctl cat SERVICE | diff - /path/unit.service` (should be identical).
- Test in non-production environment first: update file, daemon-reload, start service, verify new behavior.

---

### Pitfall 2: Environment Variable Expansion Timing Mismatch

**The Problem:**
Your unit file includes `Environment=PORT=8000` and `ExecStart=/bin/echo $PORT`. On systemd 220+, environment variables are expanded at parse time. On systemd 219, they're expanded at execution time. Behavior differs:
- systemd 220+: "$PORT" expands to "8000" at load time, ExecStart becomes `/bin/echo 8000`
- systemd 219: "$PORT" stays as literal "$PORT" at load time, ExecStart runs `/bin/echo $PORT` which outputs empty string

Unit file works on one version, fails on another.

**Why It Happens:**
- Systemd behavior changed across versions (220 was major update with breaking changes).
- Documentation doesn't clearly indicate expansion timing.
- Environment setup assumes same behavior across all supported versions.

**Prevention:**
- Check systemd version before deployment: `systemctl --version` must be 220+ (or document required minimum).
- Avoid "$VAR" syntax in ExecStart. Use EnvironmentFile instead: `EnvironmentFile=/etc/default/SERVICE` for external vars.
- Test unit file on target systemd version before deploying.
- Use explicit version checks in deployment: fail if systemd version < 220 and unit file uses env var expansion.

---

### Pitfall 3: Status Check Race Condition (Service Transitioning)

**The Problem:**
You start a service and immediately (t=100ms) poll `systemctl is-active SERVICE`. Service is still transitioning from "inactive" → "activating" → "active". Poll returns "activating" (not yet "active"). You interpret this as failure and rollback. Actually, service is still starting. By t=500ms, it would have been fully active. Race between polling and service transition window.

**Why It Happens:**
- Service startup is asynchronous. Systemd marks unit "activating" immediately, then waits for process to initialize.
- No built-in wait for fully active state (depends on Type field: simple, forking, notify, oneshot).
- Health check polling interval too fast: checks before service finished starting.

**Prevention:**
- Understand systemd Type field:
  - `Type=simple`: service transitions "active" immediately, PID tracking starts. Don't check status too early.
  - `Type=forking`: service spawns child, parent exits. Systemd waits for parent exit before marking active.
  - `Type=oneshot`: service runs once and exits. Systemd marks active while process runs, then inactive when done.
  - `Type=notify`: service sends READY=1 signal. Systemd waits for signal before marking active.
- Match health check polling strategy to Type: for simple/forking, wait 500ms before first poll. For oneshot, don't poll (use different strategy).
- Log service state transitions: `systemctl status SERVICE` should show clear transition path: `loaded → active (running)`.

---

### Pitfall 4: Permission Issues Hidden Behind Confusing Error Messages

**The Problem:**
Your unit file specifies `User=appuser` but user "appuser" doesn't exist on the system. `systemctl start SERVICE` returns "started" but service exits immediately with permission error (can't change to non-existent user). You run `systemctl status SERVICE` and see "active (exited)" (unit thinks it started, process exited). Journal shows "cannot access /home/appuser: no such file or directory" buried in logs. Root cause: user doesn't exist. Error message doesn't clearly indicate this.

**Why It Happens:**
- Systemd doesn't validate User field before starting (defers to service process).
- Service process (if it runs at all) encounters user error and exits.
- Systemd marks "active (exited)" which looks like success (confusing).

**Prevention:**
- Before deployment, validate User/Group exist: `id appuser` or `getent passwd appuser` must succeed.
- Validate Working Directory is accessible by the user: `su - appuser -c "test -x WORKING_DIR"`.
- Check unit file for permission requirements: read unit, identify all paths (ExecStart, WorkingDirectory, etc.), verify user can access.
- In test deployment, check post-start logs: `journalctl -u SERVICE -n 20` should show no permission errors.

---

### Pitfall 5: Restart Loop Due to Bad Configuration

**The Problem:**
Your unit file specifies `Restart=on-failure` without `RestartSec`. Service crashes immediately due to bad config. Systemd restarts infinitely (tight loop, no delay). CPU usage spikes from constant restarts. System becomes sluggish. Operator notices high CPU and kills the service manually. Root cause: bad config, not infrastructure.

**Why It Happens:**
- `Restart=on-failure` without RestartSec has no delay between restarts (systemd 219 behavior; later versions default to 100ms).
- Configuration error causes immediate crash, restart loop enters.
- No escalation mechanism to stop the loop after N restarts.

**Prevention:**
- Always set explicit `RestartSec=5` minimum (never 0 or implicit).
- Monitor restart counts: if `NRestarts > 2` in quick succession, escalate and refuse to proceed.
- Document expected behavior: "If service restarts > 5 times in 30s, likely config error. Check unit file and application startup logs."
- In integration tests, start service with intentionally bad config, verify it crashes, verify restart loop is detected and logged.

---

## Decision Trees and Patterns

### Decision Tree 1: Service Type Selection (Simple vs. Forking vs. Oneshot vs. Notify)

```
START: Choose systemd Type for your service
│
├─ Does your service fork children and exit parent process?
│  ├─ YES: Use Type=forking
│  │   └─ Parent spawns child, parent exits. Systemd waits for parent exit, then tracks child PID.
│  │   └─ Example: traditional daemons (syslog, nginx background start)
│  │   └─ Must set PIDFile= to locate child PID (systemd will track this PID)
│  │   └─ Gotcha: If parent doesn't exit, systemd waits forever. Configure TimeoutStartSec.
│  │
│  └─ NO: Proceed to next decision
│
├─ Does your service run once and exit (batch/one-time job)?
│  ├─ YES: Use Type=oneshot
│  │   └─ Service runs to completion and exits. Systemd stays "active" while running, "inactive" when done.
│  │   └─ Example: backup scripts, log rotation, cache warming
│  │   └─ Set RemainAfterExit=yes if you want "active" even after process exits (useful for state verification)
│  │   └─ Gotcha: Oneshot services exiting normally marks unit "inactive", not "failed". Success ≠ failure to systemd.
│  │
│  └─ NO: Proceed to next decision
│
├─ Does your service send READY=1 notification signal?
│  ├─ YES: Use Type=notify
│  │   └─ Service tells systemd when it's ready. Systemd waits for signal before marking "active".
│  │   └─ Example: services using systemd-notify library, modern frameworks (some Python, Go)
│  │   └─ Allows precise tracking of when service is truly ready (not just PID spawned).
│  │   └─ Gotcha: If service crashes before sending signal, systemd waits until timeout, then fails. Set TimeoutStartSec appropriately.
│  │   └─ Gotcha: Service must include READY=1 signal; if missing, service will timeout and fail to start.
│  │
│  └─ NO: Proceed to next decision
│
├─ Does your service run in foreground and never fork?
│  ├─ YES: Use Type=simple (default)
│  │   └─ Service runs in foreground. Systemd marks "active" immediately (process tracking only).
│  │   └─ Example: Node.js apps, Docker containers, modern stateless services
│  │   └─ Fastest startup: no waiting for signals or parent exit.
│  │   └─ Gotcha: Service can appear "active" while still initializing (no notification). Health checks needed.
│  │
│  └─ Unclear: Consult service documentation for startup behavior
│
└─ END: Use selected Type
```

**Implementation Guidance:**
- Default to Type=simple unless service explicitly documents it forks or sends notifications.
- For forking services, PIDFile is mandatory: systemd must know which PID to track.
- For oneshot, pair with RemainAfterExit=yes if subsequent services depend on it (marks "active" after completion).
- For notify, verify service is built with systemd notify support. Test with `systemd-notify --ready` to verify notification works.

---

### Decision Tree 2: Restart Policy (Never vs. Always vs. On-Failure)

```
START: Decide Restart policy
│
├─ Is service critical (must never stop)?
│  ├─ YES: Use Restart=always
│  │   └─ Systemd restarts immediately on ANY exit (success or failure).
│  │   └─ Set RestartSec=5 minimum (wait 5s between restarts).
│  │   └─ Example: mission-critical daemons (system logger, init replacement)
│  │   └─ Gotcha: Crash loop will spam restarts. Monitor NRestarts and logs.
│  │
│  └─ NO: Proceed to next decision
│
├─ Should service restart only if it crashed (non-zero exit)?
│  ├─ YES: Use Restart=on-failure
│  │   └─ Restarts on non-zero exit code, not on success (0).
│  │   └─ Set RestartSec=5 minimum.
│  │   └─ Example: most application services (API servers, workers)
│  │   └─ Gotcha: What counts as "failure"? SIGTERM counts as failure (exit code 143). Configure RestartForceExitStatus.
│  │   └─ Gotcha: Need to define "failure" explicitly: RestartForceExitStatus=0 inverts logic (restart on success).
│  │
│  └─ NO: Proceed to next decision
│
├─ Should service NEVER auto-restart (manual only)?
│  ├─ YES: Use Restart=no
│  │   └─ Service exits and stays exited. Manual `systemctl start` needed to restart.
│  │   └─ Example: one-time initialization, batch jobs, services requiring manual orchestration
│  │   └─ Gotcha: Without auto-restart, failed service requires manual intervention. Acceptable only for non-critical services.
│  │
│  └─ Unclear: Default to Restart=on-failure (safest choice for typical services)
│
├─ Configure restart limits (prevent infinite loops):
│  └─ Set StartLimitBurst=5 (max 5 restarts)
│  └─ Set StartLimitIntervalSec=10 (within 10 seconds)
│  └─ Action when limit hit: set StartLimitAction=reboot (drastic) or StartLimitAction=poweroff (safer, requires manual intervention)
│
└─ END: Use selected Restart policy
```

**Implementation Guidance:**
- Most production services should use `Restart=on-failure` with explicit RestartSec (e.g., 5s).
- Monitor StartLimitBurst: if hit repeatedly, service has fundamental issue, requires investigation.
- Test restart behavior: manually kill service PID, verify it restarts, verify delay between restarts.
- Document restart policy in deployment notes: "This service will restart automatically if it crashes."

---

### Decision Tree 3: Health Check Strategy (Systemd Status vs. HTTP Check)

```
START: Decide health check strategy
│
├─ Is HTTP health endpoint available?
│  ├─ YES: Check application-level health first
│  │   └─ Perform HTTP GET to /health (or custom endpoint)
│  │   └─ Verify response is 200 OK and body is valid
│  │   └─ This is most accurate: proves app is responding
│  │   └─ Set timeout appropriately for app startup time (e.g., 5s for Node.js, 15s for Java)
│  │   └─ Gotcha: HTTP check has latency; slow network can timeout despite service being healthy
│  │
│  └─ NO: Proceed to next decision
│
├─ Is service systemd-aware (sends notifications)?
│  ├─ YES (Type=notify): Trust systemd notification
│  │   └─ Systemd has already confirmed app is ready (received READY=1)
│  │   └─ systemctl is-active should return "active" immediately and accurately
│  │   └─ No polling needed: if unit is "active", app is guaranteed ready
│  │   └─ Gotcha: If app crashes after sending READY=1, systemd must detect via cgroups or process exit.
│  │
│  └─ NO: Proceed to next decision
│
├─ Is service simple/foreground (Type=simple)?
│  ├─ YES: Use systemd status + optional latency check
│  │   └─ systemctl is-active will return "active" when process exists
│  │   └─ BUT: doesn't prove app is responsive (may be initializing)
│  │   └─ Add application-agnostic health check if available (port binding test, socket availability)
│  │   └─ Gotcha: App can appear active while still initializing. Wait 1-2s before first health check.
│  │
│  └─ Use basic systemd status check
│      └─ systemctl is-active is all you have. Accept that health = unit active.
│      └─ Risk: app may be in broken state but unit stays "active". Monitor application behavior separately.
│
└─ END: Use selected health check strategy
```

**Implementation Guidance:**
- For API services with HTTP endpoints: always do HTTP health check (most accurate).
- For system services without HTTP endpoint: use systemd status check (type-appropriate).
- Health check should distinguish "service is initializing" from "service is broken": use startup time awareness.
- For Type=simple, add initial delay (e.g., 1s) before first health check to allow initialization.
- Log health check results: timestamp, status, latency. Reveals patterns (slow startup, intermittent failures).

---

### Decision Tree 4: Timeout Configuration (Start, Stop, Restart)

```
START: Configure timeouts
│
├─ How long does your app typically take to start?
│  ├─ < 1 second (lightweight, fast startup): Node.js, Go, Rust
│  │   └─ TimeoutStartSec=5 (5 seconds, 5x safety margin)
│  │   └─ RestartSec=2 (wait 2s between restarts)
│  │
│  ├─ 1-5 seconds (medium startup): FastAPI, Flask, Sinatra
│  │   └─ TimeoutStartSec=15 (15 seconds, 3x safety margin)
│  │   └─ RestartSec=5 (wait 5s between restarts)
│  │
│  ├─ 5-30 seconds (heavy startup): Spring Boot, Django, Laravel
│  │   └─ TimeoutStartSec=60 (60 seconds, 2x safety margin)
│  │   └─ RestartSec=10 (wait 10s between restarts)
│  │
│  └─ > 30 seconds (very heavy): Java with large heap, complex initialization
│      └─ TimeoutStartSec=120 (2 minutes, large margin)
│      └─ RestartSec=30 (wait 30s between restarts, prevent rapid restart spam)
│      └─ Consider architecture: service should start faster (split into lighter components)
│
├─ How long does your app typically take to shut down gracefully?
│  ├─ < 1 second (stateless, no connections): lightweight services
│  │   └─ TimeoutStopSec=5 (5 seconds, safety margin)
│  │
│  ├─ 1-5 seconds (flush caches, close connections): most services
│  │   └─ TimeoutStopSec=15 (15 seconds, 3x safety margin)
│  │
│  ├─ > 5 seconds (many connections, large state): databases, stateful services
│  │   └─ TimeoutStopSec=60 (60 seconds, ensure graceful shutdown)
│  │
│  └─ Unknown: Default to TimeoutStopSec=30 (safe middle ground)
│
├─ How often do you expect restarts?
│  ├─ Frequent restarts (> 1 per day): set RestartSec shorter (2-5s)
│  │   └─ Reduces time to recovery
│  │
│  ├─ Infrequent restarts (< 1 per week): set RestartSec longer (10-30s)
│  │   └─ Prevents cascading failures during restart storms
│
└─ END: Use selected timeouts
```

**Implementation Guidance:**
- Test actual startup time in target environment (not just local machine).
- Set TimeoutStartSec to 2-5x measured startup time (accounts for variation and system load).
- Set TimeoutStopSec conservatively: better to wait longer than to force-kill and lose state.
- Monitor for timeout events: if timeouts occur regularly, investigate (slow system? resource exhaustion?).
- Document timeout rationale in unit file comments for future operators.

---

## Systemd Version Compatibility

Systemd behavior and directive support varies significantly across versions.

### Version 220 (Released 2015): Major Compatibility Baseline

- First version with stable core features (widely used as baseline)
- Introduced ActiveEnterTimestampMonotonic (for reliable uptime calculation)
- Environment variable expansion timing changed (can cause compatibility issues)

**Minimum Recommended:** systemd 220+

### Version 230 (Released 2016): User Namespace & Dynamic User Support

- Introduced DynamicUser=yes (create users dynamically, avoid managing static users)
- Added user namespace support for service isolation
- Improved cgroup handling

**Recommended for:** Services needing user isolation or dynamic user management

### Version 240 (Released 2019): Significant UX Improvements

- Improved error messages (much clearer than earlier versions)
- Better journal handling and performance
- Added StartLimitAction property (control behavior on restart limit hit)

**Recommended for:** Production systems (clear errors reduce debugging time)

### Version 250+ (Released 2021+): Modern Systemd Features

- Improved security features and sandboxing
- Better performance and logging
- Advanced cgroup v2 support

**Recommended for:** New deployments on recent distributions

### Compatibility Guidance

- **Check systemd version before deployment:** `systemctl --version`
- **Document minimum required version** in deployment documentation
- **Test unit file on target version** in pre-deployment validation
- **Feature support matrix:** Maintain list of which features require which versions
  - Type=notify: 207+
  - DynamicUser: 230+
  - StateDirectory: 229+
  - RuntimeDirectory: 213+
  - ProtectSystem: 212+
  - PrivateTmp: 188+

---

## Unit File Templating and Dynamic Services

### Template Units (One Unit File, Many Instances)

Systemd supports template units: single unit file can spawn multiple instances with different parameters.

**Example:** `service@.service` template can create `service@instance1`, `service@instance2`, etc.

```ini
[Unit]
Description=Dynamic Service %i
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/myapp --instance=%i --port=%I
Environment=INSTANCE_ID=%i

[Install]
WantedBy=multi-user.target
```

Start multiple instances: `systemctl start service@app1 service@app2 service@app3`

**Deployment Considerations:**
- Each instance has separate state (PID, restart count, logs)
- Health checks must target correct instance
- Stop all instances explicitly (stopping template doesn't stop instances)
- Monitor each instance independently (separate journal, separate health check)

---

## Performance Considerations

### Service Management at Scale

Deploying many services (> 10) on single host requires attention to performance:

- **Parallel vs. Sequential Startup:** Start independent services in parallel (faster), but respect dependencies
- **Disk I/O:** Starting 50 services simultaneously reads 50 unit files from disk. I/O can become bottleneck on slow storage.
- **Cgroup Overhead:** Many services = many cgroups. System cgroup hierarchy becomes deep, performance degrades.
- **Journal Performance:** Heavy logging from all services can bottleneck journalctl and journal writer.

**Recommendations:**
- Start services in dependency order, but parallel within layers
- Use ProtectSystem=strict and PrivateTmp=yes only if needed (they add cgroup overhead)
- Configure journal rotation aggressively for multi-service hosts
- Monitor system metrics during multi-service startup: CPU, disk, memory, journal write rate

---

## Troubleshooting & Log Analysis

### Journalctl Filtering for Diagnostics

```bash
# All logs for a service
journalctl -u SERVICE_NAME

# Last 50 lines, follow new entries
journalctl -u SERVICE_NAME -n 50 -f

# Logs from last hour
journalctl -u SERVICE_NAME --since "1 hour ago"

# Only errors and warnings
journalctl -u SERVICE_NAME -p err -p warning

# Parse-friendly JSON output (for log aggregation)
journalctl -u SERVICE_NAME -o json | jq '.message'

# Performance: time taken by each journal read
journalctl -u SERVICE_NAME --no-pager --grep "took.*ms" -o short
```

### Common Journal Messages & Diagnosis

| Message | Cause | Action |
|---------|-------|--------|
| "failed to parse settings" | Syntax error in unit file | Run `systemd-analyze verify /path/unit.service` |
| "unit dependency failed" | Dependent service not active | Start dependent service first, check deps with `systemctl list-dependencies` |
| "condition failed" | ConditionXXX evaluated to false | Check unit conditions, verify system meets conditions |
| "no executable specified" | ExecStart missing or typo'd | Review unit file for ExecStart typos |
| "permission denied" | User/Group doesn't exist or path not accessible | Verify User/Group exist, check working directory permissions |
| "too many restarts" | Restart limit hit | Check application logs, fix root cause, reset restart counter |
| "timeout waiting for signal" | Type=notify but no signal sent | Verify app is built with systemd notify, check app logs |

---

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

## Systemd Unit File Setup & Validation

Before using this skill, systemd unit files must be properly configured and validated.

### Unit File Example

Example unit file at `/etc/systemd/system/backend-api.service`:

```ini
[Unit]
Description=Backend API Service
Documentation=https://docs.example.com/backend-api
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=apiuser
Group=apiuser
WorkingDirectory=/opt/backend-api
EnvironmentFile=/etc/default/backend-api
ExecStart=/opt/backend-api/bin/server --port=3000
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StartLimitBurst=5
StartLimitIntervalSec=30
TimeoutStartSec=30
TimeoutStopSec=10
KillMode=process
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Unit File Fields Explained

| Field | Purpose | Required | Example |
|-------|---------|----------|---------|
| `Type` | Service startup style | Yes | `simple`, `forking`, `oneshot`, `notify` |
| `User` | User to run service as | Recommended | `appuser` |
| `WorkingDirectory` | Working directory for process | Recommended | `/opt/app` |
| `ExecStart` | Command to start service | Yes | `/usr/bin/myapp --config=/etc/myapp.conf` |
| `ExecReload` | Command to reload (optional) | No | `/bin/kill -HUP $MAINPID` |
| `Restart` | Auto-restart policy | Recommended | `on-failure`, `always`, `no` |
| `RestartSec` | Delay between restarts | Recommended | `5` (seconds) |
| `TimeoutStartSec` | Timeout for startup | Recommended | `30` (seconds) |
| `TimeoutStopSec` | Timeout for graceful shutdown | Recommended | `10` (seconds) |
| `KillMode` | How to kill process | Recommended | `process`, `control-group` |
| `EnvironmentFile` | External environment file | Optional | `/etc/default/service` |
| `StandardOutput`, `StandardError` | Logging destination | Recommended | `journal` (send to systemd journal) |

### Unit File Deployment Steps

```bash
# 1. Copy unit file to system directory (as root/sudo)
sudo cp backend-api.service /etc/systemd/system/

# 2. Validate unit file syntax before loading
sudo systemd-analyze verify /etc/systemd/system/backend-api.service

# 3. Reload systemd daemon to recognize new/changed unit files
sudo systemctl daemon-reload

# 4. Enable unit for auto-startup on boot
sudo systemctl enable backend-api

# 5. Start the service
sudo systemctl start backend-api

# 6. Verify it started and is active
sudo systemctl status backend-api

# 7. Check journal for any errors during startup
sudo journalctl -u backend-api -n 20
```

### Pre-Deployment Unit File Validation Checklist

- [ ] Run `systemd-analyze verify /path/unit.service` (must exit 0)
- [ ] Check User/Group exist: `id USERNAME`
- [ ] Verify WorkingDirectory is accessible: `test -d /path && echo OK`
- [ ] Validate ExecStart path exists: `test -x /path/to/binary`
- [ ] Check TimeoutStartSec > estimated startup time
- [ ] Check TimeoutStopSec > estimated graceful shutdown time
- [ ] Set RestartSec appropriately (5-10s for most services)
- [ ] Set Restart=on-failure or Restart=always (not no)
- [ ] Verify EnvironmentFile exists if specified: `test -f /etc/default/service`
- [ ] Test unit file loading: `sudo systemctl daemon-reload && sudo systemctl cat backend-api`

---

## Implementation Details

### Command Execution

All commands are executed with proper error handling:

```bash
# Check if service is active
systemctl is-active backend-api
# Output: "active", "inactive", "failed", "activating", etc.

# Get detailed status
systemctl show backend-api
# Output: Key=value pairs (systemd-parseable format)

# Get specific properties (monotonic timestamp, restart count, PID)
systemctl show -p ActiveEnterTimestampMonotonic,NRestarts,MainPID backend-api
# Output: ActiveEnterTimestampMonotonic=12345678
#         NRestarts=0
#         MainPID=5432

# Verify unit file loaded correctly
systemctl cat backend-api
# Output: Full unit file as loaded by systemd

# Check if unit is enabled
systemctl is-enabled backend-api
# Output: "enabled", "disabled", "masked", "static"
```

### Status Parsing & Timestamp Handling

Use monotonic timestamps (systemd 220+) for reliable uptime calculation:

```
ActiveEnterTimestampMonotonic=123456789
^                              ^
Property (locale-independent)  Monotonic counter (nanoseconds)
```

Uptime calculation: `current_monotonic_time - ActiveEnterTimestampMonotonic`

**Key Points:**
- Monotonic timestamps don't change with system clock adjustments (NTP, manual time changes)
- Locale-independent: works on non-US systems (no day name parsing)
- More reliable than wall-clock timestamps for uptime calculation

### Error Handling & Timeout Strategy

All operations include robust error handling:

1. **Version Check**: Verify systemd version supports required directives (220+)
2. **Unit Validation**: Confirm unit file loaded with `systemctl cat`
3. **Permission Checks**: Catch permission errors and provide clear messaging
4. **Timeout Handling**: Poll with exponential backoff (100ms, 200ms, 400ms, 800ms, max 5s)
5. **Status Verification**: Confirm desired state reached before returning success
6. **Journal Analysis**: Parse systemctl status and journal for detailed error information

### Timeout & Retry Configuration

| Operation | Default Timeout | Poll Strategy | Max Retries |
|-----------|-----------------|---------------|-------------|
| start() | 30s | Exponential backoff (100ms-5s) | Until timeout |
| stop() | 30s | Exponential backoff (100ms-5s) | Until timeout |
| health_check() | 5s | Single attempt (or configurable retries) | 3 attempts recommended |

---

## Usage Examples

### Basic Deployment Flow

```javascript
// Pre-flight validation
const systemdVersion = await getSystemdVersion();
if (systemdVersion < 220) {
  throw new Error('Systemd 220+ required');
}

// Start service with validation
console.log('Starting backend-api...');
const startResult = await start('backend-api', {
  timeout_ms: 30000,
  systemd_version_check: true,
  health_check_config: { 
    port: 3000, 
    endpoint: '/health', 
    timeout_ms: 5000 
  }
});
console.log(startResult); 
// { status: "active", unit_loaded: true, active_time_ms: 1234, main_pid: 5432 }

// Service is verified active and healthy
console.log('Deployment successful!');
```

### Enhanced Health Monitoring

```javascript
// Monitor service with detailed diagnostics
async function monitorService(serviceName) {
  const baselineLatency = 50; // ms, from previous healthchecks
  
  const health = await health_check(serviceName, {
    include_http_check: true,
    http_config: { port: 3000, endpoint: '/health', timeout_ms: 5000 },
    allow_activating: false
  });
  
  console.log(`Service: ${serviceName}`);
  console.log(`  Status: ${health.status}`);
  console.log(`  Healthy: ${health.healthy}`);
  console.log(`  Uptime: ${health.uptime_seconds}s`);
  console.log(`  Latency: ${health.latency_ms}ms`);
  
  // Detect degradation
  if (health.latency_ms > baselineLatency * 3) {
    console.warn(`LATENCY_SPIKE: ${health.latency_ms}ms vs baseline ${baselineLatency}ms`);
    // Escalate to monitoring system
  }
  
  // Detect restart loops
  if (health.restart_count > 1) {
    console.error(`RESTART_LOOP: service restarted ${health.restart_count} times`);
    // Escalate and investigate
  }
  
  return health;
}

// Run monitoring loop
setInterval(() => monitorService('backend-api'), 30000);
```

### Graceful Shutdown with Verification

```javascript
async function gracefulShutdown(serviceName) {
  console.log(`Initiating graceful shutdown for ${serviceName}...`);
  
  const stopResult = await stop(serviceName, {
    timeout_ms: 30000,
    force_after_timeout: true,  // Force-kill after 30s if needed
    check_journal: true          // Verify no errors post-stop
  });
  
  console.log(stopResult);
  // { status: "inactive", stopped_at_seconds: 1234, duration_ms: 2500, force_used: false }
  
  if (stopResult.force_used) {
    console.warn('WARNING: Force-kill was necessary (graceful shutdown failed)');
    console.warn('Possible causes: blocked signal handler, uninterruptible I/O');
  }
  
  // Verify service is truly inactive
  const health = await health_check(serviceName);
  if (health.status !== 'inactive') {
    throw new Error(`Service did not stop cleanly: status=${health.status}`);
  }
  
  console.log('Graceful shutdown completed successfully');
}
```

### Multi-Service Deployment with Dependency Ordering

```javascript
// Define service dependencies
const serviceMap = {
  'mysql': { 
    dependencies: [], 
    startup_time_ms: 5000,
    port: 3306 
  },
  'redis': { 
    dependencies: [], 
    startup_time_ms: 1000,
    port: 6379 
  },
  'backend-api': { 
    dependencies: ['mysql', 'redis'], 
    startup_time_ms: 3000,
    port: 3000,
    health_endpoint: '/health'
  }
};

async function deployServices(services) {
  // Start services in dependency order
  const started = new Set();
  
  for (const serviceName of services) {
    const service = serviceMap[serviceName];
    
    // Wait for dependencies
    for (const dep of service.dependencies) {
      if (!started.has(dep)) {
        console.log(`Dependency ${dep} not started. Starting it first...`);
        await deployService(dep);
        started.add(dep);
      }
    }
    
    // Start this service
    await deployService(serviceName);
    started.add(serviceName);
  }
}

async function deployService(serviceName) {
  const service = serviceMap[serviceName];
  
  console.log(`Starting ${serviceName}...`);
  const startResult = await start(serviceName, {
    timeout_ms: service.startup_time_ms * 2,  // 2x safety margin
    health_check_config: service.health_endpoint ? {
      port: service.port,
      endpoint: service.health_endpoint,
      timeout_ms: 5000
    } : undefined
  });
  
  if (startResult.status !== 'active') {
    throw new Error(`${serviceName} failed to start`);
  }
  
  console.log(`${serviceName} is healthy and running`);
}

// Deploy entire stack
await deployServices(['mysql', 'redis', 'backend-api']);
console.log('All services deployed successfully!');
```

### Deployment with Rollback on Failure

```javascript
async function deployWithRollback(serviceName, config) {
  let previousHealth = null;
  
  try {
    // Get previous state before deployment
    previousHealth = await health_check(serviceName);
    console.log(`Previous service state: ${previousHealth.status}`);
    
    // Stop old version
    await stop(serviceName, { timeout_ms: 30000 });
    console.log('Old version stopped');
    
    // Deploy new version (restart with new config)
    const result = await start(serviceName, {
      timeout_ms: 30000,
      health_check_config: { 
        port: config.port, 
        endpoint: '/health' 
      }
    });
    
    // Verify new version is healthy
    if (result.status !== 'active') {
      throw new Error('New version failed to start');
    }
    
    console.log('Deployment successful!');
    return result;
    
  } catch (error) {
    console.error('Deployment failed:', error.message);
    
    if (previousHealth && previousHealth.status === 'active') {
      console.log('Rolling back to previous version...');
      
      // Stop failed new version
      try {
        await stop(serviceName);
      } catch (stopError) {
        console.error('Failed to stop new version:', stopError);
      }
      
      // Restart previous version
      try {
        await start(serviceName);
        const health = await health_check(serviceName);
        
        if (health.status === 'active') {
          console.log('Rollback successful! Service restored.');
        } else {
          console.error('CRITICAL: Rollback verification failed');
        }
      } catch (rollbackError) {
        console.error('CRITICAL: Rollback failed:', rollbackError);
      }
    }
    
    throw error; // Escalate after rollback attempt
  }
}
```

---

## Debugging & Troubleshooting

### Common Issues & Diagnostics

When deployments fail, use these commands to diagnose:

```bash
# Quick status check
systemctl status SERVICENAME
systemctl is-active SERVICENAME
systemctl is-enabled SERVICENAME

# Detailed service properties
systemctl show -p Type,ExecStart,User,WorkingDirectory,NRestarts,MainPID SERVICENAME

# View loaded unit file (what systemd actually has in memory)
systemctl cat SERVICENAME

# Check unit file syntax
systemd-analyze verify /etc/systemd/system/SERVICENAME.service

# Review service logs
journalctl -u SERVICENAME -n 50 --no-pager
journalctl -u SERVICENAME -p err -p warning  # Errors and warnings only
journalctl -u SERVICENAME --since "5 minutes ago"

# Monitor logs in real-time as you restart
journalctl -u SERVICENAME -f &
systemctl restart SERVICENAME

# Check dependencies
systemctl list-dependencies SERVICENAME --reverse

# See all unit load errors
systemd-analyze verify

# Performance: check startup time
systemd-analyze blame | head -10  # Slowest units
systemd-analyze critical-chain SERVICENAME  # Dependency chain for this service
```

### Common Error Messages

| Error | Likely Cause | Fix |
|-------|-----|---|
| "Unit not found" | Unit file not deployed or daemon-reload not run | Run `systemctl daemon-reload` after deploying unit |
| "cannot set user to X" | User doesn't exist | Create user: `useradd -r -s /bin/false X` |
| "permission denied" | Insufficient privileges or file permissions | Check file ownership and permissions; may need sudo |
| "no executable specified" | ExecStart missing or typo'd | Run `systemd-analyze verify` to find typos |
| "timeout waiting for signal" | Type=notify but app didn't send READY=1 | Verify app is built with systemd-notify support |
| "restart limit hit" | Service restarts too frequently | Check app logs; fix startup issues (missing config, deps, etc.) |
| "dependency not satisfied" | Dependent unit failed | Start dependencies first or remove dependency |

---

## Limitations & Constraints

### Hard Limitations

1. **systemd required**: Only works on Linux systems with systemd. Cannot deploy via this driver on non-systemd systems.
2. **Unit files pre-deployed**: Requires systemd unit files already present and properly configured at `/etc/systemd/system/`.
3. **Permissions required**: Start/stop operations require sufficient privileges (typically root or sudo).
4. **No transactional semantics**: Multiple service start/stop operations are independent; no rollback if one fails.
5. **No distributed consensus**: systemd is single-node; no coordination across multiple hosts (use conductor-orchestrate for multi-host).

### Practical Constraints

1. **Polling-based**: Health checks are point-in-time snapshots, not continuous monitoring. Service can fail 100ms after health check passes.
2. **Startup time variation**: Service startup time depends on system load, disk I/O, network conditions. Timeouts must account for variation.
3. **Restart loop difficulty**: Detecting restart loops requires post-start monitoring. Tight restart loops can consume CPU.
4. **Process identification**: Service tracking relies on PID. If service forks unexpectedly, systemd may track wrong process.
5. **Journal retention**: Systemd journal has size limits; old logs may be auto-deleted after several days or when size limit hit.
6. **Locale dependencies**: Some systemd outputs are locale-dependent (timestamps, error messages). Must handle locale variations.

### Design Constraints

1. **No custom service startup logic**: This driver only manages systemd units. Service startup must be self-contained in the unit file / app startup code.
2. **Health check is application-specific**: No generic "is the service healthy" check. Requires app-specific health endpoint or custom logic.
3. **No A/B testing**: systemd isn't designed for running multiple versions side-by-side. Blue-green deployments require separate infrastructure.
4. **No dynamic scaling**: This driver manages single service instances. Doesn't scale (scale via multiple units or container orchestration).

---

## Returns & Response Format Summary

### start() Return Format

**Success:**
```json
{
  "status": "active",
  "unit_loaded": true,
  "active_time_ms": 1234,
  "main_pid": 5432,
  "timestamp": 1649234567890
}
```

**Failure:** Throws error with message like:
- "Unit not found"
- "Systemd version incompatible (220+ required, have 219)"
- "Service did not reach active state within 30000ms"

### health_check() Return Format

**Healthy:**
```json
{
  "healthy": true,
  "status": "active",
  "uptime_seconds": 3600,
  "main_pid": 5432,
  "restart_count": 0,
  "latency_ms": 25,
  "timestamp": 1649234567890
}
```

**Unhealthy:**
```json
{
  "healthy": false,
  "status": "failed",
  "uptime_seconds": 0,
  "main_pid": null,
  "restart_count": 5,
  "timestamp": 1649234567890
}
```

**Failure:** Throws error or returns with healthy=false and status="unknown"

### stop() Return Format

**Success:**
```json
{
  "status": "inactive",
  "stopped_at_seconds": 1234,
  "duration_ms": 2500,
  "force_used": false,
  "timestamp": 1649234567890
}
```

**Failure:** Throws error with message like:
- "Service did not stop gracefully within 30000ms"
- "Unit not found"

---

## Dependencies & Compatibility

### System Requirements

- **Linux with systemd 220+**: Minimum supported version (released 2015)
- **Root or sudo access**: Required for systemctl start/stop
- **journalctl available**: For log analysis and debugging
- **systemd-analyze available**: For unit file validation

### CLI Tools Used

- `systemctl`: Service management
- `systemd-analyze`: Unit file validation and performance analysis
- `journalctl`: Log retrieval and filtering
- Standard POSIX tools: `grep`, `awk`, `test`, `stat`

### Supported systemd Features

| Feature | Minimum Version | Required | Example |
|---------|-----------------|----------|---------|
| Basic start/stop | 188 | Yes | Type=simple |
| RuntimeDirectory | 213 | No | Creates /run/SERVICE dir |
| Type=notify | 207 | No | App sends READY=1 |
| DynamicUser | 230 | No | User created dynamically |
| StateDirectory | 229 | No | App state persistence |
| ProtectSystem | 212 | No | Filesystem isolation |
| StartLimitAction | 236 | No | Action on restart limit |

---

## Performance Benchmarks

Typical operation durations (on modern hardware):

| Operation | Typical Duration | Max Duration | Notes |
|-----------|-----------------|--------------|-------|
| daemon-reload | 10-100ms | 1s | After updating unit files |
| systemctl start (simple type) | 100-500ms | 5s | Plus app startup time |
| systemctl start (forking type) | 500ms-2s | 10s | Plus parent exit time |
| health check HTTP | 10-100ms | 5s | App-dependent latency |
| systemctl stop (graceful) | 10-500ms | 30s | Plus app shutdown time |
| systemctl show (query) | 5-20ms | 100ms | Fast systemd query |

**Load Testing Notes:**
- Starting 10+ services simultaneously: expect 2-5x slowdown due to disk I/O
- Journal write bottleneck at > 1000 log lines/second
- Unit file reload becomes slow if > 1000 units present

---

## Checklist

Before claiming deployment complete:

- [ ] systemd unit file exists and passes `systemd-analyze verify`
- [ ] `start()` completed without errors
- [ ] `health_check()` returned healthy response from application HTTP endpoint
- [ ] Application logs checked for startup errors (`journalctl -u <service>`)
- [ ] `stop()` called during cleanup (even on failure paths)
- [ ] No previous version of the service left running on the target port
