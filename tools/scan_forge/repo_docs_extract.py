"""Extraction layer for repo_docs_mirror — transforms raw docs into brain-usable format.

Each mirrored Markdown file gets:
  1. YAML frontmatter  — source_repo, source_file, commit, doc_type, scanned_at
  2. Heading outline   — extracted ## / ### hierarchy appended as a navigable block
  3. ADR fields        — Status / Context / Decision / Consequences parsed from ADR files
  4. Brain node links  — wikilinks to matching modules/classes in the brain graph
  5. Search index      — one row per section across all docs → repo-docs/SEARCH_INDEX.md

OpenAPI/Swagger YAML/JSON files are kept verbatim (they're structured data, not narrative).
Non-.md doc files (.rst, .adoc, .txt) in doc dirs are kept verbatim but indexed for headings.

Bump _EXTRACT_VERSION when enrichment logic changes to force re-enrichment on next scan.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_EXTRACT_VERSION = 1

# Common words to skip when matching doc text to brain node names
_STOP_WORDS = frozenset({
    "the", "and", "for", "are", "was", "with", "this", "that", "from", "have",
    "not", "but", "all", "can", "will", "use", "used", "been", "when", "also",
    "its", "it", "in", "of", "to", "a", "an", "or", "is", "be", "as", "at",
    "by", "on", "if", "so", "do", "we", "our", "you", "any", "more", "has",
    "into", "than", "then", "they", "their", "there", "which", "what", "how",
    "new", "each", "one", "two", "see", "get", "set", "run", "add", "per",
})

_ADR_PATH_RE = re.compile(r"(?:^|/)(?:adr|decisions|decision|architecture-decisions)/", re.IGNORECASE)
_ADR_FILE_RE = re.compile(r"^\d{2,4}[-_]")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


# ---------------------------------------------------------------------------
# Doc type detection
# ---------------------------------------------------------------------------

def detect_doc_type(rel_posix: str, text: str) -> str:
    r = rel_posix.replace("\\", "/").lower()
    base = r.rsplit("/", 1)[-1]

    if base in ("readme.md", "readme.rst", "readme.txt"):
        return "readme"
    if base in ("contributing.md", "contributing.rst"):
        return "contributing"
    if base in ("changelog.md", "changelog.rst", "history.md"):
        return "changelog"
    if base in ("security.md",):
        return "security"
    if base in ("architecture.md", "architecture.rst"):
        return "architecture"
    if _ADR_PATH_RE.search(r) or _ADR_FILE_RE.match(base):
        return "adr"
    if "/guides/" in f"/{r}/" or r.startswith("guides/"):
        return "guide"
    if "/rfc/" in f"/{r}/" or r.startswith("rfc/"):
        return "rfc"
    if base.startswith("openapi") or base.startswith("swagger"):
        return "openapi"
    if "/docs/" in f"/{r}/" or r.startswith("docs/") or "/doc/" in f"/{r}/":
        # Try to sub-classify by content signals
        tl = text[:2000].lower()
        if re.search(r"\bstatus\s*:\s*(accepted|proposed|deprecated|superseded)\b", tl):
            return "adr"
        if "## api" in tl or "endpoint" in tl or "request" in tl:
            return "api-reference"
        return "guide"
    return "doc"


# ---------------------------------------------------------------------------
# Heading extraction
# ---------------------------------------------------------------------------

def extract_headings(text: str) -> list[tuple[int, str, int]]:
    """Return list of (level, title, line_number) for all ATX headings."""
    # Strip existing frontmatter before scanning
    body = _FRONTMATTER_RE.sub("", text, count=1)
    results: list[tuple[int, str, int]] = []
    for lineno, line in enumerate(body.splitlines(), start=1):
        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            results.append((level, title, lineno))
    return results


# ---------------------------------------------------------------------------
# ADR parsing
# ---------------------------------------------------------------------------

_ADR_SECTION_RE = re.compile(
    r"^#{1,3}\s*(status|context|decision|consequences|rationale|alternatives?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_adr_fields(text: str) -> dict[str, str]:
    """Extract key ADR fields from Markdown. Returns dict with present fields only."""
    fields: dict[str, str] = {}

    # Status from inline pattern: "**Status:** Accepted"
    m = re.search(r"\*{0,2}[Ss]tatus\*{0,2}\s*:?\*{0,2}\s*([A-Za-z][A-Za-z ]{1,30})", text)
    if m:
        fields["status"] = m.group(1).strip()

    # Extract section content for known ADR headings
    sections = list(_ADR_SECTION_RE.finditer(text))
    for i, match in enumerate(sections):
        key = match.group(1).lower().rstrip("s")  # "alternatives" → "alternative"
        start = match.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        content = text[start:end].strip()
        # Keep first 300 chars, collapse whitespace
        snippet = " ".join(content.split())[:300]
        if snippet:
            fields[key] = snippet

    return fields


# ---------------------------------------------------------------------------
# Brain node wikilink matching
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"\b([a-z][a-z0-9]{2,}(?:-[a-z0-9]{2,})*)\b")


def find_brain_links(text: str, brain_codebase: Path, role: str) -> list[str]:
    """Return sorted list of brain wikilink paths (e.g. 'modules/svc-auth') found in text."""
    # Collect candidate brain nodes: modules + classes
    candidates: dict[str, str] = {}  # search_term -> wiki_path
    for subdir in ("modules", "classes"):
        d = brain_codebase / subdir
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            slug = f.stem  # e.g. "svc-auth-service"
            # Strip role prefix to get meaningful words
            without_role = slug[len(role) + 1:] if slug.startswith(f"{role}-") else slug
            parts = without_role.split("-")
            for part in parts:
                if len(part) >= 4 and part not in _STOP_WORDS:
                    candidates[part] = f"{subdir}/{slug}"
            # Also try multi-word: "auth-service" → search for "auth"
            if len(without_role) >= 4 and without_role not in _STOP_WORDS:
                candidates[without_role] = f"{subdir}/{slug}"

    if not candidates:
        return []

    # Find which candidates appear in the doc text (case-insensitive word boundary)
    text_lower = text.lower()
    found: set[str] = set()
    for term, wiki_path in candidates.items():
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, text_lower):
            found.add(wiki_path)

    return sorted(found)


# ---------------------------------------------------------------------------
# Section-level search index rows
# ---------------------------------------------------------------------------

def extract_search_rows(
    role: str,
    rel: str,
    text: str,
    doc_type: str,
) -> list[dict[str, str]]:
    """Return one search row per section (heading + first non-empty paragraph)."""
    rows: list[dict[str, str]] = []
    body = _FRONTMATTER_RE.sub("", text, count=1)
    lines = body.splitlines()

    current_heading = f"({rel})"  # fallback if doc has no headings
    current_level = 1
    buffer: list[str] = []

    def _flush(heading: str, level: int, buf: list[str]) -> None:
        para = " ".join(" ".join(l.split()) for l in buf if l.strip())[:200]
        if para:
            rows.append({
                "role": role,
                "source": rel,
                "doc_type": doc_type,
                "heading": heading,
                "level": str(level),
                "summary": para,
            })

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            _flush(current_heading, current_level, buffer)
            buffer = []
            current_level = len(m.group(1))
            current_heading = m.group(2).strip()
        else:
            buffer.append(line)

    _flush(current_heading, current_level, buffer)
    return rows


# ---------------------------------------------------------------------------
# Main enrichment entry point
# ---------------------------------------------------------------------------

def enrich_markdown(
    source_bytes: bytes,
    rel: str,
    role: str,
    commit: str,
    scanned_at: str,
    brain_codebase: Path,
) -> tuple[bytes, dict[str, Any]]:
    """Return (enriched_bytes, metadata) for one Markdown file.

    metadata keys: doc_type, headings_count, adr_fields, brain_links_count, search_rows
    """
    text = source_bytes.decode("utf-8", errors="replace")
    doc_type = detect_doc_type(rel, text)
    headings = extract_headings(text)

    # --- Frontmatter ---
    fm_lines = [
        "---",
        f"source_repo: {role}",
        f"source_file: {rel}",
        f"commit: {commit[:12]}",
        f"doc_type: {doc_type}",
        f"scanned_at: {scanned_at}",
        f"extract_version: {_EXTRACT_VERSION}",
        "---",
        "",
    ]
    enriched = "\n".join(fm_lines) + text

    # --- Heading outline (only for docs with 3+ headings to avoid noise) ---
    if len(headings) >= 3:
        outline_lines = ["", "---", "", "## Document outline _(auto)_", ""]
        for level, title, lineno in headings:
            indent = "  " * (level - 1)
            outline_lines.append(f"{indent}- {title} _(line {lineno})_")
        enriched += "\n".join(outline_lines) + "\n"

    # --- ADR structured fields ---
    adr_fields: dict[str, str] = {}
    if doc_type == "adr":
        adr_fields = parse_adr_fields(text)
        if adr_fields:
            adr_lines = ["", "---", "", "## ADR fields _(auto)_", ""]
            for k, v in adr_fields.items():
                adr_lines.append(f"**{k.capitalize()}:** {v}")
                adr_lines.append("")
            enriched += "\n".join(adr_lines) + "\n"

    # --- Brain node wikilinks ---
    brain_links = find_brain_links(text, brain_codebase, role)
    if brain_links:
        link_lines = ["", "---", "", "## Related brain nodes _(auto)_", ""]
        for lnk in brain_links:
            link_lines.append(f"- [[{lnk}]]")
        enriched += "\n".join(link_lines) + "\n"

    # --- Search rows (returned to caller for index building) ---
    search_rows = extract_search_rows(role, rel, text, doc_type)

    meta: dict[str, Any] = {
        "doc_type": doc_type,
        "headings_count": len(headings),
        "adr_fields": adr_fields,
        "brain_links_count": len(brain_links),
        "search_rows": search_rows,
    }

    return enriched.encode("utf-8"), meta


# ---------------------------------------------------------------------------
# Search index writer
# ---------------------------------------------------------------------------

def write_search_index(root: Path, all_rows: list[dict[str, str]]) -> None:
    """Write repo-docs/SEARCH_INDEX.md — one row per document section."""
    if not all_rows:
        return
    lines = [
        "# Repo docs search index _(auto)_",
        "",
        "_One row per section across all mirrored docs. Use this to find relevant "
        "documentation before reading full files._",
        "",
        "| Role | Doc | Type | Heading | Summary |",
        "|---|---|---|---|---|",
    ]
    for row in all_rows:
        role = row["role"]
        src = row["source"]
        doc_type = row["doc_type"]
        heading = row["heading"].replace("|", "\\|")
        summary = row["summary"].replace("|", "\\|")
        lines.append(f"| `{role}` | `{src}` | {doc_type} | {heading} | {summary} |")
    lines.append("")
    (root / "SEARCH_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
