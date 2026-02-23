from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from app.core.audit import log_event
from app.services.llm_service import LLMService
from app.services.tool_sandbox import ToolSandbox

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolGenerateRequest(BaseModel):
    intent: str
    tool_type: str = "python"


class ToolApproveRequest(BaseModel):
    tool_id: str


@router.post("/generate")
async def generate_tool(
    payload: ToolGenerateRequest,
    user_id: str = Depends(get_current_user_id),
):
    if payload.tool_type != "python":
        raise HTTPException(status_code=400, detail="Only python tools are supported in MVP.")

    llm = LLMService()
    prompt = (
        "Generate a small, safe Python script that fulfills the user's intent. "
        "Return JSON with fields: name, description, code. "
        "Code must be self-contained, no network calls, no filesystem writes.\n\n"
        f"Intent: {payload.intent}"
    )
    response = await llm.generate(prompt, max_tokens=600)
    try:
        proposal = json.loads(response)
    except Exception:
        proposal = {"name": "generated_tool", "description": payload.intent, "code": response}

    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    INSERT INTO tool_runs (user_id, name, description, status, request, code)
                    VALUES (:user_id, :name, :description, :status, :request, :code)
                    RETURNING id, name, description, status, code
                    """
                ),
                {
                    "user_id": user_id,
                    "name": proposal.get("name"),
                    "description": proposal.get("description"),
                    "status": "pending",
                    "request": json.dumps(payload.dict()),
                    "code": proposal.get("code", ""),
                },
            ).mappings().first()
            session.commit()
        log_event("tool.generate", user_id=user_id, metadata={"tool_id": str(result["id"])})
        return dict(result)

    db = get_db()
    insert = db.table("tool_runs").insert(
        {
            "user_id": user_id,
            "name": proposal.get("name"),
            "description": proposal.get("description"),
            "status": "pending",
            "request": payload.dict(),
            "code": proposal.get("code", ""),
        }
    ).execute()
    if not insert.data:
        raise HTTPException(status_code=500, detail="Failed to create tool run")
    tool = insert.data[0]
    log_event("tool.generate", user_id=user_id, metadata={"tool_id": tool.get("id")})
    return tool


@router.get("/pending")
def list_pending(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, name, description, status, code, created_at
                    FROM tool_runs
                    WHERE user_id = :user_id AND status = 'pending'
                    ORDER BY created_at DESC
                    """
                ),
                {"user_id": user_id},
            )
            return [dict(row) for row in rows.mappings().all()]

    db = get_db()
    response = (
        db.table("tool_runs")
        .select("id, name, description, status, code, created_at")
        .eq("user_id", user_id)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


@router.post("/approve")
def approve_tool(
    payload: ToolApproveRequest,
    user_id: str = Depends(get_current_user_id),
):
    sandbox = ToolSandbox()
    if has_sql():
        with get_sql_session() as session:
            tool = session.execute(
                text(
                    """
                    SELECT id, code, status FROM tool_runs
                    WHERE id = :id AND user_id = :user_id
                    LIMIT 1
                    """
                ),
                {"id": payload.tool_id, "user_id": user_id},
            ).mappings().first()
            if not tool:
                raise HTTPException(status_code=404, detail="Tool not found")
            if tool["status"] != "pending":
                raise HTTPException(status_code=400, detail="Tool already executed")
            result = sandbox.run_python(tool["code"] or "")
            session.execute(
                text(
                    """
                    UPDATE tool_runs
                    SET status = :status, result = :result, updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": payload.tool_id,
                    "status": result["status"],
                    "result": result.get("output") or result.get("error", ""),
                },
            )
            session.commit()
        log_event("tool.approve", user_id=user_id, metadata={"tool_id": payload.tool_id})
        return {"status": "ok", "result": result}

    db = get_db()
    tool_resp = (
        db.table("tool_runs")
        .select("id, code, status")
        .eq("id", payload.tool_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not tool_resp.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool = tool_resp.data[0]
    if tool.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Tool already executed")
    result = sandbox.run_python(tool.get("code") or "")
    db.table("tool_runs").update(
        {"status": result["status"], "result": result.get("output") or result.get("error", "")}
    ).eq("id", payload.tool_id).execute()
    log_event("tool.approve", user_id=user_id, metadata={"tool_id": payload.tool_id})
    return {"status": "ok", "result": result}
