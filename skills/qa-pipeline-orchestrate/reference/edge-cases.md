# qa-pipeline-orchestrate — Edge Cases

### RED verdict and immediate re-run
After a RED, if the user fixes the bug and invokes `/qa-run` again: start from QA-P3 (branch prep) not QA-P1, unless the user changed which branch to test. Use `--from=QA-P3` shorthand in the command (`--from=QA-Pn` accepts QA-P1..QA-P7).

### Partial surface run (`--surface web`)
All non-web scenarios get status `SKIPPED (surface filter)` in the report. Verdict only covers the requested surfaces. Report must note: "Verdict is partial — `api`, `db` surfaces not run. Re-run without `--surface` filter for full verdict."

### Remote mode (testing staging)
Skip QA-P4. In the report, note the remote BASE_URL as the test target. Record that the branch state is informational (the remote may be running a different commit than local HEAD).

### Static validation only (no stack, no drivers — common in agent sessions)

When the session validates **`qa/semantic-automation.csv`** and/or writes **`semantic-eval-manifest.json`** but **does not** start a stack or invoke drivers (no **`BASE_URL`**, no device, no credentials, or policy forbids long-running services):

- Label the outcome **`pipeline_verdict: NOT_EXECUTED`** and **`execution_scope: static_only`** — **not** **YELLOW**.
- **YELLOW** remains reserved for **`eval-judge`** when drivers ran and non-critical steps failed.
- The human summary should read like **“automation not run — environment gap”**, not **“partial pass.”**

### Self-heal exhausts the loop cap on a QA RED
After **N (3)** RED → fix → re-run cycles without GREEN (per **`self-heal-loop-cap`**), **stop looping**: log **BLOCKED**, surface the cap to the user via **`AskUserQuestion`** (keep investigating / accept-and-defer / abort), and do not silently re-run a fourth time.

### No tech plans in brain
Semantic CSV authoring needs targets from tech plans + contracts. The pipeline logs `[QA-P2-SCENARIOS] status=BLOCKED reason=no-tech-plans`. Ask user: "Tech plans are absent. Would you like to (1) run `/plan` first, (2) provide a brief description for minimal **`qa/semantic-automation.csv`** rows from the PRD only, or (3) supply **`qa/semantic-automation.csv`** + **`semantic-eval-manifest.json`** manually?"
