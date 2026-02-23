import tempfile
import subprocess
from typing import Dict
import httpx
from app.config import settings


BLOCKLIST = [
    "import os",
    "import subprocess",
    "import socket",
    "import sys",
    "import pathlib",
    "open(",
    "__import__",
]


class ToolSandbox:
    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def run_python(self, code: str) -> Dict:
        if settings.TOOL_SANDBOX_URL:
            return self._run_remote(code)
        for bad in BLOCKLIST:
            if bad in code:
                return {"status": "blocked", "error": f"Blocked token: {bad}"}

        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/tool.py"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(code)

            try:
                result = subprocess.run(
                    ["python", path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                output = (result.stdout or "") + (result.stderr or "")
                return {"status": "ok" if result.returncode == 0 else "error", "output": output}
            except subprocess.TimeoutExpired:
                return {"status": "timeout", "error": "Tool execution timed out"}

    def _run_remote(self, code: str) -> Dict:
        try:
            res = httpx.post(
                f"{settings.TOOL_SANDBOX_URL.rstrip('/')}/run",
                json={"code": code},
                timeout=self.timeout_seconds,
            )
            if res.status_code != 200:
                return {"status": "error", "error": f"Sandbox error: {res.text}"}
            data = res.json()
            return data if isinstance(data, dict) else {"status": "error", "error": "Invalid sandbox response"}
        except Exception as exc:
            return {"status": "error", "error": f"Sandbox request failed: {exc}"}
