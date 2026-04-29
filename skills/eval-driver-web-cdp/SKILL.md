---
name: eval-driver-web-cdp
description: "WHEN: Eval scenario requires web UI interaction or assertion. Automates browser via Chrome DevTools Protocol. Functions: launch(), navigate(), interact(click/type/scroll), screenshot(), getDOM(), teardown()."
type: rigid
requires: [brain-read, eval-scenario-format]
version: 1.0.0
preamble-tier: 3
triggers:
  - "eval web UI"
  - "run browser eval"
  - "CDP eval driver"
  - "web UI eval"
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Eval Driver: Web UI via Chrome DevTools Protocol (CDP)

Automates browser interactions and state inspection using Chrome DevTools Protocol. Provides a programmatic interface for launching headless Chrome, navigating URLs, interacting with UI elements, capturing screenshots, and extracting DOM state.

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

## Host implementation choice (CDP, Playwright, Puppeteer, MCP)

**MUST ask the human** how web UI eval should run **before** treating any stack as decided:

1. **Raw CDP** — WebSocket client / `chrome-remote-interface` / minimal driver (matches the API shape in this skill).
2. **Playwright or Puppeteer** — running on the **operator’s machine or CI** against the **product** browser (allowed for **product eval**; D5 still forbids **LangChain-style** orchestration **inside Forge’s shipped plugin code**).
3. **Browser MCP** — IDE or host exposes MCP tools (navigate, snapshot, click). When available, the operator may prefer MCP over a custom CDP script. **Confirm** tool names, auth, timeouts, and what artifacts **`eval-judge`** needs.

If **both** MCP and a local CDP path exist, **do not assume** — **ask which to use** and record the choice (e.g. in `brain/prds/<task-id>/` notes) so runs are reproducible.

## Overview

This skill enables eval scripts to drive web UI automation through CDP, supporting:
- Headless Chrome browser lifecycle management
- URL navigation with load state verification
- User interaction simulation (click, type, scroll)
- Page screenshots for visual validation
- DOM state extraction for assertion verification
- Graceful browser teardown

## Core Functions

### launch()

**Signature:**
```javascript
async launch() → Promise<Browser>
```

**Description:**
Launches Chrome in headless mode and establishes CDP connection. Initializes browser instance for subsequent operations.

**Behavior:**
- Launches Chrome with `--headless` flag
- Disables sandbox for CI/container environments: `--no-sandbox`
- Sets window size for consistent screenshots: `1920x1080`
- Establishes Chrome DevTools Protocol connection
- Returns Browser instance with active WebSocket connection

**Options:**
```javascript
{
  headless: true,
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--window-size=1920,1080'
  ],
  defaultViewport: {
    width: 1920,
    height: 1080
  }
}
```

**Error Handling:**
- Throws if Chrome binary not found
- Throws if CDP connection fails
- Timeout: 30 seconds for browser launch

**Returns:**
```javascript
{
  // CDP protocol interface
  // Supports: Page, DOM, Input, Runtime, Network, etc. domains
}
```

**Example:**
```javascript
const browser = await launch()
// Browser ready for navigation
```

---

### navigate(browser, url)

**Signature:**
```javascript
async navigate(browser: Browser, url: string) → Promise<{
  loaded: boolean,
  title: string,
  url: string,
  statusCode: number
}>
```

**Description:**
Navigates to a URL and waits for page load completion. Blocks until DOM ready or timeout.

**Behavior:**
- Sends Page.navigate CDP command
- Waits for Page.loadEventFired event
- Waits for Network idle state (2 seconds no network requests)
- Captures page title from DOM
- Verifies HTTP status code via Network.requestWillBeSent

**Load Conditions:**
1. DOM Content Loaded event fires
2. All deferred/async scripts complete
3. Network idle threshold (2s) reached
4. OR timeout (10 seconds)

**Error Handling:**
- Returns `{loaded: false}` if page load timeout
- Rejects if URL invalid or protocol mismatch
- Logs network errors but continues
- Status code 0 for navigation abort
- Timeout: 10 seconds

**Returns:**
```javascript
{
  loaded: true|false,        // True if all load conditions met
  title: string,             // Document title
  url: string,               // Final URL (post-redirects)
  statusCode: number         // HTTP status (200, 404, etc.)
}
```

**Example:**
```javascript
const nav = await navigate(browser, 'http://localhost:3001/login')
if (!nav.loaded) {
  throw new Error(`Page failed to load: ${nav.statusCode}`)
}
console.log(`Loaded: ${nav.title}`)
```

---

### interact(browser, action, selector, value?)

**Signature:**
```javascript
async interact(
  browser: Browser,
  action: 'click'|'type'|'scroll',
  selector: string,
  value?: string
) → Promise<{
  success: boolean,
  message: string,
  elementFound: boolean,
  elementVisible: boolean
}>
```

**Description:**
Performs user interactions: click elements, type text, scroll page. Actions wait for element visibility before execution.

**Actions:**

#### click
- Locates element via CSS selector
- Waits for element visibility (max 5s)
- Scrolls element into viewport
- Dispatches click event via Input.dispatchMouseEvent
- Verifies element still visible after click

#### type
- Locates element via CSS selector
- Waits for visibility and focus-ability
- Focuses element via Input.setIgnoreInputImeFlag
- Types text character by character with 50ms delay
- Dispatch: Input.dispatchKeyEvent (keyDown, keyPress, keyUp)

#### scroll
- Scrolls page by distance specified in `value` (pixels)
- Positive: down, Negative: up
- Uses Runtime.evaluate to set window.scrollY
- Waits 500ms for DOM settle after scroll

**Element Selection:**
- CSS selector syntax (e.g., `input[name=email]`, `.btn-submit`, `#modal > button`)
- XPath also supported via DOM.querySelector fallback
- Waits max 5 seconds for element to appear

