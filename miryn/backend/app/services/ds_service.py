"""
DS Service - Divyadeep Kaur
Local NER, emotion detection, and sentence embeddings.
Enhances the reflection engine with ML models (no API cost).
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class DSService:
    """
    Provides local ML-based NER, emotion detection, and embeddings
    as a faster/cheaper alternative to LLM-based extraction.
    """

    def __init__(self):
        self._nlp = None
        self._nlp_failed = False
        self._emotion_classifier = None
        self._emotion_failed = False
        self._sentence_model = None
        self._sentence_failed = False

    def _load_spacy(self):
        if self._nlp is not None:
            return self._nlp
        if self._nlp_failed:
            return None
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully.")
        except Exception as e:
            logger.warning("spaCy load failed: %s", e)
            self._nlp_failed = True
        return self._nlp

    def _load_emotion_model(self):
        if self._emotion_classifier is not None:
            return self._emotion_classifier
        if self._emotion_failed:
            return None
        try:
            from transformers import pipeline
            self._emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
            )
            logger.info("Emotion model loaded successfully.")
        except Exception as e:
            logger.warning("Emotion model load failed: %s", e)
            self._emotion_failed = True
        return self._emotion_classifier

    def _load_sentence_model(self):
        if self._sentence_model is not None:
            return self._sentence_model
        if self._sentence_failed:
            return None
        try:
            from sentence_transformers import SentenceTransformer
            self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Sentence transformer loaded successfully.")
        except Exception as e:
            logger.warning("Sentence transformer load failed: %s", e)
            self._sentence_failed = True
        return self._sentence_model

    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text using spaCy.
        Returns list of {text, label} dicts.
        Falls back to empty list if spaCy unavailable.
        """
        nlp = self._load_spacy()
        if not nlp:
            return []
        try:
            doc = nlp(text[:1000])  # limit input size
            return [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
                if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"}
            ]
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)
            return []

    def detect_emotions(self, text: str) -> Dict:
        """
        Detect emotions from text using HuggingFace model.
        Returns {primary_emotion, intensity, secondary_emotions}.
        Falls back to neutral if model unavailable.
        """
        classifier = self._load_emotion_model()
        if not classifier:
            return {"primary_emotion": "neutral", "intensity": 0.5, "secondary_emotions": []}
        try:
            results = classifier(text[:512], top_k=None)
            if isinstance(results, dict):
                results = [results]
            elif results and isinstance(results[0], list):
                results = results[0]
            sorted_emotions = sorted(results, key=lambda x: x["score"], reverse=True)
            primary = sorted_emotions[0]
            secondary = [e["label"] for e in sorted_emotions[1:3] if e["score"] > 0.1]
            return {
                "primary_emotion": primary["label"],
                "intensity": round(primary["score"], 3),
                "secondary_emotions": secondary,
            }
        except Exception as e:
            logger.warning("Emotion detection failed: %s", e)
            return {"primary_emotion": "neutral", "intensity": 0.5, "secondary_emotions": []}

    def embed(self, text: str) -> List[float]:
        """
        Generate sentence embedding using sentence-transformers.
        Returns list of floats. Falls back to empty list if unavailable.
        """
        model = self._load_sentence_model()
        if not model:
            return []
        try:
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.warning("Embedding failed: %s", e)
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently in one batch."""
        model = self._load_sentence_model()
        if not model:
            return [[] for _ in texts]
        try:
            embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.warning("Batch embedding failed: %s", e)
            return [[] for _ in texts]


# Singleton instance
ds_service = DSService()
