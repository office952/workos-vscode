"""s50 — execution plan prepared_by + clarification target routing.

Hygiene note (2026-08-02 pre-push hardening):
This revision is an accidental side-branch from s49 that coexists with
s50_employee_payment_records on the main chain. Fresh `alembic upgrade head`
failed because `task_clarification_requests` was never created by any prior
migration (local DBs obtained it via ORM bootstrap / create_all).

Upgrade/downgrade are now inspect-before-mutate so the branch is deployable
and can merge cleanly into s61_merge_heads_actual_cost_policy.
Schema intent is unchanged.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "s50_execution_plan_prepared_by_clarification_target"
down_revision: Union[str, Sequence[str], None] = "s49_employee_monthly_internal_pay_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in inspect(op.get_bind()).get_indexes(table) if i.get("name")}


def upgrade() -> None:
    tables = _table_names()

    if "execution_plan" in tables:
        cols = _columns("execution_plan")
        idxs = _indexes("execution_plan")
        if "prepared_by_user_id" not in cols:
            op.add_column(
                "execution_plan",
                sa.Column("prepared_by_user_id", sa.String(length=255), nullable=True),
            )
        if "ix_execution_plan_prepared_by_user_id" not in idxs:
            op.create_index(
                "ix_execution_plan_prepared_by_user_id",
                "execution_plan",
                ["prepared_by_user_id"],
                unique=False,
            )

    # Table was historically bootstrapped outside Alembic; ensure it exists
    # before additive column/index work so fresh DBs can upgrade.
    if "task_clarification_requests" not in tables:
        op.create_table(
            "task_clarification_requests",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("target_user_id", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by_user_id", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_task_clarification_requests_id", "task_clarification_requests", ["id"])
        op.create_index(
            "ix_task_clarification_requests_order_id", "task_clarification_requests", ["order_id"]
        )
        op.create_index(
            "ix_task_clarification_requests_task_id", "task_clarification_requests", ["task_id"]
        )
        op.create_index(
            "ix_task_clarification_requests_employee_id",
            "task_clarification_requests",
            ["employee_id"],
        )
        op.create_index(
            "ix_task_clarification_requests_status", "task_clarification_requests", ["status"]
        )
        op.create_index(
            "ix_task_clarification_requests_target_user_id",
            "task_clarification_requests",
            ["target_user_id"],
        )
        return

    cols = _columns("task_clarification_requests")
    idxs = _indexes("task_clarification_requests")
    if "target_user_id" not in cols:
        op.add_column(
            "task_clarification_requests",
            sa.Column("target_user_id", sa.String(length=255), nullable=True),
        )
    if "ix_task_clarification_requests_target_user_id" not in idxs:
        op.create_index(
            "ix_task_clarification_requests_target_user_id",
            "task_clarification_requests",
            ["target_user_id"],
            unique=False,
        )


def downgrade() -> None:
    tables = _table_names()
    if "task_clarification_requests" in tables:
        idxs = _indexes("task_clarification_requests")
        cols = _columns("task_clarification_requests")
        if "ix_task_clarification_requests_target_user_id" in idxs:
            op.drop_index(
                "ix_task_clarification_requests_target_user_id",
                table_name="task_clarification_requests",
            )
        if "target_user_id" in cols:
            op.drop_column("task_clarification_requests", "target_user_id")
    if "execution_plan" in tables:
        idxs = _indexes("execution_plan")
        cols = _columns("execution_plan")
        if "ix_execution_plan_prepared_by_user_id" in idxs:
            op.drop_index("ix_execution_plan_prepared_by_user_id", table_name="execution_plan")
        if "prepared_by_user_id" in cols:
            op.drop_column("execution_plan", "prepared_by_user_id")