**Visibility Check:**
- Element must be in DOM
- Element must have non-zero offsetHeight/offsetWidth
- Element must not be `display: none` or `visibility: hidden`
- Parent chain must be visible

**Error Handling:**
- Returns `{success: false, elementFound: false}` if selector doesn't match
- Returns `{success: false, elementVisible: false}` if not visible after timeout
- Logs action attempt and result
- Timeout per action: 5 seconds for element find

**Returns:**
```javascript
{
  success: boolean,          // Action completed without error
  message: string,           // Descriptive status (e.g., "Clicked successfully")
  elementFound: boolean,     // Selector matched at least one element
  elementVisible: boolean    // Element was visible when action attempted
}
```

**Examples:**
```javascript
// Click submit button
await interact(browser, 'click', 'button[type=submit]')

// Type email
await interact(browser, 'type', 'input[name=email]', 'user@example.com')

// Scroll down 500px
await interact(browser, 'scroll', null, '500')
```

---

### screenshot(browser, filename)

**Signature:**
```javascript
async screenshot(
  browser: Browser,
  filename: string
) → Promise<{
  path: string,
  size: number,
  format: 'png'|'jpeg',
  width: number,
  height: number
}>
```

**Description:**
Captures current page state as image file. Supports PNG (default) and JPEG formats.

**Behavior:**
- Captures page viewport via Page.captureScreenshot
- Saves to `screenshots/` directory (auto-created)
- Filename used as-is (should include extension)
- Includes DOM content, CSS, and rendered state
- Does NOT include system UI or browser chrome

**Format Detection:**
- `.jpg`, `.jpeg` → JPEG (quality: 80%)
- `.png` → PNG (lossless)
- Default: PNG

**Path Resolution:**
- Screenshots stored in process working directory + `screenshots/`
- Full path returned for verification/upload

**Error Handling:**
- Creates `screenshots/` directory if missing
- Throws if filename invalid or path traversal attempted
- Throws if write permission denied
- Logs file size and dimensions

**Returns:**
```javascript
{
  path: string,              // Absolute path to saved file
  size: number,              // File size in bytes
  format: 'png'|'jpeg',      // Image format used
  width: number,             // Screenshot width in pixels
  height: number             // Screenshot height in pixels
}
```

**Example:**
```javascript
const shot = await screenshot(browser, 'login-form.png')
console.log(`Screenshot saved: ${shot.path} (${shot.size} bytes)`)
```

---

### getDOM(browser, selector)

**Signature:**
```javascript
async getDOM(
  browser: Browser,
  selector: string
) → Promise<{
  elements: Array<{
    tag: string,
    id: string,
    classList: string[],
    text: string,
    html: string,
    attributes: Record<string, string>,
    visible: boolean,
    rect: {x: number, y: number, width: number, height: number}
  }>,
  count: number,
  error: string|null
}>
```

**Description:**
Extracts DOM state for matching elements. Returns element properties, text content, attributes, and visibility. Useful for assertions and state validation.

**Behavior:**
- Executes Runtime.evaluate to run selector query in page context
- For each matched element:
  - Extracts tag name, ID, classes
  - Captures text content (trimmed)
  - Captures outer HTML (first 500 chars)
  - Collects all attributes
  - Computes visibility (visible + in viewport)
  - Gets bounding rect (absolute position)
- Returns all matched elements as array

**Selector Support:**
- CSS selectors: `div.modal`, `input[type=password]`, `a:nth-child(2)`
- Element index: `elements[0]` for first element
- Pseudo-selectors: `:not()`, `:first-child`, etc. (CSS4 support)

**Visibility Logic:**
- `offsetHeight > 0 && offsetWidth > 0` (rendered)
- `getComputedStyle(el).visibility !== 'hidden'` (not hidden)
- `getComputedStyle(el).display !== 'none'` (not display:none)
- Bounding rect intersects viewport (in-viewport check)

**Error Handling:**
- Returns `{elements: [], error: '...'}` if selector invalid
- Returns `{elements: []}` if selector matches nothing
- Logs error but doesn't throw
- Gracefully handles DOM mutations during query

**Returns:**
```javascript
{
  elements: [
    {
      tag: 'input',
      id: 'email-field',
      classList: ['form-control', 'required'],
      text: '',
      html: '<input type="email" name="email" ...>',
      attributes: {
        type: 'email',
        name: 'email',
        placeholder: 'Enter email'
      },
      visible: true,
      rect: {x: 100, y: 200, width: 300, height: 40}
    }
  ],
  count: 1,
  error: null
}
```

**Examples:**
```javascript
// Get success message
const result = await getDOM(browser, '.success-message')
if (result.elements.length > 0) {
  console.log(result.elements[0].text)
}

// Check if error is visible
const errors = await getDOM(browser, '.error')
assert.equal(errors.count, 0, 'Should have no errors')
```

---

### teardown(browser)

**Signature:**
```javascript
async teardown(browser: Browser) → Promise<void>
```

**Description:**
Closes browser and releases resources. Ensures graceful shutdown and cleanup.

**Behavior:**
- Closes all pages/tabs
- Disconnects CDP socket
- Kills Chrome process
- Cleans up memory
- Safe to call multiple times (idempotent)

**Error Handling:**
- Logs errors but doesn't throw
- Continues cleanup even if close fails
- Handles already-closed browser gracefully
- Timeout: 5 seconds for graceful close, force kill after

**Example:**
```javascript
try {
  // ... test operations ...
} finally {
  await teardown(browser)
}
```

---

## Protocol Details

### Chrome DevTools Protocol (CDP)

Uses Chrome DevTools Protocol v1.3+ for automation:

**Domains Used:**
- `Page` - Navigation, load events, viewport
- `Runtime` - JavaScript execution, DOM queries
- `Input` - Mouse, keyboard events
- `Network` - Request/response monitoring, idle detection
- `DOM` - Element queries (if needed for advanced scenarios)

