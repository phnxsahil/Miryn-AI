"""Prompt-level memory truthfulness: offline string assertions on the built
system prompt. No model or database calls; runs in the default CI selection."""
import pytest

from app.services.llm_service import LLMService
from app.services.safety import SAFETY_POLICY


@pytest.mark.parametrize('preset', ['companion', 'mirror', 'coach', 'thinker', 'creative'])
def test_memory_truthfulness_rules_reach_every_persona(preset):
    """Memory-claim honesty is part of the safety floor, so every persona prompt
    must carry it: corrections supersede older memories in conversation, no
    false forget/update claims, and moods are not permanent labels."""
    prompt = LLMService()._build_system_prompt({'preset': preset})
    assert SAFETY_POLICY in prompt
    assert "user's own most recent statement" in prompt
    assert 'older conflicting memories are history' in prompt
    assert "third-party statements are not the" in prompt
    assert 'unless it actually was' in prompt
    assert 'do not promise durable remembering' in prompt
    assert 'passing feeling is a moment' in prompt
