"""Sprint #20 — Product Registry Foundation.

Adds:
  1. New table `workcenter_rates` (canonical per-workcenter hourly rates).
  2. New column `inventory_materials.status` defaulting to "active"
     (preserves semantics of existing rows, which already have `unit_cost`).

This migration is idempotent: if `init_db()` auto-created the table via ORM
in earlier environments, the migration detects and skips table creation.
Similarly, column adds check existence first.

Revision ID: s20_workcenter_rates
Revises: 1588bf4744d8
Create Date: 2026-04-29

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "s20_workcenter_rates"
down_revision: Union[str, Sequence[str], None] = "1588bf4744d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(i["name"] == index_name for i in inspector.get_indexes(table_name))


def upgrade() -> None:
    """Upgrade schema (idempotent)."""
    # --- 1. Create workcenter_rates table (skip if already exists) ----------
    if not _table_exists("workcenter_rates"):
        op.create_table(
            "workcenter_rates",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("rate_per_hour", sa.Float(), nullable=True),
            sa.Column(
                "currency", sa.String(), nullable=False, server_default=sa.text("'RON'")
            ),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default=sa.text("'missing_price'"),
            ),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_workcenter_rates_code"),
        )

    if not _index_exists("workcenter_rates", "ix_workcenter_rates_code"):
        op.create_index(
            "ix_workcenter_rates_code", "workcenter_rates", ["code"], unique=True
        )
    if not _index_exists("workcenter_rates", "ix_workcenter_rates_id"):
        op.create_index(
            "ix_workcenter_rates_id", "workcenter_rates", ["id"], unique=False
        )

    # --- 2. Add status column to inventory_materials (skip if present) ------
    if not _column_exists("inventory_materials", "status"):
        with op.batch_alter_table("inventory_materials", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "status",
                    sa.String(),
                    nullable=True,
                    server_default=sa.text("'active'"),
                )
            )

        # Backfill every existing row to "active" explicitly.
        op.execute(
            "UPDATE inventory_materials SET status = 'active' WHERE status IS NULL"
        )


def downgrade() -> None:
    """Downgrade schema."""
    if _column_exists("inventory_materials", "status"):
        with op.batch_alter_table("inventory_materials", schema=None) as batch_op:
            batch_op.drop_column("status")

    if _index_exists("workcenter_rates", "ix_workcenter_rates_id"):
        op.drop_index("ix_workcenter_rates_id", table_name="workcenter_rates")
    if _index_exists("workcenter_rates", "ix_workcenter_rates_code"):
        op.drop_index("ix_workcenter_rates_code", table_name="workcenter_rates")
    if _table_exists("workcenter_rates"):
        op.drop_table("workcenter_rates")