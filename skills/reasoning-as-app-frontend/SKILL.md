---
name: reasoning-as-app-frontend
description: WHEN: Council is reasoning about a PRD. You are the app perspective (React Native/Kotlin/Swift). Analyze the PRD for mobile UI, API endpoints, offline-first patterns, native constraints, push notifications, device storage, version compatibility, sync conflicts, and platform-specific data persistence.
type: rigid
requires: [brain-read, reasoning-as-backend, reasoning-as-infra]
---

# Reasoning as App Frontend

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "This feature doesn't have a mobile component" | Every API change affects mobile. Even "backend-only" features may change response shapes, add fields, or alter error codes that the app consumes. |
| "The app will just call the same API as web" | Mobile has offline-first, bandwidth constraints, battery impact, and push notification requirements that web doesn't. Same API ≠ same contract. |
| "We'll handle offline later" | "Later" means a retrofit that touches every screen. Offline-first is an architectural decision, not a feature you bolt on. |
| "Platform differences are minor" | Android and iOS have different lifecycle models, permission flows, storage APIs, and push notification systems. "Minor" differences cause major bugs. |
| "The API versioning doesn't affect us" | Mobile apps can't force-update. Old app versions will call old API versions for months. Version compatibility is a mobile-first concern. |

**If you are thinking any of the above, you are about to violate this skill.**

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **App surface says "same as web" without separate offline analysis** — Mobile and web have fundamentally different connectivity patterns. STOP. Produce explicit offline-first analysis regardless of what web surface said.
- **API versioning compatibility is not analyzed** — App versions linger in production for months. STOP. Specify minimum supported API version, deprecation handling, and force-update thresholds before spec freeze.
- **Push notification payload schema is absent** — Notification payloads are contracts. Changes break older app versions. STOP. Define the full notification payload schema before locking.
- **Platform differences (iOS vs Android) are not documented** — Permission flows, storage APIs, and lifecycle models differ significantly. STOP. Address both platforms explicitly or flag which is in scope.
- **Sync conflict resolution strategy is "TBD"** — Offline-first with no conflict resolution creates silent data loss. STOP. Define conflict resolution strategy (last-write-wins, server-authoritative, CRDT) before spec freeze.
- **App surface reasoning depends on backend API shape before backend surface has finished** — Unilateral assumption creates mismatched contracts. STOP. Run surfaces in parallel; resolve conflicts in negotiation.
- **Battery and bandwidth impact is not assessed** — Features that drain battery or consume excessive bandwidth will be rejected by users. STOP. State explicit constraints before locking.

You are the mobile app team (Android/iOS). Given a locked PRD, reason about user-facing behavior, data consistency, offline capabilities, and platform constraints. This reasoning focuses on the app frontend's role in distributed system reliability.

## 1. Screens & Navigation

What screens? What flows?

Example:
- PRD: "Users can log in with 2FA"
- App says: "Login screen → 2FA setup screen (enable, show codes) → 2FA verify screen (code entry, SMS fallback) → home screen"

**Offline consideration:** Which screens remain usable offline? Which require fresh server state?

## 2. API Endpoints

What endpoints required? What versions?

Example:
- POST /auth/2fa/enable (v2)
- POST /auth/2fa/verify (v2)
- GET /auth/status (v2)

**Versioning consideration:** What is the app's minimum API version support? When can old versions be dropped?

## 3. Offline-First Sync

What's cached locally? How does it sync? How are conflicts resolved?

Example:
- User profile: cached, sync on auth, conflict resolution: server-wins
- 2FA status: sync on auth, cache 24h, no local writes (read-only)
- Recovery codes: encrypted local storage, manual refresh only
- Transaction log: event sourcing for local mutations

**Sync consideration:** See "Offline-First Sync Decision Tree" below for conflict strategy selection.

## 4. Native Constraints

iOS/Android specifics?

Example:
- iOS: Keychain for secrets, Face ID for 2FA, background app refresh restricted
- Android: Keystore, biometric for 2FA, JobScheduler for background sync
- Background: No background sync for time-sensitive data (2FA), ok for non-critical (cached profiles)

**Storage consideration:** See "Platform-Specific Constraints" section below.

## 5. Push Notifications

Any push triggers?

Example:
- "2FA enabled on device X" alert
- Sync conflict notification (user action required)
- Server-initiated data refresh request

**Reliability consideration:** Push delivery is best-effort; app must poll on cold start to detect missed events.

---

## 6. Edge Cases & Handling Strategies

### Edge Case: Offline Data Conflicts (Local Changes + Server Changes)

**Scenario:** User edits profile offline (name, email). While offline, an admin changes their role via backend. When device reconnects, both changes are pending sync.

**What if this happens?**
- User made local mutation: {name: "Jane", email: "jane@example.com"}
- Server now has: {name: "Jane Smith", email: "jane.smith@example.com", role: "admin"}
- Naive merge = data corruption or lost admin role change

**Action: Conflict Resolution Strategy**

Choose approach based on data semantics (in backend contract, reasoning-as-backend):

1. **Server-Wins (Safe Default)**
   - When: Authoritative state is server (role, permissions, billing info)
   - Action: Discard local mutations, refresh from server
   - User notification: "Your profile was updated by admin. Changes made on this device were discarded."
   - Pseudocode:
     ```
     if localChanges.timestamp > lastSyncTime:
       if criticalField(field) or role.changed():
         discardLocalChanges(field)
         showNotification("Admin changed your role, discarding local edits")
       else:
         mergeClientWins(field)  // non-critical: name, preference
     else:
       applyServerState()
     ```

2. **Client-Wins (Rare, Requires Idempotency)**
   - When: Client mutation is idempotent and safe (like/unlike, follow/unfollow)
   - Action: Apply local mutations, queue for server
   - Requirement: Backend must handle idempotent replays without side effects
   - Pseudocode:
     ```
     if isIdempotent(localMutation):
       applyLocal()
       queueForRetry()
     ```

