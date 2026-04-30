---
task_id: "<task-id>"
status: draft
updated: "<ISO8601>"
# `none` = no unresolved table rows. Use `pending` when any term row or Notes cell still needs product/PO decision (blocks council / spec-freeze / user-visible PR per policy).
open_doubts: none
# `user_visible` (default) = UI, public API error text, email subjects, support-facing copy. `internal` = only code/ops names; review-readiness may treat `open_doubts: pending` as advisory (see terminology-review in forge repo: docs/terminology-review.md).
terminology_risk: user_visible
---

<!--
  Copy to ~/forge/brain/prds/<task-id>/terminology.md
  Product terminology (per task) — NOT the Forge plugin skill `forge-glossary` (process terms).
-->

# Product terminology — `<task-id>`

Canonical **domain** names for this task. Use these strings in `shared-dev-spec.md`, `tech-plans/*.md`, QA CSV, and eval YAML unless the frozen contract uses a different **code** identifier. **When editing in the brain:** the Forge clone has canonical docs at `docs/terminology-review.md` — this file is under `prds/<task-id>/` (do not rely on relative links to `docs/` or `skills/`; they will not resolve from the brain path after copy).

## Frontmatter: `open_doubts`

| Value | When |
|-------|------|
| **`none`** | Every row in the table is decided; Notes column has no `TODO` / unresolved question, or each is linked to `planning-doubts.md` with resolution. |
| **`pending`** | At least one **term**, **label**, or **variant** is still under review — set this **before** asking the user in a **blocking** review turn. While `pending`, the skills **forge-council-gate** and **spec-freeze** may **block** freeze, and `prompt-submit-gates.cjs` looks at the **last** line matching `[TERMINOLOGY] …` in `conductor.log` for **NEXT GATE**; standalone `/council` appends that line in **council-multi-repo-negotiate** Step 5.4 (not the gate skill). |
| **`unknown`** | File exists but you have not classified doubts yet — treat like **`pending`** for gates until resolved. |

**Notes column vs frontmatter:** Use the **table** for per-term questions; set frontmatter **`open_doubts: pending`** when *any* such row exists. Do not leave **`none`** while the table still has open questions.

## Terms

| Term | Definition | Type | Source (PRD / contract §) | Notes / open doubts |
|------|------------|------|---------------------------|---------------------|
| _ExampleEntity_ | _One sentence._ | entity | prd-locked | |
| | | | | |

## Revision

| When | Change |
|------|--------|
| _ISO date_ | _Initial draft_ |

**DRIFT (eval/QA):** If automated scenarios or drivers show a mismatch vs this table, add a **Revision** row (preferred) or add `qa/terminology-drift-log.md` (optional template: `docs/templates/terminology-drift-log.md` in the forge repo) for audit.

## Review checklist

- [ ] User reviewed (interactive turn per `docs/terminology-review.md` in the forge plugin repo)
- [ ] `status` in frontmatter set to `review` or `locked` after approval
- [ ] `open_doubts` is `none` when the table has no unresolved rows (or link each to `planning-doubts.md`)
