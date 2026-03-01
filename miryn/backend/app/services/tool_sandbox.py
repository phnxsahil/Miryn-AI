import os
import tempfile
import subprocess
import uuid
from pathlib import Path
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
        """
        Initialize the ToolSandbox.
        
        Parameters:
            timeout_seconds (int): Maximum number of seconds to allow a tool execution before timing out. Defaults to 10.
        """
        self.timeout_seconds = timeout_seconds

    def run_python(self, code: str) -> Dict:
        """
        Execute a Python source string inside a sandboxed environment and return a structured result.
        
        If a remote sandbox URL is configured the call is delegated to the remote service. Locally, the code is checked against a blocklist and will be rejected if it contains a forbidden token.
        
        Parameters:
            code (str): Python source code to execute.
        
        Returns:
            dict: A result dictionary with one of the following shapes:
                - {"status": "ok", "output": <combined stdout+stderr>} when execution exits with code 0.
                - {"status": "error", "output": <combined stdout+stderr>} when execution exits with a non-zero code.
                - {"status": "blocked", "error": "Blocked token: <token>"} when the code contains a disallowed token.
                - {"status": "timeout", "error": "Tool execution timed out"} when execution exceeds the configured timeout.
                - Any dict returned by the remote sandbox service when a remote sandbox URL is configured.
        """
        if settings.TOOL_SANDBOX_URL:
            return self._run_remote(code)
        for bad in BLOCKLIST:
            if bad in code:
                return {"status": "blocked", "error": f"Blocked token: {bad}"}

        tmp_root = Path(os.getenv("TOOL_SANDBOX_TMP_DIR") or tempfile.gettempdir())
        tmp_root.mkdir(parents=True, exist_ok=True)
        path = tmp_root / f"tool_{uuid.uuid4().hex}.py"
        try:
            path.write_text(code, encoding="utf-8")
            result = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            output = (result.stdout or "") + (result.stderr or "")
            return {"status": "ok" if result.returncode == 0 else "error", "output": output}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Tool execution timed out"}
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    def _run_remote(self, code: str) -> Dict:
        """
        Send the provided Python source code to the configured remote sandbox and return the sandbox's response.
        
        Parameters:
            code (str): Python source code to execute in the remote sandbox.
        
        Returns:
            dict: Execution result returned by the sandbox. On success this is the sandbox-provided result dictionary; on failure returns a dictionary with "status": "error" and an "error" message describing the failure.
        """
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
