from __future__ import annotations

import json
import logging
import math
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from app.core.database import get_sql_session, has_sql
from app.core.encryption import decrypt_text
from app.core.security import get_password_hash
from app.services.identity_engine import IdentityEngine

logger = logging.getLogger(__name__)

DEMO_PASSWORD = "MirynDemo!2026"
DEMO_PERSONA_EMAILS = {
    "alpha": "persona.alpha@miryn.demo",
    "beta": "persona.beta@miryn.demo",
}


@dataclass(frozen=True)
class DemoPersonaConfig:
    key: str
    label: str
    subtitle: str
    email: str
    goal: str
    report_summary: str
    current_state: str
    identities: list[dict[str, Any]]
    conversations: list[dict[str, Any]]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _build_demo_personas() -> list[DemoPersonaConfig]:
    base = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    alpha_identities = [
        {
            "version": 1,
            "state": "onboarding",
            "created_at": _iso(base),
            "traits": {"curious": 0.68, "empathetic": 0.62},
            "values": {"human_connection": 0.82, "beauty": 0.7},
            "beliefs": [
                {"topic": "technology", "belief": "Technology should feel humane before it feels efficient.", "confidence": 0.74},
            ],
            "open_loops": [
                {"topic": "finishing the interactive installation concept", "status": "open", "importance": 6, "last_mentioned": _iso(base)},
            ],
            "patterns": [
                {"pattern_type": "associative_jump", "description": "Moves quickly between emotion, metaphor, and sensory detail.", "confidence": 0.7, "signals": {"mode": "creative"}},
            ],
            "emotions": [
                {"primary_emotion": "hopeful", "intensity": 0.58, "secondary_emotions": ["curious"], "context": {"topic": "creative vision"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.34, "emotions": 0.34, "facts": 0.16, "goals": 0.16},
            "drift_score": 0.0,
        },
        {
            "version": 2,
            "state": "exploratory",
            "created_at": _iso(base + timedelta(days=2)),
            "traits": {"curious": 0.76, "empathetic": 0.81, "artistic": 0.78},
            "values": {"human_connection": 0.88, "beauty": 0.82, "reflection": 0.75},
            "beliefs": [
                {"topic": "technology", "belief": "Technology should feel humane before it feels efficient.", "confidence": 0.81},
                {"topic": "creative_practice", "belief": "Art helps people metabolize loneliness.", "confidence": 0.79},
            ],
            "open_loops": [
                {"topic": "interactive heartbeat installation", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=2, hours=3))},
                {"topic": "finding a gallery-friendly format", "status": "open", "importance": 5, "last_mentioned": _iso(base + timedelta(days=2, hours=5))},
            ],
            "patterns": [
                {"pattern_type": "associative_jump", "description": "Links emotional states to design choices and metaphors.", "confidence": 0.82, "signals": {"mode": "creative"}},
                {"pattern_type": "meaning_seeking", "description": "Uses projects as a way to search for emotional clarity.", "confidence": 0.71, "signals": {"mode": "reflective"}},
            ],
            "emotions": [
                {"primary_emotion": "inspired", "intensity": 0.74, "secondary_emotions": ["hopeful", "tender"], "context": {"topic": "installation concept"}},
                {"primary_emotion": "anxious", "intensity": 0.42, "secondary_emotions": ["excited"], "context": {"topic": "public sharing"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.3, "emotions": 0.38, "facts": 0.14, "goals": 0.18},
            "drift_score": 0.21,
        },
        {
            "version": 3,
            "state": "exploratory",
            "created_at": _iso(base + timedelta(days=5)),
            "traits": {"curious": 0.82, "empathetic": 0.88, "artistic": 0.9},
            "values": {"human_connection": 0.9, "beauty": 0.86, "reflection": 0.83},
            "beliefs": [
                {"topic": "technology", "belief": "Technology should feel humane before it feels efficient.", "confidence": 0.84},
                {"topic": "creative_practice", "belief": "Art helps people metabolize loneliness.", "confidence": 0.87},
                {"topic": "presence", "belief": "Meaningful systems should leave room for ambiguity and feeling.", "confidence": 0.76},
            ],
            "open_loops": [
                {"topic": "interactive heartbeat installation", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=5, hours=1))},
                {"topic": "sound design for the room", "status": "open", "importance": 7, "last_mentioned": _iso(base + timedelta(days=5, hours=2))},
            ],
            "patterns": [
                {"pattern_type": "associative_jump", "description": "Expands one creative problem into multiple emotional directions.", "confidence": 0.89, "signals": {"mode": "creative"}},
                {"pattern_type": "meaning_seeking", "description": "Returns to loneliness, belonging, and tenderness as recurrent anchors.", "confidence": 0.81, "signals": {"mode": "reflective"}},
            ],
            "emotions": [
                {"primary_emotion": "inspired", "intensity": 0.81, "secondary_emotions": ["curious"], "context": {"topic": "expanding the concept"}},
                {"primary_emotion": "vulnerable", "intensity": 0.59, "secondary_emotions": ["hopeful"], "context": {"topic": "showing unfinished work"}},
            ],
            "conflicts": [
                {"statement": "I want the work to stay intimate.", "conflict_with": "I also want it to reach as many people as possible.", "severity": 0.49, "resolved": False, "resolved_at": None},
            ],
            "memory_weights": {"beliefs": 0.28, "emotions": 0.4, "facts": 0.12, "goals": 0.2},
            "drift_score": 0.44,
        },
        {
            "version": 4,
            "state": "expressive",
            "created_at": _iso(base + timedelta(days=8)),
            "traits": {"curious": 0.84, "empathetic": 0.92, "artistic": 0.94},
            "values": {"human_connection": 0.94, "beauty": 0.9, "reflection": 0.88},
            "beliefs": [
                {"topic": "technology", "belief": "Technology should feel humane before it feels efficient.", "confidence": 0.86},
                {"topic": "creative_practice", "belief": "Art helps people metabolize loneliness.", "confidence": 0.91},
                {"topic": "presence", "belief": "Meaningful systems should leave room for ambiguity and feeling.", "confidence": 0.82},
                {"topic": "embodiment", "belief": "Physical space changes how vulnerable people can be with an AI.", "confidence": 0.74},
            ],
            "open_loops": [
                {"topic": "interactive heartbeat installation", "status": "open", "importance": 9, "last_mentioned": _iso(base + timedelta(days=8, hours=1))},
                {"topic": "sound design for the room", "status": "open", "importance": 7, "last_mentioned": _iso(base + timedelta(days=8, hours=2))},
                {"topic": "testing audience emotional response", "status": "open", "importance": 6, "last_mentioned": _iso(base + timedelta(days=8, hours=3))},
            ],
            "patterns": [
                {"pattern_type": "associative_jump", "description": "Uses emotional and aesthetic associations as a primary reasoning path.", "confidence": 0.92, "signals": {"mode": "creative"}},
                {"pattern_type": "meaning_seeking", "description": "Revisits intimacy and human connection across multiple domains.", "confidence": 0.87, "signals": {"mode": "reflective"}},
                {"pattern_type": "sensory_reasoning", "description": "Talks through color, light, heartbeat, and sound as cognitive tools.", "confidence": 0.78, "signals": {"mode": "embodied"}},
            ],
            "emotions": [
                {"primary_emotion": "inspired", "intensity": 0.84, "secondary_emotions": ["hopeful", "tender"], "context": {"topic": "installation thesis"}},
                {"primary_emotion": "vulnerable", "intensity": 0.61, "secondary_emotions": ["determined"], "context": {"topic": "public critique"}},
            ],
            "conflicts": [
                {"statement": "I want the work to stay intimate.", "conflict_with": "I also want it to reach as many people as possible.", "severity": 0.41, "resolved": False, "resolved_at": None},
            ],
            "memory_weights": {"beliefs": 0.27, "emotions": 0.42, "facts": 0.12, "goals": 0.19},
            "drift_score": 0.62,
        },
    ]

    beta_identities = [
        {
            "version": 1,
            "state": "onboarding",
            "created_at": _iso(base),
            "traits": {"precise": 0.74, "analytical": 0.71},
            "values": {"efficiency": 0.82, "correctness": 0.79},
            "beliefs": [
                {"topic": "systems", "belief": "A system should be optimized before it is beautified.", "confidence": 0.79},
            ],
            "open_loops": [
                {"topic": "benchmarking vector search latency", "status": "open", "importance": 7, "last_mentioned": _iso(base)},
            ],
            "patterns": [
                {"pattern_type": "problem_decomposition", "description": "Breaks questions into measurable subproblems.", "confidence": 0.74, "signals": {"mode": "technical"}},
            ],
            "emotions": [
                {"primary_emotion": "focused", "intensity": 0.63, "secondary_emotions": ["curious"], "context": {"topic": "baseline performance"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.38, "emotions": 0.16, "facts": 0.24, "goals": 0.22},
            "drift_score": 0.0,
        },
        {
            "version": 2,
            "state": "analytical",
            "created_at": _iso(base + timedelta(days=2)),
            "traits": {"precise": 0.81, "analytical": 0.84, "optimization_oriented": 0.76},
            "values": {"efficiency": 0.88, "correctness": 0.86},
            "beliefs": [
                {"topic": "systems", "belief": "A system should be optimized before it is beautified.", "confidence": 0.84},
                {"topic": "retrieval", "belief": "Latency matters more than elegance when the user is waiting.", "confidence": 0.8},
            ],
            "open_loops": [
                {"topic": "benchmarking vector search latency", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=2, hours=1))},
                {"topic": "HNSW vs IVF trade-offs", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=2, hours=2))},
            ],
            "patterns": [
                {"pattern_type": "problem_decomposition", "description": "Turns broad questions into measurable tests.", "confidence": 0.86, "signals": {"mode": "technical"}},
                {"pattern_type": "latency_fixation", "description": "Repeatedly returns to throughput, caching, and latency ceilings.", "confidence": 0.73, "signals": {"mode": "performance"}},
            ],
            "emotions": [
                {"primary_emotion": "focused", "intensity": 0.71, "secondary_emotions": ["determined"], "context": {"topic": "benchmarking"}},
                {"primary_emotion": "frustrated", "intensity": 0.34, "secondary_emotions": ["curious"], "context": {"topic": "unexpected slowdown"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.4, "emotions": 0.15, "facts": 0.24, "goals": 0.21},
            "drift_score": 0.12,
        },
        {
            "version": 3,
            "state": "analytical",
            "created_at": _iso(base + timedelta(days=5)),
            "traits": {"precise": 0.88, "analytical": 0.89, "optimization_oriented": 0.87},
            "values": {"efficiency": 0.9, "correctness": 0.9, "repeatability": 0.82},
            "beliefs": [
                {"topic": "systems", "belief": "A system should be optimized before it is beautified.", "confidence": 0.88},
                {"topic": "retrieval", "belief": "Latency matters more than elegance when the user is waiting.", "confidence": 0.84},
                {"topic": "evaluation", "belief": "Benchmarks are only useful when the experiment is reproducible.", "confidence": 0.79},
            ],
            "open_loops": [
                {"topic": "benchmarking vector search latency", "status": "closed", "importance": 7, "last_mentioned": _iso(base + timedelta(days=5, hours=1))},
                {"topic": "HNSW vs IVF trade-offs", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=5, hours=2))},
                {"topic": "quantization effects on recall", "status": "open", "importance": 7, "last_mentioned": _iso(base + timedelta(days=5, hours=3))},
            ],
            "patterns": [
                {"pattern_type": "problem_decomposition", "description": "Breaks architecture questions into metrics and thresholds.", "confidence": 0.9, "signals": {"mode": "technical"}},
                {"pattern_type": "latency_fixation", "description": "Frames most trade-offs through responsiveness and scaling.", "confidence": 0.82, "signals": {"mode": "performance"}},
            ],
            "emotions": [
                {"primary_emotion": "focused", "intensity": 0.76, "secondary_emotions": ["curious"], "context": {"topic": "quantization tests"}},
                {"primary_emotion": "satisfied", "intensity": 0.46, "secondary_emotions": ["determined"], "context": {"topic": "closing a benchmark loop"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.41, "emotions": 0.14, "facts": 0.24, "goals": 0.21},
            "drift_score": 0.21,
        },
        {
            "version": 4,
            "state": "analytical",
            "created_at": _iso(base + timedelta(days=8)),
            "traits": {"precise": 0.91, "analytical": 0.93, "optimization_oriented": 0.92},
            "values": {"efficiency": 0.92, "correctness": 0.91, "repeatability": 0.86},
            "beliefs": [
                {"topic": "systems", "belief": "A system should be optimized before it is beautified.", "confidence": 0.91},
                {"topic": "retrieval", "belief": "Latency matters more than elegance when the user is waiting.", "confidence": 0.88},
                {"topic": "evaluation", "belief": "Benchmarks are only useful when the experiment is reproducible.", "confidence": 0.84},
                {"topic": "deployment", "belief": "The best architecture is the one that stays observable in production.", "confidence": 0.77},
            ],
            "open_loops": [
                {"topic": "HNSW vs IVF trade-offs", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=8, hours=1))},
                {"topic": "quantization effects on recall", "status": "open", "importance": 8, "last_mentioned": _iso(base + timedelta(days=8, hours=2))},
                {"topic": "production observability thresholds", "status": "open", "importance": 7, "last_mentioned": _iso(base + timedelta(days=8, hours=3))},
            ],
            "patterns": [
                {"pattern_type": "problem_decomposition", "description": "Prefers narrow, measurable questions over abstract speculation.", "confidence": 0.94, "signals": {"mode": "technical"}},
                {"pattern_type": "latency_fixation", "description": "Returns to responsiveness and cost as primary quality signals.", "confidence": 0.86, "signals": {"mode": "performance"}},
                {"pattern_type": "stack_trace_reasoning", "description": "Uses logs, metrics, and traces as the main route to insight.", "confidence": 0.76, "signals": {"mode": "observability"}},
            ],
            "emotions": [
                {"primary_emotion": "focused", "intensity": 0.78, "secondary_emotions": ["determined"], "context": {"topic": "observability"}},
                {"primary_emotion": "calm", "intensity": 0.4, "secondary_emotions": ["satisfied"], "context": {"topic": "having a clean measurement plan"}},
            ],
            "conflicts": [],
            "memory_weights": {"beliefs": 0.42, "emotions": 0.13, "facts": 0.24, "goals": 0.21},
            "drift_score": 0.28,
        },
    ]

    alpha_messages = [
        {"role": "user", "content": "I keep imagining an installation that mirrors a heartbeat and makes loneliness feel visible in the room.", "offset_hours": 0, "importance_score": 0.82, "memory_tier": "episodic", "metadata": {"topics": ["installation", "loneliness", "embodiment"], "emotions": {"primary_emotion": "hopeful", "intensity": 0.58, "secondary_emotions": ["curious"]}}},
        {"role": "assistant", "content": "That idea feels intimate and embodied. The heartbeat motif suggests a physical way to translate emotional distance into shared presence.", "offset_hours": 0.2, "importance_score": 0.88, "memory_tier": "core", "metadata": {"topics": ["installation", "presence"], "emotions": {"primary_emotion": "supportive", "intensity": 0.46, "secondary_emotions": ["curious"]}}},
        {"role": "user", "content": "I want the lighting to move from cold blue into warmer reds when people stay with the piece long enough.", "offset_hours": 48, "importance_score": 0.76, "memory_tier": "episodic", "metadata": {"topics": ["lighting", "installation", "emotion"], "emotions": {"primary_emotion": "inspired", "intensity": 0.74, "secondary_emotions": ["hopeful"]}}},
        {"role": "assistant", "content": "That color shift turns attention into care. It gives the audience a felt sense that emotional presence changes the system.", "offset_hours": 48.2, "importance_score": 0.86, "memory_tier": "core", "metadata": {"topics": ["lighting", "presence"], "emotions": {"primary_emotion": "supportive", "intensity": 0.41, "secondary_emotions": ["warm"]}}},
        {"role": "user", "content": "Part of me wants to keep the work private because it feels so personal, but I also want it to help strangers.", "offset_hours": 120, "importance_score": 0.9, "memory_tier": "core", "metadata": {"topics": ["audience", "vulnerability", "installation"], "emotions": {"primary_emotion": "vulnerable", "intensity": 0.59, "secondary_emotions": ["hopeful"]}}},
        {"role": "assistant", "content": "That tension is important: intimacy is part of the work, but so is letting it travel beyond you.", "offset_hours": 120.2, "importance_score": 0.72, "memory_tier": "episodic", "metadata": {"topics": ["audience", "intimacy"], "emotions": {"primary_emotion": "supportive", "intensity": 0.38, "secondary_emotions": ["steady"]}}},
        {"role": "user", "content": "Now I’m thinking about adding breath-triggered sound so the room feels alive even before anyone speaks.", "offset_hours": 192, "importance_score": 0.79, "memory_tier": "episodic", "metadata": {"topics": ["sound", "breath", "embodiment"], "emotions": {"primary_emotion": "inspired", "intensity": 0.84, "secondary_emotions": ["tender"]}}},
        {"role": "assistant", "content": "That expands the piece from metaphor into atmosphere. Miryn would read this as your thinking becoming more sensory and more relational over time.", "offset_hours": 192.2, "importance_score": 0.91, "memory_tier": "core", "metadata": {"topics": ["sound", "identity", "pattern"], "emotions": {"primary_emotion": "supportive", "intensity": 0.44, "secondary_emotions": ["curious"]}}},
    ]

    beta_messages = [
        {"role": "user", "content": "I’m comparing HNSW and IVF for vector retrieval, and latency variance is bothering me more than average latency.", "offset_hours": 0, "importance_score": 0.81, "memory_tier": "episodic", "metadata": {"topics": ["retrieval", "hnsw", "ivf"], "emotions": {"primary_emotion": "focused", "intensity": 0.63, "secondary_emotions": ["curious"]}}},
        {"role": "assistant", "content": "Variance is the sharper signal for user experience. A stable 120ms often feels better than a mean that hides ugly spikes.", "offset_hours": 0.2, "importance_score": 0.85, "memory_tier": "core", "metadata": {"topics": ["latency", "retrieval"], "emotions": {"primary_emotion": "supportive", "intensity": 0.39, "secondary_emotions": ["steady"]}}},
        {"role": "user", "content": "I can close one benchmark loop, but quantization keeps opening another because recall drops exactly where I need confidence.", "offset_hours": 48, "importance_score": 0.78, "memory_tier": "episodic", "metadata": {"topics": ["quantization", "recall", "benchmark"], "emotions": {"primary_emotion": "frustrated", "intensity": 0.34, "secondary_emotions": ["focused"]}}},
        {"role": "assistant", "content": "That sounds like a good open loop: the system is fast enough, but the confidence boundary is still unstable.", "offset_hours": 48.2, "importance_score": 0.82, "memory_tier": "core", "metadata": {"topics": ["open_loop", "recall"], "emotions": {"primary_emotion": "supportive", "intensity": 0.33, "secondary_emotions": ["analytical"]}}},
        {"role": "user", "content": "What I trust most is a reproducible experiment. If I can’t rerun it cleanly, I don’t believe the result.", "offset_hours": 120, "importance_score": 0.89, "memory_tier": "core", "metadata": {"topics": ["evaluation", "reproducibility"], "emotions": {"primary_emotion": "focused", "intensity": 0.76, "secondary_emotions": ["determined"]}}},
        {"role": "assistant", "content": "That belief is becoming central in your identity map: you keep returning to repeatability as a condition for trust.", "offset_hours": 120.2, "importance_score": 0.86, "memory_tier": "core", "metadata": {"topics": ["identity", "reproducibility"], "emotions": {"primary_emotion": "supportive", "intensity": 0.35, "secondary_emotions": ["clear"]}}},
        {"role": "user", "content": "I’m less interested in abstract architecture debates than whether production traces will explain the failure fast enough.", "offset_hours": 192, "importance_score": 0.83, "memory_tier": "episodic", "metadata": {"topics": ["observability", "production", "traces"], "emotions": {"primary_emotion": "calm", "intensity": 0.4, "secondary_emotions": ["focused"]}}},
        {"role": "assistant", "content": "That’s a strong Miryn signal: you’re converging toward observability as the real proof of architectural quality.", "offset_hours": 192.2, "importance_score": 0.9, "memory_tier": "core", "metadata": {"topics": ["observability", "architecture"], "emotions": {"primary_emotion": "supportive", "intensity": 0.36, "secondary_emotions": ["precise"]}}},
    ]

    return [
        DemoPersonaConfig(
            key="alpha",
            label="Aditya Verma",
            subtitle="Creative / associative / emotionally expansive",
            email=DEMO_PERSONA_EMAILS["alpha"],
            goal="Explore identity-first interaction through sensory, emotional, and artistic prompts.",
            report_summary="Persona Alpha expands quickly across emotional and creative domains, producing higher semantic drift and more varied open loops.",
            current_state="expressive",
            identities=alpha_identities,
            conversations=[
                {"title": "Creative reflection lab", "messages": alpha_messages},
                {"title": "Project narrative planning", "messages": alpha_messages},
                {"title": "Demo execution notes", "messages": alpha_messages},
            ],
        ),
        DemoPersonaConfig(
            key="beta",
            label="Priya Sharma",
            subtitle="Technical / convergent / optimization-driven",
            email=DEMO_PERSONA_EMAILS["beta"],
            goal="Probe technical identity tracking through optimization, benchmarking, and observability discussions.",
            report_summary="Persona Beta stays tightly convergent around system performance, resulting in lower drift and more stable identity evolution.",
            current_state="analytical",
            identities=beta_identities,
            conversations=[
                {"title": "Systems benchmarking notebook", "messages": beta_messages},
                {"title": "Health-check planning", "messages": beta_messages},
                {"title": "Operational readiness log", "messages": beta_messages},
            ],
        ),
    ]


