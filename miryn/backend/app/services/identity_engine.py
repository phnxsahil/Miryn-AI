from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db, has_sql, get_sql_session
from app.services.identity import (
    BeliefStore,
    OpenLoopStore,
    PatternStore,
    EmotionStore,
    ConflictStore,
)


class IdentityEngine:
    def __init__(self, reflection=None):
        """
        Initialize the IdentityEngine by configuring the backend client and creating component stores.
        """
        self.supabase = get_db() if not has_sql() else None
        self.beliefs = BeliefStore()
        self.open_loops = OpenLoopStore()
        self.patterns = PatternStore()
        self.emotions = EmotionStore()
        self.conflicts = ConflictStore()
        self.reflection = reflection

    def get_identity(self, user_id: str, sql_session: Optional[Any] = None) -> Dict:
        """
        Retrieve the latest hydrated identity for the given user, creating and returning an initial identity if none exists.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        SELECT * FROM identities
                        WHERE user_id = :user_id
                        ORDER BY version DESC
                        LIMIT 1
                        """
                    ),
                    {"user_id": user_id},
                ).mappings().first()

            if result:
                return self._hydrate_identity(dict(result), sql_session=sql_session)

            return self._create_initial_identity(user_id, sql_session=sql_session)

        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")

        response = (
            self.supabase.table("identities")
            .select("*")
            .eq("user_id", user_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return self._hydrate_identity(response.data[0])

        return self._create_initial_identity(user_id)

    def _create_initial_identity(self, user_id: str, sql_session: Optional[Any] = None) -> Dict:
        """
        Create and persist an initial identity for the given user and return the hydrated identity.
        """
        identity = {
            "user_id": user_id,
            "version": 1,
            "state": "onboarding",
            "traits": {},
            "values": {},
            "beliefs": [],
            "open_loops": [],
            "patterns": [],
            "emotions": [],
            "conflicts": [],
            "preset": None,
            "memory_weights": {},
        }
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        INSERT INTO identities (user_id, version, state, traits, values, beliefs, open_loops, preset, memory_weights)
                        VALUES (:user_id, :version, :state, :traits, :values, :beliefs, :open_loops, :preset, :memory_weights)
                        RETURNING *
                        """
                    ),
                    {
                        "user_id": user_id,
                        "version": 1,
                        "state": "onboarding",
                        "traits": json.dumps(identity["traits"]),
                        "values": json.dumps(identity["values"]),
                        "beliefs": json.dumps(identity["beliefs"]),
                        "open_loops": json.dumps(identity["open_loops"]),
                        "preset": identity["preset"],
                        "memory_weights": json.dumps(identity["memory_weights"]),
                    },
                ).mappings().first()
                return self._hydrate_identity(dict(result), sql_session=session)

        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")

        response = self.supabase.table("identities").insert(identity).execute()
        return self._hydrate_identity(response.data[0])

    def update_identity(self, user_id: str, updates: Dict, sql_session: Optional[Any] = None) -> Dict:
        """
        Merge provided identity updates into the user's current identity and persist the new version.
        """
        current = self.get_identity(user_id, sql_session=sql_session)
        merged = self._merge_identity(current, updates)

        if has_sql():
            return self._insert_identity_sql(user_id, merged, sql_session=sql_session)

        return self._insert_identity_supabase(user_id, merged, updates)

    def record_belief(self, user_id: str, topic: str, belief: str, confidence: float):
        current = self.get_identity(user_id)
        beliefs = current.get("beliefs", [])

        existing = next((b for b in beliefs if b.get("topic") == topic), None)

        now = datetime.utcnow().isoformat()
        if existing:
            existing["belief"] = belief
            existing["confidence"] = confidence
            existing["updated_at"] = now
        else:
            beliefs.append({
                "topic": topic,
                "belief": belief,
                "confidence": confidence,
                "created_at": now,
                "updated_at": now,
            })

        return self.update_identity(user_id, {"beliefs": beliefs})

    def track_open_loop(self, user_id: str, topic: str, importance: int):
        current = self.get_identity(user_id)
        open_loops = current.get("open_loops", [])

        existing = next((l for l in open_loops if l.get("topic") == topic), None)
        now = datetime.utcnow().isoformat()

        if existing:
            existing["importance"] = importance
            existing["last_mentioned"] = now
        else:
            open_loops.append({
                "topic": topic,
                "importance": importance,
                "last_mentioned": now,
            })

        return self.update_identity(user_id, {"open_loops": open_loops})

    async def detect_conflicts(self, user_id: str, new_statement: str) -> List[Dict]:
        """
        Detects potential conflicts between a user's stored identity and a new statement.
        """
        if not self.reflection:
            return []
        identity = self.get_identity(user_id)
        beliefs = identity.get("beliefs", [])
        return await self.reflection.detect_contradictions(beliefs, new_statement)

    def add_conflicts(self, user_id: str, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert the provided conflict entries for the specified user's current identity.
        """
        if not conflicts:
            return []
        identity = self.get_identity(user_id)
        identity_id = identity.get("id")
        if not identity_id:
            return []
        self.conflicts.insert(user_id, identity_id, conflicts)
        return conflicts

    def _merge_identity(self, current: Dict, updates: Dict) -> Dict:
        traits = {**self._ensure_dict(current.get("traits")), **self._ensure_dict(updates.get("traits"))}
        values = {**self._ensure_dict(current.get("values")), **self._ensure_dict(updates.get("values"))}
        beliefs = list(self._ensure_list(updates.get("beliefs", current.get("beliefs", []))))
        open_loops = list(self._ensure_list(updates.get("open_loops", current.get("open_loops", []))))
        patterns = list(self._ensure_list(updates.get("patterns", current.get("patterns", []))))
        emotions = list(self._ensure_list(updates.get("emotions", current.get("emotions", []))))
        conflicts = list(self._ensure_list(updates.get("conflicts", current.get("conflicts", []))))
        memory_weights = self._ensure_dict(updates.get("memory_weights", current.get("memory_weights", {})))

        return {
            "state": updates.get("state", current.get("state")),
            "traits": traits,
            "values": values,
            "beliefs": beliefs,
            "open_loops": open_loops,
            "patterns": patterns,
            "emotions": emotions,
            "conflicts": conflicts,
            "preset": updates.get("preset", current.get("preset")),
            "memory_weights": memory_weights,
            "base_version": current.get("version", 0),
        }

    def _insert_identity_sql(self, user_id: str, merged: Dict, sql_session: Optional[Any] = None) -> Dict:
        """
        Insert a new identity row for a user into the SQL identities table and update related stores.
        """
        payload = {
            "user_id": user_id,
            "state": merged["state"],
            "traits": json.dumps(merged["traits"]),
            "values": json.dumps(merged["values"]),
            "beliefs": json.dumps(merged["beliefs"]),
            "open_loops": json.dumps(merged["open_loops"]),
            "preset": merged.get("preset"),
            "memory_weights": json.dumps(merged.get("memory_weights", {})),
        }

        stmt = text(
            """
            WITH version_cte AS (
                SELECT COALESCE(MAX(version), 0) AS current_version
                FROM identities
                WHERE user_id = :user_id
            )
            INSERT INTO identities (user_id, version, state, traits, values, beliefs, open_loops, preset, memory_weights)
            SELECT
                :user_id,
                version_cte.current_version + 1,
                :state,
                :traits,
                :values,
                :beliefs,
                :open_loops,
                :preset,
                :memory_weights
            FROM version_cte
            RETURNING *
            """
        )

        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                result_row = None
                previous_identity = {}
                with self._session_scope(sql_session) as session:
                    previous = session.execute(
                        text(
                            """
                            SELECT * FROM identities
                            WHERE user_id = :user_id
                            ORDER BY version DESC
                            LIMIT 1
                            """
                        ),
                        {"user_id": user_id},
                    ).mappings().first()

                    # Use _deserialize_identity (no DB calls) to avoid opening
                    # nested sessions inside this session which exhausts the pool.
                    previous_identity = self._deserialize_identity(dict(previous)) if previous else {}

                    result_row = session.execute(stmt, payload).mappings().first()

                    if result_row:
                        self._log_identity_evolution_sql(
                            session,
                            user_id=user_id,
                            identity_id=str(result_row["id"]),
                            previous=previous_identity,
                            current=merged,
                            trigger_type="update_identity",
                        )

                # Sub-store writes happen AFTER the session commits to avoid
                # nested-session pool exhaustion on Neon.
                if result_row:
                    identity = dict(result_row)
                    identity_id = identity.get("id")
                    if identity_id:
                        self.beliefs.replace(user_id, identity_id, merged.get("beliefs", []), sql_session=sql_session)
                        self.open_loops.replace(user_id, identity_id, merged.get("open_loops", []), sql_session=sql_session)
                        self.patterns.replace(user_id, identity_id, merged.get("patterns", []), sql_session=sql_session)
                        self.emotions.replace(user_id, identity_id, merged.get("emotions", []), sql_session=sql_session)
                        self.conflicts.replace(user_id, identity_id, merged.get("conflicts", []), sql_session=sql_session)
                    return self._hydrate_identity(identity, sql_session=sql_session)
            except IntegrityError:
                if attempts >= 3:
                    raise
                continue

        raise RuntimeError("Failed to write identity after retries")

    def _log_identity_evolution_sql(
        self,
        session: Any,
        user_id: str,
        identity_id: str,
        previous: Dict,
        current: Dict,
        trigger_type: str,
    ) -> None:
        fields = [
            "state",
            "traits",
            "values",
            "beliefs",
            "open_loops",
            "patterns",
            "emotions",
            "conflicts",
            "preset",
            "memory_weights",
        ]

        for field in fields:
            old_value = previous.get(field)
            new_value = current.get(field)
            if old_value == new_value:
                continue
            session.execute(
                text(
                    """
                    INSERT INTO identity_evolution_log (
                        user_id, identity_id, field_changed, old_value, new_value, trigger_type
                    ) VALUES (
                        :user_id, :identity_id, :field_changed, :old_value, :new_value, :trigger_type
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "identity_id": identity_id,
                    "field_changed": field,
                    "old_value": json.dumps(old_value, default=str),
                    "new_value": json.dumps(new_value, default=str),
                    "trigger_type": trigger_type,
                },
            )

    def _log_identity_evolution_supabase(
        self,
        user_id: str,
        identity_id: str,
        previous: Dict,
        current: Dict,
        trigger_type: str,
    ) -> None:
        if not self.supabase:
            return

        fields = [
            "state",
            "traits",
            "values",
            "beliefs",
            "open_loops",
            "patterns",
            "emotions",
            "conflicts",
            "preset",
            "memory_weights",
        ]

        logs = []
        for field in fields:
            old_value = previous.get(field)
            new_value = current.get(field)
            if old_value == new_value:
                continue
            logs.append(
                {
                    "user_id": user_id,
                    "identity_id": identity_id,
                    "field_changed": field,
                    "old_value": json.dumps(old_value, default=str),
                    "new_value": json.dumps(new_value, default=str),
                    "trigger_type": trigger_type,
                }
            )

        if logs:
            self.supabase.table("identity_evolution_log").insert(logs).execute()

    def _insert_identity_supabase(self, user_id: str, merged: Dict, updates: Dict) -> Dict:
        """
        Insert a new identity version into Supabase, update related stores, and return the hydrated identity.
        """
        attempts = 0
        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")
        while attempts < 3:
            attempts += 1
            version = merged.get("base_version", 0) + 1
            
            # Get previous identity for evolution log
            previous_response = (
                self.supabase.table("identities")
                .select("*")
                .eq("user_id", user_id)
                .order("version", desc=True)
                .limit(1)
                .execute()
            )
            previous_identity = self._hydrate_identity(previous_response.data[0]) if previous_response.data else {}

            payload = {
                "user_id": user_id,
                "version": version,
                "state": merged["state"],
                "traits": merged["traits"],
                "values": merged["values"],
                "beliefs": merged["beliefs"],
                "open_loops": merged["open_loops"],
                "preset": merged.get("preset"),
                "memory_weights": merged.get("memory_weights", {}),
            }
            try:
                response = self.supabase.table("identities").insert(payload).execute()
                if not response.data:
                    raise RuntimeError("Supabase response missing identity data")
                identity = response.data[0]
                identity_id = identity.get("id")
                if identity_id:
                    self.beliefs.replace(user_id, identity_id, merged.get("beliefs", []))
                    self.open_loops.replace(user_id, identity_id, merged.get("open_loops", []))
                    self.patterns.replace(user_id, identity_id, merged.get("patterns", []))
                    self.emotions.replace(user_id, identity_id, merged.get("emotions", []))
                    self.conflicts.replace(user_id, identity_id, merged.get("conflicts", []))
                    
                    self._log_identity_evolution_supabase(
                        user_id=user_id,
                        identity_id=identity_id,
                        previous=previous_identity,
                        current=merged,
                        trigger_type="update_identity",
                    )
                return self._hydrate_identity(identity)
            except Exception as exc:
                message = str(exc).lower()
                if "duplicate" not in message or attempts >= 3:
                    raise
                # Refresh current state and retry with new merge
                current = self.get_identity(user_id)
                merged = self._merge_identity(current, updates)

        raise RuntimeError("Failed to insert identity after retries")

    def _ensure_dict(self, value: Any) -> Dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _ensure_list(self, value: Any) -> List:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def _deserialize_identity(self, identity: Dict) -> Dict:
        identity = dict(identity)
        if identity.get("id") is not None:
            identity["id"] = str(identity["id"])
        if identity.get("user_id") is not None:
            identity["user_id"] = str(identity["user_id"])
        identity["traits"] = self._ensure_dict(identity.get("traits"))
        identity["values"] = self._ensure_dict(identity.get("values"))
        identity["beliefs"] = self._ensure_list(identity.get("beliefs"))
        identity["open_loops"] = self._ensure_list(identity.get("open_loops"))
        identity["patterns"] = self._ensure_list(identity.get("patterns", []))
        identity["emotions"] = self._ensure_list(identity.get("emotions", []))
        identity["conflicts"] = self._ensure_list(identity.get("conflicts", []))
        identity["memory_weights"] = self._ensure_dict(identity.get("memory_weights", {}))
        return identity

    def _hydrate_identity(self, identity: Dict, sql_session: Optional[Any] = None) -> Dict:
        identity = self._deserialize_identity(identity)
        identity_id = identity.get("id")
        if not identity_id:
            return identity
        identity["beliefs"] = self.beliefs.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["open_loops"] = self.open_loops.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["patterns"] = self.patterns.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["emotions"] = self.emotions.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["conflicts"] = self.conflicts.load(identity["user_id"], identity_id, sql_session=sql_session)
        return identity

    @contextmanager
    def _session_scope(self, session: Optional[Any]):
        if session is not None:
            yield session
        else:
            with get_sql_session() as new_session:
                yield new_session
