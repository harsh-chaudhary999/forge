"""Mirror curated repository Markdown + OpenAPI specs into ``brain_codebase/repo-docs/``.

Produces verbatim byte-identical snapshots with ``content_sha256`` provenance in
``index.json``. Incremental: unchanged files (same SHA) are not re-copied.

Per-repo optional policy (``forge-scan-docs.policy.yaml`` / ``.forge-repo-docs.yaml``):
  ``deny_path_contains``      — never copy or index
  ``index_only_path_contains`` — appear in index.json but no file copy
  ``allow_extra_path_contains`` — include beyond the default set
  ``max_files``               — per-repo file cap (default: FORGE_REPO_DOCS_MAX_FILES)
  ``max_bytes_per_file``      — per-repo size cap (default: FORGE_REPO_DOCS_MAX_BYTES)

Caps are per-repo, not a global minimum across all repos.

Disable entirely: ``FORGE_REPO_DOCS_MIRROR=0``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import fs_util, log, repo_docs_policy

_ROOT_DOC_NAMES = frozenset(
    {
        "readme.md",
        "contributing.md",
        "changelog.md",
        "security.md",
        "architecture.md",
        "onboarding.md",
        "agents.md",
        "claude.md",
        "code_of_conduct.md",
        "governance.md",
        "gemini.md",
    },
)

_OPENAPI_NAMES = frozenset({"openapi", "swagger"})

_SKIP_SUBSTR = (
    "/.git/",
    "/node_modules/",
    "/__pycache__/",
    "/.obsidian/",
    "/.github/ISSUE_TEMPLATE",
    "/.github/PULL_REQUEST_TEMPLATE",
)


def _git_head(repo: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return (out.strip() or "unknown")[:40]
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _priority(rel_posix: str) -> tuple[int, str]:
    r = rel_posix.replace("\\", "/").lower()
    if "/docs/" in f"/{r}/" or r.startswith("docs/"):
        return (0, rel_posix)
    if "/adr/" in f"/{r}/" or r.startswith("adr/"):
        return (1, rel_posix)
    if "/doc/" in f"/{r}/" or r.startswith("doc/"):
        return (2, rel_posix)
    if "/guides/" in f"/{r}/" or r.startswith("guides/"):
        return (3, rel_posix)
    if "/rfc/" in f"/{r}/" or r.startswith("rfc/"):
        return (4, rel_posix)
    parts = r.split("/")
    if len(parts) == 1:
        return (5, rel_posix)
    if parts and parts[-1] in _ROOT_DOC_NAMES:
        return (6, rel_posix)
    return (9, rel_posix)


def _is_openapi_spec(rel_posix: str) -> bool:
    """True for openapi*.yaml/json and swagger*.yaml/json files."""
    base = rel_posix.replace("\\", "/").rsplit("/", 1)[-1].lower()
    stem = base.rsplit(".", 1)[0]
    ext = base.rsplit(".", 1)[-1] if "." in base else ""
    return any(stem.startswith(n) for n in _OPENAPI_NAMES) and ext in ("yaml", "yml", "json")


def _should_mirror_default(rel_posix: str) -> bool:
    r = rel_posix.replace("\\", "/")
    rl = r.lower()
    if any(s in rl for s in _SKIP_SUBSTR):
        return False
    if _is_openapi_spec(r):
        return True
    if not rl.endswith(".md"):
        return False
    parts = r.split("/")
    base = parts[-1].lower() if parts else ""
    for prefix in ("docs/", "doc/", "guides/", "adr/", "rfc/"):
        if f"/{rl}/".startswith(f"/{prefix}") or f"/{rl}".startswith(f"/{prefix}"):
            return True
        if rl.startswith(prefix):
            return True
    if len(parts) == 1 and base.endswith(".md"):
        return True
    if base in _ROOT_DOC_NAMES:
        return True
    return False


def _include_path(rel: str, pol: repo_docs_policy.RepoDocsPolicy) -> bool:
    if _should_mirror_default(rel):
        return True
    return repo_docs_policy.path_extra_allowed(rel, pol.allow_extra_path_contains)


@dataclass
class _WorkItem:
    pri: tuple[int, str]
    role_idx: int
    role: str
    rel: str
    src: Path
    mode: str  # "snapshot" | "index_only"


def mirror_repo_docs(brain_codebase: Path, repos: list[tuple[str, Path]]) -> dict[str, Any]:
    """Copy curated docs from each scanned repo into ``brain_codebase/repo-docs/``."""
    if os.environ.get("FORGE_REPO_DOCS_MIRROR", "1").strip() in ("0", "false", "no"):
        log.log_step("repo_docs_mirror skipped FORGE_REPO_DOCS_MIRROR=0")
        return {"enabled": False, "files": [], "index_only": [], "skipped": [], "total_bytes": 0}

    brain_codebase = brain_codebase.resolve()
    policies = {role: repo_docs_policy.load_repo_docs_policy(path) for role, path in repos}
    root = brain_codebase / "repo-docs"
    root.mkdir(parents=True, exist_ok=True)

    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head_by_role: dict[str, str] = {role: _git_head(path.resolve()) for role, path in repos}

    # Load existing index to enable incremental skip
    existing_index: dict[str, str] = {}  # brain_relative -> content_sha256
    idx_path = root / "index.json"
    if idx_path.is_file():
        try:
            prev = json.loads(idx_path.read_text(encoding="utf-8"))
            for e in prev.get("files", []):
                if e.get("brain_relative") and e.get("content_sha256"):
                    existing_index[e["brain_relative"]] = e["content_sha256"]
        except (OSError, json.JSONDecodeError):
            pass

    # Collect candidates per repo, applying per-repo policy independently
    all_written: list[dict[str, Any]] = []
    all_index_only: list[dict[str, Any]] = []
    all_skipped: list[dict[str, Any]] = []
    total_bytes = 0

    for role_idx, (role, repo) in enumerate(repos):
        repo = repo.resolve()
        pol = policies[role]
        head = head_by_role[role]

        items: list[_WorkItem] = []
        repo_skipped: list[dict[str, Any]] = []

        for p in fs_util.iter_files_under(repo):
            if not p.is_file():
                continue
            try:
                rel = p.relative_to(repo).as_posix()
            except ValueError:
                continue
            if not _include_path(rel, pol):
                continue
            if repo_docs_policy.path_denied(rel, pol.deny_path_contains):
                repo_skipped.append({"role": role, "source_relative": rel, "reason": "deny_policy"})
                continue
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            if repo_docs_policy.path_index_only(rel, pol.index_only_path_contains):
                items.append(_WorkItem(_priority(rel), role_idx, role, rel, p, "index_only"))
                continue
            if sz > pol.max_bytes_per_file:
                repo_skipped.append({"role": role, "source_relative": rel, "reason": "too_large", "bytes": sz})
                continue
            items.append(_WorkItem(_priority(rel), role_idx, role, rel, p, "snapshot"))

        items.sort(key=lambda w: (w.pri[0], w.pri[1]))
        all_skipped.extend(repo_skipped)

        repo_file_count = 0
        for w in items:
            if repo_file_count >= pol.max_files:
                all_skipped.append({"role": role, "source_relative": w.rel, "reason": "per_repo_cap"})
                continue

            if w.mode == "index_only":
                try:
                    sz = w.src.stat().st_size
                except OSError:
                    sz = -1
                all_index_only.append({
                    "role": role,
                    "source_relative": w.rel,
                    "source_head": head,
                    "bytes": sz,
                    "tier": "index_only",
                    "scanned_at": scanned_at,
                })
                repo_file_count += 1
                continue

            data = w.src.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            dest = root / role / Path(w.rel)
            brain_rel = str(dest.relative_to(brain_codebase)).replace("\\", "/")

            # Incremental: skip write if content unchanged
            if existing_index.get(brain_rel) == digest and dest.is_file():
                log.log_step(f"repo_docs_mirror unchanged={brain_rel}")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

            b = len(data)
            total_bytes += b
            all_written.append({
                "role": role,
                "source_relative": w.rel,
                "brain_relative": brain_rel,
                "source_head": head,
                "bytes": b,
                "content_sha256": digest,
                "tier": "snapshot",
                "scanned_at": scanned_at,
            })
            repo_file_count += 1

    # Remove stale brain files no longer in any repo
    current_brain_rels = {e["brain_relative"] for e in all_written}
    for old_rel in list(existing_index):
        if old_rel not in current_brain_rels:
            stale = brain_codebase / old_rel
            if stale.is_file():
                stale.unlink(missing_ok=True)
                log.log_step(f"repo_docs_mirror removed stale={old_rel}")

    policies_used = [
        {"role": r, "policy_path": policies[r].policy_path, "max_bytes_per_file": policies[r].max_bytes_per_file, "max_files": policies[r].max_files}
        for r, _ in repos
    ]

    # Write README
    (root / "README.md").write_text(
        "\n".join([
            "# Repo documentation mirror",
            "",
            "Verbatim **snapshots** of curated Markdown and OpenAPI specs, plus **index-only** rows for policy-excluded paths.",
            "See **`index.json`** for `content_sha256`, tiers, and skips. **`INDEX.md`** has a human-readable table.",
            "",
            "Default inclusion: `docs/**`, `doc/**`, `guides/**`, `adr/**`, `rfc/**`, root `*.md`, `openapi*.yaml/json`, `swagger*.yaml/json`.",
            "Optional per-repo policy: `forge-scan-docs.policy.yaml` — keys: `deny_path_contains`, `index_only_path_contains`, `allow_extra_path_contains`, `max_files`, `max_bytes_per_file`.",
            "",
            "Disable: `FORGE_REPO_DOCS_MIRROR=0`. Caps: `FORGE_REPO_DOCS_MAX_FILES`, `FORGE_REPO_DOCS_MAX_BYTES`.",
            "",
            f"Written at: {scanned_at}",
            "",
        ]) + "\n",
        encoding="utf-8",
    )

    # Write index.json
    doc: dict[str, Any] = {
        "forge_repo_docs_mirror_version": 2,
        "written_at": scanned_at,
        "verbatim_snapshot_bytes": True,
        "policies_used": policies_used,
        "files": all_written,
        "index_only": all_index_only,
        "skipped": all_skipped,
        "totals": {
            "snapshot_files": len(all_written),
            "index_only_rows": len(all_index_only),
            "skipped": len(all_skipped),
            "snapshot_bytes": total_bytes,
        },
    }
    idx_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    # Write INDEX.md
    lines = [
        "# Repo docs mirror index",
        "",
        f"_v2 — {scanned_at} — snapshots are byte-identical; SHA-256 listed below._",
        "",
        "## Snapshots",
        "",
        "| Role | Source | Brain path | HEAD | Bytes | SHA-256 (first 12) |",
        "|---|---|---|---|---:|---|",
    ]
    for e in all_written:
        head = e["source_head"]
        short = head[:12] + "…" if len(head) > 12 else head
        sha = e.get("content_sha256", "")[:12]
        lines.append(
            f"| `{e['role']}` | `{e['source_relative']}` | `{e['brain_relative']}` | `{short}` | {e['bytes']} | `{sha}…` |"
        )
    if all_index_only:
        lines.extend(["", "## Index only (no copy)", "", "| Role | Source | Bytes |", "|---|---|---:|"])
        for e in all_index_only:
            lines.append(f"| `{e['role']}` | `{e['source_relative']}` | {e.get('bytes', 'n/a')} |")
    if all_skipped:
        lines.extend(["", "## Skipped (summary)", ""])
        reasons: dict[str, int] = {}
        for s in all_skipped:
            reasons[s.get("reason", "?")] = reasons.get(s.get("reason", "?"), 0) + 1
        for k, v in sorted(reasons.items()):
            lines.append(f"- **{k}:** {v}")
    lines.append("")
    (root / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    log.log_step(
        f"repo_docs_mirror snapshots={len(all_written)} index_only={len(all_index_only)} "
        f"skipped={len(all_skipped)} bytes={total_bytes} under {root}",
    )

    return {
        "enabled": True,
        "files": all_written,
        "index_only": all_index_only,
        "skipped": all_skipped,
        "total_bytes": total_bytes,
        "root": str(root),
    }
