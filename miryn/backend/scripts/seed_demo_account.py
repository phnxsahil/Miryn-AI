"""Provision the single demo account the login screen offers.

Idempotent and re-runnable: creates the account if it is missing, otherwise
resets its password so the published demo credentials always work after a
database reset.

    cd miryn/backend && python scripts/seed_demo_account.py
"""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.core.database import get_db, get_sql_session, has_sql
from app.core.security import get_password_hash

DEMO_EMAIL = "persona.alpha@miryn.demo"
DEMO_PASSWORD = "MirynDemo!2026"
DEMO_NAME = "Aditya Verma"


def _set_profile_name(user_id: str) -> None:
    """Best-effort profile name, in its own transaction.

    Deliberately separate from the account write: on Postgres a failed statement
    aborts the whole transaction, so sharing one session would roll the demo
    account back whenever the profiles table is missing (as it is on a database
    that predates migration 009).
    """
    try:
        if has_sql():
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        INSERT INTO user_profiles (user_id, full_name)
                        VALUES (:user_id, :full_name)
                        ON CONFLICT (user_id) DO UPDATE SET full_name = EXCLUDED.full_name
                        """
                    ),
                    {"user_id": user_id, "full_name": DEMO_NAME},
                )
        else:
            get_db().table("user_profiles").upsert(
                {"user_id": user_id, "full_name": DEMO_NAME}, on_conflict="user_id"
            ).execute()
        print(f"  profile name set to {DEMO_NAME!r}")
    except Exception as exc:
        print(f"  (no profile name stored: {type(exc).__name__}: {str(exc).splitlines()[0]})")


def main() -> int:
    password_hash = get_password_hash(DEMO_PASSWORD)

    if has_sql():
        with get_sql_session() as session:
            row = session.execute(
                text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                {"email": DEMO_EMAIL},
            ).mappings().first()

            if row:
                user_id = str(row["id"])
                session.execute(
                    text("UPDATE users SET password_hash = :h, is_deleted = false WHERE id = :id"),
                    {"h": password_hash, "id": user_id},
                )
                print(f"reset password for existing demo user {DEMO_EMAIL}")
            else:
                user_id = str(uuid4())
                session.execute(
                    text(
                        "INSERT INTO users (id, email, password_hash) VALUES (:id, :email, :h)"
                    ),
                    {"id": user_id, "email": DEMO_EMAIL, "h": password_hash},
                )
                print(f"created demo user {DEMO_EMAIL}")
    else:
        db = get_db()
        res = db.table("users").select("id").eq("email", DEMO_EMAIL).limit(1).execute()
        row = (res.data or [None])[0]

        if row:
            user_id = str(row["id"])
            db.table("users").update(
                {"password_hash": password_hash, "is_deleted": False}
            ).eq("id", user_id).execute()
            print(f"reset password for existing demo user {DEMO_EMAIL}")
        else:
            created = (
                db.table("users")
                .insert({"email": DEMO_EMAIL, "password_hash": password_hash})
                .execute()
            )
            user_id = str(created.data[0]["id"])
            print(f"created demo user {DEMO_EMAIL}")

    # The account is committed by now, so a missing user_profiles table cannot
    # undo it.
    _set_profile_name(user_id)

    print(f"  email   : {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")
    print(f"  user_id : {user_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
