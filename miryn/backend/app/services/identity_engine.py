from typing import Dict, List, Any, Optional
from datetime import date, datetime
import json
from uuid import uuid4
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


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


class _RetryWrite(Exception):
    """Internal: the guarded insert lost a concurrency race; retry fresh."""


class IdentityEngine:
    def __init__(self, reflection=None):
        self.supabase = get_db() if not has_sql() else None
        self.beliefs = BeliefStore()
        self.open_loops = OpenLoopStore()
        self.patterns = PatternStore()
        self.emotions = EmotionStore()
        self.conflicts = ConflictStore()
        self.reflection = reflection

    def get_identity(self, user_id: str, sql_session: Optional[Any] = None) -> Dict:
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text("SELECT * FROM identities WHERE user_id = :user_id ORDER BY version DESC LIMIT 1"),
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
                new_id = str(uuid4())
                session.execute(
                    text(
                        """
                        INSERT INTO identities (id, user_id, version, state, traits, "values", beliefs, open_loops, preset, memory_weights)
                        VALUES (:id, :user_id, :version, :state, :traits, :values, :beliefs, :open_loops, :preset, :memory_weights)
                        """
                    ),
                    {
                        "id": new_id,
                        "user_id": user_id,
                        "version": 1,
                        "state": "onboarding",
                        "traits": json.dumps(identity["traits"], default=_json_default),
                        "values": json.dumps(identity["values"], default=_json_default),
                        "beliefs": json.dumps(identity["beliefs"], default=_json_default),
                        "open_loops": json.dumps(identity["open_loops"], default=_json_default),
                        "preset": identity["preset"],
                        "memory_weights": json.dumps(identity["memory_weights"], default=_json_default),
                    },
                )
                result = session.execute(
                    text("SELECT * FROM identities WHERE id = :id"),
                    {"id": new_id},
                ).mappings().first()
                return self._hydrate_identity(dict(result), sql_session=session)

        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")

        response = self.supabase.table("identities").insert(identity).execute()
        return self._hydrate_identity(response.data[0])

    def update_identity(self, user_id: str, updates: Dict, sql_session: Optional[Any] = None) -> Dict:
        if has_sql():
            # Ensure an initial row exists, then merge against the latest row
            # inside the insert retry loop so a version collision re-merges
            # against fresh state instead of writing a stale snapshot.
            self.get_identity(user_id, sql_session=sql_session)
            return self._insert_identity_sql(user_id, updates, sql_session=sql_session)

        current = self.get_identity(user_id, sql_session=sql_session)
        merged = self._merge_identity(current, updates)
        return self._insert_identity_supabase(user_id, merged, updates)

    def _insert_identity_sql(self, user_id: str, updates: Dict, sql_session: Optional[Any] = None) -> Dict:
        # Optimistic concurrency: the insert only lands when the latest
        # version is still the one we just merged against. If another writer
        # commits in between, zero rows are inserted and the loop retries with
        # a fresh read and a fresh merge instead of writing a stale snapshot.
        stmt = text(
            """
            INSERT INTO identities (id, user_id, version, state, traits, "values", beliefs, open_loops, preset, memory_weights)
            SELECT
                :id,
                :user_id,
                COALESCE((SELECT MAX(version) FROM identities WHERE user_id = :user_id), 0) + 1,
                :state,
                :traits,
                :values,
                :beliefs,
                :open_loops,
                :preset,
                :memory_weights
            WHERE COALESCE((SELECT MAX(version) FROM identities WHERE user_id = :user_id), 0) = :expected_version
            """
        )

        attempts = 0
        while attempts < 3:
            attempts += 1
            result_row = None
            try:
                with self._session_scope(sql_session) as session:
                    # One transaction per attempt: read, merge, guarded insert,
                    # child-store copies and the evolution log commit together,
                    # so a concurrent reader can never hydrate a committed
                    # identity row before its child stores exist. The savepoint
                    # keeps a unique-violation retry usable on a borrowed
                    # session instead of poisoning the caller's transaction.
                    with session.begin_nested():
                        previous = session.execute(
                            text("SELECT * FROM identities WHERE user_id = :user_id ORDER BY version DESC LIMIT 1"),
                            {"user_id": user_id},
                        ).mappings().first()
                        previous_identity = (
                            self._hydrate_identity(self._deserialize_identity(dict(previous)), sql_session=session)
                            if previous else {}
                        )
                        merged = self._merge_identity(previous_identity, updates)
                        new_id = str(uuid4())
                        payload = {
                            "id": new_id,
                            "user_id": user_id,
                            "state": merged["state"],
                            "traits": json.dumps(merged["traits"], default=_json_default),
                            "values": json.dumps(merged["values"], default=_json_default),
                            "beliefs": json.dumps(merged["beliefs"], default=_json_default),
                            "open_loops": json.dumps(merged["open_loops"], default=_json_default),
                            "preset": merged.get("preset"),
                            "memory_weights": json.dumps(merged.get("memory_weights", {}), default=_json_default),
                            "expected_version": previous_identity.get("version", 0),
                        }

                        insert_result = session.execute(stmt, payload)
                        if insert_result.rowcount == 0:
                            # Another writer committed between our read and
                            # insert. Roll back to the savepoint and retry
                            # against the fresh latest row.
                            raise _RetryWrite()

                        result_row = dict(session.execute(
                            text("SELECT * FROM identities WHERE id = :id"),
                            {"id": new_id},
                        ).mappings().first())

                        identity_id = str(result_row["id"])
                        self.beliefs.replace(user_id, identity_id, merged.get("beliefs", []), sql_session=session)
                        self.open_loops.replace(user_id, identity_id, merged.get("open_loops", []), sql_session=session)
                        self.patterns.replace(user_id, identity_id, merged.get("patterns", []), sql_session=session)
                        self.emotions.replace(user_id, identity_id, merged.get("emotions", []), sql_session=session)
                        self.conflicts.replace(user_id, identity_id, merged.get("conflicts", []), sql_session=session)
                        self._log_identity_evolution_sql(
                            session,
                            user_id=user_id,
                            identity_id=identity_id,
                            previous=previous_identity,
                            current=merged,
                            trigger_type="update_identity",
                        )

            except (_RetryWrite, IntegrityError):
                # Savepoint rollback already discarded the failed attempt.
                if attempts >= 3:
                    raise
                continue
            if result_row:
                # Hydrate only after the transaction commits, so a fresh
                # session sees the committed child-store copies.
                return self._hydrate_identity(result_row, sql_session=sql_session)
        raise RuntimeError("Failed to write identity")

    def _log_identity_evolution_sql(self, session: Any, user_id: str, identity_id: str, previous: Dict, current: Dict, trigger_type: str) -> None:
        fields = ["state", "traits", "values", "beliefs", "open_loops", "patterns", "emotions", "conflicts", "preset", "memory_weights"]
        params = []
        for field in fields:
            old_val = previous.get(field)
            new_val = current.get(field)
            if old_val == new_val: continue
            params.append({
                "id": str(uuid4()),
                "uid": user_id,
                "iid": identity_id,
                "f": field,
                "o": json.dumps(old_val, default=_json_default),
                "n": json.dumps(new_val, default=_json_default),
                "t": trigger_type
            })

        if params:
            session.execute(
                text("INSERT INTO identity_evolution_log (id, user_id, identity_id, field_changed, old_value, new_value, trigger_type) VALUES (:id, :uid, :iid, :f, :o, :n, :t)"),
                params
            )

    def _hydrate_identity(self, identity: Dict, sql_session: Optional[Any] = None) -> Dict:
        identity = self._deserialize_identity(identity)
        identity_id = identity.get("id")
        if not identity_id: return identity
        identity["beliefs"] = self.beliefs.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["open_loops"] = self.open_loops.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["patterns"] = self.patterns.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["emotions"] = self.emotions.load(identity["user_id"], identity_id, sql_session=sql_session)
        identity["conflicts"] = self.conflicts.load(identity["user_id"], identity_id, sql_session=sql_session)
        return identity

    def _deserialize_identity(self, identity: Dict) -> Dict:
        identity = dict(identity)
        for k in ["id", "user_id"]:
            if identity.get(k) is not None: identity[k] = str(identity[k])
        for k in ["traits", "values", "memory_weights"]:
            identity[k] = self._ensure_dict(identity.get(k))
        for k in ["beliefs", "open_loops", "patterns", "emotions", "conflicts"]:
            identity[k] = self._ensure_list(identity.get(k))
        return identity

    def _ensure_dict(self, v):
        if isinstance(v, dict): return v
        try: return json.loads(v) if isinstance(v, str) else {}
        except: return {}

    def _ensure_list(self, v):
        if isinstance(v, list): return v
        try: return json.loads(v) if isinstance(v, str) else []
        except: return []

    @contextmanager
    def _session_scope(self, session: Optional[Any]):
        if session is not None: yield session
        else:
            with get_sql_session() as new_session: yield new_session

    def record_belief(self, user_id: str, topic: str, belief: str, confidence: float):
        # Topic upsert applied against the fresh row inside the guarded
        # insert loop, so concurrent belief writes never wipe each other.
        now = datetime.utcnow().isoformat()
        return self.update_identity(user_id, {"_upsert_beliefs": [
            {"topic": topic, "belief": belief, "confidence": confidence, "created_at": now, "updated_at": now}
        ]})

    def track_open_loop(self, user_id: str, topic: str, importance: int):
        current = self.get_identity(user_id)
        open_loops = current.get("open_loops", [])
        existing = next((l for l in open_loops if l.get("topic") == topic), None)
        now = datetime.utcnow().isoformat()
        if existing:
            existing["importance"] = importance
            existing["last_mentioned"] = now
        else:
            open_loops.append({"topic": topic, "importance": importance, "last_mentioned": now})
        return self.update_identity(user_id, {"open_loops": open_loops})

    async def detect_conflicts(self, user_id: str, new_statement: str) -> List[Dict]:
        if not self.reflection: return []
        identity = self.get_identity(user_id)
        return await self.reflection.detect_contradictions(identity.get("beliefs", []), new_statement)

    def _merge_identity(self, current: Dict, updates: Dict) -> Dict:
        replace = set(updates.get("_replace", ()))
        return {
            "state": updates.get("state", current.get("state")),
            "traits": (
                self._ensure_dict(updates.get("traits"))
                if "traits" in replace
                else {**self._ensure_dict(current.get("traits")), **self._ensure_dict(updates.get("traits"))}
            ),
            "values": (
                self._ensure_dict(updates.get("values"))
                if "values" in replace
                else {**self._ensure_dict(current.get("values")), **self._ensure_dict(updates.get("values"))}
            ),
            "beliefs": self._merge_beliefs(current.get("beliefs", []), updates),
            "open_loops": self._normalize_open_loops(
                self._ensure_list(updates.get("open_loops", current.get("open_loops", [])))
            ),
            "patterns": list(self._ensure_list(updates.get("patterns", current.get("patterns", [])))),
            "emotions": list(self._ensure_list(updates.get("emotions", current.get("emotions", [])))),
            "conflicts": list(self._ensure_list(updates.get("conflicts", current.get("conflicts", [])))),
            "preset": updates.get("preset", current.get("preset")),
            "memory_weights": (
                self._ensure_dict(updates.get("memory_weights"))
                if "memory_weights" in replace
                else self._ensure_dict(updates.get("memory_weights", current.get("memory_weights", {})))
            ),
            "base_version": current.get("version", 0),
        }

    def _merge_beliefs(self, current_beliefs: Any, updates: Dict) -> List[Dict]:
        # An explicit "beliefs" list replaces wholesale. Otherwise apply
        # "_upsert_beliefs" by topic against the current list, so a belief
        # write never wipes beliefs another writer added concurrently. The
        # upsert runs inside the guarded insert loop, so each retry re-applies
        # it against the freshly read row.
        if "beliefs" in updates:
            return list(self._ensure_list(updates.get("beliefs")))
        beliefs = [dict(b) for b in self._ensure_list(current_beliefs) if isinstance(b, dict)]
        for upsert in self._ensure_list(updates.get("_upsert_beliefs", [])):
            if not isinstance(upsert, dict):
                continue
            now = upsert.get("updated_at") or datetime.utcnow().isoformat()
            existing = next((b for b in beliefs if b.get("topic") == upsert.get("topic")), None)
            if existing:
                for key, value in upsert.items():
                    if key not in ("topic", "created_at"):
                        existing[key] = value
                existing["updated_at"] = now
            else:
                merged_belief = dict(upsert)
                merged_belief.setdefault("created_at", now)
                merged_belief["updated_at"] = now
                beliefs.append(merged_belief)
        return beliefs

    def _normalize_open_loops(self, loops: List[Dict]) -> List[Dict]:
        normalized = []
        for loop in loops:
            if not isinstance(loop, dict):
                normalized.append(loop)
                continue
            loop = dict(loop)
            last_mentioned = loop.get("last_mentioned")
            if isinstance(last_mentioned, (datetime, date)):
                loop["last_mentioned"] = last_mentioned.isoformat()
            normalized.append(loop)
        return normalized

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
            "state", "traits", "values", "beliefs", "open_loops",
            "patterns", "emotions", "conflicts", "preset", "memory_weights",
        ]

        logs = []
        for field in fields:
            old_value = previous.get(field)
            new_value = current.get(field)
            if old_value == new_value:
                continue
            logs.append({
                "user_id": user_id,
                "identity_id": identity_id,
                "field_changed": field,
                "old_value": json.dumps(old_value, default=_json_default),
                "new_value": json.dumps(new_value, default=_json_default),
                "trigger_type": trigger_type,
            })

        if logs:
            self.supabase.table("identity_evolution_log").insert(logs).execute()

    def _insert_identity_supabase(self, user_id: str, merged: Dict, updates: Dict) -> Dict:
        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")
        attempts = 0
        while attempts < 3:
            attempts += 1
            version = merged.get("base_version", 0) + 1

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
                current = self.get_identity(user_id)
                merged = self._merge_identity(current, updates)

        raise RuntimeError("Failed to insert identity after retries")
