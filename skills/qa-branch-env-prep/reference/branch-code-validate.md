# Step 4b — Run Test Suite (branch-code-validate mode only)

> Applies only to `run_mode: branch-code-validate`. Skip for all other run modes.

For each repo in the `branches` map, run the configured test command:

```bash
REPO=<path>
TEST_CMD=<test_command from forge-product.md or test_commands override>

echo "=== Running tests in $REPO ==="
echo "Command: $TEST_CMD"
echo "Branch: $(git -C "$REPO" rev-parse --abbrev-ref HEAD) @ $(git -C "$REPO" rev-parse --short HEAD)"

# Run the test suite and capture output + exit code — tee directly into brain
# (durable from the first write; no /tmp staging).
LOGDIR=~/forge/brain/prds/<task-id>/qa/logs; mkdir -p "$LOGDIR"
TS=$(date -u +%Y%m%dT%H%M%SZ)
cd "$REPO" && $TEST_CMD 2>&1 | tee "$LOGDIR/test-output-$(basename "$REPO")-$TS.log"
TEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "PASS: $REPO — test suite exited 0"
else
  echo "FAIL: $REPO — test suite exited $TEST_EXIT_CODE"
fi
```

**How to resolve the test command per repo:**
1. Check `test_commands` in the input config (explicit override)
2. Else read `forge-product.md` for the repo's `test_command` field in the Projects section
3. Else detect from repo structure: `package.json` → `npm test`, `pytest.ini`/`setup.py` → `pytest`, `go.mod` → `go test ./...`, `pom.xml` → `mvn test`, `build.gradle` → `./gradlew test`
4. If still unknown: STOP. Use `AskUserQuestion` — paste **`forge-product.md`** `test_command`, pick from numbered detector guesses, or free-text **one** command — **never guess** without confirmation.

**Record results per repo:**

```
Repo               Test Command     Exit Code   Tests Run   Pass   Fail   Skip
backend-api        npm test         0           142         142    0      0
web-dashboard      npm run test:unit 1          87          80     7      0
```

If any repo exits non-zero: record as FAIL. Do not stop the entire run — run all repos first, then surface all failures at the end. Raw output is already durable under `~/forge/brain/prds/<task-id>/qa/logs/` (the `tee` above wrote it there directly).

**HARD-GATE (branch-code-validate):** After running all repos:
- [ ] Test results table written to `branch-env-manifest.md`
- [ ] Raw test output logs present under `brain/prds/<task-id>/qa/logs/`
- [ ] Overall result recorded: PASS (all repos 0) or FAIL (any repo non-zero) + which repos failed
- [ ] `[QA-CODE-VALIDATE]` gate line logged to `qa-pipeline.log`:

```bash
echo "[QA-CODE-VALIDATE] task_id=<task-id> repos=<n> pass=<n> fail=<n> status=<PASS|FAIL>" \
  >> ~/forge/brain/prds/<task-id>/qa-pipeline.log
```

After this step, proceed directly to Step 7 (manifest) and Step 8 (log gate). Skip Steps 5–6.
