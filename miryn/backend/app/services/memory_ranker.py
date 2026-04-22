"""
Memory Ranker Service - Divyadeep Kaur
Loads trained XGBoost model and ranks memories for a given user message.
Uses batch prediction for efficiency.
"""
import pickle
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

MODEL_FILE = os.path.join(os.path.dirname(__file__), "memory_ranking_model.pkl")

_model = None


def _load_model():
    """Load and cache the XGBoost model. Returns None if model file not found."""
    global _model
    if _model is not None:
        return _model
    try:
        with open(MODEL_FILE, "rb") as f:
            _model = pickle.load(f)
        logger.info("Memory ranking model loaded successfully.")
    except FileNotFoundError:
        logger.warning("memory_ranking_model.pkl not found. Run memory_ranking_model.py to train it.")
    except Exception as e:
        logger.warning("Failed to load memory ranking model: %s", e)
    return _model


def _extract_features(memory: dict) -> list:
    """Extract feature vector from a memory dict."""
    recency_score = max(0.0, 1.0 - (memory.get("days_ago", 0) / 180.0))
    return [
        recency_score,
        float(memory.get("emotional_intensity", 0.5)),
        float(memory.get("entity_overlap", 0)) / 5.0,
        float(memory.get("identity_alignment", 0)),
    ]


def rank_memories(memories: list) -> list:
    """
    Takes a list of memory dicts, returns them sorted by relevance score (highest first).
    Uses batch prediction for efficiency.
    Each memory needs: days_ago, emotional_intensity, entity_overlap, identity_alignment.
    Falls back to importance_score sort if model unavailable.
    """
    model = _load_model()

    if not model:
        # Fallback: sort by importance_score if model unavailable
        return sorted(memories, key=lambda x: x.get("importance_score", 0.5), reverse=True)

    try:
        # Batch prediction — much faster than per-memory loop
        feature_matrix = np.array([_extract_features(m) for m in memories])
        scores = model.predict(feature_matrix)
        for memory, score in zip(memories, scores):
            memory["relevance_score"] = round(float(score), 4)
    except Exception as e:
        logger.warning("Batch prediction failed: %s", e)
        for memory in memories:
            memory["relevance_score"] = memory.get("importance_score", 0.5)

    return sorted(memories, key=lambda x: x["relevance_score"], reverse=True)