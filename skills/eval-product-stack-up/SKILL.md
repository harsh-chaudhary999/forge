---
name: eval-product-stack-up
description: "WHEN: Eval is about to run and the full product stack must be brought up first. Reads forge-product.md, starts services in dependency order, runs health checks, confirms stack is ready for eval scenarios."
type: rigid
requires: [brain-read]
version: 1.0.3
preamble-tier: 4
triggers:
  - "bring up the stack"
  - "start eval stack"
  - "spin up services for eval"
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
  - AskUserQuestion
---

# Eval Product Stack Up

Orchestrates startup of the product stack for evaluation. Reads product topology from product.md, starts only the infrastructure and services that are **configured** in the product file, validates health checks, and reports readiness.

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Blocking prompts follow **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. See **`using-forge`** **Interactive human input**.

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

### Eval host preflight vs product stack (cross-cutting)

This skill only proves configured services from **`product.md`** are **READY** (HTTP health, ports, deps). It does **not** install Chrome/CDP, Android emulator/adb, XCTest/simctl, or Node/Appium — those are **eval host** concerns.

Before **`qa-semantic-csv-orchestrate`** / **`qa-pipeline-orchestrate`** QA-P5, agents **must** follow **`eval-driver-ios-xctest`**, **`eval-driver-android-adb`**, **`eval-driver-web-cdp`**, **`eval-driver-api-http`** preflight sections and write transcripts under **`~/forge/brain/prds/<task-id>/qa/logs/`** (**`skills/forge-brain-layout/SKILL.md`**). Failure modes should be distinguishable: **service unhealthy** (this skill) vs **no browser / no device / wrong OS for iOS** (driver skills). Do not blame **stack-up** when the blocker is **missing KVM** or **no `--remote-debugging-port`**.

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/stack-up-reference.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

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

## Cross-References

**Deploy Drivers (service startup):**
- `deploy-driver-pm2-ssh` — startup via PM2 over SSH (`deploy_strategy: pm2-ssh`)
- `deploy-driver-docker-compose` — startup via Docker Compose (`deploy_strategy: docker-compose`)
- `deploy-driver-systemd` — startup via systemd (`deploy_strategy: systemd`)
- `deploy-driver-local-process` — startup via local process (`deploy_strategy: local-process`)

**Eval Drivers (scenario execution):**
- `eval-driver-api-http` — REST API test scenarios
- `eval-driver-db-mysql` — database verification
- `eval-driver-cache-redis` — cache tests
- `eval-driver-bus-kafka` — event bus tests
- `eval-driver-web-cdp` — browser/web UI scenarios
- `eval-driver-android-adb` — Android device scenarios
- `eval-driver-ios-xctest` — iOS device scenarios

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

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] All required services return health-check OK before eval starts; missing service logged as RED_INFRA (not RED_PRODUCT).
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.
