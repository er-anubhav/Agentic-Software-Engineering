# ADR-003: Repository Pattern & ACID SQLite Relational Persistence

## Status
Accepted

## Context
Early implementations used parallel in-memory dictionaries alongside JSON files, creating dual-source-of-truth divergence risks and data loss on process restart.

## Decision
1. Define abstract `RelationalStore` contract implemented by `SQLiteStore` (and `PostgresStore` facade).
2. Configure SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), thread-local connection management with automatic health-check reconnects, and transaction context management (`with store.transaction():`).
3. Provide explicit `JobRepository` and `CheckpointRepository` abstractions querying database tables directly as the single source of truth.

## Consequences
- Complete data persistence across process restarts.
- Zero dual-source-of-truth state divergence.
