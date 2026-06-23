# Platform-Specific Constraints (iOS / Android / Cross-Platform)

The SKILL.md spine points here for the full platform constraint catalog: iOS storage and
background execution, Android storage and background execution, the cross-platform
constraint table, and the design patterns that handle those constraints.

## iOS

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

## Android

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

## Cross-Platform Constraints

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
