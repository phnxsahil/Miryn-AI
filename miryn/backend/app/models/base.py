"""Shared SQLAlchemy declarative base and reusable mixins."""

from __future__ import annotations

import uuid
from typing import Any, Dict

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import declarative_base


Base = declarative_base()


def generate_uuid() -> uuid.UUID:
	"""Return a uuid4 suitable for use as a primary key default."""

	return uuid.uuid4()


class SerializableMixin:
	"""Provide helpers for serializing model instances."""

	def as_dict(self) -> Dict[str, Any]:
		mapper = inspect(self).mapper
		return {column.key: getattr(self, column.key) for column in mapper.column_attrs}

	def __repr__(self) -> str:  # pragma: no cover - convenience helper
		identifier = getattr(self, "id", None)
		return f"<{self.__class__.__name__} id={identifier}>"


class UUIDPrimaryKeyMixin:
	"""Add a UUID primary key column named id."""

	id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, nullable=False)


class CreatedAtMixin:
	"""Inject a created_at timestamp."""

	created_at = Column(DateTime, server_default=func.now(), nullable=False)


class TimestampMixin(CreatedAtMixin):
	"""Inject created_at and updated_at timestamps."""

	updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class MetadataMixin:
	"""Standardize optional JSON metadata storage."""

	metadata_payload = Column("metadata", JSONB, default=dict)

	@property
	def metadata_dict(self) -> Dict[str, Any]:
		return self.metadata_payload or {}

	@metadata_dict.setter
	def metadata_dict(self, value: Dict[str, Any]) -> None:
		self.metadata_payload = value or {}
