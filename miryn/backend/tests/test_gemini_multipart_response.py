"""Multi-part Gemini responses must not lose text in production parsing.

Production reads response.text (and chunk.text when streaming) from the pinned
google-genai SDK. These fixtures run a REST-shaped payload through the SDK's own
converter, so a future SDK bump that drops later text parts fails here.
Offline, no network.
"""
import pytest

from google.genai import models, types

REST_MULTI = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [
                    {"text": "I am so sorry about Dana."},
                    {"text": " I am right here with you.", "thoughtSignature": "opaque"},
                    {"thought": True, "text": "private reasoning"},
                ],
            },
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {"candidatesTokenCount": 12},
}


def _response(payload):
    converted = models._GenerateContentResponse_from_mldev(None, payload, {})
    return types.GenerateContentResponse(**converted)


def test_text_from_all_parts_is_joined_and_thought_parts_are_excluded():
    assert _response(REST_MULTI).text == "I am so sorry about Dana. I am right here with you."


def test_single_part_still_works():
    payload = {"candidates": [{"content": {"role": "model", "parts": [{"text": "Hi."}]}, "finishReason": "STOP"}]}
    assert _response(payload).text == "Hi."


def test_thought_only_response_yields_no_text_not_the_thought():
    payload = {"candidates": [{"content": {"role": "model", "parts": [{"thought": True, "text": "x"}]}, "finishReason": "STOP"}]}
    assert not _response(payload).text


def test_stream_chunks_each_expose_their_joined_text():
    chunks = [
        _response({"candidates": [{"content": {"role": "model", "parts": [{"text": "I am"}, {"text": " so"}]}}]}),
        _response({"candidates": [{"content": {"role": "model", "parts": [{"text": " sorry."}]}, "finishReason": "STOP"}]}),
    ]
    assert "".join(c.text for c in chunks) == "I am so sorry."
