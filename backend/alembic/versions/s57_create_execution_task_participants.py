"""add execution_task_participants collaboration membership table

Revision ID: s57_create_execution_task_participants
Revises: s56_add_execution_plan_source_metadata
Create Date: 2026-07-16 00:00:00.000000

Phase 1: HELPER-only membership persistence. Empty table start; no backfill.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s57_create_execution_task_participants"
down_revision = "s56_add_execution_plan_source_metadata"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("execution_task_participants"):
        return

    op.create_table(
        "execution_task_participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=256), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="helper"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_by_employee_id", sa.Integer(), nullable=True),
        sa.Column("join_source", sa.String(length=32), nullable=True),
        sa.Column("execution_plan_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id",
            "task_id",
            "employee_id",
            name="uq_execution_task_participant",
        ),
    )
    op.create_index(
        "ix_execution_task_participants_order_id",
        "execution_task_participants",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_task_participants_task_id",
        "execution_task_participants",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_task_participants_employee_id",
        "execution_task_participants",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_task_participants_status",
        "execution_task_participants",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    if not _table_exists("execution_task_participants"):
        return
    op.drop_index(
        "ix_execution_task_participants_status",
        table_name="execution_task_participants",
    )
    op.drop_index(
        "ix_execution_task_participants_employee_id",
        table_name="execution_task_participants",
    )
    op.drop_index(
        "ix_execution_task_participants_task_id",
        table_name="execution_task_participants",
    )
    op.drop_index(
        "ix_execution_task_participants_order_id",
        table_name="execution_task_participants",
    )
    op.drop_table("execution_task_participants")
