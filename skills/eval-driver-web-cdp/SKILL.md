---
name: eval-driver-web-cdp
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires web UI interaction or assertion. Chrome DevTools Protocol: launch(), navigate(), interact(click/type/scroll), screenshot(), getDOM(), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.5
preamble-tier: 3
triggers:
  - "eval web UI"
  - "run browser eval"
  - "CDP eval driver"
  - "web UI eval"
allowed-tools:
  - Bash
  - AskUserQuestion
  - mcp__*
---

# Eval Driver: Web UI via Chrome DevTools Protocol (CDP)

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: web`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

Automates browser interactions and state inspection using Chrome DevTools Protocol. Provides a programmatic interface for launching headless Chrome, navigating URLs, interacting with UI elements, capturing screenshots, and extracting DOM state.

## Human input

Blocking human decisions (browser/profile choice, CDP-vs-Playwright-vs-MCP driver pick)
use **`AskUserQuestion`** — see **[`skills/_shared/human-input.md`](../_shared/human-input.md)**
for the canonical convention. The web-driver implementation choice is the **CLAUDE.md** D5 decision.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "If the page loads, the eval passes" | A page can load with empty data, error state, or partial render. Load event fires before content is populated. Every scenario must assert on specific content. |
| "CSS selectors are fine for targeting elements" | CSS selectors break on visual refactors that don't change behavior. Use `data-testid`, ARIA roles, or labels. Test IDs are contracts; class names are not. |
| "teardown() can be skipped if the test fails" | An unclosed Chrome process holds the debug port. The next scenario cannot connect. teardown() must run in all paths — success, failure, and timeout. |
| "Screenshots are optional evidence" | If an assertion fails and there is no screenshot, debugging the failure requires re-running the scenario. Capture evidence every time. |
| "Timing issues are flakiness, not bugs" | Timing issues are bugs in the eval script. Use explicit wait conditions (networkIdle, element visible) — not fixed sleeps — so failures are deterministic. |

## Iron Law

```
EVERY CDP SCENARIO FOLLOWS: launch() → navigate() → wait-for-load → interact → assert-specific-content → screenshot → teardown(). teardown() IS CALLED IN ALL PATHS. NO ASSERTION IS NON-SPECIFIC. NO INTERACTION HAPPENS BEFORE LOAD STATE IS CONFIRMED.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **`navigate()` is called without waiting for `networkIdle` or `DOMContentLoaded`** — Interacting with a page that has not finished loading produces false "element not found" failures. STOP. Always verify load state after `navigate()` before any interaction.
- **Element interaction uses `document.querySelector` instead of accessibility identifiers or test IDs** — CSS selectors break on UI refactors that don't change behavior. STOP. Elements must be targeted by `data-testid`, accessibility role, or stable aria-label.
- **`teardown()` is not called after the scenario completes** — An unclosed Chrome process holds a debug port that prevents the next scenario from launching. STOP. `teardown()` must be called in all paths — success, failure, and timeout.
- **Screenshot is captured but not linked in the eval evidence** — Screenshots are meaningless if the eval report doesn't reference them. STOP. Every `screenshot()` call must produce a file path entry in the scenario output.
- **Assertion is based on `getDOM()` returning non-empty rather than specific content** — A non-empty DOM matches any rendered page, including error pages. STOP. Every assertion must verify specific text, element state, or attribute value — not merely presence.
- **Browser viewport size is not set before scenarios with responsive layout** — Default headless viewport may not match the breakpoint the UI targets, causing elements to be hidden or rearranged. STOP. Set explicit viewport dimensions at `launch()` time to match the spec's target device class.
- **`launch()` / CDP connection attempted with no browser process and no `--remote-debugging-port` listener** — STOP. Complete **Preflight** below first; **BLOCK** with **`qa/logs/eval-preflight-*.log`** attachment.

## Preflight — browser discovery, CDP readiness, logging

**Before** `launch()` or any CDP WebSocket connect:

