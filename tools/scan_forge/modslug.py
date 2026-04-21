from __future__ import annotations

import re


def forge_mod_dirslug_from_dir(d: str) -> str:
    if not d:
        raise ValueError("empty dir")
    if d == ".":
        d = "root"
    s = d.replace("/", "-")
    s = s.lstrip("-").rstrip("-")
    return s


def forge_mod_node_basename_from_rel(role: str, rel: str) -> str:
    from pathlib import PurePosixPath

    d = str(PurePosixPath(rel).parent)
    if d == ".":
        d = "root"
    return f"{role}-{forge_mod_dirslug_from_dir(d)}"


def forge_page_node_basename_from_rel(role: str, rel: str) -> str:
    """Stable Obsidian-style basename for a UI file (unique per repo-relative path)."""
    r = rel.replace("\\", "/").strip("/")
    slug = r.replace("/", "-").replace(".", "-")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", slug)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-").lower()
    return f"{role}-{slug}"
