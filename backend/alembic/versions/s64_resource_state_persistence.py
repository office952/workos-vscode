"""Resource State Program R3 — eight-table expand-only persistence.

Revision ID: s64_resource_state_persistence
Revises: s63_execution_task_assignment_transitions
Create Date: 2026-08-05

EXPAND-ONLY:
  - create Resource State current-state + transition tables
  - CHECK / UNIQUE / FK / indexes (including partial unique open rows)
  - ZERO inserts / ZERO backfill / ZERO configuration activation
  - does NOT mutate execution_plan / tasks_json / assignment transitions
  - does NOT imply CLEAR

Downgrade (isolated tests only): drop s64-owned objects only.
Operational downgrade after real Resource State rows exist requires Owner GO.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "s64_resource_state_persistence"
down_revision: Union[str, Sequence[str], None] = (
    "s63_execution_task_assignment_transitions"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESOURCE_STATE_TABLES_CREATE_ORDER = (
    "resource_domain_configurations",
    "resource_domain_configuration_transitions",
    "execution_task_schedules",
    "execution_task_schedule_transitions",
    "execution_task_machine_reservations",
    "execution_task_machine_reservation_transitions",
    "execution_task_capacity_allocations",
    "execution_task_capacity_allocation_transitions",
)


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(inspect(bind).get_table_names())


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    if table_name not in set(inspect(bind).get_table_names()):
        return False
    return any(ix.get("name") == index_name for ix in inspect(bind).get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("resource_domain_configurations"):
        op.create_table(
            "resource_domain_configurations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("domain", sa.String(length=32), nullable=False),
            sa.Column(
                "application_scope_key",
                sa.String(length=64),
                nullable=False,
                server_default="application",
            ),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("configured_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("configured_by", sa.String(length=255), nullable=True),
            sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disabled_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "domain IN ('SCHEDULING', 'MACHINE_RESERVATION', 'CAPACITY_ALLOCATION')",
                name="ck_resource_domain_config_domain",
            ),
            sa.CheckConstraint(
                "status IN ('ACTIVE', 'DISABLED')",
                name="ck_resource_domain_config_status",
            ),
            sa.CheckConstraint(
                "version >= 1",
                name="ck_resource_domain_config_version",
            ),
            sa.CheckConstraint(
                "("
                "status = 'ACTIVE' AND configured_at IS NOT NULL"
                ") OR ("
                "status = 'DISABLED' AND disabled_at IS NOT NULL"
                ")",
                name="ck_resource_domain_config_status_timestamps",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "domain",
                "application_scope_key",
                name="uq_resource_domain_config_domain_scope",
            ),
        )
    if not _index_exists(
        "resource_domain_configurations", "ix_resource_domain_config_domain_scope"
    ):
        op.create_index(
            "ix_resource_domain_config_domain_scope",
            "resource_domain_configurations",
            ["domain", "application_scope_key"],
            unique=False,
        )
    if not _index_exists(
        "resource_domain_configurations", "ix_resource_domain_config_status"
    ):
        op.create_index(
            "ix_resource_domain_config_status",
            "resource_domain_configurations",
            ["status"],
            unique=False,
        )

    if not _table_exists("resource_domain_configuration_transitions"):
        op.create_table(
            "resource_domain_configuration_transitions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("configuration_id", sa.Integer(), nullable=False),
            sa.Column("domain", sa.String(length=32), nullable=False),
            sa.Column("operation", sa.String(length=64), nullable=False),
            sa.Column("previous_status", sa.String(length=16), nullable=True),
            sa.Column("new_status", sa.String(length=16), nullable=False),
            sa.Column("previous_version", sa.Integer(), nullable=True),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "domain IN ('SCHEDULING', 'MACHINE_RESERVATION', 'CAPACITY_ALLOCATION')",
                name="ck_resource_domain_config_tr_domain",
            ),
            sa.CheckConstraint(
                "previous_status IN ('ACTIVE', 'DISABLED') OR previous_status IS NULL",
                name="ck_resource_domain_config_tr_prev_status",
            ),
            sa.CheckConstraint(
                "new_status IN ('ACTIVE', 'DISABLED')",
                name="ck_resource_domain_config_tr_new_status",
            ),
            sa.ForeignKeyConstraint(
                ["configuration_id"],
                ["resource_domain_configurations.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "transition_id",
                name="uq_resource_domain_config_tr_transition_id",
            ),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_resource_domain_config_tr_idempotency",
            ),
        )
    if not _index_exists(
        "resource_domain_configuration_transitions",
        "ix_resource_domain_config_tr_configuration_id",
    ):
        op.create_index(
            "ix_resource_domain_config_tr_configuration_id",
            "resource_domain_configuration_transitions",
            ["configuration_id"],
            unique=False,
        )
    if not _index_exists(
        "resource_domain_configuration_transitions",
        "ix_resource_domain_config_tr_created_at",
    ):
        op.create_index(
            "ix_resource_domain_config_tr_created_at",
            "resource_domain_configuration_transitions",
            ["created_at"],
            unique=False,
        )

    if not _table_exists("execution_task_schedules"):
        op.create_table(
            "execution_task_schedules",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("workcenter_code", sa.String(length=128), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_by", sa.String(length=255), nullable=True),
            sa.Column("superseded_by_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.CheckConstraint(
                "status IN ('DRAFT', 'PLANNED', 'CONFIRMED', 'CANCELLED', 'SUPERSEDED')",
                name="ck_exec_task_schedule_status",
            ),
            sa.CheckConstraint(
                "version >= 1",
                name="ck_exec_task_schedule_version",
            ),
            sa.CheckConstraint(
                "length(trim(task_key)) > 0",
                name="ck_exec_task_schedule_task_key_nonblank",
            ),
            sa.CheckConstraint(
                "scheduled_end > scheduled_start",
                name="ck_exec_task_schedule_end_after_start",
            ),
            sa.CheckConstraint(
                "superseded_by_id IS NULL OR superseded_by_id != id",
                name="ck_exec_task_schedule_no_self_supersede",
            ),
            sa.CheckConstraint(
                "("
                "status != 'CANCELLED'"
                ") OR ("
                "status = 'CANCELLED' AND cancelled_at IS NOT NULL"
                ")",
                name="ck_exec_task_schedule_cancel_timestamp",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["superseded_by_id"],
                ["execution_task_schedules.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_schedule_idempotency",
            ),
        )
    if not _index_exists("execution_task_schedules", "ix_exec_task_schedule_plan_task"):
        op.create_index(
            "ix_exec_task_schedule_plan_task",
            "execution_task_schedules",
            ["execution_plan_id", "task_key"],
            unique=False,
        )
    if not _index_exists("execution_task_schedules", "ix_exec_task_schedule_status"):
        op.create_index(
            "ix_exec_task_schedule_status",
            "execution_task_schedules",
            ["status"],
            unique=False,
        )
    if not _index_exists("execution_task_schedules", "ix_exec_task_schedule_window"):
        op.create_index(
            "ix_exec_task_schedule_window",
            "execution_task_schedules",
            ["scheduled_start", "scheduled_end"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_schedules", "uq_exec_task_schedule_open_per_task"
    ):
        op.create_index(
            "uq_exec_task_schedule_open_per_task",
            "execution_task_schedules",
            ["execution_plan_id", "task_key"],
            unique=True,
            sqlite_where=sa.text("status IN ('DRAFT', 'PLANNED', 'CONFIRMED')"),
            postgresql_where=sa.text("status IN ('DRAFT', 'PLANNED', 'CONFIRMED')"),
        )

    if not _table_exists("execution_task_schedule_transitions"):
        op.create_table(
            "execution_task_schedule_transitions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("schedule_id", sa.Integer(), nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("operation", sa.String(length=64), nullable=False),
            sa.Column("previous_status", sa.String(length=16), nullable=True),
            sa.Column("new_status", sa.String(length=16), nullable=False),
            sa.Column("previous_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("previous_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("previous_version", sa.Integer(), nullable=True),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["schedule_id"],
                ["execution_task_schedules.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "transition_id",
                name="uq_exec_task_schedule_tr_transition_id",
            ),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_schedule_tr_idempotency",
            ),
        )
    if not _index_exists(
        "execution_task_schedule_transitions", "ix_exec_task_schedule_tr_schedule_id"
    ):
        op.create_index(
            "ix_exec_task_schedule_tr_schedule_id",
            "execution_task_schedule_transitions",
            ["schedule_id"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_schedule_transitions",
        "ix_exec_task_schedule_tr_plan_task_created",
    ):
        op.create_index(
            "ix_exec_task_schedule_tr_plan_task_created",
            "execution_task_schedule_transitions",
            ["execution_plan_id", "task_key", "created_at"],
            unique=False,
        )

    if not _table_exists("execution_task_machine_reservations"):
        op.create_table(
            "execution_task_machine_reservations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("machine_id", sa.Integer(), nullable=False),
            sa.Column("reservation_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reservation_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("released_by", sa.String(length=255), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_by", sa.String(length=255), nullable=True),
            sa.Column("superseded_by_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.CheckConstraint(
                "status IN ('HELD', 'RESERVED', 'CANCELLED', 'RELEASED', 'SUPERSEDED')",
                name="ck_exec_task_machine_res_status",
            ),
            sa.CheckConstraint(
                "version >= 1",
                name="ck_exec_task_machine_res_version",
            ),
            sa.CheckConstraint(
                "length(trim(task_key)) > 0",
                name="ck_exec_task_machine_res_task_key_nonblank",
            ),
            sa.CheckConstraint(
                "reservation_end > reservation_start",
                name="ck_exec_task_machine_res_end_after_start",
            ),
            sa.CheckConstraint(
                "superseded_by_id IS NULL OR superseded_by_id != id",
                name="ck_exec_task_machine_res_no_self_supersede",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["machine_id"],
                ["machines.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["superseded_by_id"],
                ["execution_task_machine_reservations.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_machine_res_idempotency",
            ),
        )
    if not _index_exists(
        "execution_task_machine_reservations", "ix_exec_task_machine_res_plan_task"
    ):
        op.create_index(
            "ix_exec_task_machine_res_plan_task",
            "execution_task_machine_reservations",
            ["execution_plan_id", "task_key"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_machine_reservations", "ix_exec_task_machine_res_status"
    ):
        op.create_index(
            "ix_exec_task_machine_res_status",
            "execution_task_machine_reservations",
            ["status"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_machine_reservations",
        "ix_exec_task_machine_res_machine_window",
    ):
        op.create_index(
            "ix_exec_task_machine_res_machine_window",
            "execution_task_machine_reservations",
            ["machine_id", "reservation_start", "reservation_end"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_machine_reservations",
        "uq_exec_task_machine_res_open_per_task_machine",
    ):
        op.create_index(
            "uq_exec_task_machine_res_open_per_task_machine",
            "execution_task_machine_reservations",
            ["execution_plan_id", "task_key", "machine_id"],
            unique=True,
            sqlite_where=sa.text("status IN ('HELD', 'RESERVED')"),
            postgresql_where=sa.text("status IN ('HELD', 'RESERVED')"),
        )

    if not _table_exists("execution_task_machine_reservation_transitions"):
        op.create_table(
            "execution_task_machine_reservation_transitions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("reservation_id", sa.Integer(), nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("machine_id", sa.Integer(), nullable=False),
            sa.Column("operation", sa.String(length=64), nullable=False),
            sa.Column("previous_status", sa.String(length=16), nullable=True),
            sa.Column("new_status", sa.String(length=16), nullable=False),
            sa.Column("previous_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("previous_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("previous_version", sa.Integer(), nullable=True),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["reservation_id"],
                ["execution_task_machine_reservations.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "transition_id",
                name="uq_exec_task_machine_res_tr_transition_id",
            ),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_machine_res_tr_idempotency",
            ),
        )
    if not _index_exists(
        "execution_task_machine_reservation_transitions",
        "ix_exec_task_machine_res_tr_reservation_id",
    ):
        op.create_index(
            "ix_exec_task_machine_res_tr_reservation_id",
            "execution_task_machine_reservation_transitions",
            ["reservation_id"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_machine_reservation_transitions",
        "ix_exec_task_machine_res_tr_plan_task_created",
    ):
        op.create_index(
            "ix_exec_task_machine_res_tr_plan_task_created",
            "execution_task_machine_reservation_transitions",
            ["execution_plan_id", "task_key", "created_at"],
            unique=False,
        )

    if not _table_exists("execution_task_capacity_allocations"):
        op.create_table(
            "execution_task_capacity_allocations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("resource_scope_type", sa.String(length=32), nullable=False),
            sa.Column("resource_scope_id", sa.String(length=128), nullable=False),
            sa.Column("workcenter_code", sa.String(length=128), nullable=True),
            sa.Column("machine_id", sa.Integer(), nullable=True),
            sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column(
                "unit",
                sa.String(length=16),
                nullable=False,
                server_default="minutes",
            ),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("superseded_by_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.CheckConstraint(
                "resource_scope_type IN ('WORKCENTER', 'MACHINE')",
                name="ck_exec_task_capacity_alloc_scope_type",
            ),
            sa.CheckConstraint(
                "status IN ('HELD', 'ALLOCATED', 'RELEASED', 'CANCELLED', 'SUPERSEDED')",
                name="ck_exec_task_capacity_alloc_status",
            ),
            sa.CheckConstraint(
                "unit = 'minutes'",
                name="ck_exec_task_capacity_alloc_unit",
            ),
            sa.CheckConstraint(
                "quantity > 0",
                name="ck_exec_task_capacity_alloc_quantity",
            ),
            sa.CheckConstraint(
                "version >= 1",
                name="ck_exec_task_capacity_alloc_version",
            ),
            sa.CheckConstraint(
                "length(trim(task_key)) > 0",
                name="ck_exec_task_capacity_alloc_task_key_nonblank",
            ),
            sa.CheckConstraint(
                "length(trim(resource_scope_id)) > 0",
                name="ck_exec_task_capacity_alloc_scope_id_nonblank",
            ),
            sa.CheckConstraint(
                "bucket_end > bucket_start",
                name="ck_exec_task_capacity_alloc_end_after_start",
            ),
            sa.CheckConstraint(
                "superseded_by_id IS NULL OR superseded_by_id != id",
                name="ck_exec_task_capacity_alloc_no_self_supersede",
            ),
            sa.CheckConstraint(
                "("
                "resource_scope_type = 'WORKCENTER' "
                "AND workcenter_code IS NOT NULL "
                "AND machine_id IS NULL"
                ") OR ("
                "resource_scope_type = 'MACHINE' "
                "AND machine_id IS NOT NULL "
                "AND workcenter_code IS NULL"
                ")",
                name="ck_exec_task_capacity_alloc_scope_xor",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["machine_id"],
                ["machines.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["superseded_by_id"],
                ["execution_task_capacity_allocations.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_capacity_alloc_idempotency",
            ),
        )
    if not _index_exists(
        "execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_plan_task"
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_plan_task",
            "execution_task_capacity_allocations",
            ["execution_plan_id", "task_key"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_status"
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_status",
            "execution_task_capacity_allocations",
            ["status"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_wc_bucket"
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_wc_bucket",
            "execution_task_capacity_allocations",
            ["workcenter_code", "bucket_start", "bucket_end"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_capacity_allocations",
        "ix_exec_task_capacity_alloc_machine_bucket",
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_machine_bucket",
            "execution_task_capacity_allocations",
            ["machine_id", "bucket_start", "bucket_end"],
            unique=False,
        )

    if not _table_exists("execution_task_capacity_allocation_transitions"):
        op.create_table(
            "execution_task_capacity_allocation_transitions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("allocation_id", sa.Integer(), nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("resource_scope_type", sa.String(length=32), nullable=False),
            sa.Column("resource_scope_id", sa.String(length=128), nullable=False),
            sa.Column("operation", sa.String(length=64), nullable=False),
            sa.Column("previous_status", sa.String(length=16), nullable=True),
            sa.Column("new_status", sa.String(length=16), nullable=False),
            sa.Column("previous_quantity", sa.Integer(), nullable=True),
            sa.Column("new_quantity", sa.Integer(), nullable=True),
            sa.Column(
                "unit",
                sa.String(length=16),
                nullable=False,
                server_default="minutes",
            ),
            sa.Column(
                "previous_bucket_start", sa.DateTime(timezone=True), nullable=True
            ),
            sa.Column("previous_bucket_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_bucket_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("new_bucket_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("previous_version", sa.Integer(), nullable=True),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["allocation_id"],
                ["execution_task_capacity_allocations.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "transition_id",
                name="uq_exec_task_capacity_alloc_tr_transition_id",
            ),
            sa.UniqueConstraint(
                "idempotency_key",
                name="uq_exec_task_capacity_alloc_tr_idempotency",
            ),
        )
    if not _index_exists(
        "execution_task_capacity_allocation_transitions",
        "ix_exec_task_capacity_alloc_tr_allocation_id",
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_tr_allocation_id",
            "execution_task_capacity_allocation_transitions",
            ["allocation_id"],
            unique=False,
        )
    if not _index_exists(
        "execution_task_capacity_allocation_transitions",
        "ix_exec_task_capacity_alloc_tr_plan_task_created",
    ):
        op.create_index(
            "ix_exec_task_capacity_alloc_tr_plan_task_created",
            "execution_task_capacity_allocation_transitions",
            ["execution_plan_id", "task_key", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    # Reverse dependency order — drop transitions before current-state tables.
    drop_order = list(reversed(RESOURCE_STATE_TABLES_CREATE_ORDER))
    index_drops: list[tuple[str, str]] = [
        (
            "execution_task_capacity_allocation_transitions",
            "ix_exec_task_capacity_alloc_tr_plan_task_created",
        ),
        (
            "execution_task_capacity_allocation_transitions",
            "ix_exec_task_capacity_alloc_tr_allocation_id",
        ),
        (
            "execution_task_capacity_allocations",
            "ix_exec_task_capacity_alloc_machine_bucket",
        ),
        ("execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_wc_bucket"),
        ("execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_status"),
        ("execution_task_capacity_allocations", "ix_exec_task_capacity_alloc_plan_task"),
        (
            "execution_task_machine_reservation_transitions",
            "ix_exec_task_machine_res_tr_plan_task_created",
        ),
        (
            "execution_task_machine_reservation_transitions",
            "ix_exec_task_machine_res_tr_reservation_id",
        ),
        (
            "execution_task_machine_reservations",
            "uq_exec_task_machine_res_open_per_task_machine",
        ),
        (
            "execution_task_machine_reservations",
            "ix_exec_task_machine_res_machine_window",
        ),
        ("execution_task_machine_reservations", "ix_exec_task_machine_res_status"),
        ("execution_task_machine_reservations", "ix_exec_task_machine_res_plan_task"),
        (
            "execution_task_schedule_transitions",
            "ix_exec_task_schedule_tr_plan_task_created",
        ),
        ("execution_task_schedule_transitions", "ix_exec_task_schedule_tr_schedule_id"),
        ("execution_task_schedules", "uq_exec_task_schedule_open_per_task"),
        ("execution_task_schedules", "ix_exec_task_schedule_window"),
        ("execution_task_schedules", "ix_exec_task_schedule_status"),
        ("execution_task_schedules", "ix_exec_task_schedule_plan_task"),
        (
            "resource_domain_configuration_transitions",
            "ix_resource_domain_config_tr_created_at",
        ),
        (
            "resource_domain_configuration_transitions",
            "ix_resource_domain_config_tr_configuration_id",
        ),
        ("resource_domain_configurations", "ix_resource_domain_config_status"),
        ("resource_domain_configurations", "ix_resource_domain_config_domain_scope"),
    ]
    for table_name, index_name in index_drops:
        if _index_exists(table_name, index_name):
            op.drop_index(index_name, table_name=table_name)
    for table_name in drop_order:
        if _table_exists(table_name):
            op.drop_table(table_name)
