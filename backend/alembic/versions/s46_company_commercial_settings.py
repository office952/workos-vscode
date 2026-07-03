"""Company commercial settings — canonical VAT % for quotes.

Revision ID: s46_company_commercial_settings
Revises: s45_operation_authorization_foundation
Create Date: 2026-06-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s46_company_commercial_settings"
down_revision: Union[str, Sequence[str], None] = "s45_operation_authorization_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("company_commercial_settings"):
        return
    op.create_table(
        "company_commercial_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "default_vat_pct",
            sa.Float(),
            nullable=False,
            server_default=sa.text("21"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    if _table_exists("company_commercial_settings"):
        op.drop_table("company_commercial_settings")
