# Self-contained stream smoke test that runs entirely in one process
# Usage: python _run_smoke.py
# Output written to _smoke_result.txt

import urllib.request, json, sys, time, os

BASE = "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke_result.txt")

lines = []
def log(msg):
    print(msg)
    lines.append(msg)

def save():
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

try:
    # 1) health check
    log("[*] Health check...")
    with urllib.request.urlopen(f"{BASE}/health", timeout=10) as r:
        log(f"[+] Health: {r.read().decode()}")

    # 2) login
    log("[*] Logging in...")
    login_body = json.dumps({"email": "miryn@gmail.com", "password": "miryn123"}).encode()
    req = urllib.request.Request(f"{BASE}/auth/login", data=login_body,
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        token = json.loads(r.read().decode())["access_token"]
    log(f"[+] Token: {token[:40]}...")

    # 3) stream
    log("[*] Calling /chat/stream ...")
    body = json.dumps({"message": "Say hello in one sentence."}).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/stream", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        log(f"[+] HTTP {resp.status}")
        full = ""
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line or not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            if "chunk" in payload:
                full += payload["chunk"]
            elif "done" in payload:
                log(f"[+] Done event. conversation_id={payload.get('conversation_id')}")
            elif "error" in payload:
                log(f"[!] Error: {payload['error']}")
        log(f"[+] Full response ({len(full)} chars):")
        log(full)
        if full:
            log("[✓] SMOKE TEST PASSED")
        else:
            log("[✗] SMOKE TEST FAILED — no chunks")
except Exception as e:
    import traceback
    log(f"[✗] SMOKE TEST FAILED — {e}")
    log(traceback.format_exc())
finally:
    save()
    print(f"[*] Results written to {OUT}")
