"""Add monthly_internal_pay_amount to employees — internal pay base for tranșe 15/30.

Not company cost (cost_lunar_firma) and not fiscal payroll.

Revision ID: s49_employee_monthly_internal_pay_amount
Revises: s48_employee_balance_transactions
Create Date: 2026-06-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s49_employee_monthly_internal_pay_amount"
down_revision: Union[str, Sequence[str], None] = "s48_employee_balance_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("monthly_internal_pay_amount", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employees", "monthly_internal_pay_amount")
