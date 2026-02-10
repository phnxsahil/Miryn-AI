from sqlalchemy import Column, String
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SerializableMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SerializableMixin, Base):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
