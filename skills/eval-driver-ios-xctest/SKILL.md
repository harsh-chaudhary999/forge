---
name: eval-driver-ios-xctest
description: "Eval driver for iOS via XCTest + xcrun simctl. Functions: connect(simulator_id), launch(bundle_id), tap(target), type(text), swipe(direction, element), assert_element(target), screenshot(), disconnect(). Use when eval scenario has driver=ios-xctest."
type: rigid
requires: [eval-scenario-format]
---

# eval-driver-ios-xctest Skill

**Phase 3.4: Eval Driver for iOS via XCTest + xcrun simctl**

This skill provides a complete iOS app automation driver using XCTest UI Testing framework and `xcrun simctl` for simulator control. It enables programmatic interaction with iOS simulators and devices for eval scenarios.

## Anti-Pattern Blockers

**DO NOT proceed with these rationalizations:**

1. **"Simulator is enough, skip real device"** — Incorrect. Simulators lack real network conditions, push notifications, biometrics, and camera. Device testing is required for production confidence.

2. **"XCTest is only for unit tests"** — Incorrect. XCTest UI Testing provides full UIInterruptionMonitor, element queries, gesture simulation, and accessibility identifier targeting.

3. **"iOS is too complex, skip mobile eval"** — Incorrect. iOS eval follows the same pattern as Android: connect → launch → interact → assert → screenshot → disconnect.

4. **"We tested Android, iOS is the same"** — Incorrect. iOS has distinct permission dialogs (system alerts via UIInterruptionMonitor), different lifecycle (foreground/background/suspended), and different element locators (accessibility identifiers vs resource IDs).

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Simulator booted state is not verified before launch** — `xcrun simctl launch` on a non-booted simulator silently fails or spawns a zombie process. STOP. Always confirm `Booted` status via `xcrun simctl list devices` before calling `launch()`.
- **Assertions use `XCTAssertTrue(app.otherElements.count > 0)` or other non-specific checks** — Non-specific assertions mean any element satisfies the condition; the test cannot fail on wrong content. STOP. Every assertion must target a named accessibility identifier or exact element predicate.
- **UIInterruptionMonitor is not registered before actions that trigger system alerts** — iOS permission dialogs (camera, notifications, location) interrupt UI flows without an active monitor. STOP. Register a UIInterruptionMonitor before any action that could trigger a system alert.
- **`disconnect()` is not called after scenario completes** — An unclosed simulator connection leaves dangling process references and prevents the next scenario from cleanly booting the same simulator. STOP. Always call `disconnect()` in a teardown block, even if the scenario fails.
- **App state from prior scenario is not cleared before new scenario** — Leftover keychain entries, cached tokens, or persisted user defaults contaminate subsequent test runs. STOP. Reset app state with `app.terminate()` + `xcrun simctl privacy reset` before each scenario.
- **`screenshot()` is called but the image is not attached to the eval report** — Screenshots without links to evidence are invisible to the eval judge. STOP. Every `screenshot()` call must save the file and record the path in the scenario output.

## Prerequisites

- Xcode installed (provides `xcrun`, `simctl`, `xcodebuild`)
- iOS Simulator or connected device (developer mode enabled)
- App built with `-destination` flag or `.app` bundle available
- `idb` (optional, for enhanced device support): `pip install fb-idb`

## Architecture

### xcrun simctl

`simctl` manages iOS simulators — create, boot, install apps, send notifications, and control lifecycle.

```bash
xcrun simctl list devices          # list available simulators
xcrun simctl boot <simulator_id>   # boot a simulator
xcrun simctl install <id> <app>    # install .app bundle
xcrun simctl launch <id> <bundle>  # launch app by bundle ID
xcrun simctl terminate <id> <bundle>
xcrun simctl screenshot <id> <path>
```

### XCTest UI Testing

XCTest UI tests run inside the app process and use the Accessibility framework to find and interact with elements.

Element locators (in priority order):
1. `accessibilityIdentifier` — most stable, set in code
2. `label` (accessibility label) — visible text or explicit label
3. `type` — element type (button, textField, staticText, etc.)
4. `predicate` — NSPredicate query for complex matching

### idb (optional)

Facebook's `idb` provides a stable gRPC interface over simctl/XCTest for programmatic control without Xcode UI:

```bash
idb connect <udid>
idb ui tap <x> <y> --udid <udid>
idb ui text <text> --udid <udid>
idb screenshot --udid <udid> /tmp/screen.png
```

