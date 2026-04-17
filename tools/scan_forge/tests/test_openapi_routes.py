"""Unit tests for OpenAPI path matching (no network)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scan_forge.openapi_routes import (
    append_openapi_routes,
    discover_openapi_files,
    parse_openapi_file,
    path_template_matches,
    path_templates_in_route_line,
)


class TestPathTemplate(unittest.TestCase):
    def test_param_match(self) -> None:
        self.assertTrue(path_template_matches("/api/users/42", "/api/users/{id}"))
        self.assertFalse(path_template_matches("/api/users", "/api/users/{id}"))
        self.assertTrue(path_template_matches("/api/hello", "/api/hello"))

    def test_templates_in_line(self) -> None:
        ln = "backend\tsrc/x:1:GET /api/v1/jobs/{jobId} _forge_openapi"
        t = path_templates_in_route_line(ln)
        self.assertIn("/api/v1/jobs/{jobId}", t)


class TestParseOpenAPIJson(unittest.TestCase):
    def test_parse_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "openapi.json"
            p.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "paths": {"/x": {"get": {}}, "/y": {"post": {}}},
                    },
                ),
                encoding="utf-8",
            )
            ops = parse_openapi_file(p)
            self.assertIn(("GET", "/x"), ops)
            self.assertIn(("POST", "/y"), ops)


class TestDiscoverOpenAPI(unittest.TestCase):
    def test_finds_openapi_in_filename(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "subdir").mkdir()
            (repo / "subdir" / "my-openapi-spec.json").write_text('{"openapi":"3.0.0","paths":{}}', encoding="utf-8")
            (repo / "swagger-v2.yaml").write_text("swagger: '2.0'\npaths: {}\n", encoding="utf-8")
            found = discover_openapi_files(repo)
            names = {p.name for p in found}
            self.assertIn("my-openapi-spec.json", names)
            self.assertIn("swagger-v2.yaml", names)


class TestAppendOpenAPI(unittest.TestCase):
    def test_append_writes_line(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "openapi.json").write_text(
                '{"openapi":"3.0.0","paths":{"/api/z":{"get":{}}}}',
                encoding="utf-8",
            )
            routes = repo / "routes.txt"
            routes.write_text("", encoding="utf-8")
            n = append_openapi_routes(repo, "smoke", routes)
            self.assertEqual(n, 1)
            text = routes.read_text(encoding="utf-8")
            self.assertIn("GET /api/z", text)
            self.assertIn("_forge_openapi", text)


if __name__ == "__main__":
    unittest.main()
