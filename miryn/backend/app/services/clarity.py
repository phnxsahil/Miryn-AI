"""Pure clarity scoring from real conversation signals."""


def compute_clarity(open_loops: int | list, avg_intensity: float, msgs_7d: int) -> tuple[int, str]:
    loop_count = len(open_loops) if isinstance(open_loops, list) else max(0, int(open_loops))
    intensity = min(1.0, max(0.0, float(avg_intensity)))
    recent_messages = max(0, int(msgs_7d))
    load = (
        0.5 * min(loop_count / 8, 1)
        + 0.3 * intensity
        + 0.2 * min(recent_messages / 70, 1)
    )
    score = round(100 * (1 - load))
    if load < 0.33:
        label = "Light"
    elif load < 0.66:
        label = "Moderate"
    else:
        label = "Heavy"
    return score, label
