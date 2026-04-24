# Eval scenario examples

Copy or adapt these YAML files into your task brain under `brain/prds/<task-id>/eval/` (for example `smoke.yaml`). They satisfy the **minimum smoke** pattern described in **`skills/eval-scenario-format/SKILL.md`**.

- **`eval-api-http-smoke.yaml`** — one `GET` against a health URL; adjust host, path, and port to your stack.
- **`eval-web-cdp-smoke.yaml`** — one browser navigation; adjust URL and optional title assertion.

After copying, run **`eval-product-stack-up`** then **`eval-coordinate-multi-surface`** (or your host’s **`/eval`**) per **`skills/forge-eval-gate/SKILL.md`**.

After **`/scan`**, you can inspect **`graph.json`** without loading every module note: **`python3 tools/forge_graph_query.py`** — see **`tools/README.md`**.
