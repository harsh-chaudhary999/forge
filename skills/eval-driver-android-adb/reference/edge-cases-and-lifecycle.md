# Edge cases & device lifecycle — reference for `eval-driver-android-adb`

> Progressive-disclosure Level 3 (loaded on demand). Full detection/recovery code for the 6 edge cases, supported platforms, and device-lifecycle tests. SKILL.md carries the summary table.

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

