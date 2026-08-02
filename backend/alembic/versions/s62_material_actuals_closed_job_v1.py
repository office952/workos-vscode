"""Additive Material Actuals / Closed-Job Proof V1.

Revision ID: s62_material_actuals_closed_job_v1
Revises: s61_merge_heads_actual_cost_policy
Create Date: 2026-08-02

Adds StockMovement.reverses_movement_id so RETURN can reverse an original
ISSUE/consumption with frozen valuation. No commercial/pricing changes.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "s62_material_actuals_closed_job_v1"
down_revision: Union[str, Sequence[str], None] = "s61_merge_heads_actual_cost_policy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    bind = op.get_bind()
    if table not in set(inspect(bind).get_table_names()):
        return set()
    return {c["name"] for c in inspect(bind).get_columns(table)}


def _indexes(table: str) -> set[str]:
    bind = op.get_bind()
    if table not in set(inspect(bind).get_table_names()):
        return set()
    return {i["name"] for i in inspect(bind).get_indexes(table) if i.get("name")}


def upgrade() -> None:
    cols = _columns("stock_movements")
    idxs = _indexes("stock_movements")
    if not cols:
        return
    with op.batch_alter_table("stock_movements", schema=None) as batch_op:
        if "reverses_movement_id" not in cols:
            batch_op.add_column(sa.Column("reverses_movement_id", sa.Integer(), nullable=True))
        if "ix_stock_movements_reverses_movement_id" not in idxs:
            batch_op.create_index(
                "ix_stock_movements_reverses_movement_id",
                ["reverses_movement_id"],
                unique=False,
            )


def downgrade() -> None:
    cols = _columns("stock_movements")
    idxs = _indexes("stock_movements")
    if not cols:
        return
    with op.batch_alter_table("stock_movements", schema=None) as batch_op:
        if "ix_stock_movements_reverses_movement_id" in idxs:
            batch_op.drop_index("ix_stock_movements_reverses_movement_id")
        if "reverses_movement_id" in cols:
            batch_op.drop_column("reverses_movement_id")
