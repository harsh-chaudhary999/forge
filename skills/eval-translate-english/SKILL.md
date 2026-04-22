---
name: eval-translate-english
description: "WHEN: A user journey is described in English and must be converted into executable eval YAML. Input: plain English flow. Output: executable YAML scenario with driver actions, targets, and expected results."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "translate to eval"
  - "convert spec to eval"
  - "write eval from English"
allowed-tools:
  - Bash
  - Write
---

# eval-translate-english

Convert plain English descriptions of user journeys and scenarios into executable YAML evaluation scenarios. Enables non-technical stakeholders to define test scenarios without needing to understand YAML syntax or eval driver APIs.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **English description contains "somehow", "at some point", or "eventually"** — These words hide missing steps. STOP. Get precise timing and order before translating.
- **Generated YAML has empty `expected:` fields or `expected: true`** — Empty assertions are not assertions. They will never fail. STOP. Derive explicit expected values from the English description.
- **Scenario references a UI element without a CSS selector or test ID** — Ambiguous selectors break in CI and on different screen sizes. STOP. Ask for or derive a stable selector before generating.
- **Scenario covers only the happy path with no error cases** — Real eval requires negative paths. STOP. Generate at least one failure or edge case scenario alongside every happy path.
- **English description is one sentence covering multiple independent flows** — Multi-flow descriptions produce multi-step YAML that can't isolate failures. STOP. Break into one YAML scenario per user journey.
- **Translated YAML references a driver (web, api, db) that is not in the product's eval stack** — Untestable scenarios produce false confidence. STOP. Verify driver availability against forge-product.md before generating.

## Iron Law

```
EVERY TRANSLATED SCENARIO HAS CONCRETE EXPECTED VALUES IN EVERY STEP, ONE USER JOURNEY PER SCENARIO, AT LEAST ONE FAILURE PATH ALONGSIDE EVERY HAPPY PATH, AND ALL DRIVERS VERIFIED AGAINST THE PRODUCT EVAL STACK. ENGLISH VAGUENESS IS NEVER PRESERVED IN THE YAML OUTPUT.
```

## Purpose

Non-technical stakeholders can describe user flows in plain English, and the skill generates complete, executable YAML scenarios that:
- Map English actions to actual eval driver commands
- Infer selectors, URLs, and API endpoints from context
- Add sensible defaults (timeouts, expected results)
- Include both UI validation and backend verification steps

**Upstream manual QA:** When **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** exists (from **`qa-manual-test-cases-from-prd`**), read it and **carry each relevant `Id` into scenario `name` / `description` / top-level comments** so **P4.4 eval execution** traces to the same acceptance rows that **TDD RED** tests were expected to cover. Do not invent parallel journeys that contradict approved CSV steps.

## Anti-Pattern Preamble: Why Plain English Isn't Enough

Teams often rationalize skipping YAML translation or cutting corners. Here's why these rationalizations fail:

### Rationalization 1: "Plain English is good enough, we don't need YAML scenarios"

**The Truth:** Ambiguous English hides integration gaps. YAML forces precision.

When you write "User logs in and views dashboard," you've made 5+ implicit assumptions:
- Which login method? (email/password, OAuth, SSO)
- What if login API is slow? How long do we wait?
- What does "views" mean? Page loaded? Data populated? API response received?
- What network conditions? (offline, high latency, timeout)
- What's the success observable? (URL change, element visibility, API response)

**Cost of Skipping:** These gaps resurface as production bugs when:
- Your CI environment is faster than production (tests pass locally, fail in pipeline)
- Network latency changes (slow network, slow API)
- UI library updates (element selectors break)
- One service depends on another (order of operations matters)

**The Win:** Translating to YAML forces you to answer these questions NOW, not in production.

### Rationalization 2: "Scenarios are a DBA/QA job, not a developer job"

**The Truth:** Developers write the code the scenarios test. They find the bugs first.

You implement a login endpoint. Only you know:
- What error states it can return (401 invalid, 429 rate-limited, 500 server error)
- How the session token is stored (cookie, localStorage, header)
- What the successful response looks like (token format, expiry)
- How authentication state flows through other parts of the system

QA and DBAs will write scenarios based on YOUR documentation. If your documentation is incomplete, the scenarios miss edge cases.

**Cost of Skipping:** QA writes scenarios that only test the happy path. When a user triggers an edge case (slow network, auth token expiry, race condition), production breaks.

**The Win:** Developers who write scenarios catch bugs before QA. You own the full user journey, not just the unit.

### Rationalization 3: "Scenarios slow translation down"

**The Truth:** Translating vague English now = debugging production failures later.

| Phase | Cost |
|-------|------|
| Translate English to YAML precisely (30 min) | 30 min |
| Run scenario, find 2-3 gaps, fix and rerun (2 cycles) | 1 hr |
| **Total for precision** | **1.5 hrs** |
| Translate vague English quickly (5 min) | 5 min |
| Skip to deployment | - |
| Production incident: "Login broken in high-latency networks" | 8 hrs (debug, page, fix, deploy, monitor) |
| **Total for speed** | **8 hrs 5 min** |

**The Win:** 1.5 hours now saves 8 hours of production firefighting.

### Rationalization 4: "We can't predict all user flows"

**The Truth:** You can't predict ALL, but you CAN cover critical paths and edge cases.

You don't need to test every combination of user actions (that's infinite). You need to test:
1. **Critical happy path**: User achieves their goal (login → view dashboard → logout)
2. **Documented edge cases**: "What if login API times out?" (you know this can happen)
3. **Integration boundaries**: Each boundary between systems (web → API, API → DB, web → cache)
4. **State transitions**: Before/after state is explicitly verified

**The Win:** Coverage isn't about 100% of flows. It's about 100% of critical paths and known risks. YAML scenarios make this explicit.

---

## Edge Cases in Translation

Real English descriptions hide complexity. These 6 edge cases surface when translating to YAML:

### Edge Case 1: Ambiguous Timeline

**Input:**
```
User logs in and checks their profile
```

**The Problem:**
When does "profile" finish loading? Network latency varies (200ms to 5s). The English sentence doesn't specify. When you translate to YAML without this precision, your scenario might:
- Pass in CI (fast network)
- Fail in production (slow network)
- Fail sometimes, pass other times (race condition)

**Translation Action:**
Add explicit wait condition for the observable outcome:
```yaml
steps:
  - id: step_1
    driver: web-cdp
    action: click
    selector: button[text=Login]
    expected: {visible: true}
  
  - id: step_2
    driver: api-http
    action: verify
    endpoint: GET /profile
    expected: {status: 200, timeout: 5000}  # EXPLICIT: Max 5s wait
    comment: "Wait for profile API (P95 latency = 5s in production)"
  
  - id: step_3
    driver: web-cdp
    action: getDOM
    selector: .profile-card
    expected: {visible: true, timeout: 5000}
    comment: "Profile card visible after API returns"
```

**Key Fix:** Translate "checks profile" to TWO steps: (1) API returns, (2) UI renders. Add timeout based on observed latency, not wishful thinking.

### Edge Case 2: Implicit State Dependencies

**Input:**
```
User updates settings
```

**The Problem:**
"Updates" implies multiple systems must coordinate:
1. Frontend validates input
2. API receives request
3. Database transaction completes
4. Cache is invalidated
5. Other users see the change

English hides all of this. If you translate just to "click Save and verify API 200," you miss:
- Database might not have committed yet (500ms delay)
- Cache might serve stale data (another user sees old settings)
- Race condition: User updates setting twice in rapid succession

