"""add execution_task_help_requests collaboration help table

Revision ID: s58_create_execution_task_help_requests
Revises: s57_create_execution_task_participants
Create Date: 2026-07-16

Phase 2: help need signal (broadcast OPEN / targeted). Empty start; no backfill.
Partial unique: at most one OPEN per (order_id, task_id).
Optional membership provenance: source_help_request_id on participants.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s58_create_execution_task_help_requests"
down_revision = "s57_create_execution_task_participants"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(ix["name"] == index_name for ix in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("execution_task_help_requests"):
        op.create_table(
            "execution_task_help_requests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_id", sa.String(length=256), nullable=False),
            sa.Column("requested_by_employee_id", sa.Integer(), nullable=False),
            sa.Column("targeted_employee_id", sa.Integer(), nullable=True),
            sa.Column(
                "status",
                sa.String(length=16),
                nullable=False,
                server_default="OPEN",
            ),
            sa.Column("reason", sa.String(length=512), nullable=True),
            sa.Column("competence_hint", sa.String(length=128), nullable=True),
            sa.Column("execution_plan_id", sa.Integer(), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["requested_by_employee_id"],
                ["employees.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["targeted_employee_id"],
                ["employees.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_execution_task_help_requests_order_id",
            "execution_task_help_requests",
            ["order_id"],
            unique=False,
        )
        op.create_index(
            "ix_execution_task_help_requests_task_id",
            "execution_task_help_requests",
            ["task_id"],
            unique=False,
        )
        op.create_index(
            "ix_execution_task_help_requests_status",
            "execution_task_help_requests",
            ["status"],
            unique=False,
        )
        op.create_index(
            "ix_execution_task_help_requests_requested_by",
            "execution_task_help_requests",
            ["requested_by_employee_id"],
            unique=False,
        )
        op.create_index(
            "ix_execution_task_help_requests_targeted",
            "execution_task_help_requests",
            ["targeted_employee_id"],
            unique=False,
        )

    if not _index_exists(
        "execution_task_help_requests", "uq_execution_task_help_open_per_task"
    ):
        op.create_index(
            "uq_execution_task_help_open_per_task",
            "execution_task_help_requests",
            ["order_id", "task_id"],
            unique=True,
            sqlite_where=sa.text("status = 'OPEN'"),
            postgresql_where=sa.text("status = 'OPEN'"),
        )

    if _table_exists("execution_task_participants") and not _column_exists(
        "execution_task_participants", "source_help_request_id"
    ):
        op.add_column(
            "execution_task_participants",
            sa.Column("source_help_request_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            "ix_execution_task_participants_source_help",
            "execution_task_participants",
            ["source_help_request_id"],
            unique=False,
        )


def downgrade() -> None:
    if _table_exists("execution_task_participants") and _column_exists(
        "execution_task_participants", "source_help_request_id"
    ):
        if _index_exists(
            "execution_task_participants", "ix_execution_task_participants_source_help"
        ):
            op.drop_index(
                "ix_execution_task_participants_source_help",
                table_name="execution_task_participants",
            )
        op.drop_column("execution_task_participants", "source_help_request_id")

    if _table_exists("execution_task_help_requests"):
        if _index_exists(
            "execution_task_help_requests", "uq_execution_task_help_open_per_task"
        ):
            op.drop_index(
                "uq_execution_task_help_open_per_task",
                table_name="execution_task_help_requests",
            )
        for ix in (
            "ix_execution_task_help_requests_targeted",
            "ix_execution_task_help_requests_requested_by",
            "ix_execution_task_help_requests_status",
            "ix_execution_task_help_requests_task_id",
            "ix_execution_task_help_requests_order_id",
        ):
            if _index_exists("execution_task_help_requests", ix):
                op.drop_index(ix, table_name="execution_task_help_requests")
        op.drop_table("execution_task_help_requests")