3. **Conflict Resolution (CRDTs or Event Log)**
   - When: Both client and server make non-overlapping changes
   - Action: Merge non-conflicting fields, escalate conflicts to user
   - Pseudocode:
     ```
     serverChanges = fetchServer()
     conflicts = findConflicts(localMutations, serverChanges)
     nonConflicts = merge(localMutations, serverChanges)
     
     if conflicts:
       showConflictUI(conflicts, allow_user_choice)
     else:
       applyMerge(nonConflicts)
     ```

**Escalation Path:**
- If conflict affects permissions/billing: FLAG as blocker, show manual resolution UI
- If conflict affects non-critical data (preferences): Use server-wins silently, log event
- If local mutations are lost: Offer undo stack (24h retention) to user

**Related:** reasoning-as-backend (server-side idempotency keys), Forge Decision D14 (persuasion: explain what happened)

---

### Edge Case: API Version Mismatch (Old App + New API)

**Scenario:** User installs app v1.5 (expects /auth/v2 endpoints with optional fields). Backend rolls out v3 API (deprecated v2, some endpoints removed, new required fields in v3).

**What if this happens?**
- App sends POST /auth/v2/verify with v2 schema (no `environment` field)
- API returns 400 Bad Request (v3 now requires `environment`)
- App crashes if not handled gracefully

**Action: Graceful Degradation**

1. **Version Negotiation at Auth**
   ```
   POST /health/versions
   Response:
   {
     "minimum_app_version": "1.5",
     "current_api_version": "v3",
     "deprecated_versions": ["v1"],
     "feature_flags": {
       "biometric_2fa": true,
       "backup_codes": true,
       "sso": false  // coming in v3.1
     }
   }
   ```
   - App checks: if local_version < minimum_app_version, show force-upgrade banner
   - App queries feature flags before attempting new features

2. **Endpoint Compatibility Layer**
   ```
   // If app detects v2 endpoint returns 410 Gone:
   fallback(v2Endpoint) {
     logDeprecation("Endpoint will stop working in 30 days")
     showAlertOnce("Please update the app", dismissible=true)
     
     // For critical paths (login), offer automatic app update
     if criticalPath:
       triggerBackgroundAppStoreUpdate()
   }
   ```

3. **Schema Versioning**
   ```
   // Instead of strict schema validation, use optional fields:
   POST /auth/v2/verify
   {
     "code": "123456",
     "device_id": "...",
     "environment": "mobile"  // NEW in v3, but optional in v2
   }
   
   // App sends both v2 and v3 fields, API uses what it needs
   ```

**Escalation Path:**
- If user's app is below minimum version: BLOCKER, force upgrade via AppStore
- If optional field missing but endpoint works: WARN in logs, no user notification
- If schema incompatible but app old: Show "Update available" banner (non-blocking)

**Related:** reasoning-as-backend (API versioning contracts), Forge Decision D14 (authority: document deprecation timelines)

---

### Edge Case: Network Recovery After Extended Offline

**Scenario:** User's app goes offline for 8 hours (flight, subway). When device reconnects, local cache has 200 pending mutations (messages sent, profile edits, likes). Server state has evolved significantly. Which mutations are still valid? Which conflict?

**What if this happens?**
- Local: user sent message to john@example.com (now deleted account)
- Server: john@example.com no longer exists
- Local: user liked post_id=123, post since deleted by admin
- App tries to replay all 200 mutations: 50+ will fail or conflict

**Action: Intelligent Replay Strategy**

1. **Batch Validation Before Sync**
   ```
   onNetworkRestored() {
     pendingMutations = getLocalQueue()
     
     // GET /sync/validate (batch check which mutations are still applicable)
     validMutations = api.validateBatch(pendingMutations)
     
     // Categorize:
     stillValid = filter(m => validMutations[m.id] == "ok")
     conflicted = filter(m => validMutations[m.id] == "conflict")
     obsolete = filter(m => validMutations[m.id] == "not_found")
     
     // Process each category
     replayMutations(stillValid)
     showConflictResolution(conflicted)
     archiveObsolete(obsolete, allow_undo=24h)
   }
   ```

2. **Merge Local Mutations with Server Changes**
   ```
   // Scenario: User cached message list [msg1, msg2] offline
   // During offline, server delivered msg3, msg4 via push (but app wasn't listening)
   
   onNetworkRestored() {
     localMessages = cache.get("messages")  // [msg1, msg2]
     
     // Fetch server version with version cursors
     serverMessages = api.getMessages(cursor=lastSyncCursor)  
     // Returns: [msg1, msg2, msg3, msg4] with metadata
     
     // Merge: server is authoritative for received messages
     // but local drafts are preserved
     merged = mergeLists(localMessages, serverMessages, comparator=timestamp)
     
     // Local mutations take precedence if not yet synced
     finalState = overlay(merged, pendingMutations)
   }
   ```

3. **Ordering & Causality**
   ```
   // Problem: User A sends message to B, then blocks B
   // In offline replay, mutations might be reversed in order
   
   // Solution: Use logical clocks or causality tracking
   mutation = {
     id: uuid,
     timestamp: clockTimestamp,
     causality: [uuid_of_prev_mutation],  // DAG, not array
     operation: "send_message | block_user"
   }
   
   // Replay in topological order (respect causality, not just timestamp)
   replayInTopologicalOrder(pendingMutations)
   ```

**Escalation Path:**
- If >50% of mutations conflict: WARN user "Many local changes couldn't be applied"
- If critical mutation fails (payment, permission): BLOCKER, show manual retry
- If message delivery failed (recipient deleted): Show as "Undeliverable" in UI, allow delete or retry

**Related:** reasoning-as-infra (event ordering, causality), brain-write (log each decision to retry)

---