**Translation Action:**
Break "update" into explicit verification steps:
```yaml
steps:
  - id: step_1
    driver: web-cdp
    action: type
    selector: input[name=timezone]
    value: "America/New_York"
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: button[text=Save]
  
  - id: step_3
    driver: api-http
    action: verify
    endpoint: PATCH /settings
    expected: {status: 200}
    comment: "API acknowledges update"
  
  - id: step_4
    driver: db-mysql
    action: verify
    query: "SELECT timezone FROM users WHERE id = ? LIMIT 1"
    expected: {timezone: "America/New_York"}
    comment: "Database committed (not just in-flight)"
  
  - id: step_5
    driver: api-http
    action: verify
    endpoint: GET /settings
    expected: {status: 200, timezone: "America/New_York"}
    comment: "Cache invalidated, fresh read returns new value"
```

**Key Fix:** Don't conflate API success with system consistency. Verify the observable state change across all boundaries (API, DB, cache).

### Edge Case 3: Branching and Conditional Flows

**Input:**
```
User enables 2FA or skips it
```

**The Problem:**
One English sentence, TWO different flows. Which one should your scenario test?
- If you test only the "enable" path, you miss bugs in the "skip" path
- If you try to test both in one scenario with conditional logic, the scenario becomes unmaintainable
- The English doesn't specify preconditions (when should each path run?)

**Translation Action:**
Create TWO separate scenarios with explicit preconditions:
```yaml
---
# Scenario 1: User enables 2FA
scenario: "User enables 2FA during setup"
preconditions:
  - user_is_authenticated: true
  - has_2fa_enabled: false
  - feature_flag_2fa: true

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings/security
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: button[text="Enable 2FA"]
  
  - id: step_3
    driver: web-cdp
    action: getDOM
    selector: .modal-2fa-setup
    expected: {visible: true}
    comment: "2FA setup modal appeared"
  
  - id: step_4
    driver: api-http
    action: verify
    endpoint: POST /auth/2fa/enable
    expected: {status: 201}

---
# Scenario 2: User skips 2FA
scenario: "User skips 2FA during setup"
preconditions:
  - user_is_authenticated: true
  - has_2fa_enabled: false
  - feature_flag_2fa: true

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings/security
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: button[text="Skip for Now"]
  
  - id: step_3
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/dashboard
    expected: {status: loaded}
    comment: "Skipped 2FA, returned to dashboard"
```

**Key Fix:** One scenario = one happy path. Create separate scenarios for each branch. Document preconditions explicitly so it's clear when each scenario applies.

### Edge Case 4: Vague Success Criteria

**Input:**
```
User sees a list of items
```

**The Problem:**
"Sees a list" is completely ambiguous:
- How many items? (1, 10, 100?)
- In what order? (newest first, alphabetical, random?)
- With what data? (name only, or name + price + description?)
- What's the minimum to claim success? (at least 1 item, or exactly 5?)

