# Adjacency, cohorts, and PRD signals

Single reference for **multi-pipeline coupling**, **segmented product behavior**, and **trust-line → store** mapping. Skills point here instead of duplicating long checklists.

## When this applies

- PRD implies **different behavior by segment** (region, tier, source, trust flag, lifecycle, …), **or**
- **`intake-interrogate` Q4b** / **`pipeline_adjacency_notes`** indicate shared entities touched by **more than one flow**, **or**
- PRD asserts **persisted** truth (“verified”, “eligible”, “classified”, …) without obvious single-table ownership.

If none of the above: still run **State 2.6** once and log **`[ADJACENCY-SCAN] … SKIPPED reason=…`** so the phase is never silently skipped.

## Conductor (State 2.6)

After **`[DISCOVERY]`**, run **`python3 tools/forge_adjacency_scan.py <task-brain-dir> <repo> …`** from the Forge repo (org patterns: **`tools/adjacency-seed-patterns.txt`** or **`--patterns`**). Appends **`discovery-adjacency.md`** under the task.

**Log exactly one line** in `conductor.log` (or session notes):

- **`[ADJACENCY-SCAN] task_id=<id> status=COMPLETE path=discovery-adjacency.md`**, or
- **`[ADJACENCY-SCAN] task_id=<id> status=SKIPPED reason=<no_repos|rg_absent|patterns_empty|human_waiver>`**

Council (State 3) must not start **without** that line. Silent omission is a failure; **`SKIPPED` + reason** is allowed.

**Human tail:** If cohort matrix is missing or **SPEC_INFERENCE-only** for product segments, log **`[HUMAN-REQUIRED] cohort_or_adjacency_gap task_id=<id>`** and resolve before treating Council as closed.

**Example log lines (`conductor-orchestrate` State 2.6):**

```
[ADJACENCY-SCAN] task_id=<id> status=COMPLETE path=discovery-adjacency.md
[ADJACENCY-SCAN] task_id=<id> status=SKIPPED reason=patterns_empty
[ADJACENCY-SCAN] task_id=<id> status=SKIPPED reason=rg_absent
[ADJACENCY-SCAN] task_id=<id> status=SKIPPED reason=no_repos
[HUMAN-REQUIRED] cohort_or_adjacency_gap task_id=<id>
```

## Brain artifacts (task folder)

| Artifact | Path | Role |
|----------|------|------|
| Adjacency grep dump | `prds/<task-id>/discovery-adjacency.md` | Optional seed scan or in-session `rg` summary |
| Cohort & adjacency | `prds/<task-id>/touchpoints/COHORT-AND-ADJACENCY.md` | Segment matrix + pipeline collisions + cron table |
| PRD signals | `prds/<task-id>/touchpoints/PRD-SIGNAL-REGISTRY.md` | PRD trust lines → table.column / topic / key / fixture |
| Risk register | `prds/<task-id>/parity/risk-register.md` | Optional “what we might break” (with **`spec-freeze`** parity) |

**Copy-paste source:** one file with all three table packs — **`docs/templates/adjacency-cohort-and-signals.template.md`**. The template is a single file for convenience; **split it into the three separate brain paths above when populating** — do not write all three table packs into one file under the task brain. Workflow: copy the full template → fill in Section A → write to `touchpoints/COHORT-AND-ADJACENCY.md`; fill in Section B → write to `touchpoints/PRD-SIGNAL-REGISTRY.md`; fill in Section C (if used) → write to `parity/risk-register.md`.

## Council and tech plans

- **Council** must not close cohort-dependent work on **`SPEC_INFERENCE`** alone for segmentation policy — see **`council-multi-repo-negotiate`** red flags (brief); detail lives in the template Section A.
- **`tech-plan-write-per-project` Section 0.1 rule 6** — Section 0 cohort rows need **`USER:`** / **`PO:`** / **`TL:`** or verbatim spec; **`REVIEW_PASS`** forbidden otherwise.
- **`tech-plan-self-review`** — inventory + binary checks reference this doc for artifact paths.
- **`verify_forge_task.py`** does **not** enforce these gates; optional brain CI may grep for **`[ADJACENCY-SCAN]`**.

## Tooling

- **`python3 tools/forge_adjacency_scan.py`** — stdlib + `rg`; see **`tools/README.md`**.
- **`tools/adjacency-seed-patterns.txt`** — org patterns only (one pattern per line; empty file still produces a stub `discovery-adjacency.md` so **`[ADJACENCY-SCAN]`** can be logged). Plain text keeps the shared repo product-agnostic and supports **`--patterns`** overrides without YAML.
