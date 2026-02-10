from fastapi import APIRouter, Depends
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
