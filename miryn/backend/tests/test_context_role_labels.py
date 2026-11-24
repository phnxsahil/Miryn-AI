"""Static checks for speaker labels in prompt context. They do NOT evaluate model behaviour."""
from app.services.llm_service import LLMService


def _fmt(memories):
    return LLMService()._format_context({"known_facts": [], "memories": memories})


def test_roles_are_labelled():
    out = _fmt([
        {"role": "user", "content": "I lost my job", "created_at": "t1"},
        {"role": "assistant", "content": "that sounds heavy", "created_at": "t2"},
    ])
    assert "[t1] User: I lost my job" in out
    assert "[t2] Miryn: that sounds heavy" in out


def test_missing_role_keeps_old_format():
    out = _fmt([{"content": "x", "created_at": "t"}, {"content": "y"}])
    assert "- [t] x" in out and "- y" in out and "User:" not in out
