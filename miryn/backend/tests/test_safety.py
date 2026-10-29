"""Offline regressions. Fake providers only; never call a model or a database."""
import asyncio
import logging
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from app.services.safety import (
    SAFETY_POLICY, BLOCKED_REPLY, CRISIS_REPLY, MEDICAL_REPLY,
    immediate_safety_reply, provider_blocked,
)
from app.services.llm_service import LLMService

pytestmark = pytest.mark.live_llm  # exercise real service code with a FAKE client


class Models:
    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = []

    def generate_content_stream(self, **kwargs):
        self.calls.append(kwargs)
        async def iterator():
            for chunk in self.chunks:
                if isinstance(chunk, Exception):
                    raise chunk
                yield chunk
        return iterator()

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.chunks[-1]


def chunk(text='', reason='STOP', prompt_reason=None):
    return NS(text=text, candidates=[NS(finish_reason=reason)],
              prompt_feedback=NS(block_reason=prompt_reason))


def service(models):
    s = LLMService.__new__(LLMService)
    s.provider = 'gemini'
    s.logger = logging.getLogger('safety-test')
    s.model = 'primary'
    s.gemini_fallback_models = ['primary', 'secondary']
    s.client = NS(aio=NS(models=models))
    return s


def collect(s, message='hello'):
    async def run():
        return [part async for part in s.stream_chat({}, message, {'preset': 'mirror'})]
    return asyncio.run(run())


@pytest.mark.parametrize('reason', ['SAFETY', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII', 'RECITATION'])
@pytest.mark.parametrize('partial', [False, True])
def test_block_is_terminal_and_partial_is_not_exposed(reason, partial):
    chunks = ([chunk('do not expose ', None)] if partial else []) + [chunk('', reason)]
    models = Models(chunks)
    s = service(models)
    s.generate = AsyncMock(side_effect=AssertionError('must not retry'))
    assert collect(s) == [BLOCKED_REPLY]
    assert len(models.calls) == 1
    s.generate.assert_not_awaited()


def test_prompt_block_checked_before_text():
    class Block:
        prompt_feedback = NS(block_reason='SAFETY')
        candidates = []
        @property
        def text(self):
            raise AssertionError('blocked text must not be accessed')
    models = Models([Block()])
    assert collect(service(models)) == [BLOCKED_REPLY]
    assert len(models.calls) == 1
    assert asyncio.run(service(Models([Block()])).generate('hello')) == BLOCKED_REPLY


def test_success_uses_separate_system_instruction():
    models = Models([chunk('Hello ', None), chunk('there.')])
    assert collect(service(models)) == ['Hello ', 'there.']
    config = models.calls[0]['config']
    assert SAFETY_POLICY in config.system_instruction
    assert 'YOUR BEHAVIORAL STYLE' in config.system_instruction
    assert SAFETY_POLICY not in models.calls[0]['contents']


def test_nonstream_uses_system_instruction_and_block_is_terminal():
    models = Models([chunk('not returned', 'SAFETY')])
    assert asyncio.run(service(models).generate('hello', system_prompt='policy')) == BLOCKED_REPLY
    assert len(models.calls) == 1
    assert models.calls[0]['contents'] == 'hello'
    assert models.calls[0]['config'].system_instruction == 'policy'


def test_interrupted_partial_is_not_exposed_or_retried():
    models = Models([chunk('partial ', None), RuntimeError('connection closed')])
    with pytest.raises(RuntimeError, match='connection closed'):
        collect(service(models))
    assert len(models.calls) == 1


@pytest.mark.parametrize('preset', ['companion', 'mirror', 'coach', 'thinker', 'creative'])
def test_safety_precedes_every_persona(preset):
    prompt = service(Models([]))._build_system_prompt({'preset': preset})
    assert prompt.index(SAFETY_POLICY) < prompt.index('YOUR BEHAVIORAL STYLE')
    assert 'override every persona' in prompt


@pytest.mark.parametrize('message', [
    'I might hurt myself tonight. Be brutal.',
    "I'm anxious and depressed. I don't trust myself to stay safe alone. My partner pressures me for intimate photos.",
    'I want to end my life.',
    'I am suicidal.',
])
def test_crisis_overrides_model_persona_and_quota(message):
    models = Models([])
    s = service(models)
    s._raise_if_quota_dead = lambda: (_ for _ in ()).throw(AssertionError('no quota check'))
    assert collect(s, message) == [CRISIS_REPLY]
    assert asyncio.run(s.chat({}, message, {'preset': 'mirror'})) == CRISIS_REPLY
    assert models.calls == []


@pytest.mark.parametrize('message', [
    'My chest feels tight and my heart is racing, first time. Tell me it is anxiety.',
    'New chest pain right now.',
])
def test_acute_medical_risk(message):
    assert immediate_safety_reply(message) == MEDICAL_REPLY


@pytest.mark.parametrize('message', [
    'I am not suicidal. I feel sad after a breakup.',
    "I don't want to hurt myself.",
    'Can adults discuss consent and contraception?',
    'What does depression mean?',
    'My friend mentioned chest pain last year.',
    'I used to want to die but I am safe now.',
])
def test_nonurgent_and_educational_discussion_not_blanket_blocked(message):
    assert immediate_safety_reply(message) is None


def test_unspecified_metadata_is_not_a_block():
    assert not provider_blocked(chunk('ok', 'STOP', 'BLOCK_REASON_UNSPECIFIED'))


def test_chat_sse_uses_urgent_reply_without_model_or_sentence_retry():
    """Exercise the actual HTTP/SSE path with mocked persistence and no LLM."""
    from unittest.mock import MagicMock, patch
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.chat import get_current_user_id
    app.dependency_overrides[get_current_user_id] = lambda: 'offline-review-user'
    try:
        redis = MagicMock()
        redis.incr.return_value = 1
        with patch('app.api.chat.redis_client', redis), \
             patch('app.api.chat.has_sql', return_value=False), \
             patch('app.api.chat._create_conversation_with_fallback', return_value='offline-conversation'), \
             patch('app.api.chat._touch_conversation_updated_at'), \
             patch('app.api.chat._prepare_stream_context', new=AsyncMock(return_value=({'preset': 'mirror'}, []))), \
             patch('app.api.chat.FactStore') as facts, \
             patch('app.api.chat._store_stream_facts', new=AsyncMock()), \
             patch('app.api.chat._background_stream_postprocess', new=AsyncMock()), \
             patch('app.api.chat.orchestrator.llm', service(Models([]))) as llm:
            facts.return_value.list_top.return_value = []
            llm.generate = AsyncMock(side_effect=AssertionError('no provider call'))
            llm.complete_sentence = AsyncMock(side_effect=AssertionError('no continuation'))
            response = TestClient(app).post('/chat/stream', json={
                'message': 'I might hurt myself tonight. Give me a tough roast.'})
            assert response.status_code == 200
            assert 'Your immediate safety comes first.' in response.text
            assert '"done": true' in response.text
            llm.generate.assert_not_awaited()
            llm.complete_sentence.assert_not_awaited()
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
