"""Small dependency-free user-agent descriptions for account sessions."""


def describe_user_agent(user_agent: str | None) -> str:
    if not user_agent:
        return "Unknown device"
    lowered = user_agent.lower()
    if "edg/" in lowered or "edge/" in lowered:
        browser = "Edge"
    elif "opr/" in lowered or "opera" in lowered:
        browser = "Opera"
    elif "firefox/" in lowered:
        browser = "Firefox"
    elif "curl/" in lowered or "python-requests" in lowered:
        browser = "API client"
    elif "chrome/" in lowered:
        browser = "Chrome"
    elif "safari/" in lowered:
        browser = "Safari"
    else:
        browser = "Browser"

    if "iphone" in lowered or "ipad" in lowered or "ios" in lowered:
        operating_system = "iPhone/iOS"
    elif "android" in lowered:
        operating_system = "Android"
    elif "windows" in lowered:
        operating_system = "Windows"
    elif "mac os" in lowered or "macintosh" in lowered:
        operating_system = "macOS"
    elif "linux" in lowered:
        operating_system = "Linux"
    else:
        operating_system = "Unknown OS"
    return f"{browser} on {operating_system}"
