---
name: eval-driver-android-adb
description: "WHEN: Eval scenario requires Android app interaction or assertion. Eval driver for Android via ADB + UIAutomator. Functions: connect(device_id), launch(package), tap(target), type(text), swipe(direction), assert_element(target), screenshot(), disconnect()."
type: rigid
requires: [eval-scenario-format]
version: 1.0.0
preamble-tier: 3
triggers:
  - "eval on Android"
  - "ADB eval driver"
  - "run Android eval"
allowed-tools:
  - Bash
  - Read
---

# eval-driver-android-adb Skill

**Phase 3.4: Eval Driver for Android via ADB + UIAutomator**

This skill provides a complete Android mobile app automation driver using Android Debug Bridge (ADB) and UIAutomator. It enables programmatic interaction with Android devices and emulators for eval scenarios, testing, and automation.

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

When an **Appium MCP** server (or similar mobile MCP) is available on the host, the operator may prefer it over **ADB + UIAutomator** for Android eval steps. **Ask explicitly**: use this skill’s **ADB driver** end-to-end, or **delegate Android UI actions to Appium MCP** (document MCP tool names, session/device assumptions, and evidence paths). Either path is valid for **product eval**; pick **one** per task so **`eval-coordinate-multi-surface`** and CI stay aligned.

## Anti-Pattern Blockers

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

When the scenario, **`product.md`**, or the user names an **AVD** (or API level → pick matching AVD from **`emulator -list-avds`**) but **`adb devices`** does not yet show that emulator:

1. Ensure **`emulator`** is on **PATH** (typically **`$ANDROID_HOME/emulator`**).
2. Start it in the background, e.g. **`emulator -avd <AvdName> -no-snapshot-load &`** (add **`-gpu`** / **`-no-window`** flags per host/CI needs). Older installs may accept **`emulator @<AvdName>`** — use what works on the host.
3. **`adb wait-for-device`** — wait until **some** device serial appears; then confirm the serial you care about (often **`emulator-5554`** incrementing).
4. **Boot complete** — poll **`adb shell getprop sys.boot_completed`** (and/or boot animation) until **`1`** before **`connect()`** / **`launch()`** — same requirement as elsewhere in this skill (emulator “listed” in adb can still be booting).

If **`emulator`** is missing, or **`emulator -list-avds`** is empty and no USB device exists, **STOP** and tell the user: install system images / create an AVD in **Android Studio Device Manager** or **`avdmanager`**, or attach a device — do not assume an emulator will appear.

### 4. Choose `device_id` (priority order) — after boot if needed

1. **Eval scenario / driver config** — **`device_id`**, **`ANDROID_SERIAL`**, **`emulator_id`**, or **`avd_name`** / **API level** pin: if **`avd_name`** (or resolvable AVD) is given and not running, follow **Boot path when the target is an AVD** (step 3 above), then connect to the resulting **`emulator-555x`** serial.
2. **`product.md`** — **`services.<app>.emulator_id`** (serial) or team field for **AVD name** / API — same: boot first if only AVD is known.
3. **Environment** — **`ANDROID_SERIAL`** when it matches a **current** `adb devices` row (after any boot).
4. **Single running device** — Exactly **one** usable row → may use **`default`** without asking.
5. **Multiple running devices, no pin** — **Interactive:** list rows + **ask once**. **CI:** **FAIL** — set **`ANDROID_SERIAL`** / scenario pin, or start **only one** emulator before eval.

### 5. Create AVD / “API x” from nothing (`avdmanager`)

- Prefer **booting an existing AVD** that matches the requested **API level** (or closest name from **`emulator -list-avds`**).
- **Creating** a new AVD (**`avdmanager create avd`**) + **installing** system images (**`sdkmanager`**) is **slow**, **license-** and **network-sensitive**, and often **breaks unattended**. If it fails, return **BLOCKED** with the exact stderr (e.g. **`sdkmanager --licenses`**, missing **`cmdline-tools`**, accept licenses).
- If spawn/create is impossible, return **`success: false`** with env/SDK/timeout detail — **never** silently skip mobile eval.

### 6. Unbiased expectation

This block improves **debuggability** and **interactive** UX; it does **not** guarantee one-command greenfield emulators on every laptop. **CI** should still document: **pre-start** one emulator (or attach one device) and set **`ANDROID_SERIAL`**, or pass **`avd_name`** / boot script so **`emulator`** + **`adb wait-for-device`** succeed without prompts.

## Architecture

### ADB (Android Debug Bridge)

ADB is the primary communication protocol with Android devices. It operates on a client-server model:

- **Server:** Runs on the host machine, manages connections
- **Daemon:** Runs on the device (adbd), handles commands
- **Client:** Command-line tool for issuing commands

Connection format: `adb connect <host>:<port>` or direct USB connection.

### UIAutomator

UIAutomator is Android's native UI automation framework. It provides:

- **Accessibility Service Integration:** Accesses UI hierarchy through accessibility framework
- **Element Locators:** Resource IDs, text content, class types, content descriptions
- **Actions:** Tap, swipe, type, long-press, scroll
- **XML Hierarchy:** Full DOM-like tree of UI elements with bounds and properties

UIAutomator commands are sent via ADB as shell commands:
```
adb shell uiautomator dump /sdcard/window_dump.xml
```

### Coordinate System

Android uses a standard Cartesian coordinate system:
- **Origin (0, 0):** Top-left corner
- **X-axis:** Horizontal, increases rightward
- **Y-axis:** Vertical, increases downward
- **Units:** Device-independent pixels (dp), reported as screen pixels

## API Reference

### connect(device_id)

Establishes connection to an Android device or emulator via ADB.

**Parameters:**
- `device_id` (string): Device identifier
  - For emulators: `"emulator-5554"`, `"emulator-5556"` (incremental ports)
  - For USB devices: Serial number (use `adb devices` to list)
  - Special value: `"default"` connects to the first available device

**Returns:**
- Object representing the ADB connection:
  - `device_id` (string): Connected device ID
  - `model` (string): Device model name
  - `android_version` (string): Android OS version
  - `api_level` (number): API level integer
  - `success` (boolean): Connection succeeded
  - `error` (string, optional): Error message if connection failed

**Example:**
```javascript
const adb = await connect('emulator-5554');
// {
//   device_id: 'emulator-5554',
//   model: 'Android SDK built for x86',
//   android_version: '12',
//   api_level: 31,
//   success: true
// }
```

**Error Handling:**
- If device not found: Returns `success: false` with error message
- If ADB daemon not running: Automatically starts daemon
- If device offline: Waits up to 10 seconds for recovery

### launch(adb, package_name, activity)

Starts an application by package name on the connected device.

**Parameters:**
- `adb` (object): ADB connection object from `connect()`
- `package_name` (string): Full package name (e.g., `"com.shopapp"`)
- `activity` (string, optional): Activity to launch within package (defaults to main activity)
  - Format: `.ActivityName` or `package.name.ActivityName`
  - If omitted, launches default activity

**Returns:**
- Object with launch result:
  - `success` (boolean): App launched successfully
  - `package_name` (string): Launched package
  - `activity` (string): Activity started
  - `pid` (number, optional): Process ID of launched app
  - `error` (string, optional): Error message if launch failed

**Example:**
```javascript
const result = await launch(adb, 'com.shopapp');
// { success: true, package_name: 'com.shopapp', activity: '.MainActivity', pid: 1234 }

const result2 = await launch(adb, 'com.shopapp', '.AuthActivity');
// { success: true, package_name: 'com.shopapp', activity: '.AuthActivity', pid: 1235 }
```