## API Reference

### connect(simulator_id)

Boots and connects to an iOS simulator or device.

**Parameters:**
- `simulator_id` (string): Simulator UDID or device UDID
  - Use `"default"` to connect to first booted simulator
  - Use `xcrun simctl list devices` to find UDIDs
  - Format: `"A1B2C3D4-E5F6-7890-ABCD-EF1234567890"`

**Returns:**
```javascript
{
  simulator_id: "A1B2C3D4-E5F6-7890-ABCD-EF1234567890",
  name: "iPhone 15 Pro",
  ios_version: "17.0",
  state: "Booted",
  success: true
}
```

**Bash implementation:**
```bash
# Boot simulator if needed
xcrun simctl boot "$simulator_id" 2>/dev/null || true
# Wait for boot
xcrun simctl bootstatus "$simulator_id" -b
# Get device info
xcrun simctl list devices | grep "$simulator_id"
```

**Error handling:**
- Simulator not found: returns `success: false`
- Boot timeout (>60s): returns `success: false`
- Already booted: continues (idempotent)

---

### launch(sim, bundle_id)

Installs (if needed) and launches an app on the connected simulator.

**Parameters:**
- `sim` (object): Connection object from `connect()`
- `bundle_id` (string): App bundle identifier (e.g., `"com.shopapp.ios"`)
- `app_path` (string, optional): Path to `.app` bundle for installation

**Returns:**
```javascript
{
  success: true,
  bundle_id: "com.shopapp.ios",
  pid: 12345
}
```

**Bash implementation:**
```bash
# Install app (if app_path provided)
xcrun simctl install "$simulator_id" "$app_path"
# Launch
xcrun simctl launch "$simulator_id" "$bundle_id"
```

**Error handling:**
- Bundle not installed and no app_path: returns `success: false`
- App crashes on launch: returns `success: false` with crash log
- Launch timeout (>30s): returns `success: false`

---

### tap(sim, target)

Taps an element by accessibility identifier, label, or coordinates.

**Parameters:**
- `sim` (object): Connection object
- `target` (object): One of:
  - `{ x: number, y: number }` — screen coordinates
  - `{ accessibility_id: "string" }` — accessibility identifier (preferred)
  - `{ label: "string" }` — accessibility label / visible text
  - `{ type: "button", label: "string" }` — element type + label

**Returns:**
```javascript
{
  success: true,
  target: { x: 195, y: 420 },
  element: { accessibility_id: "signup_button", label: "Sign Up" }
}
```

**Bash implementation (via idb):**
```bash
# By coordinates
idb ui tap "$x" "$y" --udid "$simulator_id"

# By accessibility ID (via xcodebuild UI test helper)
xcodebuild test -scheme ForgeUITests \
  -destination "id=$simulator_id" \
  -testArguments "tap:$accessibility_id"
```

**Error handling:**
- Element not found: waits up to 5s for element to appear, then returns `success: false`
- System alert present: handle via UIInterruptionMonitor (see `dismiss_alert`)
- App backgrounded: returns `success: false`

---

### type(sim, text, clear_field)

Types text into the currently focused field.

**Parameters:**
- `sim` (object): Connection object
- `text` (string): Text to input (Unicode supported)
- `clear_field` (boolean, optional): Select all and delete before typing (default: false)

**Returns:**
```javascript
{ success: true, text_sent: "hello@example.com", field_cleared: false }
```

**Bash implementation:**
```bash
idb ui text "$text" --udid "$simulator_id"
```

---

### swipe(sim, direction, element)

Swipes in a direction, optionally scoped to an element.

**Parameters:**
- `sim` (object): Connection object
- `direction` (string): `"up"` | `"down"` | `"left"` | `"right"`
- `element` (object, optional): Element to swipe within (same format as `tap` target)
- `distance` (number, optional): Swipe distance 0.0–1.0 (default: 0.5)

**Returns:**
```javascript
{ success: true, direction: "up", distance: 0.5 }
```

---

### assert_element(sim, target, timeout)

Asserts an element exists and is visible. Fails eval step if not found within timeout.

**Parameters:**
- `sim` (object): Connection object
- `target` (object): Element target (same format as `tap`)
- `timeout` (number, optional): Max wait in seconds (default: 5)

