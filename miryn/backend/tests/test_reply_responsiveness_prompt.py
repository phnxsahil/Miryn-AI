"""Static prompt checks. These do NOT evaluate model behaviour; they only guard the prompt text."""
import re

from app.services import llm_service
from app.services.llm_service import BANNED_PHRASES, DEFAULT_VOICE, PRESET_VOICES


def _prompt(preset="companion"):
    svc = llm_service.LLMService.__new__(llm_service.LLMService)
    svc._presets_cache = None
    return svc._build_system_prompt({"preset": preset, "traits": {}, "values": {}})


def test_companion_and_default_have_no_fixed_sentence_cap():
    for voice in (PRESET_VOICES["companion"], DEFAULT_VOICE):
        assert not re.search(r"\d+ to \d+ (short )?sentences", voice["length"])


def test_natural_comfort_phrases_are_not_banned():
    banned = " ".join(BANNED_PHRASES).lower()
    for phrase in ("i hear you", "must be so hard", "holding space"):
        assert phrase not in banned


def test_hurting_guidance_is_context_aware_and_keeps_safety_policy():
    p = _prompt()
    assert "WHEN SOMEONE IS HURTING" in p
    assert "negated" in p
    assert "SAFETY AND TRUTHFULNESS" in p
    assert "monitoring" in p


def test_unset_preset_falls_back_to_companion_persona():
    # identities are created with preset=None until the user visits Personalize
    p = _prompt(None)
    assert "warm, mature partner" in p
    assert "Match the moment" in p


def test_unknown_timezone_does_not_claim_a_time_of_day():
    line = llm_service._local_time_line({})
    assert "unknown" in line and "UTC" not in line
    assert "local time is" in llm_service._local_time_line({"timezone": "Asia/Kolkata"})


def test_open_loops_are_newest_first_and_marked_possibly_stale():
    loops = [{"topic": f"old{i}", "last_mentioned": f"2026-11-0{i}"} for i in range(1, 7)]
    loops.append({"topic": "newest", "last_mentioned": "2026-11-24"})
    p = _prompt()
    svc = llm_service.LLMService.__new__(llm_service.LLMService)
    svc._presets_cache = None
    p = svc._build_system_prompt({"preset": "companion", "traits": {}, "values": {}, "open_loops": loops})
    assert "newest" in p and "old1" not in p
    assert "may be stale" in p


def test_reflection_loop_extraction_ignores_assistant_only_content():
    import inspect
    from app.services import reflection_engine
    src = inspect.getsource(reflection_engine)
    assert "Base every entry on what the user said" in src and "explicitly accepts, adopts" in src


def test_hurting_guidance_forbids_invented_details():
    p = _prompt()
    assert "Do not invent biographical or scenario facts" in p
    assert "clearly label it as a guess" in p
