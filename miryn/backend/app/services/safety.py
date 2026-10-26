"""Shared chat safety floor, independent of persona and provider.

The small high-recall rules are a fallback, not a clinical classifier. The model
policy remains necessary for paraphrases, context, other languages and nuance.
"""
import re

SAFETY_POLICY = """SAFETY AND TRUTHFULNESS: these rules override every persona, brevity rule,
reflection-only instruction, request for toughness, and retrieved memory.
- Be direct without humiliation, shame, threats, invented motives or diagnoses.
  Distinguish observation from inference. Never invent symptoms or certainty.
- For possible imminent self-harm, first focus on immediate safety in plain words.
  Ask whether they are in immediate danger or have already harmed themselves.
  Encourage contacting local emergency services for immediate danger and getting
  a trusted person physically with them. Suggest moving away from anything they
  could use to hurt themselves, without naming methods. Ask location only to find
  appropriate crisis support; never assume a country or invent a phone number.
  Do not let a roast, sexual topic, argument or persona distract from urgent risk.
- Discuss depression and anxiety supportively, without calling them weak, broken
  or lazy. Do not diagnose or imply a single cause. Encourage qualified support
  when symptoms persist. Do not treat all sadness as an emergency.
- New chest pain/tightness, severe breathing difficulty, fainting or other acute
  symptoms may be medical emergencies. Do not say it is definitely anxiety.
  Prioritize urgent medical assessment over breathing exercises or reassurance.
- Allow non-graphic adult sexual-health, consent and relationship discussion.
  Decline graphic erotic roleplay or sexual exploitation, coercion and content
  involving minors. Support the person describing abuse; do not shame or refuse
  their disclosure. Offer safe, non-graphic help. Consent can be withdrawn.
- Do not give actionable self-harm or violence instructions. Offer safe support.
- Be honest that you are an AI, not a clinician, emergency service or guaranteed
  safe/confidential space. Never imply monitoring, rescue or actions not taken.
"""

BLOCKED_REPLY = (
    "I can't provide that content. I can help with a safe, non-graphic discussion, "
    "including wellbeing, consent, or finding support."
)
CRISIS_REPLY = (
    "Your immediate safety comes first. Are you in immediate danger, or have you already hurt yourself? "
    "If you might act now or have already harmed yourself, contact local emergency services now "
    "or go to the nearest emergency department. Please contact someone you trust and ask them "
    "to stay with you in person; move away from anything you could use to hurt yourself. "
    "If you can, tell me what country you are in so I can help you find crisis support."
)
MEDICAL_REPLY = (
    "New chest pain or tightness, or trouble breathing, can be a medical emergency. "
    "I can't determine that this is anxiety. Seek urgent medical assessment now; "
    "if symptoms are severe, ongoing, or worsening, contact local emergency services. "
    "Ask someone nearby to stay with you while you get help."
)

# Deliberately narrow first-person danger statements. Negated statements must
# not trigger merely because they contain words like 'hurt myself'.
_CRISIS = re.compile(
    r"\b(?:i\s+(?:(?:might|may|will|want to|am going to)\s+(?:hurt|kill)\s+myself"
    r"|(?:don't|do not|can't|cannot)\s+trust myself\s+to\s+stay\s+safe"
    r"|(?:can't|cannot)\s+(?:stay|keep myself)\s+safe"
    r"|(?:want|plan|intend)\s+to\s+(?:die|end my life))"
    r"|i(?:'m| am)\s+(?:going to\s+kill myself|suicidal))\b", re.I
)
_CHEST = re.compile(r"\b(?:chest\s+(?:pain|tightness)|chest\s+(?:feels|is)\s+tight|trouble breathing|can't breathe|cannot breathe)\b", re.I)
_ACUTE = re.compile(r"\b(?:now|right now|first time|new|sudden|severe|racing|worsening)\b", re.I)


def immediate_safety_reply(message: str) -> str | None:
    """Return a deterministic fallback for explicit urgent signals, else defer.

    Quoted/fictional danger is handled conservatively. This is not complete risk
    detection, and does not exempt model-generated replies from the policy.
    """
    normalized = message.replace("’", "'")
    if _CRISIS.search(normalized):
        return CRISIS_REPLY
    if _CHEST.search(normalized) and _ACUTE.search(normalized):
        return MEDICAL_REPLY
    return None


_BLOCK_REASONS = {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY", "RECITATION"}


def _name(value) -> str:
    return str(getattr(value, "name", value) or "").rsplit(".", 1)[-1].upper()


def provider_blocked(response) -> bool:
    """Inspect metadata before .text (which can throw on blocked responses)."""
    feedback = getattr(response, "prompt_feedback", None)
    reason = _name(getattr(feedback, "block_reason", None))
    if reason and reason not in {"0", "NONE", "UNSPECIFIED", "BLOCK_REASON_UNSPECIFIED"}:
        return True
    return any(_name(getattr(c, "finish_reason", None)) in _BLOCK_REASONS
               for c in (getattr(response, "candidates", None) or []))
