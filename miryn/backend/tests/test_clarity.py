from app.services.clarity import compute_clarity


def test_low_signal_is_high_and_light():
    score, label = compute_clarity(0, 0, 2)
    assert score >= 99
    assert label == "Light"


def test_high_real_load_is_heavy():
    score, label = compute_clarity(8, 1.0, 0)
    assert score == 20
    assert label == "Heavy"


def test_boundaries_are_stable():
    assert compute_clarity(0, 1.0, 12)[1] == "Moderate"
    assert compute_clarity(5, 0.2, 0)[1] == "Moderate"
    assert compute_clarity(8, 0.6, 0)[1] == "Heavy"
