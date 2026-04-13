"""
Identity Analytics Service - Divyadeep Kaur
Analyzes identity versions from the identities table to compute stability, drift, and timeline.
"""
import json
import logging
import math
from sqlalchemy import text

from app.core.database import get_db, has_sql, get_sql_session

logger = logging.getLogger(__name__)


class IdentityAnalytics:

    def __init__(self):
        self.supabase = get_db() if not has_sql() else None

    def analyze(self, user_id: str) -> dict:
        versions = self._fetch_versions(user_id)  # raises on DB error
        if not versions:
            return {
                "message": "No identity data yet.",
                "stability_score": None,
                "drift": None,
                "total_versions": 0,
                "version_timeline": [],
            }
        return {
            "stability_score": self._stability_score(versions),
            "drift": self._drift(versions),
            "total_versions": len(versions),
            "version_timeline": self._timeline(versions),
        }

    def _fetch_versions(self, user_id: str) -> list:
        """Raises on DB failure — never masks outages as empty data."""
        try:
            if has_sql():
                with get_sql_session() as session:
                    result = session.execute(
                        text(
                            """
                            SELECT version, beliefs, open_loops, created_at
                            FROM identities
                            WHERE user_id = :user_id
                            ORDER BY version ASC
                            """
                        ),
                        {"user_id": user_id},
                    )
                    return [dict(r) for r in result.mappings().all()]
            else:
                response = (
                    self.supabase.table("identities")
                    .select("version, beliefs, open_loops, created_at")
                    .eq("user_id", user_id)
                    .order("version")
                    .execute()
                )
                return response.data or []
        except Exception as e:
            logger.error(
                "Failed to fetch identity versions for user %s: %s", user_id, e
            )
            raise  # propagate so FastAPI returns a real 500

    def _parse_list(self, val) -> list:
        """Safely parse a DB value into a list (handles JSON strings)."""
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        return []

    def _stability_score(self, versions: list) -> float:
        """
        Stability based on how consistent belief counts are across versions.
        Returns 1.0 if only one version exists.
        """
        if len(versions) < 2:
            return 1.0
        belief_counts = [len(self._parse_list(v.get("beliefs"))) for v in versions]
        if max(belief_counts) == 0:
            return 1.0
        variance = statistics_variance(belief_counts)
        # Normalize: low variance = high stability
        stability = 1.0 / (1.0 + variance)
        return round(stability, 4)

    def _drift(self, versions: list) -> float:
        """
        Drift measured as change in belief count between first and last version,
        normalized by the first version's belief count.
        """
        if len(versions) < 2:
            return 0.0
        first_count = len(self._parse_list(versions[0].get("beliefs")))
        last_count = len(self._parse_list(versions[-1].get("beliefs")))
        if first_count == 0:
            return 0.0
        return round(abs(last_count - first_count) / first_count, 4)

    def _timeline(self, versions: list) -> list:
        return [
            {
                "version": v.get("version"),
                "created_at": v.get("created_at"),
                "belief_count": len(self._parse_list(v.get("beliefs"))),
                "open_loop_count": len(self._parse_list(v.get("open_loops"))),
            }
            for v in versions
        ]


def statistics_variance(data: list) -> float:
    """Simple variance calculation without importing statistics module."""
    n = len(data)
    if n < 2:
        return 0.0
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / n


identity_analytics = IdentityAnalytics()