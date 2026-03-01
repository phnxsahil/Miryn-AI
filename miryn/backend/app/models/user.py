from sqlalchemy import Column, String, Boolean, DateTime
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SerializableMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SerializableMixin, Base):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
