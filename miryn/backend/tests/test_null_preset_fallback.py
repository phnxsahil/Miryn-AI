"""An identity whose preset is None (new account, no style chosen) must get the companion voice."""
import os
os.environ.setdefault("SECRET_KEY", "x")
from app.services.llm_service import LLMService, PRESET_VOICES


def _svc():
    s = LLMService.__new__(LLMService)
    s._presets_cache = None
    return s


def test_none_preset_uses_companion_voice():
    p = _svc()._build_system_prompt({"traits": {}, "values": {}, "beliefs": [], "open_loops": [], "preset": None})
    assert PRESET_VOICES["companion"]["length"] in p
    assert "2 to 4 sentences." not in p


def test_missing_preset_uses_companion_voice():
    p = _svc()._build_system_prompt({"traits": {}, "values": {}, "beliefs": [], "open_loops": []})
    assert PRESET_VOICES["companion"]["length"] in p


def test_explicit_preset_unchanged():
    p = _svc()._build_system_prompt({"traits": {}, "values": {}, "beliefs": [], "open_loops": [], "preset": "coach"})
    assert PRESET_VOICES["coach"]["length"] in p