1. **`mkdir -p ~/forge/brain/prds/<task-id>/qa/logs`** (see **`skills/forge-brain-layout/SKILL.md`** **qa/logs/**).
2. **Discover binaries** — run **`which`** / common paths: **`google-chrome-stable`**, **`google-chrome`**, **`chromium`**, **`chromium-browser`**, **`microsoft-edge`** (distro-dependent); on macOS, **`/Applications/Google Chrome.app/...`**. Append **`--- web ---`** section + command output to **`eval-preflight-<ISO8601>.log`**.
3. **`AskUserQuestion`** / **`AskUserQuestion`**: which browser binary + profile (headless vs headed) + **`--remote-debugging-port=<port>`** (must match driver config). **Do not** assume Chrome if only Chromium exists.
4. **Raw CDP path:** start the chosen browser with **`--remote-debugging-port=...`** (and **`--user-data-dir`** if isolated profile needed); **verify** port listens (**`ss`**, **`lsof`**, or HTTP to **`/json/version`**) before scenarios — log failures.
5. **Playwright / Playwright MCP path:** If the human picks **Playwright** or **[microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)** — ensure **Node** is present (`node -v`, `npm -v`). Install MCP per upstream docs; run **`npx playwright install`** (or project-local install) for browsers. On **missing Node**, tell the user to install **Node LTS**, then retry — log stderr to **`qa/logs/`**.
6. **Browser MCP path:** If IDE exposes browser MCP tools, record tool names and timeouts in the task brain — same log file may reference MCP probe results.

## Host implementation choice (CDP, Playwright, Puppeteer, MCP)

**MUST** elicit with a **blocking interactive prompt** per **`using-forge`** how web UI eval should run **before** treating any stack as decided — **`AskUserQuestion`** / **numbered 1–3** + **stop**, not prose-only *which stack?*:

1. **Raw CDP** — WebSocket client / `chrome-remote-interface` / minimal driver (matches the API shape in this skill). Requires a running browser with **`--remote-debugging-port`** (**Preflight** above).
2. **Playwright or Puppeteer** — running on the **operator’s machine or CI** against the **product** browser (allowed for **product eval**; D5 still forbids **LangChain-style** orchestration **inside Forge’s shipped plugin code**). Optional IDE integration: **[microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)** — install per upstream; **`npx playwright install`** for bundled browsers.
3. **Browser MCP** — IDE or host exposes MCP tools (navigate, snapshot, click). When available, the operator may prefer MCP over a custom CDP script. **Confirm** tool names, auth, timeouts, and what artifacts **`eval-judge`** needs.

If **both** MCP and a local CDP path exist, **do not assume** — same **blocking interactive** fork (**MCP** vs **local CDP**) and record the choice (e.g. in `brain/prds/<task-id>/` notes) so runs are reproducible.

## Overview

This skill enables eval scripts to drive web UI automation through CDP, supporting:
- Headless Chrome browser lifecycle management
- URL navigation with load state verification
- User interaction simulation (click, type, scroll)
- Page screenshots for visual validation
- DOM state extraction for assertion verification
- Graceful browser teardown

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/cdp-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

## Checklist

Before running a CDP eval scenario:

- [ ] `launch()` called with explicit viewport dimensions matching target device class
- [ ] `navigate()` followed by explicit wait for load state (networkIdle or DOMContentLoaded)
- [ ] All element targeting uses `data-testid`, ARIA role, or stable aria-label (not CSS class selectors)
- [ ] Every assertion verifies specific text, attribute, or element state — not just presence
- [ ] `screenshot()` called and file path recorded in scenario output
- [ ] `teardown()` called in all paths (success, failure, timeout)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] CDP connection to the correct origin verified before first step; no screenshot-only assertions.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

| Skill / Doc | Relationship |
|---|---|
| `qa-semantic-csv-orchestrate` | **Dispatcher** — invokes this driver for steps with `Surface: web` or `web-cdp` |
| `eval-judge` | **Downstream** — reads `semantic-eval-run.log` entries this driver writes |
| `forge-eval-gate` | **Gate** — this driver is one of multiple drivers coordinated by the gate |
| `docs/semantic-eval-csv.md` | Surface → driver mapping; `DependsOn` syntax |
| `docs/semantic-eval-schema.md` | `semantic-eval-run.log` outcome enum and required fields |