class DemoCompareService:
    def __init__(self) -> None:
        self.identity_engine = IdentityEngine()
        self.personas = _build_demo_personas()

    def require_sql(self) -> None:
        if not has_sql():
            raise RuntimeError("Demo comparison requires a SQL database connection.")

    def seed_demo_personas(self) -> dict[str, Any]:
        self.require_sql()
        with get_sql_session() as session:
            self._ensure_user_profiles_table(session)
            self._ensure_user_columns(session)
            self._ensure_identity_drift_column(session)
            self._ensure_identity_created_at_column(session)
            self._ensure_message_columns(session)
            self._delete_existing_demo_users(session)

            seeded = []
            for persona in self.personas:
                user_id = str(uuid4())
                hashed_password = get_password_hash(DEMO_PASSWORD)
                session.execute(
                    text(
                        """
                        INSERT INTO users (id, email, password_hash, is_deleted, is_verified)
                        VALUES (:id, :email, :password_hash, :is_deleted, :is_verified)
                        """
                    ),
                    {
                        "id": user_id,
                        "email": persona.email,
                        "password_hash": hashed_password,
                        "is_deleted": False,
                        "is_verified": True,
                    },
                )
                self._upsert_user_profile(session, user_id, persona)
                self._insert_persona_identities(session, user_id, persona)
                self._insert_persona_conversations(session, user_id, persona)
                seeded.append(self._persona_card(user_id, persona))

            return {
                "seeded_at": datetime.now(timezone.utc).isoformat(),
                "demo_password": DEMO_PASSWORD,
                "personas": seeded,
            }

    def list_demo_personas(self) -> list[dict[str, Any]]:
        self.require_sql()
        with get_sql_session() as session:
            cards: list[dict[str, Any]] = []
            for persona in self.personas:
                row = session.execute(
                    text("SELECT id, email FROM users WHERE email = :email LIMIT 1"),
                    {"email": persona.email},
                ).mappings().first()
                if not row:
                    continue
                cards.append(self._persona_card(str(row["id"]), persona))
            return cards

    def get_persona_detail(self, user_id: str) -> dict[str, Any]:
        self.require_sql()
        persona = self._persona_config_for_user(user_id)
        current_identity = self._fetch_current_identity(user_id)
        identity_versions = self._fetch_identity_versions(user_id)
        memory_items = self._fetch_messages_for_user(user_id)
        conversations = self._fetch_conversations_for_user(user_id)
        emotion_metrics = self._emotion_metrics(memory_items)
        memory_metrics = self._memory_metrics(memory_items)

        return {
            "profile": {
                "user_id": user_id,
                "label": persona.label,
                "subtitle": persona.subtitle,
                "email": persona.email,
                "goal": persona.goal,
                "report_summary": persona.report_summary,
            },
            "identity": current_identity,
            "identity_metrics": self._identity_metrics(identity_versions),
            "emotion_metrics": emotion_metrics,
            "memory_metrics": memory_metrics,
            "memory_snapshot": self._memory_snapshot(memory_items),
            "conversations": conversations,
        }

    def compare_users(self, left_user_id: str, right_user_id: str) -> dict[str, Any]:
        left = self.get_persona_detail(left_user_id)
        right = self.get_persona_detail(right_user_id)
        difference_metrics = self._difference_metrics(left["identity"], right["identity"])

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "left": left,
            "right": right,
            "difference_metrics": difference_metrics,
            "charts": {
                "drift_timeline": [
                    {
                        "version": point["version"],
                        "left": self._timeline_value(left["identity_metrics"]["version_timeline"], point["version"], "drift_score"),
                        "right": self._timeline_value(right["identity_metrics"]["version_timeline"], point["version"], "drift_score"),
                    }
                    for point in self._combined_versions(
                        left["identity_metrics"]["version_timeline"],
                        right["identity_metrics"]["version_timeline"],
                    )
                ],
                "emotion_distribution": {
                    "left": left["emotion_metrics"]["dominant_emotions"],
                    "right": right["emotion_metrics"]["dominant_emotions"],
                },
                "memory_distribution": {
                    "left": left["memory_metrics"]["distribution"],
                    "right": right["memory_metrics"]["distribution"],
                },
                "identity_counts": {
                    "left": self._identity_counts(left["identity"]),
                    "right": self._identity_counts(right["identity"]),
                },
            },
            "report_sections": self._report_sections(left, right, difference_metrics),
        }

    def build_report(self, left_user_id: str, right_user_id: str) -> dict[str, Any]:
        comparison = self.compare_users(left_user_id, right_user_id)
        sections = comparison["report_sections"]
        left = comparison["left"]
        right = comparison["right"]

        lines = [
            "# Miryn Identity Comparison Report",
            "",
            "## Introduction",
            sections["introduction"],
            "",
            "## Persona A Profile",
            f"**{left['profile']['label']}** - {left['profile']['subtitle']}",
            left["profile"]["report_summary"],
            "",
            f"- State: {left['identity']['state']}",
            f"- Version: {left['identity']['version']}",
            f"- Drift score: {left['identity_metrics']['drift']}",
            f"- Stability score: {left['identity_metrics']['stability_score']}",
            "",
            "## Persona B Profile",
            f"**{right['profile']['label']}** - {right['profile']['subtitle']}",
            right["profile"]["report_summary"],
            "",
            f"- State: {right['identity']['state']}",
            f"- Version: {right['identity']['version']}",
            f"- Drift score: {right['identity_metrics']['drift']}",
            f"- Stability score: {right['identity_metrics']['stability_score']}",
            "",
            "## Comparative Analysis",
        ]

        for item in sections["comparison_dimensions"]:
            lines.extend([f"### {item['title']}", item["body"], ""])

        lines.extend(
            [
                "## Drift Analysis",
                sections["drift_analysis"],
                "",
                "## Memory and Identity Observations",
                sections["memory_observations"],
                "",
                "## Where Miryn Is Stronger Than Plain Chat",
                sections["miryn_standout"],
                "",
                "## Conclusion",
                sections["conclusion"],
            ]
        )

        markdown = "\n".join(lines).strip() + "\n"
        return {
            "generated_at": comparison["generated_at"],
            "left_user_id": left_user_id,
            "right_user_id": right_user_id,
            "markdown": markdown,
            "sections": sections,
        }

    def _persona_card(self, user_id: str, persona: DemoPersonaConfig) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "key": persona.key,
            "label": persona.label,
            "subtitle": persona.subtitle,
            "email": persona.email,
            "goal": persona.goal,
        }

    def _persona_config_for_user(self, user_id: str) -> DemoPersonaConfig:
        with get_sql_session() as session:
            row = session.execute(
                text("SELECT email FROM users WHERE id = :user_id LIMIT 1"),
                {"user_id": user_id},
            ).mappings().first()
        if not row:
            raise RuntimeError("Demo persona not found.")
        email = str(row["email"])
        for persona in self.personas:
            if persona.email == email:
                return persona
        raise RuntimeError("User is not a seeded demo persona.")

    def _ensure_user_profiles_table(self, session: Any) -> None:
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    full_name TEXT,
                    avatar_url TEXT,
                    primary_goal TEXT,
                    selected_traits TEXT,
                    communication_style TEXT,
                    preferred_depth TEXT,
                    onboarding_completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

    def _ensure_user_columns(self, session: Any) -> None:
        statements = [
            "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0",
            "ALTER TABLE users ADD COLUMN notification_preferences TEXT",
            "ALTER TABLE users ADD COLUMN data_retention TEXT",
            "ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP",
        ]
        for statement in statements:
            try:
                session.execute(text(statement))
            except Exception:
                pass

    def _ensure_identity_drift_column(self, session: Any) -> None:
        try:
            session.execute(text("ALTER TABLE identities ADD COLUMN drift_score FLOAT DEFAULT 0"))
        except Exception:
            pass

    def _ensure_identity_created_at_column(self, session: Any) -> None:
        try:
            session.execute(text("ALTER TABLE identities ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass
        try:
            session.execute(text("ALTER TABLE identities ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass

    def _ensure_message_columns(self, session: Any) -> None:
        statements = [
            "ALTER TABLE messages ADD COLUMN metadata TEXT",
            "ALTER TABLE messages ADD COLUMN importance_score FLOAT DEFAULT 0.5",
            "ALTER TABLE messages ADD COLUMN memory_tier VARCHAR(20) DEFAULT 'episodic'",
            "ALTER TABLE messages ADD COLUMN delete_at TIMESTAMP",
            "ALTER TABLE messages ADD COLUMN content_encrypted TEXT",
            "ALTER TABLE messages ADD COLUMN metadata_encrypted TEXT",
            "ALTER TABLE messages ADD COLUMN encryption_version INT DEFAULT 1",
            "ALTER TABLE messages ADD COLUMN idempotency_key VARCHAR(255)",
            "ALTER TABLE messages ADD COLUMN embedding_source VARCHAR(50) DEFAULT 'demo'",
        ]
        for statement in statements:
            try:
                session.execute(text(statement))
            except Exception:
                pass

    def _delete_existing_demo_users(self, session: Any) -> None:
        rows = session.execute(
            text(
                "SELECT id FROM users WHERE email IN (:alpha_email, :beta_email)"
            ),
            {
                "alpha_email": DEMO_PERSONA_EMAILS["alpha"],
                "beta_email": DEMO_PERSONA_EMAILS["beta"],
            },
        ).mappings().all()
        user_ids = [str(row["id"]) for row in rows]
        if not user_ids:
            return

        table_pairs = [
            ("identity_beliefs", "user_id"),
            ("identity_conflicts", "user_id"),
            ("identity_emotions", "user_id"),
            ("identity_open_loops", "user_id"),
            ("identity_patterns", "user_id"),
            ("identity_evolution_log", "user_id"),
            ("messages", "user_id"),
            ("conversations", "user_id"),
            ("onboarding_responses", "user_id"),
            ("audit_logs", "user_id"),
            ("notifications", "user_id"),
            ("tool_runs", "user_id"),
            ("memory_summaries", "user_id"),
            ("identities", "user_id"),
            ("user_profiles", "user_id"),
            ("users", "id"),
        ]
        for user_id in user_ids:
            for table, field in table_pairs:
                try:
                    session.execute(text(f"DELETE FROM {table} WHERE {field} = :user_id"), {"user_id": user_id})
                except Exception:
                    logger.debug("Skipping optional cleanup table=%s field=%s", table, field, exc_info=True)

    def _upsert_user_profile(self, session: Any, user_id: str, persona: DemoPersonaConfig) -> None:
        try:
            session.execute(text("DELETE FROM user_profiles WHERE user_id = :user_id"), {"user_id": user_id})
            session.execute(
                text(
                    """
                    INSERT INTO user_profiles (
                        user_id, full_name, primary_goal, selected_traits, communication_style, preferred_depth, onboarding_completed
                    ) VALUES (
                        :user_id, :full_name, :primary_goal, :selected_traits, :communication_style, :preferred_depth, :onboarding_completed
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "full_name": persona.label,
                    "primary_goal": persona.goal,
                    "selected_traits": persona.subtitle,
                    "communication_style": "reflective" if persona.key == "alpha" else "precise",
                    "preferred_depth": "deep" if persona.key == "alpha" else "structured",
                    "onboarding_completed": True,
                },
            )
        except Exception:
            logger.debug("Skipping user profile upsert for demo user %s", user_id, exc_info=True)

    def _insert_persona_identities(self, session: Any, user_id: str, persona: DemoPersonaConfig) -> None:
        previous_identity: dict[str, Any] | None = None
        for identity_seed in persona.identities:
            identity_id = str(uuid4())
            payload = deepcopy(identity_seed)
            created_at = payload.pop("created_at")
            beliefs = payload.pop("beliefs")
            open_loops = payload.pop("open_loops")
            patterns = payload.pop("patterns")
            emotions = payload.pop("emotions")
            conflicts = payload.pop("conflicts")
            drift_score = payload.pop("drift_score", 0.0)

            session.execute(
                text(
                    """
                    INSERT INTO identities (
                        id, user_id, version, state, traits, "values", beliefs, open_loops, preset, memory_weights, drift_score, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :version, :state, :traits, :values, :beliefs, :open_loops, :preset, :memory_weights, :drift_score, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": identity_id,
                    "user_id": user_id,
                    "version": payload["version"],
                    "state": payload["state"],
                    "traits": json.dumps(payload["traits"]),
                    "values": json.dumps(payload["values"]),
                    "beliefs": json.dumps(beliefs),
                    "open_loops": json.dumps(open_loops),
                    "preset": persona.key,
                    "memory_weights": json.dumps(payload["memory_weights"]),
                    "drift_score": drift_score,
                    "created_at": created_at,
                    "updated_at": created_at,
                },
            )

            current_identity = {
                "id": identity_id,
                "user_id": user_id,
                "version": payload["version"],
                "state": payload["state"],
                "traits": payload["traits"],
                "values": payload["values"],
                "beliefs": beliefs,
                "open_loops": open_loops,
                "patterns": patterns,
                "emotions": emotions,
                "conflicts": conflicts,
                "preset": persona.key,
                "memory_weights": payload["memory_weights"],
            }
            if previous_identity is not None:
                self._write_evolution_rows(session, user_id, identity_id, previous_identity, current_identity, created_at)
            previous_identity = current_identity

    def _write_evolution_rows(
        self,
        session: Any,
        user_id: str,
        identity_id: str,
        previous: dict[str, Any],
        current: dict[str, Any],
        created_at: str,
    ) -> None:
        fields = ["state", "traits", "values", "beliefs", "open_loops", "patterns", "emotions", "conflicts", "memory_weights"]
        for field in fields:
            if previous.get(field) == current.get(field):
                continue
            session.execute(
                text(
                    """
                    INSERT INTO identity_evolution_log (
                        id, user_id, identity_id, field_changed, old_value, new_value, trigger_type, created_at
                    ) VALUES (
                        :id, :user_id, :identity_id, :field_changed, :old_value, :new_value, :trigger_type, :created_at
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "identity_id": identity_id,
                    "field_changed": field,
                    "old_value": json.dumps(previous.get(field), default=str),
                    "new_value": json.dumps(current.get(field), default=str),
                    "trigger_type": "demo_seed",
                    "created_at": created_at,
                },
            )

    def _insert_persona_conversations(self, session: Any, user_id: str, persona: DemoPersonaConfig) -> None:
        base = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
        for conversation_seed in persona.conversations:
            conversation_id = str(uuid4())
            created_at = _iso(base)
            session.execute(
                text(
                    """
                    INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                    VALUES (:id, :user_id, :title, :created_at, :updated_at)
                    """
                ),
                {
                    "id": conversation_id,
                    "user_id": user_id,
                    "title": conversation_seed["title"],
                    "created_at": created_at,
                    "updated_at": created_at,
                },
            )
            for message_seed in conversation_seed["messages"]:
                created_message_at = _iso(base + timedelta(hours=float(message_seed["offset_hours"])))
                session.execute(
                    text(
                        """
                        INSERT INTO messages (
                            id, conversation_id, user_id, role, content, metadata, importance_score, memory_tier, delete_at, content_encrypted, metadata_encrypted, encryption_version, idempotency_key, embedding_source, created_at
                        ) VALUES (
                            :id, :conversation_id, :user_id, :role, :content, :metadata, :importance_score, :memory_tier, NULL, NULL, NULL, 1, NULL, :embedding_source, :created_at
                        )
                        """
                    ),
                    {
                        "id": str(uuid4()),
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "role": message_seed["role"],
                        "content": message_seed["content"],
                        "metadata": json.dumps(message_seed.get("metadata", {})),
                        "importance_score": message_seed.get("importance_score", 0.5),
                        "memory_tier": message_seed.get("memory_tier", "episodic"),
                        "embedding_source": "demo",
                        "created_at": created_message_at,
                    },
            )
            session.execute(
                text("UPDATE conversations SET updated_at = :updated_at WHERE id = :id"),
                {"updated_at": created_message_at, "id": conversation_id},
            )

    def _fetch_current_identity(self, user_id: str) -> dict[str, Any]:
        with get_sql_session() as session:
            row = session.execute(
                text("SELECT * FROM identities WHERE user_id = :user_id ORDER BY version DESC LIMIT 1"),
                {"user_id": user_id},
            ).mappings().first()

        if not row:
            raise ValueError(f"No identity found for demo user {user_id}")

        identity = dict(row)
        return {
            "id": str(identity.get("id")),
            "user_id": str(identity.get("user_id")),
            "version": int(identity.get("version") or 1),
            "state": identity.get("state") or "onboarding",
            "traits": self._ensure_dict(identity.get("traits")),
            "values": self._ensure_dict(identity.get("values")),
            "beliefs": self._ensure_list(identity.get("beliefs")),
            "open_loops": self._ensure_list(identity.get("open_loops")),
            "patterns": self._ensure_list(identity.get("patterns")),
            "emotions": self._ensure_list(identity.get("emotions")),
            "conflicts": self._ensure_list(identity.get("conflicts")),
            "preset": identity.get("preset"),
            "memory_weights": self._ensure_dict(identity.get("memory_weights")),
        }

    def _fetch_identity_versions(self, user_id: str) -> list[dict[str, Any]]:
        with get_sql_session() as session:
            rows = session.execute(
                text("SELECT * FROM identities WHERE user_id = :user_id ORDER BY version ASC"),
                {"user_id": user_id},
            ).mappings().all()
        versions: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            beliefs = self._ensure_list(item.get("beliefs"))
            open_loops = self._ensure_list(item.get("open_loops"))
            versions.append(
                {
                    "version": int(item.get("version") or 0),
                    "state": item.get("state") or "unknown",
                    "belief_count": len(beliefs),
                    "open_loop_count": len(open_loops),
                    "drift_score": float(item.get("drift_score") or 0.0),
                    "created_at": item.get("created_at") or item.get("last_updated"),
                }
            )
        return versions

    def _fetch_messages_for_user(self, user_id: str) -> list[dict[str, Any]]:
        with get_sql_session() as session:
            rows = session.execute(
                text("SELECT * FROM messages WHERE user_id = :user_id ORDER BY created_at ASC"),
                {"user_id": user_id},
            ).mappings().all()

        return [self._hydrate_message(dict(row)) for row in rows]

    def _fetch_conversations_for_user(self, user_id: str) -> list[dict[str, Any]]:
        with get_sql_session() as session:
            conversations = session.execute(
                text("SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = :user_id ORDER BY created_at ASC"),
                {"user_id": user_id},
            ).mappings().all()
            messages = session.execute(
                text("SELECT * FROM messages WHERE user_id = :user_id ORDER BY created_at ASC"),
                {"user_id": user_id},
            ).mappings().all()

        by_conversation: dict[str, list[dict[str, Any]]] = {}
        for row in messages:
            item = self._hydrate_message(dict(row))
            by_conversation.setdefault(str(item.get("conversation_id")), []).append(item)

        results: list[dict[str, Any]] = []
        for conversation in conversations:
            conversation_id = str(conversation["id"])
            results.append(
                {
                    "id": conversation_id,
                    "title": conversation.get("title") or "Untitled Conversation",
                    "created_at": conversation.get("created_at"),
                    "updated_at": conversation.get("updated_at"),
                    "messages": by_conversation.get(conversation_id, []),
                }
            )
        return results

    def _hydrate_message(self, row: dict[str, Any]) -> dict[str, Any]:
        content = row.get("content")
        if not content and row.get("content_encrypted"):
            try:
                content = decrypt_text(row.get("content_encrypted"))
            except Exception:
                content = None

        metadata = row.get("metadata")
        if not metadata and row.get("metadata_encrypted"):
            try:
                decrypted = decrypt_text(row.get("metadata_encrypted"))
                metadata = json.loads(decrypted) if decrypted else {}
            except Exception:
                metadata = {}

        return {
            "id": str(row.get("id")),
            "conversation_id": str(row.get("conversation_id")) if row.get("conversation_id") else None,
            "role": row.get("role") or "assistant",
            "content": content or "",
            "metadata": self._ensure_dict(metadata),
            "importance_score": float(row.get("importance_score") or 0.0),
            "memory_tier": row.get("memory_tier") or "episodic",
            "timestamp": row.get("created_at"),
            "created_at": row.get("created_at"),
        }

    def _identity_metrics(self, versions: list[dict[str, Any]]) -> dict[str, Any]:
        if not versions:
            return {"stability_score": None, "drift": None, "total_versions": 0, "version_timeline": []}
        belief_counts = [version["belief_count"] for version in versions]
        if len(belief_counts) < 2 or max(belief_counts) == 0:
            stability = 1.0
        else:
            avg = sum(belief_counts) / len(belief_counts)
            variance = sum((count - avg) ** 2 for count in belief_counts) / len(belief_counts)
            stability = 1.0 / (1.0 + variance)

        drift = float(versions[-1].get("drift_score") or 0.0)
        return {
            "stability_score": round(stability, 4),
            "drift": round(drift, 4),
            "total_versions": len(versions),
            "version_timeline": versions,
        }

    def _emotion_metrics(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        records = []
        for message in messages:
            emotions = self._ensure_dict(message.get("metadata")).get("emotions", {})
            primary = emotions.get("primary_emotion")
            if not primary:
                continue
            try:
                intensity = float(emotions.get("intensity", 0.5))
            except (TypeError, ValueError):
                intensity = 0.5
            records.append({"emotion": primary, "intensity": intensity})

        if not records:
            return {"mood_score": None, "volatility": None, "trend": "neutral", "entropy": None, "dominant_emotions": []}

        positive = {"joy", "happy", "excited", "content", "love", "optimistic", "hopeful", "inspired", "calm", "satisfied"}
        negative = {"sad", "angry", "fear", "disgust", "anxious", "depressed", "frustrated", "vulnerable"}
        mood_score = 0.5
        for record in records:
            emotion = record["emotion"].lower()
            if emotion in positive:
                mood_score += record["intensity"] * 0.1
            elif emotion in negative:
                mood_score -= record["intensity"] * 0.1

        intensities = [record["intensity"] for record in records]
        if len(intensities) < 2:
            volatility = 0.0
            trend = "stable"
        else:
            avg = sum(intensities) / len(intensities)
            volatility = (sum((value - avg) ** 2 for value in intensities) / len(intensities)) ** 0.5
            midpoint = len(intensities) // 2 or 1
            first_half = mean(intensities[:midpoint])
            second_half = mean(intensities[midpoint:])
            if second_half - first_half > 0.05:
                trend = "improving"
            elif second_half - first_half < -0.05:
                trend = "declining"
            else:
                trend = "stable"

        counts = Counter(record["emotion"] for record in records)
        dominant = [{"emotion": emotion, "count": count} for emotion, count in counts.most_common(4)]

        total = len(records)
        entropy = round(
            -sum((count / total) * math.log2(count / total) for count in counts.values() if count > 0),
            4,
        )

        return {
            "mood_score": round(max(0.0, min(1.0, mood_score)), 4),
            "volatility": round(volatility, 4),
            "trend": trend,
            "entropy": entropy,
            "dominant_emotions": dominant,
        }

    def _memory_metrics(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        distribution_counter = Counter(message.get("memory_tier") or "episodic" for message in messages)
        avg_importance = round(mean([message.get("importance_score", 0.0) for message in messages]) if messages else 0.0, 4)
        emotion_tagged = sum(1 for message in messages if self._ensure_dict(message.get("metadata")).get("emotions"))
        return {
            "total_messages": len(messages),
            "core_count": distribution_counter.get("core", 0),
            "episodic_count": distribution_counter.get("episodic", 0),
            "transient_count": distribution_counter.get("transient", 0),
            "emotion_tagged_count": emotion_tagged,
            "average_importance": avg_importance,
            "distribution": [
                {"tier": "core", "count": distribution_counter.get("core", 0)},
                {"tier": "episodic", "count": distribution_counter.get("episodic", 0)},
                {"tier": "transient", "count": distribution_counter.get("transient", 0)},
            ],
        }

    def _memory_snapshot(self, messages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        recent = list(reversed(messages[-6:]))
        facts = [message for message in messages if message.get("memory_tier") == "core"][-6:]
        emotions = [message for message in messages if self._ensure_dict(message.get("metadata")).get("emotions")][-6:]
        return {"recent": list(reversed(recent)), "facts": list(reversed(facts)), "emotions": list(reversed(emotions))}

    def _difference_metrics(self, left_identity: dict[str, Any], right_identity: dict[str, Any]) -> dict[str, Any]:
        left_beliefs = {belief.get("topic", "").strip(): belief.get("belief", "") for belief in left_identity.get("beliefs", [])}
        right_beliefs = {belief.get("topic", "").strip(): belief.get("belief", "") for belief in right_identity.get("beliefs", [])}
        left_loops = {loop.get("topic", "").strip() for loop in left_identity.get("open_loops", []) if loop.get("topic")}
        right_loops = {loop.get("topic", "").strip() for loop in right_identity.get("open_loops", []) if loop.get("topic")}
        left_patterns = {pattern.get("pattern_type", "").strip() for pattern in left_identity.get("patterns", []) if pattern.get("pattern_type")}
        right_patterns = {pattern.get("pattern_type", "").strip() for pattern in right_identity.get("patterns", []) if pattern.get("pattern_type")}

        return {
            "shared_belief_topics": sorted(topic for topic in left_beliefs.keys() & right_beliefs.keys() if topic),
            "left_only_belief_topics": sorted(topic for topic in left_beliefs.keys() - right_beliefs.keys() if topic),
            "right_only_belief_topics": sorted(topic for topic in right_beliefs.keys() - left_beliefs.keys() if topic),
            "shared_open_loops": sorted(topic for topic in left_loops & right_loops if topic),
            "left_only_open_loops": sorted(topic for topic in left_loops - right_loops if topic),
            "right_only_open_loops": sorted(topic for topic in right_loops - left_loops if topic),
            "shared_pattern_types": sorted(pattern for pattern in left_patterns & right_patterns if pattern),
            "left_only_pattern_types": sorted(pattern for pattern in left_patterns - right_patterns if pattern),
            "right_only_pattern_types": sorted(pattern for pattern in right_patterns - left_patterns if pattern),
            "left_conflict_count": len(left_identity.get("conflicts", [])),
            "right_conflict_count": len(right_identity.get("conflicts", [])),
        }

    def _report_sections(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        difference_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        left_label = left["profile"]["label"]
        right_label = right["profile"]["label"]
        left_drift = left["identity_metrics"]["drift"] or 0.0
        right_drift = right["identity_metrics"]["drift"] or 0.0
        left_topics = ", ".join(difference_metrics["left_only_belief_topics"]) or "none"
        right_topics = ", ".join(difference_metrics["right_only_belief_topics"]) or "none"
        shared_patterns = ", ".join(difference_metrics["shared_pattern_types"]) or "none"

        comparison_dimensions = [
            {
                "title": "Identity orientation",
                "body": (
                    f"{left_label} currently presents as {left['identity']['state']} with strong emphasis on "
                    f"{', '.join(list(left['identity'].get('traits', {}).keys())[:3]) or 'emergent traits'}, while "
                    f"{right_label} presents as {right['identity']['state']} and concentrates on "
                    f"{', '.join(list(right['identity'].get('traits', {}).keys())[:3]) or 'emergent traits'}. "
                    f"The contrast is less about positivity or negativity and more about breadth versus convergence."
                ),
            },
            {
                "title": "Beliefs and open loops",
                "body": (
                    f"{left_label} carries unique belief topics around {left_topics}, which indicates expansion into new conceptual territory. "
                    f"{right_label} instead centers unique topics around {right_topics}, showing a narrower but deeper technical lane. "
                    f"Open loops mirror this: {left_label} keeps emotionally rich creative threads active, whereas {right_label} keeps performance and observability problems open until they are measurable."
                ),
            },
            {
                "title": "Patterns and emotions",
                "body": (
                    f"Both personas share {shared_patterns}, which means Miryn is still finding persistent structure in both users. "
                    f"However, {left_label} shows broader emotional variety and more metaphor-driven pattern formation, while {right_label} shows steadier affect and more repeatable reasoning patterns."
                ),
            },
        ]

        return {
            "introduction": (
                f"This report compares two seeded demo personas inside Miryn's identity-first architecture. "
                f"The objective is to show that the same AI system can maintain two sharply different user models over time, "
                f"then explain those differences through identity evolution, emotional traces, open loops, and memory distribution."
            ),
            "comparison_dimensions": comparison_dimensions,
            "drift_analysis": (
                f"{left_label} reaches a drift score of {left_drift:.2f}, while {right_label} reaches {right_drift:.2f}. "
                f"This gap supports the thesis claim that associative, emotionally expansive users force Miryn to keep widening its internal model, "
                f"whereas highly technical users often deepen an existing line of inquiry instead of branching into new semantic territory."
            ),
            "memory_observations": (
                f"{left_label} stores more emotionally marked and metaphor-rich memories, with core memories often tied to intimacy, embodiment, and audience meaning. "
                f"{right_label} stores more benchmark-oriented and systems-focused memories, with core memories clustering around latency, reproducibility, and observability. "
                f"Miryn's memory layer therefore retains not just facts, but the style and direction of each user's cognition."
            ),
            "miryn_standout": (
                "Miryn stands out because it does more than answer prompts in isolation. It tracks identity versions, preserves open loops, "
                "quantifies drift, and turns repeated interaction into a structured, inspectable user model. "
                "That makes the product demonstrably stronger than plain chat, especially in long-running reflective or analytical relationships."
            ),
            "conclusion": (
                f"In practice, the comparison shows that {left_label} and {right_label} are not just two chat histories with different wording. "
                "They become two evolving identities with different trajectories, emotional signatures, and unresolved threads. "
                "That is the clearest evidence that Miryn's architecture is modeling the user, not merely the message."
            ),
        }

    def _combined_versions(self, left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
        version_numbers = sorted({item["version"] for item in left} | {item["version"] for item in right})
        return [{"version": version} for version in version_numbers]

    def _timeline_value(self, timeline: list[dict[str, Any]], version: int, field: str) -> float:
        match = next((item for item in timeline if item["version"] == version), None)
        if not match:
            return 0.0
        try:
            return float(match.get(field) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _identity_counts(self, identity: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"label": "Beliefs", "count": len(identity.get("beliefs", []))},
            {"label": "Open loops", "count": len(identity.get("open_loops", []))},
            {"label": "Patterns", "count": len(identity.get("patterns", []))},
            {"label": "Emotions", "count": len(identity.get("emotions", []))},
            {"label": "Conflicts", "count": len(identity.get("conflicts", []))},
        ]

    def _ensure_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _ensure_list(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []


demo_compare_service = DemoCompareService()