### Edge Case: Local Storage Constraints (App vs OS Limits)

**Scenario:** App caches profile data, messages, offline-first drafts. On mid-range Android device with 32GB storage, 8GB available.

User has:
- 50,000 messages in cache (4GB)
- 1,000 profile images (2GB)
- 500 draft documents (1.5GB)
- App binary (500MB)
- Remaining available: ~4GB

**What if this happens?**
- New version of app downloaded: 600MB
- OS reserves space for system updates: 2GB
- Available drops below 2GB
- SQLite refuses to grow, app crashes when writing cache
- Image thumbnails can't be generated (temp storage full)

**Action: Proactive Storage Management**

1. **Multi-Tier Storage Strategy**
   ```
   // Tier 1: Critical (must keep)
   /data/data/app/cache/critical/
     - auth tokens (encrypted, small)
     - user identity (small)
     - sync state metadata (small)
   Size: <50MB
   
   // Tier 2: Hot (recent, actively used)
   /data/data/app/cache/hot/
     - last 30 messages (compressed)
     - current conversation threads
     - user's own profile
   Size: 100-500MB (configurable)
   
   // Tier 3: Cold (old, low-value)
   /data/data/app/cache/cold/
     - archive of old messages
     - old profile images
     - historical data
   Size: unlimited (but on external storage if available)
   
   // Tier 4: Temp (volatile)
   /data/data/app/cache/temp/
     - image processing
     - draft serialization
     - thumbnails
   Size: auto-purge when <50MB free
   ```

2. **Storage Quotas & Eviction**
   ```
   onWrite(data, tier) {
     usedStorage = calculateStorageUsed()
     
     if usedStorage > QUOTA[tier]:
       // Evict by LRU
       evictOldest(tier, count=10)
       
       if usedStorage > QUOTA[tier] * 0.9:
         // Still over: escalate
         notifyUser("App storage is full. Some old messages will be deleted.")
         evictOldest(tier, count=100)
         
         if usedStorage > HARD_LIMIT:
           // Emergency: delete cold tier
           deleteColdCache()
     
     write(data)
   }
   
   onAppStart() {
     freeStorage = getDeviceFreeStor ()
     if freeStorage < 500MB:
       showBanners("Device storage low, some features limited")
       disableColdCacheFetch()
   }
   ```

3. **Encryption Implications**
   ```
   // Problem: SQLCipher encrypted database uses 2x space
   // Solution: Smart selection of what to encrypt
   
   critical.db (encrypted):
     auth tokens, private messages, sensitive user data
   
   noncritical.db (unencrypted):
     public posts, user profile photos, shared docs
     // Can be regenerated from server anyway
   
   // iOS: Keychain only stores secrets (<100KB)
   // Larger data: use encrypted CoreData
   ```

4. **Cleanup Strategies**
   ```
   // Automatic cleanup on install update
   onAppUpdate() {
     if previousVersion < "2.0":
       deleteOldCacheFormat()  // 300MB freed
       optimizeDatabaseSchema()
       deleteUnusedAssets()
       migrateToNewEncryption()
   }
   
   // User-initiated cleanup
   showSettings() {
     totalUsed = calculateStorageUsed()
     breakdown = {
       messages: "2.1GB",
       images: "1.8GB",
       documents: "0.5GB",
       temporary: "0.2GB"
     }
     
     // Allow user to clear by category
     button("Clear old messages >60 days", frees="900MB")
     button("Clear thumbnails", frees="300MB")
   }
   ```

**Escalation Path:**
- If device free storage <200MB: WARN user, disable new data fetches
- If app can't write critical data: BLOCKER, show "Storage full" error, suggest cleanup
- If encryption fails due to space: BLOCKER, urgent cleanup required

**Related:** reasoning-as-infra (storage tiers), platform-specific section below

---

### Edge Case: Background Sync vs Foreground App State Divergence

**Scenario:** iOS app with background fetch enabled (iOS 13+). 

