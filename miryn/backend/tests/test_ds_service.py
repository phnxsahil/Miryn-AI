"""
Unit tests for DSService — covers public methods and fallback paths
when ML models are unavailable.
"""
import sys
import types
import pytest

from app.services.ds_service import DSService


class _FloatArray(list):
    """Minimal numpy-array substitute: supports .tolist()."""
    def tolist(self):
        return list(self)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def svc():
    """Fresh DSService instance for each test."""
    return DSService()


def _make_spacy_stub(entities):
    """Return a minimal spaCy-like nlp callable that returns fixed entities."""

    class _Ent:
        def __init__(self, text, label_):
            self.text = text
            self.label_ = label_

    class _Doc:
        def __init__(self):
            self.ents = [_Ent(t, l) for t, l in entities]

    class _NLP:
        def __call__(self, text, **kwargs):
            return _Doc()

    return _NLP()


# ---------------------------------------------------------------------------
# _load_spacy failure sentinel
# ---------------------------------------------------------------------------

class TestLoadSpacyFailureSentinel:
    def test_returns_none_on_import_error(self, svc, monkeypatch):
        monkeypatch.setitem(sys.modules, "spacy", None)
        result = svc._load_spacy()
        assert result is None
        assert svc._nlp_failed is True

    def test_does_not_retry_after_failure(self, svc, monkeypatch):
        call_count = 0

        def _bad_load(name):
            nonlocal call_count
            call_count += 1
            raise OSError("model not found")

        fake_spacy = types.ModuleType("spacy")
        fake_spacy.load = _bad_load
        monkeypatch.setitem(sys.modules, "spacy", fake_spacy)

        svc._load_spacy()
        svc._load_spacy()  # second call — must NOT call load again
        assert call_count == 1
        assert svc._nlp_failed is True


# ---------------------------------------------------------------------------
# _load_emotion_model failure sentinel
# ---------------------------------------------------------------------------

class TestLoadEmotionModelFailureSentinel:
    def test_returns_none_on_import_error(self, svc, monkeypatch):
        monkeypatch.setitem(sys.modules, "transformers", None)
        result = svc._load_emotion_model()
        assert result is None
        assert svc._emotion_failed is True

    def test_does_not_retry_after_failure(self, svc, monkeypatch):
        call_count = 0

        def _bad_pipeline(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("no model")

        fake_transformers = types.ModuleType("transformers")
        fake_transformers.pipeline = _bad_pipeline
        monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

        svc._load_emotion_model()
        svc._load_emotion_model()
        assert call_count == 1
        assert svc._emotion_failed is True


# ---------------------------------------------------------------------------
# _load_sentence_model failure sentinel
# ---------------------------------------------------------------------------

class TestLoadSentenceModelFailureSentinel:
    def test_returns_none_on_import_error(self, svc, monkeypatch):
        monkeypatch.setitem(sys.modules, "sentence_transformers", None)
        result = svc._load_sentence_model()
        assert result is None
        assert svc._sentence_failed is True

    def test_does_not_retry_after_failure(self, svc, monkeypatch):
        call_count = 0

        class _BadST:
            def __init__(self, *a, **kw):
                nonlocal call_count
                call_count += 1
                raise RuntimeError("no model")

        fake_st = types.ModuleType("sentence_transformers")
        fake_st.SentenceTransformer = _BadST
        monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

        svc._load_sentence_model()
        svc._load_sentence_model()
        assert call_count == 1
        assert svc._sentence_failed is True


# ---------------------------------------------------------------------------
# warmup_models
# ---------------------------------------------------------------------------

class TestWarmupModels:
    def test_calls_all_model_loaders(self, svc, monkeypatch):
        calls = []

        monkeypatch.setattr(svc, "_load_spacy", lambda: calls.append("spacy"))
        monkeypatch.setattr(svc, "_load_emotion_model", lambda: calls.append("emotion"))
        monkeypatch.setattr(svc, "_load_sentence_model", lambda: calls.append("sentence"))

        svc.warmup_models()

        assert calls == ["spacy", "emotion", "sentence"]


# ---------------------------------------------------------------------------
# extract_entities
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_returns_empty_list_when_spacy_unavailable(self, svc, monkeypatch):
        svc._nlp_failed = True
        assert svc.extract_entities("Hello world") == []

    def test_returns_filtered_entities(self, svc):
        svc._nlp = _make_spacy_stub([
            ("Alice", "PERSON"),
            ("Google", "ORG"),
            ("the", "DET"),  # should be filtered out
        ])
        result = svc.extract_entities("Alice works at Google today")
        labels = {e["label"] for e in result}
        assert "PERSON" in labels
        assert "ORG" in labels
        assert "DET" not in labels

    def test_returns_empty_list_on_nlp_exception(self, svc):
        class _BrokenNLP:
            def __call__(self, *a, **kw):
                raise RuntimeError("broken")

        svc._nlp = _BrokenNLP()
        assert svc.extract_entities("some text") == []


# ---------------------------------------------------------------------------
# detect_emotions
# ---------------------------------------------------------------------------

class TestDetectEmotions:
    def test_returns_neutral_when_model_unavailable(self, svc):
        svc._emotion_failed = True
        result = svc.detect_emotions("I feel fine")
        assert result["primary_emotion"] == "neutral"
        assert result["intensity"] == 0.5
        assert result["secondary_emotions"] == []

    def test_returns_primary_emotion_from_classifier(self, svc):
        def _fake_classifier(text, top_k=None):
            return [
                {"label": "joy", "score": 0.9},
                {"label": "surprise", "score": 0.2},
                {"label": "anger", "score": 0.05},
            ]

        svc._emotion_classifier = _fake_classifier
        result = svc.detect_emotions("This is wonderful!")
        assert result["primary_emotion"] == "joy"
        assert result["intensity"] == pytest.approx(0.9, abs=0.001)
        assert "surprise" in result["secondary_emotions"]

    def test_returns_neutral_on_classifier_exception(self, svc):
        def _bad_classifier(*a, **kw):
            raise RuntimeError("fail")

        svc._emotion_classifier = _bad_classifier
        result = svc.detect_emotions("anything")
        assert result["primary_emotion"] == "neutral"


# ---------------------------------------------------------------------------
# embed / embed_batch
# ---------------------------------------------------------------------------

class TestEmbed:
    def _make_sentence_model(self):
        class _FakeModel:
            def encode(self, texts, normalize_embeddings=True, batch_size=32):
                if isinstance(texts, str):
                    return _FloatArray([0.1, 0.2, 0.3])
                return [_FloatArray([0.1, 0.2, 0.3]) for _ in texts]

        return _FakeModel()

    def test_returns_empty_list_when_model_unavailable(self, svc):
        svc._sentence_failed = True
        assert svc.embed("hello") == []

    def test_returns_float_list(self, svc):
        svc._sentence_model = self._make_sentence_model()
        result = svc.embed("hello world")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_embed_batch_returns_empty_lists_when_unavailable(self, svc):
        svc._sentence_failed = True
        result = svc.embed_batch(["a", "b", "c"])
        assert result == [[], [], []]

    def test_embed_batch_returns_correct_count(self, svc):
        svc._sentence_model = self._make_sentence_model()
        texts = ["one", "two", "three"]
        result = svc.embed_batch(texts)
        assert len(result) == len(texts)
        for emb in result:
            assert isinstance(emb, list)

    def test_embed_returns_empty_on_exception(self, svc):
        class _BrokenModel:
            def encode(self, *a, **kw):
                raise RuntimeError("fail")

        svc._sentence_model = _BrokenModel()
        assert svc.embed("hello") == []
