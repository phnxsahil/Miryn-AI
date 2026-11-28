"""Recent conversation turns appear in the reply prompt, in order.

Miryn's promise is continuity, but the prompt previously carried only
retrieved memories and stable facts, so the model could not see the message
before the current one. recent_turns renders the running thread after the
long-term sections, oldest first, with roles mapped to Them/You, and absent
or empty turns change nothing.
"""
from app.services.llm_service import LLMService
from app.services.recent_turns import _trim, RECENT_TURN_MAX_CHARS


def _format(turns):
    return LLMService()._format_context({"known_facts": [], "memories": [], "recent_turns": turns})


def test_turns_render_oldest_first_with_roles():
    out = _format([
        {"role": "user", "content": "My sister Priya is visiting next week"},
        {"role": "assistant", "content": "That sounds lovely. What are you two planning?"},
        {"role": "user", "content": "Maybe a day trip to the hills"},
    ])
    assert "Conversation so far" in out
    priya = out.index("Them: My sister Priya is visiting next week")
    reply = out.index("You: That sounds lovely.")
    hills = out.index("Them: Maybe a day trip to the hills")
    assert priya < reply < hills


def test_turns_follow_memories_section():
    out = LLMService()._format_context({
        "known_facts": [],
        "memories": [{"content": "User runs most mornings", "created_at": ""}],
        "recent_turns": [{"role": "user", "content": "I skipped my run today"}],
    })
    assert out.index("Relevant past conversations:") < out.index("Conversation so far")


def test_missing_or_empty_turns_leave_prompt_unchanged():
    base = LLMService()._format_context({"known_facts": [], "memories": []})
    assert "Conversation so far" not in base
    assert _format([]) == base


def test_non_user_role_maps_to_you():
    out = _format([{"role": "assistant", "content": "Welcome back"}])
    assert "You: Welcome back" in out


def test_trim_caps_long_turns():
    long_text = "x" * (RECENT_TURN_MAX_CHARS + 50)
    trimmed = _trim(long_text)
    assert len(trimmed) == RECENT_TURN_MAX_CHARS
    assert trimmed.endswith("…")
