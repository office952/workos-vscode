"""Create Actual Cost Policy Runtime V1 storage.

Revision ID: s60_actual_cost_policy_runtime_v1
Revises: s59_employee_end_date_lifecycle
Create Date: 2026-08-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s60_actual_cost_policy_runtime_v1"
down_revision = "s59_employee_end_date_lifecycle"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "role_skill_labor_cost_policies" not in tables:
        op.create_table(
            "role_skill_labor_cost_policies",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("role_code", sa.String(), nullable=False),
            sa.Column("skill_code", sa.String(), nullable=True),
            sa.Column("standard_internal_rate", sa.Float(), nullable=False),
            sa.Column("rate_unit", sa.String(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("provenance", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.UniqueConstraint("role_code", "skill_code", "effective_from", name="uq_role_skill_labor_policy_start"),
        )
        op.create_index("ix_role_skill_labor_cost_policies_role_code", "role_skill_labor_cost_policies", ["role_code"])
    if "actual_labor_cost_lines" not in tables:
        op.create_table(
            "actual_labor_cost_lines",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_id", sa.String(), nullable=False),
            sa.Column("session_ref", sa.String(), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("role_code", sa.String(), nullable=False),
            sa.Column("skill_code", sa.String(), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=False),
            sa.Column("rate_used", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False),
            sa.Column("labor_cost_amount", sa.Float(), nullable=False),
            sa.Column("policy_id", sa.Integer(), nullable=False),
            sa.Column("policy_version", sa.Integer(), nullable=False),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("freeze_status", sa.String(), nullable=False),
            sa.UniqueConstraint("order_id", "session_ref", name="uq_actual_labor_cost_line_session"),
        )
        op.create_index("ix_actual_labor_cost_lines_order_id", "actual_labor_cost_lines", ["order_id"])
    if "execution_job_closures" not in tables:
        op.create_table(
            "execution_job_closures",
            sa.Column("order_id", sa.Integer(), primary_key=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_by", sa.String(), nullable=True),
            sa.Column("reopen_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reopen_by", sa.String(), nullable=True),
            sa.Column("reopen_reason", sa.String(), nullable=True),
            sa.Column("checklist_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "execution_job_closure_events" not in tables:
        op.create_table(
            "execution_job_closure_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("actor_id", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("checklist_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_execution_job_closure_events_order_id", "execution_job_closure_events", ["order_id"])
    stock_columns = _columns("stock_movements")
    additions = (
        ("unit_cost_snapshot", sa.Float()),
        ("currency_snapshot", sa.String()),
        ("valuation_method", sa.String()),
        ("valuation_provenance", sa.String()),
        ("extended_cost_snapshot", sa.Float()),
        ("price_history_id_snapshot", sa.Integer()),
    )
    with op.batch_alter_table("stock_movements", schema=None) as batch_op:
        for name, column_type in additions:
            if name not in stock_columns:
                batch_op.add_column(sa.Column(name, column_type, nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "stock_movements" in tables:
        stock_columns = _columns("stock_movements")
        with op.batch_alter_table("stock_movements", schema=None) as batch_op:
            for name in (
                "price_history_id_snapshot", "extended_cost_snapshot", "valuation_provenance",
                "valuation_method", "currency_snapshot", "unit_cost_snapshot",
            ):
                if name in stock_columns:
                    batch_op.drop_column(name)
    for table_name in (
        "execution_job_closure_events", "execution_job_closures", "actual_labor_cost_lines",
        "role_skill_labor_cost_policies",
    ):
        if table_name in tables:
            op.drop_table(table_name)
