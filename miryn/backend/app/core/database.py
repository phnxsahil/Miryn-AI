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
            is_postgres = settings.DATABASE_URL.startswith("postgresql")
            connect_args = {}
            if is_postgres:
                connect_args = {
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000 -c lock_timeout=10000",
                }
            else:
                connect_args = {"check_same_thread": False, "timeout": 30}
            
            engine_kwargs = {
                "pool_pre_ping": True,
                "connect_args": connect_args,
            }
            if is_postgres:
                engine_kwargs.update({
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_timeout": 30,
                })
            
            self.engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
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


import threading

_sqlite_lock = threading.Lock()

@contextmanager
def get_sql_session():
    if not _db.SessionLocal or not _db.engine:
        raise RuntimeError("DATABASE_URL not configured.")

    if not _db.sql_available():
        raise RuntimeError("SQL connection unavailable.")

    is_sqlite = _db.engine.url.drivername == "sqlite"
    
    if is_sqlite:
        _sqlite_lock.acquire()

    db = _db.SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        if is_sqlite:
            _sqlite_lock.release()