**Error Handling:**
- Package not installed: Returns `success: false`
- Activity not found: Returns `success: false`
- Launch timeout (>30s): Returns `success: false`

### tap(adb, target, duration)

Performs a tap/click at specified coordinates or on an element identified by resource ID.

**Parameters:**
- `adb` (object): ADB connection object
- `target` (object): Tap target specification
  - **Coordinates:** `{ x: number, y: number }` — Tap at pixel coordinates
  - **Resource ID:** `{ resource_id: "string" }` — Tap on element with matching resource ID
  - **Text Match:** `{ text: "string" }` — Tap on element containing exact text
  - **Class Match:** `{ class: "string" }` — Tap on first element of specified class
- `duration` (number, optional): Tap duration in milliseconds (default: 100)
  - Normal tap: 100ms
  - Long-press: 500-2000ms

**Returns:**
- Object with tap result:
  - `success` (boolean): Tap executed successfully
  - `target` (object): Actual coordinates tapped (resolved from ID if applicable)
  - `element` (object, optional): Element details if resource ID/text matched
  - `error` (string, optional): Error message

**Example:**
```javascript
// Tap by coordinates
const result1 = await tap(adb, { x: 500, y: 1000 });
// { success: true, target: { x: 500, y: 1000 } }

// Tap by resource ID
const result2 = await tap(adb, { resource_id: 'com.shopapp:id/signup_button' });
// { success: true, target: { x: 520, y: 1050 }, element: { ... } }

// Tap by text
const result3 = await tap(adb, { text: 'Next' });
// { success: true, target: { x: 450, y: 900 } }

// Long-press
const result4 = await tap(adb, { x: 300, y: 500 }, 1000);
// { success: true, target: { x: 300, y: 500 } }
```

**Error Handling:**
- Element not found (by ID/text): Returns `success: false`
- Out-of-bounds coordinates: Returns `success: false`
- Device locked or unresponsive: Returns `success: false`

### type(adb, text, clear_field)

Sends text input to the currently focused element (typically an EditText field).

**Parameters:**
- `adb` (object): ADB connection object
- `text` (string): Text to type
  - Supports Unicode characters
  - Special characters escaped automatically
  - Maximum length: 4KB per call
- `clear_field` (boolean, optional): Clear field before typing (default: false)

**Returns:**
- Object with input result:
  - `success` (boolean): Text input succeeded
  - `text_sent` (string): Actual text sent to device
  - `field_cleared` (boolean): Whether field was cleared first
  - `error` (string, optional): Error message

**Example:**
```javascript
// Simple text input
const result1 = await type(adb, '+1-234-567-8900');
// { success: true, text_sent: '+1-234-567-8900', field_cleared: false }

// Clear and type
const result2 = await type(adb, 'newemail@example.com', true);
// { success: true, text_sent: 'newemail@example.com', field_cleared: true }

// Unicode support
const result3 = await type(adb, '你好世界');
// { success: true, text_sent: '你好世界', field_cleared: false }
```

**Error Handling:**
- No focused field: Returns `success: false`
- Field not accepting input: Returns `success: false`
- Device unresponsive: Returns `success: false`

### swipe(adb, start, end, duration)

Performs a swipe/drag gesture from start coordinates to end coordinates.

**Parameters:**
- `adb` (object): ADB connection object
- `start` (object): Starting point `{ x: number, y: number }`
- `end` (object): Ending point `{ x: number, y: number }`
- `duration` (number, optional): Swipe duration in milliseconds (default: 500)
  - Quick swipe: 200-300ms
  - Smooth scroll: 500-1000ms
  - Slow drag: 1000ms+

**Returns:**
- Object with swipe result:
  - `success` (boolean): Swipe executed successfully
  - `start` (object): Start coordinates used
  - `end` (object): End coordinates used
  - `duration` (number): Actual duration executed (ms)
  - `distance` (number): Pixel distance traveled
  - `error` (string, optional): Error message

**Example:**
```javascript
// Swipe up (scroll down content)
const result1 = await swipe(adb, { x: 500, y: 800 }, { x: 500, y: 300 }, 500);
// { success: true, start: { x: 500, y: 800 }, end: { x: 500, y: 300 }, distance: 500 }

// Swipe left (navigate between tabs)
const result2 = await swipe(adb, { x: 800, y: 400 }, { x: 100, y: 400 }, 400);
// { success: true, start: { x: 800, y: 400 }, end: { x: 100, y: 400 }, distance: 700 }

// Swipe down (refresh)
const result3 = await swipe(adb, { x: 500, y: 100 }, { x: 500, y: 400 }, 600);
// { success: true, start: { x: 500, y: 100 }, end: { x: 500, y: 400 }, distance: 300 }
```

**Error Handling:**
- Out-of-bounds coordinates: Returns `success: false`
- Device unresponsive: Returns `success: false`

### getUI(adb, wait_time)

Extracts the complete UI hierarchy from the current screen, including element bounds, resource IDs, and content descriptions.

**Parameters:**
- `adb` (object): ADB connection object
- `wait_time` (number, optional): Milliseconds to wait for UI to stabilize (default: 500)
  - Use longer waits (1000+) after navigations or animations

**Returns:**
- Object with UI hierarchy:
  - `success` (boolean): UI dump retrieved successfully
  - `hierarchy` (string): Raw XML of UI tree (dumpsys accessibility format)
  - `elements` (array): Parsed elements with normalized properties
    - Each element has:
      - `resource_id` (string): Full resource ID or null
      - `text` (string): Visible text content or null
      - `class` (string): Android class name (e.g., "android.widget.Button")
      - `content_desc` (string): Content description (accessibility text) or null
      - `bounds` (object): `{ x1, y1, x2, y2 }` in screen coordinates
      - `center` (object): `{ x, y }` center of element
      - `enabled` (boolean): Is element enabled
      - `clickable` (boolean): Is element clickable
      - `children` (number): Count of child elements
  - `screen_width` (number): Screen width in pixels
  - `screen_height` (number): Screen height in pixels
  - `error` (string, optional): Error message

**Example:**
```javascript
const ui = await getUI(adb);
// {
//   success: true,
//   hierarchy: "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<hierarchy ...>",
//   elements: [
//     {
//       resource_id: "com.shopapp:id/signup_button",
//       text: "Sign Up",
//       class: "android.widget.Button",
//       content_desc: null,
//       bounds: { x1: 100, y1: 800, x2: 700, y2: 900 },
//       center: { x: 400, y: 850 },
//       enabled: true,
//       clickable: true,
//       children: 0
//     },
//     {
//       resource_id: "com.shopapp:id/email_input",
//       text: "user@example.com",
//       class: "android.widget.EditText",
//       content_desc: "Email address",
//       bounds: { x1: 50, y1: 200, x2: 750, y2: 300 },
//       center: { x: 400, y: 250 },
//       enabled: true,
//       clickable: true,
//       children: 2
//     }
//   ],
//   screen_width: 1080,
//   screen_height: 2400
// }

// Finding elements
const button = ui.elements.find(e => e.resource_id === 'com.shopapp:id/signup_button');
const signupBtn = ui.elements.find(e => e.text === 'Sign Up');
const emailField = ui.elements.find(e => e.class === 'android.widget.EditText');
```

