from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Suppliers(Base):
    __tablename__ = "suppliers"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=True)
    active_orders = Column(Integer, nullable=True)
    last_delivery = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)