"""
Memory Ranker Service - Divyadeep Kaur
Loads trained XGBoost model and ranks memories for a given user message.
"""
import pickle
import numpy as np
import os

MODEL_FILE = os.path.join(os.path.dirname(__file__), "memory_ranking_model.pkl")

_model = None

def _load_model():
    global _model
    if _model is None:
        with open(MODEL_FILE, "rb") as f:
            _model = pickle.load(f)
    return _model

def _extract_features(memory: dict) -> list:
    recency_score = max(0.0, 1.0 - (memory.get("days_ago", 0) / 180.0))
    return [
        recency_score,
        memory.get("emotional_intensity", 0.5),
        memory.get("entity_overlap", 0) / 5.0,
        float(memory.get("identity_alignment", 0)),
    ]

def rank_memories(memories: list) -> list:
    """
    Takes a list of memory dicts, returns them sorted by relevance score (highest first).
    Each memory needs: days_ago, emotional_intensity, entity_overlap, identity_alignment
    """
    model = _load_model()
    for memory in memories:
        features = np.array([_extract_features(memory)])
        memory["relevance_score"] = round(float(model.predict(features)[0]), 4)
    return sorted(memories, key=lambda x: x["relevance_score"], reverse=True)