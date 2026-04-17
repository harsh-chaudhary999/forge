from __future__ import annotations


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
