from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Intake_requests(Base):
    __tablename__ = "intake_requests"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    product_family = Column(String, nullable=False)
    description = Column(String, nullable=True)
    dimensions = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    assigned_to = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    delivery_type = Column(String, nullable=True)
    product_spec_json = Column(Text, nullable=True)
    confirmed_template_code = Column(String, nullable=True)
    confirmed_template_name = Column(String, nullable=True)
    site_audit_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)