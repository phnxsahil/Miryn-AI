"""Pure helper: render the current conversation's latest turns as role-tagged lines.

Not wired into the chat path yet. It exists so the assembly rules can be unit tested offline
with fictional rows before any prompt change is evaluated.
"""
from __future__ import annotations

from typing import Any, Iterable

_LABEL = {"user": "User", "assistant": "Miryn"}


def build_recent_turns_block(rows: Iterable[dict[str, Any]], max_turns: int = 8, max_chars: int = 3000) -> str:
    """rows: oldest-first dicts with role and content. Keeps the newest turns that fit.

    The newest turn is always kept (truncated if needed). Older turns are dropped whole,
    never cut mid-sentence, once the character budget is spent. Unknown roles are skipped.
    """
    usable = [r for r in rows if str(r.get("role") or "").lower() in _LABEL and str(r.get("content") or "").strip()]
    picked: list[str] = []
    used = 0
    for row in reversed(usable[-max_turns:]):
        line = f"{_LABEL[str(row['role']).lower()]}: {str(row['content']).strip()}"
        if not picked and len(line) > max_chars:
            line = line[: max_chars - 1].rstrip() + "…"
        if picked and used + len(line) > max_chars:
            break
        picked.append(line)
        used += len(line)
    if not picked:
        return ""
    return "Recent turns in this conversation (oldest first):\n" + "\n".join(reversed(picked))
