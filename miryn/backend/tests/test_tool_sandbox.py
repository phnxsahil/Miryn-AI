from app.services.tool_sandbox import ToolSandbox


def test_tool_sandbox_blocks_dangerous_tokens():
    sandbox = ToolSandbox()
    result = sandbox.run_python("import os\nprint('hi')")
    assert result["status"] == "blocked"


def test_tool_sandbox_runs_safe_code():
    sandbox = ToolSandbox()
    result = sandbox.run_python("print('ok')")
    assert result["status"] == "ok", f"Expected 'ok' but got {result}"
