# Conductor Log Format

**File location:** `~/forge/brain/prds/<task-id>/conductor.log`

Every Forge pipeline phase transition is recorded in `conductor.log` as an append-only log. Each line follows this format:

## Line Format

```
YYYY-MM-DDTHH:MM:SSZ [MARKER] task_id=<id> [field=value ...]
```

- **Timestamp:** ISO-8601 UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`)
- **Marker:** Phase identifier in brackets — see table below
- **task_id:** The Forge task identifier (required on every line)
- **Additional fields:** Key=value pairs specific to the marker (optional but strongly recommended)

## Shell Append Command

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [MARKER] task_id=<id> field=value" >> ~/forge/brain/prds/<id>/conductor.log
```

## Marker Registry

| Marker | Phase | Required Fields | Optional Fields |
|---|---|---|---|
| `[P1-PRD-LOCKED]` | Intake complete | `task_id` | `prd_path`, `q9_design_source` |
| `[P2-SPEC-FROZEN]` | Council complete, spec frozen | `task_id` | `contracts=5`, `spec_path` |
| `[P2-SPEC-AMENDED]` | Spec amendment ratified | `task_id` | `specchg=SPECCHG-<ts>`, `contract` |
| `[P2-SPEC-AMENDMENT-REJECTED]` | Amendment rejected | `task_id` | `specchg=SPECCHG-<ts>` |
| `[P2-DISPUTE-RESOLVED]` | Disputed contract resolved | `task_id` | `contract=<name>`, `decision=DREAM-<id>` |
| `[P3-TECH-PLAN-LOCKED]` | Tech plan approved | `task_id` | `repo=<role>`, `plan_path` |
| `[P3-TECH-PLAN-REVIEW]` | Tech plan review round | `task_id` | `round=<n>`, `result=PASS\|CHANGES` |
| `[P3-TECH-PLAN-XALIGN]` | Cross-repo alignment check | `task_id` | `result=PASS\|FAIL` |
| `[P3-TECH-PLAN-HUMAN]` | Human signoff on tech plan | `task_id` | `status=APPROVED\|REJECTED` |
| `[P4.0-SEMANTIC-EVAL]` | Semantic CSV eval complete | `task_id` | `kind=semantic-csv-eval`, `outcome=pass\|fail\|yellow` |
| `[P4.1-DISPATCH]` | Dev-implementer dispatched | `task_id` | `repo=<role>`, `worktree=<path>` |
| `[P4.1-WORKTREE-FAIL]` | Worktree creation failed | `task_id` | `repos_affected=<list>`, `reason=<msg>` |
| `[P4.2-REVIEW]` | Code review complete | `task_id` | `result=PASS\|CHANGES`, `reviewer=spec\|quality` |
| `[P4.3-REVIEW-PASS]` | All reviews passed | `task_id` | — |
| `[P4.4-EVAL-PASS]` | Eval passed GREEN | `task_id` | `outcome=GREEN`, `manifest=qa/semantic-eval-manifest.json` |
| `[P4.4-EVAL-FAIL]` | Eval failed | `task_id` | `outcome=RED\|YELLOW`, `self_heal_iter=<n>` |
| `[P4.4-RED-INFRA]` | Infrastructure failure during eval | `task_id` | `symptom=<ECONNREFUSED\|docker-down\|mcp-unavailable>` |
| `[P5-PR-RAISED]` | PR raised | `task_id` | `repo=<role>`, `pr_url=<url>` |
| `[P5-PR-MERGED]` | PR merged | `task_id` | `repo=<role>`, `pr_url=<url>` |
| `[DEPLOY-<SURFACE>]` | Deployment complete | `task_id` | `surface=<pm2-ssh\|docker\|systemd\|local>`, `status=complete` |
| `[DEPLOY-HEALTH-FAIL]` | Post-deploy health check failed | `task_id` | `surface=<surface>`, `reason=<msg>` |
| `[DESIGN-INGEST]` | Design artifacts ingested | `task_id` | `figma_mcp=yes\|no\|n/a`, `status=PASS\|BLOCKED` |
| `[QA-ANALYSIS-LOCKED]` | QA analysis approved | `task_id` | `turn_count=<n>` |
| `[CANARY-ALERT]` | Canary anomaly detected | `task_id` | `metric=<name>`, `baseline=<val>`, `current=<val>` |
| `[ROLLBACK-VERIFY]` | Rollback schema verified | `task_id` | `surface=<surface>`, `result=PASS\|FAIL` |
| `[PR-BLOCKED]` | PR creation blocked | `task_id` | `reason=<eval-not-green\|...>` |

## Ordering Rule

Markers MUST be logged in ascending phase order. `[P4.4-EVAL-PASS]` cannot appear before `[P4.1-DISPATCH]`. If out-of-order markers are detected, the pipeline state is corrupt — do not proceed.

**Verification:** `grep '\[P' conductor.log | sort` should match the natural append order.

## Skills That Write to conductor.log

forge-intake-gate, forge-council-gate, spec-freeze, tech-plan-write-per-project, qa-prd-analysis, qa-semantic-csv-orchestrate, conductor-orchestrate, forge-eval-gate, pr-set-coordinate, all deploy-driver-* skills, canary.
