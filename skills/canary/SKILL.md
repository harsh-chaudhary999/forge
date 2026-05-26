---
name: canary
description: "WHEN: A deploy has just completed and you need to monitor the live app for anomalies — console errors, screenshot regressions, unexpected responses. Run post-deploy, before marking deploy complete."
type: flexible
version: 1.0.0
preamble-tier: 3
triggers:
  - "post-deploy check"
  - "monitor deploy"
  - "canary check"
  - "watch for regressions after deploy"
allowed-tools:
  - Bash
---

# canary

Post-deploy monitoring. Captures a baseline snapshot before deploy, then monitors for anomalies after. Alerts on console errors, HTTP degradation, or screenshot drift. Read-only to codebase.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "Eval passed so the deploy is fine" | Eval ran against a local stack. Canary runs against the live URL after real deployment. Different environment, different failures. |
| "I'll check manually in the browser" | Manual checks leave no record, miss timing-based issues, and don't persist baselines for comparison. |
| "One check is enough" | A single anomaly might be a transient hiccup. 2-check persistence before firing prevents false alerts. |

**Baseline before. Monitor after. Alert on persistence.**

## Invocation Modes

- `/canary baseline <url>` — capture baseline snapshot before deploy
- `/canary watch <url>` — monitor after deploy (runs 3 checks, 60s apart)
- `/canary status` — show last canary results from brain

## Workflow

### For `/canary status`

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
CANARY_DIR="$TASK_DIR/canary"

if [ -d "$CANARY_DIR" ] && [ "$(ls -A "$CANARY_DIR" 2>/dev/null)" ]; then
  ls -1t "$CANARY_DIR"/*.md | head -5 | while read f; do
    echo "$(basename "$f")"
    grep "^verdict:" "$f" | head -1
  done
else
  echo "No canary results found. Run /canary baseline <url> before deploy."
fi
```

### For `/canary baseline <url>`

**Step 1 — Capture baseline:**

```bash
BASE_URL="<user-provided URL>"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")

# Check HTTP status and response time
RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" -o /tmp/canary_body.txt "$BASE_URL" --max-time 15 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
RESPONSE_TIME=$(echo "$RESPONSE" | tail -1)

echo "Baseline HTTP: $HTTP_CODE | Response time: ${RESPONSE_TIME}s"
```

**Step 2 — Write baseline to brain:**

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
CANARY_DIR="$TASK_DIR/canary"
mkdir -p "$CANARY_DIR"

cat > "$CANARY_DIR/${TIMESTAMP}-baseline.md" << EOF
---
# output-file type for canary artifacts (not SKILL frontmatter type)
type: baseline
url: $BASE_URL
timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
http_code: $HTTP_CODE
response_time_s: $RESPONSE_TIME
---

# Canary Baseline

URL: $BASE_URL
HTTP: $HTTP_CODE
Response time: ${RESPONSE_TIME}s
EOF
echo "Baseline saved to: $CANARY_DIR/${TIMESTAMP}-baseline.md"
```

### For `/canary watch <url>`

**Step 1 — Load baseline:**

```bash
BASE_URL="<user-provided URL>"
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
CANARY_DIR="$TASK_DIR/canary"
BASELINE=$(ls -1t "$CANARY_DIR"/*-baseline.md 2>/dev/null | head -1)

if [ -z "$BASELINE" ]; then
  echo "ERROR: No baseline found. Run /canary baseline <url> before deploy."
  exit 1
fi

BASELINE_HTTP=$(grep "^http_code:" "$BASELINE" | awk '{print $2}')
BASELINE_TIME=$(grep "^response_time_s:" "$BASELINE" | awk '{print $2}')
echo "Baseline: HTTP $BASELINE_HTTP, ${BASELINE_TIME}s"
```

**Step 2 — Run 3 checks, 60s apart:**

For each of 3 checks:
```bash
CHECK_NUM=1  # increment each iteration
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL" --max-time 15 2>/dev/null)
TIME=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL" --max-time 15 2>/dev/null)
echo "Check $CHECK_NUM: HTTP $HTTP | ${TIME}s"
# Compare: flag if HTTP != baseline HTTP or time > baseline_time * 2
```

Wait 60 seconds between checks (output a countdown notice to the user).

**Step 3 — Evaluate and alert:**

- If 2 of 3 checks show anomaly (HTTP degradation or response time >2× baseline): `ALERT — anomaly persisted across 2+ checks`
- If 1 of 3: `WARNING — single anomaly, likely transient`
- If 0 of 3: `STABLE — no anomalies detected`

**Step 4 — Write results to brain:**

```bash
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
cat > "$CANARY_DIR/${TIMESTAMP}-watch.md" << EOF
---
# output-file type for canary artifacts (not SKILL frontmatter type)
type: watch
url: $BASE_URL
timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
verdict: <STABLE|WARNING|ALERT>
checks: 3
anomalies: <N>
---

# Canary Watch Results

<per-check table with HTTP code and response time>

Verdict: <STABLE|WARNING|ALERT>
EOF
```

### ALERT Escalation Procedure

When verdict is `ALERT`:

1. **Log to brain immediately:**
   ```bash
   cat >> ~/forge/brain/prds/<task-id>/conductor.log <<EOF
   $(date -u +%Y-%m-%dT%H:%M:%SZ) [CANARY-ALERT] task_id=<id> metric=<metric> baseline=<value> current=<value> delta=<pct>%
   EOF
   ```
2. **Write a blocker:** Create `~/forge/brain/prds/<task-id>/blockers/<timestamp>-canary-alert.md` with:
   - The anomalous metric and its delta from baseline
   - The time window observed
   - Whether this is a new deploy or an existing deployment
3. **Invoke rollback (if alert follows a recent deploy):**
   - Run the relevant deploy driver (e.g., `/deploy-driver-pm2-ssh`, `/deploy-driver-docker-compose`) with action=rollback.
   - Re-run canary watch after rollback to confirm return to STABLE.
4. **If alert is on an existing deployment (no recent deploy):** Escalate to human — output `BLOCKED — CANARY-ALERT: <metric> anomaly on stable deployment. Human investigation required.`
5. **HARD-GATE:** Do not proceed with any further deployment or eval while verdict is ALERT.

## Cross-References

- `deploy-driver-pm2-ssh`: Rollback via PM2 SSH when canary fires after a PM2-managed deploy.
- `deploy-driver-local-process`: Rollback via local process restart when canary fires on a local deploy.
- `deploy-driver-docker-compose`: Rollback via Docker Compose when canary fires after a Docker deploy.
- `deploy-driver-systemd`: Rollback via systemd when canary fires after a systemd-managed service deploy.
- `forge-eval-gate`: Eval gate that MUST pass GREEN before any deploy; canary fires if post-deploy metrics degrade.
- `docs/conductor-log-format.md`: `[CANARY-ALERT]`, `[DEPLOY-HEALTH-FAIL]`, and `[ROLLBACK-VERIFY]` marker formats logged by this skill.
