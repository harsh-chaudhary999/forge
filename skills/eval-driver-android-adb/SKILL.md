---
name: eval-driver-android-adb
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires Android app interaction. ADB + UIAutomator: connect(device_id), launch(package), tap(target), type(text), swipe(direction), assert_element(target), screenshot(), disconnect()."
type: rigid
requires: [brain-read]
version: 1.1.0
preamble-tier: 3
triggers:
  - "eval on Android"
  - "ADB eval driver"
  - "run Android eval"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
  - mcp__*
---

# eval-driver-android-adb Skill

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: android`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

**Phase 3.4: Eval Driver for Android via ADB + UIAutomator**

This skill provides a complete Android mobile app automation driver using Android Debug Bridge (ADB) and UIAutomator. It enables programmatic interaction with Android devices and emulators for eval scenarios, testing, and automation.

## Human input

Blocking human decisions (device choice, boot confirmation, Appium-vs-ADB driver pick)
use **`AskUserQuestion`** — see **[`skills/_shared/human-input.md`](../_shared/human-input.md)**
for the canonical convention. Appium-MCP-vs-ADB is the **CLAUDE.md** D5 driver choice — ask before assuming.

## Overview

The eval-driver-android-adb skill enables:
- Connection to Android devices and emulators via ADB
- App lifecycle management (launch, terminate)
- Touch/tap interactions (coordinates and resource IDs)
- Text input and keyboard control
- Gesture support (swipes, long-presses)
- UI hierarchy inspection and element discovery
- Screen capture for verification
- Graceful teardown and disconnect

## Optional: Appium MCP (host choice)

When an **Appium MCP** server (or similar mobile MCP) is available on the host, the operator may prefer it over **ADB + UIAutomator** for Android eval steps. **Ask explicitly**: use this skill’s **ADB driver** end-to-end, or **delegate Android UI actions to Appium MCP** (document MCP tool names, session/device assumptions, and evidence paths). Either path is valid for **product eval**; pick **one** per task so **`qa-semantic-csv-orchestrate`** and CI stay aligned.

## Anti-Pattern Preamble: Why Android Eval Drivers Silently Fail

**DO NOT proceed with these rationalizations:**

1. **"Mobile is too different, skip it"** — Incorrect. Mobile behavior is predictable once you understand platform conventions (lifecycle, permissions, ANRs). The eval-driver-android-adb skill handles this.

2. **"Emulator is enough, no device testing"** — Incorrect. Emulators have distinct performance characteristics, permission handling, and network behavior. Device testing reveals timing bugs, actual ANRs, and permissions issues that emulators mask. Use both.

3. **"ANRs are user problems not code problems"** — Incorrect. ANRs indicate main thread blocking, which is a code problem. Blocking the main thread for >5 seconds causes ANR dialogs. This is explicitly testable and must be evaluated.

4. **"UI is separate from API eval"** — Incorrect. Mobile eval requires end-to-end validation: launch app, navigate UI, trigger API calls, verify data flow and UI state. Separating UI from API testing misses integration failures.

These blockers protect against incomplete evaluations. Challenge them during eval planning.

## Iron Law

```
EVERY ANDROID EVAL SCENARIO FOLLOWS: connect() → verify device ready → launch(package) → interact → assert_element → screenshot → disconnect(). disconnect() IS CALLED IN ALL PATHS. NO ASSERTION IS NON-SPECIFIC. APP STATE IS CLEARED BETWEEN SCENARIOS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Device/emulator readiness is not verified before `launch()`** — ADB may report a device as connected while it is still booting. STOP. Verify the device is fully ready (`adb wait-for-device` + boot animation check) before calling `launch()`.
- **Assertions use generic element count or non-specific predicates** — An assertion that `clickableElements.length > 0` will pass on any screen including error screens. STOP. Every assertion must target a specific resource ID, content description, or exact text value.
- **`disconnect()` is not called after scenario completes** — Leaving an ADB connection open locks the device port and can prevent subsequent scenarios from connecting. STOP. Always call `disconnect()` in a teardown block, even if the scenario fails.
- **App state from a prior scenario is not cleared** — Leftover session tokens, shared preferences, or cached data from scenario N will contaminate scenario N+1. STOP. Terminate the app and clear app data between scenarios.
- **`screenshot()` is called but the image is not linked in eval evidence** — Screenshots without file path references in the output are invisible to the eval judge. STOP. Every `screenshot()` call must record the file path in the scenario output.
- **ANR dialogs are dismissed without logging** — An ANR indicates the app's main thread was blocked. Dismissing it silently hides a testable bug. STOP. Log the ANR occurrence and record it as a FAIL before dismissing.

