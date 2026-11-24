"""list_top must return the same public shape on every path, including when the query has no Latin tokens."""
import pytest

from app.services.fact_store import FactStore


def _rows():
    return [{
        "id": "1", "fact": "Works at Acme", "content": "Works at Acme", "category": "work",
        "importance": 0.9, "importance_score": 0.9, "created_at": None, "last_seen_at": None,
        "extractor": "heuristic", "corrects": None,
    }]


@pytest.mark.parametrize("query", [None, "hi", "work at acme", "\u0906\u091c \u092e\u0928 \u0928\u0939\u0940\u0902 \u0932\u0917 \u0930\u0939\u093e", "\U0001F614"])
def test_internal_keys_never_leak(query):
    fs = FactStore()
    fs._list = lambda user_id, limit, minimum=None: _rows()
    out = fs.list_top("u", 8, query)
    assert out and not ({"category", "extractor", "corrects"} & set(out[0]))


def test_markers_kept_only_when_requested():
    fs = FactStore()
    fs._list = lambda user_id, limit, minimum=None: _rows()
    out = fs.list_top("u", 8, "\u0906\u091c", include_markers=True)
    assert "corrects" in out[0] and "category" not in out[0]