**Error Handling:**
- Device offline: Returns `success: false`
- No UI dump available: Returns `success: false`
- XML parsing error: Returns `success: false` with error details

### screenshot(adb, filename, format)

Captures the current device screen and saves it locally.

**Parameters:**
- `adb` (object): ADB connection object
- `filename` (string): Output filename/path
  - Relative: Saved in current working directory
  - Absolute: Full path to save location (directory must exist)
  - Extensions: `.png`, `.jpg` recommended for format clarity
- `format` (string, optional): Image format (default: "png")
  - `"png"` — Lossless PNG (larger file, perfect quality)
  - `"jpg"` — JPEG compression (smaller file, lossy)

**Returns:**
- Object with screenshot result:
  - `success` (boolean): Screenshot captured and saved
  - `path` (string): Absolute path to saved file
  - `file_size` (number): Size of image file in bytes
  - `dimensions` (object): Image dimensions `{ width, height }` in pixels
  - `timestamp` (string): ISO 8601 timestamp of capture
  - `error` (string, optional): Error message

**Example:**
```javascript
// Capture to current directory
const result1 = await screenshot(adb, 'screen.png');
// { success: true, path: '/home/user/screen.png', file_size: 2048576, dimensions: { width: 1080, height: 2400 }, timestamp: '2026-04-10T14:32:15.000Z' }

// Capture with absolute path
const result2 = await screenshot(adb, '/tmp/eval_screenshots/step1.jpg', 'jpg');
// { success: true, path: '/tmp/eval_screenshots/step1.jpg', file_size: 524288, dimensions: { width: 1080, height: 2400 } }

// Multiple captures in sequence
const ui = await getUI(adb);
const step1 = await screenshot(adb, 'step1_loaded.png');
await tap(adb, { resource_id: 'com.shopapp:id/login_button' });
const step2 = await screenshot(adb, 'step2_login_screen.png');
```

**Error Handling:**
- Device offline: Returns `success: false`
- Directory doesn't exist: Returns `success: false`
- Write permission denied: Returns `success: false`
- Device storage full: Returns `success: false`

### teardown(adb)

Gracefully disconnects from the device and cleans up resources.

**Parameters:**
- `adb` (object): ADB connection object from `connect()`

**Returns:**
- Object with teardown result:
  - `success` (boolean): Disconnection successful
  - `device_id` (string): Device that was disconnected
  - `error` (string, optional): Error message

**Example:**
```javascript
const result = await teardown(adb);
// { success: true, device_id: 'emulator-5554' }
```

**Error Handling:**
- Device already disconnected: Returns `success: true` (idempotent)
- Kill app before disconnect (optional): Can terminate app with `am force-stop <package>`

## Complete Example Scenario

This example demonstrates a full mobile app eval workflow:

```javascript
// Step 1: Connect to device
const adb = await connect('emulator-5554');
console.log(`Connected to ${adb.model} (Android ${adb.android_version})`);

// Step 2: Launch app
const launched = await launch(adb, 'com.shopapp');
console.log(`App launched: ${launched.package_name}`);

// Step 3: Wait for UI to load
const initialUI = await getUI(adb);
console.log(`Found ${initialUI.elements.length} UI elements`);

// Step 4: Capture initial state
await screenshot(adb, 'step1_splash.png');

// Step 5: Find and tap sign-up button
const signupBtn = initialUI.elements.find(e => e.text === 'Sign Up');
if (signupBtn) {
  await tap(adb, { resource_id: signupBtn.resource_id });
  console.log('Tapped Sign Up button');
}

// Step 6: Wait for authentication screen
const authUI = await getUI(adb);
await screenshot(adb, 'step2_auth_screen.png');

// Step 7: Input phone number
await tap(adb, { resource_id: 'com.shopapp:id/phone_input' });
await type(adb, '+1234567890', true);
console.log('Entered phone number');

// Step 8: Capture after input
await screenshot(adb, 'step3_phone_input.png');

// Step 9: Find and tap Next button
const nextBtn = authUI.elements.find(e => e.text === 'Next');
if (nextBtn) {
  await tap(adb, { x: nextBtn.center.x, y: nextBtn.center.y });
  console.log('Tapped Next button');
}

// Step 10: Scroll down if needed
const scrollUI = await getUI(adb);
if (scrollUI.screen_height > 2000) {
  await swipe(adb, 
    { x: 540, y: 1500 }, 
    { x: 540, y: 500 },
    500
  );
  console.log('Scrolled up');
}

// Step 11: Capture final state
await screenshot(adb, 'step4_final_state.png');

// Step 12: Disconnect
const teardownResult = await teardown(adb);
console.log(`Disconnected: ${teardownResult.success}`);

console.log('Eval scenario completed successfully');
```

## Implementation Notes

### Connection Management

- **Multiple devices:** Run separate `connect()` calls with different device IDs in parallel
- **Emulator startup:** Ensure emulator is running before connect; use `emulator -avd <name>` or Android Studio
- **ADB paths:** Ensure `adb` is in PATH or use full path to ADB binary
- **Port forwarding:** For remote devices, use `adb connect <host>:<port>` after `adb forward` setup

### UIAutomator Limitations

- **Non-native UI:** Web content, Unity/Unreal games, or custom renderers may not be fully accessible
- **Animation delays:** Always wait after animations complete; use `wait_time` parameter
- **Overlays:** System dialogs, notifications may obscure targets; dismiss if needed
- **Performance:** Large hierarchies (1000+ elements) may slow UI dump; filter if possible

### Coordinate Precision

- **Density independence:** Coordinates are in screen pixels; multiply by density scale for dp
- **Multi-display:** Extended displays use offset coordinates; retrieve via `getUI()` for accuracy
- **Landscape/Portrait:** Coordinates swap with rotation; always verify after rotation

### Error Recovery

- **Flaky networks:** Retry with exponential backoff (100ms, 200ms, 400ms)
- **Device crashes:** Check `adb shell ps` for app process; restart if needed
- **Locked screen:** Unlock with `adb shell input keyevent 82` (MENU key) or pattern/PIN
- **Stale elements:** Re-fetch UI hierarchy if element references become invalid

## Usage Workflow

To use this skill in eval scenarios:

1. **Setup:** Call `connect()` with target device ID
2. **Launch:** Start app with `launch()` and wait for UI
3. **Interact:** Use `tap()`, `type()`, `swipe()` to simulate user actions
4. **Inspect:** Call `getUI()` to inspect current state and find elements
5. **Capture:** Use `screenshot()` to save state for documentation
6. **Verify:** Compare UI hierarchy and screenshots against expected outcomes
7. **Repeat:** Steps 3-6 for multi-step scenarios
8. **Cleanup:** Call `teardown()` to disconnect

## Edge Cases & Critical Scenarios

This section documents 6+ edge cases that frequently cause eval failures if not handled. Each case has detection method, impact, and recovery strategy.

### Edge Case 1: Application Not Responding (ANR) Dialog

**Trigger:** App blocks main thread for >5 seconds during operation (blocking I/O, heavy computation, missed frame deadlines).

**Detection:**
- UIAutomator hierarchy contains "ANR" or "Application Not Responding" dialog
- Elements match patterns: `resource_id` contains "android:id/button1" (Wait) and "android:id/button2" (Quit)
- Screen shows system modal with title containing "ANR" or "Not Responding"

