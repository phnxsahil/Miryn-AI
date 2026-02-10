"""Onboarding-related schemas."""

from typing import List, Dict
from pydantic import BaseModel, Field


class OnboardingAnswer(BaseModel):
    question: str
    answer: str


class OnboardingCompleteRequest(BaseModel):
    responses: List[OnboardingAnswer]
    traits: Dict = Field(default_factory=dict)
    values: Dict = Field(default_factory=dict)
