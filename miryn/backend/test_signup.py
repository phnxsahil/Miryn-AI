import asyncio
from app.api.auth import _login_guard, get_password_hash
from app.core.database import get_sql_session
from sqlalchemy import text
import traceback
import sys

def test():
    try:
        password_hash = get_password_hash("password123")
        print("Hash:", password_hash)
        
        with get_sql_session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash)
                        VALUES (:email, :password_hash)
                        RETURNING id, email
                        """
                    ),
                    {"email": "test7@example.com", "password_hash": password_hash},
                ).mappings().first()
                print("Result:", result)
            except Exception as e:
                print("Insert Error:")
                traceback.print_exc()
                
    except Exception as e:
        print("Error:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