**Code Example:**
```javascript
const ui = await getUI(adb);
const anrDialog = ui.elements.find(e => 
  e.class === 'android.widget.TextView' && 
  e.text?.includes('Not Responding')
);
if (anrDialog) {
  console.error('ANR dialog detected - app main thread blocked');
  // Find and tap "Wait" button to dismiss
  const waitBtn = ui.elements.find(e => e.resource_id?.includes('button1'));
  if (waitBtn) {
    await tap(adb, { x: waitBtn.center.x, y: waitBtn.center.y });
  }
}
```

**Impact:** Blocks all UI interaction until dismissed. Long-term ANRs cause app force-close by system.

**Recovery Strategy:**
1. Detect ANR dialog via `getUI()`
2. Tap "Wait" button to dismiss (resource_id typically `android:id/button1`)
3. If app remains unresponsive, call `am force-stop <package>` and restart
4. Root cause: Main thread is blocked; investigate app code for unoptimized operations

**Prevention:** Monitor response time during tap operations. If UI doesn't respond within 2 seconds, ANR is likely imminent.

### Edge Case 2: Device State Mismatch (App Backgrounded, Killed, Restarted)

**Trigger:** System kills app for memory pressure, user backgrounds app, or device rotates mid-operation.

**Detection:**
- `getUI()` returns home screen elements instead of app elements
- `launch()` shows app already running (`pid` matches, but UI unresponsive)
- Logcat shows `PROCESS KILLED` or `PROCESS_STATE_CACHED_EMPTY`

**Code Example:**
```javascript
// Check if app is in foreground
const ui = await getUI(adb);
const appElements = ui.elements.filter(e => e.resource_id?.startsWith('com.shopapp'));
if (appElements.length === 0) {
  console.warn('App backgrounded or killed - not in foreground');
  // Relaunch app
  const relaunched = await launch(adb, 'com.shopapp');
  if (relaunched.success) {
    await getUI(adb, 1000); // Wait for fresh launch
  }
}
```

**Impact:** UI interactions fail silently. Element references become stale. Navigation state lost.

**Recovery Strategy:**
1. Detect backgrounded app: UI hierarchy has no app-owned elements
2. Call `launch()` again (idempotent if already running, restarts if killed)
3. Wait for UI to stabilize (`getUI()` with 1000ms wait_time)
4. Re-query element locations before continuing

### Edge Case 3: Permission Denials (Camera, Location, Contacts)

**Trigger:** First time app requests dangerous permission (not granted in manifest or user denied).

**Detection:**
- Dialog appears with title "Allow [App] to access [Permission]?"
- Elements: "Allow" button (positive), "Deny" button (negative), permission description text
- System permission UI detected via accessibility dump

**Code Example:**
```javascript
const ui = await getUI(adb);
const permissionDialog = ui.elements.find(e => 
  e.text?.includes('Allow') && 
  e.class === 'android.widget.Button'
);
const denyBtn = ui.elements.find(e => 
  e.text === 'Deny' && 
  e.class === 'android.widget.Button'
);

if (permissionDialog && denyBtn) {
  console.log('Permission dialog detected');
  // Grant: tap Allow button
  await tap(adb, { x: permissionDialog.center.x, y: permissionDialog.center.y });
  // Or deny: await tap(adb, { x: denyBtn.center.x, y: denyBtn.center.y });
}
```

**Impact:** App crashes or shows error state if required permission denied. Optional features disabled if permission not granted.

**Recovery Strategy:**
1. Detect permission dialog in UI hierarchy
2. Grant permission by tapping "Allow" button
3. If permission required and user denies, app may crash (test both grant and deny flows)
4. Verify app behavior after permission grant/deny (error handling, graceful fallback)
5. For testing multiple permissions, grant all first, then test revocation separately

### Edge Case 4: Slow Device (High-Latency Responses, Slow UI Rendering)

**Trigger:** Device CPU throttled, RAM exhausted, storage fragmented, or heavy background load.

**Detection:**
- `getUI()` takes >2 seconds to return (XML parsing delay)
- UI updates not visible after `tap()` for >1 second
- Swipe animations visibly choppy, elements lag
- `adb shell getprop ro.kernel.qemu` returns "1" (emulator detected)

**Code Example:**
```javascript
const startTime = Date.now();
const ui = await getUI(adb);
const uiLatency = Date.now() - startTime;

if (uiLatency > 1500) {
  console.warn(`Slow device detected: UI fetch took ${uiLatency}ms`);
  // Increase wait times
  const slowUI = await getUI(adb, 2000); // 2s stabilization instead of 500ms
}
```

**Impact:** Tests fail due to timing assumptions. UI elements not clickable yet when targeted. Animations obscure state changes.

**Recovery Strategy:**
1. Detect latency via timing measurements
2. Increase `wait_time` parameter in `getUI()` (use 1000-2000ms instead of 500ms)
3. Add explicit delays after `tap()` before subsequent `getUI()`: `await new Promise(r => setTimeout(r, 500))`
4. Use longer swipe durations (1000ms+ instead of 500ms) to ensure gestures complete
5. Verify device load: `adb shell top` or `adb shell dumpsys meminfo`

### Edge Case 5: Network Connectivity Changes (WiFi → Cellular → Offline)

**Trigger:** Network switches mid-operation, WiFi drops, cellular signal lost, device airplane mode toggled.

**Detection:**
- Network requests time out or fail (captured in logcat)
- App shows "No internet" error dialog or banner
- Offline-first cache state diverges from server state
- `adb shell dumpsys connectivity` shows different network type

**Code Example:**
```javascript
// Simulate network change to test offline handling
const offline = await runCommand(adb, 'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true');
const ui = await getUI(adb, 1000);
const errorMsg = ui.elements.find(e => e.text?.includes('offline') || e.text?.includes('internet'));

if (errorMsg) {
  console.log('App correctly shows offline message');
  // Restore network
  await runCommand(adb, 'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false');
  const reconnectedUI = await getUI(adb, 2000);
  // Verify app auto-recovers or shows sync button
}
```

**Impact:** API calls fail, sync stalls, cached data may be inconsistent. App may crash or hang waiting for network.

**Recovery Strategy:**
1. Simulate network change via airplane mode toggle or `adb shell` commands
2. Verify app shows offline UI (error message, retry button, cached data indicator)
3. Restore network connectivity
4. Wait for app to auto-sync or provide explicit sync trigger
5. Verify data consistency after reconnection
6. Test both graceful offline handling (cache, retry) and failure cases (error dialog)

### Edge Case 6: UI Element Timing (Animation Delays, Lazy Rendering)

**Trigger:** UI elements not yet rendered when targeted, animations in progress, RecyclerView still loading items.

**Detection:**
- Element bounds report `{ x1: 0, y1: 0, x2: 0, y2: 0 }` (off-screen or not laid out)
- Element `clickable: false` even though should be interactive
- `getUI()` returns elements but subsequent `tap()` fails with "element not found"
- Scroll position changes unexpectedly (items loading dynamically)

**Code Example:**
```javascript
// Robust element targeting with retry
async function tapWithRetry(adb, target, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const result = await tap(adb, target);
    if (result.success) return result;
    
    if (i < maxRetries - 1) {
      console.warn(`Tap failed (attempt ${i + 1}), retrying...`);
      await new Promise(r => setTimeout(r, 300)); // Wait for animation
      // Re-fetch UI in case element moved
      const ui = await getUI(adb);
    }
  }
  throw new Error('Tap failed after retries');
}

// Usage: Wait for element to become clickable
const findElement = async (adb, predicate, maxWaits = 5) => {
  for (let i = 0; i < maxWaits; i++) {
    const ui = await getUI(adb);
    const element = ui.elements.find(e => predicate(e) && e.clickable && 
      e.bounds.x1 !== e.bounds.x2); // Has non-zero bounds
    if (element) return element;
    await new Promise(r => setTimeout(r, 200));
  }
  return null;
};

const btn = await findElement(adb, e => e.text === 'Submit');
if (btn) await tapWithRetry(adb, { x: btn.center.x, y: btn.center.y });
```