Timeline:
- 2:00 PM: User closes app after viewing messages
- 2:15 PM: OS grants background fetch, app syncs silently
- 2:15 PM: Server has new message from Alice
- 2:20 PM: User opens app in foreground
- Foreground: displays old message list (didn't refresh yet)
- Foreground: User drafts reply to Alice
- Background sync completes in parallel, inserts Alice's message
- Race condition: draft was in response to old state

**What if this happens?**
- Background thread inserts new message into cache while foreground reads it
- Foreground thread writes draft with wrong thread_id or order
- User's draft appears in wrong context
- Both threads modify cache simultaneously (SQLite lock contention)

**Action: Explicit Sync Serialization**

1. **Sync State Machine**
   ```
   enum SyncState {
     IDLE,            // No sync in progress
     BG_SYNCING,      // Background fetch is running
     FG_REQUESTED,    // Foreground requested fresh sync
     FG_BLOCKING,     // Foreground blocked until sync completes
     CONFLICT_WAIT    // Waiting for user to resolve conflict
   }
   
   onForegroundResume() {
     if state == BG_SYNCING:
       // Option 1: Wait for background sync to complete
       // Option 2: Cancel background sync, prioritize foreground
       
       // Choose based on time elapsed and data freshness
       if bgSyncElapsedTime > 5s:
         // Take the result, refresh foreground from updated cache
         awaitBackgroundSync()
       else:
         // Probably won't finish soon, do fresh foreground sync
         cancelBackgroundSync()
         startForegroundSync()
   }
   
   onBackgroundFetch() {
     if state == FG_ACTIVE:
       // Only sync if app is backgrounded
       return skipBackgroundSync()
     
     state = BG_SYNCING
     try:
       syncData()
     finally:
       state = IDLE
   }
   ```

2. **Cache Coherency for Concurrent Access**
   ```
   // Use a write-ahead transaction log
   // Both background and foreground sync queue changes
   
   transactionLog = [
     {
       source: "background_sync",
       timestamp: 1450,
       operation: "insert_message",
       data: {...}
     },
     {
       source: "foreground_user",
       timestamp: 1451,
       operation: "update_draft",
       data: {...}
     }
   ]
   
   // Apply transactionally to cache in order
   for transaction in transactionLog.sorted_by_timestamp:
     applyToDatabase(transaction)
   
   // Refresh UI once
   notifyUIOfChanges(allChanges)
   ```

3. **Message List Consistency**
   ```
   // Problem: Message order changes during sync
   // Solution: Deferred update to message list
   
   onForegroundActive() {
     messageList.isLocked = true  // Prevent scroll jank
     
     if backgroundFetchDidInsertMessages:
       // Don't re-render yet
       queuedUpdates = collectPendingUpdates()
     
     syncWithServer() {
       newMessages = api.getMessages(cursor)
       updateCache(newMessages)
       queuedUpdates += newMessages
     }
     
     // Batch update UI once
     messageList.isLocked = false
     applyQueuedUpdates(messageList)  // Single re-render
   }
   ```

**Escalation Path:**
- If background sync data is stale (>5 min old): WARN "Data may be out of date, pull to refresh"
- If foreground/background conflict detected: BLOCKER, show "Sync error, tap to resolve"
- If transaction log fills up (>1000 pending): BLOCKER, force sync immediately

**Related:** reasoning-as-infra (concurrency control), Forge Decision D14 (explain what's syncing)

---

### Edge Case: Biometric Authentication State Change

**Scenario:** User enables Face ID during app use. Later, Face ID is disabled in device settings (user re-enrolls face, or disables biometric). App must handle the change gracefully without crashing or security issues.

**What if this happens?**
- App cached that Face ID is available and enabled
- User goes to Settings > Face & Passcode > deletes enrolled face
- App still tries to call biometric prompt for next transaction
- API call fails with "No biometric enrolled" error
- App crashes if not caught

**Action: Biometric Availability Polling**

```
onAppStart() {
  biometricState = cachedBiometricState()
  
  // Check actual device state
  actualState = LocalAuthentication.canEvaluatePolicy()
  
  if cachedBiometricState != actualState:
    showAlert("Biometric setting changed")
    saveBiometricState(actualState)
    
    if actualState == false && cached == true:
      // Biometric was disabled
      showAlert("Face ID disabled. Use password for next login.")
      requirePasswordOnNextAuth = true
    else if actualState == true && cached == false:
      showAlert("Face ID enabled. Use it next time?")
      offerBiometricEnroll()
}

onBiometricAttempt() {
  try:
    result = BiometricPrompt.authenticate()
    if result.success:
      proceedWithTransaction()
    else:
      // Possible: user cancelled, or biometric failed
      showPasswordFallback()
  catch BiometricUnavailableException:
    // Biometric was disabled between attempts
    saveBiometricState(false)
    showAlert("Biometric no longer available")
    showPasswordFallback()
}
```

**Escalation Path:**
- If biometric unavailable during critical transaction: WARN, force password fallback
- If biometric permission revoked: WARN once, add manual re-enable option to settings

---

### Edge Case: Push Notification Delivery Latency & Cold Start

**Scenario:** User receives push notification while app is terminated (cold start).

- 2:00 PM: Server sends push: "Your friend sent a message"
- Push queued at FCM/APNs service
- 2:05 PM: Push delivered to device (5 second latency)
- User taps push notification
- App launches from cold start
- App makes API call to get latest messages
- But in the 5 seconds, server had 3 more messages

**What if this happens?**
- App shows stale data from push notification
- User sees old message count, old last message timestamp
- When user navigates to chat, data refreshes (jarring UX)
- User assumes message was lost

**Action: Cold Start Data Freshness Strategy**

```
onPushNotificationTapped(payload) {
  // Store push timestamp for comparison
  pushReceivedAt = timestamp()
  
  // Launch app, navigate to relevant screen
  navigateTo(payload.screen, payload.context)
  
  // Now: Check if data is still fresh
  onScreenVisible() {
    cachedData = loadFromCache()
    
    if cachedData.lastSyncTime < (pushReceivedAt - 30s):
      // Data is likely stale (push was delayed or old)
      // Show loading indicator, refresh from server
      showLoadingBanner("Loading latest messages...")
      refreshData()
    else if cachedData.lastSyncTime < pushReceivedAt:
      // Data is slightly stale, but push is fresh
      // Show cached data, refresh in background
      showCachedData(cachedData)
      refreshDataInBackground()
}

// On cold start: perform minimal API sync
onAppLaunchFromColdStart() {
  // Only fetch critical data to get app responsive fast
  // Use cache-first strategy for non-critical data
  
  criticalData = api.getMinimalState()  // Auth + user profile
  nonCriticalData = cache.getOldData() // Messages, etc.
  
  renderUI(criticalData, nonCriticalData)
  
  // Refresh full state in background once app is interactive
  after(500ms):
    refreshFullState()
}
```

**Escalation Path:**
- If push-referenced data no longer exists (message deleted): Show "This message was deleted"
- If push timestamp is >5 min old: Always do fresh sync before showing data
- If cold start >3s: WARN user, recommend app restart

**Related:** reasoning-as-infra (push delivery SLA), Forge Decision D14 (transparency about delays)

---

## 7. Common Pitfalls

### Pitfall 1: Assuming Offline Sync is Simple

**Anti-pattern:** "We'll just cache data and sync on reconnect."

**Reality:** Offline sync is one of the hardest distributed systems problems.

**Why it fails:**
- Conflict resolution is not trivial (see edge cases above)
- Network recovery after 1hr+ offline is complex (ordering, causality, validation)
- Users expect their offline actions to work seamlessly
- Real devices have unpredictable network state (WiFi drops, switches to cellular, etc.)

**Fix:**
- Use event sourcing or transaction logs (immutable history)
- Explicitly choose conflict resolution per entity type (server-wins vs client-wins vs CRDT)
- Design API to support idempotent replays (use idempotency keys)
- Test with extended offline scenarios (simulate 1hr, 8hr, 24hr offline)
- Log all conflicts to backend for observability

**Reference:** Edge Case: Offline Data Conflicts above, reasoning-as-backend (idempotency)

---

### Pitfall 2: Not Versioning API Contracts

**Anti-pattern:** "We'll just add a new field to the endpoint when needed."

**Reality:** Old app versions will crash or behave incorrectly.

**Why it fails:**
- User installs app v1.5, backend upgrades to v3 (months later)
- App makes request with v1.5 schema, gets v3 response with required new fields
- App crashes because it doesn't know about new fields or made-mandatory fields
- User can't roll back app (AppStore auto-updates in background)

**Fix:**
- Version all APIs explicitly (/v1, /v2, /v3)
- Support >=2 major versions in parallel (gives 3-6 months for users to upgrade)
- Use optional/nullable fields (assume v2 client may not send new fields in v3)
- Implement feature flags server-side to gate new features by app version
- Test with old app versions against new API before deprecating old API versions

**Reference:** Edge Case: API Version Mismatch above, reasoning-as-backend (contract negotiation), contract-api-rest skill

---

### Pitfall 3: Ignoring Device Storage Limits

**Anti-pattern:** "We'll just cache everything locally."

**Reality:** Devices run out of space, encryption adds 2x overhead, OS steals space.

**Why it fails:**
- On 32GB device with 4GB free, caching 2GB of images seems fine
- But OS reserves space for system updates (1-2GB)
- SQLCipher encrypted DB uses 2x space
- User downloads 500MB video in Photos app
- App can't write to cache, crashes on sync
- Unencrypted cache bloats: users see "app is taking too much space"

**Fix:**
- Implement multi-tier caching (critical/hot/cold, see edge case above)
- Use external storage (SD card) for non-critical data on Android
- Compress where possible (gzip messages, downscale images)
- Implement automatic LRU eviction once quota exceeded
- Separate encrypted and unencrypted caches (encrypt only secrets)
- Monitor storage usage and alert user before hitting limits

**Reference:** Edge Case: Local Storage Constraints above

---

### Pitfall 4: Syncing Without Idempotency

**Anti-pattern:** "If sync fails, user will retry manually."

**Reality:** Users expect automatic retry, which means mutations must be idempotent.

**Why it fails:**
- Network fails mid-sync: user's "like" action sent twice
- Backend counts both likes: user's like count is wrong
- Automatic retry (which is expected) compounds the problem
- Message sent twice to recipient
- Payment charged twice

**Fix:**
- Every mutable API endpoint must be idempotent (via idempotency keys)
- Client generates UUID for each mutation before sending
- Client retries with same UUID indefinitely until success
- Backend detects duplicate UUID and returns cached result instead of re-executing
- Log idempotency key with transaction for debugging

**Pseudocode:**
```
onUserAction(action) {
  mutationId = UUID()
  saveLocalMutation(action, mutationId)  // Durable queue
  
  syncMutation(mutationId, action) {
    while (true):
      try:
        api.performAction(action, idempotency_key=mutationId)
        markMutationComplete(mutationId)
        break
      catch NetworkError:
        waitThenRetry()  // Exponential backoff
  }
}

// Backend:
POST /api/action
{
  idempotency_key: "uuid-xxx",
  action: {...}
}

Backend:
  if cache.exists(idempotency_key):
    return cache.get(idempotency_key)  // Return cached result
  else:
    result = perform(action)
    cache.set(idempotency_key, result, ttl=24h)
    return result
```

**Reference:** reasoning-as-backend (idempotency keys), edge case: Network Recovery above

---

### Pitfall 5: Background Sync Race Conditions

**Anti-pattern:** "Background sync is simple, just fetch data in the background."

**Reality:** Background and foreground sync run concurrently; cache coherency is hard.

**Why it fails:**
- Background fetch inserts new messages while foreground renders list
- Message list order changes mid-scroll (user scrolls to old message, suddenly jumps to new)
- User drafts reply while background fetch completes, draft's parent message ID is stale
- SQLite write lock contention causes ANR (Application Not Responding) on Android
- Push notification arrives while background fetch is syncing, both try to update same data

**Fix:**
- Implement sync state machine (IDLE, BG_SYNCING, FG_REQUESTED)
- Use write-ahead transaction log (both background and foreground queue changes)
- Apply transactions in logical order (by timestamp/causality), not just DB order
- Batch UI updates after sync completes (prevent re-renders mid-sync)
- Use database transactions to ensure coherency (all-or-nothing writes)
- Monitor for lock contention: if >100ms, log as warning

**Reference:** Edge Case: Background Sync vs Foreground above

---

### Pitfall 6: Assuming Network is Binary (Online/Offline)

**Anti-pattern:** "We'll cache everything offline and sync online."

**Reality:** Network is a spectrum (good cellular, poor WiFi, LTE timeout, etc.).

**Why it fails:**
- App shows "offline" banner, but user has weak signal (slow, not offline)
- User waits 30s for sync to complete, thinks app is broken
- Background fetch runs on bad network and gets timeouts
- App syncs partial data: some mutations succeed, others fail, state is inconsistent
- User opens app thinking they're online, it's actually offline

**Fix:**
- Implement quality-of-service metrics (signal strength, latency, success rate)
- Show network quality indicator (not just "online/offline")
- Set aggressive timeouts for critical operations (2-3s), relaxed for background (30s)
- Implement retry with exponential backoff (don't hammer failed endpoint)
- Design mutations to be atomic (all-or-nothing) even over bad network
- Test on real devices with WiFi Analyzer, deliberately restrict bandwidth

**Reference:** reasoning-as-infra (network resilience)

---

### Pitfall 7: Not Handling Permissions Changes

**Anti-pattern:** "We checked permissions at startup, they won't change."

**Reality:** Users revoke permissions in Settings anytime; iOS/Android send callbacks.

**Why it fails:**
- App cached that user granted camera permission
- User goes to Settings and revokes it
- App tries to open camera: crashes with PermissionDeniedException
- Background sync loses access to location, can't sync location-based data
- Biometric prompt fails (Face ID was deleted, only passcode left)

**Fix:**
- Listen to permission change callbacks (PermissionChangeListener on Android, NSNotification on iOS)
- When permission is revoked: gracefully disable feature, don't crash
- Re-check permissions before every use (don't assume cached state)
- Implement feature fallbacks (if no camera: show photo picker instead)
- Log permission changes to backend for analytics (helps debug support tickets)

**Reference:** Platform-specific constraints below, edge case: Biometric Authentication State Change

---

## 8. Offline-First Sync Decision Tree

**Decision:** How to handle data mutations and conflicts when offline or with slow sync?

```
Does the data need to be
modified offline?
│
├─ NO (read-only cache)
│  └─ Strategy: Cache-on-Read, Refresh-on-Sync
│     • Load from local cache
│     • Sync in background when online
│     • Server-wins conflicts (no local mutations)
│     • Example: User profiles, posts, archived messages
│
└─ YES (local mutations allowed)
   │
   ├─ Is the mutation IDEMPOTENT?
   │  │  (can be safely retried multiple times)
   │  │
   │  ├─ YES (like/unlike, follow/unfollow)
   │  │  └─ Strategy: Client-Wins with Idempotency
   │  │     • Apply mutation locally immediately
   │  │     • Queue for sync (durable queue/transaction log)
   │  │     • Retry indefinitely with idempotency key
   │  │     • Backend deduplicates via idempotency cache
   │  │     • Fast UX: instant feedback, reliable delivery
   │  │     • Risk: briefly out-of-sync with server
   │  │
   │  └─ NO (non-idempotent: transfer, payment, deletion)
   │     └─ Is data AUTHORITATIVE on server?
   │        │  (server is source of truth)
   │        │
   │        ├─ YES (balance, permissions, role)
   │        │  └─ Strategy: Server-Wins with Local Optimism
   │        │     • Show local optimistic update immediately
   │        │     • Queue request (not mutation)
   │        │     • Validate request on reconnect
   │        │     • If invalid: revert, show error
   │        │     • Fetch authoritative state from server
   │        │     • Example: Send payment → show "pending", validate on sync
   │        │
   │        └─ NO (symmetric between client and server)
   │           └─ Strategy: Conflict-Free Replicated Data Type (CRDT)
   │              • Use commutative operations (order doesn't matter)
   │              • Example: Add/remove from set, increment counter
   │              • All devices' mutations eventually converge
   │              • Implementation: Yjs, Automerge
   │              • Trade-off: Complex, but automatic conflict resolution
   │
   └─ Multiple mutations on SAME entity offline?
      │
      ├─ YES, OVERLAPPING (user edits name while admin edits role)
      │  └─ Strategy: Conflict Resolution UI
      │     • Show both versions to user
      │     • Let user choose: keep mine, use theirs, merge
      │     • Example: Collaborative doc editing
      │     • Backend: merge strategy (last-write-wins, CRDT, etc.)
      │
      └─ NO, NON-OVERLAPPING (user edits name, admin edits role)
         └─ Strategy: Automatic Merge
            • Merge non-conflicting fields
            • Apply in order (timestamps/causality)
            • No user interaction needed
            • Backend: event sourcing to track causality
```

**Choose based on:**
1. **Idempotency:** Can mutation be replayed safely?
2. **Authority:** Is server authoritative or symmetric?
3. **Complexity tolerance:** How much code/complexity is acceptable?
4. **Conflict frequency:** How often do offline mutations conflict with server?

**Examples by entity type:**

| Entity | Mutation | Strategy | Why |
|--------|----------|----------|-----|
| Message | Send | Idempotent + queue | Safe to retry, fast feedback |
| Like | Toggle | Idempotent + client-wins | Idempotent, user expects instant feedback |
| Profile.name | Edit | Server-wins + optimistic | Server authoritative, show error if conflict |
| Balance | Transfer | Server-wins + request queue | Non-idempotent, server authoritative |
| Notification | Mark as read | Idempotent + client-wins | Idempotent, safe to replay |
| Document (collab) | Edit | CRDT | Symmetric, auto-merge on conflict |
| Permissions | Change | Server-wins only | Non-idempotent, server authoritative, no offline mutations |

---

## 9. API Versioning & Compatibility Decision Tree

**Decision:** How to manage API versions when app and backend can be out of sync?

```
Are you adding a NEW API endpoint
or modifying existing?
│
├─ NEW endpoint
│  └─ Assign version: /v2/new_endpoint
│     └─ Add to feature flags with app_min_version
│        └─ App checks feature flags before calling
│           └─ If version too old: show "Update required" or fallback
│
└─ MODIFYING existing endpoint
   │
   ├─ Adding OPTIONAL field to response?
   │  └─ YES: Use current version
   │     • Old clients ignore new fields
   │     • New clients use new fields
   │     • No crash, backward compatible
   │
   ├─ Making REQUIRED field optional?
   │  └─ YES: Use current version
   │     • Old clients still send it (can't hurt)
   │     • New behavior: field is optional
   │
   ├─ REMOVING a field?
   │  └─ NO: Never remove, deprecate instead
   │     • Mark as "deprecated as of v3"
   │     • Support for 6 months (allow time for users to upgrade)
   │     • After 6 months: move to /v1 only, /v2+ doesn't have it
   │
   ├─ Changing field SEMANTICS (e.g., "count" now means something else)?
   │  └─ YES: Bump major version (/v2 → /v3)
   │     • Old clients will misinterpret data
   │     • Force upgrade via feature flags
   │
   └─ Changing field FORMAT (e.g., string → number)?
      └─ YES: Bump major version
         • Old clients can't parse response
         • Use coercion if possible (return as string, let client parse)
```

**Deprecation Timeline:**

```
v2 launch date: Jan 2025
├─ v2 is current (all new clients use v2)
├─ v1 deprecated announcement: Mar 2025 (in-app banner)
├─ v1 support ends: Sep 2025 (6 months later)
│  └─ Clients <app_version_x are force-upgraded
│  └─ API drops /v1 support
│
v3 launch date: Jun 2025 (before v1 sunset)
├─ v3 is current (all new clients use v3)
├─ v2 deprecated announcement: Aug 2025 (in-app banner)
├─ v2 support ends: Feb 2026 (6 months later)
└─ API drops /v2 support
```

**Device Rollback Scenario:**

Problem: User had app v3 installed, then rolls back to v2 (e.g., via TestFlight, or old backup).

```
App v2 launches, tries /api/v2/endpoint
│
├─ Backend has only /v3 available
│  └─ Returns 410 Gone
│     └─ App shows "Update required" banner
│        └─ Blocks access to that feature
│        └─ Allows feature degradation for other features
│
└─ Backend maintains v2 compatibility window
   └─ Old app works fine
      └─ Encourages upgrade (not forced)
```

**Feature Flag Strategy for Gradual Rollout:**

```
POST /health/versions
Response:
{
  "minimum_app_version": "1.5",
  "current_api_version": "v3",
  "deprecated_versions": ["v1"],
  "feature_flags": {
    "biometric_2fa": {
      "enabled": true,
      "min_app_version": "2.0",
      "rollout_percentage": 95,  // 95% of users get it
      "regions": ["US", "EU"]     // Only US/EU
    },
    "offline_mode": {
      "enabled": true,
      "min_app_version": "1.5",
      "rollout_percentage": 100
    },
    "new_ui_v2": {
      "enabled": false,
      "min_app_version": "3.0",
      "rollout_percentage": 0     // Not ready yet
    }
  }
}

// Client:
onAppStart() {
  flags = api.getFeatureFlags()
  
  // Check if user is eligible
  if flags["biometric_2fa"].enabled &&
     localAppVersion >= flags["biometric_2fa"].min_app_version &&
     isInRollout(flags["biometric_2fa"].rollout_percentage) &&
     userRegion in flags["biometric_2fa"].regions:
    
    enableBiometric()
  else:
    disableBiometric()  // Falls back to password
}
```

**Contract Negotiation:**

See reasoning-as-backend (API versioning contracts). Key points:
- Frontend, Backend, Infra all agree on version timeline
- Deprecation timelines are non-negotiable (allow upgrade window)
- Feature flags allow independent deployment
- Idempotency keys required for all mutations

---

## 10. Platform-Specific Constraints

### iOS

**Keychain (Secure Storage for Secrets)**
- Capacity: ~2-4MB per app (includes system overhead)
- Use for: auth tokens, API keys, private encryption keys
- NOT for: large data (messages, images, documents)
- Data is accessible via biometric (Face ID/Touch ID) only if app requires reauthentication
- Network request: Keychain access on main thread is safe (Apple optimized it)
- Implication: Critical secrets are secure, but can't store large offline cache in Keychain. Use encrypted CoreData or SQLCipher for larger data.

**CoreData (Database)**
- Supports encryption: use NSPersistentContainer with encryptionKey
- Encryption is file-level, transparent to app
- Performance: Full DB encryption has ~10% overhead, acceptable for most cases
- SQLite under the hood: use raw SQLite for better performance if needed
- Implication: Messages, profiles, drafts stored in encrypted CoreData. Use multi-thread safe patterns (NSManagedObjectContext on main thread only, unless concurrent).

**Background App Refresh (iOS 13+)**
- Permission: User must grant "Background App Refresh"
- Frequency: iOS decides, typically 15-30 minutes, not guaranteed
- Task quota: App gets ~1-5 minutes of execution, then suspended
- Use for: Background sync of non-critical data (messages, profiles)
- NOT for: Critical features (payments, 2FA, location)
- Implication: Offline-first design must not depend on timely background sync. App must catch up on foreground launch.

**Background Processing (BGProcessingTask)**
- Minimum frequency: >6 hours apart, requires power + WiFi
- Use for: Heavy background tasks (cleanup, indexing, large syncs)
- Rare: Most apps don't need this
- Implication: Long offline sync (validation, conflict resolution) can happen in background on iOS 13+.

**Local Network Privacy (iOS 14+)**
- Apps must request permission to access local devices (printers, routers, IoT)
- Impact: If app connects to local API (behind home WiFi), user must grant permission
- Implication: In-home apps need explicit permission declaration

**Implications for Offline-First Sync:**
- Background sync is unreliable: don't depend on it
- Design app to sync fully on foreground launch (app-start)
- Use CoreData encryption for all local data
- Keychain only for secrets <100KB
- Multi-tier caching: critical in Keychain, bulk in encrypted CoreData

---

### Android

**Keystore (Secure Storage for Secrets)**
- Capacity: ~10MB per key (but OS limits overall)
- Encryption: Hardware-backed (Secure Enclave on Pixel) or software-backed (older devices)
- Use for: API keys, auth tokens, master encryption keys
- Biometric requirement: BiometricPrompt required to unlock secrets
- Implication: Secrets are HSM-protected on modern devices, but older devices use software encryption. Always assume potential unlock failure.

**SharedPreferences (Lightweight Key-Value)**
- Size: ~2-4MB per preference file
- Encryption: Use EncryptedSharedPreferences (from androidx.security)
- Performance: Fast reads, but not a database
- Use for: Small config, feature flags, app state
- NOT for: Large data (messages, images)
- Implication: Sync metadata stored here (last_sync_time, pending_mutations count), encrypted. Large data stored in SQLite.

**SQLite (Database)**
- Encryption: Use SQLCipher (open-source) or Room with encryption
- Performance: ~2x slower with encryption, acceptable for most cases
- File size: No hard limit on Android (OS allows growth)
- Implication: All app data encrypted at rest, auditable sync history

**JobScheduler (Background Sync)**
- Frequency: OS decides (typically 15m-1h), user can disable
- Constraints: Requires charging, WiFi, or low battery (configurable)
- Execution time: 10 minutes max per job, then killed
- Battery impact: Heavy syncing reduces battery significantly
- Implication: Background sync is opportunistic, not guaranteed. App must sync on foreground launch too.

**WorkManager (Reliable Background Work)**
- Frequency: Persistent queue, survives reboot
- Constraints: User can disable, work may be deferred 24+ hours
- Execution: Balances battery and reliability
- Use for: Durable sync queue (messages, mutations)
- Implication: Best-effort background sync, but not real-time

**Doze Mode (Aggressive Battery Saving)**
- Activates: After 10min idle on battery, more aggressive after 2 hours
- Impact: Network is cut off during Doze, work deferred until maintenance window
- Opt-out: Requires SCHEDULE_EXACT_ALARM (limited apps)
- Implication: Don't assume network during Doze. Sync happens on maintenance windows (15-30min apart) or on foreground launch.

**Storage (Encryption & Quotas)**
- Scoped Storage (Android 10+): Limited access to shared directories
- Data directory quota: No hard limit, but user can see storage breakdown
- Implication: App should estimate storage use and warn user if >500MB

**Implications for Offline-First Sync:**
- Background sync is deferred (can be 1+ hour)
- Don't depend on real-time background sync
- Use WorkManager for durable mutation queue
- Sync fully on foreground launch
- Expect Doze to cut network during idle
- Design with high latency in mind (1-6 hour background sync windows)

---

### Cross-Platform Constraints

| Constraint | iOS | Android | Implication |
|-----------|-----|---------|------------|
| Background execution | BGProcessingTask (6h+) or App Refresh (15-30m) | JobScheduler (15m-1h) or WorkManager | Both unreliable; sync on foreground launch |
| Secret storage | Keychain (secure, but 2-4MB) | Keystore (secure, but unlock required) | Secrets only, use Keychain/Keystore for tokens |
| Local database | CoreData (encrypted) or SQLite | SQLite or Room (encrypted via SQLCipher) | All data encrypted at rest |
| Network during Doze | Not applicable | Cut off 10min-2h+ | Design async retry queue |
| Storage quota | Device limit (varies) | Device limit + scoped storage | Implement LRU cache eviction |
| Push notifications | APNs (Apple) | FCM (Google) | Push is best-effort, not guaranteed |

**Design Patterns to Handle Constraints:**

1. **Cold Start Optimization**
   - Load critical data from cache immediately (show cached state)
   - Refresh in background (don't block UI)
   - Use skeleton screens for perceived performance

2. **Offline-First Cache**
   - Local SQLite DB for all user data (encrypted)
   - Sync happens in background, app uses cache
   - Background sync validates cache against server state

3. **Durable Mutation Queue**
   - WorkManager (Android) or NSOperationQueue (iOS)
   - Queue survives app restart, Doze, etc.
   - Retry with exponential backoff until server confirms

4. **Push + Poll Hybrid**
   - Receive push notifications (best-effort)
   - Poll server on app foreground (guarantees freshness)
   - Push is optimization, poll is backstop

5. **Degraded Mode**
   - When offline: use cached data, queue mutations
   - When online but slow: use cache, slow refresh
   - When online and fast: use live data, minimal cache

---

## 11. Output Format

Write to `~/forge/brain/prds/<task-id>/council/app.md`:

```markdown
# App Perspective

## Screens & Navigation
- List of screens and user flows

## API Endpoints
- Versioned endpoint list
- Include version negotiation strategy

## Offline-First Strategy
- Entity-level sync strategy (cache-on-read vs. idempotent queue vs. CRDT)
- Conflict resolution per entity
- Background sync design

## Platform Constraints Impact
- iOS: Keychain storage, CoreData encryption, background refresh limitations
- Android: Keystore unlock requirement, Doze mode, JobScheduler deferral
- Cold start sync strategy
- Storage tier allocation (critical/hot/cold)

## API Versioning
- Minimum app version supported
- Feature flags for gradual rollout
- Deprecation timeline

## Potential Edge Cases & Mitigations
- Offline data conflicts: [chosen strategy]
- Network recovery after outage: [validation + replay strategy]
- Background sync race conditions: [state machine + transaction log]
- Biometric permission changes: [fallback to password]
- Push notification delays: [cache + poll hybrid]

## Push Notifications
- Triggers and delivery guarantees
- Cold start handling
- Fallback to poll

---

**Ready for:** Council negotiation (compare with backend, web, infra perspectives)
```

---

## 12. Cross-References

**Related Skills:**
- reasoning-as-backend: API versioning, idempotency keys, conflict resolution strategies
- reasoning-as-web-frontend: Similar patterns for web (cache invalidation, offline capabilities)
- reasoning-as-infra: Event sourcing, message queues, network resilience
- contract-api-rest: REST contract negotiation (versioning, deprecation)
- brain-read: Look up product topology, project metadata

**Related Forge Decisions:**
- D14 (Persuasion Principles): Explain conflicts to users with clarity and authority
- D30 (Worktree-per-project-per-task): Isolation for parallel app development

**Related Brain Concepts:**
- Event Sourcing: Immutable event log for offline mutations and replay
- CRDT: Conflict-free replicated data types for automatic merge
- Idempotency: Safe replay of mutations
- Causality Tracking: Maintain order during network delays
