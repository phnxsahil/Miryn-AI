from typing import Any, Dict, List
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class BeliefStore:
    def __init__(self):
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        if has_sql():
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT topic, belief, confidence, evidence
                        FROM identity_beliefs
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
            self.supabase.table("identity_beliefs")
            .select("topic, belief, confidence, evidence")
            .eq("user_id", user_id)
            .eq("identity_id", identity_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def replace(self, user_id: str, identity_id: str, beliefs: List[Dict[str, Any]]) -> None:
        if has_sql():
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        DELETE FROM identity_beliefs
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                for belief in beliefs:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_beliefs (
                                identity_id, user_id, topic, belief, confidence, evidence
                            ) VALUES (
                                :identity_id, :user_id, :topic, :belief, :confidence, :evidence
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "topic": belief.get("topic", ""),
                            "belief": belief.get("belief", ""),
                            "confidence": belief.get("confidence", 0.5),
                            "evidence": json.dumps(belief.get("evidence", {})),
                        },
                    )
                session.commit()
            return

        if not self.supabase:
            return

        self.supabase.table("identity_beliefs").delete().eq("user_id", user_id).eq(
            "identity_id", identity_id
        ).execute()

        if not beliefs:
            return

        payload = []
        for belief in beliefs:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "topic": belief.get("topic", ""),
                    "belief": belief.get("belief", ""),
                    "confidence": belief.get("confidence", 0.5),
                    "evidence": belief.get("evidence", {}),
                }
            )

        self.supabase.table("identity_beliefs").insert(payload).execute()
