import uuid

from sqlalchemy import JSON, UUID, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from veriqko.db.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # e.g. "ERP System"
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for display
    hashed_key = Column(String, nullable=False, unique=True)  # Store hash only!
    scopes = Column(JSON, nullable=False, default=list)  # ["jobs:read", "jobs:write"]
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = relationship("User")

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    events = Column(JSON, nullable=False, default=list)  # ["job.created", "job.completed"]
    secret_key = Column(String, nullable=False)  # For signing payloads (HMAC)
    is_active = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = relationship("User")
