"""
Unit tests for DSService — covers public methods and fallback paths
when ML models are unavailable.
"""
import sys
import types
import pytest

from app.services.ds_service import DSService


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def svc():
    """Fresh DSService instance for each test."""
    return DSService()


def _make_spacy_stub(entities):
    """
    Create a minimal spaCy-like callable that produces a Doc with predefined entities.
    
    The returned callable ignores input text and, when invoked, returns an object exposing
    an `ents` attribute: a list of simple entity objects each with `text` and `label_`.
    
    Parameters:
        entities (Iterable[tuple[str, str]]): Sequence of (text, label) pairs to populate `ents`.
    
    Returns:
        callable: A spaCy-like callable that returns a Doc-like object with the configured entities.
    """

    class _Ent:
        def __init__(self, text, label_):
            """
            Initialize an entity object with its surface text and spaCy-style label.
            
            Parameters:
                text (str): The entity text as it appears in the source.
                label_ (str): The spaCy-style entity label (for example, 'PERSON' or 'ORG').
            """
            self.text = text
            self.label_ = label_

    class _Doc:
        def __init__(self):
            """
            Initialize the document and populate its `ents` attribute from the surrounding `entities` sequence.
            
            Each item in the `entities` sequence is expected to be a (text, label) pair; an `_Ent` instance is created for each pair and stored in `self.ents`.
            """
            self.ents = [_Ent(t, l) for t, l in entities]

    class _NLP:
        def __call__(self, text, **kwargs):
            """
            Produce a stub _Doc object representing a processed document; input `text` and `kwargs` are ignored.
            
            Parameters:
                text (str): Input text (ignored).
                **kwargs: Additional keyword arguments (ignored).
            
            Returns:
                _Doc: A newly constructed `_Doc` instance (contains no entities).
            """
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
            """
            Simulate a failing model loader used in tests.
            
            Raises:
                OSError: Always raised with message "model not found" after incrementing the test call counter.
            """
            nonlocal call_count
            call_count += 1
            raise OSError("model not found")

        import types
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
            """
            Increment a sentinel call counter and always raise a RuntimeError indicating the model is unavailable.
            
            This helper increments the nonlocal `call_count` each time it is invoked and then raises RuntimeError("no model").
            
            Raises:
                RuntimeError: Always raised with the message "no model".
            """
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
                """
                Constructor stub that simulates a model initialization failure for tests.
                
                Increments the enclosing `call_count` nonlocal counter and then raises a `RuntimeError`
                with the message "no model".
                
                Raises:
                    RuntimeError: Always raised to simulate a failing model constructor.
                """
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
                """
                Callable that always raises a RuntimeError.
                
                Raises:
                    RuntimeError: Always raised with the message "broken".
                """
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
            """
            Fake emotion classifier that returns a fixed list of labeled scores.
            
            Parameters:
                text (str): Input text (ignored by this fake classifier).
                top_k (int | None): Maximum number of top labels to return (ignored).
            
            Returns:
                list[dict]: A list of dictionaries each containing:
                    - "label" (str): Emotion label.
                    - "score" (float): Confidence score for the label.
            """
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
            """
            Callable that always raises a RuntimeError when invoked.
            
            Raises:
                RuntimeError: Always raised with the message "fail".
            """
            raise RuntimeError("fail")

        svc._emotion_classifier = _bad_classifier
        result = svc.detect_emotions("anything")
        assert result["primary_emotion"] == "neutral"


# ---------------------------------------------------------------------------
# embed / embed_batch
# ---------------------------------------------------------------------------

class TestEmbed:
    def _make_sentence_model(self):
        """
        Create a fake sentence embedding model for tests.
        
        The returned object exposes an `encode(texts, normalize_embeddings=True, batch_size=32)` method:
        - If `texts` is a `str`, returns a 1-D numpy array [0.1, 0.2, 0.3].
        - If `texts` is an iterable of strings, returns a 2-D numpy array with one [0.1, 0.2, 0.3] row per input.
        
        Returns:
            _FakeModel: A test double that mimics a sentence-transformers model's `encode` output as numpy arrays.
        """
        import numpy as np

        class _FakeModel:
            def encode(self, texts, normalize_embeddings=True, batch_size=32):
                """
                Return deterministic dummy embedding vectors for testing.
                
                Parameters:
                    texts (str or Sequence[str]): Input text or list of texts to encode.
                    normalize_embeddings (bool): Ignored; present to keep API compatibility.
                    batch_size (int): Ignored; present to keep API compatibility.
                
                Returns:
                    numpy.ndarray: If `texts` is a string, a 1-D array of floats representing a single embedding.
                                   If `texts` is a sequence, a 2-D array where each row is the same embedding for each input text.
                """
                if isinstance(texts, str):
                    return np.array([0.1, 0.2, 0.3])
                return np.array([[0.1, 0.2, 0.3] for _ in texts])

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
                """
                Placeholder encoder that always fails.
                
                Raises:
                    RuntimeError: Always raised with message "fail".
                """
                raise RuntimeError("fail")

        svc._sentence_model = _BrokenModel()
        assert svc.embed("hello") == []
