"""intake_requests persistence fields for template confirm, site audit

Revision ID: s42_intake_persistence_handoff
Revises: s41_intake_product_spec_json
Create Date: 2026-06-07 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s42_intake_persistence_handoff"
down_revision = "s41_intake_product_spec_json"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "intake_requests",
        sa.Column("confirmed_template_code", sa.String(), nullable=True),
    )
    op.add_column(
        "intake_requests",
        sa.Column("confirmed_template_name", sa.String(), nullable=True),
    )
    op.add_column(
        "intake_requests",
        sa.Column("site_audit_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("intake_requests", "site_audit_json")
    op.drop_column("intake_requests", "confirmed_template_name")
    op.drop_column("intake_requests", "confirmed_template_code")
