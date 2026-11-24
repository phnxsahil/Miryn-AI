"""Sentence-end detection must recognise real punctuation, not mojibake."""
import pytest

from app.services.llm_service import _has_sentence_ending


@pytest.mark.parametrize(
    "text",
    [
        "That is hard.",
        "That is hard...",
        "That is hard\u2026",
        "She said \u201cit is over.\u201d",
        "He called it \u2018done.\u2019",
        "Is that right?)",
        "\u0928\u092e\u0938\u094d\u0924\u0947\u0964",
        "Kya hua yaar\u0964",
        "\u00bfEn serio?",
    ],
)
def test_complete_replies_are_recognised(text):
    assert _has_sentence_ending(text)


@pytest.mark.parametrize("text", ["That is hard", "I think you should tell her and", "tired \u00e2", "half a thought,", "price is 5"])
def test_incomplete_replies_are_not_recognised(text):
    assert not _has_sentence_ending(text)


def test_chat_continuation_separator_set_uses_real_ellipsis():
    import app.api.chat as chat
    src = open(chat.__file__, encoding="utf-8").read()
    assert "\u00e2" not in src.split("completion.startswith(tuple(")[1].split("))")[0]
