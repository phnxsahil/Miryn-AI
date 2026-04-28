#!/usr/bin/env python3
"""Run all SQL migration files against the database in order.

Usage:
    python -m app.run_migrations

Reads DATABASE_URL from the environment. Each .sql file in the migrations/
directory is executed in sorted (lexicographic) order. Migrations are
idempotent by convention (CREATE TABLE IF NOT EXISTS, ALTER TABLE ... ADD
COLUMN IF NOT EXISTS, etc.).
"""

import os
import sys
from pathlib import Path

import sqlalchemy
from sqlalchemy import text


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)

    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    if not migrations_dir.exists():
        print(f"No migrations directory found at {migrations_dir}")
        sys.exit(0)

    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print("No migration files found")
        sys.exit(0)

    engine = sqlalchemy.create_engine(database_url)
    try:
        for sql_file in sql_files:
            print(f"Running migration: {sql_file.name}")
            sql_content = sql_file.read_text()

            with engine.begin() as conn:
                conn.execute(text(sql_content))

            print(f"Applied {sql_file.name}")

        print(f"\nAll {len(sql_files)} migrations applied successfully")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
