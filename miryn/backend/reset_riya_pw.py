import sqlite3
import os
import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

db_path = "miryn_demo.db"
password = "MirynDemo!2026"
email = "riya_v3@miryn.demo"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        pw_hash = get_password_hash(password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (pw_hash, email))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Password for {email} reset to {password}")
        else:
            print(f"User {email} not found.")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
