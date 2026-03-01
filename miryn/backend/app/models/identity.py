from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    CreatedAtMixin,
    SerializableMixin,
)


class Identity(UUIDPrimaryKeyMixin, TimestampMixin, SerializableMixin, Base):
    __tablename__ = "identities"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1)
    state = Column(String(50), default="onboarding")
    traits = Column(JSONB, default=dict)
    values = Column(JSONB, default=dict)
    beliefs = Column(JSONB, default=list)
    open_loops = Column(JSONB, default=list)
    memory_weights = Column(
        JSONB,
        default=lambda: {"beliefs": 0.33, "emotions": 0.33, "facts": 0.17, "goals": 0.17},
    )


class OnboardingResponse(UUIDPrimaryKeyMixin, CreatedAtMixin, SerializableMixin, Base):
    __tablename__ = "onboarding_responses"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question = Column(String(500), nullable=False)
    answer = Column(String)
