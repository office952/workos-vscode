"""Phase A — execution_task_assignment_transitions + legacy backfill.

Revision ID: s63_execution_task_assignment_transitions
Revises: s62_material_actuals_closed_job_v1
Create Date: 2026-08-04

EXPAND-ONLY:
  - create append-only transition history table
  - indexes / unique / check constraints
  - synthetic ASSIGN backfill for current embedded assignments
  - does NOT mutate execution_plan.tasks_json or assigned_employee_id
  - does NOT add reassignment/unassignment commands
  - does NOT write alembic_version (Alembic CLI/stamp owns revision stamping)

``_table_exists`` skip-create path is intentional recovery compatibility when a
prior runtime ``create_all`` already materialized the table. That path verifies
column parity and creates only missing canonical indexes — it does not stamp
revisions and does not drop legacy ORM duplicate index names (Owner GO required).

Downgrade (pre-Phase B only): drop Phase A objects; never unassign.
Downgrade destroys backfilled history — allowed only before Phase B / real
transition usage, never on protected QA without Owner GO.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "s63_execution_task_assignment_transitions"
down_revision: Union[str, Sequence[str], None] = "s62_material_actuals_closed_job_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EXPECTED_COLUMNS = frozenset(
    {
        "id",
        "transition_id",
        "execution_plan_id",
        "order_id",
        "task_key",
        "transition_type",
        "previous_employee_id",
        "new_employee_id",
        "actor_user_id",
        "actor_role",
        "reason_code",
        "reason_note",
        "task_state_at_transition",
        "eligibility_decision_code",
        "eligibility_provenance",
        "request_id",
        "correlation_id",
        "expected_current_employee_id",
        "source",
        "command_version",
        "metadata_json",
        "created_at",
    }
)

_CANONICAL_INDEXES = (
    ("ix_exec_task_assign_tr_transition_id", ["transition_id"], False),
    ("ix_exec_task_assign_tr_plan_id", ["execution_plan_id"], False),
    ("ix_exec_task_assign_tr_order_id", ["order_id"], False),
    ("ix_exec_task_assign_tr_task_key", ["task_key"], False),
    ("ix_exec_task_assign_tr_source", ["source"], False),
    (
        "ix_exec_task_assign_tr_plan_task_id",
        ["execution_plan_id", "task_key", "id"],
        False,
    ),
)


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(inspect(bind).get_table_names())


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    if table_name not in set(inspect(bind).get_table_names()):
        return False
    return any(ix.get("name") == index_name for ix in inspect(bind).get_indexes(table_name))


def _verify_existing_table_parity() -> None:
    """Fail closed if a pre-existing (e.g. create_all) table lacks expected columns."""
    bind = op.get_bind()
    cols = {
        c["name"]
        for c in inspect(bind).get_columns("execution_task_assignment_transitions")
    }
    missing = sorted(_EXPECTED_COLUMNS - cols)
    if missing:
        raise RuntimeError(
            "execution_task_assignment_transitions exists but fails schema parity "
            f"(missing columns: {missing}). Manual recovery required — do not "
            "stamp alembic_version until parity is restored via audited tooling."
        )


def upgrade() -> None:
    if not _table_exists("execution_task_assignment_transitions"):
        op.create_table(
            "execution_task_assignment_transitions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("transition_id", sa.String(length=36), nullable=False),
            sa.Column("execution_plan_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("task_key", sa.String(length=512), nullable=False),
            sa.Column("transition_type", sa.String(length=16), nullable=False),
            sa.Column("previous_employee_id", sa.Integer(), nullable=True),
            sa.Column("new_employee_id", sa.Integer(), nullable=True),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("actor_role", sa.String(length=50), nullable=True),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("reason_note", sa.String(length=500), nullable=True),
            sa.Column("task_state_at_transition", sa.String(length=64), nullable=True),
            sa.Column("eligibility_decision_code", sa.String(length=64), nullable=True),
            sa.Column("eligibility_provenance", sa.String(length=128), nullable=True),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("expected_current_employee_id", sa.Integer(), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("command_version", sa.String(length=32), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "transition_type IN ('ASSIGN', 'REASSIGN', 'UNASSIGN')",
                name="ck_exec_task_assign_transition_type",
            ),
            sa.CheckConstraint(
                "("
                "transition_type = 'UNASSIGN' AND new_employee_id IS NULL"
                ") OR ("
                "transition_type IN ('ASSIGN', 'REASSIGN') "
                "AND new_employee_id IS NOT NULL"
                ")",
                name="ck_exec_task_assign_transition_employee_shape",
            ),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"],
                ["execution_plan.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["previous_employee_id"],
                ["employees.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["new_employee_id"],
                ["employees.id"],
                ondelete="RESTRICT",
            ),
            # actor_user_id intentionally denormalized (no FK): users table is
            # excluded from Alembic include_object; missing actors must not
            # block historical backfill rows.
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "transition_id",
                name="uq_exec_task_assign_transition_id",
            ),
        )
    else:
        # Recovery compatibility: table already present (historically via create_all).
        # Verify parity; never invent columns or stamp revision here.
        _verify_existing_table_parity()

    for name, cols, unique in _CANONICAL_INDEXES:
        if not _index_exists("execution_task_assignment_transitions", name):
            op.create_index(
                name,
                "execution_task_assignment_transitions",
                cols,
                unique=unique,
            )

    # Controlled backfill — never rewrites tasks_json.
    from services.assignment_transition_backfill_service import (
        run_legacy_embedded_backfill,
    )
    from services.assignment_transition_consistency_service import (
        verify_plan_consistency,
    )

    bind = op.get_bind()
    report = run_legacy_embedded_backfill(bind)
    if report.errors:
        raise RuntimeError(
            "Phase A backfill aborted: " + "; ".join(report.errors[:5])
        )
    consistency = verify_plan_consistency(bind)
    if consistency.fail_closed:
        mismatches = [
            t
            for t in consistency.tasks
            if t.status
            in (
                "CURRENT_STATE_MISMATCH",
                "MULTIPLE_INITIAL_BACKFILLS",
                "MALFORMED_TRANSITION_SEQUENCE",
                "UNKNOWN",
            )
        ]
        sample = mismatches[:5]
        raise RuntimeError(
            "Phase A consistency verification failed (fail-closed): "
            + "; ".join(
                f"plan={m.execution_plan_id} task={m.task_key} status={m.status}"
                for m in sample
            )
        )


def downgrade() -> None:
    """Pre-Phase B only: drop Phase A objects. Never mutates tasks_json."""
    if not _table_exists("execution_task_assignment_transitions"):
        return
    # Drop indexes explicitly for dialects that need it; drop_table cascades most.
    for name in (
        "ix_exec_task_assign_tr_plan_task_id",
        "ix_exec_task_assign_tr_source",
        "ix_exec_task_assign_tr_task_key",
        "ix_exec_task_assign_tr_order_id",
        "ix_exec_task_assign_tr_plan_id",
        "ix_exec_task_assign_tr_transition_id",
    ):
        if _index_exists("execution_task_assignment_transitions", name):
            op.drop_index(name, table_name="execution_task_assignment_transitions")
    op.drop_table("execution_task_assignment_transitions")
    # Prove we did not touch plans (no-op SELECT for reviewer visibility).
    op.get_bind().execute(text("SELECT COUNT(*) FROM execution_plan"))
