# Forge — opportunity backlog (market-shaped gaps)

Internal-facing backlog of **discipline**, **process**, and **feature** gaps that show up in AI-assisted delivery tools broadly — not a commitment to ship, but a sane prioritization lens for Forge.

## Discipline & audit

| Gap (market pattern) | Why it hurts | Forge-shaped direction |
|---|---|---|
| **Chat is not a record** | Regulators and blameless postmortems want immutable evidence chains | Brain already git-backed; optional **`evidence-bundle`** export (manifest + SHA list + log excerpts) per task |
| **“GREEN” without reproducibility** | Teams cannot replay what passed | Pin **`qa-pipeline.log`** / **`conductor.log`** lines + **`FORGE_TASK_ID`** + container/compose digest in run reports (partially there — tighten templates) |
| **Skill drift across hosts** | Cursor vs Claude behave differently | **`forge-doctor`** one-shot: symlink targets, **`settings.json`** hook count, **`forge.mdc`** mtime vs plugin dir |

## Process & org

| Gap | Why it hurts | Forge-shaped direction |
|---|---|---|
| **QA owns staging; dev owns feature flags** | Standalone **`/qa`** vs **`/forge`** fork confusion | Already documented in README; optional **decision tree** command or **`product.md` flag** `qa_track: delivery | standalone` |
| **No DM triage of RED** | Eval fails become Slack threads, not tickets | Optional **`qa-run-report`** → MCP **`createJiraIssue`** batch (skill mentions this — standardize one path) |
| **Release train vs hotfix** | Same pipeline for both is wasteful | **`qa-branch-env-prep`** modes extended with **`hotfix`** profile (fewer surfaces, time-boxed scenario subset in **`qa-analysis.md`**) |

## Product / feature (differentiation)

| Gap (often missing in “AI coding” plugins) | Forge angle |
|---|---|
| **Multi-repo truth** | Already core: **`product.md`**, cross-repo eval — keep stress-testing monorepo + polyrepo |
| **Contract-before-code** | Council + contracts — market rarely encodes this as **markdown skills**; keep publishing success stories with **shared-dev-spec** excerpts |
| **STLC without a TMS** | Standalone QA pipeline + brain artifacts — buyers still want **export to TestRail/Xray**; deepest win is **bidirectional ID** in scenario YAML (`jira_ref` already mentioned in skills) |
| **Flaky eval classification** | **`self-heal-triage`** exists; gap is **automatic flake bucket** (same RED on re-run → label **FLAKE** in report) — small heuristic, high trust |

## What not to chase (for Forge’s positioning)

- Replacing **managed browsers** (BrowserStack, etc.) — integrate, don’t rebuild.
- **LangChain-style** orchestration inside the plugin (violates D5).
- **Fully unattended** production promotion — human gates are a feature, not a bug.

## See also

- **[README — QA & test artifacts](../README.md#qa--test-artifacts)** (delivery vs **`/qa`**)
- **`skills/qa-pipeline-orchestrate/SKILL.md`** — canonical standalone QA phases
