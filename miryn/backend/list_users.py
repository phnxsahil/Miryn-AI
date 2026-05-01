import sqlite3
import os

db_path = "miryn_demo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email FROM users LIMIT 10")
        users = cursor.fetchall()
        for u in users:
            print(u[0])
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