When you skip these details, your scenario might pass when it shouldn't:
- API returns 0 items → scenario passes (it verified element exists, but it's empty)
- Items are in wrong order → scenario passes (didn't check sort order)
- Missing data fields → scenario passes (didn't verify field presence)

**Translation Action:**
Translate vague "sees" to precise assertions:
```yaml
steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/products
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: getDOM
    selector: .product-list
    expected:
      visible: true
      element_count: {min: 3, max: 5}  # EXPLICIT: range, not just "has items"
      comment: "Verify 3-5 products displayed (pagination shows 5 per page)"
  
  - id: step_3
    driver: web-cdp
    action: getDOM
    selector: .product-item
    expected:
      has_field: ["name", "price", "rating"]  # EXPLICIT: required fields
      sorted_by: {field: "date", order: "DESC"}  # EXPLICIT: sort order
      comment: "Each product has name/price/rating, sorted newest first"
  
  - id: step_4
    driver: api-http
    action: verify
    endpoint: GET /products?limit=5
    expected:
      status: 200
      count: {min: 3, max: 5}
      schema: {name: "string", price: "number", rating: "number"}
```

**Key Fix:** Replace vague "sees" with testable assertions:
- `element_count` with min/max bounds
- `has_field` listing required fields
- `sorted_by` with field and direction
- Schema validation for API responses

### Edge Case 5: Missing Failure Paths

**Input:**
```
User logs in and navigates to settings
```

**The Problem:**
The English describes only the happy path. It doesn't mention:
- What if login API times out?
- What if the user's session expires?
- What if settings page 404s?
- What if the database is down?

Real users encounter these failures. If your scenarios only test happy paths, you'll have:
- No test coverage for error handling
- No verification that failure messages are user-friendly
- No guarantee the system degrades gracefully

**Translation Action:**
Create parallel failure-path scenarios alongside happy-path:
```yaml
---
# Happy path
scenario: "User logs in and accesses settings"
steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
  # ... login steps ...
  - id: step_3
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings

---
# Failure path: API timeout
scenario: "User logs in, but settings API times out"
preconditions:
  - inject_latency: {endpoint: "GET /settings", delay: 35000}  # Longer than 30s timeout

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
  # ... login steps ...
  - id: step_3
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings
    expected: {status: loaded}
  
  - id: step_4
    driver: web-cdp
    action: getDOM
    selector: .error-message, [role=alert]
    expected:
      visible: true
      text: {contains: ["Settings unavailable", "try again"]}
    comment: "User sees graceful error message, not blank page"

---
# Failure path: Database down
scenario: "User logs in successfully, but settings page database is down"
preconditions:
  - inject_failure: {service: "database", status: "down"}

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
  # ... login steps ...
  - id: step_3
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings
    expected: {status: loaded}
  
  - id: step_4
    driver: web-cdp
    action: getDOM
    selector: .error-message, [role=alert]
    expected:
      visible: true
      text: {contains: "Settings unavailable"}
    comment: "Graceful fallback when database is down"
```

**Key Fix:** For each happy-path scenario, create 2-3 failure-path variants:
1. **Network failure** (timeout, 5xx)
2. **Dependency failure** (database down, cache miss)
3. **Data failure** (invalid response, missing fields)

Document expected graceful degradation behavior.

### Edge Case 6: Timing-Dependent Assertions

**Input:**
```
User posts a comment, and other users see it immediately
```

**The Problem:**
"Immediately" is not testable. What does "immediately" mean?
- 100ms?
- 1 second?
- 10 seconds?

In a distributed system, "immediately" depends on:
- Database replication lag
- Cache invalidation
- Message queue propagation
- Network latency

If you write a scenario that expects < 100ms propagation, it will flake in production where actual P95 is 2 seconds.

**Translation Action:**
Translate "immediately" to documented timing windows based on observed behavior:
```yaml
# First, observe and measure
# P50: 300ms, P95: 2s, P99: 5s

steps:
  - id: step_1
    driver: web-cdp
    action: type
    selector: textarea[name=comment]
    value: "Test comment"
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: button[text="Post Comment"]
  
  - id: step_3
    driver: api-http
    action: verify
    endpoint: POST /comments
    expected: {status: 201}
    comment: "Comment posted to API"
  
  - id: step_4
    driver: web-cdp
    action: wait
    duration: 2000  # EXPLICIT: P95 propagation time
    comment: "Wait for eventual consistency (P95 = 2s in production)"
  
  - id: step_5
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/posts/123
    expected: {status: loaded}
  
  - id: step_6
    driver: web-cdp
    action: getDOM
    selector: .comment-item
    expected:
      visible: true
      text: "Test comment"
    comment: "Comment visible after P95 propagation window"
  
  metadata:
    timing_notes: "P50=300ms, P95=2s, P99=5s (measured from production logs)"
    consistency_model: "Eventual consistency with SLA of 5s max"
```

**Key Fix:** Replace vague timing ("immediately", "soon", "after") with:
1. Measure actual latency in production (P50, P95, P99)
2. Document the observed values in metadata
3. Use P95 as the wait duration (catches real-world behavior)
4. Add comment explaining why that number was chosen

---

## Ambiguity Detection & Resolution

When English is too ambiguous to translate directly to YAML, use this decision tree:

### Common Ambiguities and How to Resolve Them

#### 1. Implicit Timing: "soon", "immediately", "after", "then"

| Phrase | Problem | Resolution Question | Example Answer |
|--------|---------|-------|---------|
| "User logs in, then checks profile" | When does "then" happen? Immediately after click? After API response? | How many seconds between login click and profile check? | 2-5s (after login API returns) |
| "Item appears soon" | How long is "soon"? User expects < 1s, but actual is 3s? | What's the P95 latency you observe in production? | 2000ms (P95 from metrics) |
| "Users see the update immediately" | Eventual consistency is not immediate. How long? | What's your maximum propagation SLA? | 5000ms max, P95=2000ms |

**Decision Tree:**
```
IF phrase contains timing word ("soon", "immediately", "after", "then")
  THEN ask: "How many ms/seconds should step X wait before step Y?"
  IF answer is "I don't know"
    THEN measure in production or use conservative estimate (5000ms)
  ELSE
    TRANSLATE to explicit wait step with that duration
```

**Example Translation:**
```
English: "User enables 2FA and sees confirmation"
↓ (Ambiguous: when does confirmation appear?)
Question: "How long after clicking enable should the confirmation appear?"
Answer: "Usually under 1 second, but sometimes 2-3 seconds on slow networks"
↓
YAML:
  - action: click
    selector: button[text="Enable 2FA"]
  - action: wait
    duration: 3000
    comment: "P95 latency = 3s on slow networks"
  - action: getDOM
    selector: .confirmation-message
    expected: {visible: true}
```

#### 2. Implicit Counts: "some items", "a few records", "multiple results"

| Phrase | Problem | Resolution Question | Example Answer |
|--------|---------|--------|---------|
| "User sees a list of items" | Minimum items? Maximum? Empty list counts? | How many items should be displayed (min-max)? | 3-20 items |
| "Search returns results" | How many results? Even 1 counts? | What's the minimum number of results that proves search works? | At least 1, typically 10-50 |
| "Cart has items" | One item? Many items? | After user adds to cart, how many should be visible? | At least 1, user might add multiple |

**Decision Tree:**
```
IF phrase contains vague count ("some", "a few", "multiple", "results")
  THEN ask: "What's the minimum and maximum count that proves success?"
  IF answer is "I don't know"
    THEN use context (if paginated: page size; if filtered: sensible range)
  ELSE
    TRANSLATE to element_count with min/max bounds
```

**Example Translation:**
```
English: "User searches for 'laptop' and sees results"
↓ (Ambiguous: how many results?)
Question: "How many search results should appear?"
Answer: "Usually 10-50 results for a common term"
↓
YAML:
  - action: type
    selector: input[placeholder*=search]
    value: "laptop"
  - action: click
    selector: button[text="Search"]
  - action: getDOM
    selector: .search-results
    expected:
      visible: true
      element_count: {min: 1, max: 50}
      comment: "At least 1 result, typically 10-50 for common search term"
```

#### 3. Implicit Ordering: "in order", "by date", "alphabetically"

| Phrase | Problem | Resolution Question | Example Answer |
|--------|---------|--------|---------|
| "Items are listed in order" | Which order? Newest first? A-Z? Most relevant? | What field and direction should items be sorted by? | Date DESC (newest first) |
| "Comments appear chronologically" | Ascending or descending? | Should oldest comments or newest comments appear first? | Ascending (oldest first) |
| "Products sorted by price" | Low to high, or high to low? | Should products be sorted price ascending or descending? | Ascending (cheapest first) |

**Decision Tree:**
```
IF phrase mentions ordering ("in order", "sorted", "chronological")
  THEN ask: "What field and direction? (field ASC or field DESC)"
  IF answer is "I don't know"
    THEN ask: "Should lowest or highest value appear first?"
  ELSE
    TRANSLATE to sorted_by with field and order
```

**Example Translation:**
```
English: "User sorts products by price"
↓ (Ambiguous: high to low or low to high?)
Question: "Which direction should price be sorted? (low-to-high or high-to-low)"
Answer: "Low to high, so cheapest appears first"
↓
YAML:
  - action: click
    selector: select[name=sort]
  - action: type
    selector: select[name=sort]
    value: "price_asc"
  - action: getDOM
    selector: .product-item
    expected:
      sorted_by: {field: "price", order: "ASC"}
      comment: "Products sorted price low-to-high"
```

#### 4. Implicit Success: "works", "is correct", "loads"

| Phrase | Problem | Resolution Question | Example Answer |
|--------|---------|--------|---------|
| "Login works" | What observable outcome proves login worked? (URL? Token? Page content?) | What should the user see/experience after successful login? | Redirected to /dashboard, can see username in header |
| "Page loads correctly" | What does "correct" mean? All images? All text? All data? | What's the minimum observable state that proves the page loaded correctly? | Page title visible, main content loaded, no error messages |
| "API responds" | Status 200? With data? | What status code and response structure proves the API worked? | Status 200, response includes user object with id/email/name |

**Decision Tree:**
```
IF phrase uses vague success indicator ("works", "correct", "loads", "is")
  THEN ask: "What's the observable outcome that proves X succeeded?"
  IF answer vague ("it just works", "it's correct")
    THEN ask: "What would the user see or experience?"
  ELSE
    TRANSLATE to specific expected condition (status code, element visibility, response schema)
```

**Example Translation:**
```
English: "User resets password and receives confirmation email"
↓ (Ambiguous: what proves password was reset? Just email arrival? Or actual login with new password?)
Question: "After reset, what observable outcome proves it worked?"
Answer: "User should receive email with reset link, and after clicking link and entering new password, should be able to log in with new password"
↓
YAML:
  - action: type
    selector: input[name=email]
    value: "user@example.com"
  - action: click
    selector: button[text="Reset Password"]
  - action: getDOM
    selector: .message-success
    expected:
      visible: true
      text: {contains: "Check your email"}
    comment: "Confirmation message appears"
  
  - action: verify  # Check email backend
    endpoint: GET /emails?to=user@example.com&subject=password
    expected:
      status: 200
      count: {min: 1}
      has_field: ["reset_link"]
    comment: "Reset email sent to user"
  
  - action: navigate
    target: "http://localhost:3001/reset?token=..."  # Extract token from email
  
  - action: type
    selector: input[name=newPassword]
    value: "NewPassword123!"
  
  - action: click
    selector: button[text="Reset Password"]
  
  - action: type
    selector: input[type=email]
    value: "user@example.com"
  
  - action: type
    selector: input[type=password]
    value: "NewPassword123!"
  
  - action: click
    selector: button[text="Login"]
  
  - action: verify
    endpoint: POST /auth/login
    expected:
      status: 200
      has_field: ["token"]
    comment: "Login successful with new password proves reset worked"
```

#### 5. Missing Failure Case: No mention of "what if X fails"

| Scenario | Missing Edge Case | Resolution Question | Example Answer |
|----------|---------|---------|---------|
| "User uploads a file" | What if file is too large? Invalid format? Network fails? | What failure scenarios should be tested? | File > 10MB (rejected), invalid format (rejected), upload timeout (retry) |
| "System processes order" | What if payment fails? Inventory check fails? | What if a dependency fails? What's the graceful fallback? | Payment fails → show error, hold order for retry; inventory fails → show out-of-stock |
| "Data syncs to cloud" | What if network is offline? Storage quota exceeded? | What failure modes are possible? What should user see? | Offline → queue synced when online; quota exceeded → show storage full message |

**Decision Tree:**
```
IF scenario mentions happy path but no failure case
  THEN ask: "What can go wrong in this flow?"
  FOR each failure mode:
    ASK: "What should happen when X fails? (error message, retry, fallback)"
    TRANSLATE to separate failure-path scenario with precondition
```

**Example Translation:**
```
English: "User uploads a profile picture"
↓ (Ambiguous: what if file is too large?)
Question: "What failure cases should be tested?"
Answers: 
  1. File > 5MB (too large) → show error
  2. Invalid image format → show error
  3. Upload API timeout → show retry option
↓
Create 4 scenarios:

# Happy path
scenario: "User uploads valid profile picture"
steps:
  - action: click
    selector: input[type=file]
  - action: uploadFile
    file: "profile.jpg" (500KB, valid image)
  - action: verify
    endpoint: POST /profile/picture
    expected: {status: 201}

# Failure path 1: Too large
scenario: "User tries to upload image > 5MB, sees error"
preconditions:
  - file_size: 10485760  # 10MB
steps:
  - action: click
    selector: input[type=file]
  - action: uploadFile
    file: "large-image.jpg"
  - action: getDOM
    selector: .error-message
    expected:
      visible: true
      text: {contains: "File too large"}
    comment: "User informed of size limit"

# Failure path 2: Invalid format
scenario: "User tries to upload non-image file, sees error"
steps:
  - action: click
    selector: input[type=file]
  - action: uploadFile
    file: "document.pdf"
  - action: getDOM
    selector: .error-message
    expected:
      visible: true
      text: {contains: "Only images allowed"}

# Failure path 3: Network timeout
scenario: "Upload API times out, user can retry"
preconditions:
  - inject_latency: {endpoint: "POST /profile/picture", delay: 35000}
steps:
  - action: click
    selector: input[type=file]
  - action: uploadFile
    file: "profile.jpg"
  - action: wait
    duration: 35000
  - action: getDOM
    selector: button[text="Retry"]
    expected:
      visible: true
    comment: "User can retry after timeout"
```

---

## Input Format

### Option 1: User Story

```
User opens the app, sees login screen, enters email and password,
clicks login, sees home screen, navigates to settings, toggles 2FA,
sees success message, logs out.
```

### Option 2: Numbered Scenario

```
Scenario: Complete purchase flow
1. User logs in with valid credentials
2. User browses products  
3. User adds item to cart
4. User proceeds to checkout
5. User enters payment details
6. User confirms purchase
7. Order confirmation appears
```

### Option 3: Detailed Journey with Data

```
User logs in with email=john@example.com and password=secret123,
then navigates to settings and enables 2FA with phone number +1-555-0100,
verifies OTP, and logs out successfully.
```

## Confidence Scoring: Rating Translation Quality

After translating English to YAML, assign a confidence score (0-100%) that reflects how likely the scenario will catch real bugs. This score guides downstream decisions: LOW confidence scenarios need review before execution, HIGH confidence scenarios can run immediately.

### Confidence Levels

#### HIGH (95-100%): Ready to Execute

You assign HIGH confidence when:
- ✅ All steps have explicit, observable outcomes (not assumptions)
- ✅ No timing ambiguities (all timeouts/waits have measured values, not guesses)
- ✅ All external dependencies documented (which APIs? which databases? what network conditions?)
- ✅ Multiple surfaces coordinated (when web + API + DB are all verified)
- ✅ Failure paths tested (not just happy path)

**Example: HIGH Confidence Scenario**
```yaml
scenario: "User logs in with valid email"
confidence: 98  # HIGH
confidence_notes: "All steps explicit, measured timeouts, happy+failure paths"

preconditions:
  - user_exists: true
  - database_operational: true
  - auth_api_responding: true

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
    expected: {status: loaded}
    comment: "Navigate to login page"
  
  - id: step_2
    driver: web-cdp
    action: type
    selector: input[type=email]
    value: test-user@example.com
    expected: {value: "test-user@example.com"}
    comment: "Email field filled with known test account"
  
  - id: step_3
    driver: web-cdp
    action: type
    selector: input[type=password]
    value: TestPassword123!
    expected: {value: "TestPassword123!"}
    comment: "Password field filled"
  
  - id: step_4
    driver: web-cdp
    action: click
    selector: button[text=Login]
    expected: {visible: true}
  
  - id: step_5
    driver: api-http
    action: verify
    endpoint: POST /auth/login
    expected:
      status: 200
      timeout: 3000
      has_field: ["token", "user_id", "email"]
    comment: "API call successful with expected response structure"
  
  - id: step_6
    driver: db-mysql
    action: verify
    query: "SELECT last_login FROM users WHERE email = 'test-user@example.com' LIMIT 1"
    expected:
      has_row: true
      last_login: {is_recent: true}
    comment: "Database verified: login timestamp updated"
  
  - id: step_7
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/dashboard
    expected: {status: 200}
    comment: "Redirect to dashboard successful"
  
  - id: step_8
    driver: web-cdp
    action: getDOM
    selector: .user-greeting, [data-username]
    expected:
      visible: true
      text: {contains: "test-user"}
    comment: "Logged-in username displayed"

---

# Failure path: Invalid password
scenario: "User logs in with invalid password, sees error"
confidence: 96  # HIGH
confidence_notes: "Failure path explicitly tested, error message verified"

preconditions:
  - user_exists: true
  - database_operational: true

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: type
    selector: input[type=email]
    value: test-user@example.com
  
  - id: step_3
    driver: web-cdp
    action: type
    selector: input[type=password]
    value: WrongPassword999!
  
  - id: step_4
    driver: web-cdp
    action: click
    selector: button[text=Login]
  
  - id: step_5
    driver: api-http
    action: verify
    endpoint: POST /auth/login
    expected:
      status: 401
    comment: "API returns 401 Unauthorized"
  
  - id: step_6
    driver: web-cdp
    action: getDOM
    selector: .error-message, [role=alert]
    expected:
      visible: true
      text: {contains: ["Invalid credentials", "wrong password"]}
    comment: "User sees clear error message"
```

Why HIGH? Every step is observable, every timeout is measured, database verified, failure path tested, error handling verified.

---

#### MEDIUM (70-95%): Review Before Execution

You assign MEDIUM confidence when:
- ⚠️ Most steps explicit, but 1-2 ambiguities resolved during translation
- ⚠️ Some timeouts are estimates (not measured, but reasonable)
- ⚠️ Dependencies mostly documented (might be missing one surface)
- ⚠️ Only happy path tested (failure paths not included)

**Example: MEDIUM Confidence Scenario**
```yaml
scenario: "User browses product catalog and adds item to cart"
confidence: 78  # MEDIUM
confidence_notes: "Happy path clear, but missing failure scenarios. API timeout estimated, not measured."

preconditions:
  - user_authenticated: true
  - products_database_operational: true
  - cart_service_operational: true

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/products
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: getDOM
    selector: .product-item
    expected:
      visible: true
      element_count: {min: 1, max: 50}
    comment: "Product list loaded (count based on typical pagination)"
  
  - id: step_3
    driver: web-cdp
    action: click
    selector: "button[text='Add to Cart']"
    comment: "AMBIGUITY: Selector not verified - which product? Using first match"
  
  - id: step_4
    driver: api-http
    action: verify
    endpoint: POST /cart/items
    expected:
      status: 201
      timeout: 2000
    comment: "ESTIMATE: 2s timeout - not measured in production, reasonable for typical operation"
  
  - id: step_5
    driver: web-cdp
    action: getDOM
    selector: .success-message
    expected:
      visible: true
      text: {contains: "Added to cart"}
    comment: "Success feedback displayed"

issues:
  - type: selector_ambiguity
    step: step_3
    details: "Which product should be added? First product assumed, but not specified in original English"
    recommendation: "Specify product name or SKU in original input"
  
  - type: timeout_estimate
    step: step_4
    details: "2s timeout estimated - not measured from production metrics"
    recommendation: "Measure P95 latency in production, use that instead of estimate"
  
  - type: missing_failure_path
    details: "No test for 'what if cart service is down' or 'what if add fails'"
    recommendation: "Add failure scenarios: service unavailable, out of stock, network timeout"
```

Why MEDIUM? Selector is ambiguous (which product?), timeout is estimated not measured, and only happy path tested (no failure scenarios for service down, out of stock, network timeout).

---

#### LOW (<70%): Needs Clarification Before Execution

You assign LOW confidence when:
- ❌ Original English was vague or incomplete
- ❌ Multiple ambiguities exist (timing, counts, ordering, success criteria)
- ❌ Key details missing about preconditions or dependencies
- ❌ Significant assumptions made during translation (marked with many `review_needed: true`)

**Example: LOW Confidence Scenario**
```yaml
scenario: "User completes purchase flow"
confidence: 45  # LOW
confidence_notes: "Original English too vague. Multiple ambiguities. Recommend revisiting PRD with stakeholder."

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/checkout
    expected: {status: loaded}
    comment: "AMBIGUITY: What if user not authenticated? Assumes logged in."
    review_needed: true
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: button[text="Proceed"]
    comment: "AMBIGUITY: Which button? 'Proceed' is vague. Could be 'Proceed to Shipping', 'Next', etc."
    review_needed: true
  
  - id: step_3
    driver: web-cdp
    action: type
    selector: input[name=cardNumber]
    value: 4111111111111111
    comment: "AMBIGUITY: Payment card details. Test card? Real card? Expiry? CVV?"
    review_needed: true
  
  - id: step_4
    driver: web-cdp
    action: click
    selector: button[text="Submit"]
    comment: "AMBIGUITY: When does purchase confirm? After click? After API response? After payment processor response?"
    review_needed: true
    timeout: 5000  # GUESS - no basis for this timeout
  
  - id: step_5
    driver: web-cdp
    action: getDOM
    selector: .confirmation
    expected:
      visible: true
    comment: "AMBIGUITY: What does confirmation look like? Order ID? Email? Page text?"
    review_needed: true

issues:
  - type: missing_preconditions
    details: "Is user authenticated? Is cart populated? Are shipping methods available?"
    recommendation: "Document preconditions: user logged in, cart has 1+ items, shipping address valid"
  
  - type: vague_selectors
    details: "Button selectors like 'Proceed' and 'Submit' are too generic"
    recommendation: "Specify exact button text or use data-testid selectors"
  
  - type: missing_data_spec
    details: "Payment card number is hardcoded without clarity on test vs real"
    recommendation: "Clarify: use Stripe test card, specify expiry/CVV handling"
  
  - type: missing_success_criteria
    details: "What proves purchase succeeded? Order ID in DB? Email sent? Payment confirmed?"
    recommendation: "Define observable outcomes: order in database, email sent, payment status = 'completed'"

recommendation: "HOLD - Do not execute. Schedule review with product team to clarify requirements."
```

Why LOW? Original English "User completes purchase flow" is too vague. Multiple selectors ambiguous, missing preconditions, no clear success criteria, many guesses on timeouts and payment handling.

---

### How to Improve Confidence

| Current Level | Action | Expected Outcome |
|---------------|--------|------------------|
| LOW (< 70%) | Document ambiguities with stakeholder, refine input English | Move to MEDIUM |
| MEDIUM (70-95%) | Measure timeouts in production, add failure path scenarios | Move to HIGH |
| HIGH (95-100%) | Maintain by reviewing every time system changes | Stay HIGH |

---

## Translation Algorithm

### Step 1: Verb Extraction

Parse the English text and extract action verbs:

| Verb | Driver | Action | Purpose |
|------|--------|--------|---------|
| opens | web-cdp | navigate | Load a page |
| sees | web-cdp | getDOM / poll | Verify visibility |
| enters | web-cdp | type | Fill form fields |
| clicks | web-cdp | click | Interact with buttons/links |
| navigates to | web-cdp | navigate | Change URL |
| toggles | web-cdp | click | Toggle switch/checkbox |
| browses | web-cdp | navigate + scroll | Browse content |
| hovers | web-cdp | hover | Trigger hover state |
| scrolls | web-cdp | scroll | Scroll page |
| submits | web-cdp | click | Submit form |
| verifies | web-cdp | getDOM | Assert text/state |
| logs in | web-cdp | type+click+navigate | Complete login flow |
| logs out | web-cdp | click+navigate | Logout flow |
| adds to | web-cdp | click | Add item to cart/list |
| removes | web-cdp | click | Delete/remove action |
| searches for | web-cdp | type+click | Search interaction |

### Step 2: Selector Inference

Infer CSS selectors from action context:

```
Text                                    → Inferred Selector
"clicks login button"                   → button[text=Login], button.login, button#login
"enters email"                          → input[name=email], input[type=email]
"enters password"                       → input[name=password], input[type=password]
"navigates to settings"                 → a[text=Settings], button[text=Settings]
"toggles 2FA"                           → input[type=checkbox], switch[label="2FA"]
"sees success message"                  → .alert-success, .message-success, [role=alert]
"clicks Add to Cart"                    → button[text="Add to Cart"]
"enters search query"                   → input[placeholder*=search]
```

### Step 3: URL Inference

Infer base URLs from navigation context:

```
Text                                    → Inferred URL Pattern
"opens the app"                         → http://localhost:3001/ (app root)
"navigates to login"                    → http://localhost:3001/login
"navigates to settings"                 → http://localhost:3001/settings
"navigates to checkout"                 → http://localhost:3001/checkout
"navigates to dashboard"                → http://localhost:3001/dashboard
"navigates to products"                 → http://localhost:3001/products
```

### Step 4: API Verification Inference

Add backend verification steps based on action type:

```
Action                      → API Endpoint Pattern
"logs in"                   → POST /auth/login
"enables 2FA"               → POST /auth/2fa/enable
"adds to cart"              → POST /cart/items
"proceeds to checkout"      → POST /orders/checkout
"confirms purchase"         → POST /orders/create
"logs out"                  → POST /auth/logout
"submits form"              → POST /[resource]/create or PATCH /[resource]/update
```

### Step 5: Database Verification (Optional)

If schema is known, add DB verification:

```
Action                      → DB Query Pattern
"logs in"                   → SELECT * FROM users WHERE email = ? (verify password updated)
"enables 2FA"               → SELECT * FROM users WHERE id = ? (verify 2fa_enabled = true)
"adds to cart"              → SELECT * FROM cart_items WHERE user_id = ? (count increased)
"confirms purchase"         → SELECT * FROM orders WHERE user_id = ? (verify status = 'pending')
```

### Step 6: YAML Generation

Generate complete YAML with:
- Unique step IDs (step_1, step_2, etc.)
- Driver specifications (web-cdp, api-http, db-mysql)
- Action details (selector, value, expected results)
- Comments explaining inferred decisions
- Sensible defaults (30s timeout, visible:true expectation)

## Golden Rules of Translation

These 5 rules are the foundation of precision YAML scenarios. Violations are the #1 source of flaky, unreliable tests.

### Rule 1: Explicit Preconditions

**State all assumptions before any step.**

❌ **Bad: Implicit preconditions**
```yaml
steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/dashboard
    comment: "Navigate to dashboard"
```
Why bad? The scenario assumes the user is authenticated. If they're not, navigation will redirect to login, and the test will fail mysteriously.

✅ **Good: Explicit preconditions**
```yaml
preconditions:
  - user_is_authenticated: true
  - auth_token_valid: true
  - user_has_profile_completed: true  # Dashboard requires profile data

steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/dashboard
    expected: {status: 200}
    comment: "Navigate to dashboard (requires authenticated user with completed profile)"
```

**Apply this rule:**
- Before step 1, list ALL assumptions about system state
- Include: user authentication, database records, configuration flags, external service availability
- If a step requires specific data, document it in preconditions

---

### Rule 2: Observable Postconditions

**Every step's success must be observable (not assumed).**

❌ **Bad: Assumed success**
```yaml
steps:
  - id: step_1
    action: type
    selector: input[type=email]
    value: user@example.com
    comment: "Enter email"
  
  - id: step_2
    action: click
    selector: button[text=Submit]
    comment: "Click submit"
  
  - id: step_3
    action: navigate
    target: http://localhost:3001/dashboard
    comment: "Navigate to dashboard"
```
Why bad? After clicking submit (step 2), we assume the form submitted successfully and navigation completed. But what if:
- Form validation failed? (network latency, validation error)
- API call failed? (500 error)
- User was redirected elsewhere? (permission denied)

❌ **Better: Verify API response**
```yaml
steps:
  - id: step_1
    action: type
    selector: input[type=email]
    value: user@example.com
    expected: {value: "user@example.com"}
  
  - id: step_2
    action: click
    selector: button[text=Submit]
  
  - id: step_3
    action: verify
    endpoint: POST /profile/setup
    expected: {status: 200}
    comment: "API call succeeded"
  
  - id: step_4
    action: navigate
    target: http://localhost:3001/dashboard
    expected: {status: 200}
```

✅ **Best: Verify UI state AND backend state**
```yaml
steps:
  - id: step_1
    action: type
    selector: input[type=email]
    value: user@example.com
    expected: {value: "user@example.com"}
    comment: "Email field has correct value"
  
  - id: step_2
    action: click
    selector: button[text=Submit]
    expected: {visible: true}
    comment: "Submit button clicked"
  
  - id: step_3
    driver: api-http
    action: verify
    endpoint: POST /profile/setup
    expected: {status: 200}
    comment: "API accepted submission"
  
  - id: step_4
    driver: db-mysql
    action: verify
    query: "SELECT email FROM profiles WHERE user_id = ? LIMIT 1"
    expected: {email: "user@example.com"}
    comment: "Database persisted the change"
  
  - id: step_5
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/dashboard
    expected: {status: 200}
  
  - id: step_6
    driver: web-cdp
    action: getDOM
    selector: .profile-card
    expected:
      visible: true
      text: {contains: "user@example.com"}
    comment: "UI renders persisted change"
```

**Apply this rule:**
- After every action, add `expected` field with observable outcome
- Include: HTTP status codes, element visibility, text content, database state, API response structure
- If you can't observe it, you can't verify it passed

---

### Rule 3: No Implicit State

**All state changes must be explicitly verified (DB, cache, search index, etc).**

❌ **Bad: Implicit state changes**
```yaml
steps:
  - id: step_1
    action: click
    selector: button[text="Add to Cart"]
    comment: "Add item to cart"
  
  - id: step_2
    action: navigate
    target: http://localhost:3001/cart
    comment: "View cart"
  
  - id: step_3
    action: getDOM
    selector: .cart-item
    expected: {visible: true}
    comment: "Item visible in cart UI"
```
Why bad? We verify the UI shows the item, but we don't verify:
- Item was persisted to database (API could have failed, but UI cached it locally)
- Inventory was decremented (double-add could happen)
- Cart total price is correct (price calculation could be wrong)

✅ **Good: Explicit state verification**
```yaml
steps:
  - id: step_1
    action: click
    selector: button[text="Add to Cart"]
  
  - id: step_2
    driver: api-http
    action: verify
    endpoint: POST /cart/items
    expected: {status: 201}
    comment: "API persisted item to cart"
  
  - id: step_3
    driver: db-mysql
    action: verify
    query: "SELECT COUNT(*) as count FROM cart_items WHERE user_id = ? LIMIT 1"
    expected: {count: {min: 1}}
    comment: "Database shows item in cart"
  
  - id: step_4
    driver: api-http
    action: verify
    endpoint: GET /inventory?product_id=123
    expected:
      available_quantity: {lt: 100}  # Was 100, now < 100 due to add
    comment: "Inventory decremented"
  
  - id: step_5
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/cart
    expected: {status: 200}
  
  - id: step_6
    driver: web-cdp
    action: getDOM
    selector: .cart-item
    expected:
      visible: true
      text: {contains: "$99.99"}  # Explicit price verification
    comment: "Cart item visible with correct price"
```

**Apply this rule:**
- Never assume state changed just because a UI element appeared
- Verify across boundaries: API → database → cache → UI
- Include state checks for: database records, search index documents, cache values, inventory counts

---

### Rule 4: Timing is Evidence

**Every timeout/wait value is a performance claim.**

❌ **Bad: Arbitrary timeouts**
```yaml
steps:
  - id: step_1
    action: click
    selector: button[text="Search"]
  
  - id: step_2
    action: wait
    duration: 5000  # Why 5s? Guessed?
    comment: "Wait for results"
  
  - id: step_3
    action: getDOM
    selector: .search-results
    expected: {visible: true}
```
Why bad? 5000ms is arbitrary. When your test fails with "results not visible after 5s," was the timeout too short, or is the API actually slow?

✅ **Good: Measured, documented timeouts**
```yaml
steps:
  - id: step_1
    action: click
    selector: button[text="Search"]
    comment: "Click search button"
  
  - id: step_2
    driver: api-http
    action: verify
    endpoint: GET /search?q=laptop
    expected:
      status: 200
      timeout: 3000  # Based on production metrics: P95 = 2.8s
    comment: "Search API response (P95 latency = 2.8s from production logs)"
  
  - id: step_3
    driver: web-cdp
    action: wait
    duration: 3000  # Consistent with API timeout
    comment: "Wait for results to render (P95 render time = 200ms, total P95 = 3s)"
  
  - id: step_4
    driver: web-cdp
    action: getDOM
    selector: .search-results
    expected:
      visible: true
      timeout: 500
    comment: "Results visible within expected timeframe"

metadata:
  performance_notes: "Based on production SLO: API P95=2.8s, render P95=200ms, total P95=3s"
  measurement_source: "DataDog APM logs, week of 2024-04-01"
  alert_threshold: "If search takes > 5s (P99), page should show 'search still loading' message"
```

**Apply this rule:**
- Every timeout/wait should reference measured data (production logs, APM metrics, load test results)
- Document where the number came from (DataDog, CloudWatch, custom metrics, manual testing)
- If you don't have metrics yet, estimate conservatively (e.g., 5s for unknown APIs) and mark for measurement
- Include performance expectations in metadata for future reference

---

### Rule 5: Failure is Data

**Translate both happy path AND documented failure cases.**

❌ **Bad: Only happy path**
```yaml
scenario: "User resets password"
steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/reset-password
  - id: step_2
    action: type
    selector: input[type=email]
    value: user@example.com
  - id: step_3
    action: click
    selector: button[text="Send Reset Link"]
  - id: step_4
    action: verify
    endpoint: POST /auth/reset-password
    expected: {status: 200}
```
Why bad? Only tests the happy path. What about:
- User account doesn't exist? (API returns 404)
- Email service is down? (API returns 503)
- Rate limiting triggered? (API returns 429)

✅ **Good: Happy + failure paths**

**Happy path scenario:**
```yaml
scenario: "User resets password successfully"
tags: [auth, password-reset, happy-path]

steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/reset-password
    expected: {status: 200}
  - id: step_2
    action: type
    selector: input[type=email]
    value: user@example.com
    expected: {value: "user@example.com"}
  - id: step_3
    action: click
    selector: button[text="Send Reset Link"]
  - id: step_4
    action: verify
    endpoint: POST /auth/reset-password
    expected:
      status: 200
      has_field: ["reset_token"]
  - id: step_5
    action: getDOM
    selector: .message-success
    expected:
      visible: true
      text: {contains: "Check your email"}
```

**Failure path 1: User doesn't exist**
```yaml
scenario: "User tries to reset password for non-existent account"
tags: [auth, password-reset, error-path]

preconditions:
  - account_does_not_exist: true

steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/reset-password
  - id: step_2
    action: type
    selector: input[type=email]
    value: nonexistent@example.com
  - id: step_3
    action: click
    selector: button[text="Send Reset Link"]
  - id: step_4
    action: verify
    endpoint: POST /auth/reset-password
    expected:
      status: 404
  - id: step_5
    action: getDOM
    selector: .message-error
    expected:
      visible: true
      text: {contains: ["No account found", "Check your email"]}  # UX: Don't reveal if account exists
    comment: "Security: Server returns 404, but UI shows safe message"
```

**Failure path 2: Email service down**
```yaml
scenario: "Password reset requested, but email service is down"
tags: [auth, password-reset, error-path]

preconditions:
  - email_service_status: down
  - user_exists: true

steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/reset-password
  - id: step_2
    action: type
    selector: input[type=email]
    value: user@example.com
  - id: step_3
    action: click
    selector: button[text="Send Reset Link"]
  - id: step_4
    action: verify
    endpoint: POST /auth/reset-password
    expected:
      status: 503
  - id: step_5
    action: getDOM
    selector: .message-error
    expected:
      visible: true
      text: {contains: ["temporarily unavailable", "try again later"]}
    comment: "User informed of service unavailability, not asked to retry immediately"
```

**Failure path 3: Rate limiting**
```yaml
scenario: "Password reset rate limited after multiple attempts"
tags: [auth, password-reset, error-path, rate-limiting]

preconditions:
  - user_attempts_reset_5_times: true  # Already triggered rate limit

steps:
  - id: step_1
    action: navigate
    target: http://localhost:3001/reset-password
  - id: step_2
    action: type
    selector: input[type=email]
    value: user@example.com
  - id: step_3
    action: click
    selector: button[text="Send Reset Link"]
  - id: step_4
    action: verify
    endpoint: POST /auth/reset-password
    expected:
      status: 429
  - id: step_5
    action: getDOM
    selector: .message-error
    expected:
      visible: true
      text: {contains: "Too many requests", "try again in"}
    comment: "User informed of rate limit with retry window"
```

**Apply this rule:**
- For each happy-path scenario, create failure-path variants for:
  - Missing data (user doesn't exist, invalid input)
  - Service failure (API down, timeout, 500 error)
  - Rate limiting / quota exceeded
  - Permission denied (user not authorized)
  - Dependency failure (database, cache, search index down)
- Test that error messages are user-friendly and actionable
- Verify system degrades gracefully (no blank page, no exception stack trace)

---

## Translation Rules

### Basic Rules

1. **Each sentence = one or more steps** (verb extracts to action)
2. **Navigation always includes load verification** (expected: {status: loaded})
3. **Form fills include type+verify** (type action + expected value verification)
4. **Button clicks include visibility check** (expected: {visible: true})
5. **Login always includes API verification** (POST /auth/login → {status: 200})

### Data Extraction Rules

Extract and track data mentioned in text:

```
"enters email=john@example.com"         → email: "john@example.com"
"enters password=secret123"             → password: "secret123"
"enters phone number +1-555-0100"       → phone: "+1-555-0100"
"searches for 'laptop'"                 → query: "laptop"
"adds 3 items"                          → quantity: 3
```

### Contextual Inference

- **After login, assume authenticated**: subsequent navigations expect 200 status
- **After add-to-cart, assume item in cart**: verify via DB or GET /cart
- **After purchase, assume order created**: verify via DB or GET /orders
- **After logout, assume unauthenticated**: subsequent navigations expect redirect or 401

### Error Handling

If inference is ambiguous:
1. Use most common selector pattern
2. Add inline comment: `# INFER: selector not specified, using pattern X`
3. Mark for human review with `review_needed: true`
4. Suggest alternatives in comment

## Example 1: Simple Login Flow

**Input:**
```
User logs in with email=john@example.com and password=secret123,
then navigates to settings and enables 2FA
```

**Output:**
```yaml
scenario: "User logs in and enables 2FA"
description: "Login with credentials, navigate to settings, enable 2FA"
tags: [authentication, security]

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
    expected: {status: loaded}
    comment: "INFER: Navigate to login page"
  
  - id: step_2
    driver: web-cdp
    action: type
    selector: input[type=email]
    value: john@example.com
    expected: {value: "john@example.com"}
    comment: "INFER: Enter email into email input"
  
  - id: step_3
    driver: web-cdp
    action: type
    selector: input[type=password]
    value: secret123
    expected: {value: "secret123"}
    comment: "INFER: Enter password into password input"
  
  - id: step_4
    driver: web-cdp
    action: click
    selector: button[text=Login]
    expected: {visible: true}
    comment: "INFER: Click login button"
  
  - id: step_5
    driver: api-http
    action: verify
    endpoint: POST /auth/login
    expected: {status: 200}
    comment: "INFER: Verify login API call succeeded"
  
  - id: step_6
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings
    expected: {status: loaded}
    comment: "INFER: Navigate to settings page"
  
  - id: step_7
    driver: web-cdp
    action: click
    selector: input[type=checkbox][label*="2FA"], switch[label*="2FA"]
    expected: {checked: true}
    comment: "INFER: Toggle 2FA checkbox"
    review_needed: true
    review_reason: "2FA selector pattern ambiguous, suggest user verify"
  
  - id: step_8
    driver: api-http
    action: verify
    endpoint: POST /auth/2fa/enable
    expected: {status: 201}
    comment: "INFER: Verify 2FA enable API call"
```

## Example 2: E-Commerce Purchase Flow

**Input:**
```
Scenario: Complete purchase flow
1. User logs in with valid credentials
2. User browses products page
3. User adds laptop to cart
4. User proceeds to checkout
5. User enters payment details: card=4111111111111111
6. User confirms purchase
7. Order confirmation appears with status "Processing"
```

**Output:**
```yaml
scenario: "Complete purchase flow"
description: "E-commerce purchase from login to confirmation"
tags: [ecommerce, payment, checkout]

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/login
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: click
    selector: input[type=email]
    expected: {focused: true}
  
  - id: step_3
    driver: web-cdp
    action: type
    selector: input[type=email]
    value: user@example.com
    comment: "INFER: Default test email"
  
  - id: step_4
    driver: web-cdp
    action: type
    selector: input[type=password]
    value: password123
    comment: "INFER: Default test password"
  
  - id: step_5
    driver: web-cdp
    action: click
    selector: button[text=Login]
  
  - id: step_6
    driver: api-http
    action: verify
    endpoint: POST /auth/login
    expected: {status: 200}
  
  - id: step_7
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/products
    expected: {status: loaded}
    comment: "INFER: Browse products page"
  
  - id: step_8
    driver: web-cdp
    action: scroll
    selector: html
    direction: down
    distance: 500
    comment: "INFER: Scroll to find laptop product"
  
  - id: step_9
    driver: web-cdp
    action: click
    selector: button[text="Add to Cart"], a[text*=laptop]
    expected: {visible: true}
    comment: "INFER: Add laptop to cart - selector ambiguous, suggest user verify"
    review_needed: true
  
  - id: step_10
    driver: api-http
    action: verify
    endpoint: POST /cart/items
    expected: {status: 201}
    comment: "INFER: Verify item added to cart via API"
  
  - id: step_11
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/checkout
    expected: {status: loaded}
  
  - id: step_12
    driver: web-cdp
    action: type
    selector: input[name=cardNumber]
    value: 4111111111111111
    comment: "INFER: Enter payment card number"
    review_needed: true
    review_reason: "Payment input is sensitive - verify this is test card in test environment"
  
  - id: step_13
    driver: web-cdp
    action: click
    selector: button[text="Confirm Purchase"], button[text=Submit]
    expected: {visible: true}
    comment: "INFER: Submit purchase"
  
  - id: step_14
    driver: api-http
    action: verify
    endpoint: POST /orders/create
    expected: {status: 201}
  
  - id: step_15
    driver: web-cdp
    action: getDOM
    selector: .order-confirmation, [role=alert]
    expected:
      visible: true
      text: "Processing"
    comment: "INFER: Verify order confirmation with Processing status"
```

## Example 3: Account Settings Flow

**Input:**
```
User opens settings, sees their current name "John Doe",
changes it to "Jane Smith", enables email notifications,
disables SMS notifications, saves changes, sees success message.
```

**Output:**
```yaml
scenario: "Update account settings"
description: "Modify profile and notification preferences"
tags: [settings, profile, preferences]

steps:
  - id: step_1
    driver: web-cdp
    action: navigate
    target: http://localhost:3001/settings
    expected: {status: loaded}
  
  - id: step_2
    driver: web-cdp
    action: getDOM
    selector: input[name=fullName]
    expected: {value: "John Doe"}
    comment: "INFER: Verify current name displayed"
  
  - id: step_3
    driver: web-cdp
    action: triple_click
    selector: input[name=fullName]
    comment: "INFER: Select all text in name field"
  
  - id: step_4
    driver: web-cdp
    action: type
    selector: input[name=fullName]
    value: Jane Smith
    expected: {value: "Jane Smith"}
  
  - id: step_5
    driver: web-cdp
    action: click
    selector: input[name=emailNotifications], input[id=emailNotifs]
    expected: {checked: true}
    comment: "INFER: Enable email notifications"
    review_needed: true
  
  - id: step_6
    driver: web-cdp
    action: click
    selector: input[name=smsNotifications], input[id=smsNotifs]
    expected: {checked: false}
    comment: "INFER: Disable SMS notifications"
    review_needed: true
  
  - id: step_7
    driver: web-cdp
    action: click
    selector: button[text=Save], button[text="Save Changes"]
    expected: {visible: true}
  
  - id: step_8
    driver: api-http
    action: verify
    endpoint: PATCH /settings
    expected: {status: 200}
  
  - id: step_9
    driver: web-cdp
    action: getDOM
    selector: .alert-success, [role=alert][text*=success]
    expected: {visible: true, text: "success"}
    comment: "INFER: Verify success message appeared"
```

## Human Review Checklist

After translation, the human reviewer should verify:

- [ ] All selectors are correct (run with actual app if needed)
- [ ] All URLs match actual app routes
- [ ] API endpoints match actual backend routes
- [ ] Data values are sensible (valid email, phone, etc.)
- [ ] Expected results are testable
- [ ] Timeouts are reasonable (30s default, 60s for slow operations)
- [ ] Comments explain non-obvious inferences
- [ ] No sensitive data in YAML (use placeholders)
- [ ] Steps flow logically (auth before protected routes)
- [ ] Both UI and API verifications included where appropriate

## Configuration & Defaults

```yaml
defaults:
  timeout: 30000  # 30 seconds per step
  retry_count: 1
  polling_interval: 500  # ms
  base_url: http://localhost:3001
  
selector_patterns:
  button: ["button[text=X]", "button.X", "button#X"]
  input: ["input[type=X]", "input[name=X]", "input[id=X]"]
  link: ["a[text=X]", "a.X", "a[href*=X]"]
  
api_patterns:
  login: "POST /auth/login"
  logout: "POST /auth/logout"
  create_resource: "POST /{resource}"
  update_resource: "PATCH /{resource}/{id}"
  delete_resource: "DELETE /{resource}/{id}"
```

## Usage in Eval Framework

Generated YAML is directly executable by eval-driver-web-cdp and eval-driver-api-http:

```bash
eval-run --scenario translated_scenario.yaml --driver web-cdp,api-http
```

Steps marked with `review_needed: true` should be manually verified before execution.

## Tips for Non-Technical Authors

- Use complete sentences: "User clicks the login button" not "click login"
- Be specific about data: "enters email user@example.com" not "enters email"
- Describe what the user sees: "sees home screen" helps infer navigation
- Use common action words (opens, sees, enters, clicks, navigates)
- Mention expected results: "sees success message" generates verification step
- Group related actions: "logs in" handles multiple sub-steps automatically

## Future Enhancements

- [ ] Multi-language support (translate to English first, then to YAML)
- [ ] Template library (common flows like login, checkout, search)
- [ ] Visual selector picker (integrate browser DevTools)
- [ ] Scenario parameterization (reuse with different data)
- [ ] Conditional steps (if element exists, then...)
- [ ] Parallel step execution (independent steps run concurrently)
- [ ] Screenshot capture on failure
- [ ] Performance assertions (step completes in < X ms)

## Checklist

Before submitting a translated YAML scenario:

- [ ] Every `expected:` field contains a concrete, machine-verifiable value (no prose like "user sees their order")
- [ ] One YAML scenario per user journey (no multi-flow scenarios)
- [ ] At least one failure or error path scenario generated alongside every happy path
- [ ] All element selectors use `data-testid`, ARIA role, or stable aria-label (not CSS classes)
- [ ] All drivers verified against `forge-product.md` eval stack before generating
- [ ] No vague English terms preserved ("eventually", "somehow", "at some point")
- [ ] Scenario committed to brain before eval is invoked
