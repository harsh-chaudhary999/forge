from __future__ import annotations

import re
import subprocess
from pathlib import Path


def run_grep_rn(
    repo: Path,
    pattern: str,
    includes: list[str] | None = None,
) -> str:
    """Run GNU grep -rn; return stdout (empty if no matches)."""
    cmd: list[str] = ["grep", "-rn", pattern, str(repo)]
    if includes:
        for inc in includes:
            cmd.append(f"--include={inc}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=600)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if p.returncode not in (0, 1):
        return ""
    return p.stdout or ""


def filter_grep_lines(stdout: str, repo: Path) -> str:
    """Apply common bash-pipeline excludes (node_modules, dist, tests…)."""
    if not stdout:
        return ""
    test_re = re.compile(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/")
    out_lines: list[str] = []
    for line in stdout.splitlines():
        if "node_modules" in line:
            continue
        if "/dist/" in line or "/build/" in line or "/target/" in line:
            continue
        if "/.next/" in line:
            continue
        if "/.git/" in line:
            continue
        # strip repo prefix for consistent handling — keep as grep prints (abs path)
        try:
            if str(repo) not in line and not line.startswith(str(repo)):
                pass
        except Exception:
            pass
        if test_re.search(line):
            continue
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if out_lines else "")


def cksum_first_field(text: str) -> str:
    p = subprocess.run(
        ["cksum"],
        input=text.encode("utf-8", errors="surrogateescape"),
        capture_output=True,
        check=False,
    )
    if p.returncode != 0 or not p.stdout:
        return "0"
    return p.stdout.decode().split()[0]
