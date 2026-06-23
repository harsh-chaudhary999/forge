# Deployment & Migration Patterns

## Pattern 1: Zero-Downtime Database Migrations

**Scenario:** Add new column to `users` table. Migrate data. Keep service running.

**Timeline:**
```
Phase 1: Prepare (pre-deployment, 30 min)
  - Create column (nullable): ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT NULL
  - Verify column created, not used yet

Phase 2: Code Deploy (0-5 min downtime if needed)
  - Code deployed with feature flag OFF
  - Code reads/writes old column only
  - New column is present but unused
  
Phase 3: Backfill (1-2 hours, running in background)
  - Backfill job: SELECT id FROM users WHERE status IS NULL LIMIT 10000
  - Update in batches of 10k, sleep 1s between batches
  - Monitor progress, ensure replication not lagging
  
Phase 4: Cutover (5 min)
  - Feature flag ON
  - Code now reads/writes new column
  - Old column still present for rollback
  
Phase 5: Cleanup (next release, 5 min)
  - Drop old column: ALTER TABLE users DROP COLUMN old_column
  - Verify code doesn't reference old column
```

**Safety:**
- Rollback safe: old column exists, code checks both, prefers new
- Replication safe: backfill is slow to not overload secondary
- Feature flag safe: if new column broken, flip flag OFF, revert reads to old

---

## Pattern 2: Blue-Green Elasticsearch Reindex

**Scenario:** Elasticsearch index schema changes. Reindex 2B documents without downtime.

**Timeline:**
```
Phase 1: Create green index
  - Create new index "products_green" with new schema
  - Apply reindex: POST _reindex source=products_blue, dest=products_green
  - Reindex runs in background (takes 2-4 hours for 2B docs)
  
Phase 2: Verify green
  - When green 100% reindexed: run validation
  - Sample 1000 random docs, verify schema correct
  - Run test queries on green, verify results match blue
  
Phase 3: Switch alias
  - Update alias: products → products_green (was products_blue)
  - All traffic switches to green immediately
  - Blue still exists for rollback
  
Phase 4: Cleanup
  - After 24h: delete blue index (save disk space)
```

**Safety:**
- No downtime: alias switch is atomic
- Rollback easy: alias points back to blue if green broken
- Parallel: reindexing doesn't affect blue (normal read/write traffic continues)

---

## Pattern 3: Feature Flag Driven Rollout

**Scenario:** Add new caching layer. Gradually increase traffic without full deployment.

**Code:**
```python
def get_user_profile(user_id):
  if feature_flag_enabled('use_cache_v2'):
    try:
      return redis_v2.get(f'user:{user_id}')
    except Exception:
      # fall back to database
      pass
  return database.query(f'SELECT * FROM users WHERE id={user_id}')
```

**Rollout:**
```
Canary (5% of traffic):
  - Feature flag: use_cache_v2 = 5%
  - Monitor: cache hit rate, latency, errors
  - Wait 30m: ensure stable
  
Ramp (25% of traffic):
  - Feature flag: use_cache_v2 = 25%
  - Monitor: cache memory, evictions
  - Wait 1h: ensure stable
  
Production (100%):
  - Feature flag: use_cache_v2 = 100%
  - All traffic uses v2
  - Continue monitoring for 24h
```

**Rollback:**
- Feature flag: use_cache_v2 = 0
- All traffic reverts to database
- Instant, no code redeploy needed

---

## Pattern 4: Canary Deployment (Kubernetes)

**Scenario:** Deploy new MySQL connection pool logic. Test on 10% of replicas first.

**Strategy:**
```
Canary (1 replica, 10% traffic):
  - Deploy new code to 1 replica instance
  - Route 10% of read traffic to this replica
  - Monitor latency, errors, CPU
  - Threshold: if p99 latency > baseline + 20%, auto-rollback canary
  
Ramp (3 replicas, 30% traffic):
  - If canary stable for 30m: deploy to 3 more replicas
  - Route 30% of traffic to these 4
  
Production (all replicas, 100%):
  - Deploy to all replicas
  - Monitor for 24h for regression
```

**Metrics to Monitor:**
- Latency p99, p95 (should stay within ±5% of baseline)
- Error rate (should be < 0.1% vs baseline)
- Connection pool utilization (should be ±10% of baseline)
- CPU usage (should be ±10% of baseline)

---

## Pattern 5: Kafka Consumer Group Upgrade

**Scenario:** Consumer code has bug (doesn't handle certain event types). Fix code, deploy with new consumer group.

**Timeline:**
```
Phase 1: Deploy new consumer group
  - New code in parallel branch: consumer_group_v2
  - Both v1 (old, in prod) and v2 (new, in staging) read same topic
  - v2 doesn't commit offsets yet (run in shadow mode)
  
Phase 2: Validate new consumer
  - v2 runs for 24h without committing
  - Compare v2 output with v1: ensure same messages processed
  - If v2 correct: proceed
  
Phase 3: Switch
  - v1: stop consuming (stop deployment, don't crash)
  - v2: start consuming from v1's last offset (resume processing)
  - If v2 breaks: kill v2, restart v1 (only lost 1-2m of messages)
  
Phase 4: Cleanup
  - After 7 days: delete v1 consumer group (stop alerting)
```

**Safety:**
- No message loss: v1 and v2 read same topic, v2 catches up
- Easy rollback: restart v1 if v2 broken
- Validation: 24h dry-run ensures correctness

---

## Pattern 6: Database Failover & Switchback

**Scenario:** Primary database failing. Failover to replica. Repair primary. Switchback.

**Emergency Failover (< 5 min):**
```
Step 1: Detect failure
  - Alert: primary not responding
  - Confirm: can't connect from multiple regions
  
Step 2: Promote replica
  - Replica becomes new primary
  - DNS: primary → replica (updates in 5-30s)
  - App: automatically reconnects (connection pooler does retry)
  
Step 3: Disable old primary (prevent split-brain)
  - Firewall: block old primary from cluster
  - Or: stop MySQL process
  
Step 4: Monitor new primary
  - Verify writes working: insert test record
  - Verify replicas replicating from new primary
  - Alert: page oncall team
```

**Repair & Switchback (1-4 hours):**
```
Step 1: Repair old primary
  - Hardware: replace disk, reboot
  - MySQL: `RESET MASTER` (clear binary logs), start fresh
  
Step 2: Resync old primary as replica
  - Configure old primary to replicate from new primary
  - Monitor: replication lag until caught up
  
Step 3: Switchback (optional)
  - If old primary healthy: switchback (requires downtime)
  - Or: keep new primary in place, old as replica
```

**Metrics to Monitor:**
- Connection count on new primary (should match old)
- Replication lag on new replicas (should converge < 5s)
- Error rate (should return to normal)
