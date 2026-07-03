"""Employee internal payment records — not fiscal payroll.

Revision ID: s50_employee_payment_records
Revises: s49_employee_monthly_internal_pay_amount
Create Date: 2026-06-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s50_employee_payment_records"
down_revision: Union[str, Sequence[str], None] = "s49_employee_monthly_internal_pay_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_payment_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("slot", sa.String(length=2), nullable=False),
        sa.Column("amount_paid", sa.Float(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="confirmed"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_employee_payment_records_employee_period",
        "employee_payment_records",
        ["employee_id", "year", "month", "slot"],
    )


def downgrade() -> None:
    op.drop_index("ix_employee_payment_records_employee_period", table_name="employee_payment_records")
    op.drop_table("employee_payment_records")
