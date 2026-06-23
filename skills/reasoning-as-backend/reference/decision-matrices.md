# Backend Reasoning — Decision Tree & Matrices

The sync-vs-async decision tree and the implementation decision matrix the
backend surface uses to classify each operation. The reasoning question set
itself lives in `../SKILL.md`.

## Decision Tree: Synchronous vs. Asynchronous Reasoning

When designing backend logic, choose between synchronous (blocking) and asynchronous (non-blocking) patterns based on your latency requirements, consistency needs, and failure recovery strategies.

```
DOES THE OPERATION NEED AN IMMEDIATE RESPONSE TO THE CLIENT?
│
├─ YES, client is waiting (user submitted form, waiting for result) → SYNCHRONOUS
│  │
│  ├─ Operation must complete within SLO (e.g., < 200ms p99)
│  ├─ Client sees success/failure immediately
│  ├─ Use database transactions to ensure atomicity
│  ├─ If operation fails, client sees error and can retry
│  │
│  └─ Example: User signup, payment authorization, login
│
└─ NO, client is NOT waiting (background job, notifications, audit logs) → ASYNCHRONOUS
   │
   ├─ Publish event to queue, return success immediately
   ├─ Consumer processes event asynchronously
   ├─ Use eventual consistency with retry/DLQ strategy
   ├─ If processing fails, event goes to DLQ for manual replay
   │
   ├─ Is order important (Event A must be processed before Event B)?
   │ │
   │ ├─ YES → Use partitioned queue with partition key
   │ │       └─ Example: All user events for user 123 go to same partition
   │ │
   │ └─ NO → Use standard queue
   │        └─ Example: Notification sent to 1000 users (no ordering needed)
   │
   └─ Example: Email notifications, audit logging, analytics events
```

**Implementation Decision Matrix**:

| Scenario | Pattern | SLO | Consistency | Complexity |
|----------|---------|-----|-------------|-----------|
| User login | Sync | < 100ms p99 | Strong | Low |
| Payment processing | Sync | < 500ms p99 | Strong | High |
| Send welcome email | Async | No SLO (best effort) | Eventual | Low |
| Update user profile + notify followers | Sync (profile) + Async (notifications) | < 200ms p99 | Strong (profile), Eventual (notifications) | Medium |
| Financial audit log | Async (eventually consistent) | Acceptable 5-60min | Eventual (replay from DLQ if needed) | Medium |
| Real-time notification | Async (but fast, <1s) | < 1s p99 | Eventual | Medium |
