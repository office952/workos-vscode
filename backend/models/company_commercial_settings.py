"""Company-level commercial settings — singleton row for quote VAT governance."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer


class CompanyCommercialSettings(Base):
    __tablename__ = "company_commercial_settings"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    default_vat_pct = Column(Float, nullable=False, default=21.0, server_default="21")
    eur_to_ron_rate = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
