#!/usr/bin/env python3
"""Check Forge skills + agents against the Agent Skills open standard.

The Agent Skills standard (Anthropic, 2025-12-18; adopted by Claude Code, Codex,
Cursor, and others) requires every SKILL.md to carry YAML frontmatter with two
fields, and constrains their values:

  name        - required; <= 64 chars; only [a-z0-9-]; no XML tags;
                must not contain the reserved words "anthropic" or "claude".
  description - required; non-empty; <= 1024 chars; no XML tags.

Forge layers extra frontmatter on top (type, requires, preamble-tier,
allowed-tools, triggers, model, effort, ...). Those are allowed — the standard
ignores unknown keys — but `name` and `description` must stay conformant so the
skills load identically across every standard-compliant host.

This validator scans skills/<name>/SKILL.md and agents/*.md. Exit 0 = all
conform; exit 1 = at least one violation (suitable for CI).

Usage:
  python3 tools/check_skill_standard.py            # scan from repo root
  python3 tools/check_skill_standard.py --root DIR # scan a specific repo root
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9-]+$")
XML_RE = re.compile(r"<[^>]+>")
RESERVED = ("anthropic", "claude")
MAX_NAME = 64
MAX_DESC = 1024


def _frontmatter(path: str) -> str:
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def _field(block: str, key: str) -> str | None:
    m = re.search(rf'^{key}:\s*"(.*?)"\s*$', block, re.M)
    if m:
        return m.group(1)
    m = re.search(rf"^{key}:\s*'(.*?)'\s*$", block, re.M)
    if m:
        return m.group(1)
    m = re.search(rf"^{key}:\s*(.+?)\s*$", block, re.M)
    return m.group(1) if m else None


def check_file(path: str) -> list[str]:
    block = _frontmatter(path)
    problems: list[str] = []
    if not block:
        return ["no YAML frontmatter"]
    name = _field(block, "name")
    desc = _field(block, "description")

    if not name:
        problems.append("missing required field: name")
    else:
        if len(name) > MAX_NAME:
            problems.append(f"name exceeds {MAX_NAME} chars ({len(name)})")
        if not NAME_RE.match(name):
            problems.append(f"name must match [a-z0-9-]: {name!r}")
        if any(r in name.lower() for r in RESERVED):
            problems.append(f"name contains a reserved word ({'/'.join(RESERVED)}): {name!r}")

    if not desc:
        problems.append("missing or empty required field: description")
    else:
        if len(desc) > MAX_DESC:
            problems.append(f"description exceeds {MAX_DESC} chars ({len(desc)})")
        if XML_RE.search(desc):
            problems.append(f"description contains XML-like tag(s): {XML_RE.findall(desc)[:3]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate skills/agents against the Agent Skills standard.")
    ap.add_argument("--root", default=".", help="Repo root containing skills/ and agents/ (default: cwd)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.root, "skills", "*", "SKILL.md")))
    files += sorted(glob.glob(os.path.join(args.root, "agents", "*.md")))

    if not files:
        print(f"No skills/ or agents/ found under {args.root!r}", file=sys.stderr)
        return 1

    total_viol = 0
    for f in files:
        problems = check_file(f)
        if problems:
            total_viol += len(problems)
            rel = os.path.relpath(f, args.root)
            for p in problems:
                print(f"VIOLATION [{rel}]: {p}", file=sys.stderr)

    if total_viol:
        print(f"\nFAIL: {total_viol} violation(s) across {len(files)} files", file=sys.stderr)
        return 1
    print(f"OK: {len(files)} skills/agents conform to the Agent Skills standard (name + description).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
