from typing import Any, Dict, List
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class PatternStore:
    def __init__(self):
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        if has_sql():
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT pattern_type, description, signals, confidence
                        FROM identity_patterns
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        ORDER BY created_at ASC
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                return [dict(row) for row in result.mappings().all()]

        if not self.supabase:
            return []

        response = (
            self.supabase.table("identity_patterns")
            .select("pattern_type, description, signals, confidence")
            .eq("user_id", user_id)
            .eq("identity_id", identity_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def replace(self, user_id: str, identity_id: str, patterns: List[Dict[str, Any]]) -> None:
        if has_sql():
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        DELETE FROM identity_patterns
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                for pattern in patterns:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_patterns (
                                identity_id, user_id, pattern_type, description, signals, confidence
                            ) VALUES (
                                :identity_id, :user_id, :pattern_type, :description, :signals, :confidence
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "pattern_type": pattern.get("pattern_type", ""),
                            "description": pattern.get("description", ""),
                            "signals": json.dumps(pattern.get("signals", {})),
                            "confidence": pattern.get("confidence", 0.5),
                        },
                    )
                session.commit()
            return

        if not self.supabase:
            return

        self.supabase.table("identity_patterns").delete().eq("user_id", user_id).eq(
            "identity_id", identity_id
        ).execute()

        if not patterns:
            return

        payload = []
        for pattern in patterns:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "pattern_type": pattern.get("pattern_type", ""),
                    "description": pattern.get("description", ""),
                    "signals": pattern.get("signals", {}),
                    "confidence": pattern.get("confidence", 0.5),
                }
            )

        self.supabase.table("identity_patterns").insert(payload).execute()
