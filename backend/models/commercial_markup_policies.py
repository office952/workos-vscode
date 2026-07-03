from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String


class Commercial_markup_policies(Base):
    __tablename__ = "commercial_markup_policies"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    scope_type = Column(String, nullable=False)
    scope_value = Column(String, nullable=False)
    markup_type = Column(String, nullable=False)
    markup_percent = Column(Float, nullable=True)
    markup_fixed = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    min_margin_amount = Column(Float, nullable=True)
    rounding_mode = Column(String, nullable=False, default="none")
    applies_to = Column(String, nullable=False, default="material_cost")
    status = Column(String, nullable=False, default="draft")
    priority = Column(Integer, nullable=False, default=100)
    notes = Column(String, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now, nullable=False)