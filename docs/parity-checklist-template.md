# Parity checklist (copy → `~/forge/brain/prds/<task-id>/parity/checklist.md`)

**Purpose:** Prove council locked against the **same depth** as the org’s best **authoritative artifact** (RFC, detailed design note, wiki export, document, diagram packet) — or **explicit N/A + risk** per row. Silence is not agreement.

**Instructions:** Copy this file into the task’s `parity/` folder. For each row: `DONE` | `N/A` + one-line reason | `WAIVER: …` + owner + ticket/ref. `spec-freeze` / thin `shared-dev-spec` without parity material is **BLOCKED** unless `parity_waiver: true` is recorded in `parity/waiver.md` (see `spec-freeze`).

**Ingest tip:** Export or paste any **authoritative** long-form source (wiki, doc tool, PDF text, ticket description export) into `parity/external-plan.md` so the brain holds what downstream agents can **Read** — not only the PRD stub.

| # | Area | Gate (minimum) | Status |
|---|------|------------------|--------|
| 1 | REST | Paths, verbs, auth, versioning strategy, **error envelope**; at least one **JSON request + response example** per new/changed surface-relevant endpoint | |
| 2 | DB | Migration list; projections/read models if any; **indexes**; **backfill** strategy for NOT NULL / data moves | |
| 3 | MQ / events | Topology: exchange/topic type, **queue/topic names**, routing keys **or** “single topic + message type discriminator”; **idempotency key**; ordering; **DLQ**; **who mutates authoritative state** (HTTP-only vs consumer writes DB — must be explicit) | |
| 4 | Cron / jobs | Schedule + **TZ**; idempotency; sweep vs full scan; shadow/dry-run mode | |
| 5 | Web / app FE | State layer (e.g. React Query / Redux / Zustand); **variant / feature-flag matrix** when PRD implies gated UI; SSR/redirect rules; deep-link / query-param callbacks | |
| 6 | Admin / CRM (if in scope) | Permissions model; shared table/lib; routes; audit UI | |
| 7 | Security | PII classification; rate limits; CSRF/session rules for OAuth-style or cookie flows | |
| 8 | Observability | Dashboards or metrics names + **runbook one-pager** pointer | |
| 9 | Rollout | Feature flag name; canary rule or “immediate 100%” + risk | |
|10 | Test pyramid | Min counts per layer **or** `WAIVED` + reason + owner | |

## Domain triggers (add rows or sub-bullets when PRD implies)

When the PRD mentions any of the below, **extend** this checklist (do not leave silent):

- **Gated UI / post-condition behaviour** (e.g. after deadline, role-specific surfaces) → lock **surface list / enum / flag matrix** in `shared-dev-spec` or **WAIVER**
- **Third-party identity / document verification** → lock **retention, token/hash handling, encryption boundary** or **WAIVER**
- **Async handoff** (message broker in critical path) → lock **choreography** (what advances stage N+1: synchronous HTTP vs consumer), idempotency, DLQ or **WAIVER**

---

## Precedence (when both PRD and external plan exist)

1. **`shared-dev-spec.md`** (after freeze) is **normative** for **interfaces** (REST, events, DB, cache, search) — implementers and tech plans align to it.
2. **`parity/external-plan.md`** is **evidence** that council considered the detailed plan. If it **contradicts** the frozen spec, the spec wins until a **change request** / re-council updates the freeze.
3. **`delivery-plan.md`** (non-frozen) may **reference** spec sections; it does not override contracts.
