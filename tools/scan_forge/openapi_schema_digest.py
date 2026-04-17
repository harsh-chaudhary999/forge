"""Emit ``openapi-schema-digest.md`` — shallow ``components.schemas`` field lists per repo.

This does **not** prove React props ↔ DTO bindings; it gives grepable names for LLMs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import log, openapi_routes


def _load_spec_dict(path: Path) -> dict | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(raw) > openapi_routes.MAX_BYTES:
        return None
    if raw.strip().startswith("{"):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    try:
        import yaml  # type: ignore[import-untyped]

        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _deref_schema_name(ref: str) -> str:
    if not isinstance(ref, str):
        return ""
    m = re.match(r"#/components/schemas/(.+)", ref)
    return m.group(1) if m else ""


def _props_lines(schema: object, schemas: dict[str, object], depth: int, cap: int) -> list[str]:
    if depth < 0 or cap <= 0:
        return []
    out: list[str] = []
    if isinstance(schema, dict) and "$ref" in schema:
        name = _deref_schema_name(schema["$ref"])
        if name and name in schemas:
            return _props_lines(schemas[name], schemas, depth, cap)
        return [f"- _(ref {schema['$ref']})_"]
    if not isinstance(schema, dict):
        return []
    props = schema.get("properties")
    if not isinstance(props, dict):
        return []
    for i, (key, val) in enumerate(props.items()):
        if i >= 40:
            out.append(f"- _… ({len(props) - 40} more properties)_")
            break
        typ = "unknown"
        if isinstance(val, dict):
            if "$ref" in val:
                typ = f"ref `{_deref_schema_name(val['$ref']) or val['$ref']}`"
            else:
                typ = str(val.get("type", val.get("format", "object")))
        out.append(f"- `{key}` ({typ})")
    return out


def write_digest(brain_codebase: Path, repos: list[tuple[str, Path]]) -> None:
    """Write ``openapi-schema-digest.md`` under ``brain_codebase``."""
    brain_codebase = brain_codebase.resolve()
    chunks: list[str] = [
        "# OpenAPI schema digest",
        "",
        "_Auto-generated shallow lists from `components.schemas` where present. "
        "Use for LLM / recall — not proof of React prop ↔ field binding._",
        "",
    ]
    any_content = False
    for role, repo in repos:
        repo = repo.resolve()
        specs = openapi_routes.discover_openapi_files(repo)
        if not specs:
            continue
        role_had_schema = False
        sec: list[str] = [f"## Role `{role}` (`{repo.name}`)", ""]
        for spec in specs[:15]:
            data = _load_spec_dict(spec)
            if not data:
                continue
            comps = data.get("components")
            if not isinstance(comps, dict):
                continue
            schemas = comps.get("schemas")
            if not isinstance(schemas, dict) or not schemas:
                continue
            try:
                rel = spec.relative_to(repo).as_posix()
            except ValueError:
                rel = str(spec)
            sec.append(f"### `{rel}`")
            sec.append("")
            for sname, sdef in list(schemas.items())[:80]:
                sec.append(f"#### `{sname}`")
                lines = _props_lines(sdef, schemas, depth=2, cap=50)
                if lines:
                    sec.extend(lines)
                    role_had_schema = True
                else:
                    sec.append("_(no properties or non-object schema)_")
                sec.append("")
        if role_had_schema:
            chunks.extend(sec)
            any_content = True

    if not any_content:
        chunks.append("_No `components.schemas` blocks found in discovered OpenAPI files._")
        chunks.append("")

    out = brain_codebase / "openapi-schema-digest.md"
    out.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8", errors="replace")
    log.log_step(f"openapi_schema_digest written path={out}")
