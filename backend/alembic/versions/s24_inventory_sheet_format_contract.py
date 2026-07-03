"""Sprint #24 — Inventory canonical sheet format contract.

Adds optional, backward-compatible sheet format fields to inventory_materials.
No stock/cost/status behavior changes.

Revision ID: s24_inventory_sheet_format
Revises: s23_dossier_hardening
Create Date: 2026-05-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s24_inventory_sheet_format"
down_revision: Union[str, Sequence[str], None] = "s23_dossier_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def upgrade() -> None:
    columns = [
        ("sheet_format_type", sa.Column("sheet_format_type", sa.String(), nullable=True, server_default=sa.text("'unknown'"))),
        ("sheet_width", sa.Column("sheet_width", sa.Float(), nullable=True)),
        ("sheet_height", sa.Column("sheet_height", sa.Float(), nullable=True)),
        ("sheet_unit", sa.Column("sheet_unit", sa.String(), nullable=True, server_default=sa.text("'unknown'"))),
        ("sheet_thickness", sa.Column("sheet_thickness", sa.Float(), nullable=True)),
        (
            "sheet_thickness_unit",
            sa.Column("sheet_thickness_unit", sa.String(), nullable=True, server_default=sa.text("'unknown'")),
        ),
        ("usable_width", sa.Column("usable_width", sa.Float(), nullable=True)),
        ("usable_height", sa.Column("usable_height", sa.Float(), nullable=True)),
        ("format_source", sa.Column("format_source", sa.String(), nullable=True, server_default=sa.text("'unknown'"))),
        ("format_verified", sa.Column("format_verified", sa.Boolean(), nullable=True, server_default=sa.false())),
        ("format_notes", sa.Column("format_notes", sa.String(), nullable=True)),
    ]

    with op.batch_alter_table("inventory_materials", schema=None) as batch_op:
        for name, col in columns:
            if not _column_exists("inventory_materials", name):
                batch_op.add_column(col)


def downgrade() -> None:
    drop_order = [
        "format_notes",
        "format_verified",
        "format_source",
        "usable_height",
        "usable_width",
        "sheet_thickness_unit",
        "sheet_thickness",
        "sheet_unit",
        "sheet_height",
        "sheet_width",
        "sheet_format_type",
    ]

    with op.batch_alter_table("inventory_materials", schema=None) as batch_op:
        for name in drop_order:
            if _column_exists("inventory_materials", name):
                batch_op.drop_column(name)
