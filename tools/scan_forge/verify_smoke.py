#!/usr/bin/env python3
"""Smoke-test scan_forge using ephemeral fixture repos (nothing under fixtures/ required)."""
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


def _write_smoke_fixtures(parent: Path) -> tuple[Path, Path]:
    """Minimal backend + web trees matching former tools/scan_forge/fixtures/smoke/*."""
    backend = parent / "backend"
    web = parent / "web"
    (backend / "src").mkdir(parents=True, exist_ok=True)
    (web / "src").mkdir(parents=True, exist_ok=True)
    (backend / "src" / "routes.ts").write_text(
        """import express from 'express';

const app = express();

app.get('/api/hello', (_req, res) => {
  res.json({ ok: true });
});

export default app;
""",
        encoding="utf-8",
    )
    (backend / "openapi.json").write_text(
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
    (backend / "src" / "health.test.ts").write_text(
        """import { describe, it } from 'vitest';

describe('health', () => {
  it('responds', () => {
    expect(1).toBe(1);
  });
});
""",
        encoding="utf-8",
    )
    (web / "index.html").write_text(
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
    (web / "src" / "main.jsx").write_text(
        """/** Vite entry — smoke fixture for HTML → JSX brain links. */
import App from "./App.jsx";

export function main() {
  return App ? 1 : 0;
}

""",
        encoding="utf-8",
    )
    (web / "src" / "App.jsx").write_text(
        """/** Root component — smoke fixture for JSX → JSX brain links. */
export default function App() {
  return null;
}
""",
        encoding="utf-8",
    )
    (web / "src" / "client.ts").write_text(
        """export async function loadHello(): Promise<boolean> {
  const response = await fetch('/api/hello');
  return response.ok;
}
""",
        encoding="utf-8",
    )
    # Repo-docs mirror fixtures
    (backend / "docs").mkdir(parents=True, exist_ok=True)
    (backend / "docs" / "api.md").write_text("# API notes\n\nSmoke fixture for repo-docs mirror.\n", encoding="utf-8")
    (backend / "extras").mkdir(parents=True, exist_ok=True)
    (backend / "extras" / "special.md").write_text("# Extra\n\nPolicy allow_extra.\n", encoding="utf-8")
    (backend / "CHANGELOG.md").write_text("# Changelog\n\nIndex-only smoke.\n", encoding="utf-8")
    (backend / "DO_NOT_MIRROR_secret.md").write_text("# Secret\n", encoding="utf-8")
    (backend / "forge-scan-docs.policy.yaml").write_text(
        "version: 1\n"
        "deny_path_contains:\n"
        '  - "DO_NOT_MIRROR"\n'
        "allow_extra_path_contains:\n"
        '  - "extras/"\n'
        "index_only_path_contains:\n"
        '  - "CHANGELOG"\n',
        encoding="utf-8",
    )
    (web / "README.md").write_text("# Web smoke\n\nRoot readme for repo-docs mirror.\n", encoding="utf-8")
    return backend, web


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    run_dir = Path(tempfile.mkdtemp(prefix="forge_scan_smoke."))
    brain = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_brain."))
    fixtures_parent = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_fixtures."))
    try:
        backend_repo, web_repo = _write_smoke_fixtures(fixtures_parent)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "tools")
        cmd = [
            sys.executable,
            "-m",
            "scan_forge",
            "--run-dir",
            str(run_dir),
            "--brain-codebase",
            str(brain),
            "--skip-phase57",
            "--repos",
            f"backend:{backend_repo}",
            f"web:{web_repo}",
        ]
        subprocess.run(cmd, check=True, cwd=str(root), env=env)
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert meta.get("status") == "ok", meta
        assert isinstance(meta.get("phase_timings_ms"), dict), meta
        assert meta.get("total_elapsed_ms", 0) > 0, meta
        assert (run_dir / "_role" / "backend" / "forge_scan_source_files.txt").is_file()
        assert (run_dir / "_role" / "web" / "forge_scan_source_files.txt").is_file()
        routes = run_dir / "forge_scan_api_routes.txt"
        text = routes.read_text(encoding="utf-8", errors="replace")
        assert "/api/hello" in text, routes
        scan_doc = json.loads((brain / "SCAN.json").read_text(encoding="utf-8"))
        repos = scan_doc.get("repos")
        assert isinstance(repos, dict) and "backend" in repos and "web" in repos, scan_doc
        assert scan_doc.get("source_files", 0) >= 2
        g = json.loads((brain / "graph.json").read_text(encoding="utf-8"))
        assert g.get("forge_scan_graph_version") == 1
        assert isinstance(g.get("nodes"), list)
        assert (brain / "SCAN_SUMMARY.md").is_file()
        assert (brain / ".forge_scan_manifest.json").is_file()
        index_page = brain / "pages" / "web-index-html.md"
        main_page = brain / "pages" / "web-src-main-jsx.md"
        assert index_page.is_file(), index_page
        assert main_page.is_file(), main_page
        ix = index_page.read_text(encoding="utf-8", errors="replace")
        mx = main_page.read_text(encoding="utf-8", errors="replace")
        assert "[[pages/web-src-main-jsx]]" in ix, "index.html page should wikilink main.jsx"
        assert "[[pages/web-index-html]]" in mx, "main.jsx page should wikilink back to index.html"
        assert "[[pages/web-src-app-jsx]]" in mx, "main.jsx should wikilink App.jsx via static import"
        app_page = brain / "pages" / "web-src-app-jsx.md"
        assert app_page.is_file(), app_page
        ap = app_page.read_text(encoding="utf-8", errors="replace")
        assert "[[pages/web-src-main-jsx]]" in ap, "App.jsx should show Imported by main.jsx"
        mod_backend_src = brain / "modules" / "backend-src.md"
        assert mod_backend_src.is_file(), mod_backend_src
        msrc = mod_backend_src.read_text(encoding="utf-8", errors="replace")
        assert "## HTTP routes (auto)" in msrc, "backend src module should list API paths from route inventory"
        assert "/api/hello" in msrc, "route inventory should surface /api/hello on module note"
        # Repo-docs mirror assertions
        mirrored_api = brain / "repo-docs" / "backend" / "docs" / "api.md"
        mirrored_readme = brain / "repo-docs" / "web" / "README.md"
        assert mirrored_api.is_file(), mirrored_api
        assert mirrored_readme.is_file(), mirrored_readme
        assert "Smoke fixture" in mirrored_api.read_text(encoding="utf-8")
        assert (brain / "repo-docs" / "INDEX.md").is_file()
        idx = json.loads((brain / "repo-docs" / "index.json").read_text(encoding="utf-8"))
        assert idx.get("forge_repo_docs_mirror_version") == 2
        assert idx.get("totals", {}).get("snapshot_files", 0) >= 2
        snapshots = idx.get("files") or []
        assert any("content_sha256" in e and len(e["content_sha256"]) == 64 for e in snapshots)
        # Policy: allow_extra should be mirrored
        assert (brain / "repo-docs" / "backend" / "extras" / "special.md").is_file()
        # Policy: index_only CHANGELOG should NOT be copied but should appear in index
        assert not (brain / "repo-docs" / "backend" / "CHANGELOG.md").is_file()
        index_only = idx.get("index_only") or []
        assert any("CHANGELOG" in e.get("source_relative", "") for e in index_only)
        # Policy: deny should be absent from both snapshot and index
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
