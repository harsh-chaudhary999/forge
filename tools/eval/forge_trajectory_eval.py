#!/usr/bin/env python3
"""Forge trajectory eval — score the *delivery trajectory*, not just the product.

Forge's `eval-judge` answers "does the product work?" (GREEN/RED/YELLOW from the
semantic-eval manifest). The 2026 frontier in agent evaluation is *trajectory*
eval — judging how the run got there: gate adherence, phase ordering, eval
outcome, self-heal efficiency. Forge logs a structured, per-phase delivery
trajectory (`conductor.log` + brain), so it can score its own runs.

Caveat: this audits the *log*, not the run — `gate_adherence` measures whether the
conductor logged each phase marker, not whether the gate truly executed. The score
is only as trustworthy as the conductor's logging discipline; treat it as a
corroborating axis to the product verdict (`eval-judge`), not a substitute.

This is the deterministic substrate an Agent-as-a-Judge (e.g. `dream-retrospect`)
builds on: it parses `prds/<task-id>/conductor.log` and emits a structured
verdict over four dimensions. Stdlib only.

Usage:
  python3 tools/forge_trajectory_eval.py --task-id <id> [--brain ~/forge/brain] [--strict]
  python3 tools/forge_trajectory_eval.py --task-id <id> --out trajectory.json

Exit 0 normally; with --strict, exit 1 when the verdict is RED (eval failed or
phase ordering is corrupt).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

MARKER_RE = re.compile(r"\[([A-Z0-9.\-]+)\]")
PHASE_RE = re.compile(r"^P(\d+)(?:\.(\d+))?-")
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")
FIELD_RE = re.compile(r"(\w+)=([^\s]+)")


def brain_root(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser()
    for env in ("FORGE_BRAIN", "FORGE_BRAIN_PATH"):
        v = os.environ.get(env)
        if v:
            return Path(v).expanduser()
    return Path.home() / "forge" / "brain"


def phase_rank(marker: str) -> float | None:
    m = PHASE_RE.match(marker)
    if not m:
        return None
    major = int(m.group(1))
    minor = int(m.group(2)) if m.group(2) else 0
    return major + minor / 10.0


def parse_log(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        mk = MARKER_RE.search(line)
        if not mk:
            continue
        marker = mk.group(1)
        ts = TS_RE.match(line)
        fields = dict(FIELD_RE.findall(line[mk.end():]))
        events.append({
            "marker": marker,
            "rank": phase_rank(marker),
            "ts": ts.group(1) if ts else None,
            "fields": fields,
        })
    return events


def analyze(task_id: str, brain: Path) -> dict:
    log_path = brain / "prds" / task_id / "conductor.log"
    if not log_path.exists():
        return {"task_id": task_id, "error": f"no conductor.log at {log_path}"}

    events = parse_log(log_path)
    markers = [e["marker"] for e in events]

    def has(prefix: str) -> bool:
        return any(m.startswith(prefix) for m in markers)

    gates = {
        "intake_locked": has("P1-PRD-LOCKED"),
        "spec_frozen": has("P2-SPEC-FROZEN"),
        "semantic_eval": has("P4.0-SEMANTIC-EVAL"),
        "tdd_red": has("P4.0-TDD-RED"),
        "dispatched": has("P4.1-DISPATCH"),
        "review_passed": has("P4.3-REVIEW-PASS"),
        "eval_ran": has("P4.4-EVAL"),
    }

    # Phase ordering: ranked markers must be non-decreasing.
    ranked = [(e["marker"], e["rank"]) for e in events if e["rank"] is not None]
    ordering_ok = all(ranked[i][1] <= ranked[i + 1][1] for i in range(len(ranked) - 1))
    ordering_violations = [
        f"{ranked[i][0]} -> {ranked[i + 1][0]}"
        for i in range(len(ranked) - 1)
        if ranked[i][1] > ranked[i + 1][1]
    ]

    # Eval outcome from the last P4.4 marker.
    eval_outcome = None
    for e in reversed(events):
        if e["marker"].startswith("P4.4-EVAL-PASS"):
            eval_outcome = "GREEN"
            break
        if e["marker"].startswith("P4.4-EVAL-FAIL"):
            eval_outcome = e["fields"].get("outcome", "RED").upper()
            break
        if e["marker"].startswith("P4.4-RED-INFRA"):
            eval_outcome = "RED_INFRA"
            break

    self_heal_loops = sum(1 for m in markers if m.startswith("P4.4-EVAL-FAIL"))

    # ── Dimension scores (0-5) ──
    core_gates = ["intake_locked", "spec_frozen", "semantic_eval", "dispatched", "eval_ran"]
    present = sum(1 for g in core_gates if gates[g])
    gate_adherence = round(5 * present / len(core_gates), 1)
    ordering_score = 5 if ordering_ok else 2
    eval_score = {"GREEN": 5, "YELLOW": 3, "RED_INFRA": 2, "RED": 1}.get(eval_outcome, 0)
    heal_score = {0: 5, 1: 4, 2: 3, 3: 1}.get(self_heal_loops, 0)  # >3 loops exceeds the self-heal cap → 0

    scores = {
        "gate_adherence": gate_adherence,
        "phase_ordering": ordering_score,
        "eval_outcome": eval_score,
        "heal_efficiency": heal_score,
    }
    overall = round(sum(scores.values()) / len(scores), 1)

    if not ordering_ok or eval_outcome in ("RED",):
        verdict = "RED"
    elif eval_outcome in ("YELLOW", "RED_INFRA") or overall < 4:
        verdict = "YELLOW"
    elif eval_outcome == "GREEN":
        verdict = "GREEN"
    else:
        verdict = "YELLOW"

    return {
        "task_id": task_id,
        "log": str(log_path),
        "event_count": len(events),
        "markers": markers,
        "gates": gates,
        "ordering_ok": ordering_ok,
        "ordering_violations": ordering_violations,
        "eval_outcome": eval_outcome,
        "self_heal_loops": self_heal_loops,
        "scores": scores,
        "overall": overall,
        "verdict": verdict,
    }


def human_summary(v: dict) -> str:
    if "error" in v:
        return f"trajectory: {v['error']}"
    lines = [
        f"Trajectory verdict for {v['task_id']}: {v['verdict']} (overall {v['overall']}/5)",
        f"  gates: " + ", ".join(f"{k}={'Y' if val else 'n'}" for k, val in v["gates"].items()),
        f"  scores: " + ", ".join(f"{k}={val}" for k, val in v["scores"].items()),
        f"  eval_outcome={v['eval_outcome']}  self_heal_loops={v['self_heal_loops']}  ordering_ok={v['ordering_ok']}",
    ]
    if v["ordering_violations"]:
        lines.append("  ordering violations: " + "; ".join(v["ordering_violations"]))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Score a Forge delivery trajectory from conductor.log.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--brain", default=None, help="Brain root (default: $FORGE_BRAIN or ~/forge/brain)")
    ap.add_argument("--out", default=None, help="Write JSON verdict to this file (default: stdout summary + JSON)")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when verdict is RED")
    args = ap.parse_args()

    verdict = analyze(args.task_id, brain_root(args.brain))
    payload = json.dumps(verdict, indent=2)

    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(human_summary(verdict))
        print(payload)

    if args.strict and verdict.get("verdict") == "RED":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
