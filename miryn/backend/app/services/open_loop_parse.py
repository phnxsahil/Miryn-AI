"""Parse the reflection model's "open_loops" field.

An open loop is something the user left unresolved: a pending decision, a plan that is not
done, or a question they still want answered. Plain discussion topics are not open loops.
Only well-formed items count; anything else is ignored and never guessed from topics.
"""

from typing import Any, Dict, List

MAX_LOOPS_PER_CHAT = 3
MAX_TOPIC_CHARS = 80


def parse_open_loops(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    loops: List[Dict[str, Any]] = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        topic = item.get("topic")
        if not isinstance(topic, str):
            continue
        topic = " ".join(topic.split())[:MAX_TOPIC_CHARS]
        if not topic or topic.casefold() in seen:
            continue
        try:
            importance = int(item.get("importance", 1))
        except (TypeError, ValueError):
            importance = 1
        loops.append({"topic": topic, "importance": min(max(importance, 1), 3)})
        seen.add(topic.casefold())
        if len(loops) >= MAX_LOOPS_PER_CHAT:
            break
    return loops
