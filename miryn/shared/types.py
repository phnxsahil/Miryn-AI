from typing import Dict, Any, List
from pydantic import BaseModel


class SharedIdentity(BaseModel):
    id: str
    user_id: str
    version: int
    state: str
    traits: Dict[str, Any]
    values: Dict[str, Any]
    beliefs: List[Dict[str, Any]]
    open_loops: List[Dict[str, Any]]


class SharedMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
