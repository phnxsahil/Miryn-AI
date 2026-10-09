from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import time
import json
import logging
import threading
import hashlib
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.config import settings


logger = logging.getLogger(__name__)
_PURGE_INTERVAL_SECONDS = 3600
_last_purge_ts: float = 0.0
_last_purge_lock = threading.Lock()


def _maybe_purge():
    global _last_purge_ts
    retention_days = settings.AUDIT_RETENTION_DAYS
    if not retention_days:
        return
    now = time.time()
    should_purge = False
    with _last_purge_lock:
        if now - _last_purge_ts >= _PURGE_INTERVAL_SECONDS:
            _last_purge_ts = now
            should_purge = True
    if should_purge:
        purge_expired_audit_logs(retention_days)


def _normalize_metadata(metadata: Optional[Dict[str, Any]] = None) -> str:
    try:
        return json.dumps(metadata or {})
    except (TypeError, ValueError):
        logger.warning("Failed to serialize audit metadata, storing empty object")
        return json.dumps({})


def _now_utc():
    return datetime.now(timezone.utc)


def _safe_user_ref(user_id: Optional[str]) -> str:
    if not user_id:
        return "anon"
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return f"user:{digest[:10]}"


def log_event(
    event_type: str,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    force_pii: bool = False,
):
    _maybe_purge()

    if user_agent:
        user_agent = user_agent[:512]
    if not settings.AUDIT_STORE_PII and not force_pii:
        ip = None
        user_agent = None

    serialized_metadata = _normalize_metadata(metadata)
    created_at = _now_utc()

    if has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        INSERT INTO audit_logs (
                            user_id, event_type, path, method, status_code, ip, user_agent, metadata, created_at
                        ) VALUES (
                            :user_id, :event_type, :path, :method, :status_code, :ip, :user_agent, :metadata, :created_at
                        )
                        """
                    ),
                    {
                        "user_id": user_id,
                        "event_type": event_type,
                        "path": path,
                        "method": method,
                        "status_code": status_code,
                        "ip": ip,
                        "user_agent": user_agent,
                        "metadata": serialized_metadata,
                        "created_at": created_at,
                    },
                )
            return
        except Exception:
            logger.exception("Failed to persist audit log (SQL backend)")
            return

    try:
        db = get_db()
        db.table("audit_logs").insert({
            "user_id": user_id,
            "event_type": event_type,
            "path": path,
            "method": method,
            "status_code": status_code,
            "ip": ip,
            "user_agent": user_agent,
            "metadata": serialized_metadata,
            "created_at": created_at.isoformat(),
        }).execute()
    except Exception:
        logger.exception("Failed to persist audit log (Supabase backend)")


def purge_expired_audit_logs(retention_days: Optional[int] = None) -> None:
    days = retention_days or settings.AUDIT_RETENTION_DAYS
    if not days:
        return
    cutoff = _now_utc() - timedelta(days=days)
    if has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text("DELETE FROM audit_logs WHERE created_at < :cutoff"),
                    {"cutoff": cutoff},
                )
        except Exception:
            logger.exception("Failed to purge audit logs (SQL backend)")
    else:
        try:
            db = get_db()
            db.table("audit_logs").delete().lt("created_at", cutoff.isoformat()).execute()
        except Exception:
            logger.exception("Failed to purge audit logs (Supabase backend)")


def anonymize_audit_logs(user_id: str) -> None:
    if not user_id:
        return
    if has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text("UPDATE audit_logs SET ip = NULL, user_agent = NULL WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
        except Exception:
            logger.exception("Failed to anonymize audit logs for %s", _safe_user_ref(user_id))
    else:
        try:
            db = get_db()
            db.table("audit_logs").update({"ip": None, "user_agent": None}).eq("user_id", user_id).execute()
        except Exception:
            logger.exception(
                "Failed to anonymize audit logs (Supabase) for %s",
                _safe_user_ref(user_id),
            )
