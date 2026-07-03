"""add source review audit table

Revision ID: s38_inventory_material_source_review_audit
Revises: s37_inventory_material_governance_fields
Create Date: 2026-06-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s38_inventory_material_source_review_audit"
down_revision = "s37_inventory_material_governance_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_material_source_review_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("inventory_materials.id"), nullable=False),
        sa.Column("material_code", sa.String(), nullable=False),
        sa.Column("old_status", sa.String(), nullable=True),
        sa.Column("new_status", sa.String(), nullable=True),
        sa.Column("old_source_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_source_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("old_source_url", sa.String(), nullable=True),
        sa.Column("new_source_url", sa.String(), nullable=True),
        sa.Column("old_source_name", sa.String(), nullable=True),
        sa.Column("new_source_name", sa.String(), nullable=True),
        sa.Column("old_source_notes", sa.String(), nullable=True),
        sa.Column("new_source_notes", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_inventory_material_source_review_audit_material_id", "inventory_material_source_review_audit", ["material_id"])
    op.create_index("ix_inventory_material_source_review_audit_material_code", "inventory_material_source_review_audit", ["material_code"])
    op.create_index("ix_inventory_material_source_review_audit_created_at", "inventory_material_source_review_audit", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_inventory_material_source_review_audit_created_at", table_name="inventory_material_source_review_audit")
    op.drop_index("ix_inventory_material_source_review_audit_material_code", table_name="inventory_material_source_review_audit")
    op.drop_index("ix_inventory_material_source_review_audit_material_id", table_name="inventory_material_source_review_audit")
    op.drop_table("inventory_material_source_review_audit")