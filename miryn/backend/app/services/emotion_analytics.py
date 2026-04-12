"""
Emotion Analytics Service - Divyadeep Kaur
Tracks and analyzes user emotions over time.
Computes volatility, trends, mood score and entropy.
"""
import json
import logging
import math
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import has_sql, get_sql_session, get_db
from app.core.encryption import decrypt_text

logger = logging.getLogger(__name__)

EMOTION_VALENCE = {
    "joy": 1.0,
    "surprise": 0.2,
    "neutral": 0.0,
    "disgust": -0.5,
    "fear": -0.6,
    "sadness": -0.7,
    "anger": -0.8,
}


class EmotionAnalytics:
    """
    Analyzes emotional patterns from stored message metadata.
    Provides volatility, trend, mood score and entropy metrics.
    """

    def _fetch_emotions(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Fetch and decrypt emotion records from messages for a user within the last N days.
        Returns list of emotion dicts sorted by time.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        records = []

        try:
            if has_sql():
                with get_sql_session() as session:
                    result = session.execute(
                        text("""
                            SELECT metadata_encrypted, metadata, created_at
                            FROM messages
                            WHERE user_id = :user_id
                              AND role = 'user'
                              AND created_at >= :cutoff
                            ORDER BY created_at ASC
                        """),
                        {"user_id": user_id, "cutoff": cutoff},
                    )
                    rows = result.mappings().all()
            else:
                db = get_db()
                response = (
                    db.table("messages")
                    .select("metadata_encrypted, metadata, created_at")
                    .eq("user_id", user_id)
                    .eq("role", "user")
                    .gte("created_at", cutoff.isoformat())
                    .execute()
                )
                rows = response.data or []

            for row in rows:
                r = dict(row)
                meta = {}
                encrypted = r.get("metadata_encrypted")
                if encrypted:
                    try:
                        decrypted = decrypt_text(encrypted)
                        if decrypted:
                            meta = json.loads(decrypted)
                    except Exception:
                        pass
                if not meta:
                    meta = r.get("metadata") or {}

                emotions = meta.get("emotions", {})
                if emotions and emotions.get("primary_emotion"):
                    try:
                        intensity = float(emotions.get("intensity", 0.5))
                        intensity = max(0.0, min(1.0, intensity))
                    except (TypeError, ValueError):
                        intensity = 0.5
                    records.append({
                        "emotion": emotions["primary_emotion"],
                        "intensity": intensity,
                        "secondary": emotions.get("secondary_emotions", []),
                        "timestamp": r["created_at"],
                    })

        except Exception as e:
            logger.warning("Failed to fetch emotions for user %s: %s", user_id, e)

        return records

    def compute_mood_score(self, records: List[Dict]) -> float:
        """
        Compute average mood score (-1 to 1) from emotion records.
        Positive = happy, Negative = stressed/sad.
        """
        if not records:
            return 0.0
        scores = []
        for r in records:
            valence = EMOTION_VALENCE.get(r["emotion"], 0.0)
            weighted = valence * r["intensity"]
            scores.append(weighted)
        return round(sum(scores) / len(scores), 3)

    def compute_volatility(self, records: List[Dict]) -> float:
        """
        Compute emotional volatility as standard deviation of mood scores.
        High volatility = mood swings. Low = stable.
        """
        if len(records) < 2:
            return 0.0
        scores = [EMOTION_VALENCE.get(r["emotion"], 0.0) * r["intensity"] for r in records]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return round(math.sqrt(variance), 3)

    def compute_trend(self, records: List[Dict], window: int = 5) -> str:
        """
        Compute emotional trend using moving average.
        Returns: 'improving', 'declining', or 'stable'.
        """
        if len(records) < 2:
            return "stable"
        scores = [EMOTION_VALENCE.get(r["emotion"], 0.0) * r["intensity"] for r in records]
        if len(scores) <= window:
            first_half = scores[:len(scores) // 2]
            second_half = scores[len(scores) // 2:]
        else:
            first_half = scores[:window]
            second_half = scores[-window:]
        if not first_half or not second_half:
            return "stable"
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        diff = avg_second - avg_first
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"

    def compute_entropy(self, records: List[Dict]) -> float:
        """
        Compute emotional entropy — how varied the emotions are.
        High entropy = diverse emotions. Low = repetitive.
        """
        if not records:
            return 0.0
        counts: Dict[str, int] = {}
        for r in records:
            counts[r["emotion"]] = counts.get(r["emotion"], 0) + 1
        total = len(records)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 3)

    def get_dominant_emotions(self, records: List[Dict]) -> List[Dict]:
        """
        Get top 3 most frequent emotions with their percentages.
        """
        if not records:
            return []
        counts: Dict[str, int] = {}
        for r in records:
            counts[r["emotion"]] = counts.get(r["emotion"], 0) + 1
        total = len(records)
        sorted_emotions = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"emotion": e, "count": c, "percentage": round(c / total * 100, 1)}
            for e, c in sorted_emotions[:3]
        ]

    def analyze(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Run full emotion analytics for a user over the last N days.

        Returns:
            Dict with mood_score, volatility, trend, entropy,
            dominant_emotions, total_messages, and period_days.
        """
        records = self._fetch_emotions(user_id, days=days)

        if not records:
            return {
                "mood_score": 0.0,
                "volatility": 0.0,
                "trend": "stable",
                "entropy": 0.0,
                "dominant_emotions": [],
                "total_messages": 0,
                "period_days": days,
                "message": "Not enough data yet. Keep chatting!",
            }

        return {
            "mood_score": self.compute_mood_score(records),
            "volatility": self.compute_volatility(records),
            "trend": self.compute_trend(records),
            "entropy": self.compute_entropy(records),
            "dominant_emotions": self.get_dominant_emotions(records),
            "total_messages": len(records),
            "period_days": days,
        }


# Singleton instance
emotion_analytics = EmotionAnalytics()