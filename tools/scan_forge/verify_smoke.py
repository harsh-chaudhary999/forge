#!/usr/bin/env python3
"""Smoke-test scan_forge using ephemeral fixture repos (nothing under fixtures/ required).

Role names used here (``svc`` and ``ui``) are arbitrary smoke labels — Forge imposes no
naming convention. Real products pass whatever ``--repos <role>:<path>`` labels fit their
stack (``api``, ``bff``, ``worker``, ``mobile``, ``gateway``, …).
"""
from __future__ import annotations

import json
import os
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
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "tools")
        cmd = [
            sys.executable,
            "-m",
            "scan_forge",
            "--run-dir", str(run_dir),
            "--brain-codebase", str(brain),
            "--skip-phase57",
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
        assert (brain / "SCAN_SUMMARY.md").is_file()
        assert (brain / ".forge_scan_manifest.json").is_file()

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
    finally:
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(brain, ignore_errors=True)
        shutil.rmtree(fixtures_parent, ignore_errors=True)

    print("verify_smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
