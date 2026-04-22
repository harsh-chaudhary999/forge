---
# Human tech-plan gate — copy to `~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`
# when all repo plans have agent REVIEW_PASS + XALIGN PASS (or N/A). Conductor uses this
# as the explicit phase between automated plan review and State 4b (eval / RED).

status: approved | changes_requested | waived
actor: "<human or role name>"
timestamp: "<ISO8601>"
repos_acknowledged:
  - "<repo-plan-stem as in tech-plans/*.md>"
---

## Summary (optional)

One short paragraph: what was reviewed, any residual risk accepted.

## Feedback — `changes_requested`

When **status** is `changes_requested`, list concrete edits expected in which `tech-plans/*.md` sections; do **not** advance the Forge pipeline until plans are revised, **`tech-plan-self-review`** re-runs, **XALIGN** re-runs, and a **new** signoff file (bump filename or replace content with new timestamp) shows **`approved`** or **`waived`**.

## Approval — `approved`

I confirm the elaborative tech plans for the repos listed above match delivery intent and frozen `shared-dev-spec` / contracts. **Go ahead** to State 4b (eval YAML, RED, …).

## Waiver — `waived`

Use only when no human is available **and** policy allows (e.g. solo automation, same operator who authored plans). **One-line reason** required. Pipeline may proceed with logged **`[TECH-PLAN-HUMAN] waived=yes reason=…`**.
