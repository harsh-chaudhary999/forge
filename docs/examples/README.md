# Examples

- **`sample-prd.md`** — Example PRD shape for narrative demos (see repo **`README.md`**).
- **`semantic-automation.csv`** — Machine-eval CSV with **api** → **mysql** (**DependsOn** chain after an API write) and **web** rows (columns per **`docs/semantic-eval-csv.md`**). Copy into **`~/forge/brain/prds/<task-id>/qa/`** and extend for your product.

Semantic automation: **`docs/semantic-eval-csv.md`**, **`tools/run_semantic_csv_eval.py`**, **`qa/semantic-eval-manifest.json`**.

After **`/scan`**, you can inspect **`graph.json`** without loading every module note: **`python3 tools/forge_graph_query.py`** — see **`tools/README.md`**.