## Host and device resolution (before `connect()`)

Use this **every** eval run so failures are **actionable** (missing SDK vs no device vs wrong device), not opaque.

### Preflight — host capability, logging, failure modes (run before §1)

**Log file (canonical):** **`mkdir -p ~/forge/brain/prds/<task-id>/qa/logs`** then append to **`eval-preflight-<ISO8601>.log`** (see **`skills/forge-brain-layout/SKILL.md`** **qa/logs/**). Start each probe block with **`--- android ---`**. **Tee** or redirect **stdout + stderr** of **`adb`**, **`emulator`**, **`sdkmanager`**, **`avdmanager`** into that file so crashes are debuggable.

| Check | Action |
|--------|--------|
| **Environment** | If **`which adb`** fails or **`emulator` / `sdkmanager` missing**, append checklist to log: **`ANDROID_HOME`**, **`ANDROID_SDK_ROOT`**, **`PATH`** must include **`platform-tools`**, **`emulator`**, **`cmdline-tools/latest/bin`**. Tell user to fix env and retry — **do not** guess paths. |
| **Linux KVM (acceleration)** | On Linux: **`[ -r /dev/kvm ]`**; if **`kvm-ok`** exists, run it. **No KVM** (or CI without `/dev/kvm`) → hardware emu often **too slow or stuck**; **BLOCK** with log path: use a **KVM-capable host**, **physical USB device**, or **external device farm** — **no infinite boot wait**. |
| **Timeouts (no infinite loops)** | Cap **wall-clock** for emulator start (team default e.g. **10–15 min** first boot). Cap **poll iterations** for **`sys.boot_completed`** (e.g. **60** tries × **5 s** = **5 min** max) — then **BLOCK** with last **`adb`** / **`getprop`** lines in log. |
| **Air-gapped / download failure** | If **`sdkmanager`** / image install fails (network, 403, disk): **STOP**, paste **stderr** into log, **do not** blind-retry. Suggest **proxy**, **offline SDK mirror**, or **Android Studio** SDK Manager — user must decide. |
| **Permission errors (SDK dirs)** | If **`EACCES`** / cannot write under **`ANDROID_HOME`**: **do not** run **`sudo`** inside the agent session. Print **exact** **`chown`**/**`chmod`** or one-line **`sudo`** commands for the **user’s terminal**, then **`AskUserQuestion`**: *Applied — retry preflight?* per **`using-forge`**. |

**Non-empty AVD list but no running emulator (before `connect()`):** This path is **common** (e.g. **`Pixel_10_Pro_XL`** exists but **`adb devices`** is empty). It is **not** the same as **§5** (zero AVDs).

1. After § Preflight env/KVM checks, run **`adb devices -l`** and **`emulator -list-avds`**; append to **`qa/logs/eval-preflight-*.log`**.
2. If **`emulator -list-avds`** returns **≥1** name and **`adb devices`** shows **no** usable **`emulator-555x`** / **`device`** row (empty list or only **`offline`**/**`unauthorized`**): **list the AVD names** and use **`AskUserQuestion`**: *Boot one of these now for Android eval? Which AVD?* (or *defer / use USB device*). **Do not** assume **`url-only`** from **`qa-branch-env-prep`** meant “skip Android” — explicit decline → log **`drivers=skipped_reason=android:no_running_device_user_declined_boot`** when scenarios still require Android.
3. On **confirm**, follow **§3 Boot path** with **§ Preflight** timeouts — **no** unbounded **`wait-for-device`** / **`getprop`** loops.
4. **`qa-branch-env-prep` Step 0.0** may already have listed the same AVDs — **still** confirm boot here before **`connect()`** if no device is attached.

### 1. Preconditions (fail fast with a clear message)

- **`adb` in PATH** — If `which adb` fails, tell the user: install **Android SDK Platform-Tools**, or set **`ANDROID_HOME`** (or **`ANDROID_SDK_ROOT`**) and add **`$ANDROID_HOME/platform-tools`** to **PATH**. Do not guess paths.
- **`ANDROID_HOME`** — If `adb` works but `emulator` / `avdmanager` are needed and are missing from PATH, same fix (often **`$ANDROID_HOME/emulator`** and **`$ANDROID_HOME/cmdline-tools/latest/bin`**).

### 2. Discover in the right order (`adb` vs `emulator`)

**`adb devices -l` only shows emulators that are already running** and connected to adb. It will **not** list AVDs that exist on disk but are powered off.

Use **both** layers:

1. **Running targets** — **`adb devices -l`** (or **`adb devices`**) for **already booted** emulators (`emulator-5554`, …) and **USB** devices (`device`, not `unauthorized` / `offline` unless you can fix with **`adb kill-server`** + replug).
2. **Installable / offline AVDs** — **`emulator -list-avds`** (binary usually under **`$ANDROID_HOME/emulator`**; put that dir on **PATH**). That lists **AVD names** you can **boot** with **`emulator`** even though they do **not** yet appear under `adb devices`.

**No AVDs in `emulator -list-avds`** does not rule out a **physical** device on USB — still use **`adb devices`**.

### 3. Boot path when the target is an AVD, not yet in `adb devices`

When the scenario, **`forge-product.md`**, or the user names an **AVD** (or API level → pick matching AVD from **`emulator -list-avds`**) but **`adb devices`** does not yet show that emulator:

1. Ensure **`emulator`** is on **PATH** (typically **`$ANDROID_HOME/emulator`**).
2. Start it in the background, e.g. **`emulator -avd <AvdName> -no-snapshot-load &`** (add **`-gpu`** / **`-no-window`** flags per host/CI needs). Older installs may accept **`emulator @<AvdName>`** — use what works on the host.
3. **`adb wait-for-device`** — wait until **some** device serial appears; then confirm the serial you care about (often **`emulator-5554`** incrementing).
4. **Boot complete** — poll **`adb shell getprop sys.boot_completed`** (and/or boot animation) until **`1`** before **`connect()`** / **`launch()`** — same requirement as elsewhere in this skill (emulator “listed” in adb can still be booting).

If **`emulator`** is missing, or **`emulator -list-avds`** is empty and no USB device exists, **STOP** and tell the user: install system images / create an AVD in **Android Studio Device Manager** or **`avdmanager`**, or attach a device — do not assume an emulator will appear.

### 4. Choose `device_id` (priority order) — after boot if needed

1. **Eval scenario / driver config** — **`device_id`**, **`ANDROID_SERIAL`**, **`emulator_id`**, or **`avd_name`** / **API level** pin: if **`avd_name`** (or resolvable AVD) is given and not running, follow **Boot path when the target is an AVD** (step 3 above), then connect to the resulting **`emulator-555x`** serial.
2. **`forge-product.md`** — **`services.<app>.emulator_id`** (serial) or team field for **AVD name** / API — same: boot first if only AVD is known.
3. **Environment** — **`ANDROID_SERIAL`** when it matches a **current** `adb devices` row (after any boot).
4. **Single running device** — Exactly **one** usable row → may use **`default`** without asking.
5. **Multiple running devices, no pin** — **Interactive:** list rows + **ask once**. **CI:** **FAIL** — set **`ANDROID_SERIAL`** / scenario pin, or start **only one** emulator before eval.

### 5. Create AVD / “API x” from nothing (`avdmanager`)

- Prefer **booting an existing AVD** that matches the requested **API level** (or closest name from **`emulator -list-avds`**).
- **Creating** a new AVD (**`avdmanager create avd`**) + **installing** system images (**`sdkmanager`**) is **slow**, **license-** and **network-sensitive**, and often **breaks unattended**. If it fails, return **BLOCKED** with the exact stderr (e.g. **`sdkmanager --licenses`**, missing **`cmdline-tools`**, accept licenses).
- If spawn/create is impossible, return **`success: false`** with env/SDK/timeout detail — **never** silently skip mobile eval.

**Ordered path when `emulator -list-avds` is empty and no USB device** (log each step to **`qa/logs/eval-preflight-*.log`**):

1. **List installed system images** — **`sdkmanager --list_installed`** (and/or list **`system-images`** packages). If a **usable** **Google APIs** / **default** x86_64 image exists for the target API, run **`avdmanager create avd -n <name> -k <system-image-id>`** with **non-interactive** flags (`--force` if supported). See **`sdkmanager --licenses`** if prompted.
2. If **no** suitable image is installed: **`AskUserQuestion`** for **API level** and **ABI** (e.g. **google_apis** vs **default**, **x86_64**). Install packages such as **`platforms;android-XX`** and **`system-images;android-XX;google_apis;x86_64`** via **`sdkmanager`** — append full stderr on failure (**air-gap** → stop with evidence).
3. **Create AVD** with **`avdmanager create avd`**, then **boot** per **§3** with **§ Preflight** timeouts (**no** unbounded **`getprop`** loop).
4. **`adb wait-for-device`** → **`sys.boot_completed == 1`** within capped polls — else **BLOCK** with log tail.

### 5b. Optional: Appium MCP / Appium server (host choice)

If the human chooses **Appium** over raw ADB UIAutomator (per **CLAUDE.md** D5 — **ask** first): follow upstream **[appium/appium-mcp](https://github.com/appium/appium-mcp)** for MCP wiring; **`npm i -g appium`** may require **Node** — if **`npm`** / **`node`** missing, tell user to install **Node LTS**, then retry. **Do not** **`sudo`** in-agent for system-wide installs; document failures in **`qa/logs/`**. Align with **`qa-semantic-csv-orchestrate`** so one path is selected per task.

### 6. Unbiased expectation

This block improves **debuggability** and **interactive** UX; it does **not** guarantee one-command greenfield emulators on every laptop. **CI** should still document: **pre-start** one emulator (or attach one device) and set **`ANDROID_SERIAL`**, or pass **`avd_name`** / boot script so **`emulator`** + **`adb wait-for-device`** succeed without prompts.

## Edge cases (summary — full code in `reference/edge-cases-and-lifecycle.md`)

| # | Edge case | Detect | Recover |
|---|---|---|---|
| 1 | ANR dialog | "Not Responding" TextView in the UI dump | tap **Wait** (`button1`); if still stuck `am force-stop` + relaunch; **log as FAIL** before dismissing |
| 2 | App backgrounded / killed / restarted | no `com.<app>` elements in the dump | `launch()` (idempotent), `getUI(1000)`, re-query element positions |
| 3 | Permission dialog | Allow/Deny buttons present | tap **Allow** (or exercise the Deny path); verify feature works / degrades gracefully |
| 4 | Slow device | `getUI()` takes > 1.5 s | raise `wait_time` to 1000–2000 ms, add post-`tap()` delays, longer swipe durations |
| 5 | Network change (wifi → cell → offline) | offline banner / `dumpsys connectivity` | toggle airplane mode, assert offline UI, restore, verify auto-sync + data consistency |
| 6 | UI element timing (lazy render / animation) | zero bounds or `clickable:false` | retry loop until non-zero bounds **and** clickable; scroll-to-element first |

Full detection/recovery code, supported platforms, and **device-lifecycle** tests
(foreground/background, runtime permission grant/deny/revoke, back-button, memory
pressure) → **`reference/edge-cases-and-lifecycle.md`**.

## Out of Scope (Future Phases)

- iOS automation (separate eval-driver-ios-xctest skill planned)
- WebDriver protocol integration
- Performance profiling and metrics collection
- Parallel multi-app evaluation
- Advanced gesture recognition (pinch, rotate)
- Screen recording and video playback
- Custom UIAutomator instrumentation code
- Integration with APK installation/management

## Reference (load on demand)

This SKILL.md is the operational contract (runner dispatch, preflight / device
resolution, discipline, edge-case summary). The catalog and depth live under
`reference/` — read the one the task needs (Agent Skills progressive disclosure):

- **`reference/adb-driver-api.md`** — ADB/UIAutomator architecture; the full API (`connect`, `launch`, `tap`, `type`, `swipe`, `getUI`, `screenshot`, `teardown`) with parameters/returns/errors; a complete example; implementation notes; the usage workflow.
- **`reference/edge-cases-and-lifecycle.md`** — full code for the 6 edge cases above, supported platforms, and device-lifecycle tests.
- **`reference/uiautomator-guide.md`** — element selection (resource id / text / class), dialog & system-popup handling, scrolling/gestures, ANR recovery & detection, and the error-handling reference.

## Checklist

Before running an Android ADB eval scenario:

- [ ] Device/emulator readiness verified (not just ADB connected — fully booted)
- [ ] App state cleared from prior scenario (terminate + clear data)
- [ ] All assertions target specific resource IDs, content descriptions, or exact text
- [ ] ANR dialogs monitored and logged (not silently dismissed)
- [ ] `screenshot()` called and file path recorded in scenario output
- [ ] `disconnect()` called in all paths (success, failure, timeout)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] ADB device/emulator listed by `adb devices` before test run; UI hierarchy captured on FAIL.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

- `qa-semantic-csv-orchestrate`: Generates `qa/semantic-automation.csv` with `android` surface steps that this driver executes.
- `eval-judge`: Aggregates Android step outcomes from `semantic-eval-run.log` into a final PASS/FAIL/YELLOW verdict.
- `forge-eval-gate`: Consumes `semantic-eval-manifest.json` written by this driver to gate PR merge.
- `qa-live-app`: Higher-level skill that orchestrates this driver as part of live app testing.
- `docs/semantic-eval-csv.md`: CSV column definitions and `android` surface alias (`android-adb`) used by this driver.
- `docs/semantic-eval-schema.md`: JSON schema for `semantic-eval-manifest.json` and step outcome enum (PASS/FAIL/BLOCKED_DEPENDENCY/CONTEXT_GAP/SKIPPED).
