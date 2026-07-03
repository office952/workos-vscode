"""Employee attendance events — default-present pontaj with exceptions.

Revision ID: s47_employee_attendance_events
Revises: s46_company_commercial_settings
Create Date: 2026-06-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s47_employee_attendance_events"
down_revision: Union[str, Sequence[str], None] = "s46_company_commercial_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    if _table_exists("employee_attendance_events"):
        cols = _column_names("employee_attendance_events")
        # Replace legacy single-day schema (event_date) before first commit.
        if "start_date" not in cols or "event_status" not in cols:
            op.drop_table("employee_attendance_events")
        else:
            return

    op.create_table(
        "employee_attendance_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_status", sa.String(length=32), nullable=False, server_default="confirmed"),
        sa.Column("hours_override", sa.Float(), nullable=True),
        sa.Column("hours_delta", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_employee_attendance_events_employee_id",
        "employee_attendance_events",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_attendance_events_start_date",
        "employee_attendance_events",
        ["start_date"],
        unique=False,
    )
    op.create_index(
        "ix_employee_attendance_events_end_date",
        "employee_attendance_events",
        ["end_date"],
        unique=False,
    )


def downgrade() -> None:
    if _table_exists("employee_attendance_events"):
        op.drop_table("employee_attendance_events")
