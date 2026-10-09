from app.services.fact_store import FactStore, bumped_importance


def test_repeated_mentions_raise_importance_without_saturating():
    value = 0.7
    checkpoints = []
    for count in range(1, 21):
        value = bumped_importance(value, 0.7)
        if count in (1, 5, 20):
            checkpoints.append(value)

    assert checkpoints[0] < checkpoints[1] < checkpoints[2] < 1.0


def test_higher_importance_gets_a_smaller_repeat_bump():
    assert bumped_importance(0.9, 0.9) - 0.9 < bumped_importance(0.5, 0.5) - 0.5


def test_manual_importance_can_remain_at_one():
    assert bumped_importance(1.0, 1.0) == 1.0


def test_list_returns_empty_when_encryption_is_unavailable(monkeypatch):
    monkeypatch.setattr("app.services.fact_store.encryption_available", lambda: False)

    assert FactStore()._list("user-1", 8) == []
