#!/usr/bin/env python3
"""Scaffold a new Forge skill directory with compliant frontmatter, then
self-check it — so a new skill starts from a linted skeleton instead of
hand-written frontmatter (the exact failure mode behind every bug fixed in
docs/release-readiness-2026.md A5: malformed version fields, broken
cross-references, all originated as hand-typed YAML with no linter in the loop
at authoring time).

This is a scaffold, NOT a rigor shortcut: for `rigid` skills, the generated
skeleton still requires you to follow `forge-writing-skills`' TDD-for-skills
methodology (pressure testing, persuasion-grounded design) before the skill is
real — this script only removes the mechanical toil of getting frontmatter and
section skeletons right on the first try.

Usage:
    python3 tools/dev/scaffold_skill.py <skill-name> --type rigid|flexible|reference [--tier N] [--requires a,b,c]

Writes skills/<skill-name>/SKILL.md, then runs check_skill_standard.py,
lint_skill_allowed_tools.py, and check_skill_crossrefs.py against it and
reports pass/fail — so you know before you start filling it in whether the
skeleton itself is clean.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT / "skills"

SECTIONS_BY_TYPE = {
    "rigid": [
        "## Human input\n\n_(delete this section if the skill doesn't use AskUserQuestion)_\n",
        "## Anti-Pattern Preamble\n\n| Rationalization | Why It Fails |\n|---|---|\n| TODO | TODO |\n",
        "## Iron Law\n\n```\nTODO — the one non-negotiable rule this skill enforces.\n```\n",
        "## HARD-GATE\n\nTODO — what must never be skipped, and what MAY be skipped when a documented condition holds.\n",
        "## Red Flags — STOP\n\nIf you notice any of these, STOP and do not proceed:\n\n- TODO\n",
        "## Workflow\n\nTODO\n",
        "## Edge Cases & Fallback Paths\n\n### Edge Case 1: TODO\n\n**Diagnosis**: TODO\n\n**Response**: TODO\n\n**Escalation**: TODO\n",
        "## Output\n\nTODO — exact artifact this skill produces and where it's written.\n",
        "## Cross-References\n\n- `TODO`: TODO\n",
    ],
    "flexible": [
        "## Anti-Pattern Preamble\n\n| Rationalization | Why It Fails |\n|---|---|\n| TODO | TODO |\n",
        "## Workflow\n\nTODO\n",
        "## Edge Cases\n\n- TODO\n",
        "## Output\n\nTODO\n",
        "## Cross-References\n\n- `TODO`: TODO\n",
    ],
    "reference": [
        "## Overview\n\nTODO\n",
        "## Cross-References\n\n- `TODO`: TODO\n",
    ],
}


def build_frontmatter(name: str, type_: str, tier: int, requires: list[str]) -> str:
    lines = [
        "---",
        f"name: {name}",
        f'description: "WHEN: TODO — describe the trigger condition. TODO — what this skill does in one sentence."',
        f"type: {type_}",
    ]
    if requires:
        lines.append(f"requires: [{', '.join(requires)}]")
    lines.append("version: 1.0.0")
    lines.append(f"preamble-tier: {tier}")
    lines.append("allowed-tools:")
    lines.append("  - Read")
    lines.append("---")
    return "\n".join(lines) + "\n"


def build_body(name: str, type_: str) -> str:
    title = " ".join(w.capitalize() for w in name.split("-"))
    parts = [f"\n# {title}\n"]
    parts.extend(SECTIONS_BY_TYPE[type_])
    return "\n".join(parts)


def run_checkers() -> bool:
    ok = True
    for script in (
        "tools/check_skill_standard.py",
        "tools/dev/lint_skill_allowed_tools.py",
        "tools/check_skill_crossrefs.py",
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / script)], cwd=ROOT, capture_output=True, text=True
        )
        print(f"--- {script} ---")
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip())
            ok = False
    return ok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("name", help="skill name, kebab-case")
    p.add_argument("--type", required=True, choices=["rigid", "flexible", "reference"])
    p.add_argument("--tier", type=int, default=2, help="preamble tier, 1-4 (default 2)")
    p.add_argument("--requires", default="", help="comma-separated skill dependencies")
    args = p.parse_args()

    skill_dir = SKILLS_DIR / args.name
    if skill_dir.exists():
        print(f"REFUSE: skills/{args.name}/ already exists — not overwriting.")
        return 1

    requires = [r.strip() for r in args.requires.split(",") if r.strip()]
    for r in requires:
        if not (SKILLS_DIR / r).is_dir():
            print(f"REFUSE: requires: [{r}] does not exist as a real skill.")
            return 1

    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    content = build_frontmatter(args.name, args.type, args.tier, requires) + build_body(
        args.name, args.type
    )
    skill_md.write_text(content, encoding="utf-8")
    print(f"Wrote {skill_md.relative_to(ROOT)} ({len(content.splitlines())} lines)\n")

    if args.type == "rigid":
        print(
            "NOTE: type=rigid — before this skill is real, follow forge-writing-skills' "
            "TDD-for-skills methodology (pressure testing, persuasion-grounded design). "
            "This scaffold only gets the mechanical parts (frontmatter, section skeleton, "
            "linter-clean) right on the first try.\n"
        )

    ok = run_checkers()
    print("\nSCAFFOLD CLEAN — fill in the TODOs." if ok else "\nSCAFFOLD HAS LINT ISSUES — fix before filling in content.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
