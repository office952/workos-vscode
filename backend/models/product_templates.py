from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String


class Product_templates(Base):
    __tablename__ = "product_templates"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    template_code = Column(String, nullable=False)
    family_id = Column(String, nullable=True)
    family_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    components_json = Column(String, nullable=True)
    operations_json = Column(String, nullable=True)
    required_materials_json = Column(String, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    base_labor_rate = Column(Float, nullable=True)
    base_margin_pct = Column(Float, nullable=True)
    active = Column(Boolean, nullable=True)
    notes = Column(String, nullable=True)
    # Additive publication lifecycle — NULL = legacy unspecified (not published).
    # active=true must never be treated as published/offerable/runtime-ready alone.
    publication_status = Column(String, nullable=True)
    publication_version = Column(Integer, nullable=True)
    last_e2e_verdict = Column(String, nullable=True)
    last_e2e_checked_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    published_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)