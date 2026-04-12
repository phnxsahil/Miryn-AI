"""
Identity Analytics Service - Divyadeep Kaur
"""
import json
import logging
import math

from app.db.database import get_db_connection

logger = logging.getLogger(__name__)


class IdentityAnalytics:

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
            with get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT version, beliefs, open_loops, embedding, created_at
                    FROM identity_versions
                    WHERE user_id = ?
                    ORDER BY created_at ASC
                    """,
                    (user_id,),
                ).fetchall()
            return [dict(r) for r in rows]
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
        if len(versions) < 2:
            return 1.0
        similarities = []
        for i in range(1, len(versions)):
            e1 = self._parse_embedding(versions[i - 1].get("embedding"))
            e2 = self._parse_embedding(versions[i].get("embedding"))
            if e1 and e2:
                similarities.append(self._cosine_similarity(e1, e2))
        if not similarities:
            return 1.0
        return round(sum(similarities) / len(similarities), 4)

    def _drift(self, versions: list) -> float:
        if len(versions) < 2:
            return 0.0
        e_first = self._parse_embedding(versions[0].get("embedding"))
        e_last = self._parse_embedding(versions[-1].get("embedding"))
        if not e_first or not e_last:
            return 0.0
        return round(1.0 - self._cosine_similarity(e_first, e_last), 4)

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

    def _parse_embedding(self, val) -> list:
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return []

    def _cosine_similarity(self, a: list, b: list) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x ** 2 for x in a))
        mag_b = math.sqrt(sum(x ** 2 for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


identity_analytics = IdentityAnalytics()