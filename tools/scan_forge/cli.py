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
    incremental: bool,
) -> dict:
    from . import (
        cleanup,
        codebase_index,
        edge_store,
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
        scan_state,
        scan_paths,
        scan_summary,
        topology_reader,
        validate_roles,
        verify_brain_codebase,
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

    changed_by_role: dict[str, list[str]] = {}
    role_scan_mode: dict[str, str] = {}
    incremental_reasons: dict[str, str] = {}
    previous_heads = scan_state.load_previous_heads(brain) if incremental else {}
    if incremental:
        for role, path in repos:
            changed, reason = scan_state.detect_changed_paths(path, previous_heads.get(role))
            incremental_reasons[role] = reason
            if changed is None:
                role_scan_mode[role] = "full_fallback"
                changed_by_role[role] = []
            elif not changed:
                role_scan_mode[role] = "skip_no_changes"
                changed_by_role[role] = []
            else:
                role_scan_mode[role] = "full_changed"
                changed_by_role[role] = changed
        changed_file = scan_state.write_changed_paths(run_dir, changed_by_role)
        meta["incremental"] = {
            "enabled": True,
            "role_mode": role_scan_mode,
            "reasons": incremental_reasons,
            "changed_paths_file": str(changed_file),
            "changed_files_n": sum(len(v) for v in changed_by_role.values()),
        }
        meta["incremental"]["change_profile"] = scan_state.summarize_changed_paths(changed_by_role)
    else:
        for role, _path in repos:
            role_scan_mode[role] = "full"
            changed_by_role[role] = []
        meta["incremental"] = {
            "enabled": False,
            "role_mode": role_scan_mode,
            "changed_files_n": 0,
        }

    any_role_scanned = False
    scanned_idx = 0
    for role, path in repos:
        if role_scan_mode.get(role) == "skip_no_changes":
            continue
        role_dir = scan_paths.role_scan_dir(run_dir, role)
        any_role_scanned = True
        t0 = time.perf_counter()
        phase1.run_phase1(path, role_dir)
        timings[f"phase1:{role}"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        phase35.run_phase35(path, role_dir, run_dir, append_routes=(scanned_idx > 0))
        timings[f"phase35:{role}"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        phase4.run_phase4(path, brain, role, role_dir, run_dir)
        timings[f"phase4:{role}"] = int((time.perf_counter() - t0) * 1000)
        scanned_idx += 1

    run_phase5_stack = True
    if incremental and any_role_scanned:
        if any(m == "full_fallback" for m in role_scan_mode.values()):
            run_phase5_stack = True
            meta["incremental"]["phase5_56_mode"] = "run_full_fallback"
            meta["incremental"]["phase5_56_reason"] = (
                "fallback_role_detected; cannot trust prior state"
            )
        else:
            prof = meta.get("incremental", {}).get("change_profile")
            if isinstance(prof, dict) and prof.get("phase5_required") is False:
                run_phase5_stack = False
                meta["incremental"]["phase5_56_mode"] = "skipped_by_profile"
                meta["incremental"]["phase5_56_reason"] = (
                    "no_phase5_inputs_detected (heuristic); keeping previous cross-repo edges"
                )
            else:
                meta["incremental"]["phase5_56_mode"] = "run_full"
                meta["incremental"]["phase5_56_reason"] = "phase5_inputs_changed_or_uncertain"

    if any_role_scanned and run_phase5_stack:
        t0 = time.perf_counter()
        openapi_schema_digest.write_digest(brain, repos)
        timings["openapi_schema_digest"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        phase5.run_phase5([p for _, p in repos], run_dir, topology=topology)
        timings["phase5"] = int((time.perf_counter() - t0) * 1000)
        imp_tsv = run_dir / "forge_scan_ast_import_edges.tsv"
        if imp_tsv.is_file():
            (brain / "forge_scan_ast_import_edges.tsv").write_text(
                imp_tsv.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
        t0 = time.perf_counter()
        phase56.run_phase56(brain, run_dir, topology=topology)
        timings["phase56"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        scan_graph_export.write_graph_json(brain)
        timings["graph_export"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        edge_store.write_edge_store(brain)
        timings["edge_store"] = int((time.perf_counter() - t0) * 1000)
    elif any_role_scanned:
        meta["incremental"]["skipped_phase5_stack"] = True
    else:
        meta["incremental"]["skipped_scan_phases"] = True

    t0 = time.perf_counter()
    scan_summary.write_scan_summary(brain, repos)
    timings["scan_summary"] = int((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    scan_manifest.write_manifest(
        brain,
        repos,
        incremental_enabled=incremental,
        changed_by_role=changed_by_role,
    )
    timings["scan_manifest"] = int((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    scan_state.write_state_file(
        brain,
        repos,
        changed_by_role=changed_by_role,
        incremental_enabled=incremental,
    )
    timings["scan_state"] = int((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    codebase_index.write_codebase_index_md(brain, repos)
    timings["codebase_index"] = int((time.perf_counter() - t0) * 1000)

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

    skip_verify = os.environ.get("FORGE_SCAN_SKIP_VERIFY", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not skip_verify:
        t0 = time.perf_counter()
        v_code, v_msgs = verify_brain_codebase.verify_brain_codebase_with_retries(brain)
        timings["verify_scan_outputs_ms"] = int((time.perf_counter() - t0) * 1000)
        meta["verify_scan_outputs"] = {
            "exit_code": v_code,
            "messages": v_msgs,
            "retries": 3,
        }
        if v_code != 0:
            meta["status"] = "verify_failed"
            meta["finished_at"] = datetime.now(timezone.utc).isoformat()
            meta["total_elapsed_ms"] = int((time.perf_counter() - wall0) * 1000)
            (run_dir / "run.json").write_text(
                json.dumps(meta, indent=2) + "\n",
                encoding="utf-8",
            )
            return meta

    if do_cleanup:
        cleanup.run_cleanup(run_dir)

    meta["status"] = "ok"
    meta["finished_at"] = datetime.now(timezone.utc).isoformat()
    meta["total_elapsed_ms"] = int((time.perf_counter() - wall0) * 1000)
    if skip_verify:
        meta["verify_scan_outputs"] = {
            "exit_code": None,
            "skipped": True,
            "reason": "FORGE_SCAN_SKIP_VERIFY",
        }
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
    ap.add_argument("--incremental", action="store_true")
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

    env_incremental = os.environ.get("FORGE_SCAN_INCREMENTAL", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    try:
        meta = run_scan(
            brain,
            repos,
            run_dir,
            pmd,
            skip_phase57=args.skip_phase57,
            do_cleanup=args.cleanup,
            phase57_write_report=args.phase57_write_report,
            incremental=bool(args.incremental or env_incremental),
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
    if status == "verify_failed":
        detail = meta.get("verify_scan_outputs") or {}
        print(json.dumps(detail, indent=2), file=sys.stderr)
        msgs = detail.get("messages") or []
        if isinstance(msgs, list):
            print("\n".join(str(m) for m in msgs), file=sys.stderr)
        raise SystemExit(
            "Post-scan integrity verify failed (brain tree incomplete). "
            "Fix paths or re-run; see messages above. "
            "Emergency only: FORGE_SCAN_SKIP_VERIFY=1",
        )
    if args.keep_run_dir:
        print(json.dumps({"run_dir": str(run_dir), "status": status}, indent=2))
    else:
        print(str(run_dir))


if __name__ == "__main__":
    main()
