"""Static checks for timezone fallback, open-loop ordering and extractor wording. They do NOT evaluate model behaviour."""
from app.services import llm_service


def _svc():
    svc = llm_service.LLMService.__new__(llm_service.LLMService)
    svc._presets_cache = None
    return svc


def test_unknown_timezone_does_not_claim_a_time_of_day():
    line = llm_service._local_time_line({})
    assert "unknown" in line and "UTC" not in line
    assert "local time is" in llm_service._local_time_line({"timezone": "Asia/Kolkata"})


def test_open_loops_are_newest_first_and_marked_possibly_stale():
    loops = [{"topic": f"old{i}", "last_mentioned": f"2026-11-0{i}"} for i in range(1, 7)]
    loops.append({"topic": "newest", "last_mentioned": "2026-11-24"})
    p = _svc()._build_system_prompt({"preset": "companion", "traits": {}, "values": {}, "open_loops": loops})
    assert "newest" in p and "old1" not in p
    assert "may be stale" in p


def test_reflection_prompt_wording_ignores_assistant_only_content():
    import inspect
    from app.services import reflection_engine
    src = inspect.getsource(reflection_engine)
    assert "Base every entry on what the user said" in src and "explicitly accepts, adopts" in src
