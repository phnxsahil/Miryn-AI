import asyncio

from app.services.llm_service import LLMService
from app.services.reflection_engine import ReflectionEngine


class _StubLLM:
    def __init__(self, response):
        self.response = response

    async def generate(self, prompt, max_tokens=0):
        self.prompt = prompt
        return self.response

    parse_json_response = staticmethod(LLMService.parse_json_response)


def _extract(response):
    llm = _StubLLM(response)
    engine = ReflectionEngine.__new__(ReflectionEngine)
    engine.llm = llm
    return asyncio.run(engine._extract_all({"user": "hi", "assistant": "hello"})), llm


def test_open_loops_come_only_from_open_loops_field():
    (entities, emotions, topics, loops), llm = _extract(
        '{"entities": [], "emotions": {"primary_emotion": "calm", "intensity": 0.4},'
        ' "topics": ["dog food", "fintech"],'
        ' "open_loops": [{"topic": "Decide on Pune move", "importance": 2}]}'
    )
    assert topics == ["dog food", "fintech"]
    assert loops == [{"topic": "Decide on Pune move", "importance": 2}]
    assert "open_loops" in llm.prompt


def test_topics_without_open_loops_field_write_no_loops():
    (_, _, topics, loops), _ = _extract('{"topics": ["dog food"], "emotions": {}}')
    assert topics == ["dog food"]
    assert loops == []


def test_unparseable_response_returns_no_loops():
    (_, _, topics, loops), _ = _extract("not json")
    assert topics == [] and loops == []
