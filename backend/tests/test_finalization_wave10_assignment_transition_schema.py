"""Finalization Wave 10 / Phase A — transition schema + backfill (isolated DB).

Never touches protected QA fixture order 880750 / backend/dev.db.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.sqlite_pragma import register_sqlite_foreign_keys
from models.execution_task_assignment_transition import (
    REASON_NOTE_MAX_LEN,
    ExecutionTaskAssignmentTransition,
)
from services.assignment_transition_backfill_service import (
    BACKFILL_REASON_CODE,
    build_backfill_row,
    deterministic_legacy_backfill_transition_id,
    inventory_embedded_assignments,
    run_legacy_embedded_backfill,
)
from services.assignment_transition_consistency_service import (
    STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY,
    STATUS_CURRENT_STATE_MISMATCH,
    STATUS_MULTIPLE_INITIAL_BACKFILLS,
    STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY,
    evaluate_task_consistency,
    verify_plan_consistency,
)
from services.assignment_transition_repository import (
    APPEND_ONLY_ALLOWED_MUTATORS,
    FORBIDDEN_MUTATOR_NAMES,
    AssignmentTransitionAppendOnlyRepository,
    repository_public_mutation_methods,
)


def _ops_envelope(tasks: list[dict], *, planned: list | None = None) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": planned
            or [
                {
                    "task_key": "ignore_me",
                    "assigned_employee_id": 999,
                }
            ],
            "planned_operations": [
                {"op_key": "ignore_op", "assigned_employee_id": 998}
            ],
            "operational_tasks": tasks,
        }
    )


def _bootstrap_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'active',
                    employee_type VARCHAR NOT NULL DEFAULT 'internal',
                    salary_currency VARCHAR NOT NULL DEFAULT 'RON',
                    salary_period VARCHAR NOT NULL DEFAULT 'monthly'
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE execution_plan (
                    id INTEGER PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    order_code VARCHAR NOT NULL,
                    snapshot_version INTEGER NOT NULL,
                    tasks_json VARCHAR NOT NULL,
                    total_estimated_time_minutes FLOAT NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )


def _load_s63_module():
    import importlib.util

    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "s63_execution_task_assignment_transitions.py"
    )
    spec = importlib.util.spec_from_file_location(
        "s63_execution_task_assignment_transitions", path
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_s63_upgrade(engine) -> None:
    mod = _load_s63_module()
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            mod.upgrade()


def _run_s63_downgrade(engine) -> None:
    mod = _load_s63_module()
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            mod.downgrade()


def test_deterministic_transition_id_stable():
    a = deterministic_legacy_backfill_transition_id(
        execution_plan_id=23,
        task_key="node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
        assigned_employee_id=7,
        assignment_updated_at="2026-08-04T16:16:57.406324+00:00",
    )
    b = deterministic_legacy_backfill_transition_id(
        execution_plan_id=23,
        task_key="node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
        assigned_employee_id=7,
        assignment_updated_at="2026-08-04T16:16:57.406324+00:00",
    )
    assert a == b
    uuid.UUID(a)


def test_inventory_ignores_planned_and_counts_ops_only():
    rows = [
        {
            "id": 1,
            "order_id": 100,
            "tasks_json": _ops_envelope(
                [
                    {"task_id": "t1", "assigned_employee_id": 7},
                    {"task_id": "t2"},
                ]
            ),
            "updated_at": "2026-08-04 19:16:57.407320",
            "created_at": "2026-08-04 19:00:00",
        }
    ]
    inv = inventory_embedded_assignments(rows)
    assert inv.plans_scanned == 1
    assert inv.operational_tasks_scanned == 2
    assert inv.current_assignments_found == 1
    assert inv.expected_transition_rows == 1
    assert inv.malformed_assignment_states == 0
    assert inv.candidates[0].task_key == "t1"


def test_inventory_malformed_employee_type():
    rows = [
        {
            "id": 1,
            "order_id": 100,
            "tasks_json": _ops_envelope(
                [{"task_id": "t1", "assigned_employee_id": "7"}]
            ),
            "updated_at": "2026-08-04T00:00:00+00:00",
            "created_at": None,
        }
    ]
    inv = inventory_embedded_assignments(rows)
    assert inv.malformed_assignment_states == 1
    assert inv.expected_transition_rows == 0


def test_consistency_match_and_mismatch_and_multiple_backfill():
    match = evaluate_task_consistency(
        execution_plan_id=1,
        order_id=1,
        task_key="t1",
        embedded_assigned_employee_id=7,
        transitions=[
            {
                "transition_id": "a",
                "transition_type": "ASSIGN",
                "new_employee_id": 7,
                "source": "LEGACY_EMBEDDED_BACKFILL",
            }
        ],
    )
    assert match.status == STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY

    mismatch = evaluate_task_consistency(
        execution_plan_id=1,
        order_id=1,
        task_key="t1",
        embedded_assigned_employee_id=7,
        transitions=[
            {
                "transition_id": "a",
                "transition_type": "ASSIGN",
                "new_employee_id": 8,
                "source": "LEGACY_EMBEDDED_BACKFILL",
            }
        ],
    )
    assert mismatch.status == STATUS_CURRENT_STATE_MISMATCH

    multi = evaluate_task_consistency(
        execution_plan_id=1,
        order_id=1,
        task_key="t1",
        embedded_assigned_employee_id=7,
        transitions=[
            {
                "transition_id": "a",
                "transition_type": "ASSIGN",
                "new_employee_id": 7,
                "source": "LEGACY_EMBEDDED_BACKFILL",
            },
            {
                "transition_id": "b",
                "transition_type": "ASSIGN",
                "new_employee_id": 7,
                "source": "LEGACY_EMBEDDED_BACKFILL",
            },
        ],
    )
    assert multi.status == STATUS_MULTIPLE_INITIAL_BACKFILLS

    empty = evaluate_task_consistency(
        execution_plan_id=1,
        order_id=1,
        task_key="t2",
        embedded_assigned_employee_id=None,
        transitions=[],
    )
    assert empty.status == STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY


def test_migration_upgrade_backfill_idempotent_and_downgrade(tmp_path: Path):
    db_path = tmp_path / "phase_a.db"
    engine = create_engine(f"sqlite:///{db_path}")
    register_sqlite_foreign_keys(engine)
    _bootstrap_schema(engine)
    tasks_json = _ops_envelope(
        [
            {
                "task_id": "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
                "assigned_employee_id": 7,
                "assignment_actor_user_id": "dev-admin-user-00000000",
                "assignment_updated_at": "2026-08-04T16:16:57.406324+00:00",
                "assignment_source": "canonical_controlled_assign_v1",
            },
            {"task_id": "other_unassigned"},
        ]
    )
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO employees (id, name) VALUES (7, 'Andrei')")
        )
        conn.execute(
            text(
                """
                INSERT INTO execution_plan (
                    id, order_id, order_code, snapshot_version, tasks_json,
                    total_estimated_time_minutes, created_at, updated_at
                ) VALUES (
                    23, 880750, '880750', 1, :tj, 0,
                    '2026-08-04 16:00:00', '2026-08-04 19:16:57.407320'
                )
                """
            ),
            {"tj": tasks_json},
        )
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_before = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()

    _run_s63_upgrade(engine)

    with engine.begin() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
        ).scalar_one()
        assert count == 1
        row = conn.execute(
            text(
                "SELECT transition_type, previous_employee_id, new_employee_id, "
                "source, reason_code, actor_user_id, metadata_json "
                "FROM execution_task_assignment_transitions"
            )
        ).mappings().one()
        assert row["transition_type"] == "ASSIGN"
        assert row["previous_employee_id"] is None
        assert row["new_employee_id"] == 7
        assert row["source"] == "LEGACY_EMBEDDED_BACKFILL"
        assert row["reason_code"] == BACKFILL_REASON_CODE
        assert row["actor_user_id"] == "dev-admin-user-00000000"
        meta = json.loads(row["metadata_json"])
        assert meta["embedded_assignment_source"] == "canonical_controlled_assign_v1"
        assert "tasks_json" not in meta
        assert conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one() == sha_before
        assert (
            conn.execute(
                text("SELECT updated_at FROM execution_plan WHERE id=23")
            ).scalar_one()
            == upd_before
        )
        consistency = verify_plan_consistency(conn, execution_plan_id=23)
        assert consistency.fail_closed is False
        led = [
            t
            for t in consistency.tasks
            if t.task_key.endswith("led_install_letters")
        ][0]
        assert led.status == STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY

    # Idempotent re-run of upgrade/backfill path
    _run_s63_upgrade(engine)
    with engine.begin() as conn:
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
            ).scalar_one()
            == 1
        )

    _run_s63_downgrade(engine)
    with engine.begin() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        assert "execution_task_assignment_transitions" not in tables
        assert (
            conn.execute(
                text("SELECT tasks_json FROM execution_plan WHERE id=23")
            ).scalar_one()
            == sha_before
        )

    # upgrade after downgrade
    _run_s63_upgrade(engine)
    with engine.begin() as conn:
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
            ).scalar_one()
            == 1
        )


def test_backfill_zero_and_multiple_assignments(tmp_path: Path):
    db_path = tmp_path / "multi.db"
    engine = create_engine(f"sqlite:///{db_path}")
    register_sqlite_foreign_keys(engine)
    _bootstrap_schema(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO employees (id, name) VALUES (4, 'E4')"))
        conn.execute(text("INSERT INTO employees (id, name) VALUES (7, 'E7')"))
        conn.execute(
            text(
                """
                INSERT INTO execution_plan (
                    id, order_id, order_code, snapshot_version, tasks_json,
                    total_estimated_time_minutes, created_at, updated_at
                ) VALUES
                (1, 10, '10', 1, :tj1, 0, '2026-07-01', '2026-07-01'),
                (2, 20, '20', 1, :tj2, 0, '2026-07-02', '2026-07-02')
                """
            ),
            {
                "tj1": _ops_envelope(
                    [
                        {"task_id": "a", "assigned_employee_id": 4},
                        {"task_id": "b", "assigned_employee_id": 4},
                    ]
                ),
                "tj2": _ops_envelope([{"task_id": "c"}]),
            },
        )
    _run_s63_upgrade(engine)
    with engine.begin() as conn:
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
            ).scalar_one()
            == 2
        )
        report = run_legacy_embedded_backfill(conn)
        assert report.inserted == 0
        assert report.skipped_existing == 2


def test_unique_transition_id_and_invalid_type_rejected(tmp_path: Path):
    db_path = tmp_path / "constraints.db"
    engine = create_engine(f"sqlite:///{db_path}")
    register_sqlite_foreign_keys(engine)
    _bootstrap_schema(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO employees (id, name) VALUES (7, 'E7')"))
        conn.execute(
            text(
                """
                INSERT INTO execution_plan (
                    id, order_id, order_code, snapshot_version, tasks_json,
                    total_estimated_time_minutes, created_at, updated_at
                ) VALUES (1, 1, '1', 1, :tj, 0, '2026-08-01', '2026-08-01')
                """
            ),
            {"tj": _ops_envelope([])},
        )
    _run_s63_upgrade(engine)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(
            text(
                """
                INSERT INTO execution_task_assignment_transitions (
                    transition_id, execution_plan_id, order_id, task_key,
                    transition_type, previous_employee_id, new_employee_id,
                    source, created_at
                ) VALUES (
                    '11111111-1111-4111-8111-111111111111', 1, 1, 't',
                    'ASSIGN', NULL, 7, 'TEST', '2026-08-01T00:00:00+00:00'
                )
                """
            )
        )
        with pytest.raises(Exception):
            conn.execute(
                text(
                    """
                    INSERT INTO execution_task_assignment_transitions (
                        transition_id, execution_plan_id, order_id, task_key,
                        transition_type, previous_employee_id, new_employee_id,
                        source, created_at
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 1, 1, 't2',
                        'ASSIGN', NULL, 7, 'TEST', '2026-08-01T00:00:00+00:00'
                    )
                    """
                )
            )
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        with pytest.raises(Exception):
            conn.execute(
                text(
                    """
                    INSERT INTO execution_task_assignment_transitions (
                        transition_id, execution_plan_id, order_id, task_key,
                        transition_type, previous_employee_id, new_employee_id,
                        source, created_at
                    ) VALUES (
                        '22222222-2222-4222-8222-222222222222', 1, 1, 't3',
                        'NOT_A_TYPE', NULL, 7, 'TEST', '2026-08-01T00:00:00+00:00'
                    )
                    """
                )
            )


def test_append_only_repository_contract(db_fixture):
    methods = repository_public_mutation_methods()
    for forbidden in FORBIDDEN_MUTATOR_NAMES:
        assert forbidden not in methods
    assert "insert_transition" in methods
    assert APPEND_ONLY_ALLOWED_MUTATORS == {"insert_transition"}

    async def _run():
        async with db_fixture.session_maker() as session:
            from models.employees import Employees
            from models.execution_plan import ExecutionPlan
            from models.orders import Orders

            order = Orders(
                id=880_001,
                code="W10-880001",
                client_name="W10 Client",
                status="confirmed",
                snapshot_version=1,
                snapshot_line_items="[]",
            )
            session.add(order)
            await session.flush()
            emp = Employees(
                name="W10 Emp",
                status="active",
                employee_type="productive",
            )
            session.add(emp)
            await session.flush()
            plan = ExecutionPlan(
                order_id=order.id,
                order_code=order.code,
                snapshot_version=1,
                tasks_json=_ops_envelope([]),
                total_estimated_time_minutes=0.0,
            )
            session.add(plan)
            await session.flush()
            repo = AssignmentTransitionAppendOnlyRepository(session)
            row = ExecutionTaskAssignmentTransition(
                transition_id=str(uuid.uuid4()),
                execution_plan_id=plan.id,
                order_id=order.id,
                task_key="t_w10",
                transition_type="ASSIGN",
                previous_employee_id=None,
                new_employee_id=emp.id,
                reason_code=BACKFILL_REASON_CODE,
                source="TEST_APPEND",
                created_at=datetime.now(timezone.utc),
            )
            await repo.insert_transition(row)
            got = await repo.get_by_transition_id(row.transition_id)
            assert got is not None
            assert got.new_employee_id == emp.id
            listed = await repo.list_for_task(
                execution_plan_id=plan.id, task_key="t_w10"
            )
            assert len(listed) == 1
            await session.commit()

    db_fixture.run(_run())


def test_reason_note_limit_enforced(db_fixture):
    async def _run():
        async with db_fixture.session_maker() as session:
            repo = AssignmentTransitionAppendOnlyRepository(session)
            row = ExecutionTaskAssignmentTransition(
                transition_id=str(uuid.uuid4()),
                execution_plan_id=1,
                order_id=1,
                task_key="t",
                transition_type="ASSIGN",
                new_employee_id=1,
                reason_note="x" * (REASON_NOTE_MAX_LEN + 1),
                created_at=datetime.now(timezone.utc),
            )
            with pytest.raises(ValueError, match="reason_note_exceeds_max_length"):
                await repo.insert_transition(row)

    db_fixture.run(_run())


def test_build_backfill_preserves_null_actor_and_timestamp_fallback():
    from services.assignment_transition_backfill_service import (
        EmbeddedAssignmentCandidate,
    )

    candidate = EmbeddedAssignmentCandidate(
        execution_plan_id=4,
        order_id=23099,
        task_key="t",
        assigned_employee_id=4,
        assignment_actor_user_id=None,
        assignment_updated_at=None,
        assignment_source=None,
        plan_updated_at="2026-07-15 03:56:39.431647",
        plan_created_at="2026-07-15 03:00:00",
    )
    row = build_backfill_row(candidate)
    assert row["actor_user_id"] is None
    assert row["metadata_json"] is None
    assert row["source"] == "LEGACY_EMBEDDED_BACKFILL"
    assert row["created_at"].year == 2026


def test_no_reassignment_routes_registered():
    from main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert not any("/reassign" in p for p in paths)
    assert not any("/unassign" in p for p in paths)
