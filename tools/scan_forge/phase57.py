from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

from . import log


def _collect_md_index(parent: Path) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = defaultdict(list)
    for p in parent.rglob("*.md"):
        rel = str(p).replace("\\", "/")
        if "/.obsidian/" in rel:
            continue
        if "/repo-docs/" in rel:
            continue
        if p.name == "wikilink-orphan-report.md":
            continue
        idx[p.stem].append(p)
    for k in idx:
        idx[k] = sorted(idx[k])
    return idx


def _normalize_embed(match: str) -> str:
    s = match.strip()
    if s.startswith("![[") and s.endswith("]]"):
        return "[[" + s[3:]
    return s


def _resolve_target(parent: Path, idx: dict[str, list[Path]], raw_inner: str) -> bool:
    target = raw_inner.split("|", 1)[0].split("#", 1)[0].strip()
    if not target:
        return True
    # Repo-doc mirrors may contain external wiki namespaces (e.g. "memory:1234")
    # that are not expected to resolve inside codebase/.
    if ":" in target:
        return True
    if "/" in target:
        rel = target if target.endswith(".md") else f"{target}.md"
        if (parent / rel).is_file():
            return True
        if (parent / f"{target}.md").is_file():
            return True
        base = Path(target).stem
        return bool(idx.get(base))
    return bool(idx.get(target))


def _wikilinks_in_file(path: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for i, line in enumerate(lines, start=1):
        for m in re.finditer(r"\[\[([^]]+)\]\]", line):
            out.append((i, m.group(0)))
        for m in re.finditer(r"!\[\[([^]]+)\]\]", line):
            inner = m.group(1)
            out.append((i, f"[[{inner}]]"))
    return out


def run_phase57(parent: Path, write_report: bool) -> None:
    parent = parent.resolve()
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "phase57"
    log.log_start("phase57", f"brain_parent={parent} write_report={int(write_report)}")

    idx = _collect_md_index(parent)
    if not idx:
        log.log_warn("no_markdown_under_parent")
        print(f"No .md files found under {parent} (excluding .obsidian).")
        log.log_done("orphans=0 ambiguous_basename_groups=0")
        return

    links: list[tuple[Path, int, str]] = []
    seen: set[tuple[str, int, str]] = set()
    for md in sorted(parent.rglob("*.md")):
        rel = str(md).replace("\\", "/")
        if "/.obsidian/" in rel:
            continue
        if "/repo-docs/" in rel:
            continue
        if md.name == "wikilink-orphan-report.md":
            continue
        for lineno, m in _wikilinks_in_file(md):
            key = (str(md.resolve()), lineno, m)
            if key in seen:
                continue
            seen.add(key)
            links.append((md, lineno, m))

    report_lines: list[str] = [
        "# Wikilink validation (phase57)\n",
        "\n",
        "_Targets are checked against existing `.md` files under this tree (excluding `.obsidian/`)._\n\n",
        f"**Brain root:** `{parent}`\n\n",
        "## Orphan [[wikilinks]] (no matching note)\n\n",
    ]

    orphans = 0
    for file, line, match in sorted(links, key=lambda t: (str(t[0]), t[1], t[2])):
        inner = match[2:-2] if match.startswith("[[") else match
        raw = inner
        inner_body = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not inner_body:
            continue
        if _resolve_target(parent, idx, raw):
            continue
        orphans += 1
        report_lines.append(
            f"- `{file}` line {line} — `{match}` — no matching `{inner_body}.md`\n",
        )
        log.log_warn(f"orphan_link file={file} line={line} target={inner_body}")

    if orphans == 0:
        report_lines.append("_None found._\n\n")

    report_lines.append("\n## Ambiguous basenames (same note name in multiple folders)\n\n")
    report_lines.append(
        "_Obsidian may pick an arbitrary match; prefer unique slugs (e.g. `ROLE-dir-sub`)._\n\n",
    )

    ambig_groups = [(b, ps) for b, ps in idx.items() if len(ps) > 1]
    ambig_groups.sort(key=lambda t: t[0])
    uniq_amb = 0
    if ambig_groups:
        for b, paths in ambig_groups:
            uniq_amb += 1
            report_lines.append(f"### `{b}` ({len(paths)} files)\n\n")
            for p in paths:
                report_lines.append(f"- `{p}`\n")
            report_lines.append("\n")
        log.log_stat(f"phase=5.7 ambiguous_basename_groups={uniq_amb}")
    else:
        report_lines.append("_None._\n\n")

    report_lines.extend(
        [
            "\n## How to fix orphans\n\n",
            "1. **Re-run scan** after slug fixes: phase4 + phase56 use the same directory slug; mismatched `ROLE` vs repo folder basename breaks module filenames.\n",
            "2. **Rename or add** the missing note so the basename matches the link text before `|` or `#`.\n",
            "3. **Remove or replace** stale hand-written `[[...]]` in stubs after refactors.\n",
        ],
    )

    report = "".join(report_lines)
    if write_report:
        out = parent / "wikilink-orphan-report.md"
        out.write_text(report, encoding="utf-8", errors="replace")
        log.log_stat(f"phase=5.7 orphans={orphans} report={out}")
        print(f"Wrote {out}")
    else:
        log.log_stat(f"phase=5.7 orphans={orphans} (stdout only; pass --write-report for markdown file)")
        print(report)

    log.log_done(f"orphans={orphans} ambiguous_basename_groups={uniq_amb}")
