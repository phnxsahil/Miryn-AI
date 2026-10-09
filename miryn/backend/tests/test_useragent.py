from app.core.useragent import describe_user_agent


def test_chrome_windows():
    assert describe_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36") == "Chrome on Windows"


def test_safari_iphone():
    assert describe_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1") == "Safari on iPhone/iOS"


def test_firefox_linux():
    assert describe_user_agent("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0") == "Firefox on Linux"


def test_curl():
    assert describe_user_agent("curl/8.0.1") == "API client on Unknown OS"


def test_empty_user_agent():
    assert describe_user_agent(None) == "Unknown device"
