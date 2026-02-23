from typing import Any, Dict, List
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class ConflictStore:
    def __init__(self):
        """
        Initialize the ConflictStore instance and choose the storage client.
        
        Sets self.supabase to the Supabase client returned by get_db() when a SQL backend is not available (has_sql() is False); otherwise sets self.supabase to None.
        """
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve conflict records for a specific user identity, ordered by creation time (newest first).
        
        Returns:
            A list of dictionaries with keys "statement", "conflict_with", "severity", "resolved", and "resolved_at". Returns an empty list if no records exist or if no storage backend is available.
        """
        if has_sql():
            with get_sql_session() as session:
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

    def insert(self, user_id: str, identity_id: str, conflicts: List[Dict[str, Any]]) -> None:
        """
        Insert one or more identity conflict records into the configured storage backend.
        
        This writes the provided conflict entries for the given user and identity to the active data store (SQL if available, otherwise Supabase). Each entry in `conflicts` is inserted as a separate row.
        
        Parameters:
            user_id (str): ID of the user who owns the identity.
            identity_id (str): ID of the identity the conflicts relate to.
            conflicts (List[Dict[str, Any]]): List of conflict records. Each record may contain:
                - "statement" (str): The conflicting statement. Defaults to "".
                - "conflict_with" (str): The value or statement this conflicts with. Defaults to "".
                - "severity" (float): Severity score for the conflict. Defaults to 0.5.
                - "resolved" (bool): Whether the conflict is resolved. Defaults to False.
                - "resolved_at" (optional): Timestamp when the conflict was resolved, if any.
        """
        if not conflicts:
            return

        if has_sql():
            with get_sql_session() as session:
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
