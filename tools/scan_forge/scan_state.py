"""Incremental scan state: previous heads, changed paths, and file blob snapshots."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from . import fs_util, log

STATE_FILE = ".forge_scan_file_state.json"

_UI_SUFFIXES = {".html", ".htm", ".vue", ".svelte"}
_OPENAPI_SUFFIXES = {".json", ".yaml", ".yml"}
_OPENAPI_NAMES = ("openapi", "swagger")


def _git_out(repo: Path, args: list[str]) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def _is_scan_relevant(rel_posix: str) -> bool:
    rel = rel_posix.strip().replace("\\", "/")
    if not rel:
        return False
    if fs_util._rel_has_excluded_dir(rel):
        return False
    name = Path(rel).name
    low = name.lower()
    if any(low.endswith(suf) for suf in fs_util.SOURCE_SUFFIXES):
        return True
    if any(low.endswith(suf) for suf in _UI_SUFFIXES):
        return True
    if any(low.endswith(suf) for suf in _OPENAPI_SUFFIXES) and any(k in low for k in _OPENAPI_NAMES):
        return True
    return False


def _tracked_blobs(repo: Path) -> dict[str, str]:
    out = _git_out(repo, ["ls-files", "-s"])
    if out is None:
        return {}
    blobs: dict[str, str] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        # 100644 <sha> 0\tpath
        if "\t" not in line:
            continue
        left, rel = line.split("\t", 1)
        parts = left.split()
        if len(parts) < 3:
            continue
        sha = parts[1].strip()
        rel = rel.strip().replace("\\", "/")
        if not _is_scan_relevant(rel):
            continue
        blobs[rel] = sha
    return blobs


def _untracked_relevant(repo: Path) -> list[str]:
    out = _git_out(repo, ["ls-files", "--others", "--exclude-standard"])
    if out is None:
        return []
    rels: list[str] = []
    for line in out.splitlines():
        rel = line.strip().replace("\\", "/")
        if _is_scan_relevant(rel):
            rels.append(rel)
    rels.sort()
    return rels


def _git_changed_worktree(repo: Path) -> list[str] | None:
    """Tracked file changes in working tree/index (staged + unstaged)."""
    out = _git_out(repo, ["status", "--porcelain"])
    if out is None:
        return None
    rels: set[str] = set()
    for line in out.splitlines():
        if not line.strip() or len(line) < 4:
            continue
        rel = line[3:].strip().replace("\\", "/")
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1].strip()
        if _is_scan_relevant(rel):
            rels.add(rel)
    return sorted(rels)


def load_previous_heads(brain_codebase: Path) -> dict[str, str]:
    path = brain_codebase.resolve() / STATE_FILE
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    roles = doc.get("roles")
    if not isinstance(roles, dict):
        return {}
    out: dict[str, str] = {}
    for role, val in roles.items():
        if not isinstance(val, dict):
            continue
        head = val.get("head")
        if isinstance(head, str) and head:
            out[str(role)] = head
    return out


def detect_changed_paths(repo: Path, previous_head: str | None) -> tuple[list[str] | None, str]:
    """Return (changed_paths or None-for-full, reason)."""
    repo = repo.resolve()
    if not previous_head:
        return None, "no_previous_head"
    head_now = _git_out(repo, ["rev-parse", "HEAD"])
    if head_now is None:
        return None, "git_head_unavailable"
    head_now = head_now.strip()
    if not head_now:
        return None, "git_head_unavailable"
    # Validate old head is reachable in this repo.
    valid_old = _git_out(repo, ["cat-file", "-e", f"{previous_head}^{{commit}}"])
    if valid_old is None:
        return None, "previous_head_missing"
    dirty = _git_changed_worktree(repo)
    dirty = dirty if dirty is not None else []
    if previous_head == head_now:
        return sorted(set(dirty + _untracked_relevant(repo))), "same_head_worktree"
    raw = _git_out(repo, ["diff", "--name-only", previous_head, head_now])
    if raw is None:
        return None, "git_diff_failed"
    changed: list[str] = []
    for line in raw.splitlines():
        rel = line.strip().replace("\\", "/")
        if _is_scan_relevant(rel):
            changed.append(rel)
    changed = sorted(set(changed + dirty + _untracked_relevant(repo)))
    return changed, "git_diff_plus_worktree"


def write_changed_paths(run_dir: Path, changed_by_role: dict[str, list[str]]) -> Path:
    out = run_dir.resolve() / "changed_paths.txt"
    rows: list[str] = []
    for role in sorted(changed_by_role.keys()):
        for rel in changed_by_role[role]:
            rows.append(f"{role}\t{rel}")
    out.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return out


def write_state_file(
    brain_codebase: Path,
    repos: list[tuple[str, Path]],
    changed_by_role: dict[str, list[str]],
    incremental_enabled: bool,
) -> Path:
    path = brain_codebase.resolve() / STATE_FILE
    doc: dict[str, Any] = {
        "forge_scan_file_state_version": 1,
        "incremental_enabled": bool(incremental_enabled),
        "roles": {},
    }
    for role, repo in repos:
        repo = repo.resolve()
        head = (_git_out(repo, ["rev-parse", "HEAD"]) or "").strip() or None
        tree = (_git_out(repo, ["rev-parse", "HEAD^{tree}"]) or "").strip() or None
        blobs = _tracked_blobs(repo)
        untracked = _untracked_relevant(repo)
        doc["roles"][role] = {
            "path": str(repo),
            "head": head,
            "tree": tree,
            "changed_paths_count": len(changed_by_role.get(role, [])),
            "tracked_blob_count": len(blobs),
            "tracked_blobs": blobs,
            "untracked_relevant": untracked,
        }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    log.log_step(f"scan_state written path={path}")
    return path
