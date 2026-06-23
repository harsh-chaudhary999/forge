# Common Pitfalls (App Frontend Reasoning)

The SKILL.md spine points here for the full anti-pattern catalog. Each pitfall names the
anti-pattern, the reality, why it fails, the fix, and a cross-reference to the relevant
edge case or sibling reasoning skill.

## Pitfall 1: Assuming Offline Sync is Simple

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

## Pitfall 2: Not Versioning API Contracts

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

## Pitfall 3: Ignoring Device Storage Limits

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

## Pitfall 4: Syncing Without Idempotency

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

## Pitfall 5: Background Sync Race Conditions

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

## Pitfall 6: Assuming Network is Binary (Online/Offline)

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

## Pitfall 7: Not Handling Permissions Changes

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
