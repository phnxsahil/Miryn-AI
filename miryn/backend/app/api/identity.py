from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from app.services.identity_engine import IdentityEngine
from app.schemas.identity import IdentityOut, IdentityUpdate

router = APIRouter(prefix="/identity", tags=["identity"])

identity_engine = IdentityEngine()


@router.get("/", response_model=IdentityOut)
def get_identity(user_id: str = Depends(get_current_user_id)):
    return identity_engine.get_identity(user_id)


@router.patch("/", response_model=IdentityOut)
def update_identity(
    payload: IdentityUpdate,
    user_id: str = Depends(get_current_user_id),
):
    updated = identity_engine.update_identity(user_id, payload.dict(exclude_none=True))
    return updated


@router.get("/evolution")
def get_identity_evolution(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT *
                    FROM identity_evolution_log
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                ),
                {"user_id": user_id},
            ).mappings().all()
            return [dict(row) for row in rows]

    db = get_db()
    response = (
        db.table("identity_evolution_log")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return response.data or []
