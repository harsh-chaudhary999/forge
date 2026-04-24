"""
Portable phase ledger: append-only JSONL with optional SHA256 artifact attestation.

Editor-agnostic: any shell or automation can append rows via append_phase_ledger.py;
verify_forge_task.py can validate structure and (optionally) re-hash files.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_NAME = "phase-ledger.jsonl"
CURRENT_SCHEMA = 1

RELPATH_SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/\-]*$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_entry(
    task_id: str,
    phase_marker: str,
    artifact_relpaths: list[str],
    task_dir: Path,
    note: str | None = None,
) -> dict[str, Any]:
    if not phase_marker.strip():
        raise ValueError("phase_marker must be non-empty")
    artifacts: list[dict[str, str]] = []
    for rel in artifact_relpaths or []:
        rel = rel.strip().lstrip("/")
        if not rel or ".." in rel or rel.startswith("/"):
            raise ValueError(f"unsafe artifact relpath: {rel!r}")
        if not RELPATH_SAFE.match(rel):
            raise ValueError(f"artifact relpath must match safe pattern: {rel!r}")
        p = task_dir / rel
        if not p.is_file():
            raise FileNotFoundError(f"artifact not a file: {p}")
        artifacts.append({"relpath": rel, "sha256": file_sha256(p)})
    rec: dict[str, Any] = {
        "schema_version": CURRENT_SCHEMA,
        "task_id": task_id,
        "phase_marker": phase_marker.strip(),
        "recorded_at": _utc_now_iso(),
        "artifacts": artifacts,
    }
    if note:
        rec["note"] = str(note)[:2000]
    return rec


def append_entry(task_dir: Path, entry: dict[str, Any]) -> Path:
    path = task_dir / LEDGER_NAME
    line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    return path


def _resolved_artifact_path(task_dir: Path, rel: str) -> tuple[Path | None, str | None]:
    """Resolve *rel* under *task_dir* with the same safety rules as build_entry.

    Returns (path, None) on success, or (None, error_message) if *rel* is unsafe
    or escapes *task_dir* (e.g. via ``..`` or symlinks).
    """
    rel = str(rel).strip().lstrip("/")
    if not rel or ".." in rel or rel.startswith("/"):
        return None, f"unsafe artifact relpath: {rel!r}"
    if not RELPATH_SAFE.match(rel):
        return None, f"artifact relpath must match safe pattern: {rel!r}"
    raw = task_dir / rel
    try:
        fp = raw.resolve()
        td = task_dir.resolve()
    except OSError as exc:
        return None, f"cannot resolve path: {exc}"
    try:
        fp.relative_to(td)
    except ValueError:
        return None, f"artifact path escapes task_dir: {rel!r}"
    return fp, None


def verify_ledger(
    task_dir: Path,
    *,
    verify_hashes: bool,
    task_id_expected: str | None = None,
) -> list[str]:
    """Return human-readable errors; empty means OK."""
    path = task_dir / LEDGER_NAME
    if not path.is_file():
        return []
    errs: list[str] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            obj: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            errs.append(f"{LEDGER_NAME} line {i}: invalid JSON ({exc})")
            continue
        if not isinstance(obj, dict):
            errs.append(f"{LEDGER_NAME} line {i}: root must be an object")
            continue
        if obj.get("schema_version") != CURRENT_SCHEMA:
            errs.append(
                f"{LEDGER_NAME} line {i}: unsupported or missing schema_version "
                f"(expected {CURRENT_SCHEMA})"
            )
        tid = obj.get("task_id")
        if task_id_expected and tid != task_id_expected:
            errs.append(
                f"{LEDGER_NAME} line {i}: task_id {tid!r} does not match expected {task_id_expected!r}"
            )
        if not obj.get("phase_marker"):
            errs.append(f"{LEDGER_NAME} line {i}: missing phase_marker")
        if not obj.get("recorded_at"):
            errs.append(f"{LEDGER_NAME} line {i}: missing recorded_at")
        arts = obj.get("artifacts")
        if arts is None:
            errs.append(f"{LEDGER_NAME} line {i}: missing artifacts (use [] if none)")
            continue
        if not isinstance(arts, list):
            errs.append(f"{LEDGER_NAME} line {i}: artifacts must be a list")
            continue
        for j, a in enumerate(arts):
            if not isinstance(a, dict):
                errs.append(f"{LEDGER_NAME} line {i} artifacts[{j}]: must be object")
                continue
            rel = a.get("relpath")
            sha = a.get("sha256")
            if not rel or not sha:
                errs.append(f"{LEDGER_NAME} line {i} artifacts[{j}]: need relpath and sha256")
                continue
            fp, unsafe = _resolved_artifact_path(task_dir, str(rel))
            if unsafe:
                errs.append(f"{LEDGER_NAME} line {i} artifacts[{j}]: {unsafe}")
                continue
            assert fp is not None
            if verify_hashes:
                if not fp.is_file():
                    errs.append(f"{LEDGER_NAME} line {i}: missing file {fp}")
                    continue
                try:
                    actual = file_sha256(fp)
                except OSError as exc:
                    errs.append(f"{LEDGER_NAME} line {i}: cannot hash {fp}: {exc}")
                    continue
                if actual.lower() != str(sha).lower():
                    errs.append(
                        f"{LEDGER_NAME} line {i}: sha256 mismatch for {rel!r} "
                        f"(ledger={sha[:12]}… disk={actual[:12]}…)"
                    )
    return errs


__all__ = [
    "LEDGER_NAME",
    "append_entry",
    "build_entry",
    "file_sha256",
    "verify_ledger",
]
