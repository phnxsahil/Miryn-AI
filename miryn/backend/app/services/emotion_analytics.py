"""
Emotion Analytics Service - Divyadeep Kaur
Analyzes stored emotion metadata to compute mood scores, trends, and volatility.
"""
import json
import logging
import statistics
import math
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import text

from app.core.database import get_db, has_sql, get_sql_session
from app.core.encryption import decrypt_text

logger = logging.getLogger(__name__)


class EmotionAnalytics:

    def __init__(self):
        self.supabase = get_db() if not has_sql() else None

    def analyze(self, user_id: str, days: int = 30) -> dict:
        records = self._fetch_records(user_id, days)
        if not records:
            return {
                "message": "No emotion data yet.",
                "mood_score": None,
                "volatility": None,
                "trend": None,
                "entropy": None,
                "dominant_emotions": [],
            }
        return {
            "mood_score": self._mood_score(records),
            "volatility": self._volatility(records),
            "trend": self._trend(records),
            "entropy": self._entropy(records),
            "dominant_emotions": self._dominant_emotions(records),
        }

    def _fetch_records(self, user_id: str, days: int) -> list:
        records = []
        cutoff = datetime.utcnow() - timedelta(days=days)

        try:
            if has_sql():
                with get_sql_session() as session:
                    result = session.execute(
                        text(
                            """
                            SELECT metadata_encrypted, metadata, created_at
                            FROM messages
                            WHERE user_id = :user_id AND created_at >= :cutoff
                            ORDER BY created_at ASC
                            """
                        ),
                        {"user_id": user_id, "cutoff": cutoff},
                    )
                    rows = [dict(r) for r in result.mappings().all()]
            else:
                response = (
                    self.supabase.table("messages")
                    .select("metadata_encrypted, metadata, created_at")
                    .eq("user_id", user_id)
                    .gte("created_at", cutoff.isoformat())
                    .order("created_at")
                    .execute()
                )
                rows = response.data or []
        except Exception as e:
            logger.error("Failed to fetch emotions for user %s: %s", user_id, e)
            raise  # propagate so FastAPI returns a real 500

        for row in rows:
            # per-row isolation — one bad record never kills the batch
            try:
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
                    raw = r.get("metadata") or {}
                    if isinstance(raw, str):
                        try:
                            meta = json.loads(raw)
                        except Exception:
                            meta = {}
                    else:
                        meta = raw

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
                logger.warning("Skipping malformed row for user %s: %s", user_id, e)
                continue

        return records

    def _mood_score(self, records: list) -> float:
        positive = {"joy", "happy", "excited", "content", "love", "optimistic"}
        negative = {"sad", "angry", "fear", "disgust", "anxious", "depressed"}
        score = 0.5
        for r in records:
            em = r["emotion"].lower()
            if em in positive:
                score += r["intensity"] * 0.1
            elif em in negative:
                score -= r["intensity"] * 0.1
        return round(max(0.0, min(1.0, score)), 4)

    def _volatility(self, records: list) -> float:
        if len(records) < 2:
            return 0.0
        intensities = [r["intensity"] for r in records]
        return round(statistics.stdev(intensities), 4)

    def _trend(self, records: list) -> str:
        if len(records) < 4:
            return "neutral"
        mid = len(records) // 2
        first_half = statistics.mean(r["intensity"] for r in records[:mid])
        second_half = statistics.mean(r["intensity"] for r in records[mid:])
        diff = second_half - first_half
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"

    def _entropy(self, records: list) -> float:
        counts = Counter(r["emotion"] for r in records)
        total = len(records)
        return round(
            -sum((c / total) * math.log2(c / total) for c in counts.values()),
            4,
        )

    def _dominant_emotions(self, records: list, top_n: int = 3) -> list:
        counts = Counter(r["emotion"] for r in records)
        return [{"emotion": e, "count": c} for e, c in counts.most_common(top_n)]


emotion_analytics = EmotionAnalytics()