#!/usr/bin/env python3
"""
Portable lint: SKILL.md frontmatter allowed-tools + rigid skill completeness.

Runs anywhere Python 3 runs (CI, pre-commit). Does not depend on editor hooks.

Optional --write-policy emits tools/skill-tool-policy.json for hosts that can
consume a static manifest (still optional per platform).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RE_FM = re.compile(r"\A---\n([\s\S]*?)\n---")
RE_NAME = re.compile(r"^name:\s*(.+)\s*$", re.MULTILINE)
RE_TYPE = re.compile(r"^type:\s*(\S+)\s*$", re.MULTILINE)
RE_ALLOWED_BLOCK = re.compile(
    r"^allowed-tools:\s*\n((?:\s+-\s+[^\n]+\n?)+)", re.MULTILINE
)
RE_HARD_BODY = re.compile(r"(^|\n)##\s*HARD-GATE\b", re.MULTILINE)
RE_HARD_TITLE = re.compile(r"(^|\n)# [^\n]*\bHARD-GATE\b", re.MULTILINE)
RE_HARD_DESC = re.compile(r"^description:\s*\"[^\"]*\bHARD-GATE:", re.MULTILINE)

# Claude / Cursor / common agent tool names (extend when platforms add tools).
KNOWN_TOOLS = frozenset(
    {
        "Bash",
        "Read",
        "Write",
        "Edit",
        "Grep",
        "Glob",
        "SemanticSearch",
        "WebFetch",
        "WebSearch",
        "Task",
        "AskQuestion",
        "SwitchMode",
        "GenerateImage",
        "Delete",
        "ReadLints",
        "EditNotebook",
        "TodoWrite",
        "Shell",
        "StrReplace",
        "CodebaseSearch",
        "NotebookEdit",
        "AwaitShell",
        "ListMcpResources",
        "call_mcp_tool",
        "fetch_mcp_resource",
    }
)


def _parse_frontmatter(text: str) -> str | None:
    m = RE_FM.match(text)
    return m.group(1) if m else None


def _allowed_tools(fm: str) -> list[str]:
    m = RE_ALLOWED_BLOCK.search(fm)
    out: list[str] = []
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if line.startswith("- "):
                out.append(line[2:].strip())
        return out
    inline = re.search(r"^allowed-tools:\s*\[(.*)\]\s*$", fm, re.MULTILINE)
    if inline:
        for tok in inline.group(1).split(","):
            t = tok.strip()
            if t:
                out.append(t)
    return out


def _is_hard_gate(skill_text: str, fm: str) -> bool:
    return bool(
        RE_HARD_BODY.search(skill_text)
        or RE_HARD_TITLE.search(skill_text)
        or RE_HARD_DESC.search(fm)
    )


def lint_skill_file(path: Path) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errs: list[str] = []
    warns: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(text)
    if fm is None:
        errs.append(f"{path}: missing YAML frontmatter")
        return errs, warns
    name_m = RE_NAME.search(fm)
    typ_m = RE_TYPE.search(fm)
    name = name_m.group(1).strip() if name_m else path.parent.name
    typ = typ_m.group(1).strip().lower() if typ_m else ""
    tools = _allowed_tools(fm)
    if typ == "rigid" and not tools:
        errs.append(f"{path}: type rigid but allowed-tools missing or empty")
    for t in tools:
        if t not in KNOWN_TOOLS:
            warns.append(f"{path} ({name}): unknown allowed-tools entry {t!r} (extend KNOWN_TOOLS if valid)")
    return errs, warns


def collect_policy(skills_root: Path) -> dict:
    skills: dict = {}
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        if "_preamble" in skill_md.parts:
            continue
        rel_parent = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text) or ""
        name_m = RE_NAME.search(fm)
        name = name_m.group(1).strip() if name_m else rel_parent
        typ_m = RE_TYPE.search(fm)
        typ = typ_m.group(1).strip().lower() if typ_m else ""
        tools = _allowed_tools(fm)
        skills[name] = {
            "path": str(skill_md.relative_to(skills_root)),
            "type": typ,
            "hard_gate": _is_hard_gate(text, fm),
            "allowed_tools": tools,
        }
    return {"schema_version": 1, "skills": skills}


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint skills/*/SKILL.md allowed-tools (portable).")
    ap.add_argument(
        "--skills-root",
        default=None,
        help="Directory containing <skill-name>/SKILL.md (default: <forge>/skills)",
    )
    ap.add_argument(
        "--write-policy",
        default=None,
        help="Write skill-tool-policy.json to this path (e.g. tools/skill-tool-policy.json)",
    )
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    skills_root = Path(args.skills_root).expanduser() if args.skills_root else (root / "skills")
    if not skills_root.is_dir():
        print(f"ERROR: skills root not a directory: {skills_root}", file=sys.stderr)
        return 2

    all_errs: list[str] = []
    all_warns: list[str] = []
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        if "_preamble" in skill_md.parts:
            continue
        e, w = lint_skill_file(skill_md)
        all_errs.extend(e)
        all_warns.extend(w)

    for w in all_warns:
        print(f"WARN: {w}", file=sys.stderr)
    if all_errs:
        print("lint_skill_allowed_tools: FAILED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    if args.write_policy:
        out = Path(args.write_policy).expanduser().resolve()
        root_resolved = root.resolve()
        try:
            out.relative_to(root_resolved)
        except ValueError:
            print(
                f"ERROR: --write-policy must stay within repository root: {root_resolved}",
                file=sys.stderr,
            )
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        pol = collect_policy(skills_root)
        out.write_text(json.dumps(pol, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"OK: wrote {out}")

    print(f"OK: scanned skills under {skills_root} ({len(all_warns)} warn)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
