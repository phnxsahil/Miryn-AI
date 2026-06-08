# Performance Optimization Rationale: Bulk Inserts vs. N+1 Queries

## Problem Statement
The current implementation of `_log_identity_evolution_sql` in `miryn/backend/app/services/identity_engine.py` performs an individual `INSERT` query for each field that has changed in the identity. This is a classic N+1 query problem, where the number of database round-trips scales linearly with the number of changes.

## Optimization: Bulk Insert
The proposed optimization is to replace these individual calls with a single bulk insert operation (or `executemany` in SQLAlchemy/DB-API terms).

### Benefits:
1.  **Reduced Round-Trip Time (RTT):** Instead of $N$ round-trips to the database, we perform only 1. This is particularly significant if the database is on a different server or if there is high network latency.
2.  **Reduced Transaction Overhead:** Each individual `INSERT` typically carries its own transaction overhead unless explicitly wrapped in a single transaction. Even within a transaction, the database engine must parse, plan, and execute multiple statements. A bulk insert allows the database to process the data set more efficiently.
3.  **Lower CPU and Memory Usage:** Reducing the number of statement executions reduces the overhead on both the application server (fewer DB-API calls) and the database server (fewer queries to parse and log).
4.  **Atomicity and Consistency:** While already handled by the existing session scope, bulk operations are inherently atomic at the statement level.

### Quantitative Expectation:
In many database systems (like PostgreSQL or SQLite), bulk inserts can be orders of magnitude faster than individual inserts for large $N$. For the identity evolution log, $N$ is typically small (up to 10 fields), but the cumulative effect across many users and updates is significant.

## Environment Constraints
Due to the absence of the full runtime environment (SQLAlchemy and other dependencies) in the current sandbox, a live benchmark was not performed. Instead, this rationale serves as the theoretical basis for the optimization, supplemented by mock-based verification to ensure functional correctness.
