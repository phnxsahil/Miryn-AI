from typing import Any, Dict, List
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class OpenLoopStore:
    def __init__(self):
        """
        Initialize the OpenLoopStore and configure the Supabase client attribute.
        
        Sets self.supabase to a Supabase client when SQL is not configured; otherwise sets it to None.
        """
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve open-loop records for the specified user and identity.
        
        Results are ordered by creation time (oldest first). Each record dictionary contains the keys
        `topic`, `status`, `importance`, and `last_mentioned`. If no records are found or no backend
        is available, an empty list is returned.
        
        Returns:
            List[Dict[str, Any]]: List of open-loop record dictionaries.
        """
        if has_sql():
            with get_sql_session() as session:
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

    def replace(self, user_id: str, identity_id: str, loops: List[Dict[str, Any]]) -> None:
        """
        Replace all open-loop records for the given user and identity with the provided list of loops.
        
        Deletes existing records for the (user_id, identity_id) pair and inserts the supplied loops into the persistence backend (SQL or Supabase). If the configured backend is unavailable, the method is a no-op. Each loop may include keys `topic`, `status`, `importance`, and `last_mentioned`; missing keys are filled with defaults (`topic` -> "", `status` -> "open", `importance` -> 1).
        
        Parameters:
            user_id (str): Identifier of the user owning the loops.
            identity_id (str): Identifier of the identity associated with the loops.
            loops (List[Dict[str, Any]]): List of loop objects to store. Each object should be a mapping that may contain `topic`, `status`, `importance`, and `last_mentioned`.
        """
        if has_sql():
            with get_sql_session() as session:
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
