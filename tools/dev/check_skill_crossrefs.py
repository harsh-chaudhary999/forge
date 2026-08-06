#!/usr/bin/env python3
"""Check Forge skill files for three bug classes found by manual audit that no
other linter catches: broken skill-name cross-references, malformed `version`
frontmatter, and regression of the forge-product.md migration (bare product.md).

None of `check_skill_standard.py` (name/description only) or
`lint_skill_allowed_tools.py` (type/allowed-tools only) or the CI markdown-link
check (only `[text](url)` syntax) look at any of these. All three were found by
hand in a manual audit (see docs/release-readiness-2026.md A5) and then fixed —
this script exists so the same bug classes don't silently reappear on the next
skill edit.

A skill body legitimately needs to mention a *fictional* skill name as a
teaching example (e.g. "if a new skill `foo-bar-v2` overlapped with `foo-bar`,
you'd..."). Mark that exact line with a trailing `<!-- crossref: fictional-example -->`
comment to suppress it — the checker skips any line carrying that marker.

1. Broken skill-name cross-references
   A backtick-quoted, kebab-case token (>= 3 hyphen-segments) that shares a
   >=2-segment family prefix with two or more *real* skill directories (e.g.
   `eval-driver-*`, `deploy-driver-*`) but does not itself match any real
   skill directory name is flagged. This caught `eval-driver-search-elasticsearch`
   (real skill: eval-driver-search-es) and `deploy-driver-k8s` (never built).
   The family-prefix requirement keeps this from flagging arbitrary kebab-case
   prose; requiring the full token to be unmatched (not just look skill-shaped)
   keeps it from flagging generic category mentions.

2. Malformed `version` frontmatter
   `version: version: 1.0.5` (duplicated key text baked into the value, instead
   of `version: 1.0.5`) parses as valid YAML with the wrong string value, so no
   existing check catches it. This checks the field matches `X.Y.Z`.

3. Bare `product.md` regression
   The June-2026 A8 migration renamed every bare `product.md` reference to
   `forge-product.md` across 48 files (a functional break, not cosmetic: the
   creator and consumers had drifted onto different filenames). This guards
   against a future edit reintroducing the bare form.

Usage:
    python3 tools/dev/check_skill_crossrefs.py [--verbose]

Exit 0 = clean; exit 1 = at least one violation (suitable for CI).
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT / "skills"

BACKTICK_TOKEN_RE = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+){2,})`")
SUPPRESS_MARKER = "<!-- crossref: fictional-example -->"
VERSION_LINE_RE = re.compile(r"^version:\s*(.+)$", re.MULTILINE)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
BARE_PRODUCT_MD_RE = re.compile(r"(?<!forge-)\bproduct\.md\b")


def real_skill_names() -> set[str]:
    return {
        p.name
        for p in SKILLS_DIR.iterdir()
        if p.is_dir() and p.name != "_shared" and (p / "SKILL.md").is_file()
    }


def family_prefixes(names: set[str]) -> set[str]:
    """>=2-segment hyphen prefixes shared by 2+ real skill names."""
    counts: dict[str, int] = defaultdict(int)
    for name in names:
        segs = name.split("-")
        for i in range(2, len(segs)):
            counts["-".join(segs[:i])] += 1
    return {prefix for prefix, count in counts.items() if count >= 2}


def iter_skill_md_files():
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name == "_shared":
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            yield skill_dir.name, skill_md
        ref_dir = skill_dir / "reference"
        if ref_dir.is_dir():
            for ref_md in sorted(ref_dir.glob("*.md")):
                yield skill_dir.name, ref_md


def check_crossrefs(real_names: set[str], families: set[str], verbose: bool) -> list[str]:
    violations = []
    for skill_name, path in iter_skill_md_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        suppressed_lines = {
            i + 1 for i, line in enumerate(text.split("\n")) if SUPPRESS_MARKER in line
        }
        for match in BACKTICK_TOKEN_RE.finditer(text):
            candidate = match.group(1)
            if candidate in real_names or candidate in families:
                continue
            line_no = text.count("\n", 0, match.start()) + 1
            if line_no in suppressed_lines:
                continue
            segs = candidate.split("-")
            shares_family = any(
                "-".join(segs[:i]) in families for i in range(2, len(segs))
            )
            if shares_family:
                violations.append(
                    f"{path.relative_to(ROOT)}:{line_no}: `{candidate}` looks like a skill "
                    f"reference (shares a family prefix with real skills) but no such "
                    f"skill directory exists — referenced from `{skill_name}`"
                )
    return violations


def check_versions(verbose: bool) -> list[str]:
    violations = []
    for skill_name, path in iter_skill_md_files():
        if path.name != "SKILL.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not fm_match:
            continue
        m = VERSION_LINE_RE.search(fm_match.group(1))
        if not m:
            continue
        value = m.group(1).strip()
        if not SEMVER_RE.match(value):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"{path.relative_to(ROOT)}:{line}: version field is `{value}` — "
                f"expected `X.Y.Z` semver (skill: `{skill_name}`)"
            )
    return violations


def check_bare_product_md(verbose: bool) -> list[str]:
    violations = []
    for skill_name, path in iter_skill_md_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in BARE_PRODUCT_MD_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            violations.append(
                f"{path.relative_to(ROOT)}:{line}: bare `product.md` — should be "
                f"`forge-product.md` (skill: `{skill_name}`)"
            )
    return violations


def main() -> int:
    verbose = "--verbose" in sys.argv
    real_names = real_skill_names()
    families = family_prefixes(real_names)

    all_violations = (
        check_crossrefs(real_names, families, verbose)
        + check_versions(verbose)
        + check_bare_product_md(verbose)
    )

    if all_violations:
        print(f"FAIL: {len(all_violations)} violation(s) found:\n")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print(
        f"OK: {len(real_names)} skills scanned — no broken cross-references, "
        f"malformed version fields, or bare product.md references"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
