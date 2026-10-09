from contextlib import nullcontext
from unittest.mock import MagicMock

import app.services.identity.emotions as emotions_module
from app.services.identity.emotions import EmotionStore


def test_replace_skips_neutral_emotions(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(emotions_module, "has_sql", lambda: True)
    monkeypatch.setattr(emotions_module, "get_sql_session", lambda: nullcontext(session))

    EmotionStore().replace(
        "user-1",
        "identity-1",
        [
            {"primary_emotion": "neutral", "intensity": 0.5},
            {"primary_emotion": "stressed", "intensity": 0.8},
        ],
    )

    inserts = [
        call
        for call in session.execute.call_args_list
        if "INSERT INTO identity_emotions" in str(call.args[0])
    ]
    assert len(inserts) == 1
    assert inserts[0].args[1]["primary_emotion"] == "stressed"
