---
name: self-heal-locate-fault
description: "WHEN: Semantic machine-eval failed. Parse qa/semantic-eval-run.log (+ semantic-eval-manifest.json), trace the failure chain backwards to the root service, and collect logs and state as evidence."
type: rigid
requires: [brain-read]
version: 1.0.3
preamble-tier: 3
triggers:
  - "locate the fault"
  - "find where eval failed"
  - "which service failed"
allowed-tools:
  - Bash
---

# Self-Heal: Locate Fault

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The error message says which service failed" | Error messages report symptoms, not causes. A 500 from the API may be caused by a cache miss, a DB timeout, or a Kafka lag. |
| "It's probably the service I just changed" | Confirmation bias. The change you made may have exposed a pre-existing bug in a different service. Follow the evidence. |
| "I'll just re-run the eval and see if it passes" | Flaky passes hide real bugs. Diagnose first, fix, then verify. A green re-run without diagnosis is a time bomb. |
| "The logs are too noisy, I'll guess" | Guessing wastes self-heal loop iterations. Filter logs by timestamp and request ID to find the actual failure chain. |
| "Multiple services failed, so it's an environment issue" | Multi-service failures often have a single root cause (e.g., one service returning bad data that cascades). Find the first failure in the chain. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
FAULT LOCATION TRACES THE FAILURE CHAIN BACKWARDS TO THE FIRST FAILURE IN THE TIMELINE. THE LAST SERVICE TO LOG AN ERROR IS NOT THE ROOT. FOLLOW REQUEST IDs AND TIMESTAMPS — NOT INTUITION.
```

## HARD-GATE Anti-Patterns (Critical Enforcement)

### Anti-Pattern 1: "The Last Service in the Eval Output is the Fault Source"

**Why It Fails:** Last output often reflects a downstream cascade effect, not the root cause. The root cause is almost always upstream—the service that failed first, which caused the downstream failures.

**Enforcement (5 MUST bullets):**

- **MUST trace failure chain backwards** — Start from failing assertion, work backwards through call graph using request IDs and timestamps
- **MUST check timing across all services** — Root cause has the earliest failure timestamp; downstream cascades happen later
- **MUST follow causality arrows** — Identify which service's failure triggered the next service's failure (e.g., null response → downstream NullPointerException)
- **MUST compare log patterns** — Root cause produces logs that precede all other error logs by 100+ ms; cascades produce simultaneous logs
- **MUST verify with request ID trace** — Use correlation IDs to follow a single request through the call chain; the first service that logged the error is the fault source

**Example of failure:** Eval output shows cache service error last. Tracing backwards finds API service returned stale data 500ms earlier. Cache was responding normally but to poisoned data from API. API is the root cause.

---

### Anti-Pattern 2: "Just Read the Top-Level Error Message"

**Why It Fails:** Top-level error messages are user-facing abstractions designed for readability, not diagnosis. Root cause is buried in nested exception chains, caused_by fields, or stack trace context layers.

**Enforcement (5 MUST bullets):**

- **MUST unwrap full exception stack** — Do not stop at the first error message. Extract complete nested exceptions: error.cause, error.caused_by, error.inner_exception
- **MUST parse error chain completely** — Read from outermost (user-facing) to innermost (root technical cause). Example: "Request failed" → "Connection timeout" → "ECONNREFUSED" → "Port not listening"
- **MUST extract root exception type** — Innermost exception type is most specific. "NullPointerException at line 156" beats "Internal Server Error"
- **MUST check for wrapped exceptions** — Many frameworks wrap errors; unwrap at least 3 layers deep. Search for keywords: "caused by", "inner exception", "nested error", "error chain"
- **MUST correlate message with stack trace** — Match the error message to a specific file:line in the stack trace. If no match, error message is user-facing abstraction; dig deeper into stack

**Example of failure:** Top-level says "Database error". Unwrapping finds "Connection pool exhausted" → "Max connections (10) reached" → actual root is connection leak in another service. Top-level hid the real cause.

---

### Anti-Pattern 3: "If Logs Are Empty, the Fault is in the Code"

**Why It Fails:** Empty logs for the failure window typically indicate the service never received the request (routing failure), not a code bug. Code always produces logs when it executes; silence means the request never arrived.

**Enforcement (5 MUST bullets):**

- **MUST check network connectivity** — Before concluding code fault, verify service received traffic: check network interfaces, routing tables, firewall rules, load balancer logs
- **MUST trace request routing** — Use request ID to track request through ingress → API gateway → load balancer → service. If request doesn't appear in any layer, routing failed
- **MUST verify service is listening** — Service may not be bound to the correct port, or the address may be 127.0.0.1 instead of 0.0.0.0. Check service logs from startup, netstat output, lsof
- **MUST examine network layer logs** — If app logs are empty, check infrastructure logs: Docker logs, Kubernetes logs, network device logs, reverse proxy logs
- **MUST expand log time window** — Logs may be rotated or buffered. Expand window to ±60s from failure time, check log rotation timestamps, check buffering in place

**Example of failure:** Web-to-API call produces no API logs. "Code must be broken." Actually: API binding to localhost only; web (in different container) cannot reach it. Networking issue, not code.

---

### Anti-Pattern 4: "Pattern Matching Against a Single Error is Sufficient"

**Why It Fails:** Identical error messages can occur from completely different code paths and faults. Error string alone is not unique; full context (stack trace, code location, surrounding logs) is required to distinguish root causes.

**Enforcement (5 MUST bullets):**

- **MUST collect full call stack context** — Do not diagnose from error message only. Extract stack trace showing exactly which file:line threw the error
- **MUST compare complete stack traces** — Same error string from two different stack traces = two different root causes. Example: "NullPointerException" from auth middleware vs database layer are different bugs
- **MUST fingerprint by code location** — Use file:line as primary identifier, not error message. Build fingerprint from: (filename, line_number, function_name, error_type)
- **MUST cross-reference surrounding logs** — Look at logs 5-10 seconds before the error for setup context. Different setup paths → different root causes despite identical error message
- **MUST archive new patterns** — If error message doesn't match known patterns, collect full context and archive as new pattern for future lookups

**Example of failure:** "Connection refused" is seen in both outbound database connection and external service API call. Same message; completely different roots. Stack trace reveals one is in db.connect() and other is in webhooks.post(). Two different faults.

---

### Anti-Pattern 5: "Infrastructure Faults Don't Produce Application Logs"

**Why It Fails:** Infrastructure failures always produce application-level logs. When infrastructure fails (network down, disk full, OOM), the application always logs the effect: connection timeout, ECONNREFUSED, disk write failure, memory allocation error. Infra faults are observable through app logs.

**Enforcement (5 MUST bullets):**

- **MUST search for secondary indicators** — Infra faults manifest as: ECONNREFUSED, ETIMEDOUT, ENOBUFS, "No space left on device", "Out of memory", "Too many open files", DNS resolution failures
- **MUST check system timestamps** — Infra faults often have precise timestamp markers: disk/memory spikes, network packet loss, CPU throttling. Cross-reference app error timestamp with system metrics
- **MUST trace cascading effects** — Infra failure in one service produces timeout in dependent services. Look for: first service logs infra symptom (e.g., ECONNREFUSED), downstream services log timeout waiting for it
- **MUST examine resource limits** — Check kernel limits, container limits, process limits at fault timestamp. Many "mysterious failures" are actually hitting hard limits set at deployment
- **MUST correlate with infrastructure events** — Check load balancer health checks, container orchestration logs, auto-scaler events, deployment logs at exact error timestamp

**Example of failure:** "Service X is buggy" based on error logs. Actually: node running low on disk, kernel killing processes, service never even got to run user code. Infra fault, observable through "too many open files" in logs, but misattributed to service code.

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Fault is attributed to the most recently changed service without log evidence** — Confirmation bias. STOP. Trace the failure chain from the failing assertion back through the call graph using actual logs.
- **"Multiple services failed" is used to conclude "environment issue" without finding the root** — Multi-service cascades have a single root cause. STOP. Find the first failure in the chain by timestamp.
- **Fault location is stated as "probably Service X" without a request ID trace** — Probability without evidence is a guess. STOP. Find the request ID in the failing eval output and follow it through logs.
- **Only the last log line is examined** — Failures log their cause before their effect. STOP. Search logs 30+ seconds before the failure time for the root event.
- **Fault is declared "unknown" after one log search** — Unknown fault = insufficient log collection. STOP. Expand log collection to all services, not just the reported failing one.
- **Re-running eval before completing fault location** — Passing on re-run hides intermittent bugs. STOP. Complete fault location and triage before re-running eval.

When an eval scenario fails, this skill diagnoses which service caused the failure and collects evidence for remediation.

## Overview

The skill performs three sequential operations:
1. **Route + parse failure evidence** — **`qa/semantic-eval-run.log`** + **`qa/semantic-eval-manifest.json`** (semantic CSV eval only — see below)
2. **Identify Fault** — Determine which service/component failed
3. **Collect Evidence** — Gather logs, stack traces, request/response bodies, and state

## Eval evidence: semantic CSV only (HARD-GATE)

Forge machine-eval is **semantic CSV + manifest + run log** only. **Do not** look for legacy **`prds/<task-id>/eval/`** YAML scenario dumps or driver transcript trees — that path is removed.

| Situation | Primary failure artifact | Do **not** use |
|-----------|--------------------------|----------------|
| **Pre-semantic** (no run log yet) | N/A — do not self-heal until **`qa-semantic-csv-orchestrate`** has produced **`qa/semantic-eval-run.log`** (and usually **`qa/semantic-eval-manifest.json`**). | Guessing from **`semantic-automation.csv`** alone without a failed run record |
| **Semantic** (`qa/semantic-automation.csv` + manifest) | **`~/forge/brain/prds/<task-id>/qa/semantic-eval-run.log`** (plus **`qa/semantic-eval-manifest.json`** **`outcome`**) | Nonexistent **`eval/`** YAML / driver artifacts |

**Semantic RED:** If **`qa/semantic-eval-manifest.json`** has **`outcome: fail`** (or Phase 4.4 semantic branch returned RED), **open `qa/semantic-eval-run.log` first.** Format: comment header lines (`# …`, `task_id=…`, `driver=…`), then **one JSON object per line** per semantic step. Parse each line with **`jq`** or a small script; locate objects where **`status`** is **`FAILED`**, **`ERROR`**, or non-success; read **`id`**, **`surface`**, **`intent`**, and any **`error`** / **`message`** fields.

