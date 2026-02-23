import hashlib
import math
from typing import List
import logging
from app.config import settings


class EmbeddingService:
    """
    Embeddings with Gemini-backed vectors, with a deterministic hash fallback.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.logger = logging.getLogger(__name__)
        self._gemini = None

    def _ensure_gemini(self):
        if self._gemini is not None:
            return self._gemini
        try:
            import google.generativeai as genai

            key = settings.GEMINI_API_KEY
            if not key:
                return None
            genai.configure(api_key=key)
            self._gemini = genai
            return self._gemini
        except Exception as exc:
            self.logger.warning("Failed to init Gemini embeddings: %s", exc)
            return None

    def _hash_embed(self, text: str) -> List[float]:
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
        gemini = self._ensure_gemini()
        if gemini:
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
                        res = gemini.embed_content(
                            model=m,
                            content=text,
                            task_type="retrieval_document",
                        )
                        embedding = res.get("embedding") if isinstance(res, dict) else None
                        if embedding:
                            return self._compress(list(embedding))
                    except Exception as exc:
                        last_error = exc
                        continue
                if last_error:
                    self.logger.warning("Gemini embedding failed, fallback to hash: %s", last_error)
            except Exception as exc:
                self.logger.warning("Gemini embedding error, fallback to hash: %s", exc)
        return self._hash_embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


embedding_service = EmbeddingService()
