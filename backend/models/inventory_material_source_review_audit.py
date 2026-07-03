from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String


class Inventory_material_source_review_audit(Base):
    __tablename__ = "inventory_material_source_review_audit"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    material_id = Column(Integer, ForeignKey("inventory_materials.id"), nullable=False, index=True)
    material_code = Column(String, nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    old_source_checked_at = Column(DateTime(timezone=True), nullable=True)
    new_source_checked_at = Column(DateTime(timezone=True), nullable=True)
    old_source_url = Column(String, nullable=True)
    new_source_url = Column(String, nullable=True)
    old_source_name = Column(String, nullable=True)
    new_source_name = Column(String, nullable=True)
    old_source_notes = Column(String, nullable=True)
    new_source_notes = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)