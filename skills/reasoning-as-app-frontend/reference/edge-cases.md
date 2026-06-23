# App Frontend Edge Cases & Handling Strategies

The SKILL.md spine points here for the full edge-case catalog. Each entry names the
scenario, the failure mode ("what if this happens?"), the concrete action with
pseudocode, and an escalation path (WARN / BLOCKER / flag). Resolve every escalation
through the marker-block transport described in SKILL.md "Escalation transport".

## Edge Case: Offline Data Conflicts (Local Changes + Server Changes)

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

**Related:** reasoning-as-backend (server-side idempotency keys), persuasion-grounded design (explain what happened — see forge-writing-skills)

---

## Edge Case: API Version Mismatch (Old App + New API)

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

**Related:** reasoning-as-backend (API versioning contracts), persuasion-grounded design (authority: document deprecation timelines — see forge-writing-skills)

---

## Edge Case: Network Recovery After Extended Offline

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

## Edge Case: Local Storage Constraints (App vs OS Limits)

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

## Edge Case: Background Sync vs Foreground App State Divergence

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

**Related:** reasoning-as-infra (concurrency control), persuasion-grounded design (explain what's syncing — see forge-writing-skills)

---

## Edge Case: Biometric Authentication State Change

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

## Edge Case: Push Notification Delivery Latency & Cold Start

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

**Related:** reasoning-as-infra (push delivery SLA), persuasion-grounded design (transparency about delays — see forge-writing-skills)
