"""commercial markup policies foundation

Revision ID: s39_commercial_markup_policies_foundation
Revises: s38_inventory_material_source_review_audit
Create Date: 2026-06-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s39_commercial_markup_policies_foundation"
down_revision = "s38_inventory_material_source_review_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_markup_policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_value", sa.String(), nullable=False),
        sa.Column("markup_type", sa.String(), nullable=False),
        sa.Column("markup_percent", sa.Float(), nullable=True),
        sa.Column("markup_fixed", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("min_margin_amount", sa.Float(), nullable=True),
        sa.Column("rounding_mode", sa.String(), nullable=False, server_default="none"),
        sa.Column("applies_to", sa.String(), nullable=False, server_default="material_cost"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(
        "ix_commercial_markup_policies_scope",
        "commercial_markup_policies",
        ["scope_type", "scope_value"],
    )
    op.create_index(
        "ix_commercial_markup_policies_status",
        "commercial_markup_policies",
        ["status"],
    )
    op.create_index(
        "ix_commercial_markup_policies_priority",
        "commercial_markup_policies",
        ["priority"],
    )


def downgrade() -> None:
    op.drop_index("ix_commercial_markup_policies_priority", table_name="commercial_markup_policies")
    op.drop_index("ix_commercial_markup_policies_status", table_name="commercial_markup_policies")
    op.drop_index("ix_commercial_markup_policies_scope", table_name="commercial_markup_policies")
    op.drop_table("commercial_markup_policies")