from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, JSON, Text


class Orders(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False)
    quote_id = Column(Integer, nullable=True)
    quote_code = Column(String, nullable=True)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    status = Column(String, nullable=False)
    product_summary = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    locked_at = Column(String, nullable=True)
    promised_delivery = Column(String, nullable=True)
    job_id = Column(String, nullable=True)
    payment_status = Column(String, nullable=True)
    snapshot_version = Column(Integer, nullable=True)
    snapshot_line_items = Column(String, nullable=True)
    quote_snapshot_v2_id = Column(
        Integer,
        ForeignKey("quote_snapshots_v2.id"),
        nullable=True,
        index=True,
    )
    snapshot_v2_json = Column(Text, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    readiness_snapshot = Column(JSON, nullable=True)