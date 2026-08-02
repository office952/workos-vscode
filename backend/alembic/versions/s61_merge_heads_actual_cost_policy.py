"""Merge Alembic heads into a single deployable chain.

Revision ID: s61_merge_heads_actual_cost_policy
Revises: s50_execution_plan_prepared_by_clarification_target, s60_actual_cost_policy_runtime_v1
Create Date: 2026-08-02

Merge-only. No schema, table, column, or data changes.

Heads before merge:
  - s50_execution_plan_prepared_by_clarification_target
    (side branch from s49_employee_monthly_internal_pay_amount)
  - s60_actual_cost_policy_runtime_v1
    (main chain … → s50_employee_payment_records → … → s59 → s60)

After merge, single head:
  s61_merge_heads_actual_cost_policy

Deployment command: alembic upgrade head
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = "s61_merge_heads_actual_cost_policy"
down_revision: Union[str, Sequence[str], None] = (
    "s50_execution_plan_prepared_by_clarification_target",
    "s60_actual_cost_policy_runtime_v1",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge only — no schema changes."""
    pass


def downgrade() -> None:
    """Merge only — no schema changes."""
    pass
