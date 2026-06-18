---
stage: eval
description: Context injected during Forge eval phase (P4.1-DISPATCH → P4.4-EVAL-GREEN) — stack-up, drivers, judge, self-heal
---

# Forge — Eval Stage

**You are in the EVAL phase.** Your job is to bring up the full product stack, run all eval scenarios across surfaces, judge the results, and self-heal any RED scenarios before claiming GREEN.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, invoke it before any response. This is not negotiable.

## Iron Law

```
NO EVAL SCENARIO RUNS AGAINST A PARTIAL STACK. EVERY ASSERTION VERIFIES SPECIFIC VALUES — NOT "STATUS 2xx" OR "ELEMENT EXISTS". SELF-HEAL RUNS ON EVERY RED SCENARIO BEFORE CLAIMING DONE. GREEN IS LOGGED ONLY AFTER ALL SCENARIOS PASS ON THE SAME RUN.
```

## Active Skills (invoke in this order)

1. `forge-eval-gate` — verifies implementation is complete before eval opens
2. `eval-product-stack-up` — brings up ALL services in dependency order, waits for all health checks
3. **`qa-semantic-csv-orchestrate`** / `tools/run_semantic_csv_eval.py` **(semantic CSV — manifest + run.log)** — Phase 4.4 records **`[P4.4-EVAL-GREEN] path=semantic`** via **`eval-judge`** § Semantic path. Repo **unit tests** are from **`forge-tdd`**, not driver YAML.
4. If the host maps **Surface** in **`qa/semantic-automation.csv`** to tools, use the matching **`eval-driver-***`** skills as the runner documentation.
   - API: `eval-driver-api-http`
   - Database: `eval-driver-db-mysql`
   - Cache: `eval-driver-cache-redis`
   - Web UI: `eval-driver-web-cdp`
   - Android: `eval-driver-android-adb`
   - iOS: `eval-driver-ios-xctest`
   - Kafka: `eval-driver-bus-kafka`
   - Search: `eval-driver-search-es`
5. `eval-judge` — scores driver results **or** semantic manifest+log; produces GREEN/RED/YELLOW verdict
6. If RED: `self-heal-locate-fault` → `self-heal-triage` → `self-heal-systematic-debug` → re-run eval

## Stack-Up Rules

- Read `forge-product.md` fresh — do NOT use cached service list
- Start services in topological dependency order (DB before API, API before UI)
- Wait for all health checks to pass — do NOT proceed if any service is degraded
- If stack-up fails: BLOCKED — fix infrastructure before running any scenario

## Anti-Patterns — STOP

- **"Stack is probably up from last time"** — Always verify. Run `eval-product-stack-up` fresh. Stale stacks cause false positives.
- **"Status 2xx is sufficient for an API assertion"** — It is not. Assert specific field values, content-type, and response shape.
- **"One surface passed, that's enough for now"** — All **manifest rows** (semantic path) or **all mapped surfaces** in the run must pass. Partial eval is not eval.
- **"The self-heal found the bug, I'll fix it and claim GREEN without re-running"** — Fix + re-run is mandatory. GREEN requires all scenarios to pass on the same run after the fix.
- **"teardown() can be skipped if the scenario passes"** — teardown() is called in ALL paths. A passing scenario with no teardown leaves state that contaminates the next run.

## Self-Heal Loop Cap

Maximum 3 self-heal iterations per scenario (`self-heal-loop-cap`). If still RED after 3 attempts: BLOCKED — escalate, do not loop further.

## Next Gate

**Semantic (default):** manifest **`outcome: pass`** after stack-up run → `eval-judge` § Semantic path → log **`[P4.4-EVAL-GREEN] path=semantic`**. **Legacy out-of-band YAML** (if used outside Forge orchestration): all scenarios GREEN in single run → `eval-judge` emits GREEN → log `[P4.4-EVAL-GREEN]`. Then switch to PR phase.
