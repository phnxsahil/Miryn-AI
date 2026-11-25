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


def _prompt(preset):
    ident = {"traits": {}, "values": {}, "beliefs": [], "open_loops": [], "timezone": "Asia/Kolkata"}
    if preset != "__missing__":
        ident["preset"] = preset
    return _svc()._build_system_prompt(ident)


def test_empty_string_preset_uses_companion_voice():
    p = _prompt("")
    assert PRESET_VOICES["companion"]["length"] in p
    assert "2 to 4 sentences." not in p


def test_none_missing_and_empty_match_explicit_companion():
    import re
    def norm(t):
        return re.sub(r"(?m)^.*(?:local time|It is now|NOW).*$", "", t)
    want = norm(_prompt("companion"))
    for preset in (None, "", "__missing__"):
        assert norm(_prompt(preset)) == want


def test_safety_policy_present_verbatim_for_every_preset_path():
    from app.services.safety import SAFETY_POLICY
    for preset in (None, "", "__missing__", "companion", "coach"):
        assert SAFETY_POLICY in _prompt(preset)
