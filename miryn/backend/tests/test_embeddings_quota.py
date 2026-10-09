from types import SimpleNamespace

from app.core.embeddings import EmbeddingService
from app.services.llm_service import LLMService


def test_embeddings_skip_gemini_when_quota_is_dead(monkeypatch) -> None:
    class FailingModels:
        def embed_content(self, **_kwargs):
            raise AssertionError("Gemini must not be called while quota is dead")

    service = EmbeddingService()
    service._gemini = SimpleNamespace(models=FailingModels())
    monkeypatch.setattr(LLMService, "quota_dead", classmethod(lambda _cls: True))

    vector, source = service.embed_with_source("hello")

    assert len(vector) == service.dim
    assert source == "hash_fallback"


def test_embeddings_use_gemini_when_quota_is_available(monkeypatch) -> None:
    calls = []

    class WorkingModels:
        def embed_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.25] * 384)])

    service = EmbeddingService()
    service._gemini = SimpleNamespace(models=WorkingModels())
    monkeypatch.setattr(LLMService, "quota_dead", classmethod(lambda _cls: False))

    vector, source = service.embed_with_source("hello")

    assert calls
    assert len(vector) == service.dim
    assert source == "gemini"