**Impact:** Element appears in hierarchy but can't be interacted with. Tests fail intermittently due to race conditions.

**Recovery Strategy:**
1. Verify element has non-zero bounds before tapping
2. Check `clickable: true` before interaction attempt
3. Wait for element to become clickable using retry loop with delays
4. Increase `wait_time` parameter in `getUI()` after navigation
5. For scrollable lists, scroll to element first, then tap
6. Use animation delay compensation: wait 300-500ms after `tap()` before next action

## Supported Platforms

- Android API 21+ (Android 5.0 Lollipop and newer)
- Both emulators and physical devices
- USB-connected devices and network-connected devices (TCP/IP)
- All standard Android UI frameworks (Android Framework, Jetpack Compose, etc.)

## Device Lifecycle Management

Understanding and testing app lifecycle transitions is critical for mobile eval. The Android app lifecycle has distinct states, and bugs often occur during transitions between states.

### App Foreground/Background State Management

The app can be in one of these states:
- **Foreground:** Visible to user, has keyboard/touch focus, running in full mode
- **Background:** User switched to another app, but process still alive (paused state)
- **Killed:** System terminated process due to memory pressure or explicit force-stop
- **Restarted:** Process brought back from killed state

**Testing foreground/background transitions:**

```javascript
// Test 1: App backgrounded by user
const ui1 = await getUI(adb);
const appElement1 = ui1.elements.filter(e => e.resource_id?.startsWith('com.shopapp'));
console.log(`Foreground elements: ${appElement1.length}`);

// Send app to background (press home key)
await runCommand(adb, 'adb shell input keyevent 3'); // HOME key
await new Promise(r => setTimeout(r, 500));

const ui2 = await getUI(adb);
const appElement2 = ui2.elements.filter(e => e.resource_id?.startsWith('com.shopapp'));
console.log(`Background elements: ${appElement2.length}`);

if (appElement2.length === 0) {
  console.log('App correctly backgrounded');
}

// Bring app back to foreground (press recent apps, select app)
await runCommand(adb, 'adb shell input keyevent 187'); // RECENT_APPS key
const ui3 = await getUI(adb);

// Verify app state is preserved or recreated correctly
```

**Testing memory kill scenarios:**

```javascript
// Kill app due to memory pressure
await runCommand(adb, 'adb shell am force-stop com.shopapp');
await new Promise(r => setTimeout(r, 500));

// Verify app process killed
const psResult = await runCommand(adb, 'adb shell ps | grep com.shopapp');
if (!psResult.stdout.includes('com.shopapp')) {
  console.log('App process successfully killed');
}

// Relaunch app (should restore saved state if using onSaveInstanceState)
const relaunched = await launch(adb, 'com.shopapp');
const ui = await getUI(adb, 1500);

// Verify app correctly restores state or shows fresh start
```

**Expected behaviors to test:**
- Data persisted to disk before backgrounding is restored
- In-memory state lost unless saved to Bundle via `onSaveInstanceState()`
- Resuming foreground should call `onResume()` lifecycle method
- Fragments/screens maintain navigation stack across background/foreground

### Permission Grant/Deny Flows

Android runtime permissions (API 23+) are granted at runtime, not install time. Testing both grant and deny paths is essential.

**Permission dialog detection and handling:**

```javascript
// Request permission (app initiates)
await tap(adb, { resource_id: 'com.shopapp:id/request_camera_button' });
await new Promise(r => setTimeout(r, 500)); // Wait for dialog to appear

const ui = await getUI(adb);
const allowBtn = ui.elements.find(e => 
  e.text === 'Allow' && 
  e.resource_id?.includes('permission_allow')
);
const denyBtn = ui.elements.find(e => 
  e.text === 'Deny' && 
  e.resource_id?.includes('permission_deny')
);

console.log(`Permission dialog visible: Allow=${!!allowBtn}, Deny=${!!denyBtn}`);

// Test grant path
if (allowBtn) {
  await tap(adb, { x: allowBtn.center.x, y: allowBtn.center.y });
  const uiAfterGrant = await getUI(adb, 1000);
  // Verify app enables camera feature
}

// Test deny path (would need to restart or simulate)
// Verify app shows error message or disables feature
```

**Testing multiple permission requests:**

```javascript
// Grant multiple permissions in sequence
const permissions = ['camera', 'location', 'contacts'];
for (const perm of permissions) {
  await tap(adb, { resource_id: `com.shopapp:id/request_${perm}_button` });
  await new Promise(r => setTimeout(r, 500));
  
  const ui = await getUI(adb);
  const allowBtn = ui.elements.find(e => e.text === 'Allow');
  if (allowBtn) {
    await tap(adb, { x: allowBtn.center.x, y: allowBtn.center.y });
  }
  await new Promise(r => setTimeout(r, 500));
}

// Verify all permissions active
```

**Testing revocation:**

```javascript
// Revoke permission via adb shell
await runCommand(adb, 'adb shell pm revoke com.shopapp android.permission.CAMERA');
await new Promise(r => setTimeout(r, 500));

// Verify app gracefully handles missing permission
const ui = await getUI(adb);
const errorMsg = ui.elements.find(e => e.text?.includes('camera') && e.text?.includes('not'));
if (errorMsg) {
  console.log('App correctly shows permission error');
}
```

### Navigation Back Button Behavior

The back button (BACK keyevent 4) is critical to Android UX. Apps should handle it correctly at each screen.

**Testing back navigation:**

```javascript
// Navigate through app
await tap(adb, { resource_id: 'com.shopapp:id/navigation_item_products' });
const ui1 = await getUI(adb);

await tap(adb, { resource_id: 'com.shopapp:id/product_card_1' });
const ui2 = await getUI(adb);

// Press back key
await runCommand(adb, 'adb shell input keyevent 4'); // BACK key
await new Promise(r => setTimeout(r, 300));

const ui3 = await getUI(adb);
// Should return to products list

// Press back again
await runCommand(adb, 'adb shell input keyevent 4');
await new Promise(r => setTimeout(r, 300));

const ui4 = await getUI(adb);
// Should return to initial screen

// Press back at home (should exit app)
await runCommand(adb, 'adb shell input keyevent 4');
await new Promise(r => setTimeout(r, 500));

const uiFinal = await getUI(adb);
const appElements = uiFinal.elements.filter(e => e.resource_id?.startsWith('com.shopapp'));
if (appElements.length === 0) {
  console.log('App correctly exited on back from home');
}
```

**Testing back with dialogs:**

```javascript
// Open dialog
await tap(adb, { resource_id: 'com.shopapp:id/show_settings_button' });
const uiDialog = await getUI(adb);
const dialog = uiDialog.elements.find(e => e.class === 'android.widget.FrameLayout' && e.children > 0);

// Press back key
await runCommand(adb, 'adb shell input keyevent 4');
await new Promise(r => setTimeout(r, 300));

const uiAfter = await getUI(adb);
const dialogGone = !uiAfter.elements.find(e => e === dialog);
if (dialogGone) {
  console.log('Dialog correctly dismissed on back');
}
```

