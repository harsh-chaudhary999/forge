---
name: eval-driver-ios-xctest
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches driver=ios-xctest. iOS via XCTest + xcrun simctl: connect(simulator_id), launch(bundle_id), tap(target), type(text), swipe(direction, element), assert_element(target), screenshot(), disconnect()."
type: rigid
requires: [brain-read]
version: 1.0.3
preamble-tier: 3
triggers:
  - "eval on iOS"
  - "XCTest eval"
  - "run iOS eval"
allowed-tools:
  - Bash
  - AskUserQuestion
  - mcp__*
---

# eval-driver-ios-xctest Skill

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: ios`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

**Phase 3.4: Eval Driver for iOS via XCTest + xcrun simctl**

This skill provides a complete iOS app automation driver using XCTest UI Testing framework and `xcrun simctl` for simulator control. It enables programmatic interaction with iOS simulators and devices for eval scenarios.

## Human input (all hosts)

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Map to the host’s **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor **`AskQuestion`**; hosts without the tool: **numbered options + stop**). See **`using-forge`** **Interactive human input** (e.g. Appium MCP vs XCTest per **CLAUDE.md** D5).

## Optional: Appium MCP vs XCTest (host choice)

**Ask the human** whether iOS UI eval should use **`xcrun simctl` + XCTest** (this skill) or an **Appium MCP** / host Appium stack when both are plausible (Appium can drive simulators and devices with different bootstrap tradeoffs). Record the decision and bootstrap commands in the task brain so local runs and CI do not diverge silently.

## Anti-Pattern Preamble: Why iOS Eval Drivers Silently Fail

**DO NOT proceed with these rationalizations:**

1. **"Simulator is enough, skip real device"** — Incorrect. Simulators lack real network conditions, push notifications, biometrics, and camera. Device testing is required for production confidence.

2. **"XCTest is only for unit tests"** — Incorrect. XCTest UI Testing provides full UIInterruptionMonitor, element queries, gesture simulation, and accessibility identifier targeting.

3. **"iOS is too complex, skip mobile eval"** — Incorrect. iOS eval follows the same pattern as Android: connect → launch → interact → assert → screenshot → disconnect.

4. **"We tested Android, iOS is the same"** — Incorrect. iOS has distinct permission dialogs (system alerts via UIInterruptionMonitor), different lifecycle (foreground/background/suspended), and different element locators (accessibility identifiers vs resource IDs).

## Iron Law

```
EVERY iOS EVAL SCENARIO FOLLOWS: connect() → verify booted → launch(bundle_id) → interact → assert_element → screenshot → disconnect(). NO SCENARIO SKIPS teardown. NO ASSERTION IS NON-SPECIFIC. UIInterruptionMonitor IS REGISTERED BEFORE ANY SYSTEM-ALERT-TRIGGERING ACTION.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Simulator booted state is not verified before launch** — `xcrun simctl launch` on a non-booted simulator silently fails or spawns a zombie process. STOP. Always confirm `Booted` status via `xcrun simctl list devices` before calling `launch()`.
- **Assertions use `XCTAssertTrue(app.otherElements.count > 0)` or other non-specific checks** — Non-specific assertions mean any element satisfies the condition; the test cannot fail on wrong content. STOP. Every assertion must target a named accessibility identifier or exact element predicate.
- **UIInterruptionMonitor is not registered before actions that trigger system alerts** — iOS permission dialogs (camera, notifications, location) interrupt UI flows without an active monitor. STOP. Register a UIInterruptionMonitor before any action that could trigger a system alert.
- **`disconnect()` is not called after scenario completes** — An unclosed simulator connection leaves dangling process references and prevents the next scenario from cleanly booting the same simulator. STOP. Always call `disconnect()` in a teardown block, even if the scenario fails.
- **App state from prior scenario is not cleared before new scenario** — Leftover keychain entries, cached tokens, or persisted user defaults contaminate subsequent test runs. STOP. Reset app state with `app.terminate()` + `xcrun simctl privacy reset` before each scenario.
- **`screenshot()` is called but the image is not attached to the eval report** — Screenshots without links to evidence are invisible to the eval judge. STOP. Every `screenshot()` call must save the file and record the path in the scenario output.

