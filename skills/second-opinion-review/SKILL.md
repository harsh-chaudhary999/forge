---
name: second-opinion-review
description: "WHEN: Implementation or a plan is done and you want a structured second pass from another model or reviewer before merge — same repo, no new automation required."
type: flexible
requires: [forge-trust-code]
version: 1.0.0
preamble-tier: 3
triggers:
  - "second opinion"
  - "another model review"
  - "dual review"
allowed-tools:
  - Bash
  - Read
---

# second-opinion-review

Use this **after** your primary implementation pass and **after** you would normally invoke **`forge-trust-code`**. It does not replace spec review; it adds an explicit **independent reasoning pass** so obvious gaps are not missed because one session anchored on the same assumptions.

## Anti-Pattern Preamble

| Rationalization | Why it fails |
|---|---|
| "I'll just ask the same model again" | Same context window, same biases. A second pass only helps if the **prompt or reviewer** changes materially. |
| "Second opinion = slower, skip it" | Cheaper than a revert. Scope it: one file, one risk area, or one contract slice. |
| "I'll merge and fix if reviewers complain" | Post-merge fixes cost more than a 10-minute focused second read on hot paths. |

## Workflow

1. **Freeze inputs:** Point the reviewer at exact commit SHA, diff or file list, and the **locked** PRD path (`prd-locked.md`) plus any **shared-dev-spec** excerpt that matters.
2. **Scope the question:** One primary question (for example: "Are error paths and idempotency claims in the API contract actually implemented?").
3. **Run the second pass:** Different model **or** human **or** same model with explicit instruction: "Do not trust the prior summary; verify from files."
4. **Record outcome:** If anything changes, log it with **`forge-brain-persist`** (what was missed, what you fixed).

## Checklist (reviewer)

- [ ] Claims in PR description match files touched.
- [ ] Security-sensitive paths (auth, input validation, secrets) double-checked.
- [ ] Contracts (API, events, DB) aligned with council-locked spec, not just "works locally."

## Relationship to conductor

**`conductor-orchestrate`** still owns phase order. This skill is an **optional adjunct** before merge when stakes or ambiguity are high.
