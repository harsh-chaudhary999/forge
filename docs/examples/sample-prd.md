# PRD: Example — Item favorites (sample)

Use this as a **shape reference** for your own PRD. Replace sections with your product, constraints, and acceptance tests.

## Problem

Users cannot save favorite items across web and mobile in a reliable way.

## Goals

- Persist favorites per user with correct authorization.
- Reflect favorites in near real time across surfaces where applicable.

## Success metrics

- p95 read path under 200ms under nominal load.
- Zero unauthorized cross-user reads in security review scenarios.

## Technical scope

- Backend: REST endpoints, persistence, auth integration.
- Web: favorites UI, optimistic updates, error handling.
- App: offline-safe read path where required by product policy.

## Out of scope

- Social sharing, recommendations v2, admin bulk import.

## Acceptance criteria

- Authenticated user can add/remove favorite; repeated add is idempotent or returns defined conflict.
- Unauthorized access returns 401/403 consistently.
- Documented merge order across repos if schema changes.

## Risks & dependencies

- Cache invalidation vs DB source of truth.
- Depends on existing auth session model.
