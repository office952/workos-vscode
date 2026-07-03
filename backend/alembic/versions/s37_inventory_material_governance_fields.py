"""Inventory material governance fields for schema-backed policy layer.

Revision ID: s37_inventory_material_governance_fields
Revises: s36_inventory_material_source_metadata
Create Date: 2026-06-03

Adds optional governance fields on inventory_materials:
- subcategory
- source_review_status
- source_reviewed_at
- source_reviewed_by
"""

from alembic import op
import sqlalchemy as sa


revision = "s37_inventory_material_governance_fields"
down_revision = "s36_inventory_material_source_metadata"
branch_labels = None
depends_on = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("inventory_materials"):
        return

    cols = _column_names(inspector, "inventory_materials")

    if "subcategory" not in cols:
        op.add_column("inventory_materials", sa.Column("subcategory", sa.String(), nullable=True))

    if "source_review_status" not in cols:
        op.add_column("inventory_materials", sa.Column("source_review_status", sa.String(), nullable=True))

    if "source_reviewed_at" not in cols:
        op.add_column(
            "inventory_materials",
            sa.Column("source_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "source_reviewed_by" not in cols:
        op.add_column("inventory_materials", sa.Column("source_reviewed_by", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("inventory_materials"):
        return

    cols = _column_names(inspector, "inventory_materials")

    if "source_reviewed_by" in cols:
        op.drop_column("inventory_materials", "source_reviewed_by")
    if "source_reviewed_at" in cols:
        op.drop_column("inventory_materials", "source_reviewed_at")
    if "source_review_status" in cols:
        op.drop_column("inventory_materials", "source_review_status")
    if "subcategory" in cols:
        op.drop_column("inventory_materials", "subcategory")