## Host and simulator resolution (before `connect()`)

Mirror the Android driver: **detect → pin from config → else ask (interactive) or FAIL (CI)**.

### 0. Host OS gate (HARD-GATE — run first)

**XCTest and `xcrun simctl` require macOS.** They **cannot** run on Linux, Windows, or generic CI workers without a **Mac** toolchain.

1. Run **`uname -s`** (or host-equivalent). If the result is **not** **`Darwin`**, **STOP** immediately — **do not** invoke **`xcrun`**, **`simctl`**, or **`xcodebuild`** on this host.
2. **`mkdir -p ~/forge/brain/prds/<task-id>/qa/logs`** and append one line to **`eval-preflight-<ISO8601>.log`**: e.g. **`--- ios ---`**, **`uname`**, **`BLOCKED: XCTest requires macOS + Xcode`** (see **`skills/forge-brain-layout/SKILL.md`** **qa/logs/**).
3. Tell the user plainly: **this machine is not macOS** — run iOS eval on a **Mac** or a **CI runner with macOS + Xcode**, or mark **`driver: ios-xctest`** scenarios **N/A** with reason **`host_os_not_darwin`** in the eval report / **`qa-pipeline-orchestrate`** log.

### 1. Preconditions (fail fast with a clear message)

- **`xcrun` / Xcode** — If `xcrun simctl list devices` fails, tell the user to install **Xcode** (simulators need full **Xcode.app**, not Command Line Tools alone). **License:** accepting the Xcode license is **one-time host prep** (open **Xcode** once, or run **`xcodebuild -license`** as an **interactive** admin session on that Mac). **Do not** run **`sudo`** (or any password-prompting step) inside the eval driver / CI job — it **hangs or fails** unattended. If the failure is “license not accepted”, return **BLOCKED** with that diagnosis and point the operator at host prep, not at embedding sudo in the scenario.
- **`DEVELOPER_DIR`** — If multiple Xcode.app copies exist and the wrong one is selected, document **`export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`**.

### 2. Discover what exists

Run **`xcrun simctl list devices available`** (and/or `booted`) and parse **Booted** / **Shutdown** simulators with **name**, **UDID**, and **runtime** (iOS version).

Physical devices are a separate flow (developer disk image, pairing); if eval targets device UDID, verify it appears under **`xcrun xctrace list devices`** or `devicectl` per host OS — if unsupported here, **FAIL** with “device path not implemented in this driver” rather than guessing.

### 3. Choose `simulator_id` (priority order)

1. **Eval scenario / driver config** — If YAML names **`simulator_id`**, **`SIMULATOR_UDID`**, or **iOS runtime + device name** (team convention), resolve to a UDID from the list.
2. **`product.md`** — If **`services.<app>.simulator_id`** (or Forge seed convention **`default`**) matches a listed UDID or name, use it.
3. **Environment** — If **`SIMULATOR_UDID`** (or team **`IOS_SIMULATOR_UDID`**) is set and valid, use it.
4. **Single booted simulator** — If exactly **one** is **Booted**, **`default`** may target it.
5. **Multiple matches, no pin** — **Interactive:** list **name — iOS version — UDID** and **ask once** which to boot/use unless the user already specified in this task. **CI:** **FAIL** with instructions to set **`SIMULATOR_UDID`** or scenario UDID, or boot exactly one simulator before eval.

### 4. “Boot iOS x” / runtime request (explicit user or scenario only)

- **`xcrun simctl boot <UDID>`** when **Shutdown**; wait with **`xcrun simctl bootstatus <UDID> -b`** before **`launch()`** (aligns with Red Flags above).
- If the user asks for a **runtime that is not installed** (e.g. iOS 18.2 simulator not present), **FAIL** with: run **`xcodebuild -downloadPlatform iOS`** / Xcode **Settings → Platforms**, or pick an installed runtime — do not fabricate UDIDs.

### 5. Unbiased expectation

Simulator **discovery and boot** is reliable on macOS CI when images are preinstalled; **downloading** new runtimes inside eval is usually **too slow and flaky** for a gate. Prefer **fail with install instructions** over silent hangs.

## Prerequisites

- Xcode installed (provides `xcrun`, `simctl`, `xcodebuild`)
- iOS Simulator or connected device (developer mode enabled)
- App built with `-destination` flag or `.app` bundle available
- `idb` (optional, for enhanced device support): `pip install fb-idb`

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/xctest-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

## Decision Tree: Test Device Selection

Choose the right device/simulator configuration for your eval based on coverage and speed requirements.

```
WHAT IS YOUR PRIMARY EVAL GOAL?
│
├─ SPEED & ITERATION (during development) → Use iPhone 15 Simulator
│  │
│  ├─ Fastest to boot (< 5 seconds)
│  ├─ Lowest memory overhead (~500MB)
│  ├─ Sufficient for UI/UX evals
│  └─ Tip: Re-use same simulator across runs to avoid boot penalty
│
├─ COMPATIBILITY (test on multiple iOS versions) → Use REPEATABLE DEVICE MATRIX
│  │
│  ├─ iPhone 15 Pro (latest hardware, iOS 17)
│  ├─ iPhone 12 (mid-cycle, iOS 16)
│  ├─ iPhone SE (low-end hardware, iOS 15)
│  └─ Run same eval on all 3 to catch version/hardware-specific bugs
│
├─ REAL DEVICE VALIDATION (production confidence) → Use CONNECTED PHYSICAL DEVICE
│  │
│  ├─ Network: Real Wi-Fi/LTE, not simulated
│  ├─ Hardware: Real GPU, real touch response, real memory constraints
│  ├─ Biometrics: Real Face ID / Touch ID (not simulated)
│  ├─ Permissions: Real permission dialogs, not test overrides
│  │
│  └─ Note: Slower (~30-60s to reconnect), requires physical device
│
└─ UNCERTAIN → Default: iPhone 15 Simulator
   └─ Balanced: Good speed, modern iOS, wide compatibility
```

**Implementation**:
```javascript
// Option 1: Simulator (fast, for iteration)
const sim = await connect({ simulator_id: "default" })

// Option 2: Specific simulator version (for compatibility)
const sim12 = await connect({ simulator_id: "iPhone-12-iOS-16" })
const sim15 = await connect({ simulator_id: "iPhone-15-iOS-17" })

// Option 3: Physical device (for production realism)
const device = await connect({ simulator_id: "00008120-001E5D001234567A" })  // Device UDID
```

---

## Checklist

Before running an iOS XCTest eval scenario:

- [ ] Simulator `Booted` status verified via `xcrun simctl list devices` before `launch()`
- [ ] App state cleared from prior scenario (`app.terminate()` + `xcrun simctl privacy reset`)
- [ ] `UIInterruptionMonitor` registered before any action that triggers system alerts
- [ ] All assertions target named accessibility identifiers or exact element predicates
- [ ] `screenshot()` called and file path recorded in scenario output
- [ ] `disconnect()` called in all paths (success, failure, timeout)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] XCTest scheme compiled without warnings; device UDID confirmed connected before test run.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

- `qa-semantic-csv-orchestrate`: Generates `qa/semantic-automation.csv` with `ios` surface steps that this driver executes.
- `eval-judge`: Aggregates iOS step outcomes from `semantic-eval-run.log` into a final PASS/FAIL/YELLOW verdict.
- `forge-eval-gate`: Consumes `semantic-eval-manifest.json` written by this driver to gate PR merge.
- `qa-live-app`: Higher-level skill that orchestrates this driver as part of live app testing.
- `docs/semantic-eval-csv.md`: CSV column definitions and `ios` surface alias (`ios-xctest`) used by this driver.
- `docs/semantic-eval-schema.md`: JSON schema for `semantic-eval-manifest.json` and step outcome enum (PASS/FAIL/BLOCKED_DEPENDENCY/CONTEXT_GAP/SKIPPED).
