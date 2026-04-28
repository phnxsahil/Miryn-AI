from typing import Optional
from contextlib import contextmanager
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)


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
        self._sql_health_checked_at: datetime | None = None
        self._sql_healthy = False
        if settings.DATABASE_URL:
            self.engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000 -c lock_timeout=10000",
                },
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def sql_available(self) -> bool:
        if not self.SessionLocal or not self.engine:
            return False

        now = datetime.utcnow()
        if self._sql_health_checked_at and now - self._sql_health_checked_at < timedelta(seconds=30):
            return self._sql_healthy

        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            self._sql_healthy = True
        except Exception as exc:
            self._sql_healthy = False
            logger.warning("SQL connection unavailable, falling back to Supabase: %s", exc)
        finally:
            self._sql_health_checked_at = now

        return self._sql_healthy


_db = Database()


def get_db() -> Client:
    if not _db.supabase:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    return _db.supabase


def has_sql() -> bool:
    return _db.sql_available()


def get_sql_engine():
    if not _db.engine:
        raise RuntimeError("DATABASE_URL not configured.")
    return _db.engine


@contextmanager
def get_sql_session():
    if not _db.SessionLocal or not _db.engine:
        raise RuntimeError("DATABASE_URL not configured.")

    if not _db.sql_available():
        raise RuntimeError("SQL connection unavailable.")

    db = _db.SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
