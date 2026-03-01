"""Quick SSE stream smoke test."""
import urllib.request
import json
import sys
import os
import time

BASE = "http://127.0.0.1:8000"

# Wait for server to be ready (up to 15s)
print("[*] Waiting for backend to be ready...")
for i in range(15):
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=2) as r:
            if r.status == 200:
                print(f"[+] Backend healthy after {i+1}s")
                break
    except Exception:
        time.sleep(1)
else:
    print("[✗] Backend never came up on port 8000")
    sys.exit(1)

# Login
print("[*] Logging in...")
login_data = json.dumps({"email": "miryn@gmail.com", "password": "miryn123"}).encode()
req = urllib.request.Request(
    f"{BASE}/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=15) as resp:
    TOKEN = json.loads(resp.read().decode())["access_token"]
print(f"[+] Got token: {TOKEN[:40]}...")

# Stream call
body = json.dumps({"message": "Hello, just a quick test. Reply in one sentence."}).encode()
req = urllib.request.Request(
    f"{BASE}/chat/stream",
    data=body,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    },
    method="POST",
)

print("[*] Calling /chat/stream ...")
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        print(f"[+] Status: {resp.status}")
        full = ""
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                if "chunk" in payload:
                    sys.stdout.write(payload["chunk"])
                    sys.stdout.flush()
                    full += payload["chunk"]
                elif "done" in payload:
                    print()
                    print(f"\n[+] Stream done. conversation_id={payload.get('conversation_id')}")
                elif "error" in payload:
                    print(f"\n[!] Stream error: {payload['error']}")
        if full:
            print(f"[+] Total chars received: {len(full)}")
            print("[✓] SMOKE TEST PASSED")
        else:
            print("[✗] SMOKE TEST FAILED — no chunks received")
except Exception as e:
    print(f"[✗] SMOKE TEST FAILED — {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
