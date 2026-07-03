from datetime import datetime

from core.database import Base
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text


class Inventory_sheet_remediation_audit_events(Base):
    __tablename__ = "inventory_sheet_remediation_audit_events"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False, index=True)
    issue_code = Column(String, nullable=False)
    old_values = Column(JSON, nullable=False)
    new_values = Column(JSON, nullable=False)
    changed_by = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    reason = Column(Text, nullable=False)
    validation_result_before = Column(JSON, nullable=False)
    validation_result_after = Column(JSON, nullable=False)
    source = Column(String, nullable=False)
