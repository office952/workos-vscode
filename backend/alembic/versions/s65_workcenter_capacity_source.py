"""Capacity Stage 1 — workcenter capacity source + allocation workload labels.

Revision ID: s65_workcenter_capacity_source
Revises: s64_resource_state_persistence
Create Date: 2026-08-05

EXPAND-ONLY:
  - create workcenter_capacity_sources + transitions
  - partial unique: one ACTIVE source per workcenter_code + bucket_date
  - add workload_* columns on execution_task_capacity_allocations
  - add workload_* columns on capacity allocation transitions
  - ZERO QA activation / ZERO data backfill
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "s65_workcenter_capacity_source"
down_revision: Union[str, Sequence[str], None] = "s64_resource_state_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns(table_name)}
    return column_name in cols


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return index_name in {ix["name"] for ix in inspect(bind).get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists("workcenter_capacity_sources"):
        op.create_table(
            "workcenter_capacity_sources",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("workcenter_code", sa.String(length=128), nullable=False),
            sa.Column("bucket_date", sa.Date(), nullable=False),
            sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("available_minutes", sa.Integer(), nullable=False),
            sa.Column(
                "over_allocation_policy",
                sa.String(length=32),
                nullable=False,
                server_default="WARN_ONLY",
            ),
            sa.Column(
                "source_label",
                sa.String(length=32),
                nullable=False,
                server_default="OWNER_CONFIGURED",
            ),
            sa.Column("source_explanation", sa.String(length=500), nullable=True),
            sa.Column(
                "source_execution_truth",
                sa.Integer(),
                nullable=False,
                server_default="1",
            ),
            sa.Column(
                "status", sa.String(length=16), nullable=False, server_default="ACTIVE"
            ),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disabled_by", sa.String(length=255), nullable=True),
            sa.Column("superseded_by_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.CheckConstraint(
                "status IN ('ACTIVE', 'DISABLED', 'SUPERSEDED')",
                name="ck_wc_capacity_source_status",
            ),
            sa.CheckConstraint(
                "over_allocation_policy IN "
                "('WARN_ONLY', 'HARD_BLOCK', 'ALLOW_WITH_REASON')",
                name="ck_wc_capacity_source_policy",
            ),
            sa.CheckConstraint(
                "source_label IN "
                "('OWNER_CONFIGURED', 'SYSTEM_DERIVED', 'AI_DECISION')",
                name="ck_wc_capacity_source_label",
            ),
            sa.CheckConstraint(
                "available_minutes >= 0",
                name="ck_wc_capacity_source_minutes_nonneg",
            ),
            sa.CheckConstraint("version >= 1", name="ck_wc_capacity_source_version"),
            sa.CheckConstraint(
                "length(trim(workcenter_code)) > 0",
                name="ck_wc_capacity_source_wc_nonblank",
            ),
            sa.CheckConstraint(
                "bucket_end > bucket_start",
                name="ck_wc_capacity_source_end_after_start",
            ),
            sa.CheckConstraint(
                "superseded_by_id IS NULL OR superseded_by_id != id",
                name="ck_wc_capacity_source_no_self_supersede",
            ),
            sa.ForeignKeyConstraint(
                ["superseded_by_id"],
                ["workcenter_capacity_sources.id"],
                ondelete="RESTRICT",
            ),
            sa.UniqueConstraint(
                "idempotency_key", name="uq_wc_capacity_source_idempotency"
            ),
        )
        op.create_index(
            "ix_wc_capacity_source_status",
            "workcenter_capacity_sources",
            ["status"],
        )
        op.create_index(
            "ix_wc_capacity_source_wc_day",
            "workcenter_capacity_sources",
            ["workcenter_code", "bucket_date"],
        )

    # One ACTIVE source per workcenter/day (SQLite partial unique).
    if _table_exists("workcenter_capacity_sources") and not _index_exists(
        "workcenter_capacity_sources", "uq_wc_capacity_source_active_wc_day"
    ):
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_wc_capacity_source_active_wc_day "
                "ON workcenter_capacity_sources (workcenter_code, bucket_date) "
                "WHERE status = 'ACTIVE'"
            )
        )

    if not _table_exists("workcenter_capacity_source_transitions"):
        op.create_table(
            "workcenter_capacity_source_transitions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("source_id", sa.Integer(), nullable=False),
            sa.Column("workcenter_code", sa.String(length=128), nullable=False),
            sa.Column("bucket_date", sa.Date(), nullable=False),
            sa.Column("operation", sa.String(length=64), nullable=False),
            sa.Column("previous_status", sa.String(length=16), nullable=True),
            sa.Column("new_status", sa.String(length=16), nullable=False),
            sa.Column("previous_available_minutes", sa.Integer(), nullable=True),
            sa.Column("new_available_minutes", sa.Integer(), nullable=True),
            sa.Column("previous_policy", sa.String(length=32), nullable=True),
            sa.Column("new_policy", sa.String(length=32), nullable=True),
            sa.Column("previous_version", sa.Integer(), nullable=True),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["source_id"],
                ["workcenter_capacity_sources.id"],
                ondelete="RESTRICT",
            ),
            sa.UniqueConstraint(
                "transition_id", name="uq_wc_capacity_source_tr_transition_id"
            ),
            sa.UniqueConstraint(
                "idempotency_key", name="uq_wc_capacity_source_tr_idempotency"
            ),
        )
        op.create_index(
            "ix_wc_capacity_source_tr_source_id",
            "workcenter_capacity_source_transitions",
            ["source_id"],
        )
        op.create_index(
            "ix_wc_capacity_source_tr_wc_day_created",
            "workcenter_capacity_source_transitions",
            ["workcenter_code", "bucket_date", "created_at"],
        )

    # Expand allocation tables with labeled workload (nullable for pre-Stage-1 rows).
    if _table_exists("execution_task_capacity_allocations"):
        if not _column_exists(
            "execution_task_capacity_allocations", "workload_source"
        ):
            op.add_column(
                "execution_task_capacity_allocations",
                sa.Column("workload_source", sa.String(length=64), nullable=True),
            )
        if not _column_exists(
            "execution_task_capacity_allocations", "workload_source_reference"
        ):
            op.add_column(
                "execution_task_capacity_allocations",
                sa.Column(
                    "workload_source_reference", sa.String(length=255), nullable=True
                ),
            )
        if not _column_exists(
            "execution_task_capacity_allocations", "workload_explanation"
        ):
            op.add_column(
                "execution_task_capacity_allocations",
                sa.Column("workload_explanation", sa.String(length=500), nullable=True),
            )

    if _table_exists("execution_task_capacity_allocation_transitions"):
        if not _column_exists(
            "execution_task_capacity_allocation_transitions", "workload_source"
        ):
            op.add_column(
                "execution_task_capacity_allocation_transitions",
                sa.Column("workload_source", sa.String(length=64), nullable=True),
            )
        if not _column_exists(
            "execution_task_capacity_allocation_transitions",
            "workload_source_reference",
        ):
            op.add_column(
                "execution_task_capacity_allocation_transitions",
                sa.Column(
                    "workload_source_reference", sa.String(length=255), nullable=True
                ),
            )
        if not _column_exists(
            "execution_task_capacity_allocation_transitions", "workload_explanation"
        ):
            op.add_column(
                "execution_task_capacity_allocation_transitions",
                sa.Column("workload_explanation", sa.String(length=500), nullable=True),
            )


def downgrade() -> None:
    """Isolated tests only — drop Stage-1 objects."""
    if _table_exists("execution_task_capacity_allocation_transitions"):
        for col in (
            "workload_explanation",
            "workload_source_reference",
            "workload_source",
        ):
            if _column_exists(
                "execution_task_capacity_allocation_transitions", col
            ):
                op.drop_column(
                    "execution_task_capacity_allocation_transitions", col
                )
    if _table_exists("execution_task_capacity_allocations"):
        for col in (
            "workload_explanation",
            "workload_source_reference",
            "workload_source",
        ):
            if _column_exists("execution_task_capacity_allocations", col):
                op.drop_column("execution_task_capacity_allocations", col)

    if _table_exists("workcenter_capacity_source_transitions"):
        op.drop_table("workcenter_capacity_source_transitions")

    if _table_exists("workcenter_capacity_sources"):
        if _index_exists(
            "workcenter_capacity_sources", "uq_wc_capacity_source_active_wc_day"
        ):
            op.execute(
                sa.text("DROP INDEX IF EXISTS uq_wc_capacity_source_active_wc_day")
            )
        op.drop_table("workcenter_capacity_sources")
