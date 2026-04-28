#!/usr/bin/env python3
"""Smoke-test scan_forge using ephemeral fixture repos (nothing under fixtures/ required).

Role names used here (``svc`` and ``ui``) are arbitrary smoke labels — Forge imposes no
naming convention. Real products pass whatever ``--repos <role>:<path>`` labels fit their
stack (``api``, ``bff``, ``worker``, ``mobile``, ``gateway``, …).
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

# Arbitrary role names — deliberately NOT "backend"/"web" to avoid implying convention.
_ROLE_SVC = "svc"
_ROLE_UI = "ui"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True)


def _git_init_and_commit(repo: Path, message: str) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "smoke@example.com")
    _git(repo, "config", "user.name", "Smoke Bot")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)


def _write_smoke_fixtures(parent: Path) -> tuple[Path, Path]:
    """Write two minimal fake repos under parent/<role>/."""
    svc = parent / _ROLE_SVC
    ui = parent / _ROLE_UI
    (svc / "src").mkdir(parents=True, exist_ok=True)
    (ui / "src").mkdir(parents=True, exist_ok=True)

    (svc / "src" / "routes.ts").write_text(
        """import express from 'express';

const app = express();

app.get('/api/hello', (_req, res) => {
  res.json({ ok: true });
});

export default app;
""",
        encoding="utf-8",
    )
    (svc / "openapi.json").write_text(
        """{
  "openapi": "3.0.0",
  "info": { "title": "Smoke", "version": "1.0.0" },
  "paths": {
    "/api/hello": {
      "get": { "summary": "hello" }
    }
  }
}
""",
        encoding="utf-8",
    )
    (svc / "src" / "health.test.ts").write_text(
        """import { describe, it } from 'vitest';

describe('health', () => {
  it('responds', () => {
    expect(1).toBe(1);
  });
});
""",
        encoding="utf-8",
    )
    (ui / "index.html").write_text(
        """<!DOCTYPE html>
