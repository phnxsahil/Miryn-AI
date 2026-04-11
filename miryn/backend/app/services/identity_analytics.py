"""
Identity Analytics Service - Divyadeep Kaur
Computes identity stability score and drift over time
using cosine similarity between identity versions.
"""
import json
import logging
import math
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import text
from app.core.database import has_sql, get_sql_session, get_db

logger = logging.getLogger(__name__)


class IdentityAnalytics:
    """
    Analyzes identity versions to compute stability and drift metrics.
    Uses cosine similarity between serialized identity vectors.
    """

    def _fetch_identity_versions(self, user_id: str) -> List[Dict]:
        """
        Fetch all identity versions for a user ordered by version number.
        Returns list of identity dicts.
        """
        try:
            if has_sql():
                with get_sql_session() as session:
                    result = session.execute(
                        text("""
                            SELECT version, traits, values, beliefs,
                                   open_loops, created_at
                            FROM identities
                            WHERE user_id = :user_id
                            ORDER BY version ASC
                        """),
                        {"user_id": user_id},
                    )
                    return [dict(row) for row in result.mappings().all()]
            else:
                db = get_db()
                response = (
                    db.table("identities")
                    .select("version, traits, values, beliefs, open_loops, created_at")
                    .eq("user_id", user_id)
                    .order("version")
                    .execute()
                )
                return response.data or []
        except Exception as e:
            logger.warning("Failed to fetch identity versions for user %s: %s", user_id, e)
            return []

    def _identity_to_vector(self, identity: Dict) -> Dict[str, float]:
        """
        Convert an identity record into a flat feature vector.
        Each key in traits/values becomes a dimension.
        Beliefs and open_loops contribute as counts.
        """
        vector: Dict[str, float] = {}

        def parse_json(val):
            if isinstance(val, dict):
                return val
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return {}
            return {}

        traits = parse_json(identity.get("traits") or {})
        if isinstance(traits, dict):
            for k, v in traits.items():
                try:
                    vector[f"trait_{k}"] = float(v) if isinstance(v, (int, float)) else 1.0
                except Exception:
                    vector[f"trait_{k}"] = 1.0

        values = parse_json(identity.get("values") or {})
        if isinstance(values, dict):
            for k, v in values.items():
                try:
                    vector[f"value_{k}"] = float(v) if isinstance(v, (int, float)) else 1.0
                except Exception:
                    vector[f"value_{k}"] = 1.0

        beliefs = parse_json(identity.get("beliefs") or [])
        vector["belief_count"] = float(len(beliefs) if isinstance(beliefs, list) else 0)

        open_loops = parse_json(identity.get("open_loops") or [])
        vector["open_loop_count"] = float(len(open_loops) if isinstance(open_loops, list) else 0)

        return vector

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """
        Compute cosine similarity between two feature vectors.
        Returns value between 0 and 1. 1 = identical, 0 = completely different.
        """
        all_keys = set(vec_a.keys()) | set(vec_b.keys())
        if not all_keys:
            return 1.0

        dot_product = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if mag_a == 0 or mag_b == 0:
            return 1.0 if mag_a == mag_b else 0.0

        return round(dot_product / (mag_a * mag_b), 3)

    def compute_stability_score(self, versions: List[Dict]) -> float:
        """
        Compute identity stability score (0-1).
        1 = perfectly stable (no change), 0 = completely changed.
        Based on average cosine similarity between consecutive versions.
        """
        if len(versions) < 2:
            return 1.0

        similarities = []
        for i in range(len(versions) - 1):
            vec_a = self._identity_to_vector(versions[i])
            vec_b = self._identity_to_vector(versions[i + 1])
            sim = self._cosine_similarity(vec_a, vec_b)
            similarities.append(sim)

        return round(sum(similarities) / len(similarities), 3)

    def compute_drift(self, versions: List[Dict]) -> float:
        """
        Compute identity drift — how much the identity has changed
        from the first version to the latest version.
        0 = no drift, 1 = completely different from start.
        """
        if len(versions) < 2:
            return 0.0

        vec_first = self._identity_to_vector(versions[0])
        vec_last = self._identity_to_vector(versions[-1])
        similarity = self._cosine_similarity(vec_first, vec_last)
        return round(1.0 - similarity, 3)

    def get_version_timeline(self, versions: List[Dict]) -> List[Dict]:
        """
        Build a timeline of identity changes with similarity between each version.
        """
        timeline = []
        for i, v in enumerate(versions):
            entry = {
                "version": v["version"],
                "created_at": str(v["created_at"]),
                "belief_count": len(v.get("beliefs") or []),
                "open_loop_count": len(v.get("open_loops") or []),
            }
            if i > 0:
                vec_prev = self._identity_to_vector(versions[i - 1])
                vec_curr = self._identity_to_vector(v)
                entry["similarity_to_previous"] = self._cosine_similarity(vec_prev, vec_curr)
            timeline.append(entry)
        return timeline

    def analyze(self, user_id: str) -> Dict[str, Any]:
        """
        Run full identity analytics for a user.

        Returns:
            Dict with stability_score, drift, total_versions,
            and version_timeline.
        """
        versions = self._fetch_identity_versions(user_id)

        if not versions:
            return {
                "stability_score": 1.0,
                "drift": 0.0,
                "total_versions": 0,
                "version_timeline": [],
                "message": "No identity data yet.",
            }

        return {
            "stability_score": self.compute_stability_score(versions),
            "drift": self.compute_drift(versions),
            "total_versions": len(versions),
            "version_timeline": self.get_version_timeline(versions),
        }


# Singleton instance
identity_analytics = IdentityAnalytics()