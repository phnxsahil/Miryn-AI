from sqlalchemy import Column, String, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.models.base import (
    Base,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    MetadataMixin,
    SerializableMixin,
)


class Message(UUIDPrimaryKeyMixin, CreatedAtMixin, MetadataMixin, SerializableMixin, Base):
    __tablename__ = "messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    idempotency_key = Column(String(255), nullable=True)
    embedding_source = Column(String(50), nullable=False, default="gemini")
    embedding = Column(Vector(384))
    importance_score = Column(Float, default=0.5)
