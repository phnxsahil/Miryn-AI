from typing import Any, Dict, List, Optional
import json
from contextlib import contextmanager
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class BeliefStore:
    def __init__(self):
        """
        Initialize the instance and select the storage backend.
        
        Sets self.supabase to a Supabase client when a SQL backend is not available; otherwise sets self.supabase to None to indicate SQL will be used.
        """
        self.supabase = get_db() if not has_sql() else None

    @contextmanager
    def _session_scope(self, session: Optional[Any]):
        if session is not None:
            yield session
        else:
            with get_sql_session() as new_session:
                yield new_session

    def load(self, user_id: str, identity_id: str, sql_session: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Load stored beliefs for the specified user and identity from the configured backend.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
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
                rows = [dict(row) for row in result.mappings().all()]
                for row in rows:
                    if isinstance(row.get("evidence"), str):
                        try:
                            row["evidence"] = json.loads(row["evidence"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                return rows

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

    def replace(self, user_id: str, identity_id: str, beliefs: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Replace stored beliefs for a specific user identity with the provided list.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
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
                # Only commit if we created the session ourselves
                if sql_session is None:
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
