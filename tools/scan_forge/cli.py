"""CLI and ``run_scan`` orchestrator; sets ``FORGE_SCAN_TMP`` / ``FORGE_SCAN_RUN_DIR``."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(raw: str, root: Path) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (root / p).resolve()
    else:
        p = p.resolve()
    if not p.is_dir():
        raise SystemExit(f"Not a directory: {p}")
    return p


def _parse_repo(spec: str, root: Path) -> tuple[str, Path]:
    if ":" in spec:
        role, path_s = spec.split(":", 1)
        role = role.strip()
        path_s = path_s.strip()
        return role, _resolve_path(path_s, root)
    path = _resolve_path(spec.strip(), root)
    role = path.name.replace(".", "-")
    return role, path


def run_scan(
    brain: Path,
    repos: list[tuple[str, Path]],
    run_dir: Path,
    product_md: Path | None,
    skip_phase57: bool,
    do_cleanup: bool,
    phase57_write_report: bool,
) -> dict:
    from . import (
        cleanup,
        openapi_schema_digest,
        phase1,
        phase35,
        phase4,
        phase5,
        phase56,
        phase57,
        repo_docs_mirror,
        scan_graph_export,
        scan_manifest,
        scan_paths,
        scan_summary,
        topology_reader,
        validate_roles,
    )

    run_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["FORGE_SCAN_RUN_DIR"] = str(run_dir)
    env["FORGE_SCAN_TMP"] = str(run_dir)
    os.environ["FORGE_SCAN_TMP"] = str(run_dir)
    os.environ["FORGE_SCAN_RUN_DIR"] = str(run_dir)

    meta: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "brain_codebase": str(brain),
        "repos": [{"role": r, "path": str(p)} for r, p in repos],
        "orchestrator": "scan_forge",
        "phase_timings_ms": {},
    }
    timings: dict[str, int] = meta["phase_timings_ms"]
    wall0 = time.perf_counter()

    topology = None
    if product_md is not None and product_md.is_file():
        validate_roles.run_validate_roles(product_md)
        topology = topology_reader.read_topology(product_md)

    for i, (role, path) in enumerate(repos):
        role_dir = scan_paths.role_scan_dir(run_dir, role)
        t0 = time.perf_counter()
        phase1.run_phase1(path, role_dir)
        timings[f"phase1:{role}"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        phase35.run_phase35(path, role_dir, run_dir, append_routes=(i > 0))
        timings[f"phase35:{role}"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        phase4.run_phase4(path, brain, role, role_dir, run_dir)
        timings[f"phase4:{role}"] = int((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    openapi_schema_digest.write_digest(brain, repos)
    timings["openapi_schema_digest"] = int((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    phase5.run_phase5([p for _, p in repos], run_dir, topology=topology)
    timings["phase5"] = int((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    phase56.run_phase56(brain, run_dir, topology=topology)
    timings["phase56"] = int((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    scan_graph_export.write_graph_json(brain)
    timings["graph_export"] = int((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    scan_summary.write_scan_summary(brain, repos)
    timings["scan_summary"] = int((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    scan_manifest.write_manifest(brain, repos)
    timings["scan_manifest"] = int((time.perf_counter() - t0) * 1000)

    if not skip_phase57:
        t0 = time.perf_counter()
        phase57.run_phase57(brain, write_report=phase57_write_report)
        timings["phase57"] = int((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    rd = repo_docs_mirror.mirror_repo_docs(brain, repos)
    timings["repo_docs_mirror"] = int((time.perf_counter() - t0) * 1000)
    meta["repo_docs_mirror"] = {
        "enabled": rd.get("enabled"),
        "snapshot_files": len(rd.get("files", [])),
        "index_only_rows": len(rd.get("index_only", [])),
        "skipped": len(rd.get("skipped", [])),
        "total_bytes": rd.get("total_bytes", 0),
    }

    if do_cleanup:
        cleanup.run_cleanup(run_dir)

    meta["status"] = "ok"
    meta["finished_at"] = datetime.now(timezone.utc).isoformat()
    meta["total_elapsed_ms"] = int((time.perf_counter() - wall0) * 1000)
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    root = _repo_root()
    ap = argparse.ArgumentParser(description="Forge scan-codebase (Python phases).")
    ap.add_argument("--brain-codebase", type=Path, required=True)
    ap.add_argument("--repos", nargs="+", required=True)
    ap.add_argument("--run-dir", type=Path, default=None)
    ap.add_argument("--keep-run-dir", action="store_true")
    ap.add_argument("--product-md", type=Path, default=None)
    ap.add_argument("--skip-phase57", action="store_true")
    ap.add_argument("--phase57-write-report", action="store_true")
    ap.add_argument("--cleanup", action="store_true")
    args = ap.parse_args(argv)

    brain = args.brain_codebase.expanduser()
    if not brain.is_absolute():
        brain = (root / brain).resolve()
    else:
        brain = brain.resolve()
    if not brain.is_dir():
        raise SystemExit(f"--brain-codebase must be a directory: {brain}")

    repos = [_parse_repo(s, root) for s in args.repos]

    if args.run_dir is not None:
        run_dir = args.run_dir.expanduser()
        if not run_dir.is_absolute():
            run_dir = (root / run_dir).resolve()
        else:
            run_dir = run_dir.resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = Path(tempfile.mkdtemp(prefix="forge_scan_run_", dir=None))

    pmd = args.product_md
    if pmd is not None:
        pmd = pmd.expanduser()
        if not pmd.is_absolute():
            pmd = (root / pmd).resolve()
        else:
            pmd = pmd.resolve()
    else:
        pmd = None

    try:
        meta = run_scan(
            brain,
            repos,
            run_dir,
            pmd,
            skip_phase57=args.skip_phase57,
            do_cleanup=args.cleanup,
            phase57_write_report=args.phase57_write_report,
        )
    except SystemExit:
        raise
    except Exception as exc:
        meta = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "run_dir": str(run_dir),
            "brain_codebase": str(brain),
            "repos": [{"role": r, "path": str(p)} for r, p in repos],
            "status": "error",
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "phase_timings_ms": {},
        }
        (run_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        raise

    status = str(meta.get("status", "ok"))
    if args.keep_run_dir:
        print(json.dumps({"run_dir": str(run_dir), "status": status}, indent=2))
    else:
        print(str(run_dir))


if __name__ == "__main__":
    main()