### Memory Pressure Scenarios

Testing app behavior under memory constraints reveals data loss and crash vulnerabilities.

**Simulating memory pressure:**

```javascript
// Get initial memory state
const memBefore = await runCommand(adb, 'adb shell dumpsys meminfo com.shopapp');

// Fill memory with junk data
await runCommand(adb, 'adb shell pm trim-memory 100'); // Force trim level CRITICAL

// Verify app doesn't crash
const ui = await getUI(adb, 1000);
const isAlive = ui.elements.filter(e => e.resource_id?.startsWith('com.shopapp')).length > 0;

if (isAlive) {
  console.log('App survived memory pressure');
} else {
  console.log('App killed by memory pressure - may need optimization');
}

// Verify user data not lost (if saved to disk)
const savedData = ui.elements.find(e => e.text?.includes('previous_state'));
if (savedData) {
  console.log('Data correctly persisted across memory pressure');
}
```

## Out of Scope (Future Phases)

- iOS automation (separate eval-driver-ios-xctest skill planned)
- WebDriver protocol integration
- Performance profiling and metrics collection
- Parallel multi-app evaluation
- Advanced gesture recognition (pinch, rotate)
- Screen recording and video playback
- Custom UIAutomator instrumentation code
- Integration with APK installation/management

## UIAutomator Detailed Guidance

UIAutomator is Android's native accessibility automation framework. Mastering element selection, dialog handling, gestures, and waiting strategies is essential for robust evals.

### Selecting Elements by Resource ID

Resource IDs are the most reliable way to select elements. They remain stable across screen rotations and layout changes.

**Resource ID format:** `package_name:id/element_name` (e.g., `com.shopapp:id/login_button`)

**Finding resource IDs in UI hierarchy:**

```javascript
const ui = await getUI(adb);

// Find button by exact resource ID
const loginBtn = ui.elements.find(e => e.resource_id === 'com.shopapp:id/login_button');
if (loginBtn) {
  console.log(`Found login button at ${loginBtn.center.x}, ${loginBtn.center.y}`);
  await tap(adb, { resource_id: 'com.shopapp:id/login_button' });
}

// Find elements by partial resource ID match (useful when exact ID unknown)
const emailField = ui.elements.find(e => e.resource_id?.includes('email'));

// Find all buttons (by resource ID prefix)
const allButtons = ui.elements.filter(e => 
  e.resource_id?.startsWith('com.shopapp:id/') && 
  e.class === 'android.widget.Button'
);
```

**Best practices:**
- Always prefer resource ID over text or coordinates
- Resource IDs are developer-controlled and stable
- Text content changes with localization; resource IDs don't
- Coordinates break when layout changes

### Selecting Elements by Text

Text matching is useful for buttons, labels, and user-facing strings. However, text is fragile across localization.

**Exact text matching:**

```javascript
const ui = await getUI(adb);

// Find button with exact text "Sign Up"
const signupBtn = ui.elements.find(e => e.text === 'Sign Up');
if (signupBtn) {
  await tap(adb, { x: signupBtn.center.x, y: signupBtn.center.y });
}

// Find input field with label text
const emailLabel = ui.elements.find(e => 
  e.text === 'Email Address' && 
  e.class === 'android.widget.TextView'
);
```

**Partial text matching:**

```javascript
// Find elements containing substring (case-sensitive)
const errorMsg = ui.elements.find(e => e.text?.includes('Invalid'));

// Case-insensitive match
const btn = ui.elements.find(e => e.text?.toLowerCase().includes('submit'));

// Text with whitespace normalization (remove extra spaces)
const label = ui.elements.find(e => 
  e.text?.trim().replace(/\s+/g, ' ') === 'First Name'
);
```

**Cautions:**
- Text changes with app localization/language
- Text may be dynamically generated (timestamps, user data)
- Whitespace normalization needed (newlines, extra spaces)
- Text matching fails if content rendered via WebView or custom renderers

### Selecting Elements by Class

Class matching finds elements by Android widget type. Useful for finding all buttons, TextViews, EditTexts, etc.

**Common Android classes:**
- `android.widget.Button` — Standard button
- `android.widget.EditText` — Text input field
- `android.widget.TextView` — Text label (read-only)
- `android.widget.ImageView` — Image/icon
- `android.widget.ProgressBar` — Loading indicator
- `android.view.ViewGroup` — Container (LinearLayout, FrameLayout, etc.)
- `android.widget.CheckBox`, `android.widget.RadioButton` — Selection controls
- `android.widget.Spinner` — Dropdown selector
- `android.widget.ScrollView` — Scrollable container

**Class-based selection:**

```javascript
const ui = await getUI(adb);

// Find first button
const firstBtn = ui.elements.find(e => e.class === 'android.widget.Button');

// Find all clickable text elements
const clickableLabels = ui.elements.filter(e => 
  e.class === 'android.widget.TextView' && 
  e.clickable
);

// Find input fields (EditText)
const inputFields = ui.elements.filter(e => 
  e.class === 'android.widget.EditText'
);

// Complex selector: find enabled button with non-empty text
const submitBtn = ui.elements.find(e => 
  e.class === 'android.widget.Button' && 
  e.enabled && 
  e.text && 
  e.text.length > 0
);
```

**Combined selectors (resource ID + class):**

```javascript
// Most reliable: combine resource ID and class to avoid matches in WebViews
const loginBtn = ui.elements.find(e => 
  e.resource_id === 'com.shopapp:id/login_button' && 
  e.class === 'android.widget.Button'
);
```

### Handling Dialogs and System Popups

Dialogs are overlays that block interaction with underlying content. System popups (permission dialogs, alerts) must be handled explicitly.

**Dialog detection:**

```javascript
const ui = await getUI(adb);

// Find dialog by looking for modal containers
const dialog = ui.elements.find(e => 
  e.class === 'android.widget.FrameLayout' && // Dialog typically in FrameLayout
  e.children > 0 &&
  e.bounds.y1 > 100 // Not at top of screen (indicating not status bar)
);

// Check for common dialog button patterns
const positiveBtn = ui.elements.find(e => 
  (e.text === 'OK' || e.text === 'Yes' || e.text === 'Allow') &&
  e.class === 'android.widget.Button'
);
const negativeBtn = ui.elements.find(e => 
  (e.text === 'Cancel' || e.text === 'No' || e.text === 'Deny') &&
  e.class === 'android.widget.Button'
);

if (positiveBtn && negativeBtn) {
  console.log('Dialog detected with positive and negative buttons');
}
```

**Dismissing dialogs:**

```javascript
// Method 1: Tap positive button (OK, Allow, Yes)
const okBtn = ui.elements.find(e => e.text === 'OK');
if (okBtn) {
  await tap(adb, { x: okBtn.center.x, y: okBtn.center.y });
  await getUI(adb, 500); // Verify dialog gone
}

// Method 2: Tap negative button (Cancel, Deny, No)
const cancelBtn = ui.elements.find(e => e.text === 'Cancel');
if (cancelBtn) {
  await tap(adb, { x: cancelBtn.center.x, y: cancelBtn.center.y });
}

// Method 3: Press back key (works for most dialogs)
await runCommand(adb, 'adb shell input keyevent 4'); // BACK key
await new Promise(r => setTimeout(r, 300));
const uiAfter = await getUI(adb);

// Verify dialog is gone
if (!uiAfter.elements.find(e => e.text === 'OK')) {
  console.log('Dialog dismissed');
}
```

