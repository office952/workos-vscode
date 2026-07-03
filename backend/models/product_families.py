from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String


class Product_families(Base):
    __tablename__ = "product_families"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    family_id = Column(String, nullable=False, unique=True, index=True)
    label = Column(String, nullable=False)
    category = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    default_template_id = Column(Integer, ForeignKey("product_templates.id"), nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)