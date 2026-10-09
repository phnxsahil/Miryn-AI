"""
Chat smoke tests + edge cases.
Run against the live demo server (DATABASE_URL=sqlite:///./miryn_demo.db).

Usage:
    pytest tests/test_chat_smoke.py -v -s --timeout=60

ponytail: no mocking — these hit the real endpoint so we catch real wiring bugs.
ceiling: requires server running on 127.0.0.1:8000 with riya_v3@miryn.demo seeded.
"""
import json
import os
import pytest
import httpx

BASE = os.getenv("SMOKE_BASE", "http://127.0.0.1:8000")
DEMO_EMAIL = "riya_v3@miryn.demo"
DEMO_PASSWORD = "MirynDemo!2026"

pytestmark = pytest.mark.live
if os.getenv("SMOKE_LIVE") != "1":
    pytest.skip(
        "live smoke tests hit a real server and real LLM; run with SMOKE_LIVE=1",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def token():
    """Login once, reuse token across tests in this module."""
    r = httpx.post(
        f"{BASE}/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _stream_chunks(response: httpx.Response) -> tuple[list[str], str | None, str | None]:
    """Parse SSE stream. Returns (chunks, conversation_id, error)."""
    chunks, conv_id, error = [], None, None
    for line in response.text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = json.loads(line[6:])
        if "chunk" in payload:
            chunks.append(payload["chunk"])
        elif "done" in payload:
            conv_id = payload.get("conversation_id")
        elif "error" in payload:
            error = payload["error"]
    return chunks, conv_id, error


# ---------------------------------------------------------------------------
# smoke - happy path
# ---------------------------------------------------------------------------

@pytest.mark.timeout(60)
def test_chat_stream_happy_path(token):
    """Basic: send a message, get a streamed reply."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "Say hello in exactly one sentence."},
        timeout=60,
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
    chunks, conv_id, error = _stream_chunks(r)
    assert not error, f"Stream returned error: {error}"
    assert chunks, "No chunks received - LLM returned nothing"
    assert conv_id, "No conversation_id in done event"
    full = "".join(chunks).strip()
    assert len(full) > 5, f"Response suspiciously short: {full!r}"


@pytest.mark.timeout(60)
def test_chat_stream_conversation_continuity(token):
    """Second message in same conversation - should return same conversation_id."""
    # first turn
    r1 = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "My name is Alex."},
        timeout=60,
    )
    assert r1.status_code == 200
    _, conv_id, _ = _stream_chunks(r1)
    assert conv_id

    # second turn in same conversation
    r2 = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "What is my name?", "conversation_id": conv_id},
        timeout=60,
    )
    assert r2.status_code == 200
    chunks2, conv_id2, error2 = _stream_chunks(r2)
    assert not error2
    assert conv_id2 == conv_id, "Conversation ID changed between turns"
    assert chunks2


# ---------------------------------------------------------------------------
# edge cases - auth
# ---------------------------------------------------------------------------

def test_stream_requires_auth():
    """No token -> 401."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        json={"message": "Hello"},
        timeout=10,
    )
    assert r.status_code == 401


def test_stream_bad_token():
    """Garbage token -> 401."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers={"Authorization": "Bearer not.a.valid.token"},
        json={"message": "Hello"},
        timeout=10,
    )
    assert r.status_code == 401


def test_stream_tampered_token(token):
    """Valid header + tampered payload -> 401."""
    parts = token.split(".")
    if len(parts) == 3:
        tampered = parts[0] + ".dGFtcGVyZWQ." + parts[2]  # replaced payload
        r = httpx.post(
            f"{BASE}/chat/stream",
            headers={"Authorization": f"Bearer {tampered}"},
            json={"message": "Hello"},
            timeout=10,
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# edge cases - input validation
# ---------------------------------------------------------------------------

def test_stream_empty_message(token):
    """Empty string message - server should 422 or error event, not 500."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": ""},
        timeout=30,
    )
    assert r.status_code in (200, 422), f"Unexpected status for empty message: {r.status_code}"


def test_stream_whitespace_only_message(token):
    """Whitespace-only message - should not crash."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "   "},
        timeout=30,
    )
    assert r.status_code in (200, 422)


def test_stream_very_long_message(token):
    """8 KB message - should not crash the server."""
    long_msg = "a" * 8192
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": long_msg},
        timeout=60,
    )
    assert r.status_code in (200, 413, 422), f"Long message gave unexpected {r.status_code}"


def test_stream_missing_message_field(token):
    """No 'message' key -> 422."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"not_message": "hello"},
        timeout=10,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# edge cases - conversation ownership
# ---------------------------------------------------------------------------

def test_stream_wrong_conversation_owner(token):
    """conversation_id that belongs to nobody -> 404."""
    fake_conv_id = "00000000-0000-0000-0000-000000000001"
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "Hello", "conversation_id": fake_conv_id},
        timeout=10,
    )
    assert r.status_code in (403, 404), f"Expected 403/404 for unknown conv, got {r.status_code}"


# ---------------------------------------------------------------------------
# edge cases - SSE format
# ---------------------------------------------------------------------------

@pytest.mark.timeout(60)
def test_stream_sse_format(token):
    """Every non-empty data line must be valid JSON."""
    r = httpx.post(
        f"{BASE}/chat/stream",
        headers=_auth(token),
        json={"message": "Count to three."},
        timeout=60,
    )
    assert r.status_code == 200
    bad_lines = []
    for line in r.text.splitlines():
        if line.startswith("data: "):
            try:
                json.loads(line[6:])
            except json.JSONDecodeError:
                bad_lines.append(line)
    assert not bad_lines, f"Malformed SSE lines: {bad_lines}"


# ---------------------------------------------------------------------------
# health baseline
# ---------------------------------------------------------------------------

def test_health():
    """Server must be up and report all checks healthy."""
    r = httpx.get(f"{BASE}/health", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
