from typing import Optional
from contextlib import contextmanager
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings


class Database:
    def __init__(self) -> None:
        self.supabase: Optional[Client] = None
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )

        self.engine = None
        self.SessionLocal = None
        if settings.DATABASE_URL:
            self.engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)


_db = Database()


def get_db() -> Client:
    if not _db.supabase:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    return _db.supabase


def has_sql() -> bool:
    return _db.SessionLocal is not None


def get_sql_engine():
    if not _db.engine:
        raise RuntimeError("DATABASE_URL not configured.")
    return _db.engine


@contextmanager
def get_sql_session():
    if not _db.SessionLocal:
        raise RuntimeError("DATABASE_URL not configured.")
    db = _db.SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
