"""add quotes.accepted_snapshot_v2_id FK to quote_snapshots_v2

Revision ID: s54_add_quotes_accepted_snapshot_v2_id
Revises: s53_create_quote_snapshots_v2
Create Date: 2026-06-30 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s54_add_quotes_accepted_snapshot_v2_id"
down_revision = "s53_create_quote_snapshots_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("quotes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("accepted_snapshot_v2_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_quotes_accepted_snapshot_v2_id",
            ["accepted_snapshot_v2_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_quotes_accepted_snapshot_v2_id",
            "quote_snapshots_v2",
            ["accepted_snapshot_v2_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("quotes", schema=None) as batch_op:
        batch_op.drop_constraint("fk_quotes_accepted_snapshot_v2_id", type_="foreignkey")
        batch_op.drop_index("ix_quotes_accepted_snapshot_v2_id")
        batch_op.drop_column("accepted_snapshot_v2_id")