**Trace Surface → service:** Map **`surface`** values (**Web**, **API**, **Android**, …) to repos/services via **`~/forge/brain/products/<slug>/forge-product.md`** Projects / roles. Evidence starts in the **log JSON** lines and the failing step’s **`id`** in **`qa/semantic-automation.csv`**.

## Algorithm

### Parse semantic eval output (`semantic-eval-run.log`)

1. Read **`qa/semantic-eval-run.log`** under the task’s **`qa/`** folder.
2. Skip non-JSON lines (comments starting with **`#`**, **`task_id=`**, **`driver=`**, blanks).
3. For **each JSON line**, inspect **`id`**, **`status`**, **`surface`**, **`reason`**, **`error`**, **`message`**, **`intent`**.
4. Treat **`SKIPPED`** with **`dependency_not_passed`** as cascade — the **first** non-PASS step in topological order is often the root; still verify upstream **`DependsOn`** in **`semantic-automation.csv`**.
5. Cross-reference failed **`id`** with **`qa/semantic-automation.csv`** for **Intent** text and dependencies.

**When:** Semantic Phase 4.4 path failed; **`eval/`** may have **no** matching driver transcript — rely on the steps above (semantic log only).

### Identify Fault

Map the failure to a service or component using causal reasoning. Pattern tables
(HTTP error codes, data inconsistency, service-chain position, external
dependencies) and the per-evidence-type Quick Reference Card of `grep`/`curl`/`redis-cli`
queries are in [reference/fault-patterns.md](reference/fault-patterns.md).

