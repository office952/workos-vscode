"""MACHINE_RUN tables + Reservation TASK|RUN owner grain (OPTION_B).

Revision ID: s66_machine_run_reservation_grain
Revises: s65_workcenter_capacity_source
Create Date: 2026-08-07

EXPAND:
  - create machine_runs / participants / transitions
  - reservation owner XOR (task XOR run)
  - reservation transition ownership snapshot
  - ZERO synthetic MACHINE_RUN backfill
  - existing reservations remain task-owned
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "s66_machine_run_reservation_grain"
down_revision: Union[str, Sequence[str], None] = "s65_workcenter_capacity_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OWNER_XOR_SQL = (
    "("
    "execution_plan_id IS NOT NULL AND task_key IS NOT NULL "
    "AND machine_run_id IS NULL"
    ") OR ("
    "execution_plan_id IS NULL AND task_key IS NULL "
    "AND machine_run_id IS NOT NULL"
    ")"
)

TR_OWNER_SNAPSHOT_SQL = (
    "("
    "owner_form = 'TASK' AND execution_plan_id IS NOT NULL "
    "AND task_key IS NOT NULL AND machine_run_id IS NULL"
    ") OR ("
    "owner_form = 'MACHINE_RUN' AND machine_run_id IS NOT NULL "
    "AND execution_plan_id IS NULL AND task_key IS NULL"
    ")"
)


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
    if not _table_exists("machine_runs"):
        op.create_table(
            "machine_runs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("machine_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_by", sa.String(length=255), nullable=True),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("released_by", sa.String(length=255), nullable=True),
            sa.Column("superseded_by_id", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=False),
            sa.CheckConstraint(
                "status IN ('HELD', 'RESERVED', 'CANCELLED', 'RELEASED', 'SUPERSEDED')",
                name="ck_machine_run_status",
            ),
            sa.CheckConstraint("version >= 1", name="ck_machine_run_version"),
            sa.CheckConstraint(
                "superseded_by_id IS NULL OR superseded_by_id != id",
                name="ck_machine_run_no_self_supersede",
            ),
            sa.ForeignKeyConstraint(
                ["machine_id"], ["machines.id"], ondelete="RESTRICT"
            ),
            sa.ForeignKeyConstraint(
                ["superseded_by_id"], ["machine_runs.id"], ondelete="RESTRICT"
            ),
            sa.UniqueConstraint(
                "idempotency_key", name="uq_machine_run_idempotency"
            ),
        )
    if not _index_exists("machine_runs", "ix_machine_run_status"):
        op.create_index("ix_machine_run_status", "machine_runs", ["status"])
    if not _index_exists("machine_runs", "ix_machine_run_machine_id"):
        op.create_index("ix_machine_run_machine_id", "machine_runs", ["machine_id"])

    if not _table_exists("machine_run_participants"):
        op.create_table(
            "machine_run_participants",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("machine_run_id", sa.Integer(), nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column(
                "status", sa.String(length=16), nullable=False, server_default="ACTIVE"
            ),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("added_by", sa.String(length=255), nullable=True),
            sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("removed_by", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=36), nullable=True),
            sa.CheckConstraint(
                "status IN ('ACTIVE', 'REMOVED')",
                name="ck_machine_run_participant_status",
            ),
            sa.CheckConstraint(
                "length(trim(task_key)) > 0",
                name="ck_machine_run_participant_task_key_nonblank",
            ),
            sa.ForeignKeyConstraint(
                ["machine_run_id"], ["machine_runs.id"], ondelete="RESTRICT"
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"], ["execution_plan.id"], ondelete="RESTRICT"
            ),
            sa.UniqueConstraint(
                "machine_run_id",
                "execution_plan_id",
                "task_key",
                name="uq_machine_run_participant_membership",
            ),
        )
    if not _index_exists(
        "machine_run_participants", "ix_machine_run_participant_plan_task"
    ):
        op.create_index(
            "ix_machine_run_participant_plan_task",
            "machine_run_participants",
            ["execution_plan_id", "task_key"],
        )
    if not _index_exists(
        "machine_run_participants", "uq_machine_run_participant_active_plan_task"
    ):
        op.create_index(
            "uq_machine_run_participant_active_plan_task",
            "machine_run_participants",
            ["execution_plan_id", "task_key"],
            unique=True,
            sqlite_where=sa.text("status = 'ACTIVE'"),
            postgresql_where=sa.text("status = 'ACTIVE'"),
        )

    if not _table_exists("machine_run_transitions"):
        op.create_table(
            "machine_run_transitions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("machine_run_id", sa.Integer(), nullable=False),
            sa.Column("machine_id", sa.Integer(), nullable=False),
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
            sa.ForeignKeyConstraint(
                ["machine_run_id"], ["machine_runs.id"], ondelete="RESTRICT"
            ),
            sa.UniqueConstraint(
                "transition_id", name="uq_machine_run_tr_transition_id"
            ),
            sa.UniqueConstraint(
                "idempotency_key", name="uq_machine_run_tr_idempotency"
            ),
        )
    if not _index_exists("machine_run_transitions", "ix_machine_run_tr_run_id"):
        op.create_index(
            "ix_machine_run_tr_run_id", "machine_run_transitions", ["machine_run_id"]
        )
    if not _index_exists("machine_run_transitions", "ix_machine_run_tr_run_created"):
        op.create_index(
            "ix_machine_run_tr_run_created",
            "machine_run_transitions",
            ["machine_run_id", "created_at"],
        )

    # SQLite batch recreate drops/renames tables; child FKs from transitions
    # require foreign_keys OFF on this connection for the duration.
    op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # Reservation grain: drop task open unique before table recreate so we can
    # replace its WHERE clause after owner columns exist.
    if _index_exists(
        "execution_task_machine_reservations",
        "uq_exec_task_machine_res_open_per_task_machine",
    ):
        op.drop_index(
            "uq_exec_task_machine_res_open_per_task_machine",
            table_name="execution_task_machine_reservations",
        )

    if _table_exists("execution_task_machine_reservations") and not _column_exists(
        "execution_task_machine_reservations", "machine_run_id"
    ):
        with op.batch_alter_table(
            "execution_task_machine_reservations", recreate="always"
        ) as batch:
            batch.add_column(sa.Column("machine_run_id", sa.Integer(), nullable=True))
            batch.alter_column(
                "execution_plan_id",
                existing_type=sa.Integer(),
                nullable=True,
            )
            batch.alter_column(
                "order_id",
                existing_type=sa.Integer(),
                nullable=True,
            )
            batch.alter_column(
                "task_key",
                existing_type=sa.String(length=512),
                nullable=True,
            )
            batch.create_foreign_key(
                "fk_exec_task_machine_res_machine_run_id",
                "machine_runs",
                ["machine_run_id"],
                ["id"],
                ondelete="RESTRICT",
            )
            batch.create_unique_constraint(
                "uq_exec_task_machine_res_machine_run_id",
                ["machine_run_id"],
            )
            # Replace nonblank CHECK with NULL-tolerant form + XOR.
            batch.drop_constraint(
                "ck_exec_task_machine_res_task_key_nonblank", type_="check"
            )
            batch.create_check_constraint(
                "ck_exec_task_machine_res_task_key_nonblank",
                "task_key IS NULL OR length(trim(task_key)) > 0",
            )
            batch.create_check_constraint(
                "ck_exec_task_machine_res_owner_xor",
                OWNER_XOR_SQL,
            )

    if not _index_exists(
        "execution_task_machine_reservations",
        "ix_exec_task_machine_res_machine_run_id",
    ):
        op.create_index(
            "ix_exec_task_machine_res_machine_run_id",
            "execution_task_machine_reservations",
            ["machine_run_id"],
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
            sqlite_where=sa.text(
                "status IN ('HELD', 'RESERVED') AND machine_run_id IS NULL"
            ),
            postgresql_where=sa.text(
                "status IN ('HELD', 'RESERVED') AND machine_run_id IS NULL"
            ),
        )

    if _table_exists(
        "execution_task_machine_reservation_transitions"
    ) and not _column_exists(
        "execution_task_machine_reservation_transitions", "owner_form"
    ):
        with op.batch_alter_table(
            "execution_task_machine_reservation_transitions", recreate="always"
        ) as batch:
            batch.add_column(
                sa.Column(
                    "owner_form",
                    sa.String(length=16),
                    nullable=False,
                    server_default="TASK",
                )
            )
            batch.add_column(sa.Column("machine_run_id", sa.Integer(), nullable=True))
            batch.alter_column(
                "execution_plan_id",
                existing_type=sa.Integer(),
                nullable=True,
            )
            batch.alter_column(
                "task_key",
                existing_type=sa.String(length=512),
                nullable=True,
            )
            batch.create_foreign_key(
                "fk_exec_task_machine_res_tr_machine_run_id",
                "machine_runs",
                ["machine_run_id"],
                ["id"],
                ondelete="RESTRICT",
            )
            batch.create_check_constraint(
                "ck_exec_task_machine_res_tr_owner_form",
                "owner_form IN ('TASK', 'MACHINE_RUN')",
            )
            batch.create_check_constraint(
                "ck_exec_task_machine_res_tr_owner_snapshot",
                TR_OWNER_SNAPSHOT_SQL,
            )

    if not _index_exists(
        "execution_task_machine_reservation_transitions",
        "ix_exec_task_machine_res_tr_machine_run_id",
    ):
        op.create_index(
            "ix_exec_task_machine_res_tr_machine_run_id",
            "execution_task_machine_reservation_transitions",
            ["machine_run_id"],
        )

    op.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    """Revert grain only when no run-owned reservations exist."""
    bind = op.get_bind()
    if _table_exists("execution_task_machine_reservations"):
        run_owned = bind.execute(
            text(
                "SELECT COUNT(*) FROM execution_task_machine_reservations "
                "WHERE machine_run_id IS NOT NULL"
            )
        ).scalar()
        if int(run_owned or 0) > 0:
            raise RuntimeError(
                "s66 downgrade blocked: run-owned reservations present"
            )

    op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    if _index_exists(
        "execution_task_machine_reservation_transitions",
        "ix_exec_task_machine_res_tr_machine_run_id",
    ):
        op.drop_index(
            "ix_exec_task_machine_res_tr_machine_run_id",
            table_name="execution_task_machine_reservation_transitions",
        )

    if _column_exists(
        "execution_task_machine_reservation_transitions", "owner_form"
    ):
        with op.batch_alter_table(
            "execution_task_machine_reservation_transitions", recreate="always"
        ) as batch:
            batch.drop_constraint(
                "ck_exec_task_machine_res_tr_owner_snapshot", type_="check"
            )
            batch.drop_constraint(
                "ck_exec_task_machine_res_tr_owner_form", type_="check"
            )
            batch.drop_constraint(
                "fk_exec_task_machine_res_tr_machine_run_id", type_="foreignkey"
            )
            batch.drop_column("machine_run_id")
            batch.drop_column("owner_form")
            batch.alter_column(
                "execution_plan_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
            batch.alter_column(
                "task_key",
                existing_type=sa.String(length=512),
                nullable=False,
            )

    if _index_exists(
        "execution_task_machine_reservations",
        "uq_exec_task_machine_res_open_per_task_machine",
    ):
        op.drop_index(
            "uq_exec_task_machine_res_open_per_task_machine",
            table_name="execution_task_machine_reservations",
        )
    if _index_exists(
        "execution_task_machine_reservations",
        "ix_exec_task_machine_res_machine_run_id",
    ):
        op.drop_index(
            "ix_exec_task_machine_res_machine_run_id",
            table_name="execution_task_machine_reservations",
        )

    if _column_exists("execution_task_machine_reservations", "machine_run_id"):
        with op.batch_alter_table(
            "execution_task_machine_reservations", recreate="always"
        ) as batch:
            batch.drop_constraint(
                "ck_exec_task_machine_res_owner_xor", type_="check"
            )
            batch.drop_constraint(
                "uq_exec_task_machine_res_machine_run_id", type_="unique"
            )
            batch.drop_constraint(
                "fk_exec_task_machine_res_machine_run_id", type_="foreignkey"
            )
            batch.drop_column("machine_run_id")
            batch.alter_column(
                "execution_plan_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
            batch.alter_column(
                "order_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
            batch.alter_column(
                "task_key",
                existing_type=sa.String(length=512),
                nullable=False,
            )
            batch.drop_constraint(
                "ck_exec_task_machine_res_task_key_nonblank", type_="check"
            )
            batch.create_check_constraint(
                "ck_exec_task_machine_res_task_key_nonblank",
                "length(trim(task_key)) > 0",
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

    for name in (
        "machine_run_transitions",
        "machine_run_participants",
        "machine_runs",
    ):
        if _table_exists(name):
            op.drop_table(name)

    op.execute(sa.text("PRAGMA foreign_keys = ON"))
