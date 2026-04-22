---
name: benchmark
description: "WHEN: You need to detect performance regressions before merge — TTFB, response time, bundle size. Run as part of forge-eval-gate or standalone before raising a PR."
type: flexible
version: 1.0.0
preamble-tier: 3
triggers:
  - "performance check"
  - "benchmark"
  - "check for regressions"
  - "perf baseline"
allowed-tools:
  - Bash
  - Write
---

# benchmark

Performance regression detection. Baselines key metrics, flags regressions against threshold. Persists history to brain.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The code looks fast, no need to benchmark" | Code metrics don't equal runtime behavior. Network latency, GC pauses, and bundle size only appear at runtime. |
| "Tests pass so performance is fine" | Tests verify correctness, not speed. A 10× slowdown can pass all tests. |
| "I'll check performance after merging" | Post-merge performance regressions are incidents, not findings. Benchmark before merge. |

**Measure. Baseline. Flag regressions. Block if over threshold.**

## Invocation Modes

- `/benchmark baseline <url>` — capture performance baseline
- `/benchmark check <url>` — measure current and compare to baseline
- `/benchmark history` — show trend from brain

## Thresholds (flag as regression if exceeded)

| Metric | Regression threshold |
|--------|---------------------|
| TTFB (time to first byte) | >50% increase OR >500ms absolute |
| Total response time | >50% increase OR >2000ms absolute |
| Response size | >25% increase |

## Workflow

### For `/benchmark history`

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
BENCH_DIR="$TASK_DIR/benchmarks"

if [ -d "$BENCH_DIR" ] && [ "$(ls -A "$BENCH_DIR" 2>/dev/null)" ]; then
  echo "Benchmark history (newest first):"
  ls -1t "$BENCH_DIR"/*.md 2>/dev/null | head -10 | while read f; do
    echo "$(basename "$f") — $(grep "^verdict:" "$f" | awk '{print $2}')"
  done
else
  echo "No benchmark history. Run /benchmark baseline <url> first."
fi
```

### For `/benchmark baseline <url>`

**Step 1 — Measure baseline metrics:**

```bash
BASE_URL="<user-provided URL>"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")

# Measure TTFB, total time, and response size
METRICS=$(curl -s -o /tmp/bench_body.txt -w "%{time_starttransfer}|%{time_total}|%{size_download}" "$BASE_URL" --max-time 30 2>/dev/null)
TTFB=$(echo "$METRICS" | cut -d'|' -f1)
TOTAL=$(echo "$METRICS" | cut -d'|' -f2)
SIZE=$(echo "$METRICS" | cut -d'|' -f3)

echo "TTFB: ${TTFB}s | Total: ${TOTAL}s | Size: ${SIZE} bytes"
```

**Step 2 — Write baseline:**

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
BENCH_DIR="$TASK_DIR/benchmarks"
mkdir -p "$BENCH_DIR"

cat > "$BENCH_DIR/${TIMESTAMP}-baseline.md" << EOF
---
type: baseline
url: $BASE_URL
timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
ttfb_s: $TTFB
total_s: $TOTAL
size_bytes: $SIZE
---
# Benchmark Baseline
URL: $BASE_URL
TTFB: ${TTFB}s | Total: ${TOTAL}s | Size: ${SIZE} bytes
EOF
echo "Baseline saved: $BENCH_DIR/${TIMESTAMP}-baseline.md"
```

### For `/benchmark check <url>`

**Step 1 — Load baseline and measure current:**

```bash
BASE_URL="<user-provided URL>"
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
BENCH_DIR="$TASK_DIR/benchmarks"
BASELINE=$(ls -1t "$BENCH_DIR"/*-baseline.md 2>/dev/null | head -1)

if [ -z "$BASELINE" ]; then
  echo "ERROR: No baseline found. Run /benchmark baseline <url> first."
  exit 1
fi

BASE_TTFB=$(grep "^ttfb_s:" "$BASELINE" | awk '{print $2}')
BASE_TOTAL=$(grep "^total_s:" "$BASELINE" | awk '{print $2}')
BASE_SIZE=$(grep "^size_bytes:" "$BASELINE" | awk '{print $2}')

METRICS=$(curl -s -o /tmp/bench_body.txt -w "%{time_starttransfer}|%{time_total}|%{size_download}" "$BASE_URL" --max-time 30 2>/dev/null)
CUR_TTFB=$(echo "$METRICS" | cut -d'|' -f1)
CUR_TOTAL=$(echo "$METRICS" | cut -d'|' -f2)
CUR_SIZE=$(echo "$METRICS" | cut -d'|' -f3)

echo "Current:  TTFB=${CUR_TTFB}s | Total=${CUR_TOTAL}s | Size=${CUR_SIZE}b"
echo "Baseline: TTFB=${BASE_TTFB}s | Total=${BASE_TOTAL}s | Size=${BASE_SIZE}b"
```

**Step 2 — Compare against thresholds:**

Using Python for float comparison:
```bash
python3 -c "
ttfb_base, ttfb_cur = float('$BASE_TTFB'), float('$CUR_TTFB')
total_base, total_cur = float('$BASE_TOTAL'), float('$CUR_TOTAL')
size_base, size_cur = float('$BASE_SIZE'), float('$CUR_SIZE')
regressions = []
if ttfb_cur > ttfb_base * 1.5 or ttfb_cur > 0.5:
    regressions.append(f'TTFB: {ttfb_base:.3f}s → {ttfb_cur:.3f}s (threshold: 50% or 0.5s)')
if total_cur > total_base * 1.5 or total_cur > 2.0:
    regressions.append(f'Total time: {total_base:.3f}s → {total_cur:.3f}s')
if size_base > 0 and size_cur > size_base * 1.25:
    regressions.append(f'Size: {size_base:.0f}b → {size_cur:.0f}b (+25%)')
if regressions:
    print('REGRESSION DETECTED')
    for r in regressions: print(f'  ✗ {r}')
else:
    print('NO REGRESSION — within thresholds')
"
```

**Step 3 — Write results and output verdict:**

```bash
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
# Write result file to $BENCH_DIR/${TIMESTAMP}-check.md with verdict (PASS/REGRESSION)
# Output summary table comparing current vs baseline for each metric
```
