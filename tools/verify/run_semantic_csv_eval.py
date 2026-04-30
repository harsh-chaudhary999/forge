#!/usr/bin/env python3
"""
Execute or validate semantic-automation.csv and write qa/semantic-eval-manifest.json.

  python3 tools/verify/run_semantic_csv_eval.py --task-id MY-TASK --brain ~/forge/brain
  python3 tools/verify/run_semantic_csv_eval.py ... --dry-run
  python3 tools/verify/run_semantic_csv_eval.py ... --driver noop

Host drivers (FORGE_SEMANTIC_DRIVER): noop (default) — records structure only.
Real CDP/ADB/MCP execution belongs on the operator host; extend SemanticDriver in tooling.

See docs/semantic-eval-csv.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from forge_paths import default_brain_root, sanitize_task_id
from semantic_csv import (
    SemanticStep,
    parse_semantic_automation_csv,
    topological_order,
    validate_depends_closure,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _relative_under_task(task_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(task_dir))
    except ValueError:
        return str(path)


def _write_run_log(
    path: Path,
    *,
    task_id: str,
    ordered: list[SemanticStep],
    step_results: list[dict],
    driver: str,
    dry_run: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# semantic-eval-run {_utc_now_iso()}",
        f"task_id={task_id}",
        f"driver={driver} dry_run={dry_run}",
        "",
    ]
    for r in step_results:
        lines.append(json.dumps(r, ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _noop_run(ordered: list[SemanticStep], *, dry_run: bool) -> tuple[list[dict], str]:
    """Returns (result rows, aggregate outcome pass|fail|yellow). Noop never marks steps FAILED."""
    results: list[dict] = []
    failed_ids: set[str] = set()
    for s in ordered:
        if any(d in failed_ids for d in s.depends_on):
            results.append(
                {
                    "id": s.id,
                    "status": "SKIPPED",
                    "reason": "dependency_not_passed",
                    "surface": s.surface,
                }
            )
            continue
        if dry_run:
            results.append(
                {
                    "id": s.id,
                    "status": "VALIDATED",
                    "surface": s.surface,
                    "intent": s.intent,
                }
            )
        else:
            results.append(
                {
                    "id": s.id,
                    "status": "PASSED",
                    "surface": s.surface,
                    "intent": s.intent,
                    "note": "noop driver — no real host execution",
                }
            )
    outcome = "yellow" if dry_run else "pass"
    return results, outcome


def run_pipeline(
    *,
    task_dir: Path,
    task_id: str,
    csv_path: Path | None,
    dry_run: bool,
    driver_name: str,
    outcome_override: str | None,
) -> int:
    qa = task_dir / "qa"
    csv_file = csv_path or (qa / "semantic-automation.csv")
    steps, parse_errs = parse_semantic_automation_csv(csv_file)
    if parse_errs:
        for e in parse_errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    dep_errs = validate_depends_closure(steps)
    if dep_errs:
        for e in dep_errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    ordered, to_err = topological_order(steps)
    if to_err or not ordered:
        print(f"ERROR: {to_err or 'order failed'}", file=sys.stderr)
        return 1

    if driver_name != "noop":
        print(
            f"WARN: driver {driver_name!r} not implemented — using noop semantics",
            file=sys.stderr,
        )

    step_results, outcome = _noop_run(ordered, dry_run=dry_run)
    if outcome_override:
        outcome = outcome_override

    manifest = {
        "schema_version": 1,
        "task_id": task_id,
        "recorded_at": _utc_now_iso(),
        "kind": "semantic-csv-eval",
        "outcome": outcome,
        "csv_path": _relative_under_task(task_dir, csv_file),
        "step_count": len(ordered),
        "driver": driver_name,
        "dry_run": dry_run,
    }

    qa.mkdir(parents=True, exist_ok=True)
    manifest_path = qa / "semantic-eval-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    log_path = qa / "semantic-eval-run.log"
    _write_run_log(
        log_path,
        task_id=task_id,
        ordered=ordered,
        step_results=step_results,
        driver=driver_name,
        dry_run=dry_run,
    )

    print(f"Wrote {manifest_path}")
    print(f"Wrote {log_path}")
    print(f"outcome={outcome} steps={len(ordered)}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Run semantic automation CSV → manifest + log.")
    p.add_argument("--task-id", required=True)
    p.add_argument("--brain", default=None, help="Brain root (default: env or ~/forge/brain)")
    p.add_argument(
        "--csv",
        default=None,
        help="Override path to semantic-automation.csv (default: prds/<task-id>/qa/semantic-automation.csv)",
    )
    p.add_argument("--dry-run", action="store_true", help="Validate + yellow outcome (structure only)")
    p.add_argument(
        "--driver",
        default="noop",
        help="Host driver name (default noop — no CDP/ADB until wired)",
    )
    p.add_argument(
        "--outcome",
        default=None,
        choices=("pass", "fail", "yellow"),
        help="Override manifest outcome (optional)",
    )
    args = p.parse_args()
    try:
        task_id = sanitize_task_id(args.task_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    brain = Path(args.brain).expanduser() if args.brain else default_brain_root()
    task_dir = brain / "prds" / task_id
    if not task_dir.is_dir():
        print(f"ERROR: missing task dir {task_dir}", file=sys.stderr)
        return 1
    csv_path = Path(args.csv).expanduser() if args.csv else None
    return run_pipeline(
        task_dir=task_dir,
        task_id=task_id,
        csv_path=csv_path,
        dry_run=bool(args.dry_run),
        driver_name=args.driver,
        outcome_override=args.outcome,
    )


if __name__ == "__main__":
    raise SystemExit(main())