**Returns:**
```javascript
{
  success: true,
  found: true,
  element: {
    accessibility_id: "welcome_banner",
    label: "Welcome back",
    visible: true,
    frame: { x: 0, y: 100, width: 390, height: 60 }
  }
}
```

---

### dismiss_alert(sim, button_label)

Handles iOS system permission dialogs (camera, notifications, location).

**Parameters:**
- `sim` (object): Connection object
- `button_label` (string): Button text to tap — `"Allow"`, `"Don't Allow"`, `"OK"`

**Returns:**
```javascript
{ success: true, alert_title: "\"ShopApp\" Would Like to Send You Notifications", dismissed: true }
```

**Note:** Must be called when system alert is blocking interaction. Register as UIInterruptionMonitor before triggering the permission-requesting action.

---

### screenshot(sim, path)

Captures a screenshot of the current simulator state.

**Parameters:**
- `sim` (object): Connection object
- `path` (string, optional): Output path (default: `/tmp/forge-ios-<timestamp>.png`)

**Returns:**
```javascript
{ success: true, path: "/tmp/forge-ios-1234567890.png", size_bytes: 204800 }
```

**Bash implementation:**
```bash
xcrun simctl io "$simulator_id" screenshot "$path"
```

---

### disconnect(sim)

Terminates the app and optionally shuts down the simulator.

**Parameters:**
- `sim` (object): Connection object
- `shutdown` (boolean, optional): Shut down simulator after disconnect (default: false)

**Returns:**
```javascript
{ success: true, simulator_id: "...", shutdown: false }
```

---

## Eval Scenario Integration

Scenarios using this driver set `driver: ios-xctest`:

```yaml
scenario: ios_signup_flow
driver: ios-xctest
simulator_id: "default"
bundle_id: "com.shopapp.ios"

steps:
  - action: connect
    params:
      simulator_id: "default"

  - action: launch
    params:
      bundle_id: "com.shopapp.ios"

  - action: tap
    params:
      target: { accessibility_id: "get_started_button" }

  - action: dismiss_alert
    params:
      button_label: "Allow"

  - action: type
    params:
      text: "test@example.com"
      clear_field: true

  - action: assert_element
    params:
      target: { accessibility_id: "home_screen" }
      timeout: 10

  - action: screenshot
    params:
      path: "/tmp/ios-signup-result.png"

  - action: disconnect
```

## Differences from Android Driver

| Aspect | Android (ADB) | iOS (XCTest) |
|---|---|---|
| Element locator | `resource_id` | `accessibility_id` |
| System dialogs | Auto-dismissed by ADB | Requires `dismiss_alert` |
| Emulator control | `adb -e` | `xcrun simctl` |
| Text input | `adb shell input text` | `idb ui text` or XCTest |
| Screenshot | `adb shell screencap` | `xcrun simctl io screenshot` |
| Device listing | `adb devices` | `xcrun simctl list devices` |
| App install | `adb install` | `xcrun simctl install` |

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| `Simulator not booted` | `xcrun simctl boot` not called | Call `connect()` first |
| `Bundle not installed` | App not on simulator | Provide `app_path` to `launch()` |
| `Element not found` | Accessibility ID missing or screen not ready | Add `assert_element` wait before tap |
| `System alert blocking` | Permission dialog intercepted interaction | Call `dismiss_alert` before affected action |
| `SpringBoard crash` | Simulator overloaded | Restart simulator, reduce parallel scenarios |

---

## Edge Cases & Failure Modes

### Edge Case 1: Simulator Not Running or Not Booted

**Scenario**: You attempt to launch an app on a simulator that is not currently running or booted, or the simulator UUID doesn't exist.

**Symptom**: `SimulatorError: Simulator not found` or `xcrun simctl launch` silently fails with exit code 1. App process is never created.

**Do NOT**: Assume the simulator is booted. Do NOT call `launch()` without verifying simulator state. Do NOT use hardcoded simulator IDs that might not exist on this machine.

**Mitigation**:
- Always call `connect()` first, which performs `xcrun simctl bootstatus` verification
- Check simulator list before connecting: `xcrun simctl list devices | grep Booted`
- Use `"default"` as simulator_id to auto-select first booted simulator
- Verify boot completed before proceeding; wait for Springboard to be ready
- Add explicit timeout for boot operations (>60 seconds indicates infrastructure issue)

