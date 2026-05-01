import sqlalchemy
from sqlalchemy import text
import os

DB_URL = "sqlite:///./miryn_demo.db"
engine = sqlalchemy.create_engine(DB_URL)

sql_file = "migrations/000_sqlite_init.sql"
if not os.path.exists(sql_file):
    print(f"Error: {sql_file} not found")
    exit(1)

with open(sql_file, "r") as f:
    sql = f.read()

print("Initializing SQLite Database...")
with engine.connect() as conn:
    # Split by semicolon but handle multiline
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for s in statements:
        try:
            conn.execute(text(s))
            print(f"Executed statement: {s[:50]}...")
        except Exception as e:
            print(f"Error executing: {s[:50]}... -> {e}")
    conn.commit()

print("Database initialized successfully.")
