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
        """
        Initialize DSService instance state.
        
        Sets up cached model handles and corresponding failure flags used for lazy loading:
        - _nlp: spaCy language model handle or None
        - _nlp_failed: True if spaCy loading previously failed
        - _emotion_classifier: emotion classification pipeline or None
        - _emotion_failed: True if emotion model loading previously failed
        - _sentence_model: sentence-transformers model or None
        - _sentence_failed: True if sentence model loading previously failed
        """
        self._nlp = None
        self._nlp_failed = False
        self._emotion_classifier = None
        self._emotion_failed = False
        self._sentence_model = None
        self._sentence_failed = False

    def _load_spacy(self):
        """
        Load and cache the spaCy English model for later use.
        
        Loads the `en_core_web_sm` spaCy model and stores it on the instance for reuse.
        On successful load the cached model is returned. If a previous load attempt failed
        or a current load fails, the method marks the loader as failed and returns `None`.
        
        Returns:
            The loaded spaCy language model instance, or `None` if loading failed.
        """
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
        """
        Lazily loads and caches a HuggingFace text-classification pipeline for emotion detection.
        
        On success caches the pipeline in `self._emotion_classifier` and returns it. If a previous load attempt failed returns `None`; on a new failure sets `self._emotion_failed = True` and returns `None`.
        
        Returns:
            The loaded transformers pipeline for emotion classification, or `None` if unavailable.
        """
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
        """
        Load and cache the SentenceTransformer model "all-MiniLM-L6-v2" for producing embeddings.
        
        If the model is already loaded this returns the cached instance. If a prior load attempt failed, this returns None and does not retry. On successful load the model instance is cached on the service for future calls.
        
        Returns:
            SentenceTransformer or None: The loaded SentenceTransformer instance, or `None` if the model is unavailable.
        """
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
        Extract named entities from the first 1000 characters of the provided text and return only selected entity types.
        
        Returns:
            List[Dict]: A list of dictionaries each containing "text" (entity string) and "label" (spaCy entity label). Returns an empty list if spaCy is unavailable or extraction fails.
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
        Identify the primary and up to two secondary emotions expressed in the given text and report the primary emotion's intensity.
        
        The function analyzes (at most) the first 512 characters of the input and returns a neutral fallback if the emotion model is unavailable or detection fails.
        
        Returns:
            dict: A mapping with keys:
                - "primary_emotion" (str): Label of the highest-scoring emotion.
                - "intensity" (float): The top emotion's score rounded to 3 decimals.
                - "secondary_emotions" (List[str]): Up to two additional emotion labels whose score is greater than 0.1.
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
        Compute a normalized sentence embedding for the given text.
        
        Returns:
            List[float]: Normalized embedding vector for the input text; returns an empty list if the sentence-transformers model is unavailable or encoding fails.
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
        """
        Encode a sequence of texts into normalized sentence embeddings using a single batch.
        
        Parameters:
            texts (List[str]): The input strings to encode.
        
        Returns:
            List[List[float]]: A list of embedding vectors (one per input). If the sentence-transformers model is unavailable or encoding fails, returns a list of empty lists with the same length as `texts`.
        """
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
