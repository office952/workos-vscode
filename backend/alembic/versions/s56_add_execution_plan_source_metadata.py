"""add execution_plan source metadata columns

Revision ID: s56_add_execution_plan_source_metadata
Revises: s55_add_orders_quote_snapshot_v2_fields
Create Date: 2026-06-30 16:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s56_add_execution_plan_source_metadata"
down_revision = "s55_add_orders_quote_snapshot_v2_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("execution_plan", schema=None) as batch_op:
        batch_op.add_column(sa.Column("plan_source", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("source_quote_snapshot_v2_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("source_snapshot_code", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("source_content_hash", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("source_order_snapshot_version", sa.String(), nullable=True))
        batch_op.create_index(
            "ix_execution_plan_plan_source",
            ["plan_source"],
            unique=False,
        )
        batch_op.create_index(
            "ix_execution_plan_source_quote_snapshot_v2_id",
            ["source_quote_snapshot_v2_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_execution_plan_source_quote_snapshot_v2_id",
            "quote_snapshots_v2",
            ["source_quote_snapshot_v2_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("execution_plan", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_execution_plan_source_quote_snapshot_v2_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_execution_plan_source_quote_snapshot_v2_id")
        batch_op.drop_index("ix_execution_plan_plan_source")
        batch_op.drop_column("source_order_snapshot_version")
        batch_op.drop_column("source_content_hash")
        batch_op.drop_column("source_snapshot_code")
        batch_op.drop_column("source_quote_snapshot_v2_id")
        batch_op.drop_column("plan_source")
