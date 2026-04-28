"""Chat-related request and response models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    insights: Optional[dict] = None
    conflicts: Optional[list] = None
    entities: Optional[List[Dict[str, Any]]] = None
    emotions: Optional[Dict[str, Any]] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: dict = Field(default_factory=dict)
    importance_score: float = 0.5


class ChatHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[MessageOut]


class TitleUpdate(BaseModel):
    title: str