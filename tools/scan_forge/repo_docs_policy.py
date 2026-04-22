"""Optional per-repo YAML policy for ``repo_docs_mirror`` (curate without losing intent)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_POLICY_FILENAMES = (
    "forge-scan-docs.policy.yaml",
    ".forge-repo-docs.yaml",
    "forge-repo-docs.yaml",
)


@dataclass
class RepoDocsPolicy:
    """Effective policy for one repository (defaults + file overrides)."""

    max_files: int
    max_bytes_per_file: int
    deny_path_contains: list[str] = field(default_factory=list)
    index_only_path_contains: list[str] = field(default_factory=list)
    allow_extra_path_contains: list[str] = field(default_factory=list)
    policy_path: str | None = None
    #: When True, only mirror ``.md`` under ``docs/``, ``adr/``, etc. (legacy layout).
    #: Default **False**: every ``.md`` file is eligible (still subject to skip paths,
    #: deny/index_only, and ``max_files``) so prose can live at arbitrary paths.
    restrict_markdown_to_doc_dirs: bool = False


def _default_limits() -> tuple[int, int]:
    return (
        int(os.environ.get("FORGE_REPO_DOCS_MAX_FILES", "120")),
        int(os.environ.get("FORGE_REPO_DOCS_MAX_BYTES", str(512 * 1024))),
    )


def _parse_simple_yaml(text: str) -> dict[str, Any] | None:
    """Stdlib-only fallback for the simple list-of-strings YAML format used by policy files.

    Handles:
      key: scalar_value
      list_key:
        - item
        - "quoted item"
    """
    result: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in text.splitlines():
        # Skip comments and blank lines
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            current_list_key = None
            continue
        if stripped.startswith("  - ") or stripped.startswith("- "):
            # List item
            item = stripped.lstrip()[2:].strip().strip('"').strip("'")
            if current_list_key is not None:
                result.setdefault(current_list_key, []).append(item)
            continue
        if ":" in stripped and not stripped.startswith(" "):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                # Scalar value — try int, then bool, then string
                if val.isdigit():
                    result[key] = int(val)
                elif val.lower() in ("true", "yes"):
                    result[key] = True
                elif val.lower() in ("false", "no"):
                    result[key] = False
                else:
                    result[key] = val
                current_list_key = None
            else:
                # Start of a list block
                current_list_key = key
                result.setdefault(key, [])
    return result if result else None


def load_repo_docs_policy(repo: Path) -> RepoDocsPolicy:
    """Load first present policy file from repo root; YAML optional (stdlib-only fallback)."""
    mf, mb = _default_limits()
    out = RepoDocsPolicy(max_files=mf, max_bytes_per_file=mb)
    repo = repo.resolve()
    for name in _POLICY_FILENAMES:
        path = repo / name
        if not path.is_file():
            continue
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        data: dict[str, Any] | None = None
        try:
            import yaml  # type: ignore[import-untyped]
            loaded = yaml.safe_load(raw_text)
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            pass
        if not isinstance(data, dict):
            data = _parse_simple_yaml(raw_text)
        if not isinstance(data, dict):
            continue
        try:
            if int(data.get("version", 1)) < 1:
                continue
        except (TypeError, ValueError):
            continue
        out.policy_path = str(path)
        if data.get("max_files") is not None:
            try:
                out.max_files = max(1, int(data["max_files"]))
            except (TypeError, ValueError):
                pass
        if data.get("max_bytes_per_file") is not None:
            try:
                out.max_bytes_per_file = max(1024, int(data["max_bytes_per_file"]))
            except (TypeError, ValueError):
                pass

        def _str_list(key: str) -> list[str]:
            v = data.get(key)
            if not isinstance(v, list):
                return []
            return [str(x) for x in v if x is not None and str(x).strip()]

        out.deny_path_contains = _str_list("deny_path_contains")
        out.index_only_path_contains = _str_list("index_only_path_contains")
        out.allow_extra_path_contains = _str_list("allow_extra_path_contains")
        if data.get("restrict_markdown_to_doc_dirs") is not None:
            out.restrict_markdown_to_doc_dirs = bool(data["restrict_markdown_to_doc_dirs"])
        # Legacy key (inverse semantics); ``true`` was a no-op once all-md became default.
        if data.get("include_all_markdown") is False:
            out.restrict_markdown_to_doc_dirs = True
        break

    return out


def path_denied(rel_posix: str, deny: list[str]) -> bool:
    r = rel_posix.replace("\\", "/")
    return any(d and d in r for d in deny)


def path_index_only(rel_posix: str, index_only: list[str]) -> bool:
    r = rel_posix.replace("\\", "/")
    return any(s and s in r for s in index_only)


def path_extra_allowed(rel_posix: str, extras: list[str]) -> bool:
    r = rel_posix.replace("\\", "/")
    return any(s and s in r for s in extras)