**System permission dialogs:**

```javascript
// Permission dialogs have consistent button layout
const permissionDialog = ui.elements.find(e => 
  e.text?.includes('Allow') && e.text?.includes('Deny')
);

if (permissionDialog) {
  console.log('Permission dialog detected');
  
  // Grant: tap Allow button (usually on right)
  const allowBtn = ui.elements.find(e => 
    e.text === 'Allow' &&
    e.resource_id?.includes('permission') ||
    e.resource_id?.includes('allow')
  );
  
  if (allowBtn) {
    await tap(adb, { x: allowBtn.center.x, y: allowBtn.center.y });
    await new Promise(r => setTimeout(r, 500)); // Permissions take time to apply
  }
}
```

### Scrolling and Gesture Commands

Scrolling is essential for accessing off-screen elements in long lists.

**Vertical scrolling (up and down):**

```javascript
// Scroll down (swipe up)
// Start near bottom of screen, drag upward to reveal more content below
await swipe(adb, 
  { x: 540, y: 1800 },  // Start: lower on screen
  { x: 540, y: 400 },   // End: upper on screen
  500                     // Duration: 500ms
);
await new Promise(r => setTimeout(r, 300)); // Wait for scroll to complete

// Scroll up (swipe down)
// Start near top, drag downward to scroll back up
await swipe(adb,
  { x: 540, y: 400 },   // Start: upper on screen
  { x: 540, y: 1800 },  // End: lower on screen
  500
);
```

**Horizontal scrolling (tabs, pagination):**

```javascript
// Scroll right (swipe left)
await swipe(adb,
  { x: 800, y: 900 },   // Start: right side
  { x: 100, y: 900 },   // End: left side
  400                     // Quick swipe
);

// Scroll left (swipe right)
await swipe(adb,
  { x: 100, y: 900 },
  { x: 800, y: 900 },
  400
);
```

**Finding elements via scroll:**

```javascript
// Scroll until element appears
async function scrollToElement(adb, predicate, maxScrolls = 5) {
  for (let i = 0; i < maxScrolls; i++) {
    const ui = await getUI(adb);
    const element = ui.elements.find(predicate);
    if (element && element.bounds.y1 > 0 && element.bounds.y2 < ui.screen_height) {
      return element; // Element visible on screen
    }
    
    // Scroll down
    await swipe(adb,
      { x: ui.screen_width / 2, y: ui.screen_height - 200 },
      { x: ui.screen_width / 2, y: 200 },
      500
    );
  }
  return null;
}

const targetBtn = await scrollToElement(adb, e => e.text === 'View All Orders');
if (targetBtn) {
  await tap(adb, { x: targetBtn.center.x, y: targetBtn.center.y });
}
```

**Long-press gestures:**

```javascript
// Long-press to trigger context menu or selection
await tap(adb, 
  { resource_id: 'com.shopapp:id/product_item_1' },
  1500  // 1500ms = long-press duration
);

const ui = await getUI(adb);
// Check for context menu (typically appears at tap location)
const contextMenu = ui.elements.find(e => 
  e.class?.includes('Menu') || e.text?.includes('Share')
);
```

### Waiting for UI Stability

UI changes are async. Elements don't appear instantly; animations complete over time. Use wait strategies to avoid race conditions.

**Explicit waits with timeout:**

```javascript
async function waitForElement(adb, predicate, timeoutMs = 5000, pollIntervalMs = 200) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const ui = await getUI(adb, 100);
    const element = ui.elements.find(predicate);
    if (element && element.bounds.x1 !== element.bounds.x2) {
      return element; // Found and has non-zero bounds
    }
    await new Promise(r => setTimeout(r, pollIntervalMs));
  }
  return null; // Timeout
}

// Usage: Wait for "Next" button to appear after tap
await tap(adb, { resource_id: 'com.shopapp:id/start_button' });
const nextBtn = await waitForElement(adb, 
  e => e.text === 'Next' && e.enabled,
  3000  // 3 second timeout
);
if (nextBtn) {
  await tap(adb, { x: nextBtn.center.x, y: nextBtn.center.y });
}
```

**Waiting after animations:**

```javascript
// After tap, wait for animation to complete before next action
const animationDelay = 300; // Standard Android animation duration
await new Promise(r => setTimeout(r, animationDelay));

// Get fresh UI after animation
const ui = await getUI(adb);
```

**Stability polling (wait for UI to stop changing):**

```javascript
// Wait for UI hierarchy to stabilize (element counts stop changing)
async function waitForStability(adb, stableMs = 500) {
  let lastCount = 0;
  let stableCount = 0;
  const maxAttempts = 20;
  
  for (let i = 0; i < maxAttempts; i++) {
    const ui = await getUI(adb);
    if (ui.elements.length === lastCount) {
      stableCount++;
      if (stableCount >= stableMs / 100) return ui; // Stable for stableMs
    } else {
      stableCount = 0;
    }
    lastCount = ui.elements.length;
    await new Promise(r => setTimeout(r, 100));
  }
  return null;
}

const stableUI = await waitForStability(adb);
```

## ANR Recovery & Detection

Application Not Responding (ANR) dialogs are critical failure modes in mobile eval. They indicate the main thread is blocked, which is a code defect. Detecting and recovering from ANRs is essential.

### Detecting ANR Dialogs

ANR dialogs appear as system modal dialogs with specific characteristics. Detection involves both UI hierarchy inspection and visual/text cues.

**Visual characteristics:**

```javascript
// ANR dialog detection via UI hierarchy
async function detectANR(adb) {
  const ui = await getUI(adb);
  
  // Method 1: Look for "ANR" text in hierarchy
  const anrTextElement = ui.elements.find(e =>
    e.text?.includes('Application') && 
    e.text?.includes('Responding')
  );
  if (anrTextElement) {
    console.error('ANR detected: app not responding');
    return true;
  }
  
  // Method 2: Look for typical ANR dialog buttons
  // ANR dialogs typically have "Wait" and "Close App" buttons
  const hasWaitBtn = ui.elements.some(e => 
    e.text === 'Wait' && 
    e.class === 'android.widget.Button'
  );
  const hasCloseBtn = ui.elements.some(e => 
    (e.text === 'Close' || e.text === 'OK') && 
    e.class === 'android.widget.Button'
  );
  
  if (hasWaitBtn && hasCloseBtn) {
    console.error('ANR dialog detected: Wait/Close buttons present');
    return true;
  }
  
  // Method 3: Look for system dialog with "not responding" in any text
  const dialogWithError = ui.elements.find(e =>
    e.text?.toLowerCase().includes('not responding') ||
    e.text?.toLowerCase().includes('responding')
  );
  if (dialogWithError) {
    console.error('ANR dialog found via error text');
    return true;
  }
  
  return false;
}
```

**Root causes of ANRs:**

ANRs indicate these code problems:
- **Main thread I/O:** Network requests, database queries, file operations on main thread
- **Long computations:** Heavy calculations blocking UI thread (>5 seconds)
- **Expensive layouts:** Complex view hierarchies taking >16ms to render (skips frame deadline)
- **Deadlocks:** Threads waiting on locks held by main thread
- **Infinite loops:** Main thread stuck in busy loop
- **Unresponsive services:** Service taking >10 seconds to start or process

### ANR Recovery Strategy

Once an ANR is detected, the recovery process depends on test goals: continue past ANR, or abort and report.

