#!/usr/bin/env python3
"""Benchmark scan performance/quality signals on synthetic fixtures."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from scan_forge.verify_smoke import _ROLE_SVC, _ROLE_UI, _git_init_and_commit, _write_smoke_fixtures


def _run_scan(
    cmd: list[str], cwd: Path, env: dict[str, str], run_dir: Path, label: str
) -> dict:
    try:
        subprocess.run(cmd, check=True, cwd=str(cwd), env=env, timeout=300)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label}: scan timed out after {exc.timeout}s") from exc
    run_json = run_dir / "run.json"
    try:
        return json.loads(run_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label}: invalid JSON in {run_json}: {exc}") from exc


def _compute_metrics() -> dict:
    run_dir = Path(tempfile.mkdtemp(prefix="forge_scan_bench_run."))
    brain = Path(tempfile.mkdtemp(prefix="forge_scan_bench_brain."))
    fixtures_parent = Path(tempfile.mkdtemp(prefix="forge_scan_bench_fixtures."))
    try:
        svc_repo, ui_repo = _write_smoke_fixtures(fixtures_parent)
        _git_init_and_commit(svc_repo, "bench fixtures svc")
        _git_init_and_commit(ui_repo, "bench fixtures ui")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "PYTHONPATH": str(TOOLS),
        }

        base_cmd = [
            sys.executable,
            "-m",
            "scan_forge",
            "--run-dir",
            str(run_dir),
            "--brain-codebase",
            str(brain),
            "--skip-phase57",
            "--repos",
            f"{_ROLE_SVC}:{svc_repo}",
            f"{_ROLE_UI}:{ui_repo}",
        ]
        full_meta = _run_scan(base_cmd, ROOT, env, run_dir, "full")

        inc_cmd = [*base_cmd, "--incremental"]
        inc_warm = _run_scan(inc_cmd, ROOT, env, run_dir, "incremental_warm")
        inc_nochange = _run_scan(inc_cmd, ROOT, env, run_dir, "incremental_nochange")

        # small tracked change
        routes_ts = svc_repo / "src" / "routes.ts"
        routes_ts.write_text(routes_ts.read_text(encoding="utf-8") + "\n// bench touch\n", encoding="utf-8")
        inc_small_change = _run_scan(inc_cmd, ROOT, env, run_dir, "incremental_small_change")

        metrics = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runs": {
                "full": full_meta,
                "incremental_warm": inc_warm,
                "incremental_nochange": inc_nochange,
                "incremental_small_change": inc_small_change,
            },
        }
        full_ms = int(full_meta.get("total_elapsed_ms", 0) or 0)
        nochange_ms = int(inc_nochange.get("total_elapsed_ms", 0) or 0)
        small_ms = int(inc_small_change.get("total_elapsed_ms", 0) or 0)
        changed_n = int((inc_small_change.get("incremental") or {}).get("changed_files_n", 0) or 0)
        gates = {
            "precision_runtime_improves_nochange": bool(full_ms > 0 and 0 < nochange_ms < full_ms),
            "nochange_skips_scan_phases": bool((inc_nochange.get("incremental") or {}).get("skipped_scan_phases")),
            "small_change_detected": bool(changed_n >= 1),
            "small_change_not_skipped": bool(not (inc_small_change.get("incremental") or {}).get("skipped_scan_phases", False)),
        }
        metrics["summary"] = {
            "full_ms": full_ms,
            "incremental_nochange_ms": nochange_ms,
            "incremental_small_change_ms": small_ms,
            "small_change_changed_files_n": changed_n,
        }
        metrics["gates"] = gates
        return metrics
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(brain, ignore_errors=True)
        shutil.rmtree(fixtures_parent, ignore_errors=True)


def _write_markdown(path: Path, doc: dict) -> None:
    s = doc.get("summary") or {}
    g = doc.get("gates") or {}
    lines = [
        "# Scan benchmark",
        "",
        f"- generated_at: `{doc.get('generated_at')}`",
        f"- full_ms: {s.get('full_ms')}",
        f"- incremental_nochange_ms: {s.get('incremental_nochange_ms')}",
        f"- incremental_small_change_ms: {s.get('incremental_small_change_ms')}",
        f"- small_change_changed_files_n: {s.get('small_change_changed_files_n')}",
        "",
        "## Gates",
        "",
    ]
    for k, v in sorted(g.items()):
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run synthetic scan benchmark and emit gate report.")
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when any gate fails.")
    args = ap.parse_args(argv)

    doc = _compute_metrics()
    output_json = args.output_json or Path(tempfile.mkdtemp(prefix="forge_scan_bench_out.")) / "scan_bench.latest.json"
    output_md = args.output_md or output_json.with_suffix(".md")
    output_json.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    _write_markdown(output_md, doc)
    print(f"scan_bench: wrote {output_json}")
    print(f"scan_bench: wrote {output_md}")

    if args.strict and not all(bool(v) for v in (doc.get("gates") or {}).values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