**Key Events:**
- `Page.loadEventFired` - Window load complete
- `Page.domContentLoaded` - DOM ready
- `Network.requestWillBeSent` / `Network.responseReceived` - Network activity
- `Runtime.executionContextCreated` - JS context ready

### Connection

Uses WebSocket connection to local Chrome debugging port (default: 9222):

```javascript
{
  wsEndpoint: 'ws://localhost:9222/devtools/browser/...'
}
```

### Timeouts & Defaults

| Operation | Timeout |
|-----------|---------|
| Browser launch | 30s |
| Page navigation | 10s |
| Element find | 5s |
| Element click | 5s |
| Element type | 5s |
| Network idle | 2s (inactivity) |
| Browser close | 5s |

---

## Anti-Patterns: Common Flaky Test Mistakes

**DANGER: These beliefs cause flaky, unmaintainable eval scripts.**

### 1. "UI tests are flaky, so skip them"
**WRONG:** Flakiness is a signal of bad test design, not a reason to avoid UI tests.
- **Root cause:** Tight coupling to timing, missing waits, or brittle selectors
- **Correct approach:** Invest in robust wait strategies (wait_for_visible, wait_for_clickable), use data attributes for selectors, retry logic with exponential backoff
- **Impact:** Skipping UI tests leaves silent failures in production UI paths

### 2. "Screenshots are enough validation"
**WRONG:** Visual screenshots alone cannot verify logic, state, or assertions.
- **Root cause:** Screenshots capture appearance, not correctness; CSS can hide broken elements
- **Correct approach:** Combine screenshots (debugging) with DOM queries (assertions). Use `getDOM()` to verify text, attributes, and element count before taking screenshots
- **Impact:** A screenshot of a "success" button is not proof the form submitted

### 3. "Wait for DOM ready means element is ready"
**WRONG:** Page load completion does not guarantee element visibility or interactivity.
- **Root cause:** React/Vue hydration, lazy loading, animations, and dynamic injection happen AFTER load events
- **Correct approach:** Use explicit waits for selector visibility (`wait_for: 'selector_visible'`) and clickability checks before interaction
- **Impact:** Clicking invisible elements fails or clicks the wrong DOM node

### 4. "Click actions never fail"
**WRONG:** Clicks fail silently when element is not clickable (off-screen, animation in progress, handler not attached).
- **Root cause:** Missing null checks, stale element references, or race conditions between click and handler attachment
- **Correct approach:** Always check `success` and `elementVisible` return values. Retry with backoff on failure. Verify element is clickable (not just visible) before clicking
- **Impact:** Silent failures cascade downstream; assertions pass even though click didn't work

---

## Edge Cases: Real-World Flakiness Scenarios

Web UI automation encounters these systematic challenges. Understanding them prevents flaky tests.

### Edge Case 1: Flaky Element Location
**Problem:** Element exists in DOM but is not yet visible or clickable.
- **Symptom:** Test passes occasionally; selector finds element but click/type fails with "elementVisible: false"
- **Root causes:**
  - CSS has not applied yet (element exists but `display: none` or `visibility: hidden`)
  - Parent container is hidden, scrolled out of view, or has `overflow: hidden`
  - Element is dynamically injected after initial render (React lazy load)
  - Z-index or stacking context hides element behind another layer
- **Detection:**
  - `getDOM()` returns count > 0 but visible: false
  - `interact()` returns `{success: false, elementFound: true, elementVisible: false}`
- **Fix Strategy:**
  1. Use explicit visibility wait: `wait_for: 'selector_visible'` before interact
  2. Add polling loop: query element every 100ms until visible or timeout
  3. Check computed styles: log element's actual `display`, `visibility`, `opacity`, `getBoundingClientRect()`
  4. Scroll to element before interaction: use `interact(browser, 'scroll', selector)` or JavaScript scroll

**Example Fix:**
```javascript
// WRONG: Assumes element is ready
await interact(browser, 'click', '.submit-btn')

// RIGHT: Wait for visibility + check result
const waitResult = await getDOM(browser, '.submit-btn')
if (!waitResult.elements[0]?.visible) {
  // Wait 500ms for CSS to apply
  await new Promise(r => setTimeout(r, 500))
  // Try again with scroll
  await interact(browser, 'scroll', '.submit-btn')
}
const clickResult = await interact(browser, 'click', '.submit-btn')
if (!clickResult.success) {
  throw new Error(`Click failed: visible=${clickResult.elementVisible}`)
}
```

### Edge Case 2: Async Rendering (React/Vue Hydration Delays)
**Problem:** Page loads (network idle) but JavaScript framework is still hydrating or lazy-loading content.
- **Symptom:** Navigation says `loaded: true`, but interactive elements don't exist yet. Test flakes because element appears ~500ms later
- **Root causes:**
  - React/Vue hydration takes time; SSR HTML exists but JS hasn't made it interactive
  - Lazy-loaded components (React.lazy, dynamic imports) haven't loaded yet
  - API calls populate data AFTER page load event fires
  - JavaScript bundle is slow to parse/execute in CI environment
- **Detection:**
  - Page navigation completes, but element queries return empty
  - Element count increases when you retry query after delay
  - Browser DevTools shows "Rendering" or "Recalculate Styles" activity after load
- **Fix Strategy:**
  1. Wait for specific element after navigation, not just page load
  2. Use longer network idle threshold or add custom wait condition
  3. Retry with exponential backoff (100ms, 200ms, 400ms, 800ms)
  4. Check for `data-testid` attributes that appear AFTER hydration