**Recovery: Dismiss and Continue**

```javascript
// Dismiss ANR dialog by tapping "Wait" button
async function recoverFromANR(adb) {
  const ui = await getUI(adb);
  
  // Find "Wait" button (keeps app running)
  const waitBtn = ui.elements.find(e => 
    e.text === 'Wait' && 
    e.class === 'android.widget.Button'
  );
  
  if (waitBtn) {
    console.log('Tapping Wait button to dismiss ANR');
    await tap(adb, { 
      x: waitBtn.center.x, 
      y: waitBtn.center.y 
    });
    
    // Wait for ANR dialog to dismiss
    await new Promise(r => setTimeout(r, 500));
    
    // Verify dialog gone
    const uiAfter = await getUI(adb);
    const anrStillPresent = uiAfter.elements.find(e => 
      e.text?.includes('Responding')
    );
    
    if (!anrStillPresent) {
      console.log('ANR dialog dismissed, app responsive');
      return true;
    }
  }
  
  return false;
}

// Usage
if (await detectANR(adb)) {
  if (await recoverFromANR(adb)) {
    console.log('Continuing eval after ANR recovery');
    // Continue with eval steps
  } else {
    console.error('ANR persists, aborting eval');
    // Abort eval, report ANR
  }
}
```

**Recovery: Force-Stop and Restart**

```javascript
async function forceStopAndRestart(adb, packageName) {
  console.log(`Force-stopping ${packageName} due to ANR`);
  
  // Kill the app process
  await runCommand(adb, `adb shell am force-stop ${packageName}`);
  await new Promise(r => setTimeout(r, 500));
  
  // Clear app cache (optional, helps with stale state)
  // await runCommand(adb, `adb shell pm clear ${packageName}`);
  
  // Relaunch app
  const result = await launch(adb, packageName);
  if (result.success) {
    console.log('App restarted after ANR');
    const ui = await getUI(adb, 1500); // Wait for fresh launch
    return true;
  }
  
  return false;
}
```

**Detecting persistent ANRs:**

```javascript
async function checkForPersistentANR(adb, maxAttempts = 3) {
  const anrHistory = [];
  
  for (let i = 0; i < maxAttempts; i++) {
    if (await detectANR(adb)) {
      anrHistory.push(true);
      console.warn(`ANR detected (attempt ${i + 1}/${maxAttempts})`);
      
      if (!(await recoverFromANR(adb))) {
        console.error('Failed to recover from ANR');
        return false;
      }
      
      // Wait between attempts
      await new Promise(r => setTimeout(r, 1000));
    } else {
      anrHistory.push(false);
      break;
    }
  }
  
  // If ANR occurred in last 2 consecutive checks, it's persistent
  if (anrHistory.slice(-2).every(x => x === true)) {
    console.error('Persistent ANR detected - app fundamentally unresponsive');
    return false;
  }
  
  return true;
}
```

### Root Cause Investigation

After detecting an ANR, investigate via logcat to find the actual blocking operation.

**Logcat investigation:**

```javascript
// Fetch ANR trace from logcat after ANR occurs
async function investigateANR(adb) {
  // Get recent logcat (last 200 lines)
  const logcat = await runCommand(adb, 'adb logcat -d *:S AndroidRuntime:E -n 200');
  
  // Look for "ANR in" message with package name
  const anrLine = logcat.stdout.split('\n').find(line => 
    line.includes('ANR in') || line.includes('Application Not Responding')
  );
  
  if (anrLine) {
    console.error(`ANR info: ${anrLine}`);
    // Parse to find package and activity
    // Example: "ANR in com.shopapp (.MainActivity)"
  }
  
  // Look for main thread state ("WAITING on..." indicates lock contention)
  const mainThreadLines = logcat.stdout.split('\n').filter(line =>
    line.includes('main') && (
      line.includes('WAITING') ||
      line.includes('BLOCKED') ||
      line.includes('at ')
    )
  );
  
  console.error('Main thread state during ANR:');
  mainThreadLines.slice(0, 10).forEach(line => console.error(line));
  
  // Common blocking patterns
  if (logcat.stdout.includes('HttpURLConnection') || logcat.stdout.includes('okhttp')) {
    console.error('Root cause: Network request on main thread');
  }
  if (logcat.stdout.includes('SQLiteDatabase')) {
    console.error('Root cause: Database query on main thread');
  }
  if (logcat.stdout.includes('File')) {
    console.error('Root cause: File I/O on main thread');
  }
}
```

### Prevention: Monitoring Response Times

Proactively monitor for ANR precursors by tracking UI response latency.

**Response time monitoring:**

```javascript
// Tap with latency measurement to detect ANR risk
async function tapWithLatencyCheck(adb, target, maxLatencyMs = 2000) {
  console.log(`Tapping with max latency threshold: ${maxLatencyMs}ms`);
  
  const startTime = Date.now();
  const tapResult = await tap(adb, target);
  const tapLatency = Date.now() - startTime;
  
  console.log(`Tap latency: ${tapLatency}ms`);
  
  if (tapLatency > maxLatencyMs) {
    console.warn(`Tap slow (${tapLatency}ms > ${maxLatencyMs}ms) - ANR imminent?`);
    
    // Check for ANR before continuing
    const ui = await getUI(adb);
    if (await detectANR(adb)) {
      console.error('ANR dialog appeared after slow tap');
      return false;
    }
  }
  
  return tapResult.success;
}

// Usage in eval scenario
for (const action of evalSteps) {
  if (action.type === 'tap') {
    if (!await tapWithLatencyCheck(adb, action.target, 2000)) {
      console.error('Tap operation failed or ANR detected');
      break;
    }
  }
}
```

**UI fetch latency as ANR indicator:**

```javascript
// Monitor getUI latency - high latency indicates ANR risk
async function monitorUILatency(adb, thresholdMs = 1500) {
  const startTime = Date.now();
  const ui = await getUI(adb);
  const latency = Date.now() - startTime;
  
  if (latency > thresholdMs) {
    console.warn(`UI fetch slow: ${latency}ms (threshold: ${thresholdMs}ms)`);
    
    // High latency + specific elements = ANR risk
    const anrDialog = ui.elements.find(e => e.text?.includes('Responding'));
    if (anrDialog) {
      console.error('ANR dialog already present with slow UI fetch');
      return false;
    }
  }
  
  return true;
}
```

## Error Handling Reference

All functions follow consistent error handling patterns:

```javascript
// Always check success flag
if (!result.success) {
  console.error(`Operation failed: ${result.error}`);
  // Handle error: retry, skip step, abort scenario, etc.
}

// Success cases contain operation-specific data
if (result.success && result.element) {
  console.log(`Found element at ${result.element.bounds}`);
}

// Errors include context for debugging
if (ui.success) {
  const clickableCount = ui.elements.filter(e => e.clickable).length;
  console.log(`${clickableCount} clickable elements on screen`);
} else {
  console.error(`UI dump failed: ${ui.error}`);
}
```

## Checklist

Before running an Android ADB eval scenario:

- [ ] Device/emulator readiness verified (not just ADB connected — fully booted)
- [ ] App state cleared from prior scenario (terminate + clear data)
- [ ] All assertions target specific resource IDs, content descriptions, or exact text
- [ ] ANR dialogs monitored and logged (not silently dismissed)
- [ ] `screenshot()` called and file path recorded in scenario output
- [ ] `disconnect()` called in all paths (success, failure, timeout)
