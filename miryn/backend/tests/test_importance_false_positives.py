"""Adversarial false-positive regressions for the heuristic memory extractor.

These cases come from the independent review of PR #35 (probes run against
base and branch). Every "junk" case must NOT be stored: each one previously
produced a NEW false positive introduced by the round-2 heuristic broadening.
The "keep" cases pin the genuine recall wins so the narrowing does not revert
them, and the "drop" cases pin the question/probe guards.
"""
from app.services.importance import score_message_heuristic

JUNK = [
    "The main tension in the novel is class conflict",
    "It's a mere formality, the main operation was approved last week",
    "I think the main issue is the operation of the pump",
    "and I broke up the fight between my kids yesterday",
    "I'm moving to the next question now",
    "Moving to the next slide, this one shows revenue",
    "I never booked anything for that trip",
    "My first point is that we should leave earlier",
    "The main exam results are out on the portal",
    "main tension mein nahi hoon, sab theek hai",
    "I had tension in my shoulders after the workout",
    "Her dog's bday is on Saturday, she told me",
    "riya bday 12 may hai, usko gift dena hai",
    "uske bhai's shaadi next month hai, he told me",
    "First day of the big sale was crazy, I got nothing",
    "I read that the operation succeeded in the news today",
]

KEEP = [
    "My first marathon is in February, just started training",
    "I just booked my tickets to Jaipur for Diwali",
    "Nani's operation is on Friday, taking the day off",
    "I shifted to a cheaper flat in Whitefield last week",
    "My interview with Amazon got moved to Thursday",
    "Riya and I broke up last night",
    "Mom's birthday is on 3rd March, want to plan something",
    "I usually study late at night, like 1am",
    "mera weight 72 kg tha last month",
]

DROP = [
    "Is my interview today?",
    "kya main bahut tension mein hoon?",
    "uski nani ka operation kal hai, wo bahut pareshan hai",
    "her bday is next week btw",
    "What if mom's surgery gets delayed, should I call her?",
    "Did I tell you where mom's ring is?",
    "What do you remember about my flight?",
]

# Additional held-out negatives in the same classes, not in the review probes.
EXTRA_JUNK = [
    "The main character finally breaks up with her in chapter 9",
    "My first thought was to call the plumber",
    "I'm moving to the next topic after this",
    "uski shaadi december mein hai, he mentioned it",
    "His dog's bday party is on Sunday",
    "I booked nothing yet, still comparing prices",
]


def _texts(sentence):
    return [f.text.lower() for f in score_message_heuristic(sentence)]


def test_review_junk_probes_not_stored():
    for sentence in JUNK:
        assert score_message_heuristic(sentence) == [], sentence


def test_extra_held_out_junk_not_stored():
    for sentence in EXTRA_JUNK:
        assert score_message_heuristic(sentence) == [], sentence


def test_genuine_recall_wins_still_stored():
    for sentence in KEEP:
        assert score_message_heuristic(sentence), sentence


def test_probe_guards_still_drop():
    for sentence in DROP:
        assert score_message_heuristic(sentence) == [], sentence


def test_third_party_occasion_never_becomes_user_identity():
    # HIGH-1 from the review: a third party's occasion must not be stored as
    # the user's own identity fact.
    for sentence in (
        "Her dog's bday is on Saturday, she told me",
        "riya bday 12 may hai, usko gift dena hai",
        "His dog's bday party is on Sunday",
    ):
        for fact in score_message_heuristic(sentence):
            assert fact.category != "identity", sentence
