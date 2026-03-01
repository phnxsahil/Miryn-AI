from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IdentityBelief(BaseModel):
    topic: str
    belief: str
    confidence: float = 0.5
    evidence: Dict[str, Any] = Field(default_factory=dict)


class IdentityOpenLoop(BaseModel):
    topic: str
    status: str = "open"
    importance: int = 1
    last_mentioned: Optional[str] = None


class IdentityPattern(BaseModel):
    pattern_type: str
    description: str
    signals: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5


class IdentityEmotion(BaseModel):
    primary_emotion: str
    intensity: float = 0.5
    secondary_emotions: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


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
    traits: Dict[str, Any] = Field(default_factory=dict)
    values: Dict[str, Any] = Field(default_factory=dict)
    beliefs: List[IdentityBelief] = Field(default_factory=list)
    open_loops: List[IdentityOpenLoop] = Field(default_factory=list)
    patterns: List[IdentityPattern] = Field(default_factory=list)
    emotions: List[IdentityEmotion] = Field(default_factory=list)
    conflicts: List[IdentityConflict] = Field(default_factory=list)
    memory_weights: Dict[str, float] = Field(default_factory=dict)


class IdentityUpdate(BaseModel):
    traits: Optional[Dict[str, Any]] = None
    values: Optional[Dict[str, Any]] = None
    beliefs: Optional[List[IdentityBelief]] = None
    open_loops: Optional[List[IdentityOpenLoop]] = None
    patterns: Optional[List[IdentityPattern]] = None
    emotions: Optional[List[IdentityEmotion]] = None
    conflicts: Optional[List[IdentityConflict]] = None
    state: Optional[str] = None
