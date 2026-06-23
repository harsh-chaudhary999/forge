# Decision Matrices: Offline-First Sync & API Versioning

The SKILL.md spine points here for the two decision trees that drive app-frontend
reasoning: the offline-first sync strategy selector (per entity type) and the API
versioning & compatibility selector (with deprecation timelines, rollback handling, and
feature-flag rollout).

## Offline-First Sync Decision Tree

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

## API Versioning & Compatibility Decision Tree

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
