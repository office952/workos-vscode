from models.base import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func


class Integration_settings(Base):
    __tablename__ = "integration_settings"
    __table_args__ = (UniqueConstraint("provider", name="uq_integration_settings_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(64), nullable=False, index=True)

    enabled = Column(Boolean, nullable=False, default=False, server_default="0")
    base_url = Column(String(512), nullable=True)
    username_secret = Column(Text, nullable=True)
    token_secret = Column(Text, nullable=True)
    lookup_path = Column(String(255), nullable=True)
    timeout_seconds = Column(Integer, nullable=True)

    config_source = Column(String(32), nullable=False, default="app_settings", server_default="app_settings")
    last_test_status = Column(String(32), nullable=True)
    last_test_at = Column(DateTime(timezone=True), nullable=True)
    last_test_message = Column(String(512), nullable=True)

    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())