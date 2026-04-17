"""
Memory Ranking API - Divyadeep Kaur
GET /memory/ranked — ranks stored memories by relevance score
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from app.core.security import get_current_user_id
from app.services.memory_ranking_model import rank_memories

router = APIRouter(prefix="/memory", tags=["Memory Ranking"])


class MemoryInput(BaseModel):
    memory: str
    days_ago: int
    emotional_intensity: float
    entity_overlap: int
    identity_alignment: int


class RankMemoriesRequest(BaseModel):
    memories: List[MemoryInput]


class RankedMemory(BaseModel):
    memory: str
    days_ago: int
    emotional_intensity: float
    entity_overlap: int
    identity_alignment: int
    relevance_score: float


class RankMemoriesResponse(BaseModel):
    ranked_memories: List[RankedMemory]
    total: int


@router.post("/ranked", response_model=RankMemoriesResponse)
async def rank_memories_endpoint(
    request: RankMemoriesRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Rank a list of memories by relevance score using the ML model.
    Returns memories sorted from most to least relevant.
    """
    memories = [m.dict() for m in request.memories]
    ranked = rank_memories({}, memories)
    return RankMemoriesResponse(
        ranked_memories=ranked,
        total=len(ranked)
    )