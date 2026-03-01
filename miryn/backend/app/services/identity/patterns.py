from typing import Any, Dict, List, Optional
import json
from contextlib import contextmanager
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class PatternStore:
    def __init__(self):
        """
        Initialize a PatternStore instance and configure its storage client.
        
        Sets the instance attribute `supabase` to a Supabase client when SQL storage is not available; otherwise sets `supabase` to `None` to indicate SQL will be used.
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
        Retrieve identity patterns for a given user and identity, ordered by creation time.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
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

    def replace(self, user_id: str, identity_id: str, patterns: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Replace all identity patterns for a given user and identity with the supplied list.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
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
                if sql_session is None:
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
