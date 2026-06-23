# State Management Patterns, Pitfalls & Sync Strategy

## Common Pitfalls

Avoid these patterns when reasoning about web frontend:

1. **Assuming state updates are instant** - React state and async operations are unpredictable. Optimistic updates can conflict with server truth. Always track loading/error states separately and validate after async completion.
   - Counter: Implement proper loading states, debounce rapid changes, use server-side validation as source of truth.

2. **Over-engineering state management** - Not every piece of state needs Redux/Zustand. Simple component state works fine for most cases. Only elevate to global state when multiple unrelated components need it.
   - Counter: Start with local state, only lift when needed. Document your state "why" (why is it at this level?).

3. **Ignoring localStorage persistence implications** - Persisting to localStorage works until it doesn't (storage limits, stale data after backend changes, cross-tab sync failures). Don't persist without a clear expiry or validation strategy.
   - Counter: Persist with timestamps, validate on app startup, provide clear user messaging when syncing with server.

4. **API contract mismatches discovered late** - Frontend assumes response fields that backend doesn't provide. Only caught in integration testing or production.
   - Counter: Define API contracts explicitly in PRD analysis. Frontend/backend teams sign off together. Use shared TypeScript types where possible.

5. **Form state complexity without plan** - Nested objects, conditional fields, dynamic arrays lead to bugs. State gets out of sync with validation. Form submission fails silently.
   - Counter: Use dedicated form libraries (React Hook Form, Formik). Define validation schema upfront. Test form state separately from submission.

6. **Race conditions in async state** - User clicks twice, triggers two async calls. The second response arrives first, gets overwritten by the first. UI shows wrong data.
   - Counter: Cancel in-flight requests before new ones. Use Request IDs to ignore stale responses. Show loading state to prevent double-clicks.

7. **Cross-component communication via prop drilling** - Passing props 4-5 levels deep becomes unmaintainable. Changes to props break multiple components. Siblings can't communicate easily.
   - Counter: Use context for shared concerns (auth, theme, feature flags). Use state management for domain state. Keep props for local concerns only.

## State Management Decision Tree

When analyzing a PRD, use this decision tree to choose your state management approach:

```
START: Do multiple unrelated components need this state?
  NO  → Keep in component (useState at lowest common ancestor)
        → When: Local form state, UI toggles, temporary filters
        → Example: Modal open/close, tab selection, accordion expansion

  YES → Will state persist across page reloads?
    NO  → Use React Context + useReducer (ephemeral shared state)
          → When: Auth user info, theme selection, feature flags
          → Example: User context with login/logout, theme switcher
          → Trade-off: Simpler than Redux, no persistence, re-renders on change

    YES → How much state and how often does it change?
      SMALL + INFREQUENT  → localStorage + Context
                            → When: User preferences (theme, language, sidebar collapse)
                            → Example: Persisting theme choice, saved filters
                            → Trade-off: Simple, works offline, risk of stale data

      LARGE + FREQUENT    → Zustand or similar lightweight store
                            → When: Domain state (products, cart, user posts)
                            → Example: Shopping cart, feed data, editing state
                            → Trade-off: More powerful than context, less boilerplate than Redux
                            
      COMPLEX + FREQUENT  → Redux or similar with middleware
                            → When: Time-travel debugging needed, complex flows (undo/redo)
                            → Example: Collaborative editor, complex workflow with multiple steps
                            → Trade-off: Most powerful, most boilerplate, best for debugging

      ASYNC + PAGINATED   → React Query / SWR + lightweight store
                            → When: Server-driven data (API responses, cache invalidation)
                            → Example: User feed, search results, data tables
                            → Trade-off: Handles caching/syncing for you, opinionated
```

### Persistence Strategy Checklist

When deciding to persist state to localStorage:

- **What to persist:** User preferences (theme, layout), saved form drafts, UI state (sidebar open/closed)
- **What NOT to persist:** Auth tokens (use httpOnly cookies), sensitive data, frequently-changing server data
- **Validation on startup:** Always validate persisted data against current API/schema. Discard if stale (check timestamp).
- **Sync strategy:** On app mount, compare localStorage with server state. Show spinner while syncing. Disable UI if conflict detected.
- **Storage limits:** localStorage is ~5-10MB. Monitor size for large state. Compress if needed.

### Backend Sync Points

Identify where state must sync with backend:

| State | Sync Trigger | Conflict Resolution |
|-------|--------------|---------------------|
| Auth token | Login/logout | Server truth (token validation) |
| User profile | Edit profile form submit | Optimistic update + rollback on error |
| Shopping cart | Add/remove item | Merge server cart with local changes |
| Feature flags | App startup | Server truth always, client cache for perf |
| Saved filters | Save button click | Server persists, local cache for speed |
