"""Field installation team reporting reality columns.

Revision ID: s44_field_installation_reporting
Revises: s43_operational_resource_registry
Create Date: 2026-06-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s44_field_installation_reporting"
down_revision: Union[str, Sequence[str], None] = "s43_operational_resource_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _column_exists("field_installation_teams", "started_at"):
        op.add_column("field_installation_teams", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("field_installation_teams", "ended_at"):
        op.add_column("field_installation_teams", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
    if not _column_exists("field_installation_teams", "client_observations"):
        op.add_column("field_installation_teams", sa.Column("client_observations", sa.Text(), nullable=True))
    if not _column_exists("field_installation_teams", "reporting_json"):
        op.add_column("field_installation_teams", sa.Column("reporting_json", sa.Text(), nullable=True))


def downgrade() -> None:
    if _column_exists("field_installation_teams", "reporting_json"):
        op.drop_column("field_installation_teams", "reporting_json")
    if _column_exists("field_installation_teams", "client_observations"):
        op.drop_column("field_installation_teams", "client_observations")
    if _column_exists("field_installation_teams", "ended_at"):
        op.drop_column("field_installation_teams", "ended_at")
    if _column_exists("field_installation_teams", "started_at"):
        op.drop_column("field_installation_teams", "started_at")
