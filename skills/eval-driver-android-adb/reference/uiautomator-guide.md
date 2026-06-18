# UIAutomator guide & error handling — reference for `eval-driver-android-adb`

> Progressive-disclosure Level 3 (loaded on demand). Element selection (resource id / text / class), dialog & system-popup handling, scrolling/gestures, ANR recovery & detection, and the error-handling reference.

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

