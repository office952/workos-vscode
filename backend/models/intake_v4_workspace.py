"""ORM model for Intake V4 operator workspace persistence."""

from __future__ import annotations

from core.database import Base
from sqlalchemy import Column, DateTime, String, Text, func


class IntakeV4WorkspaceRecord(Base):
    __tablename__ = "intake_v4_workspaces"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, nullable=False)
    workspace_code = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    template_code = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="draft", index=True)
    payload_json = Column(Text, nullable=False)
    readiness_status = Column(String, nullable=True)
    created_by_user_id = Column(String, nullable=True, index=True)
    updated_by_user_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True, index=True)
