from __future__ import annotations

import subprocess
from pathlib import Path

SOURCE_SUFFIXES = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".go",
    ".java",
    ".kt",
    ".rs",
    ".rb",
    ".dart",
    ".swift",
    ".cpp",
    ".c",
    ".h",
}

SKIP_DIR_NAMES = {
    "node_modules",
    ".git",
    "__pycache__",
    "vendor",
    "dist",
    "build",
    "coverage",
}

SKIP_PATH_PARTS = ("/.git/",)


def _is_source_name(name: str) -> bool:
    lower = name.lower()
    if not any(lower.endswith(s) for s in SOURCE_SUFFIXES):
        return False
    if ".generated." in lower or ".min." in lower:
        return False
    if ".spec." in lower or ".test." in lower:
        return False
    return True


def _is_test_name(name: str) -> bool:
    lower = name.lower()
    if ".spec." in lower or ".test." in lower:
        return True
    if "_test." in lower:
        return True
    if lower.startswith("test_") and lower.endswith(".py"):
        return True
    return False


def git_submodule_displaypaths(repo: Path) -> list[str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "submodule", "--quiet", "foreach", "echo $displaypath"],
            capture_output=True,
            text=True,
            timeout=120,
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    out = []
    for line in (p.stdout or "").splitlines():
        line = line.strip()
        if line:
            out.append(line)
    return out


def path_under_submodule(rel_posix: str, submodules: list[str]) -> bool:
    for sm in submodules:
        sm = sm.strip().strip("/")
        if not sm:
            continue
        if rel_posix == sm or rel_posix.startswith(sm + "/"):
            return True
    return False


def _rel_has_excluded_dir(rel_posix: str) -> bool:
    parts = rel_posix.split("/")
    for x in parts:
        if x in SKIP_DIR_NAMES:
            return True
        if x in ("vendor", "dist", "build"):
            return True
    return False


def iter_files_under(repo: Path) -> list[Path]:
    files: list[Path] = []
    submods = git_submodule_displaypaths(repo)
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(repo).as_posix()
        except ValueError:
            continue
        if _rel_has_excluded_dir(rel):
            continue
        if "/node_modules/" in f"/{rel}/" or rel.startswith("node_modules/"):
            continue
        if ".git/" in rel or rel.startswith(".git/"):
            continue
        if "/__pycache__/" in f"/{rel}/":
            continue
        if "/vendor/" in f"/{rel}/":
            continue
        if "/dist/" in f"/{rel}/" or "/build/" in f"/{rel}/":
            continue
        if path_under_submodule(rel, submods):
            continue
        files.append(p)
    files.sort()
    return files


def list_source_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for p in iter_files_under(repo):
        name = p.name
        if _is_source_name(name):
            out.append(p)
    return out


def list_test_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for p in iter_files_under(repo):
        name = p.name
        if _is_test_name(name):
            out.append(p)
    return out
