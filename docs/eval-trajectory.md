# Trajectory eval + OpenTelemetry export

Forge evaluates on **two axes**, and 2026's agent-evaluation frontier needs both:

| Axis | Question | Where |
|---|---|---|
| **Product verdict** | Does the feature work? | `eval-judge` (GREEN/RED/YELLOW from the semantic-eval manifest) |
| **Trajectory verdict** | Did the *run* follow the gates — ordering, eval outcome, heal efficiency? | `tools/forge_trajectory_eval.py` |

Output verdict and trajectory verdict are complementary: a feature can pass its
scenarios (product GREEN) while the run took a corrupt path (trajectory RED), and
vice versa. `dream-retrospect-post-pr` consumes both.

Forge logs a structured, per-phase delivery trajectory — every phase transition
is in `conductor.log` — so it can score its own runs. This is the deterministic
substrate an Agent-as-a-Judge builds on, not a replacement for it.

## Trajectory analyzer

```bash
python3 tools/forge_trajectory_eval.py --task-id <id> [--brain ~/forge/brain] [--strict]
python3 tools/forge_trajectory_eval.py --task-id <id> --out trajectory.json
```

It parses `prds/<id>/conductor.log` and scores four dimensions (0–5):

| Dimension | What it measures |
|---|---|
| `gate_adherence` | Fraction of core gates present: intake lock, spec freeze, semantic eval, dispatch, eval ran. |
| `phase_ordering` | Phase markers logged in non-decreasing rank (`P1 < P2 < P3 < P4.0 … < P5`). Same-rank repeats (heal loops at `P4.4`) are allowed; a true backward jump is flagged. |
| `eval_outcome` | From the last `[P4.4-EVAL-*]` marker: GREEN 5, YELLOW 3, RED_INFRA 2, RED 1. |
| `heal_efficiency` | Penalizes repeated `[P4.4-EVAL-FAIL]`: 0 loops → 5, 1 → 4, 2 → 3, 3 → 1, >3 → 0 (exceeds the self-heal cap). |

`verdict` is `RED` on broken ordering or RED eval, `GREEN` on a clean GREEN run,
`YELLOW` otherwise. `--strict` exits 1 on RED (CI gate).

> **Caveat — it audits the log, not the run.** `gate_adherence` measures whether
> the conductor *logged* each phase marker, not whether the gate truly executed; a
> run that skips a gate may also skip its marker. The trajectory score is only as
> trustworthy as the conductor's logging discipline — treat a GREEN trajectory as
> "the run *claims* a clean path," corroborated by (not a substitute for) the
> product verdict from `eval-judge`.

## OpenTelemetry export

```bash
python3 tools/forge_otel_export.py --task-id <id> [--brain ~/forge/brain] [--out trace.json]
```

Emits the trajectory as **OTLP/JSON** — the neutral wire format that
[Langfuse](https://langfuse.com), [Braintrust](https://www.braintrust.dev),
[Arize Phoenix](https://phoenix.arize.com), and any OTel-compatible backend
ingest. One root span per task (carrying the trajectory scores + verdict), one
child span per phase marker; the eval spans carry OpenTelemetry **GenAI semantic
convention** attributes (`gen_ai.operation.name`, `gen_ai.system`,
`gen_ai.response.finish_reason`). Post it to an OTLP/HTTP endpoint:

```bash
curl -X POST -H 'Content-Type: application/json' --data @trace.json http://localhost:4318/v1/traces
```

Both tools are **stdlib only** — no OpenTelemetry SDK dependency, so they add no
runtime dependency to the plugin (D5/D13).

## Where it plugs in

- `dream-retrospect-post-pr` runs the analyzer before its qualitative 1–5 scoring
  and (optionally) exports OTLP so delivery quality is tracked over time.
- `eval-judge` cross-references it: product verdict (eval-judge) vs trajectory
  verdict (this tool).
