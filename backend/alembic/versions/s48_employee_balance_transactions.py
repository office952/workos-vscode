"""Employee internal balance ledger — advances, loans, retentions.

Revision ID: s48_employee_balance_transactions
Revises: s47_employee_attendance_events
Create Date: 2026-06-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s48_employee_balance_transactions"
down_revision: Union[str, Sequence[str], None] = "s47_employee_attendance_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_balance_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RON"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_employee_balance_transactions_employee_id",
        "employee_balance_transactions",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_balance_transactions_transaction_date",
        "employee_balance_transactions",
        ["transaction_date"],
        unique=False,
    )
    op.create_index(
        "ix_employee_balance_transactions_status",
        "employee_balance_transactions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("employee_balance_transactions")
