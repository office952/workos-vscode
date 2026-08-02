"""F7C — Operational Resource Readiness: ORR allow-list ∩ machines registry (read-only).

Owner mandatory cases:
  - WC_CNC_ROUTING resolves canonically
  - WC_CNC does not silently pass
  - unknown workcenter -> warning not guessed mapping
  - machine-required not falsely ready when none compatible
  - workcenter-only / work_area-only not falsely blocked for missing machine
  - capacity warning != commercial blocker
  - GET creates no assignments/sessions
  - commercial/snapshot unchanged (read-only proof)
  - materialization gate remains closed
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.operational_registry import MachineRegistry, OperationResourceRequirement
from schemas.operational_resource_readiness import BLOCKED_STATUSES
from services.dec009_materialize_gate import (
    LIVE_DEC009_STATUS,
    evaluate_materialize_authorization,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.operational_resource_readiness_service import (
    build_operational_resource_readiness,
)
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_f7a_product_linked_task_contract_enrichment import (
    COMMERCIAL_TOTAL,
    _f7a_oid,
    _f7a_snapshot_json,
)


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return SimpleNamespace(all=lambda: self._value)


def _plan_db(envelope: dict, *, machines: list[MachineRegistry] | None = None):
    plan = SimpleNamespace(id=99, tasks_json=json.dumps(envelope))
    machines = machines or []
    db = AsyncMock()

    async def execute(stmt):
        sql = str(stmt).lower()
        if "execution_plan" in sql:
            return _FakeResult(plan)
        if "machines" in sql:
            return _FakeResult(machines)
        return _FakeResult(None)

    db.execute = execute
    return db, plan


def _machine(code: str, *, kind: str = "machine", active: bool = True, wc: str | None = None):
    return SimpleNamespace(
        machine_code=code,
        name=code,
        resource_kind=kind,
        workcenter_code=wc,
        is_active=active,
        is_available=True,
        operational_status="active" if active else "maintenance",
    )


class _FakeRegistry:
    def __init__(self, mappings: dict[str, dict]):
        self._mappings = mappings

    async def resolve_operation_mapping(self, operation_code: str):
        return self._mappings.get((operation_code or "").lower())


def _patch_registry(monkeypatch, mappings: dict[str, dict]):
    monkeypatch.setattr(
        "services.operational_resource_readiness_service.OperationalRegistryService",
        lambda db: _FakeRegistry(mappings),
    )


# ---------------------------------------------------------------------------
# Top-level status: plan_not_found / blocked_not_materialized
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_not_found():
    db = AsyncMock()

    async def execute(stmt):
        return _FakeResult(None)

    db.execute = execute
    result = await build_operational_resource_readiness(db, 404404)
    assert result.status == "plan_not_found"
    assert result.tasks == []
    assert result.side_effects == "none"


@pytest.mark.asyncio
async def test_no_planned_tasks_fallback_when_not_materialized(monkeypatch):
    envelope = {
        "planned_tasks": [{"task_key": "only_planned", "source_operation_code": "face_cnc_cut"}],
        "operational_tasks": [],
    }
    db, _ = _plan_db(envelope)
    _patch_registry(monkeypatch, {})
    result = await build_operational_resource_readiness(db, 1)
    assert result.status == "blocked_not_materialized"
    assert result.tasks == []


# ---------------------------------------------------------------------------
# WC_CNC_ROUTING canonical, machine-required, ready path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wc_cnc_routing_resolves_canonically_and_ready_with_warnings(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_cnc",
                "source_operation_code": "face_cnc_cut",
                "workcenter": "WC_CNC_ROUTING",
                "estimated_time_minutes": None,
            }
        ]
    }
    machines = [_machine("MCH-CNC-4020", kind="machine", wc="WC_CNC_ROUTING")]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "face_cnc_cut": {
                "operation_code": "cnc_cutting",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_CNC_ROUTING"],
                "allowed_resource_codes": ["MCH-CNC-4020"],
                "default_resource_code": "MCH-CNC-4020",
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    assert result.status == "ok"
    row = result.tasks[0]
    assert row.workcenter_code == "WC_CNC_ROUTING"
    assert row.workcenter_registry_status == "resolved"
    assert row.resource_requirement_mode == "orr_allowlist"
    assert row.status == "ready_with_warnings"
    assert "PLANNING_MINUTES_SOURCE_MISSING" in row.warnings
    assert [c.resource_code for c in row.compatible_machine_candidates] == ["MCH-CNC-4020"]
    assert row.status not in BLOCKED_STATUSES  # capacity warning != commercial blocker


# ---------------------------------------------------------------------------
# WC_CNC must never silently pass as WC_CNC_ROUTING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wc_cnc_non_canonical_does_not_silently_pass(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_cnc_legacy",
                "source_operation_code": "face_cnc_cut",
                "workcenter": "WC_CNC",
                "estimated_time_minutes": 12.0,
            }
        ]
    }
    machines = [_machine("MCH-CNC-4020", kind="machine", wc="WC_CNC_ROUTING")]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "face_cnc_cut": {
                "operation_code": "cnc_cutting",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_CNC_ROUTING"],
                "allowed_resource_codes": ["MCH-CNC-4020"],
                "default_resource_code": "MCH-CNC-4020",
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    # Frozen WC_CNC is preserved verbatim — never silently rewritten.
    assert row.workcenter_code == "WC_CNC"
    assert row.workcenter_registry_status == "non_canonical"
    assert any(w.startswith("WORKCENTER_NON_CANONICAL:WC_CNC") for w in row.warnings)
    # Must not be silently "ready" — non-canonical is a warning status, not blocked.
    assert row.status == "ready_with_warnings"
    assert row.status != "ready"


# ---------------------------------------------------------------------------
# Unknown workcenter -> warning, never a guessed mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_workcenter_warns_without_guessing(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_unknown_wc",
                "source_operation_code": "face_cnc_cut",
                "workcenter": "WC_TOTALLY_MADE_UP",
                "estimated_time_minutes": 5.0,
            }
        ]
    }
    machines = [_machine("MCH-CNC-4020", kind="machine")]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "face_cnc_cut": {
                "operation_code": "cnc_cutting",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_CNC_ROUTING"],
                "allowed_resource_codes": ["MCH-CNC-4020"],
                "default_resource_code": "MCH-CNC-4020",
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.workcenter_code == "WC_TOTALLY_MADE_UP"
    assert row.workcenter_registry_status == "missing"
    assert any(w.startswith("WORKCENTER_UNKNOWN:") for w in row.warnings)
    assert any(w.startswith("FROZEN_WORKCENTER_NOT_IN_ORR_ALLOWLIST:") for w in row.warnings)
    # Never invented a canonical mapping — resource pool still comes from ORR by op code.
    assert row.resource_requirement_mode == "orr_allowlist"


# ---------------------------------------------------------------------------
# Empty workcenter -> missing_workcenter (blocking-ish, but explicit not guessed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_workcenter_is_missing_workcenter(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_no_wc",
                "source_operation_code": "face_cnc_cut",
                "workcenter": None,
                "estimated_time_minutes": None,
            }
        ]
    }
    db, _ = _plan_db(envelope, machines=[])
    _patch_registry(monkeypatch, {})
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.workcenter_registry_status == "empty"
    assert row.status == "missing_workcenter"
    assert "workcenter_missing" in row.blockers
    assert result.blocked_count == 1


# ---------------------------------------------------------------------------
# Missing ORR mapping -> unknown_resource_policy (never invented)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_orr_mapping_is_unknown_resource_policy(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_no_orr",
                "source_operation_code": "totally_unmapped_operation",
                "workcenter": "WC_ASSEMBLY",
                "estimated_time_minutes": 1.0,
            }
        ]
    }
    db, _ = _plan_db(envelope, machines=[])
    _patch_registry(monkeypatch, {})
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.status == "unknown_resource_policy"
    assert row.resource_requirement_mode == "unknown_resource_policy"
    assert "orr_mapping_missing" in row.blockers


# ---------------------------------------------------------------------------
# Ambiguous workcenter mapping (>1 allowed WC) -> ambiguous_mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ambiguous_workcenter_mapping(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_ambiguous",
                "source_operation_code": "led_install_letters",
                "workcenter": "WC_LED_ASSEMBLY",
                "estimated_time_minutes": 1.0,
            }
        ]
    }
    db, _ = _plan_db(envelope, machines=[])
    _patch_registry(
        monkeypatch,
        {
            "led_install_letters": {
                "operation_code": "montaj_led",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_LED_ASSEMBLY", "WC_ASSEMBLY"],
                "allowed_resource_codes": [],
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.status == "ambiguous_mapping"
    assert "workcenter_mapping_ambiguous" in row.blockers


# ---------------------------------------------------------------------------
# Machine-required but none compatible (registered, all inactive)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_machine_required_but_none_compatible(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_down",
                "source_operation_code": "welding",
                "workcenter": "WC_METAL_FAB",
                "estimated_time_minutes": 1.0,
            }
        ]
    }
    machines = [
        _machine("MCH-WELD-STEEL", kind="tool", active=False, wc="WC_METAL_FAB"),
        _machine("MCH-WELD-ALU", kind="tool", active=False, wc="WC_METAL_FAB"),
    ]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "welding": {
                "operation_code": "welding",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_METAL_FAB"],
                "allowed_resource_codes": ["MCH-WELD-STEEL", "MCH-WELD-ALU"],
                "default_resource_code": None,
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.resource_requirement_mode == "orr_allowlist"
    assert row.status == "machine_required_but_none_compatible"
    assert row.compatible_machine_candidates == []
    assert "no_compatible_machine_registered" in row.blockers
    assert row.status in BLOCKED_STATUSES


# ---------------------------------------------------------------------------
# Machine unavailable — the one known default machine is down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_machine_unavailable_when_default_resource_inactive(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_default_down",
                "source_operation_code": "cant_modelare",
                "workcenter": "WC_LETTER_FORMING",
                "estimated_time_minutes": 1.0,
            }
        ]
    }
    machines = [_machine("MCH-CNC-CANT-LITERE", kind="machine", active=False, wc="WC_LETTER_FORMING")]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "cant_modelare": {
                "operation_code": "cant_modelare",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_LETTER_FORMING"],
                "allowed_resource_codes": ["MCH-CNC-CANT-LITERE"],
                "default_resource_code": "MCH-CNC-CANT-LITERE",
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.status == "machine_unavailable"
    assert "default_resource_inactive" in row.blockers


# ---------------------------------------------------------------------------
# workcenter_only (work_area-only ORR resources) not falsely blocked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workcenter_only_not_falsely_blocked_for_missing_machine(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_paint",
                "source_operation_code": "painting",
                "workcenter": "WC_ASSEMBLY",
                "estimated_time_minutes": None,
            }
        ]
    }
    machines = [
        _machine("WA-ASSEMBLY-01", kind="work_area", wc="WC_ASSEMBLY"),
        _machine("WA-ASSEMBLY-02", kind="work_area", wc="WC_ASSEMBLY"),
    ]
    db, _ = _plan_db(envelope, machines=machines)
    _patch_registry(
        monkeypatch,
        {
            "painting": {
                "operation_code": "assembly",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_ASSEMBLY"],
                "allowed_resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
                "default_resource_code": None,
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.resource_requirement_mode == "workcenter_only"
    assert row.status == "workcenter_only"
    assert row.status not in BLOCKED_STATUSES
    assert row.compatible_machine_candidates == []
    assert [c.resource_code for c in row.work_area_candidates] == [
        "WA-ASSEMBLY-01",
        "WA-ASSEMBLY-02",
    ]


@pytest.mark.asyncio
async def test_no_resource_codes_is_workcenter_only(monkeypatch):
    envelope = {
        "operational_tasks": [
            {
                "task_id": "t_field",
                "source_operation_code": "field_installation",
                "workcenter": "WC_FIELD_INSTALLATION",
                "estimated_time_minutes": None,
            }
        ]
    }
    db, _ = _plan_db(envelope, machines=[])
    _patch_registry(
        monkeypatch,
        {
            "field_installation": {
                "operation_code": "field_installation",
                "authorization_mode": "hybrid",
                "allowed_workcenter_codes": ["WC_FIELD_INSTALLATION"],
                "allowed_resource_codes": [],
                "default_resource_code": None,
            }
        },
    )
    result = await build_operational_resource_readiness(db, 1)
    row = result.tasks[0]
    assert row.resource_requirement_mode == "workcenter_only"
    assert row.status == "workcenter_only"


# ---------------------------------------------------------------------------
# Integration — real F7A-style 5-task fixture, real ORR + machines rows.
# Mirrors Stage A facts (fixture 880811 / plan 22).
# ---------------------------------------------------------------------------


async def _seed_orr_and_machines(db_session) -> None:
    existing = await db_session.execute(
        select(MachineRegistry).where(MachineRegistry.machine_code == "MCH-CNC-4020")
    )
    if existing.scalar_one_or_none() is not None:
        return  # already seeded by an earlier test sharing the session-scoped DB
    orr_rows = [
        OperationResourceRequirement(
            operation_code="cnc_cutting",
            allowed_workcenter_codes=json.dumps(["WC_CNC_ROUTING"]),
            allowed_resource_codes=json.dumps(["MCH-CNC-4020"]),
            authorization_mode="hybrid",
            default_resource_code="MCH-CNC-4020",
            product_system_aliases=json.dumps(["face_cnc_cut"]),
        ),
        OperationResourceRequirement(
            operation_code="cant_modelare",
            allowed_workcenter_codes=json.dumps(["WC_LETTER_FORMING"]),
            allowed_resource_codes=json.dumps(["MCH-CNC-CANT-LITERE"]),
            authorization_mode="hybrid",
            default_resource_code="MCH-CNC-CANT-LITERE",
            product_system_aliases=json.dumps(["side_forming"]),
        ),
        OperationResourceRequirement(
            operation_code="welding",
            allowed_workcenter_codes=json.dumps(["WC_METAL_FAB"]),
            allowed_resource_codes=json.dumps(
                ["MCH-WELD-STEEL", "MCH-WELD-ALU", "WA-WELD-TABLE"]
            ),
            authorization_mode="hybrid",
            default_resource_code=None,
            product_system_aliases=json.dumps(["return_face_bonding"]),
        ),
        OperationResourceRequirement(
            operation_code="assembly",
            allowed_workcenter_codes=json.dumps(["WC_ASSEMBLY"]),
            allowed_resource_codes=json.dumps(["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"]),
            authorization_mode="hybrid",
            default_resource_code=None,
            product_system_aliases=json.dumps(["painting"]),
        ),
        OperationResourceRequirement(
            operation_code="packaging",
            allowed_workcenter_codes=json.dumps(["WC_ASSEMBLY"]),
            allowed_resource_codes=json.dumps(["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"]),
            authorization_mode="hybrid",
            default_resource_code=None,
            product_system_aliases=json.dumps(["packaging_letters"]),
        ),
    ]
    machine_rows = [
        MachineRegistry(
            machine_code="MCH-CNC-4020",
            name="CNC 4020",
            machine_type="cnc_router",
            resource_kind="machine",
            workcenter_code="WC_CNC_ROUTING",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="MCH-CNC-CANT-LITERE",
            name="CNC Cant Litere",
            machine_type="letter_forming",
            resource_kind="machine",
            workcenter_code="WC_LETTER_FORMING",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="MCH-WELD-STEEL",
            name="Aparat sudura otel",
            machine_type="welder_steel",
            resource_kind="tool",
            workcenter_code="WC_METAL_FAB",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="MCH-WELD-ALU",
            name="Aparat sudura aluminiu",
            machine_type="welder_aluminum",
            resource_kind="tool",
            workcenter_code="WC_METAL_FAB",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="WA-WELD-TABLE",
            name="Masa pentru sudura",
            machine_type="work_area",
            resource_kind="work_area",
            workcenter_code="WC_METAL_FAB",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="WA-ASSEMBLY-01",
            name="Masa lucru ansamblare 1",
            machine_type="work_area",
            resource_kind="work_area",
            workcenter_code="WC_ASSEMBLY",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
        MachineRegistry(
            machine_code="WA-ASSEMBLY-02",
            name="Masa lucru ansamblare 2",
            machine_type="work_area",
            resource_kind="work_area",
            workcenter_code="WC_ASSEMBLY",
            operational_status="active",
            is_available=True,
            is_active=True,
        ),
    ]
    db_session.add_all(orr_rows)
    db_session.add_all(machine_rows)
    await db_session.commit()


@pytest.mark.asyncio
async def test_f7c_five_task_fixture_matches_stage_a_readiness_matrix(db_session):
    """Real materialized 5-task envelope (F7A/F7B shape) + real ORR/machines rows."""
    await _seed_orr_and_machines(db_session)

    oid = _f7a_oid()
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=_f7a_snapshot_json(order_id=oid, quote_snapshot_v2_id=oid),
    )
    await create_execution_plan_v2_from_order(db_session, order.id)
    materialize_result = await materialize_execution_plan_v2_operational_tasks(
        db_session, order.id
    )
    assert materialize_result.operational_tasks_count == 5

    reality_before = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    gate_before = evaluate_materialize_authorization(
        order_id=order.id, plan_id=materialize_result.execution_plan_id
    )

    result = await build_operational_resource_readiness(db_session, order.id)
    assert result.status == "ok"
    assert result.operational_task_count == 5
    assert result.side_effects == "none"

    by_op = {t.source_operation_code: t for t in result.tasks}

    face = by_op["face_cnc_cut"]
    assert face.workcenter_code == "WC_CNC_ROUTING"
    assert face.workcenter_registry_status == "resolved"
    assert face.resource_requirement_mode == "orr_allowlist"
    assert face.status == "ready_with_warnings"
    assert [c.resource_code for c in face.compatible_machine_candidates] == ["MCH-CNC-4020"]

    side = by_op["side_forming"]
    assert side.workcenter_code == "WC_LETTER_FORMING"
    assert side.status == "ready_with_warnings"
    assert [c.resource_code for c in side.compatible_machine_candidates] == [
        "MCH-CNC-CANT-LITERE"
    ]

    bond = by_op["return_face_bonding"]
    assert bond.workcenter_code == "WC_METAL_FAB"
    assert bond.resource_requirement_mode == "orr_allowlist"
    assert bond.status == "ready_with_warnings"
    assert {c.resource_code for c in bond.compatible_machine_candidates} == {
        "MCH-WELD-STEEL",
        "MCH-WELD-ALU",
    }
    assert [c.resource_code for c in bond.work_area_candidates] == ["WA-WELD-TABLE"]
    assert bond.default_resource_code is None

    paint = by_op["painting"]
    assert paint.resource_requirement_mode == "workcenter_only"
    assert paint.status == "workcenter_only"
    assert paint.compatible_machine_candidates == []

    pack = by_op["packaging_letters"]
    assert pack.resource_requirement_mode == "workcenter_only"
    assert pack.status == "workcenter_only"

    # Zero side effects — no assignments/sessions, no plan mutation, gate stays closed.
    reality_after = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert reality_after == reality_before
    assert plans_after == plans_before

    await db_session.refresh(order)
    assert json.loads(order.snapshot_v2_json)["accepted_commercial_total"] == COMMERCIAL_TOTAL

    assert LIVE_DEC009_STATUS == "A"
    gate_after = evaluate_materialize_authorization(
        order_id=order.id, plan_id=materialize_result.execution_plan_id
    )
    # The read-only GET must never change gate state either way.
    assert gate_after == gate_before

    # Idempotent — calling again produces the identical matrix, zero new writes.
    result_again = await build_operational_resource_readiness(db_session, order.id)
    assert result_again.model_dump() == result.model_dump()
    reality_final = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    assert reality_final == reality_before


def test_endpoint_resource_readiness_returns_ok(db_fixture, db_session, auth_client):
    """HTTP-level GET proof — read-only, no assignments/sessions created."""
    oid = _f7a_oid()

    async def _setup():
        await _seed_orr_and_machines(db_session)
        order = await _seed_v2_order_with_snapshot(
            db_session,
            order_id=oid,
            snapshot_v2_json=_f7a_snapshot_json(order_id=oid, quote_snapshot_v2_id=oid),
        )
        await create_execution_plan_v2_from_order(db_session, order.id)
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    db_fixture.run(_setup())

    resp = auth_client.get(f"/api/v1/execution/plan-v2/from-order/{oid}/resource-readiness")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "operational_resource_readiness"
    assert body["status"] == "ok"
    assert body["operational_task_count"] == 5
    assert body["side_effects"] == "none"

    async def _count_reality():
        return int(
            (await db_session.scalar(select(func.count()).select_from(ExecutionReality))) or 0
        )

    assert db_fixture.run(_count_reality()) == 0