**Example Fix:**
```javascript
// WRONG: Assumes load event means everything is ready
const nav = await navigate(browser, url)
const form = await getDOM(browser, 'form[data-testid=login]')
if (form.count === 0) {
  throw new Error('Form not found')  // Flaky - sometimes it appears after 500ms
}

// RIGHT: Retry with backoff until element appears
async function waitForElement(browser, selector, maxWait = 5000) {
  const startTime = Date.now()
  let attempts = 0
  while (Date.now() - startTime < maxWait) {
    const result = await getDOM(browser, selector)
    if (result.count > 0 && result.elements[0].visible) {
      return result.elements[0]
    }
    attempts++
    const backoffMs = Math.min(100 * Math.pow(2, attempts), 1000)
    await new Promise(r => setTimeout(r, backoffMs))
  }
  throw new Error(`Element ${selector} not found after ${maxWait}ms`)
}

const nav = await navigate(browser, url)
const form = await waitForElement(browser, 'form[data-testid=login]')
```

### Edge Case 3: DOM Stale References
**Problem:** Element was found and cached, but removed from DOM before interaction.
- **Symptom:** `getDOM()` returned element at time T, but by time T+100ms, parent was unmounted and element is gone. Click fails with "elementFound: false"
- **Root causes:**
  - Modal/dropdown closed between assertion and action
  - Conditional render changed (e.g., `{isOpen && <Modal/>}` became false)
  - Parent component re-mounted with new DOM tree
  - SPA route change unmounted old page before new page loaded
  - Race condition: test queried element, but async state update removed parent
- **Detection:**
  - `getDOM()` succeeds, but next `interact()` fails with `elementFound: false`
  - No clear timing gap in test code, but element is gone
  - Happens intermittently (race condition)
