from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class IdentityBelief(BaseModel):
    topic: str
    belief: str
    confidence: float = 0.5
    evidence: Dict[str, Any] = {}


class IdentityOpenLoop(BaseModel):
    topic: str
    status: str = "open"
    importance: int = 1
    last_mentioned: Optional[str] = None


class IdentityPattern(BaseModel):
    pattern_type: str
    description: str
    signals: Dict[str, Any] = {}
    confidence: float = 0.5


class IdentityEmotion(BaseModel):
    primary_emotion: str
    intensity: float = 0.5
    secondary_emotions: List[str] = []
    context: Dict[str, Any] = {}


class IdentityConflict(BaseModel):
    statement: str
    conflict_with: str
    severity: float = 0.5
    resolved: bool = False
    resolved_at: Optional[str] = None


class IdentityOut(BaseModel):
    id: str
    user_id: str
    version: int
    state: str
    traits: Dict[str, Any] = {}
    values: Dict[str, Any] = {}
    beliefs: List[IdentityBelief] = []
    open_loops: List[IdentityOpenLoop] = []
    patterns: List[IdentityPattern] = []
    emotions: List[IdentityEmotion] = []
    conflicts: List[IdentityConflict] = []


class IdentityUpdate(BaseModel):
    traits: Optional[Dict[str, Any]] = None
    values: Optional[Dict[str, Any]] = None
    beliefs: Optional[List[IdentityBelief]] = None
    open_loops: Optional[List[IdentityOpenLoop]] = None
    patterns: Optional[List[IdentityPattern]] = None
    emotions: Optional[List[IdentityEmotion]] = None
    conflicts: Optional[List[IdentityConflict]] = None
    state: Optional[str] = None
