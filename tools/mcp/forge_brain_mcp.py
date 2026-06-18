#!/usr/bin/env python3
"""Forge Brain MCP server — exposes the git-backed Forge brain to any MCP client.

A minimal, dependency-free Model Context Protocol server (JSON-RPC 2.0 over stdio,
newline-delimited) that lets Claude Code — or any MCP client — query the Forge
brain without a Forge session loaded. It is **read-only**: it never writes,
edits, or deletes brain files.

Why this exists: the brain is Forge's system of record (PRDs, specs, decisions,
eval verdicts, conductor phase logs). Exposing it over MCP turns Forge from "a
plugin you must be inside" into a memory layer any agent can consult. Shipping an
MCP *surface* does not violate D5/D13 — it bundles no agent framework and adds no
runtime dependency (stdlib only).

Tools (all read-only, all confined to the brain root):
  brain_read              read a brain file, or list a directory
  brain_list              list a brain directory tree (shallow)
  brain_recall            case-insensitive substring search across brain markdown
  brain_why               provenance for a file/decision (git log + frontmatter)
  brain_conductor_status  latest conductor.log phase markers for a task (or all)

Also exposes (all read-only):
  resources/*  every brain text file as an MCP resource (uri brain:///<path>),
               plus a brain:///{path} template — so MCP clients can browse and read
               the brain as resources, not only by calling tools.
  prompts/*    task_brief, decision_provenance, recall_brain — ready-made prompts
               that pull the relevant brain content inline for one-shot questions.

Brain root resolution (first match wins):
  $FORGE_BRAIN  ->  $FORGE_BRAIN_PATH  ->  ~/forge/brain

Protocol notes:
- stdio transport is newline-delimited JSON-RPC; one message per line.
- Nothing but JSON-RPC may be written to stdout. Diagnostics go to stderr.

Run standalone for a smoke test:
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
                '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 tools/mcp/forge_brain_mcp.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SERVER_NAME = "forge-brain"
SERVER_VERSION = "1.2.0"
DEFAULT_PROTOCOL = "2025-06-18"
MAX_FILE_BYTES = 200_000
MAX_RECALL_RESULTS = 50
MAX_RESOURCES = 200  # resources/list page size; the rest paginate via an offset cursor
TEXT_SUFFIXES = (".md", ".csv", ".log", ".json", ".txt", ".tsv")
RESOURCE_SCHEME = "brain:///"


def log(msg: str) -> None:
    print(f"[forge-brain-mcp] {msg}", file=sys.stderr, flush=True)


def brain_root() -> Path:
    for env in ("FORGE_BRAIN", "FORGE_BRAIN_PATH"):
        v = os.environ.get(env)
        if v:
            return Path(v).expanduser()
    return Path.home() / "forge" / "brain"


def _safe(root: Path, rel: str) -> Path | None:
    """Resolve rel under root; return None on traversal outside root."""
    target = (root / rel).resolve()
    root_r = root.resolve()
    if target == root_r or str(target).startswith(str(root_r) + os.sep):
        return target
    return None


# ── Tool implementations (return plain text) ──────────────────────────────

def tool_brain_read(args: dict) -> str:
    root = brain_root()
    rel = (args.get("path") or ".").strip()
    if not root.exists():
        return f"Brain root does not exist: {root}"
    target = _safe(root, rel)
    if target is None:
        return f"Refused: path escapes the brain root ({rel!r})."
    if not target.exists():
        return f"Not found: {rel}"
    if target.is_dir():
        return tool_brain_list({"path": rel})
    data = target.read_bytes()
    truncated = ""
    if len(data) > MAX_FILE_BYTES:
        data = data[:MAX_FILE_BYTES]
        truncated = f"\n\n[truncated at {MAX_FILE_BYTES} bytes]"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return f"{rel} is not UTF-8 text ({len(data)} bytes)."
    return f"# {rel}\n\n{text}{truncated}"


def tool_brain_list(args: dict) -> str:
    root = brain_root()
    rel = (args.get("path") or ".").strip()
    if not root.exists():
        return f"Brain root does not exist: {root}"
    target = _safe(root, rel)
    if target is None:
        return f"Refused: path escapes the brain root ({rel!r})."
    if not target.exists():
        return f"Not found: {rel}"
    if target.is_file():
        return f"{rel} (file, {target.stat().st_size} bytes)"
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [f"{rel.rstrip('/')}/" if rel != "." else "(brain root)"]
    for p in entries:
        if p.name.startswith(".git"):
            continue
        mark = "/" if p.is_dir() else ""
        size = "" if p.is_dir() else f"  ({p.stat().st_size} B)"
        lines.append(f"  {p.name}{mark}{size}")
    return "\n".join(lines)


def tool_brain_recall(args: dict) -> str:
    root = brain_root()
    query = (args.get("query") or "").strip()
    if not query:
        return "Provide a non-empty 'query'."
    if not root.exists():
        return f"Brain root does not exist: {root}"
    try:
        limit = int(args.get("max_results", 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, MAX_RECALL_RESULTS))
    q = query.lower()
    hits: list[str] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                for n, line in enumerate(fh, 1):
                    if q in line.lower():
                        rel = path.relative_to(root)
                        hits.append(f"{rel}:{n}: {line.strip()[:200]}")
                        if len(hits) >= limit:
                            break
        except OSError:
            continue
        if len(hits) >= limit:
            break
    if not hits:
        return f"No matches for {query!r} under {root}"
    header = f"{len(hits)} match(es) for {query!r} (limit {limit}):"
    return header + "\n" + "\n".join(hits)


def _git(root: Path, *git_args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(root), *git_args],
            capture_output=True, text=True, timeout=15,
        )
        return r.returncode, (r.stdout or r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def _frontmatter(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[: end + 4]
    return ""


def tool_brain_why(args: dict) -> str:
    root = brain_root()
    target = (args.get("target") or "").strip()
    if not target:
        return "Provide 'target' (a brain-relative file path or a decision id like D102)."
    if not root.exists():
        return f"Brain root does not exist: {root}"
    # Resolve a decision id (D###) to a file if needed.
    path = _safe(root, target)
    if path is None or not path.exists():
        matches = [p for p in root.rglob(f"*{target}*") if p.is_file() and p.suffix == ".md"]
        if not matches:
            return f"No brain file matches {target!r}."
        path = matches[0]
    rel = path.relative_to(root)
    out = [f"Provenance for {rel}:", ""]
    fm = _frontmatter(path)
    if fm:
        out += ["Frontmatter:", fm, ""]
    code, log_out = _git(root, "log", "--oneline", "-n", "20", "--", str(rel))
    if code == 0 and log_out:
        out += ["Git history (newest first):", log_out]
    else:
        out += ["(brain is not a git repo, or no history for this file)"]
    return "\n".join(out)


def tool_brain_conductor_status(args: dict) -> str:
    root = brain_root()
    prds = root / "prds"
    if not prds.exists():
        return f"No prds/ directory under {root}"
    task_id = (args.get("task_id") or "").strip()

    def last_markers(log_path: Path, n: int = 8) -> str:
        try:
            lines = [ln.strip() for ln in log_path.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
        except OSError:
            return "(unreadable)"
        markers = [ln for ln in lines if ln.startswith("[") or "P4" in ln or "P1" in ln]
        tail = (markers or lines)[-n:]
        return "\n    ".join(tail) if tail else "(empty)"

    if task_id:
        log_path = prds / task_id / "conductor.log"
        if not log_path.exists():
            return f"No conductor.log for task {task_id} (looked at {log_path})."
        return f"conductor.log — {task_id} (last markers):\n    {last_markers(log_path)}"

    out = []
    for d in sorted(prds.iterdir()):
        lp = d / "conductor.log"
        if lp.exists():
            out.append(f"{d.name}:\n    {last_markers(lp, 4)}")
    return "\n\n".join(out) if out else "No conductor.log found under any prds/<task-id>/."


# ── Resources (every brain text file as an MCP resource) ──────────────────

def _iter_brain_files(root: Path):
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _mime(path: Path) -> str:
    return "text/markdown" if path.suffix.lower() == ".md" else "text/plain"


def _rel_from_uri(uri: str) -> str | None:
    for prefix in ("brain:///", "brain://"):
        if uri.startswith(prefix):
            return uri[len(prefix):]
    return None


def list_resources(cursor) -> dict:
    root = brain_root()
    if not root.exists():
        return {"resources": []}
    files = list(_iter_brain_files(root))
    try:
        start = int(cursor) if cursor else 0
    except (TypeError, ValueError):
        start = 0
    page = files[start:start + MAX_RESOURCES]
    resources = [
        {"uri": RESOURCE_SCHEME + str(p.relative_to(root)),
         "name": str(p.relative_to(root)),
         "mimeType": _mime(p)}
        for p in page
    ]
    result = {"resources": resources}
    nxt = start + MAX_RESOURCES
    if nxt < len(files):
        result["nextCursor"] = str(nxt)
    return result


def list_resource_templates() -> dict:
    return {"resourceTemplates": [{
        "uriTemplate": "brain:///{path}",
        "name": "brain-file",
        "description": "Any text file under the Forge brain root, addressed by its relative path.",
        "mimeType": "text/markdown",
    }]}


def read_resource(uri: str) -> dict:
    root = brain_root()
    rel = _rel_from_uri(uri)
    if rel is None:
        raise ValueError(f"unsupported resource URI {uri!r} (expected brain:///<path>)")
    target = _safe(root, rel) if root.exists() else None
    if target is None or not target.exists() or target.is_dir():
        raise FileNotFoundError(uri)
    data = target.read_bytes()[:MAX_FILE_BYTES]
    return {"contents": [{"uri": uri, "mimeType": _mime(target),
                          "text": data.decode("utf-8", errors="replace")}]}


# ── Prompts (ready-made questions that embed the relevant brain content) ───

PROMPTS = [
    {
        "name": "task_brief",
        "description": "Pull a task's locked PRD, shared-dev-spec, and conductor status inline, then ask for a scope/contracts/status summary.",
        "arguments": [{"name": "task_id", "description": "Task id under prds/.", "required": True}],
    },
    {
        "name": "decision_provenance",
        "description": "Embed a decision's provenance (frontmatter + git history) and ask why it was made and what it superseded.",
        "arguments": [{"name": "target", "description": "Brain-relative file path or a decision id (e.g. D102).", "required": True}],
    },
    {
        "name": "recall_brain",
        "description": "Search the brain for a term and embed the matching lines, then ask for a synthesis of prior art.",
        "arguments": [{"name": "query", "description": "Text to search the brain for.", "required": True}],
    },
]
PROMPTS_BY_NAME = {p["name"]: p for p in PROMPTS}


def _user_msg(text: str) -> dict:
    return {"role": "user", "content": {"type": "text", "text": text}}


def get_prompt(name: str, arguments: dict) -> dict:
    if name == "task_brief":
        tid = (arguments.get("task_id") or "").strip()
        if not tid:
            raise ValueError("task_brief requires 'task_id'.")
        prd = tool_brain_read({"path": f"prds/{tid}/prd-locked.md"})
        spec = tool_brain_read({"path": f"prds/{tid}/shared-dev-spec.md"})
        if spec.startswith("Not found"):
            spec = tool_brain_read({"path": f"prds/{tid}/shared-dev-spec.DRAFT.md"})
        status = tool_brain_conductor_status({"task_id": tid})
        text = (
            f"Below is the locked PRD, shared-dev-spec, and conductor status for Forge task {tid}.\n\n"
            f"=== PRD ===\n{prd}\n\n=== SHARED-DEV-SPEC ===\n{spec}\n\n=== CONDUCTOR STATUS ===\n{status}\n\n"
            "Summarize: the scope, the contracts and their producers/consumers, the current phase, "
            "and any unresolved conflicts or blockers."
        )
        return {"description": f"Brief for task {tid}", "messages": [_user_msg(text)]}

    if name == "decision_provenance":
        target = (arguments.get("target") or "").strip()
        if not target:
            raise ValueError("decision_provenance requires 'target'.")
        text = (
            f"Provenance for {target} from the Forge brain:\n\n{tool_brain_why({'target': target})}\n\n"
            "Explain why this decision was made, what (if anything) it supersedes, and whether it is still current."
        )
        return {"description": f"Provenance for {target}", "messages": [_user_msg(text)]}

    if name == "recall_brain":
        query = (arguments.get("query") or "").strip()
        if not query:
            raise ValueError("recall_brain requires 'query'.")
        text = (
            f"Brain matches for {query!r}:\n\n{tool_brain_recall({'query': query})}\n\n"
            "Synthesize the prior art: what has already been decided or learned about this, and where it lives."
        )
        return {"description": f"Recall: {query}", "messages": [_user_msg(text)]}

    raise ValueError(f"unknown prompt: {name}")


TOOLS = [
    {
        "name": "brain_read",
        "description": "Read a Forge brain file (returns its text), or list a directory if the path is a folder. Path is relative to the brain root.",
        "handler": tool_brain_read,
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Brain-relative path, e.g. 'prds/<task-id>/prd-locked.md' or 'decisions/'"}},
            "required": ["path"],
        },
    },
    {
        "name": "brain_list",
        "description": "List a Forge brain directory (one level). Use to discover what exists before reading files.",
        "handler": tool_brain_list,
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Brain-relative directory; '.' for the brain root."}},
        },
    },
    {
        "name": "brain_recall",
        "description": "Case-insensitive substring search across brain markdown/csv/log/json/txt files. Returns file:line snippets.",
        "handler": tool_brain_recall,
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search for."},
                "max_results": {"type": "integer", "description": "Max hits (1-50, default 20)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "brain_why",
        "description": "Provenance for a brain decision/file: its YAML frontmatter plus git history (who/when/why). Accepts a brain-relative path or a decision id (e.g. D102).",
        "handler": tool_brain_why,
        "inputSchema": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "Brain-relative file path or decision id."}},
            "required": ["target"],
        },
    },
    {
        "name": "brain_conductor_status",
        "description": "Latest conductor.log phase markers for a task (task_id), or a summary across all tasks under prds/ when task_id is omitted.",
        "handler": tool_brain_conductor_status,
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string", "description": "Task id under prds/. Omit for an all-tasks summary."}},
        },
    },
]
TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


# ── JSON-RPC plumbing ─────────────────────────────────────────────────────

def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle(msg: dict):
    method = msg.get("method")
    msg_id = msg.get("id")
    is_request = msg_id is not None

    if method == "initialize":
        proto = (msg.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
        return _result(msg_id, {
            "protocolVersion": proto,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method in ("notifications/initialized", "initialized"):
        return None  # notification — no response

    if method == "ping":
        return _result(msg_id, {})

    if method == "tools/list":
        listed = [{"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]} for t in TOOLS]
        return _result(msg_id, {"tools": listed})

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = TOOLS_BY_NAME.get(name)
        if not tool:
            return _error(msg_id, -32602, f"Unknown tool: {name}")
        try:
            text = tool["handler"](arguments)
        except Exception as e:  # never crash the server on a tool error
            log(f"tool {name} error: {e}")
            return _result(msg_id, {"content": [{"type": "text", "text": f"Tool error: {e}"}], "isError": True})
        return _result(msg_id, {"content": [{"type": "text", "text": text}]})

    if method == "resources/list":
        cursor = (msg.get("params") or {}).get("cursor")
        return _result(msg_id, list_resources(cursor))

    if method == "resources/templates/list":
        return _result(msg_id, list_resource_templates())

    if method == "resources/read":
        uri = (msg.get("params") or {}).get("uri") or ""
        try:
            return _result(msg_id, read_resource(uri))
        except FileNotFoundError:
            return _error(msg_id, -32002, f"Resource not found: {uri}")
        except ValueError as e:
            return _error(msg_id, -32602, str(e))
        except Exception as e:
            log(f"resources/read error: {e}")
            return _error(msg_id, -32603, f"Internal error: {e}")

    if method == "prompts/list":
        listed = [{k: v for k, v in p.items()} for p in PROMPTS]
        return _result(msg_id, {"prompts": listed})

    if method == "prompts/get":
        params = msg.get("params") or {}
        name = params.get("name")
        if name not in PROMPTS_BY_NAME:
            return _error(msg_id, -32602, f"Unknown prompt: {name}")
        try:
            return _result(msg_id, get_prompt(name, params.get("arguments") or {}))
        except ValueError as e:
            return _error(msg_id, -32602, str(e))
        except Exception as e:
            log(f"prompts/get error: {e}")
            return _error(msg_id, -32603, f"Internal error: {e}")

    if is_request:
        return _error(msg_id, -32601, f"Method not found: {method}")
    return None  # unknown notification


def main() -> int:
    log(f"started; brain root = {brain_root()}")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log(f"skipping non-JSON line: {raw[:80]!r}")
            continue
        try:
            response = handle(msg)
        except Exception as e:  # protocol-level guard
            response = _error(msg.get("id"), -32603, f"Internal error: {e}")
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
