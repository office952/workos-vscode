"""Sprint #25 — SmartBill integration settings secure storage.

Creates integration_settings table used for app-managed provider configuration.
Secrets are stored encrypted at service layer; migration never writes credential defaults.

Revision ID: s25_smartbill_integration_settings
Revises: s24_inventory_sheet_format
Create Date: 2026-05-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s25_smartbill_integration_settings"
down_revision: Union[str, Sequence[str], None] = "s24_inventory_sheet_format"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("integration_settings"):
        return

    op.create_table(
        "integration_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("username_secret", sa.Text(), nullable=True),
        sa.Column("token_secret", sa.Text(), nullable=True),
        sa.Column("lookup_path", sa.String(length=255), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("config_source", sa.String(length=32), nullable=False, server_default=sa.text("'app_settings'")),
        sa.Column("last_test_status", sa.String(length=32), nullable=True),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_message", sa.String(length=512), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", name="uq_integration_settings_provider"),
    )
    op.create_index(op.f("ix_integration_settings_id"), "integration_settings", ["id"], unique=False)
    op.create_index(op.f("ix_integration_settings_provider"), "integration_settings", ["provider"], unique=False)


def downgrade() -> None:
    if not _table_exists("integration_settings"):
        return

    op.drop_index(op.f("ix_integration_settings_provider"), table_name="integration_settings")
    op.drop_index(op.f("ix_integration_settings_id"), table_name="integration_settings")
    op.drop_table("integration_settings")