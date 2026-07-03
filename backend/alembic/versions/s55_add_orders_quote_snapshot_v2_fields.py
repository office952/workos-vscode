"""add orders.quote_snapshot_v2_id and orders.snapshot_v2_json

Revision ID: s55_add_orders_quote_snapshot_v2_fields
Revises: s54_add_quotes_accepted_snapshot_v2_id
Create Date: 2026-06-30 14:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s55_add_orders_quote_snapshot_v2_fields"
down_revision = "s54_add_quotes_accepted_snapshot_v2_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("quote_snapshot_v2_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("snapshot_v2_json", sa.Text(), nullable=True))
        batch_op.create_index(
            "ix_orders_quote_snapshot_v2_id",
            ["quote_snapshot_v2_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_orders_quote_snapshot_v2_id",
            "quote_snapshots_v2",
            ["quote_snapshot_v2_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint("fk_orders_quote_snapshot_v2_id", type_="foreignkey")
        batch_op.drop_index("ix_orders_quote_snapshot_v2_id")
        batch_op.drop_column("snapshot_v2_json")
        batch_op.drop_column("quote_snapshot_v2_id")
