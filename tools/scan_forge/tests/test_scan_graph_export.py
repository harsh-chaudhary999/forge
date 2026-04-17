"""Tests for ``scan_graph_export`` (no network)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scan_forge.scan_graph_export import write_graph_json


class TestScanGraphExport(unittest.TestCase):
    def test_writes_graph_with_edge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            brain = Path(td)
            (brain / "modules").mkdir(parents=True)
            (brain / "modules" / "web-src.md").write_text("# web-src\n", encoding="utf-8")
            (brain / "modules" / "backend-root.md").write_text("# backend-root\n", encoding="utf-8")
            (brain / "SCAN.json").write_text(
                json.dumps({"scanned_at": "2026-01-01T00:00:00Z", "repos": {}}),
                encoding="utf-8",
            )
            (brain / "cross-repo-automap.md").write_text(
                "# automap\n\n```tsv\n"
                "web\tsrc/client.ts\tbackend\topenapi.json\t/api/hello\tOPENAPI\n"
                "```\n",
                encoding="utf-8",
            )
            out = write_graph_json(brain)
            assert out is not None
            doc = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(doc.get("forge_scan_graph_version"), 1)
            self.assertTrue(any(n["id"] == "web-src" for n in doc["nodes"]))
            self.assertEqual(len(doc["edges"]), 1)
            self.assertEqual(doc["edges"][0]["provenance"], "OPENAPI")
            self.assertEqual(doc["edges"][0]["source"], "web-src")
            self.assertEqual(doc["edges"][0]["target"], "backend-root")


if __name__ == "__main__":
    unittest.main()
