"""Mirror curated repository Markdown + OpenAPI specs into ``brain_codebase/repo-docs/``.

Markdown files are enriched (not verbatim) by ``repo_docs_extract``:
  - YAML frontmatter (source_repo, commit, doc_type, scanned_at)
  - Heading outline appended for navigation
  - ADR structured fields (Status, Context, Decision, Consequences)
  - Wikilinks to matching brain module/class nodes
  - Per-section rows fed into SEARCH_INDEX.md

OpenAPI/Swagger YAML/JSON files are stored verbatim (structured data, not narrative).

Incremental: source SHA tracked; files only re-enriched when source changes or
extract_version bumps. Stale brain files removed when source docs are deleted.

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

from . import fs_util, log, repo_docs_extract, repo_docs_policy

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
    # key: brain_relative → (source_sha256, extract_version)
    existing_index: dict[str, tuple[str, int]] = {}
    idx_path = root / "index.json"
    if idx_path.is_file():
        try:
            prev = json.loads(idx_path.read_text(encoding="utf-8"))
            for e in prev.get("files", []):
                if e.get("brain_relative") and e.get("source_sha256"):
                    existing_index[e["brain_relative"]] = (
                        e["source_sha256"],
                        e.get("extract_version", 0),
                    )
        except (OSError, json.JSONDecodeError):
            pass

    # Collect candidates per repo, applying per-repo policy independently
    all_written: list[dict[str, Any]] = []
    all_index_only: list[dict[str, Any]] = []
    all_skipped: list[dict[str, Any]] = []
    all_search_rows: list[dict[str, str]] = []
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
            source_digest = hashlib.sha256(data).hexdigest()
            dest = root / role / Path(w.rel)
            brain_rel = str(dest.relative_to(brain_codebase)).replace("\\", "/")
            is_markdown = w.rel.lower().endswith(".md")

            # Incremental: skip if source unchanged AND extract version unchanged
            prev_sha, prev_ver = existing_index.get(brain_rel, ("", -1))
            needs_write = (
                source_digest != prev_sha
                or prev_ver != repo_docs_extract._EXTRACT_VERSION
                or not dest.is_file()
            )

            entry: dict[str, Any] = {
                "role": role,
                "source_relative": w.rel,
                "brain_relative": brain_rel,
                "source_head": head,
                "source_sha256": source_digest,
                "extract_version": repo_docs_extract._EXTRACT_VERSION if is_markdown else 0,
                "tier": "snapshot",
                "scanned_at": scanned_at,
            }

            if needs_write:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if is_markdown:
                    enriched, meta = repo_docs_extract.enrich_markdown(
                        data, w.rel, role, head, scanned_at, brain_codebase
                    )
                    dest.write_bytes(enriched)
                    entry["doc_type"] = meta["doc_type"]
                    entry["headings_count"] = meta["headings_count"]
                    entry["brain_links_count"] = meta["brain_links_count"]
                    all_search_rows.extend(meta["search_rows"])
                    b = len(enriched)
                else:
                    dest.write_bytes(data)
                    b = len(data)
                entry["bytes"] = b
            else:
                log.log_step(f"repo_docs_mirror unchanged={brain_rel}")
                entry["bytes"] = dest.stat().st_size if dest.is_file() else len(data)
                # Re-collect search rows from existing enriched file for index rebuild
                if is_markdown and dest.is_file():
                    existing_text = dest.read_text(encoding="utf-8", errors="replace")
                    doc_type = repo_docs_extract.detect_doc_type(w.rel, existing_text)
                    entry["doc_type"] = doc_type
                    all_search_rows.extend(
                        repo_docs_extract.extract_search_rows(role, w.rel, existing_text, doc_type)
                    )

            total_bytes += entry["bytes"]
            all_written.append(entry)
            repo_file_count += 1

    # Remove stale brain files no longer in any repo
    current_brain_rels = {e["brain_relative"] for e in all_written}
    for old_rel in list(existing_index):
        if old_rel not in current_brain_rels:
            stale = brain_codebase / old_rel
            if stale.is_file():
                stale.unlink(missing_ok=True)
                log.log_step(f"repo_docs_mirror removed stale={old_rel}")

    # Write search index
    repo_docs_extract.write_search_index(root, all_search_rows)

    policies_used = [
        {"role": r, "policy_path": policies[r].policy_path, "max_bytes_per_file": policies[r].max_bytes_per_file, "max_files": policies[r].max_files}
        for r, _ in repos
    ]

    # Write README
    (root / "README.md").write_text(
        "\n".join([
            "# Repo documentation mirror",
            "",
            "Enriched Markdown snapshots of curated docs from each scanned repo.",
            "Each `.md` file has: **YAML frontmatter** (source, commit, doc_type) + "
            "**heading outline** + **ADR fields** (if applicable) + "
            "**brain node wikilinks** (auto-detected).",
            "",
            "**`SEARCH_INDEX.md`** — one row per section across all docs for topic search.",
            "**`INDEX.md`** — file inventory table. **`index.json`** — machine-readable metadata.",
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
        "forge_repo_docs_mirror_version": 3,
        "written_at": scanned_at,
        "extract_version": repo_docs_extract._EXTRACT_VERSION,
        "enriched_markdown": True,
        "policies_used": policies_used,
        "files": all_written,
        "index_only": all_index_only,
        "skipped": all_skipped,
        "totals": {
            "snapshot_files": len(all_written),
            "index_only_rows": len(all_index_only),
            "skipped": len(all_skipped),
            "snapshot_bytes": total_bytes,
            "search_index_rows": len(all_search_rows),
        },
    }
    idx_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    # Write INDEX.md
    lines = [
        "# Repo docs mirror index",
        "",
        f"_v3 — {scanned_at} — Markdown files enriched with frontmatter, outline, ADR fields, and brain links._",
        "",
        "## Snapshots",
        "",
        "| Role | Source | Type | Brain path | HEAD | Bytes |",
        "|---|---|---|---|---|---:|",
    ]
    for e in all_written:
        head = e["source_head"]
        short = head[:12] + "…" if len(head) > 12 else head
        doc_type = e.get("doc_type", "")
        lines.append(
            f"| `{e['role']}` | `{e['source_relative']}` | {doc_type} | `{e['brain_relative']}` | `{short}` | {e['bytes']} |"
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
        f"skipped={len(all_skipped)} bytes={total_bytes} search_rows={len(all_search_rows)} under {root}",
    )

    return {
        "enabled": True,
        "files": all_written,
        "index_only": all_index_only,
        "skipped": all_skipped,
        "total_bytes": total_bytes,
        "root": str(root),
    }
