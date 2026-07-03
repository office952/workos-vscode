from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String


class Quotes(Base):
    __tablename__ = "quotes"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False)
    intake_id = Column(Integer, nullable=True)
    intake_code = Column(String, nullable=True)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    status = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    valid_until = Column(String, nullable=True)
    line_items = Column(String, nullable=True)
    subtotal = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    discount_pct = Column(Float, nullable=True)
    total_before_vat = Column(Float, nullable=True)
    vat = Column(Float, nullable=True)
    grand_total = Column(Float, nullable=True)
    margin_pct = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    accepted_snapshot_v2_id = Column(
        Integer,
        ForeignKey("quote_snapshots_v2.id"),
        nullable=True,
        index=True,
    )
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)