<html lang="en">
  <head><meta charset="UTF-8" /></head>
  <body>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )
    (ui / "src" / "main.jsx").write_text(
        """/** Vite entry — smoke fixture for HTML → JSX brain links. */
import App from "./App.jsx";

export function main() {
  return App ? 1 : 0;
}

""",
        encoding="utf-8",
    )
    (ui / "src" / "App.jsx").write_text(
        """/** Root component — smoke fixture for JSX → JSX brain links. */
export default function App() {
  return null;
}
""",
        encoding="utf-8",
    )
    (ui / "src" / "client.ts").write_text(
        """export async function loadHello(): Promise<boolean> {
  const response = await fetch('/api/hello');
  return response.ok;
}
""",
        encoding="utf-8",
    )

    # Repo-docs mirror fixtures — policy applied to svc only
    (svc / "docs").mkdir(parents=True, exist_ok=True)
    (svc / "docs" / "api.md").write_text("# API notes\n\nSmoke fixture for repo-docs mirror.\n", encoding="utf-8")
    (svc / "extras").mkdir(parents=True, exist_ok=True)
    (svc / "extras" / "special.md").write_text("# Extra\n\nPolicy allow_extra.\n", encoding="utf-8")
    (svc / "CHANGELOG.md").write_text("# Changelog\n\nIndex-only smoke.\n", encoding="utf-8")
    (svc / "DO_NOT_MIRROR_secret.md").write_text("# Secret\n", encoding="utf-8")
    (svc / "forge-scan-docs.policy.yaml").write_text(
        "version: 1\n"
        "deny_path_contains:\n"
        '  - "DO_NOT_MIRROR"\n'
        "allow_extra_path_contains:\n"
        '  - "extras/"\n'
        "index_only_path_contains:\n"
        '  - "CHANGELOG"\n',
        encoding="utf-8",
    )
    (ui / "README.md").write_text("# UI smoke\n\nRoot readme for repo-docs mirror.\n", encoding="utf-8")

    return svc, ui


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    run_dir = Path(tempfile.mkdtemp(prefix="forge_scan_smoke."))
    brain = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_brain."))
    fixtures_parent = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_fixtures."))
    try:
        svc_repo, ui_repo = _write_smoke_fixtures(fixtures_parent)
        _git_init_and_commit(svc_repo, "initial svc fixtures")
        _git_init_and_commit(ui_repo, "initial ui fixtures")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "tools")
        cmd = [
            sys.executable,
            "-m",
            "scan_forge",
            "--run-dir", str(run_dir),
            "--brain-codebase", str(brain),
            "--skip-phase57",
            "--incremental",
            "--repos",
            f"{_ROLE_SVC}:{svc_repo}",
            f"{_ROLE_UI}:{ui_repo}",
        ]
        subprocess.run(cmd, check=True, cwd=str(root), env=env)

        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert meta.get("status") == "ok", meta
        assert isinstance(meta.get("phase_timings_ms"), dict), meta
        assert meta.get("total_elapsed_ms", 0) > 0, meta
        assert (run_dir / "_role" / _ROLE_SVC / "forge_scan_source_files.txt").is_file()
        assert (run_dir / "_role" / _ROLE_UI / "forge_scan_source_files.txt").is_file()

        routes = run_dir / "forge_scan_api_routes.txt"
        text = routes.read_text(encoding="utf-8", errors="replace")
        assert "/api/hello" in text, routes

        scan_doc = json.loads((brain / "SCAN.json").read_text(encoding="utf-8"))
        repos_map = scan_doc.get("repos")
        assert isinstance(repos_map, dict) and _ROLE_SVC in repos_map and _ROLE_UI in repos_map, scan_doc
        assert scan_doc.get("source_files", 0) >= 2

        g = json.loads((brain / "graph.json").read_text(encoding="utf-8"))
        assert g.get("forge_scan_graph_version") == 1
        assert isinstance(g.get("nodes"), list)
        assert isinstance(g.get("edges"), list)
        edge_db = brain / "forge_scan_edges.sqlite"
        assert edge_db.is_file(), edge_db
        with sqlite3.connect(str(edge_db)) as conn:
            row = conn.execute("select count(*) from edges").fetchone()
        assert row and int(row[0]) >= 0
        assert (brain / "SCAN_SUMMARY.md").is_file()
        assert (brain / ".forge_scan_manifest.json").is_file()
        assert (brain / "index.md").is_file(), "cli must write codebase index before verify"

        # Page wikilinks (role-prefixed by the scan)
        index_page = brain / "pages" / f"{_ROLE_UI}-index-html.md"
        main_page  = brain / "pages" / f"{_ROLE_UI}-src-main-jsx.md"
        app_page   = brain / "pages" / f"{_ROLE_UI}-src-app-jsx.md"
        assert index_page.is_file(), index_page
        assert main_page.is_file(), main_page
        assert app_page.is_file(), app_page
        ix = index_page.read_text(encoding="utf-8", errors="replace")
        mx = main_page.read_text(encoding="utf-8", errors="replace")
        ap = app_page.read_text(encoding="utf-8", errors="replace")
        assert f"[[pages/{_ROLE_UI}-src-main-jsx]]" in ix, "index.html page should wikilink main.jsx"
        assert f"[[pages/{_ROLE_UI}-index-html]]" in mx, "main.jsx page should wikilink back to index.html"
        assert f"[[pages/{_ROLE_UI}-src-app-jsx]]" in mx, "main.jsx should wikilink App.jsx via static import"
        assert f"[[pages/{_ROLE_UI}-src-main-jsx]]" in ap, "App.jsx should show Imported by main.jsx"

        mod_svc_src = brain / "modules" / f"{_ROLE_SVC}-src.md"
        assert mod_svc_src.is_file(), mod_svc_src
        msrc = mod_svc_src.read_text(encoding="utf-8", errors="replace")
        assert "## HTTP routes (auto)" in msrc, "svc src module should list API paths from route inventory"
        assert "/api/hello" in msrc, "route inventory should surface /api/hello on module note"

        # Repo-docs mirror assertions
        mirrored_api    = brain / "repo-docs" / _ROLE_SVC / "docs" / "api.md"
        mirrored_readme = brain / "repo-docs" / _ROLE_UI / "README.md"
        assert mirrored_api.is_file(), mirrored_api
        assert mirrored_readme.is_file(), mirrored_readme
        api_text = mirrored_api.read_text(encoding="utf-8")
        # Enriched: frontmatter present
        assert api_text.startswith("---\n"), "mirrored .md should start with YAML frontmatter"
        assert "source_repo:" in api_text
        assert "doc_type:" in api_text
        # Original content preserved
        assert "Smoke fixture" in api_text
        # readme enriched with correct doc_type
        readme_text = mirrored_readme.read_text(encoding="utf-8")
        assert "doc_type: readme" in readme_text, readme_text[:300]
        # Search index built
        assert (brain / "repo-docs" / "SEARCH_INDEX.md").is_file()
        search_text = (brain / "repo-docs" / "SEARCH_INDEX.md").read_text(encoding="utf-8")
        assert _ROLE_SVC in search_text, "search index should contain svc role rows"
        assert (brain / "repo-docs" / "INDEX.md").is_file()
        idx = json.loads((brain / "repo-docs" / "index.json").read_text(encoding="utf-8"))
        assert idx.get("forge_repo_docs_mirror_version") == 3
        assert idx.get("enriched_markdown") is True
        assert idx.get("totals", {}).get("snapshot_files", 0) >= 2
        snapshots = idx.get("files") or []
        assert any("source_sha256" in e for e in snapshots)
        # Policy: allow_extra should be mirrored
        assert (brain / "repo-docs" / _ROLE_SVC / "extras" / "special.md").is_file()
        # Policy: index_only CHANGELOG should NOT be copied but appear in index_only list
        assert not (brain / "repo-docs" / _ROLE_SVC / "CHANGELOG.md").is_file()
        index_only = idx.get("index_only") or []
        assert any("CHANGELOG" in e.get("source_relative", "") for e in index_only)
        # Policy: deny should be absent, present in skipped with reason=deny_policy
        skipped = idx.get("skipped") or []
        assert any(
            "DO_NOT_MIRROR" in e.get("source_relative", "") and e.get("reason") == "deny_policy"
            for e in skipped
        )

        # Incremental second run: no git changes -> skip per-role scan phases.
        subprocess.run(cmd, check=True, cwd=str(root), env=env)
        meta2 = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        inc = meta2.get("incremental") or {}
        assert inc.get("enabled") is True
        assert inc.get("changed_files_n") == 0, inc
        assert inc.get("skipped_scan_phases") is True, inc
        state = json.loads((brain / ".forge_scan_file_state.json").read_text(encoding="utf-8"))
        roles = state.get("roles") or {}
        assert _ROLE_SVC in roles and _ROLE_UI in roles
        assert isinstance(roles[_ROLE_SVC].get("tracked_blobs"), dict)
        assert isinstance(roles[_ROLE_UI].get("tracked_blobs"), dict)

        # Incremental third run: uncommitted tracked file change must trigger re-scan.
        routes_ts = svc_repo / "src" / "routes.ts"
        routes_ts.write_text(
            routes_ts.read_text(encoding="utf-8")
            + "\n// uncommitted smoke edit\n",
            encoding="utf-8",
        )
        subprocess.run(cmd, check=True, cwd=str(root), env=env)
        meta3 = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        inc3 = meta3.get("incremental") or {}
        assert inc3.get("enabled") is True
        assert int(inc3.get("changed_files_n", 0)) >= 1, inc3
        assert not inc3.get("skipped_scan_phases", False), inc3

        # Incremental fourth run: rename/delete-heavy + mixed staged/unstaged/untracked.
        _git(ui_repo, "mv", "src/client.ts", "src/client_renamed.ts")
        _git(ui_repo, "rm", "src/App.jsx")
        (ui_repo / "src" / "new_feature.ts").write_text(
            "export const newlyAdded = true;\n",
            encoding="utf-8",
        )
        main_jsx = ui_repo / "src" / "main.jsx"
        main_jsx.write_text(main_jsx.read_text(encoding="utf-8") + "\n// staged edit\n", encoding="utf-8")
        _git(ui_repo, "add", "src/main.jsx")
        main_jsx.write_text(main_jsx.read_text(encoding="utf-8") + "\n// unstaged edit\n", encoding="utf-8")
        subprocess.run(cmd, check=True, cwd=str(root), env=env)
        meta4 = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        inc4 = meta4.get("incremental") or {}
        assert int(inc4.get("changed_files_n", 0)) >= 3, inc4
        assert not inc4.get("skipped_scan_phases", False), inc4
        cp = Path((inc4.get("changed_paths_file") or ""))
        assert cp.is_file(), inc4
        cp_text = cp.read_text(encoding="utf-8")
        assert "client_renamed.ts" in cp_text
        assert "new_feature.ts" in cp_text

        # Non-git fallback: incremental should stay safe and run full path.
        nongit = fixtures_parent / "nongit"
        (nongit / "src").mkdir(parents=True, exist_ok=True)
        (nongit / "src" / "tool.py").write_text(
            "def ping() -> str:\n    return 'pong'\n",
            encoding="utf-8",
        )
        run_dir_ng = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_nongit."))
        brain_ng = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_brain_nongit."))
        cmd_ng = [
            sys.executable,
            "-m",
            "scan_forge",
            "--run-dir", str(run_dir_ng),
            "--brain-codebase", str(brain_ng),
            "--skip-phase57",
            "--incremental",
            "--repos",
            f"misc:{nongit}",
        ]
        subprocess.run(cmd_ng, check=True, cwd=str(root), env=env)
        meta_ng = json.loads((run_dir_ng / "run.json").read_text(encoding="utf-8"))
        inc_ng = meta_ng.get("incremental") or {}
        assert inc_ng.get("enabled") is True
        assert (inc_ng.get("role_mode") or {}).get("misc") == "full_fallback", inc_ng
        rsn = (inc_ng.get("reasons") or {}).get("misc")
        assert rsn in {"no_previous_head", "git_head_unavailable", "previous_head_missing"}, inc_ng
        import shutil
        shutil.rmtree(run_dir_ng, ignore_errors=True)
        shutil.rmtree(brain_ng, ignore_errors=True)
    finally:
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(brain, ignore_errors=True)
        shutil.rmtree(fixtures_parent, ignore_errors=True)

    print("verify_smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
