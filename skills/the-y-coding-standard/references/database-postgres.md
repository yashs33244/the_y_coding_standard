# Database and PostgreSQL Standards

## When to load this file

Load this reference when:
- Touching any `.sql` file.
- Designing or modifying schema.
- Writing or reviewing a migration.
- Optimizing a query or debugging a slow endpoint.
- Making indexing decisions or reading an EXPLAIN plan.
- Provisioning a new database or wiring up a Postgres client.
- Building anything that talks to Postgres from application code.

If your task touches the database, this file applies. No exceptions.

## Target version

Postgres 16+. Latest stable is what we ship on. When provisioning a new instance, run a WebSearch for "latest stable Postgres version" before picking a number. Do not default to whatever was current last year.

## Hosting posture

Prefer managed Postgres. Self-managed Postgres is a tax I do not pay on new projects.

Pick one of these for new projects:
- **Neon** for serverless-first apps. Branching is a real feature, not a checkbox.
- **Supabase** when I want auth, storage, and realtime bundled with the DB.
- **Vercel Postgres** (Neon under the hood) when the app already lives on Vercel and I want one bill.

Self-hosted Postgres is only acceptable when there is a hard requirement that managed cannot meet (data residency, compliance, extreme cost at scale). Otherwise, no.

## Naming Conventions

Everything lowercase, snake_case. No CamelCase. No quoted identifiers. Ever.

| Thing | Convention | Example |
|---|---|---|
| Tables | plural snake_case | `users`, `order_items` |
| Columns | singular snake_case | `created_at`, `user_id` |
| Primary keys | `id` (type: `uuid`) | `id uuid PRIMARY KEY` |
| Foreign keys | `<referenced_table_singular>_id` | `user_id`, `product_id` |
| Indexes | `idx_<table>_<column(s)>` | `idx_users_email` |
| Unique constraints | `uq_<table>_<column(s)>` | `uq_users_email` |
| Check constraints | `ck_<table>_<description>` | `ck_orders_status` |
| Junction tables | `<table_a>_<table_b>` (alphabetical) | `roles_users` |

## Schema Design Principles

### Required columns on every table

Every table gets these three columns. No exceptions. If you think your table is special, it is not.

```sql
id          UUID PRIMARY KEY DEFAULT uuidv7(),
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### UUIDv7 over UUIDv4

UUIDv7 is sortable by time. UUIDv4 is not. Sortable IDs mean btree indexes stay tight and pagination plays nice with insertion order. Use UUIDv7.

If your Postgres version or extension does not have `uuidv7()` natively, install `pg_uuidv7` or generate UUIDv7 in app code. Do not fall back to UUIDv4 silently. Pick UUIDv7 deliberately.

`BIGSERIAL` is allowed only for high-throughput append-only tables (events, audit logs) where the storage and index cost of UUIDs is measurable. Default is UUIDv7.

### Timestamps

Always `TIMESTAMPTZ`. Never bare `TIMESTAMP`. Store UTC, display in the user's timezone. Trigger or ORM hook updates `updated_at` on every write.

### Soft deletes

Use `deleted_at TIMESTAMPTZ` when audit trails matter. Pair it with a partial index excluding deleted rows from common queries:

```sql
CREATE INDEX idx_orders_active ON orders(user_id) WHERE deleted_at IS NULL;
```

## Column Types

| Use case | Type |
|---|---|
| IDs | `UUID` (UUIDv7) |
| Short text (name, email) | `VARCHAR(255)` or `TEXT` |
| Long text | `TEXT` |
| Money or currency | `NUMERIC(19, 4)`. Never `FLOAT`. Never. |
| Status or enum | `TEXT` + CHECK constraint, or Postgres `ENUM` |
| JSON payloads | `JSONB` (binary, indexed). Not `JSON`. |
| Flags | `BOOLEAN NOT NULL DEFAULT FALSE` |
| Timestamps | `TIMESTAMPTZ` |
| Embeddings (AI features) | `vector(n)` from pgvector |

## Migrations

Migrations are mandatory. Hand-editing the database is a fireable offense.

Pick the tool that matches the stack:

| Stack | Tool |
|---|---|
| TypeScript (Drizzle) | Drizzle Kit |
| TypeScript (Prisma) | Prisma Migrate |
| Python | Alembic |
| Java | Flyway |

Rules that apply across all of them:

- Every schema change goes through a migration file. No exceptions.
- Every migration ships with a rollback path. Either a down migration, or a documented manual rollback in the PR description. If you cannot describe how to undo it, you do not understand it yet.
- Migration files are immutable once merged to main. Fix a mistake with a new migration.
- Name migrations descriptively: `V3__add_index_on_orders_user_id.sql` or `0003_add_index_on_orders_user_id.ts`.
- Test every migration on a staging copy before production.
- Large-table `ALTER TABLE` operations need a locking review. Prefer `pg_repack` or online schema change tools when the table is hot.

Example migration:

```sql
-- V2__create_orders_table.sql
CREATE TABLE orders (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled')),
    total       NUMERIC(19, 4) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status) WHERE status != 'cancelled';