### Collect Evidence

For the identified fault service, gather logs, stack traces, request/response
data, DB state, cache state, and service state. Full per-category source lists
and the fault-fingerprint → evidence-source decision tree are in
[reference/evidence-collection.md](reference/evidence-collection.md).

### Output Fault Diagnosis

Emit the structured `fault_diagnosis` YAML (service, error, evidence,
actionable) for `self-heal-triage`. Full output template and three worked
example diagnoses (backend-API, database, cache faults) are in
[reference/examples.md](reference/examples.md).

## Edge Cases (Critical Scenarios)

Five critical scenarios — no logs for the failure window, multiple services
logging the same error at the same timestamp, missing error fingerprint, clock
skew across services, and silent faults — each with symptom, why-it-happens,
Do-NOT list, action steps, and escalation path, are in
[reference/edge-cases.md](reference/edge-cases.md).

## Checklist

Before handing fault diagnosis to self-heal-triage:

- [ ] **Semantic eval evidence open** — **`semantic-eval-run.log`** (+ manifest **`outcome`**); RED **must** cite failed step **`id`**s from JSON lines
- [ ] Failure chain traced backwards from failing assertion to root service (not just last log entry)
- [ ] Request ID used to correlate logs across services
- [ ] Exception stack unwrapped to root cause (not stopped at user-facing error message)
- [ ] Timestamps compared across services (clock skew corrected if >100ms gap detected)
- [ ] Evidence collected: logs, stack trace, request/response, DB state, cache state as applicable
- [ ] Fault diagnosis recorded using the **structured handoff template** below (YAML-shaped fields for **`self-heal-triage`** consumption — **not** removed eval-scenario YAML)

