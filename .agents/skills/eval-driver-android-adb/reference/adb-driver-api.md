# ADB driver API — reference for `eval-driver-android-adb`

> Progressive-disclosure Level 3 (loaded on demand). Architecture, the full driver API, a complete example, implementation notes, and the usage workflow. SKILL.md is the operational contract; this is the catalog.

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

