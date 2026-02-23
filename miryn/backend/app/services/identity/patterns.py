from typing import Any, Dict, List
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class PatternStore:
    def __init__(self):
        """
        Initialize a PatternStore instance and configure its storage client.
        
        Sets the instance attribute `supabase` to a Supabase client when SQL storage is not available; otherwise sets `supabase` to `None` to indicate SQL will be used.
        """
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve identity patterns for a given user and identity, ordered by creation time.
        
        Returns:
            A list of dictionaries, each containing the keys 'pattern_type', 'description', 'signals', and 'confidence'. The list is empty if no matching patterns are found.
        """
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
                rows = [dict(row) for row in result.mappings().all()]
                for row in rows:
                    if isinstance(row.get("signals"), str):
                        try:
                            row["signals"] = json.loads(row["signals"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                return rows

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
        """
        Replace all identity patterns for a given user and identity with the supplied list.
        
        Parameters:
            user_id (str): ID of the user owning the identity.
            identity_id (str): ID of the identity whose patterns will be replaced.
            patterns (List[Dict[str, Any]]): List of pattern objects to store. Each pattern may contain:
                - "pattern_type" (str): type of the pattern (defaults to "").
                - "description" (str): human-readable description (defaults to "").
                - "signals" (dict): pattern signals (defaults to {}). When using the SQL backend, signals are serialized to a JSON string before storage.
                - "confidence" (float): confidence score (defaults to 0.5).
        
        Notes:
            - If a SQL backend is available, existing rows for the (user_id, identity_id) pair are deleted and the provided patterns are inserted within a transaction.
            - If a Supabase backend is used, existing records for the pair are deleted and the provided patterns are inserted as a batch.
            - If `patterns` is empty or no backend client is available, the method returns without inserting anything.
        """
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
