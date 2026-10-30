"""Aggregate account counts only. Never select email, messages, or identity data."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import text

REPORTING_ZONE = ZoneInfo("Asia/Kolkata")
UTC_ZONE = ZoneInfo("UTC")


def read_account_metrics(session, days=30, now=None):
    now = now or datetime.utcnow()
    local_now = now.replace(tzinfo=UTC_ZONE).astimezone(REPORTING_ZONE)
    local_today = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = local_today.astimezone(UTC_ZONE).replace(tzinfo=None)
    start = today - timedelta(days=days - 1)
    local_start = local_today - timedelta(days=days - 1)
    summary = session.execute(text("""
        SELECT COUNT(*) AS accounts_created,
          COALESCE(SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END), 0) AS active_accounts,
          COALESCE(SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END), 0) AS deleted_accounts,
          COALESCE(SUM(CASE WHEN created_at >= :today AND created_at <= :now THEN 1 ELSE 0 END), 0) AS new_today,
          COALESCE(SUM(CASE WHEN created_at >= :week AND created_at <= :now THEN 1 ELSE 0 END), 0) AS new_last_7_days,
          COALESCE(SUM(CASE WHEN created_at >= :start AND created_at <= :now THEN 1 ELSE 0 END), 0) AS new_in_period
        FROM users
    """), {"today": today, "week": today - timedelta(days=6), "start": start, "now": now}).mappings().one()
    day_expression = "DATE(created_at + INTERVAL '5 hours 30 minutes')"
    if getattr(session, "bind", session).dialect.name == "sqlite":
        day_expression = "DATE(created_at, '+5 hours', '+30 minutes')"
    rows = session.execute(text(f"""
        SELECT {day_expression} AS day, COUNT(*) AS count FROM users
        WHERE created_at >= :start AND created_at <= :now
        GROUP BY {day_expression} ORDER BY day
    """), {"start": start, "now": now}).mappings().all()
    by_day = {str(row["day"]): int(row["count"]) for row in rows}
    return {
        "generated_at": now.isoformat() + "Z", "timezone": "Asia/Kolkata", "days": days,
        **{key: int(value) for key, value in summary.items()},
        "daily_signups": [{"date": (local_start + timedelta(days=i)).date().isoformat(),
                           "count": by_day.get((local_start + timedelta(days=i)).date().isoformat(), 0)}
                          for i in range(days)],
        "notes": ["Counts include owner and test accounts; no automatic exclusions.",
                  "Accounts created includes soft-deleted accounts still retained in the database.",
                  "Active means not marked deleted, not recently active or verified.",
                  "Deleted records that were permanently removed cannot be reconstructed."]
    }