```

### Backfills

Adding a NOT NULL column to a populated table is a three-step move, not a one-liner:

1. Add the column as nullable with a default.
2. Backfill in batches. Batched updates of 1k to 10k rows with a sleep. Never a single massive `UPDATE` that locks the table.
3. Once backfill is verified, add the NOT NULL constraint.

A single `UPDATE table SET col = ...` across millions of rows is how you take production down. Do not do it.

### Destructive migrations

`DROP COLUMN`, `DROP TABLE`, and `RENAME` are destructive. Protocol:

1. Ship a feature flag that stops reads of the column or table.
2. Verify zero traffic against the dropped surface for a full deploy cycle (minimum 24 hours, longer if traffic is uneven).
3. Then ship the destructive migration.

No flag, no drop. Code that still references the column after the migration is a P0.

## Indexing Strategy

- Every foreign key column gets an index. Postgres does not create these automatically. If your migration adds a foreign key, the same migration adds the index. This is non-negotiable.
- Every column referenced in a `WHERE`, `ORDER BY`, or `JOIN` gets an index after a query plan review. Not before. Review the `EXPLAIN ANALYZE` output, then add the index.
- Partial indexes for filtered queries: `CREATE INDEX ... WHERE deleted_at IS NULL`.
- Composite indexes for multi-column filters. Column order matters. Most selective first, or match the WHERE clause order if equality conditions dominate.
- Monitor `pg_stat_user_indexes`. Unused indexes are pure cost. Drop them.

## Query Rules

### Never use SELECT * in application code

Name every column you intend to read. `SELECT *` is a footgun:
- Schema changes silently change the shape of your result.
- You pay network and serialization cost for columns you do not use.
- ORM hydration over fields you did not mean to load.

`SELECT *` is acceptable in an interactive psql session for inspection. Nowhere else.

```sql
-- Bad
SELECT * FROM users WHERE email = $1;

-- Good
SELECT id, email, created_at FROM users WHERE email = $1;
```

### Parameterized queries always

No string interpolation into SQL. Ever. Not "just this once." Not "the input is trusted." Not for admin tools. Never.

```ts
// Bad
db.query(`SELECT * FROM users WHERE email = '${email}'`);

// Good
db.query('SELECT id, email FROM users WHERE email = $1', [email]);
```

Every ORM and driver supports parameter binding. Use it. If you find yourself building SQL with template strings, stop and rewrite.

### No N+1 queries

Always batch related data with JOINs, subqueries, or a single `WHERE id IN (...)`. Never a loop that fires one query per item. Use the ORM's eager loading (`with`, `include`, `joinedload`) or write the JOIN yourself.

### EXPLAIN ANALYZE before shipping

Run `EXPLAIN ANALYZE` on every non-trivial query before it hits production. Look for:
- Sequential scans on large tables. Add an index.
- Nested loop joins on large tables. Consider a hash join via query rewrite.
- Cost estimates that disagree with actual rows. Run `ANALYZE` on the table.

### Pagination

Keyset (cursor) pagination over `OFFSET` for any list that grows past a few hundred rows.

```sql
-- Bad: O(n) for large offsets
SELECT id, status, total FROM orders
ORDER BY created_at DESC
LIMIT 20 OFFSET 10000;

-- Good: O(log n) with an index on created_at
SELECT id, status, total FROM orders
WHERE created_at < $1
ORDER BY created_at DESC
LIMIT 20;
```

### Transactions

Wrap multi-step writes in a single transaction. Keep transactions short. Long transactions hold locks and block other writers. Do not call external APIs inside a transaction.

## Connection Management

Pooling is mandatory.

- Local dev: built-in pool of your driver (`pg.Pool`, SQLAlchemy pool, HikariCP) is fine.
- Production long-running services: `pgBouncer` in transaction mode.
- Serverless (Vercel functions, Lambda, Cloudflare Workers): the Neon, Supabase, or Vercel pooler. Always. Never raw connections from serverless. A cold function opening a fresh TCP connection per invocation will exhaust Postgres `max_connections` and take the database down.

Pool sizing starting point: `(CPU cores * 2) + effective_spindle_count`. Tune from there based on `pg_stat_activity`.

### Read-write splitting

Most apps do not need this. Do not add a read replica because it sounds cool. Add it when:
- Read traffic is provably saturating the primary.
- You have measured query latency degradation correlated with read load.
- You can tolerate replica lag in the affected code paths.

Otherwise, one primary is enough.

## AI Features: pgvector

Embeddings live in Postgres via `pgvector`. Default for any AI feature.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

Reach for a dedicated vector DB (Pinecone, Weaviate, Qdrant) only when pgvector measurably stops scaling. For 99% of apps, that day never comes.

## Security

- Parameterized queries. Always. See above. This rule shows up twice on purpose.
- Row-level security for multi-tenant data. Tenant isolation in the database, not just the app layer.
- Least privilege. The application user gets `SELECT, INSERT, UPDATE, DELETE` on the tables it needs. Not `CREATE`. Not `DROP`. Not superuser. Migrations run under a separate role.
- Never store secrets in plaintext. Hash passwords with argon2 or bcrypt at the application layer. `pgcrypto` is acceptable for column-level encryption of PII when keys are managed outside the database.
- Connection strings are secrets. They live in environment variables or the platform secret store. Never in code, never in `.env` files committed to git.

## When this reference loads

This file should be in context whenever the task involves:

- Writing or reviewing SQL (any `.sql` file).
- Schema design or table creation.
- Migrations (Drizzle Kit, Prisma Migrate, Alembic, Flyway, or raw SQL).
- Query optimization or debugging a slow query.
- Indexing decisions or EXPLAIN plan review.
- Provisioning a new Postgres instance on Neon, Supabase, or Vercel.
- Wiring up a Postgres client in application code (driver, ORM, pooler).
- Adding pgvector or any AI feature backed by embeddings.
- Anything labeled "database" in a plan or PR.

If the task is "is this query fast enough" or "should this be an index" or "how do I roll this migration back", this file applies. Load it and follow it.
