---
# Human tech-plan gate — copy to `~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`
# when all repo plans have agent REVIEW_PASS + XALIGN PASS (or N/A). Conductor uses this
# as the explicit phase between automated plan review and State 4b (eval / RED).

status: approved | changes_requested | waived
actor: "<human or role name>"
timestamp: "<ISO8601>"
repos_acknowledged:
  - "<repo-plan-stem as in tech-plans/*.md>"
product_terminology_ack: "yes" | "no" | "not_applicable"
# "yes" = terminology.md reviewed/locked for in-scope product copy, or "not_applicable" = no product-facing terms in this task (see Waiver)
---

## Summary (optional)

One short paragraph: what was reviewed, any residual risk accepted.

## Feedback — `changes_requested`

When **status** is `changes_requested`, list concrete edits expected in which `tech-plans/*.md` sections; do **not** advance the Forge pipeline until plans are revised, **`tech-plan-self-review`** re-runs, **XALIGN** re-runs, and a **new** signoff file (bump filename or replace content with new timestamp) shows **`approved`** or **`waived`**.

## Approval — `approved`

I confirm the elaborative tech plans for the repos listed above match delivery intent and frozen `shared-dev-spec` / contracts. **Product terminology** (`terminology.md`) is acknowledged where applicable (`product_terminology_ack: "yes"` or `"not_applicable"` with reason in **Waiver** below if needed). **Go ahead** to State 4b (semantic machine eval, RED, …).

## Waiver — `waived`

Use only when no human is available **and** policy allows (e.g. solo automation, same operator who authored plans). **One-line reason** required. Pipeline may proceed with logged **`[TECH-PLAN-HUMAN] waived=yes reason=…`**.

**Product terminology — `product_terminology_ack: "not_applicable"`:** If this task has **no** product-facing copy (e.g. purely internal plumbing), state that here. If you skip `terminology.md` because it was **not yet** drafted and user-visible copy exists in plans, that is **not** “not applicable” — use `changes_requested` or complete terminology review first.
