"""Onboarding-related schemas."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class OnboardingAnswer(BaseModel):
    question: str
    answer: str


class OnboardingCompleteRequest(BaseModel):
    responses: List[OnboardingAnswer]
    traits: Dict = Field(default_factory=dict)
    values: Dict = Field(default_factory=dict)
    preset: Optional[str] = "companion"
    goals: Optional[List[str]] = Field(default_factory=list)
    seed_belief: Optional[str] = None