- **Fix Strategy:**
  1. Query element immediately before action (don't cache results)
  2. Add explicit stability wait: verify element is still there before interact
  3. Use data attributes (not text/position) for selectors to handle re-renders
  4. Verify parent structure hasn't changed

**Example Fix:**
```javascript
// WRONG: Cache DOM result, then click later
const buttons = await getDOM(browser, '.save-btn')
if (buttons.count === 0) throw new Error('Save button not found')
await new Promise(r => setTimeout(r, 200))  // Some async operation
await interact(browser, 'click', '.save-btn')  // Might fail - parent unmounted

// RIGHT: Query just before interact, verify stability
async function clickStable(browser, selector) {
  // Verify element exists and is visible
  const result = await getDOM(browser, selector)
  if (result.count === 0 || !result.elements[0].visible) {
    throw new Error(`Element ${selector} not ready`)
  }
  
  // Click immediately after verification
  const clickResult = await interact(browser, 'click', selector)
  if (!clickResult.success) {
    // Element was removed or hidden between check and click - retry
    return await clickStable(browser, selector)
  }
  return clickResult
}

await clickStable(browser, '.save-btn')
```

### Edge Case 4: Viewport/Scroll Issues
**Problem:** Element exists and is visible, but is off-screen (below fold) so click fails or scrolls to wrong position.
- **Symptom:** Element visible on local machine (small window fits full page), but in CI (standard viewport) element is below fold. Click target is wrong due to scroll position
- **Root causes:**
  - Page height varies by content (dynamic lists, images)
  - CI runs with fixed 1920x1080 viewport, but test was written with different aspect ratio
  - Element's scroll position calculated incorrectly by browser
  - Parent has `overflow: hidden` or `overflow: auto` affecting scroll context
  - Nested scrollable containers (not window, but div.content is scrollable)
- **Detection:**
  - `getDOM()` shows `visible: true` and rect shows negative Y, or Y > viewport height
  - Click succeeds but clicks wrong element at that screen position
  - Screenshot shows element off-screen
- **Fix Strategy:**
  1. Always scroll element into view before interact (implemented in `interact()` but verify)
  2. Use `getDOM()` rect to verify element is within viewport bounds
  3. Scroll parent container if viewport scroll didn't work
  4. Check for nested scrollable contexts

**Example Fix:**
```javascript
// WRONG: Trust that interact() handles scroll
await interact(browser, 'click', '.bottom-button')  // Might click wrong element

// RIGHT: Verify scroll position before clicking
async function clickWithScroll(browser, selector) {
  const result = await getDOM(browser, selector)
  if (result.count === 0) throw new Error(`Element ${selector} not found`)
  
  const rect = result.elements[0].rect
  if (rect.y < 0 || rect.y + rect.height > 1080) {
    // Element off-screen, scroll to center
    await interact(browser, 'scroll', null, Math.round(rect.y - 540).toString())
    // Wait for scroll settle
    await new Promise(r => setTimeout(r, 200))
  }
  
  return await interact(browser, 'click', selector)
}

await clickWithScroll(browser, '.bottom-button')
```

### Edge Case 5: Race Conditions
**Problem:** Click action fires, but event handler has not been attached yet; click is processed but does nothing.
- **Symptom:** Click succeeds (returns `success: true`), element doesn't change state. Click listener wasn't attached yet due to async script loading
- **Root causes:**
  - React/Vue component rendered but not mounted (event handlers attach in useEffect/onMounted)
  - Event delegation not set up yet (jQuery on() or modern event handler attachment)
  - Third-party library (analytics, tracking) lazily attaches handlers
  - Click event fires in event capture phase before handler is attached in bubble phase
- **Detection:**
  - `interact()` returns `{success: true}` but page state unchanged
  - No error, but action had no effect
  - Retrying the action works (handler now attached)
- **Fix Strategy:**
  1. Wait for framework to be "ready" (e.g., check `window.React` or `__NUXT__`)
  2. Retry action multiple times (handler might attach on second click)
  3. Use explicit waits for event listeners using JavaScript Runtime evaluation
  4. Verify DOM state changed after action (element should have new class, attribute, etc.)

**Example Fix:**
```javascript
// WRONG: Click and hope handler is attached
await interact(browser, 'click', '.submit')
const result = await getDOM(browser, '.success-msg')
if (result.count === 0) {
  // Did handler fire? Or was it already gone?
  throw new Error('No success message')
}

// RIGHT: Verify action had effect, retry if not
async function clickWithEffect(browser, clickSelector, resultSelector) {
  const beforeResult = await getDOM(browser, resultSelector)
  const beforeCount = beforeResult.count
  
  await interact(browser, 'click', clickSelector)
  
  // Wait for effect - result should appear or change
  const maxRetries = 3
  for (let i = 0; i < maxRetries; i++) {
    await new Promise(r => setTimeout(r, 100 * (i + 1)))
    const afterResult = await getDOM(browser, resultSelector)
    if (afterResult.count > beforeCount) {
      return afterResult.elements[0]  // Success - effect happened
    }
  }
  
  throw new Error(`Click on ${clickSelector} had no effect on ${resultSelector}`)
}

const successMsg = await clickWithEffect(browser, '.submit', '.success-msg')
```

### Edge Case 6: Animation/Transition Timing
**Problem:** Element is visible and clickable, but CSS animations are in progress; clicking during animation causes race conditions or intermediate states.
- **Symptom:** Element appears in screenshot, but animation hasn't completed. Clicking during animation leaves page in partial state (e.g., modal 50% visible)
- **Root causes:**
  - CSS transitions (0.3s opacity, 0.5s transform) are playing
  - Keyframe animations (fade-in, slide-in) take time to complete
  - Element is positioned during animation, bounding rect changes mid-animation
  - Animation-delay causes element to animate AFTER being visible
- **Detection:**
  - Screenshot shows partially animated element
  - Element position/size changes between getDOM calls
  - Click succeeds but clicks partial element (e.g., only the visible part)
- **Fix Strategy:**
  1. Wait for animation completion before interaction (getComputedStyle animation-iteration-count)
  2. Disable animations in test (CSS or JavaScript override)
  3. Wait for element rect to stabilize (query twice, compare rects)
  4. Add artificial delay to account for animation duration

**Example Fix:**
```javascript
// WRONG: Click element as soon as it's visible
await interact(browser, 'click', '.modal')

// RIGHT: Wait for animation to complete
async function waitForAnimationComplete(browser, selector) {
  const element = await getDOM(browser, selector)
  if (element.count === 0) throw new Error(`${selector} not found`)
  
  // Query twice to check if position is stable
  const rect1 = element.elements[0].rect
  await new Promise(r => setTimeout(r, 100))
  const element2 = await getDOM(browser, selector)
  const rect2 = element2.elements[0].rect
  
  // If rects differ significantly, animation is still playing
  if (Math.abs(rect1.y - rect2.y) > 5 || Math.abs(rect1.x - rect2.x) > 5) {
    // Animation in progress, wait longer
    await new Promise(r => setTimeout(r, 300))
  }
}

await waitForAnimationComplete(browser, '.modal')
await interact(browser, 'click', '.modal-button')
```

---

## Error Handling

**Common Errors:**

| Error | Cause | Recovery |
|-------|-------|----------|
| `Protocol error` | Chrome crashed | Restart; relaunch browser |
| `Element not found` | Selector invalid/timing | Adjust selector; increase wait |
| `Element not visible` | Hidden/off-screen | Check CSS/DOM state; scroll |
| `Navigation timeout` | Page slow/unresponsive | Increase timeout; check URL |
| `Connection closed` | Browser terminated | Relaunch; check resources |

**Best Practices:**

1. **Always teardown:** Use try/finally blocks
2. **Check return status:** Verify `success` field before assertions
3. **Wait for stability:** Use `navigate()` wait conditions; don't rush actions
4. **Validate selectors:** Test with browser DevTools first
5. **Handle timeouts gracefully:** Retry with backoff for flaky scenarios
6. **Screenshot on failure:** Capture state before throwing

---

## Wait Strategies: Handling Async State

Proper waiting is the foundation of non-flaky tests. Understanding the difference between states prevents races and timeouts.

### wait_for Options

The `navigate()` function supports different wait conditions:

#### document_ready
Waits for DOM ready and page load event, but does NOT wait for network idle.
- **When to use:** Pages that don't require additional network requests after load
- **Advantage:** Fast (10-20ms for simple pages)
- **Risk:** Element might not exist yet if lazy-loaded via API
- **Example:** Static HTML pages, pre-rendered SSR with all content

```javascript
// Document ready but API calls still pending
const nav = await navigate(browser, 'http://example.com', { wait_for: 'document_ready' })
// getDOM() might return empty if data hasn't loaded yet
```

#### network_idle (default)
Waits for DOM ready + network idle (2 seconds with no pending requests).
- **When to use:** Most API-driven pages, SPAs, React/Vue apps
- **Advantage:** Ensures initial data fetch completes before tests interact
- **Risk:** Slow on pages with long-polling or continuous background requests
- **Example:** Login pages, dashboard with API calls, dynamically populated lists

```javascript
// Recommended for most tests
const nav = await navigate(browser, 'http://example.com')  // network_idle by default
// Page has loaded AND initial API calls completed
```

#### selector_visible
Waits for DOM ready + specific element to become visible.
- **When to use:** Pages where you need a specific element before proceeding
- **Advantage:** Very specific; fails fast if element never appears
- **Risk:** Timeout if element never appears or selector is wrong
- **Example:** Login form must be visible before typing password

```javascript
// Wait for form before continuing
const nav = await navigate(browser, 'http://localhost:3001/login', {
  wait_for: 'selector_visible',
  selector: 'form[data-testid=login-form]'
})
if (!nav.loaded) {
  throw new Error('Login form never appeared')
}
```

### Exist vs Visible vs Clickable

These are distinct states. Understand the differences:

#### Exist
Element is in the DOM tree.
- Checked by: CSS selector returns non-zero count
- Not guaranteed to be visible or interactable
- Example: `<div style="display: none">Hidden button</div>` exists but is not visible
- **Test with:** `getDOM()` returns count > 0, but may have visible: false

```javascript
const result = await getDOM(browser, '#hidden-button')
console.log(result.count)  // 1 - element exists
console.log(result.elements[0].visible)  // false - but not visible
```

#### Visible
Element is in DOM, rendered with non-zero dimensions, and CSS does not hide it.
- Checked by: offsetHeight > 0 && offsetWidth > 0 && not hidden by CSS
- May not be fully in viewport (could be partially off-screen)
- May still be covered by other elements (z-index issue)
- **Test with:** `getDOM()` returns visible: true, but bounding rect may be off-screen

```javascript
const result = await getDOM(browser, '#button-below-fold')
console.log(result.elements[0].visible)  // true - rendered
console.log(result.elements[0].rect.y)   // 2000 - below viewport (1080px)
```

#### Clickable
Element is visible + in viewport + event handler is attached + not disabled.
- Requires: visible + rect intersects viewport + not `pointer-events: none` + not disabled attribute
- The most restrictive state; requires all conditions
- **Test with:** `interact(browser, 'click', selector)` before checking return value

```javascript
// Element is visible but not yet clickable
const result = await getDOM(browser, '.submit-btn')
console.log(result.elements[0].visible)  // true - visible
const clickResult = await interact(browser, 'click', '.submit-btn')
console.log(clickResult.success)  // false - handler not attached yet, or disabled
console.log(clickResult.elementVisible)  // true - was visible, but interaction failed
```

### Polling with Timeouts

For robust tests, poll element state until it reaches desired condition or timeout:

#### Pattern 1: Simple Retry Loop
```javascript
async function waitForElement(browser, selector, maxWaitMs = 5000) {
  const startTime = Date.now()
  const pollIntervalMs = 100
  
  while (Date.now() - startTime < maxWaitMs) {
    const result = await getDOM(browser, selector)
    if (result.count > 0 && result.elements[0].visible) {
      return result.elements[0]
    }
    await new Promise(r => setTimeout(r, pollIntervalMs))
  }
  
  throw new Error(`Timeout waiting for ${selector} after ${maxWaitMs}ms`)
}

// Usage
const element = await waitForElement(browser, '.success-message')
```

#### Pattern 2: Exponential Backoff (reduce CPU for long waits)
```javascript
async function waitForElementWithBackoff(browser, selector, maxWaitMs = 5000) {
  const startTime = Date.now()
  let pollIntervalMs = 50
  
  while (Date.now() - startTime < maxWaitMs) {
    const result = await getDOM(browser, selector)
    if (result.count > 0 && result.elements[0].visible) {
      return result.elements[0]
    }
    
    await new Promise(r => setTimeout(r, pollIntervalMs))
    // Increase interval each iteration, cap at 500ms
    pollIntervalMs = Math.min(pollIntervalMs * 1.5, 500)
  }
  
  throw new Error(`Timeout waiting for ${selector} after ${maxWaitMs}ms`)
}
```

#### Pattern 3: Condition-Based Polling
```javascript
async function waitForCondition(browser, condition, maxWaitMs = 5000) {
  const startTime = Date.now()
  
  while (Date.now() - startTime < maxWaitMs) {
    if (await condition(browser)) {
      return true
    }
    await new Promise(r => setTimeout(r, 100))
  }
  
  throw new Error(`Condition not met after ${maxWaitMs}ms`)
}

// Usage: Wait for error count to be zero
await waitForCondition(
  browser,
  async (b) => {
    const errors = await getDOM(b, '.error-message')
    return errors.count === 0
  },
  3000
)
```

#### Pattern 4: State Stability Polling (wait for element to stop changing)
```javascript
async function waitForStableElement(browser, selector, maxWaitMs = 5000) {
  const startTime = Date.now()
  let lastRect = null
  let stableCount = 0  // Need 2 consecutive identical rects
  
  while (Date.now() - startTime < maxWaitMs) {
    const result = await getDOM(browser, selector)
    if (result.count === 0) {
      lastRect = null
      stableCount = 0
      await new Promise(r => setTimeout(r, 100))
      continue
    }
    
    const currentRect = result.elements[0].rect
    
    // Check if rect hasn't changed
    if (lastRect && 
        lastRect.x === currentRect.x && 
        lastRect.y === currentRect.y && 
        lastRect.width === currentRect.width && 
        lastRect.height === currentRect.height) {
      stableCount++
      if (stableCount >= 2) {  // Stable for 200ms
        return result.elements[0]
      }
    } else {
      stableCount = 0  // Reset, element is still moving
    }
    
    lastRect = currentRect
    await new Promise(r => setTimeout(r, 100))
  }
  
  throw new Error(`Element ${selector} never stabilized after ${maxWaitMs}ms`)
}

// Usage: Wait for animated modal to finish animating
const modal = await waitForStableElement(browser, '.modal', 3000)
```

---

## Screenshot Guidance: Visual Validation & Debugging

Screenshots are powerful tools for debugging and documentation, but must be used correctly. They capture state, not truth.

### When to Take Screenshots

#### Before Assertion
Take a screenshot right before making an assertion. If assertion fails, you already have visual evidence.

```javascript
// GOOD: Screenshot before assertion
const result = await getDOM(browser, '.success-message')
const shot = await screenshot(browser, 'before-success-check.png')

if (result.count === 0) {
  // Screenshot already captured, shows why assertion failed
  throw new Error('Success message not found - see before-success-check.png')
}
```

#### On Failure
Capture page state when errors occur. This is the single most important debugging tool.

```javascript
try {
  await interact(browser, 'click', '.delete-button')
  const confirmation = await getDOM(browser, '.confirmation-dialog')
  if (confirmation.count === 0) {
    throw new Error('Confirmation dialog did not appear')
  }
} catch (err) {
  // Capture page state at moment of failure
  await screenshot(browser, `failure-${Date.now()}.png`)
  throw err
}
```

#### On Success (for documentation)
Take screenshots at key success milestones. These serve as visual proof of feature working.

```javascript
// Screenshot successful login
const loginSuccess = await getDOM(browser, '.dashboard-header')
if (loginSuccess.count > 0) {
  await screenshot(browser, 'login-successful.png')
  console.log('Login verified, screenshot saved')
}
```

### Screenshots as Debugging Evidence

Screenshots reveal issues that assertions can't detect:

#### Visual Differences
```javascript
// Before and after screenshots to detect layout/styling changes
await screenshot(browser, 'page-before-update.png')
await interact(browser, 'click', '.theme-toggle')
await new Promise(r => setTimeout(r, 300))  // Wait for theme animation
await screenshot(browser, 'page-after-update.png')
// Visual diff these screenshots to find CSS differences
```

#### Layout Issues
```javascript
// Screenshot shows if element is actually off-screen or covered
const element = await getDOM(browser, '.modal')
if (element.count > 0 && element.elements[0].visible) {
  // getDOM says visible, but screenshot might show it's covered by overlay
  const shot = await screenshot(browser, 'modal-overlap-check.png')
  // Manual inspection: is modal actually visible, or hidden behind something?
}
```

#### Rendering Failures
```javascript
// Screenshot catches CSS not applying, images not loading, etc.
await navigate(browser, 'http://localhost:3001/gallery')
// Images should be visible by now
const images = await getDOM(browser, 'img')
if (images.count === 0) {
  // Why no images? Screenshot will show if page is blank or partially rendered
  await screenshot(browser, 'gallery-broken.png')
  throw new Error('Gallery images not found')
}
```

### Full Page vs Element-Specific

#### Full Page Screenshot (default)
```javascript
// Captures entire viewport (1920x1080)
const shot = await screenshot(browser, 'full-page.png')
// Good for: seeing overall layout, context around failure
```

For element-specific details, use getDOM() to get bounding rect, then crop screenshot:

#### Element Crop (manual)
```javascript
// Get element's bounding box
const result = await getDOM(browser, '.button-to-crop')
const rect = result.elements[0].rect
console.log(`Crop: x=${rect.x}, y=${rect.y}, w=${rect.width}, h=${rect.height}`)

// Take full screenshot, then crop in post-processing or use external tool
const shot = await screenshot(browser, 'full-page.png')
// Use ImageMagick: convert full-page.png -crop 200x50+100+200 button.png
```

---

## Flakiness Detection: Identifying and Fixing Intermittent Failures

A test that passes sometimes and fails sometimes is flaky. Flakiness indicates a real problem, not randomness.

### How to Identify Flaky Tests

#### Pattern 1: Intermittent Failures (works 4 out of 5 runs)
```javascript
// Run same test 5 times, watch for intermittent failures
// If test passes sometimes and fails sometimes, it's flaky

// Root cause: Timing-dependent code
await interact(browser, 'click', '.save-button')
// What if handler takes 200ms to attach? Sometimes it's ready, sometimes not
const result = await getDOM(browser, '.success-message')
if (result.count === 0) {
  throw new Error('Save failed')  // Intermittent failure
}
```

#### Pattern 2: Timing-Dependent Failures (passes with longer timeouts)
```javascript
// Test fails with --timeout 5000 but passes with --timeout 10000
// Clear sign: your test is waiting for something async, but timeout too short

// Bad: Fixed sleep (works on developer machine, fails in CI)
await interact(browser, 'click', '.submit')
await new Promise(r => setTimeout(r, 100))  // Works locally (maybe), fails on slow CI
const result = await getDOM(browser, '.result')

// Good: Polling with reasonable timeout
const element = await waitForElement(browser, '.result', 5000)
```

#### Pattern 3: Tests Pass Locally, Fail in CI
```javascript
// This almost always indicates:
// 1. Timing assumption (element loads in 100ms on your machine, takes 2s in CI)
// 2. Viewport difference (your screen size != CI viewport)
// 3. Network difference (local loopback is fast, CI network is slow)

// Test that passes locally might miss this timing issue:
const result = await getDOM(browser, 'input[name=email]')
// input may not exist yet if API call takes 1.5s

// Fix: Explicit wait handles both fast and slow environments
const input = await waitForElement(browser, 'input[name=email]', 5000)
```

### Retry Logic for Flaky Selectors

When a selector is intermittently unreliable, build in retry logic:

```javascript
async function interactWithRetry(browser, action, selector, value, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await interact(browser, action, selector, value)
      if (result.success && result.elementVisible) {
        return result  // Success
      }
      
      if (attempt < maxRetries - 1) {
        // Not yet successful, retry
        console.log(`Attempt ${attempt + 1} failed, retrying...`)
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 100))  // Exponential backoff
        continue
      }
    } catch (err) {
      if (attempt < maxRetries - 1) {
        console.log(`Attempt ${attempt + 1} threw error, retrying...`)
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 100))
        continue
      }
      throw err
    }
  }
  
  throw new Error(`Failed after ${maxRetries} attempts: ${selector}`)
}

// Usage
await interactWithRetry(browser, 'click', '.flaky-button')
```

### Root Cause Analysis: Finding the Real Problem

When you discover a flaky test, don't just add delays. Diagnose the root cause:

#### Investigation Workflow

**Step 1: Gather Evidence**
```javascript
// Log element state before action
const beforeClick = await getDOM(browser, '.button')
console.log('Before click:', {
  found: beforeClick.count > 0,
  visible: beforeClick.elements[0]?.visible,
  rect: beforeClick.elements[0]?.rect,
  classes: beforeClick.elements[0]?.classList
})

// Try action and capture result
const clickResult = await interact(browser, 'click', '.button')
console.log('Click result:', clickResult)

// Check state after action
const afterClick = await getDOM(browser, '.result')
console.log('After click:', {
  resultCount: afterClick.count,
  resultVisible: afterClick.elements[0]?.visible
})
```

**Step 2: Identify the Bottleneck**
```javascript
// Too-tight timeout (element takes 500ms to appear, timeout is 200ms)
// FIX: Increase timeout or use polling
const elem = await waitForElement(browser, '.result', 5000)

// Element appears then disappears (modal closes automatically)
// FIX: Capture value immediately after appearance
const modal = await getDOM(browser, '.modal')
const modalText = modal.elements[0]?.text  // Capture immediately
// Then assert the value

// Animation in progress when clicking
// FIX: Wait for animation to complete before clicking
await waitForStableElement(browser, '.animated-button')
await interact(browser, 'click', '.animated-button')

// Handler not attached yet
// FIX: Retry click action with backoff
await interactWithRetry(browser, 'click', '.button-with-late-handler', null, 3)
```

**Step 3: Implement Targeted Fix**
```javascript
// Once you identify the root cause, implement specific fix:

// Issue: Animation delay
// Fix: Wait for element to stabilize before interaction
async function clickAnimatedElement(browser, selector) {
  await waitForStableElement(browser, selector, 2000)
  return await interact(browser, 'click', selector)
}

// Issue: Async data loading
// Fix: Poll for element to appear with reasonable timeout
async function clickAfterDataLoads(browser, selector) {
  await waitForElement(browser, selector, 5000)
  return await interact(browser, 'click', selector)
}

// Issue: Handler attachment race
// Fix: Retry with exponential backoff
async function clickWithHandlerRetry(browser, selector) {
  return await interactWithRetry(browser, 'click', selector, null, 3)
}
```

**Step 4: Validate Fix**
```javascript
// Run test multiple times to confirm flakiness is gone
// Local: npm test -- --repeat=10
// CI: Run same test 10 times in pipeline, verify no intermittent failures
```

---

## Example Usage

```javascript
// Complete eval script example
const { launch, navigate, interact, screenshot, getDOM, teardown } = require('./eval-driver-web-cdp')

async function runEval() {
  let browser
  try {
    // 1. Launch browser
    browser = await launch()
    console.log('Browser launched')

    // 2. Navigate to login page
    const nav = await navigate(browser, 'http://localhost:3001/login')
    if (!nav.loaded) {
      throw new Error(`Failed to load login page: ${nav.statusCode}`)
    }

    // 3. Check login form visible
    const form = await getDOM(browser, 'form[data-testid=login-form]')
    if (form.count === 0) {
      throw new Error('Login form not found')
    }

    // 4. Interact with form
    await interact(browser, 'type', 'input[name=email]', 'user@example.com')
    await interact(browser, 'type', 'input[name=password]', 'correct-password')
    await interact(browser, 'click', 'button[type=submit]')

    // 5. Wait for navigation (re-navigate to capture new state)
    const afterSubmit = await navigate(browser, 'http://localhost:3001/dashboard')
    if (!afterSubmit.loaded) {
      throw new Error('Dashboard failed to load after login')
    }

    // 6. Verify success
    const success = await getDOM(browser, '.welcome-message')
    if (success.count === 0) {
      throw new Error('Success message not visible')
    }
    console.log('Login successful:', success.elements[0].text)

    // 7. Screenshot for documentation
    const shot = await screenshot(browser, 'dashboard.png')
    console.log('Screenshot:', shot.path)

    return { success: true, result: success.elements[0].text }

  } catch (err) {
    console.error('Eval failed:', err.message)
    if (browser) {
      await screenshot(browser, 'error-state.png')
    }
    throw err
  } finally {
    // 8. Always cleanup
    if (browser) {
      await teardown(browser)
    }
  }
}

// Run
runEval().then(() => {
  console.log('Eval complete')
  process.exit(0)
}).catch(err => {
  console.error(err)
  process.exit(1)
})
```

---

## Implementation Notes

- **Language:** JavaScript/Node.js 16+
- **Dependencies:** Chrome/Chromium installed, CDP client library (e.g., `puppeteer`, `chrome-remote-interface`, or raw WebSocket)
- **Platform:** Linux, macOS, Windows (Chrome available)
- **Headless:** Yes (no GUI, suitable for CI/CD)
- **Concurrency:** Single browser per instance (create multiple instances for parallel eval)

---

## Dependencies

```
chrome-remote-interface@^0.32.0  (or puppeteer/other CDP client)
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **CDP** | Chrome DevTools Protocol - low-level API for Chrome automation |
| **Headless** | Browser runs without GUI, suitable for automation/testing |
| **Viewport** | Visible page area (1920x1080 default) |
| **Network idle** | No pending network requests for 2+ seconds |
| **DOM** | Document Object Model - in-memory representation of HTML |
| **Selector** | CSS query to find elements (e.g., `#id`, `.class`, `[attr=value]`) |
| **Visibility** | Element rendered and not hidden by CSS |

---

## Roadmap

**Future Enhancements:**
- Support for Firefox (Marionette protocol)
- Multi-tab/window management
- Session recording (video capture)
- Performance metrics collection (Lighthouse integration)
- Mobile viewport emulation
- Accessibility tree extraction
- Shadow DOM support
- Cookie/storage management

## Checklist

Before running a CDP eval scenario:

- [ ] `launch()` called with explicit viewport dimensions matching target device class
- [ ] `navigate()` followed by explicit wait for load state (networkIdle or DOMContentLoaded)
- [ ] All element targeting uses `data-testid`, ARIA role, or stable aria-label (not CSS class selectors)
- [ ] Every assertion verifies specific text, attribute, or element state — not just presence
- [ ] `screenshot()` called and file path recorded in scenario output
- [ ] `teardown()` called in all paths (success, failure, timeout)
