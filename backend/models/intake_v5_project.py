"""Intake V5 project — simplified end-to-end flow.

One row per project: stores form inputs, computed BOM, and linkage
to existing Quotes / Orders / ExecutionPlan tables.
"""

from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func


class IntakeV5Project(Base):
    __tablename__ = "intake_v5_projects"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True, index=True)
    template_code = Column(String, nullable=False, default="TPL-VOLUMETRIC-LETTERS_v2")
    status = Column(String, nullable=False, default="draft", index=True)

    # Client
    client_name = Column(String, nullable=False)
    job_title = Column(String, nullable=True)

    # Form inputs (JSON)
    inputs_json = Column(Text, nullable=False)

    # Cached BOM result (JSON) — recalculated on input change
    bom_json = Column(Text, nullable=True)

    # Totals (denormalised for listing)
    material_total_eur = Column(Float, nullable=True)
    operation_total_eur = Column(Float, nullable=True)
    grand_total_eur = Column(Float, nullable=True)

    # Linkage to existing tables
    quote_id = Column(Integer, nullable=True, index=True)
    order_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