**Example**:
```javascript
// GOOD: Verify simulator state before launch
const simList = await bash("xcrun simctl list devices | grep '(Booted)'")
if (!simList || simList.length === 0) {
  throw new Error("BLOCKED: No booted simulator found. Start a simulator first.")
}

const sim = await connect({ simulator_id: "default" })
if (sim.state !== "Booted") {
  throw new Error(`BLOCKED: Simulator ${sim.simulator_id} is not booted (state: ${sim.state})`)
}

const launchResult = await launch(sim, "com.example.app")
if (!launchResult.success) {
  throw new Error(`BLOCKED: Failed to launch app. Check app is built and installed.`)
}

// BAD: Assume simulator exists
const sim2 = await connect({ simulator_id: "UUID-that-might-not-exist" })
```

**Escalation**: `BLOCKED` — Simulator infrastructure not ready. Verify Xcode installation and simulator availability.

---

### Edge Case 2: Test Timeout (Slow UI Rendering or Missing Element)

**Scenario**: Your eval waits for a UI element to appear (via `assert_element` or implicit tap wait), but the element never appears within the 5-second default timeout. This could be due to slow rendering, slow network, or the element genuinely missing.

**Symptom**: `TimeoutError: Element not found within 5000ms` or `assert_element` returns `success: false` after timeout.

**Do NOT**: Increase timeout to 30 seconds as a blanket fix. Do NOT ignore timeout failures; they indicate a real problem. Do NOT assume network latency; profile the app's rendering performance.

**Mitigation**:
- Use explicit waits before tap: `assert_element(sim, target, timeout)` with adequate timeout (10-15s for slow networks)
- Profile rendering speed with Xcode Instruments before eval to establish realistic timeouts
- Check simulator performance: slow simulators (especially iOS 16+) may need longer timeouts
- Verify element accessibility identifier is present in app code (`UIView.accessibilityIdentifier`)
- Add intermediate assertions to narrow down where delay occurs (e.g., assert splash screen fades before next element)

**Example**:
```javascript
// GOOD: Explicit wait before interaction
const connResult = await assert_element(sim, {
  accessibility_id: "splash_screen_fade"
}, 10)  // Wait 10s for splash to fade
if (!connResult.found) {
  throw new Error("NEEDS_CONTEXT: Splash screen did not fade within timeout. App may be slow or hanging.")
}

// Now safe to interact
await tap(sim, { accessibility_id: "get_started_button" })

// BAD: Assume element appears instantly
await tap(sim, { accessibility_id: "some_button" })  // May timeout if not ready
```

**Escalation**: `NEEDS_CONTEXT` — Profile app rendering performance. Verify element accessibility IDs are configured in app code.

---

### Edge Case 3: Memory Pressure / App Crash During Test

**Scenario**: The iOS app is terminated due to memory pressure (jetsam) or crashes during test execution. This is common in simulators under heavy load or with memory leaks.

**Symptom**: `AppCrashError: App 'com.example.app' was terminated` or `SpringBoard shows crash report dialog` blocking further interactions.

**Do NOT**: Continue test after app crash without restart. Do NOT assume memory pressure won't happen in production. Do NOT leak resources in eval setup (large image loads, etc.).

**Mitigation**:
- Always wrap eval in try/finally with `disconnect()` to cleanly terminate and restart app
- Profile memory usage with Xcode before eval; memory leaks will cause crashes under load
- Reduce parallelism: run fewer eval scenarios concurrently to reduce memory pressure
- Clear app cache and large resources before running eval: `app.terminate()` + reset keychain
- Monitor system memory with `xcrun simctl diagnose` to detect resource exhaustion

**Example**:
```javascript
// GOOD: Handle app crash gracefully
const sim = await connect({ simulator_id: "default" })
try {
  const launchResult = await launch(sim, "com.example.app")
  if (!launchResult.success) {
    throw new Error("BLOCKED: App failed to launch.")
  }
  
  // Run test steps
  await tap(sim, { accessibility_id: "button" })
  
} catch (err) {
  if (err.message.includes("App") && err.message.includes("terminated")) {
    // App crashed
    throw new Error("DONE_WITH_CONCERNS: App crashed during test. Memory leak or jetsam. Profile with Instruments.")
  }
  throw err
} finally {
  // Always disconnect, even on crash
  await disconnect(sim, { shutdown: false })
}

// BAD: Continue after crash
const sim2 = await connect({ simulator_id: "default" })
await launch(sim2, "com.example.app")
await tap(sim2, { accessibility_id: "button" })
// If app crashes here, no cleanup happens
```

