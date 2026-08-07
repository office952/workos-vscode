"""MACHINE_RUN execution status schema — RUNNING/COMPLETED + actual timestamps.

Revision ID: s67_machine_run_execution_status
Revises: s66_machine_run_reservation_grain
Create Date: 2026-08-07

EXPAND-ONLY (code schema; QA rollout NOT authorized):
  - extend machine_runs.status CHECK with RUNNING, COMPLETED
  - add nullable machine_runs.started_at / completed_at
  - ZERO START/COMPLETE runtime
  - ZERO Reservation status vocabulary change
  - ZERO QA activation / ZERO data backfill
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "s67_machine_run_execution_status"
down_revision: Union[str, Sequence[str], None] = "s66_machine_run_reservation_grain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_CHECK_OLD = (
    "status IN ('HELD', 'RESERVED', 'CANCELLED', 'RELEASED', 'SUPERSEDED')"
)
STATUS_CHECK_NEW = (
    "status IN ('HELD', 'RESERVED', 'RUNNING', 'COMPLETED', "
    "'CANCELLED', 'RELEASED', 'SUPERSEDED')"
)


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns(table_name)}
    return column_name in cols


def upgrade() -> None:
    if not _table_exists("machine_runs"):
        raise RuntimeError(
            "s67 upgrade requires machine_runs from s66_machine_run_reservation_grain"
        )

    # Child FKs (participants, transitions, reservations) require FK OFF
    # while batch recreate rewrites machine_runs.
    op.execute(sa.text("PRAGMA foreign_keys = OFF"))
    try:
        needs_status = True
        bind = op.get_bind()
        ddl = bind.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='machine_runs'"
            )
        ).scalar()
        if ddl and "RUNNING" in ddl and "COMPLETED" in ddl:
            needs_status = False

        needs_started = not _column_exists("machine_runs", "started_at")
        needs_completed = not _column_exists("machine_runs", "completed_at")

        if needs_status or needs_started or needs_completed:
            with op.batch_alter_table("machine_runs", recreate="always") as batch:
                if needs_started:
                    batch.add_column(
                        sa.Column(
                            "started_at",
                            sa.DateTime(timezone=True),
                            nullable=True,
                        )
                    )
                if needs_completed:
                    batch.add_column(
                        sa.Column(
                            "completed_at",
                            sa.DateTime(timezone=True),
                            nullable=True,
                        )
                    )
                if needs_status:
                    batch.drop_constraint("ck_machine_run_status", type_="check")
                    batch.create_check_constraint(
                        "ck_machine_run_status",
                        STATUS_CHECK_NEW,
                    )
    finally:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    if not _table_exists("machine_runs"):
        return

    bind = op.get_bind()
    exec_rows = bind.execute(
        text(
            "SELECT COUNT(*) FROM machine_runs "
            "WHERE status IN ('RUNNING', 'COMPLETED')"
        )
    ).scalar()
    if int(exec_rows or 0) > 0:
        raise RuntimeError(
            "s67 downgrade blocked: machine_runs with status "
            "RUNNING or COMPLETED present "
            "(no safe remap to commitment-only vocabulary)"
        )

    op.execute(sa.text("PRAGMA foreign_keys = OFF"))
    try:
        has_started = _column_exists("machine_runs", "started_at")
        has_completed = _column_exists("machine_runs", "completed_at")
        ddl = bind.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='machine_runs'"
            )
        ).scalar()
        has_new_check = bool(ddl and "RUNNING" in ddl and "COMPLETED" in ddl)

        if has_started or has_completed or has_new_check:
            with op.batch_alter_table("machine_runs", recreate="always") as batch:
                if has_new_check:
                    batch.drop_constraint("ck_machine_run_status", type_="check")
                    batch.create_check_constraint(
                        "ck_machine_run_status",
                        STATUS_CHECK_OLD,
                    )
                if has_completed:
                    batch.drop_column("completed_at")
                if has_started:
                    batch.drop_column("started_at")
    finally:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))
