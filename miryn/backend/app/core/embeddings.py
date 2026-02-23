import hashlib
import math
from typing import List
import logging
from app.config import settings


class EmbeddingService:
    """
    Embeddings with Gemini-backed vectors, with a deterministic hash fallback.
    """

    _INIT_FAILED = object()  # sentinel for caching failed init

    def __init__(self, dim: int = 384):
        """
        Initialize the EmbeddingService with a target embedding dimension and logger, and prepare the internal Gemini client placeholder.
        
        Parameters:
            dim (int): Desired length of embeddings produced or returned by this service (default 384). This value controls padding/truncation/compression behavior for embeddings.
        
        """
        self.dim = dim
        self.logger = logging.getLogger(__name__)
        self._gemini = None

    def _ensure_gemini(self):
        """
        Ensure and return a cached Gemini client configured with the API key, or None if unavailable.

        Attempts to import and configure the Google Gemini (google.generativeai) client using settings.GEMINI_API_KEY, caches the client on success, and logs a warning on failure.

        Returns:
            genai or None: The configured Gemini client module if initialized, otherwise `None`.
        """
        if self._gemini is self._INIT_FAILED:
            return None
        if self._gemini is not None:
            return self._gemini
        try:
            from google import genai

            key = settings.GEMINI_API_KEY
            if not key:
                self._gemini = self._INIT_FAILED
                return None
            self._gemini = genai.Client(api_key=key)
            return self._gemini
        except Exception as exc:
            self.logger.warning("Failed to init Gemini embeddings: %s", exc)
            self._gemini = self._INIT_FAILED
            return None

    def _hash_embed(self, text: str) -> List[float]:
        """
        Create a deterministic, unit-length embedding vector derived from `text`.
        
        For non-empty text this produces a repeatable pseudo-embedding based on a SHA-256 digest and normalizes it to length 1. For an empty string returns a basis vector of length `self.dim` with a 1.0 at index 0 (if `self.dim > 0`) and 0.0 elsewhere.
        
        Parameters:
            text (str): Input string to convert into an embedding.
        
        Returns:
            List[float]: A list of floats of length `self.dim` representing a normalized embedding vector.
        """
        if not text:
            basis = [0.0] * self.dim
            if self.dim:
                basis[0] = 1.0
            return basis
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [0.0] * self.dim
        for i in range(self.dim):
            b = digest[i % len(digest)]
            vec[i] = (b / 127.5) - 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _compress(self, vec: List[float]) -> List[float]:
        """
        Adjusts a numeric vector to the service's target embedding dimension.
        
        If the input vector length equals the target dimension, it is returned unchanged. If it is shorter, the vector is padded with zeros to reach the target length. If it is longer, the vector is reduced to the target length by averaging contiguous segments.
        
        Parameters:
            vec (List[float]): Input embedding vector.
        
        Returns:
            List[float]: A vector of length equal to the service's configured `dim`.
        """
        if len(vec) == self.dim:
            return vec
        if len(vec) < self.dim:
            padded = vec + [0.0] * (self.dim - len(vec))
            return padded[: self.dim]
        ratio = len(vec) / self.dim
        compressed = []
        for i in range(self.dim):
            start = int(i * ratio)
            end = int((i + 1) * ratio)
            end = max(end, start + 1)
            chunk = vec[start:end]
            compressed.append(sum(chunk) / len(chunk))
        return compressed

    def embed(self, text: str) -> List[float]:
        """
        Produce an embedding vector for the input text using Gemini when available, otherwise fall back to a deterministic hash-based embedding.

        Parameters:
            text (str): The input text to embed.

        Returns:
            List[float]: An embedding vector of length equal to the service's configured dimension.
        """
        client = self._ensure_gemini()
        if client:
            try:
                model = settings.GEMINI_EMBEDDING_MODEL
                candidates = [
                    f"models/{model}" if not model.startswith("models/") else model,
                    model,
                    "models/text-embedding-004",
                    "text-embedding-004",
                ]
                last_error = None
                for m in candidates:
                    try:
                        res = client.models.embed_content(
                            model=m,
                            contents=text,
                        )
                        embedding = res.embeddings[0].values if res.embeddings else None
                        if embedding:
                            return self._compress(list(embedding))
                    except Exception as exc:
                        last_error = exc
                        continue
                if last_error:
                    self.logger.warning("Gemini embedding failed, fallback to hash: %s", last_error)
                else:
                    self.logger.warning("Gemini embedding returned empty results for all candidates, fallback to hash")
            except Exception as exc:
                self.logger.warning("Gemini embedding error, fallback to hash: %s", exc)
        return self._hash_embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts.
        
        Parameters:
            texts (List[str]): Input strings to embed; order is preserved.
        
        Returns:
            embeddings (List[List[float]]): A list of embedding vectors corresponding to each input text.
        """
        return [self.embed(t) for t in texts]


embedding_service = EmbeddingService()
