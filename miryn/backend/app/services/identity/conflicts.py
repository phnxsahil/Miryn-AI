from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class ConflictStore:
    def __init__(self):
        """
        Initialize the ConflictStore instance and choose the storage client.
        
        Sets self.supabase to the Supabase client returned by get_db() when a SQL backend is not available (has_sql() is False); otherwise sets self.supabase to None.
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
        Retrieve conflict records for a specific user identity, ordered by creation time (newest first).
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        SELECT statement, conflict_with, severity, resolved, resolved_at
                        FROM identity_conflicts
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        ORDER BY created_at DESC
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                return [dict(row) for row in result.mappings().all()]

        if not self.supabase:
            return []

        response = (
            self.supabase.table("identity_conflicts")
            .select("statement, conflict_with, severity, resolved, resolved_at")
            .eq("user_id", user_id)
            .eq("identity_id", identity_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def insert(self, user_id: str, identity_id: str, conflicts: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Insert one or more identity conflict records into the configured storage backend.
        """
        if not conflicts:
            return

        if has_sql():
            with self._session_scope(sql_session) as session:
                for conflict in conflicts:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_conflicts (
                                identity_id, user_id, statement, conflict_with, severity, resolved, resolved_at
                            ) VALUES (
                                :identity_id, :user_id, :statement, :conflict_with, :severity, :resolved, :resolved_at
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "statement": conflict.get("statement", ""),
                            "conflict_with": conflict.get("conflict_with", ""),
                            "severity": conflict.get("severity", 0.5),
                            "resolved": conflict.get("resolved", False),
                            "resolved_at": conflict.get("resolved_at"),
                        },
                    )
                if sql_session is None:
                    session.commit()
            return

        if not self.supabase:
            return

        payload = []
        for conflict in conflicts:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "statement": conflict.get("statement", ""),
                    "conflict_with": conflict.get("conflict_with", ""),
                    "severity": conflict.get("severity", 0.5),
                    "resolved": conflict.get("resolved", False),
                    "resolved_at": conflict.get("resolved_at"),
                }
            )

        self.supabase.table("identity_conflicts").insert(payload).execute()

    def replace(self, user_id: str, identity_id: str, conflicts: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Replace all conflict records for a specific user identity with the provided list.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                session.execute(
                    text(
                        """
                        DELETE FROM identity_conflicts
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                for conflict in conflicts:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_conflicts (
                                identity_id, user_id, statement, conflict_with, severity, resolved, resolved_at
                            ) VALUES (
                                :identity_id, :user_id, :statement, :conflict_with, :severity, :resolved, :resolved_at
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "statement": conflict.get("statement", ""),
                            "conflict_with": conflict.get("conflict_with", ""),
                            "severity": conflict.get("severity", 0.5),
                            "resolved": conflict.get("resolved", False),
                            "resolved_at": conflict.get("resolved_at"),
                        },
                    )
                if sql_session is None:
                    session.commit()
            return

        if not self.supabase:
            return

        self.supabase.table("identity_conflicts").delete().eq(
            "user_id", user_id
        ).eq("identity_id", identity_id).execute()

        if not conflicts:
            return

        payload = []
        for conflict in conflicts:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "statement": conflict.get("statement", ""),
                    "conflict_with": conflict.get("conflict_with", ""),
                    "severity": conflict.get("severity", 0.5),
                    "resolved": conflict.get("resolved", False),
                    "resolved_at": conflict.get("resolved_at"),
                }
            )

        self.supabase.table("identity_conflicts").insert(payload).execute()
