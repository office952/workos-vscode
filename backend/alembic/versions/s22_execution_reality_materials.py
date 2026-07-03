"""Sprint #22 — Add materials_json column to execution_reality.

BUILD SET 3B: ExecutionReality Materials Capture.

Adds a `materials_json` TEXT column (default "[]") to the execution_reality
table. This stores consumed materials as observational data only — no
inventory side effects, no cost engine updates.

Revision ID: s22_materials_capture
Revises: s21_uncovered_models
Create Date: 2026-05-12
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s22_materials_capture"
down_revision: Union[str, Sequence[str], None] = "s21_uncovered_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not _column_exists("execution_reality", "materials_json"):
        op.add_column(
            "execution_reality",
            sa.Column("materials_json", sa.String(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    if _column_exists("execution_reality", "materials_json"):
        op.drop_column("execution_reality", "materials_json")