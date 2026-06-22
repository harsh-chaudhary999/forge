# Indexing Strategy

Proper indexing ensures performance and prevents database bloat.

## Primary Key Design

**Auto-increment (INT/BIGINT):**
```sql
-- Traditional: simple, small, sequential
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advantages: small storage, fast lookups
-- Disadvantages: sequential (security risk?), max 2^63 values
```

**UUID (VARCHAR(36)):**
```sql
-- UUID: globally unique, distributed
CREATE TABLE sessions (
  id CHAR(36) PRIMARY KEY,  -- UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  user_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Advantages: distributed, no collisions, secure
-- Disadvantages: larger storage (36 bytes), slower joins
```

**Rules:**
- Use BIGINT for most tables (8 bytes)
- Use UUID only if distributed generation needed
- Use INT (4 bytes) only for small tables (< 2 billion rows)
- Primary key should never change (use surrogate key)

## Foreign Key Indexes

Always index foreign keys:

```sql
-- Foreign key automatically creates index on the same side
-- BUT you must also index the child side:
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  INDEX idx_customer_id (customer_id)  -- IMPORTANT: for lookups, deletes
);

-- Query: Find all orders for a customer
EXPLAIN SELECT * FROM orders WHERE customer_id = 123;  -- Uses idx_customer_id
```

**Rules:**
- Every FOREIGN KEY must have an INDEX on the same column
- Index improves DELETE performance (CASCADE deletes)
- Index improves JOIN performance
- Naming convention: `idx_<table>_<column>` or `idx_<column>`

## Query Performance Indexes

Indexes should be based on actual query patterns:

```sql
CREATE TABLE user_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  device_type VARCHAR(50),
  
  INDEX idx_user_id (user_id),  -- For lookups
  INDEX idx_status (status),     -- For filtering
  INDEX idx_last_activity (last_activity),  -- For ORDER BY
  INDEX idx_device_type (device_type),  -- (created speculatively; never read -> dropped in the unused-index example below)
  INDEX idx_user_status (user_id, status)   -- Composite: both WHERE clauses
);

-- Query patterns (inform indexing):
-- 1. Find active sessions for user
EXPLAIN SELECT * FROM user_sessions 
  WHERE user_id = 123 AND status = 'active';
-- Uses: idx_user_status (composite)

-- 2. Find oldest inactive sessions
EXPLAIN SELECT * FROM user_sessions 
  WHERE status = 'inactive' 
  ORDER BY last_activity ASC 
  LIMIT 10;
-- Uses: idx_status, then sorts by last_activity

-- 3. Find devices used in last 7 days
EXPLAIN SELECT DISTINCT device_type FROM user_sessions 
  WHERE last_activity > NOW() - INTERVAL 7 DAY;
-- Uses: idx_last_activity
```

**Rules:**
- Index columns in WHERE clauses (filtering)
- Index columns in JOIN conditions
- Index ORDER BY columns
- Composite indexes: most selective first (user_id before status)
- Monitor EXPLAIN output for "Using index" vs "Using temporary"

## Index Bloat Monitoring

Over-indexing causes INSERT/UPDATE slowdowns:

```sql
-- Find unused indexes
SELECT OBJECT_SCHEMA, OBJECT_NAME, INDEX_NAME, COUNT_READ, COUNT_INSERT, COUNT_UPDATE, COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA != 'mysql'
  AND COUNT_READ = 0  -- Never read
  AND (COUNT_INSERT > 0 OR COUNT_UPDATE > 0 OR COUNT_DELETE > 0)
ORDER BY COUNT_INSERT + COUNT_UPDATE + COUNT_DELETE DESC;

-- Find slow indexes
SHOW INDEXES FROM users;
-- Manually review index coverage and selectivity

-- Drop unused index
ALTER TABLE user_sessions DROP INDEX idx_device_type;
```

**Rules:**
- Review index usage monthly
- Drop indexes with COUNT_READ = 0
- Each index costs ~1-5% on INSERT/UPDATE
- Aim for 3-7 indexes per table maximum
- Document why each index exists in migration comment
