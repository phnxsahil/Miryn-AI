"""Static checks for timezone fallback and open-loop ordering. They do NOT evaluate model behaviour."""
from app.services import llm_service


def test_unknown_timezone_does_not_claim_a_time_of_day():
    line = llm_service._local_time_line({})
    assert "unknown" in line and "UTC" not in line
    assert "local time is" in llm_service._local_time_line({"timezone": "Asia/Kolkata"})


def test_open_loops_are_newest_first():
    loops = [{"topic": f"old{i}", "last_mentioned": f"2026-11-0{i}"} for i in range(1, 7)]
    loops.append({"topic": "newest", "last_mentioned": "2026-11-24"})
    svc = llm_service.LLMService.__new__(llm_service.LLMService)
    svc._presets_cache = None
    p = svc._build_system_prompt({"preset": "companion", "traits": {}, "values": {}, "open_loops": loops})
    assert "newest" in p and "old1" not in p
