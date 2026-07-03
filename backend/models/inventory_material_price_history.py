from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String


class Inventory_material_price_history(Base):
    __tablename__ = "inventory_material_price_history"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    material_id = Column(Integer, ForeignKey("inventory_materials.id"), nullable=False, index=True)
    unit_cost = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    vat_percent = Column(Float, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    changed_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    changed_by = Column(String, nullable=True)
    change_reason = Column(String, nullable=True)
    snapshot_source = Column(String, nullable=True)