## Post-Implementation Checklist

- [ ] Fault localized to a specific file + line range (not a vague "the API is broken").
- [ ] Root cause classification assigned: product bug / infra failure / test assertion error / config issue.
- [ ] Evidence written to brain: `blockers/<timestamp>-<description>.md` with task_id: anchor.
- [ ] RED_INFRA path taken (not self-heal retry) if the fault is infrastructure (ECONNREFUSED, Docker down).
- [ ] Fault location passed to self-heal-triage as structured input (not loose prose).

## Cross-References

- **`qa-semantic-csv-orchestrate`**, **`docs/semantic-eval-csv.md`** — semantic CSV schema and runner.
- **`eval-judge`** § Semantic path — verdict from manifest + log.

### Related Skills

1. **self-heal-triage**
   - When to use: After fault has been located, use triage to classify failure type
   - Purpose: Determines which of triage's 4 categories the failure is — Flaky Test, Bad Test, Real Bug, or Environment Issue
   - Input: Fault diagnosis from self-heal-locate-fault
   - Output: Classification (`flaky` | `bad_test` | `real_bug` | `environment`) with confidence score

2. **self-heal-loop-cap**
   - When to use: To ensure healing loop doesn't spin infinitely on the same failure
   - Purpose: Enforces max 3 retries per failure; after 3 attempts, escalates to human review
   - Input: Failure count, fault location
   - Output: Continue healing or escalate decision

3. **self-heal-systematic-debug**
   - When to use: When fault diagnosis is incomplete or unclear, and deeper investigation needed
   - Purpose: Runs 4-phase debugging workflow: investigate → hypothesis → test → verdict
   - Input: Fault diagnosis with uncertainty markers (NEEDS_CONTEXT, BLOCKED)
   - Output: Root cause with high confidence, ready for remediation

---

## Skill Execution Flow

```
Eval Fails
    │
    └──> self-heal-locate-fault (THIS SKILL)
            Output: Fault diagnosis with evidence
    │
    └──> self-heal-triage
            Output: Failure classification
    │
    ├──> IF FLAKY: re-run with instrumentation
    │
    ├──> IF TEST_BUG: skip test, file issue
    │
    └──> IF REPRODUCIBLE:
            │
            └──> self-heal-systematic-debug (if needed for complex faults)
                    Output: Confirmed root cause
            │
            └──> self-heal-remediate
                    Output: Fix applied, eval re-run
```
