---
name: eval-driver-api-http
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires HTTP API request/response verification. Minimal HTTP driver: setup(config), call(method, path, body), verify(response, assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.2
preamble-tier: 3
triggers:
  - "eval HTTP API"
  - "run API eval"
  - "HTTP eval driver"
allowed-tools:
  - Bash
---

# eval-driver-api-http Skill

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: api`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

**Minimal HTTP Driver for Eval**

This skill provides a minimal HTTP driver for evaluating API endpoints. It handles HTTP request/response cycles for basic eval scenarios. Full multi-surface eval support will be implemented in later phases.

## Anti-Pattern Preamble

**DO NOT assume these falsehoods:**

1. **"HTTP tests are enough, no need multi-surface eval"** — HTTP tests verify only the happy path. Real production behavior involves connection failures, timeouts, SSL cert issues, rate limiting, and connection pooling exhaustion that HTTP mocks never expose. Always plan for multi-surface eval (web, mobile, cache, message bus).

2. **"We can mock HTTP responses"** — Mocking network behavior is dangerous. Mocks hide real failure modes: connection resets, partial reads, slow networks vs. timeouts, retry exhaustion, certificate validation failures. Eval must exercise real network conditions. Mock *data*, not *transport*.

3. **"Network timeouts don't matter for eval"** — Timeouts are performance contracts between client and server. Setting wrong timeouts creates false positives (tests pass locally, fail in production under load) or false negatives (tests timeout, production succeeds). Timeout configuration must be derived from observed P95 latency + buffer, not guesses.

## Iron Law

```
EVERY HTTP EVAL ASSERTION VERIFIES SPECIFIC STATUS CODE, RESPONSE BODY FIELDS, AND CONTENT-TYPE. NO ASSERTION IS "STATUS 2xx IS ENOUGH." TIMEOUTS ARE DERIVED FROM P95 LATENCY DATA, NOT DEFAULTS. teardown() IS CALLED IN ALL PATHS.
```

## Preflight — formal driver vs ad-hoc curl (HARD-GATE)

When YAML declares **`driver: api-http`** (or equivalent) and **`baseUrl` / env** resolve to a **reachable** API host, the agent **must** execute scenarios through this skill’s contract — **`setup` → `call` → `verify` → `teardown`** (or a **documented** bash/HTTP script that **matches** the same assertions, status, and body checks — not looser than **`verify`**).

**Forbidden:** Marking API eval **pass/fail** using **only** informal **`curl`** one-liners while skipping **`qa-semantic-csv-orchestrate`** / host dispatch to this driver when the stack is up — that is a **process skip**, not a system constraint. **Log** request/response summaries (status, key headers, body snippet) under **`~/forge/brain/prds/<task-id>/qa/logs/eval-preflight-<ISO8601>.log`** or per-run HTTP trace (**redact** **`Authorization`**, API keys).

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`curl` smoke alone substitutes for `driver: api-http` steps** — STOP. Run **`eval-driver-api-http`** (via **`qa-semantic-csv-orchestrate`** or the host runner) so status / body assertions are enforced consistently. Informal probes may **supplement** debugging; they **do not replace** driver execution when the API is reachable.
- **Assertion checks only that status code is 2xx without verifying response body** — A 200 OK with an empty body or error payload in the body is not a passing eval. STOP. Every assertion must verify specific response body fields.
- **Timeout is set to the driver default without consulting P95 latency data** — Default timeouts (5000ms) may mask slow endpoints or cause false timeouts on valid but slower responses. STOP. Set timeout to observed P95 latency + 50% buffer for each endpoint.
- **`teardown()` is not called after scenario completes** — An HTTP driver with open keep-alive connections will prevent subsequent scenarios from connecting to the same port. STOP. Always call `teardown()` in all paths.
- **Eval sends requests against a live production URL** — Eval exercises edge cases and failure modes that can corrupt or modify production data. STOP. Eval must always target a dedicated eval environment.
- **Certificate validation is suppressed without documentation** — `rejectUnauthorized: false` silently disables SSL verification and hides certificate issues. STOP. Fix the certificate issue, not the check.
- **Response body is compared by stringification instead of field-by-field** — JSON field order and whitespace vary by serializer. String comparison produces false failures. STOP. Parse the response and assert on individual fields.

## Overview

The eval-driver-api-http skill enables:
- Setup of HTTP test environment
- Execution of HTTP requests against APIs
- Verification of HTTP responses
- Transient failure recovery and retry strategies
- Timeout management based on real latency data
- Teardown and cleanup

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/api-http-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

## Checklist

Before running an HTTP API eval scenario:

- [ ] Target URL points to eval environment (not production)
- [ ] Timeout derived from P95 latency data, not default value
- [ ] Assertions verify specific status code AND specific response body fields
- [ ] Response body compared field-by-field, not by string equality
- [ ] Certificate validation is enabled (not suppressed with rejectUnauthorized: false)
- [ ] `teardown()` called in all paths (success, failure, timeout)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] All HTTP requests include correct auth headers; status codes matched, not just 2xx.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

| Skill / Doc | Relationship |
|---|---|
| `qa-semantic-csv-orchestrate` | **Dispatcher** — invokes this driver for steps with `Surface: api` or `api-http` |
| `eval-judge` | **Downstream** — reads `semantic-eval-run.log` entries this driver writes |
| `forge-eval-gate` | **Gate** — this driver is one of multiple drivers coordinated by the gate |
| `docs/semantic-eval-csv.md` | Surface → driver mapping; `DependsOn` syntax |
| `docs/semantic-eval-schema.md` | `semantic-eval-run.log` outcome enum and required fields |
