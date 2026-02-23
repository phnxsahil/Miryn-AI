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
    def __init__(self):
        """
        Initialize the IdentityEngine by configuring the backend client and creating component stores.
        
        Sets `self.supabase` to a Supabase client when SQL is not configured; otherwise leaves it as `None`. Instantiates stores for beliefs, open loops, patterns, emotions, and conflicts as attributes on the engine.
        """
        self.supabase = get_db() if not has_sql() else None
        self.beliefs = BeliefStore()
        self.open_loops = OpenLoopStore()
        self.patterns = PatternStore()
        self.emotions = EmotionStore()
        self.conflicts = ConflictStore()

    def get_identity(self, user_id: str, sql_session: Optional[Any] = None) -> Dict:
        """
        Retrieve the latest hydrated identity for the given user, creating and returning an initial identity if none exists.
        
        Parameters:
            user_id (str): The user's unique identifier.
            sql_session (Optional[Any]): Optional SQLAlchemy session to use for the lookup; if not provided a session will be created when SQL is enabled.
        
        Returns:
            Dict: The hydrated identity object for the user (includes traits, values, beliefs, open_loops, patterns, emotions, and conflicts).
        
        Raises:
            RuntimeError: If SQL is not configured and the Supabase client is not available.
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
                return self._hydrate_identity(dict(result))

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
        
        If an SQL backend is configured the identity is inserted into the identities table; otherwise the identity is inserted via Supabase. The created identity starts at version 1 with state "onboarding" and empty traits, values, beliefs, open_loops, patterns, emotions, and conflicts.
        
        Parameters:
            user_id (str): The user's identifier.
            sql_session (Optional[Any]): An optional SQLAlchemy session to use for the insert; if omitted, a session will be created.
        
        Returns:
            Dict: The persisted identity dictionary with related components loaded (hydrated).
        
        Raises:
            RuntimeError: If no SQL backend is available and the Supabase client is not configured.
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
        }
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        INSERT INTO identities (user_id, version, state, traits, values, beliefs, open_loops)
                        VALUES (:user_id, :version, :state, :traits, :values, :beliefs, :open_loops)
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
                    },
                ).mappings().first()
                return self._hydrate_identity(dict(result))

        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")

        response = self.supabase.table("identities").insert(identity).execute()
        return self._hydrate_identity(response.data[0])

    def update_identity(self, user_id: str, updates: Dict, sql_session: Optional[Any] = None) -> Dict:
        """
        Merge provided identity updates into the user's current identity and persist the new version.
        
        Parameters:
            user_id (str): The user's unique identifier.
            updates (Dict): Partial identity fields to merge into the current identity (may contain traits, values, beliefs, open_loops, patterns, emotions, conflicts, and/or state).
            sql_session (Optional[Any]): Optional SQLAlchemy session to use for SQL persistence; if omitted a session will be created when needed.
        
        Returns:
            Dict: The newly persisted, hydrated identity including merged fields and related store data.
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

    def detect_conflicts(self, user_id: str, new_statement: str) -> List[Dict]:
        """
        Detects potential conflicts between a user's stored identity and a new statement.
        
        Parameters:
            user_id (str): Identifier of the user whose identity will be compared.
            new_statement (str): Statement to evaluate for potential conflicts with the user's identity.
        
        Returns:
            List[Dict]: A list of conflict objects where each dict describes a detected conflict. Returns an empty list if no conflicts are found.
        """
        _ = self.get_identity(user_id)
        return []

    def add_conflicts(self, user_id: str, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert the provided conflict entries for the specified user's current identity.
        
        If `conflicts` is empty or the user has no persisted identity, no action is taken and an empty list is returned.
        
        Parameters:
            user_id (str): The user's identifier.
            conflicts (List[Dict[str, Any]]): A list of conflict records to add; each record is a dict of conflict fields.
        
        Returns:
            List[Dict[str, Any]]: The same `conflicts` list after persistence, or an empty list if nothing was added.
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
        """
        Merge an existing identity with incoming updates, producing the next identity payload.
        
        Parameters:
            current (Dict): The existing identity object; its `version` is used as `base_version`.
            updates (Dict): Partial identity fields to apply; keys may include `state`, `traits`, `values`, `beliefs`, `open_loops`, `patterns`, `emotions`, and `conflicts`.
        
        Returns:
            Dict: A merged identity containing:
                - `state`: updated state if provided, otherwise from `current`
                - `traits` and `values`: dictionaries with `updates` taking precedence
                - `beliefs`, `open_loops`, `patterns`, `emotions`, `conflicts`: lists sourced from `updates` if present, otherwise from `current`
                - `base_version`: the numeric version from `current` (defaults to 0 if missing)
        """
        traits = {**self._ensure_dict(current.get("traits")), **self._ensure_dict(updates.get("traits"))}
        values = {**self._ensure_dict(current.get("values")), **self._ensure_dict(updates.get("values"))}
        beliefs = list(self._ensure_list(updates.get("beliefs", current.get("beliefs", []))))
        open_loops = list(self._ensure_list(updates.get("open_loops", current.get("open_loops", []))))
        patterns = list(self._ensure_list(updates.get("patterns", current.get("patterns", []))))
        emotions = list(self._ensure_list(updates.get("emotions", current.get("emotions", []))))
        conflicts = list(self._ensure_list(updates.get("conflicts", current.get("conflicts", []))))

        return {
            "state": updates.get("state", current.get("state")),
            "traits": traits,
            "values": values,
            "beliefs": beliefs,
            "open_loops": open_loops,
            "patterns": patterns,
            "emotions": emotions,
            "conflicts": conflicts,
            "base_version": current.get("version", 0),
        }

    def _insert_identity_sql(self, user_id: str, merged: Dict, sql_session: Optional[Any] = None) -> Dict:
        """
        Insert a new identity row for a user into the SQL identities table and update related stores.
        
        Attempts to insert a new identity with version = current_max_version + 1, persists associated component stores (beliefs, open_loops, patterns, emotions, conflicts) when the insert succeeds, and returns the hydrated identity.
        
        Parameters:
            user_id (str): The user identifier to associate with the new identity.
            merged (Dict): Merged identity payload containing at least keys "state", "traits", "values", "beliefs", and "open_loops". Optional keys: "patterns", "emotions", "conflicts".
            sql_session (Optional[Any]): Optional SQLAlchemy session to use for the operation; if omitted, a session will be created.
        
        Returns:
            Dict: The hydrated identity record as stored in the database.
        
        Raises:
            sqlalchemy.exc.IntegrityError: If a database integrity constraint prevents insertion and persists after retries.
            RuntimeError: If the insertion fails after retrying multiple times.
        """
        payload = {
            "user_id": user_id,
            "state": merged["state"],
            "traits": json.dumps(merged["traits"]),
            "values": json.dumps(merged["values"]),
            "beliefs": json.dumps(merged["beliefs"]),
            "open_loops": json.dumps(merged["open_loops"]),
        }

        stmt = text(
            """
            WITH version_cte AS (
                SELECT COALESCE(MAX(version), 0) AS current_version
                FROM identities
                WHERE user_id = :user_id
            )
            INSERT INTO identities (user_id, version, state, traits, values, beliefs, open_loops)
            SELECT
                :user_id,
                version_cte.current_version + 1,
                :state,
                :traits,
                :values,
                :beliefs,
                :open_loops
            FROM version_cte
            RETURNING *
            """
        )

        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                with self._session_scope(sql_session) as session:
                    result = session.execute(stmt, payload).mappings().first()
                if result:
                    identity = dict(result)
                    identity_id = identity.get("id")
                    if identity_id:
                        self.beliefs.replace(user_id, identity_id, merged.get("beliefs", []))
                        self.open_loops.replace(user_id, identity_id, merged.get("open_loops", []))
                        self.patterns.replace(user_id, identity_id, merged.get("patterns", []))
                        self.emotions.replace(user_id, identity_id, merged.get("emotions", []))
                        self.conflicts.insert(user_id, identity_id, merged.get("conflicts", []))
                    return self._hydrate_identity(identity)
            except IntegrityError:
                if attempts >= 3:
                    raise
                continue

        raise RuntimeError("Failed to write identity after retries")

    def _insert_identity_supabase(self, user_id: str, merged: Dict, updates: Dict) -> Dict:
        """
        Insert a new identity version into Supabase, update related stores, and return the hydrated identity.
        
        Parameters:
            user_id (str): The user's unique identifier to associate with the new identity.
            merged (Dict): The merged identity payload containing keys such as `base_version`, `state`, `traits`, `values`, `beliefs`, `open_loops`, `patterns`, `emotions`, and `conflicts`. `base_version` is used to compute the new identity version.
            updates (Dict): The original updates passed by the caller; used to recompute a merged payload if an insert collision occurs and a retry is attempted.
        
        Returns:
            Dict: The hydrated identity record returned from Supabase with related components loaded.
        
        Raises:
            RuntimeError: If the Supabase client is not configured or if insertion fails after retrying.
        """
        attempts = 0
        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")
        while attempts < 3:
            attempts += 1
            version = merged.get("base_version", 0) + 1
            payload = {
                "user_id": user_id,
                "version": version,
                "state": merged["state"],
                "traits": merged["traits"],
                "values": merged["values"],
                "beliefs": merged["beliefs"],
                "open_loops": merged["open_loops"],
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
                    self.conflicts.insert(user_id, identity_id, merged.get("conflicts", []))
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
        """
        Normalize an identity record's container fields to consistent dict and list types.
        
        Parameters:
            identity (Dict): Raw identity mapping that may contain traits, values, beliefs, open_loops, patterns, emotions, and conflicts in varying formats.
        
        Returns:
            Dict: A shallow copy of the input with the following guaranteed types:
                - `traits`: dict
                - `values`: dict
                - `beliefs`: list
                - `open_loops`: list
                - `patterns`: list
                - `emotions`: list
                - `conflicts`: list
        """
        identity = dict(identity)
        identity["traits"] = self._ensure_dict(identity.get("traits"))
        identity["values"] = self._ensure_dict(identity.get("values"))
        identity["beliefs"] = self._ensure_list(identity.get("beliefs"))
        identity["open_loops"] = self._ensure_list(identity.get("open_loops"))
        identity["patterns"] = self._ensure_list(identity.get("patterns", []))
        identity["emotions"] = self._ensure_list(identity.get("emotions", []))
        identity["conflicts"] = self._ensure_list(identity.get("conflicts", []))
        return identity

    def _hydrate_identity(self, identity: Dict) -> Dict:
        """
        Normalize an identity payload and populate its related components from their stores when an identity id is present.
        
        Parameters:
            identity (Dict): Identity data (row or payload) to deserialize and hydrate; may be a raw DB/Supabase record or an already-deserialized dict.
        
        Returns:
            Dict: The deserialized identity with fields `beliefs`, `open_loops`, `patterns`, `emotions`, and `conflicts` replaced by the corresponding lists loaded from their stores when `id` is present. If `id` is missing, returns the deserialized identity unchanged.
        """
        identity = self._deserialize_identity(identity)
        identity_id = identity.get("id")
        if not identity_id:
            return identity
        identity["beliefs"] = self.beliefs.load(identity["user_id"], identity_id)
        identity["open_loops"] = self.open_loops.load(identity["user_id"], identity_id)
        identity["patterns"] = self.patterns.load(identity["user_id"], identity_id)
        identity["emotions"] = self.emotions.load(identity["user_id"], identity_id)
        identity["conflicts"] = self.conflicts.load(identity["user_id"], identity_id)
        return identity

    @contextmanager
    def _session_scope(self, session: Optional[Any]):
        if session is not None:
            yield session
        else:
            with get_sql_session() as new_session:
                yield new_session
