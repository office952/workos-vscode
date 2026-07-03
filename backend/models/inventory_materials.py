from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String


class Inventory_materials(Base):
    __tablename__ = "inventory_materials"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    unit = Column(String, nullable=False)
    stock_current = Column(Float, nullable=True)
    stock_min = Column(Float, nullable=True)
    stock_max = Column(Float, nullable=True)
    unit_cost = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    vat_percent = Column(Float, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    supplier = Column(String, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_checked_at = Column(DateTime(timezone=True), nullable=True)
    source_notes = Column(String, nullable=True)
    source_review_status = Column(String, nullable=True)
    source_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    source_reviewed_by = Column(String, nullable=True)
    last_restocked = Column(String, nullable=True)
    consumption_rate = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    sheet_format_type = Column(String, nullable=True, default="unknown")
    sheet_width = Column(Float, nullable=True)
    sheet_height = Column(Float, nullable=True)
    sheet_unit = Column(String, nullable=True, default="unknown")
    sheet_thickness = Column(Float, nullable=True)
    sheet_thickness_unit = Column(String, nullable=True, default="unknown")
    usable_width = Column(Float, nullable=True)
    usable_height = Column(Float, nullable=True)
    format_source = Column(String, nullable=True, default="unknown")
    format_verified = Column(Boolean, nullable=True, default=False)
    format_notes = Column(String, nullable=True)
    # Sprint #20: canonical status for the "no invented price" invariant.
    # One of: "active" | "missing_price" | "needs_owner_input" | "archived".
    # Nullable for backward-compatibility with rows seeded before Sprint #20.
    status = Column(String, nullable=True, default="missing_price")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)