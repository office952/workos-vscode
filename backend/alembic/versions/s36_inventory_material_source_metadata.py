"""Inventory material source metadata for UI v1 backend gaps.

Revision ID: s36_inventory_material_source_metadata
Revises: s35_material_price_registry_v1_1
Create Date: 2026-06-02

Adds optional source reference metadata fields on inventory_materials:
- source_name
- source_url
- source_checked_at
- source_notes
"""

from alembic import op
import sqlalchemy as sa


revision = "s36_inventory_material_source_metadata"
down_revision = "s35_material_price_registry_v1_1"
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

    if "source_name" not in cols:
        op.add_column("inventory_materials", sa.Column("source_name", sa.String(), nullable=True))

    if "source_url" not in cols:
        op.add_column("inventory_materials", sa.Column("source_url", sa.String(), nullable=True))

    if "source_checked_at" not in cols:
        op.add_column(
            "inventory_materials",
            sa.Column("source_checked_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "source_notes" not in cols:
        op.add_column("inventory_materials", sa.Column("source_notes", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("inventory_materials"):
        return

    cols = _column_names(inspector, "inventory_materials")

    if "source_notes" in cols:
        op.drop_column("inventory_materials", "source_notes")
    if "source_checked_at" in cols:
        op.drop_column("inventory_materials", "source_checked_at")
    if "source_url" in cols:
        op.drop_column("inventory_materials", "source_url")
    if "source_name" in cols:
        op.drop_column("inventory_materials", "source_name")
