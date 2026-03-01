from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class OpenLoopStore:
    def __init__(self):
        """
        Initialize the OpenLoopStore and configure the Supabase client attribute.
        
        Sets self.supabase to a Supabase client when SQL is not configured; otherwise sets it to None.
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
        Retrieve open-loop records for the specified user and identity.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        SELECT topic, status, importance, last_mentioned
                        FROM identity_open_loops
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
            self.supabase.table("identity_open_loops")
            .select("topic, status, importance, last_mentioned")
            .eq("user_id", user_id)
            .eq("identity_id", identity_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def replace(self, user_id: str, identity_id: str, loops: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Replace all open-loop records for the given user and identity with the provided list of loops.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                session.execute(
                    text(
                        """
                        DELETE FROM identity_open_loops
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                for loop in loops:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_open_loops (
                                identity_id, user_id, topic, status, importance, last_mentioned
                            ) VALUES (
                                :identity_id, :user_id, :topic, :status, :importance, :last_mentioned
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "topic": loop.get("topic", ""),
                            "status": loop.get("status", "open"),
                            "importance": loop.get("importance", 1),
                            "last_mentioned": loop.get("last_mentioned"),
                        },
                    )
                if sql_session is None:
                    session.commit()
            return

        if not self.supabase:
            return

        self.supabase.table("identity_open_loops").delete().eq("user_id", user_id).eq(
            "identity_id", identity_id
        ).execute()

        if not loops:
            return

        payload = []
        for loop in loops:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "topic": loop.get("topic", ""),
                    "status": loop.get("status", "open"),
                    "importance": loop.get("importance", 1),
                    "last_mentioned": loop.get("last_mentioned"),
                }
            )

        self.supabase.table("identity_open_loops").insert(payload).execute()