**Escalation**: `DONE_WITH_CONCERNS` — App crashed. Profile for memory leaks with Xcode Instruments.

---

### Edge Case 4: Simulator State Pollution (Previous Test Left App in Bad State)

**Scenario**: A previous test run left the app in an inconsistent state: cached authentication tokens, persisted user defaults, leftover keychain entries, or unsaved state. The current eval tries to run signup but app thinks user is already logged in.

**Symptom**: `ExecutionError: Expected login screen, but app showed home screen` or weird navigation flows that don't match scenario.

**Do NOT**: Assume app state is clean between eval scenarios. Do NOT skip app reset. Do NOT rely on app's own logout to be complete.

**Mitigation**:
- Always reset app state before scenario: `app.terminate()` + `xcrun simctl privacy reset` for permissions + clear keychain
- Use `--reset-contents-and-settings` when booting simulator for completely fresh state
- Clear app-specific data: defaults, cache, cookies via terminal commands or API
- For critical scenarios, create fresh test user accounts instead of reusing old ones
- Verify initial state with assertion before proceeding: `assert_element(sim, { accessibility_id: "login_screen" })`

**Example**:
```javascript
// GOOD: Full state reset between scenarios
const sim = await connect({ simulator_id: "default" })

// Step 1: Terminate app
await execute(sim, "app.terminate()")

// Step 2: Reset simulator privacy/permissions
await bash("xcrun simctl privacy reset ${sim.simulator_id} all")

// Step 3: Clear keychain
await bash("xcrun simctl keychain reset ${sim.simulator_id}")

// Step 4: Relaunch clean
const launchResult = await launch(sim, "com.example.app")

// Step 5: Verify initial state (login screen should appear)
await assert_element(sim, {
  accessibility_id: "login_screen"
}, 10)

// Now eval is guaranteed to start from clean state

// BAD: Skip cleanup
const sim2 = await connect({ simulator_id: "default" })
await launch(sim2, "com.example.app")
// State from last run might interfere!
```

**Escalation**: `NEEDS_COORDINATION` — State pollution indicates scenario dependency. Coordinate to ensure each scenario resets state independently.

---

### Edge Case 5: System Alert Blocking Without UIInterruptionMonitor

**Scenario**: A system permission dialog (notification, location, camera) appears unexpectedly, blocking your tap/type actions. Without a registered `UIInterruptionMonitor`, the eval hangs waiting for the alert to dismiss.

**Symptom**: `TimeoutError: Element tap blocked by system alert` or `assert_element` times out because system dialog is covering the target.

**Do NOT**: Assume system alerts won't appear. Do NOT hardcode alert dismissals; use UIInterruptionMonitor. Do NOT ignore permission requests; they're part of UX.

**Mitigation**:
- Register `UIInterruptionMonitor` BEFORE any action that triggers permissions (camera, location, notifications)
- Use `dismiss_alert(sim, "Allow")` or `dismiss_alert(sim, "Don't Allow")` based on scenario requirements
- For multiple alerts, register multiple monitors (one per expected alert)
- Always dismiss alerts in try/finally to ensure cleanup even if test fails
- Document which permissions each eval scenario requires

**Example**:
```javascript
// GOOD: Expect and handle system alerts
const sim = await connect({ simulator_id: "default" })
await launch(sim, "com.example.app")

// Register monitor BEFORE triggering permissions
// This catches system alerts and dismisses them automatically
const alertMonitor = {
  predicate: "type == 'XCUIElementTypeAlert' AND name CONTAINS 'Notification'",
  button_to_tap: "Allow"
}

// Now trigger action that causes permission request
await tap(sim, { accessibility_id: "enable_notifications_button" })

// Handle the alert
await dismiss_alert(sim, "Allow")

// Verify notification was enabled
await assert_element(sim, {
  accessibility_id: "notifications_enabled_badge"
}, 5)

// BAD: No alert handling
const sim2 = await connect({ simulator_id: "default" })
await launch(sim2, "com.example.app")
await tap(sim2, { accessibility_id: "enable_notifications_button" })
// System dialog appears but there's no monitor → test hangs!
```

**Escalation**: `NEEDS_CONTEXT` — System alert handling requires knowledge of permission requests in app flow. Coordinate with app team on which permissions are triggered.

---

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
