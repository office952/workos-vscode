"""s50 — execution plan prepared_by + clarification target routing."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s50_execution_plan_prepared_by_clarification_target"
down_revision: Union[str, Sequence[str], None] = "s49_employee_monthly_internal_pay_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "execution_plan",
        sa.Column("prepared_by_user_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_execution_plan_prepared_by_user_id",
        "execution_plan",
        ["prepared_by_user_id"],
        unique=False,
    )
    op.add_column(
        "task_clarification_requests",
        sa.Column("target_user_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_task_clarification_requests_target_user_id",
        "task_clarification_requests",
        ["target_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_clarification_requests_target_user_id", table_name="task_clarification_requests")
    op.drop_column("task_clarification_requests", "target_user_id")
    op.drop_index("ix_execution_plan_prepared_by_user_id", table_name="execution_plan")
    op.drop_column("execution_plan", "prepared_by_user_id")
