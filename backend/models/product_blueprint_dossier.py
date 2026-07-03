"""ORM model for product_blueprint_dossier table.

Phase A — Product Blueprint Dossier Foundation.
Phase B — Hardening (FK, delete policy, versioning, semantic validation).

Decision: Option C — Controlled mixed model.

This table stores the extended technical documentation for each product template.
It is linked to product_templates via template_id (UNIQUE — one dossier per template).
FK constraint: ON DELETE RESTRICT — template cannot be deleted while dossier exists.

product_templates remains the operational configuration (components, operations, materials).
product_blueprint_dossier stores documentation, variants, task rules, time assumptions,
QC checkpoints, risks, and section completion state.

This model does NOT calculate cost, create offers, create orders, create tasks,
modify stock, or rewrite snapshots.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String


class ProductBlueprintDossier(Base):
    __tablename__ = "product_blueprint_dossier"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    template_id = Column(
        Integer,
        ForeignKey("product_templates.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    template_code = Column(String, nullable=False)
    dossier_version = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="draft")

    # --- Section JSON fields (all nullable — gradual population) ---
    sections_json = Column(String, nullable=True)
    variants_json = Column(String, nullable=True)
    layers_json = Column(String, nullable=True)
    task_rules_json = Column(String, nullable=True)
    time_assumptions_json = Column(String, nullable=True)
    costengine_mapping_json = Column(String, nullable=True)
    quote_readiness_json = Column(String, nullable=True)
    output_blocks_json = Column(String, nullable=True)
    visual_prompt_blocks_json = Column(String, nullable=True)
    production_notes_json = Column(String, nullable=True)
    qc_checkpoints_json = Column(String, nullable=True)
    risks_json = Column(String, nullable=True)
    completion_state_json = Column(String, nullable=True)

    # --- Ownership / review ---
    owner_role = Column(String, nullable=True)
    reviewer_role = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)