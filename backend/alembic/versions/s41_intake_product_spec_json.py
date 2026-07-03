"""intake_requests product_spec_json for per-customer product inputs

Revision ID: s41_intake_product_spec_json
Revises: s40_vector_asset_registry_svg_metrics
Create Date: 2026-06-04 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s41_intake_product_spec_json"
down_revision = "s40_vector_asset_registry_svg_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "intake_requests",
        sa.Column("product_spec_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("intake_requests", "product_spec_json")
