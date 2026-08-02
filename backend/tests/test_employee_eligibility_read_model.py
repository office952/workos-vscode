"""DEC-014/015 — ORR LED singleton + employee eligibility read model."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.operation_workcenter_resolution_service import (
    resolve_workcenter_for_operation,
)

LED_MAPPINGS_BEFORE = [
    {
        "operation_code": "montaj_led",
        "allowed_workcenter_codes": ["WC_LED_ASSEMBLY", "WC_ASSEMBLY"],
        "product_system_aliases": ["led_install_letters", "electrical_letters"],
    }
]

LED_MAPPINGS_AFTER = [
    {
        "operation_code": "montaj_led",
        "allowed_workcenter_codes": ["WC_LED_ASSEMBLY"],
        "product_system_aliases": ["led_install_letters", "electrical_letters"],
        "required_skill_codes": ["SK_ELECTRICIAN"],
        "authorization_mode": "hybrid",
    },
    {
        "operation_code": "assembly",
        "allowed_workcenter_codes": ["WC_ASSEMBLY"],
        "product_system_aliases": ["assembly_letters"],
        "required_skill_codes": ["SK_ASSEMBLY"],
        "authorization_mode": "hybrid",
    },
]


def test_led_ambiguous_before_disambiguation():
    r = resolve_workcenter_for_operation("led_install_letters", LED_MAPPINGS_BEFORE)
    assert r.status == "ambiguous"
    assert r.workcenter_code is None


def test_led_canonical_after_disambiguation():
    r = resolve_workcenter_for_operation("led_install_letters", LED_MAPPINGS_AFTER)
    assert r.status == "resolved"
    assert r.workcenter_code == "WC_LED_ASSEMBLY"
    r2 = resolve_workcenter_for_operation("electrical_letters", LED_MAPPINGS_AFTER)
    assert r2.workcenter_code == "WC_LED_ASSEMBLY"
    a = resolve_workcenter_for_operation("assembly_letters", LED_MAPPINGS_AFTER)
    assert a.workcenter_code == "WC_ASSEMBLY"


def test_no_label_substring_fallback_for_led():
    r = resolve_workcenter_for_operation("LED Electric Station", LED_MAPPINGS_AFTER)
    assert r.status == "source_missing"
    assert r.workcenter_code is None


def test_zero_one_multiple_wc_semantics():
    empty = resolve_workcenter_for_operation(
        "op",
        [{"operation_code": "op", "allowed_workcenter_codes": [], "product_system_aliases": []}],
    )
    assert empty.status == "not_required"
    one = resolve_workcenter_for_operation(
        "op",
        [{"operation_code": "op", "allowed_workcenter_codes": ["WC_A"], "product_system_aliases": []}],
    )
    assert one.status == "resolved"
    multi = resolve_workcenter_for_operation(
        "op",
        [
            {
                "operation_code": "op",
                "allowed_workcenter_codes": ["WC_A", "WC_B"],
                "product_system_aliases": [],
            }
        ],
    )
    assert multi.status == "ambiguous"


@pytest.mark.asyncio
async def test_eligibility_blocks_ambiguous_and_matches_explicit(monkeypatch):
    envelope = {
        "execution_tasks_created": True,
        "operational_tasks": [
            {
                "task_id": "t_led",
                "process_id": "led_install_letters",
                "source_operation_code": "led_install_letters",
                "process_type": "led_assembly",
                "workcenter": None,
                "warnings": ["WORKCENTER_MAPPING_AMBIGUOUS"],
                "estimated_time_minutes": None,
            },
            {
                "task_id": "t_ok",
                "process_id": "assembly_letters",
                "source_operation_code": "assembly_letters",
                "process_type": "assembly",
                "workcenter": "WC_ASSEMBLY",
                "machine_requirement": {
                    "workcenter": "WC_ASSEMBLY",
                    "resolution_status": "resolved",
                },
                "warnings": ["PLANNING_MINUTES_SOURCE_MISSING"],
                "estimated_time_minutes": None,
            },
        ],
        "planned_tasks": [{"task_key": "should_be_ignored"}],
    }
    plan = SimpleNamespace(id=99, tasks_json=json.dumps(envelope))

    emp_ok = SimpleNamespace(id=7, name="Andrei", status="active")
    emp_inactive = SimpleNamespace(id=99, name="Gone", status="inactive")

    class FakeResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

        def scalars(self):
            return SimpleNamespace(all=lambda: self._value)

    db = AsyncMock()

    async def execute(stmt):
        sql = str(stmt)
        if "execution_plan" in sql.lower() or "ExecutionPlan" in sql:
            return FakeResult(plan)
        # employees active query
        return FakeResult([emp_ok])

    db.execute = execute

    class FakeRegistry:
        async def get_employee_authorizations(self, employee_id: int):
            if employee_id == 7:
                return {
                    "skill_codes": ["SK_ASSEMBLY", "SK_ELECTRICIAN"],
                    "workcenter_codes": ["WC_ASSEMBLY", "WC_LED_ASSEMBLY"],
                    "resource_codes": ["WA-ASSEMBLY-01"],
                }
            return {"skill_codes": [], "workcenter_codes": [], "resource_codes": []}

        async def resolve_operation_mapping(self, operation_code: str):
            code = (operation_code or "").lower()
            if code in {"led_install_letters", "montaj_led"}:
                return {
                    "operation_code": "montaj_led",
                    "authorization_mode": "hybrid",
                    "required_skill_codes": ["SK_ELECTRICIAN"],
                    "allowed_workcenter_codes": ["WC_LED_ASSEMBLY"],
                    "allowed_resource_codes": [],
                    "resolution": "alias",
                }
            if code in {"assembly_letters", "assembly"}:
                return {
                    "operation_code": "assembly",
                    "authorization_mode": "hybrid",
                    "required_skill_codes": ["SK_ASSEMBLY"],
                    "allowed_workcenter_codes": ["WC_ASSEMBLY"],
                    "allowed_resource_codes": [],
                    "resolution": "alias",
                }
            return None

        async def get_operation_employee_ids(self, operation_code: str):
            return []

        def _employee_matches_mapping_rules(self, auth, mapping, machine_type=None):
            from services.operational_registry_service import OperationalRegistryService

            return OperationalRegistryService._employee_matches_mapping_rules(
                self, auth, mapping, machine_type=machine_type
            )

    monkeypatch.setattr(
        "services.employee_eligibility_read_model_service.OperationalRegistryService",
        lambda db: FakeRegistry(),
    )

    result = await build_employee_eligibility_read_model(db, 12345)
    assert result["side_effects"] == "none"
    assert result["operational_task_count"] == 2
    by = {t["task_key"]: t for t in result["tasks"]}
    assert by["t_led"]["eligibility_status"] == "blocked_ambiguous_workcenter"
    assert by["t_led"]["eligible_employee_count"] == 0
    assert by["t_ok"]["eligibility_status"] == "ready_with_warnings"
    assert by["t_ok"]["eligible_employee_count"] == 1
    assert by["t_ok"]["eligible_employees"][0]["employee_id"] == 7
    assert "planning_minutes_source_missing" in by["t_ok"]["warnings"]
    # Prove planned_tasks were not used as fallback for empty ops path separately
    assert emp_inactive.id not in {
        e["employee_id"] for e in by["t_ok"]["eligible_employees"]
    }


@pytest.mark.asyncio
async def test_eligibility_no_planned_tasks_fallback(monkeypatch):
    envelope = {
        "planned_tasks": [{"task_key": "only_planned", "source_operation_code": "assembly_letters"}],
        "operational_tasks": [],
    }
    plan = SimpleNamespace(id=1, tasks_json=json.dumps(envelope))

    class FakeResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

        def scalars(self):
            return SimpleNamespace(all=lambda: self._value)

    db = AsyncMock()

    async def execute(stmt):
        return FakeResult(plan)

    db.execute = execute
    monkeypatch.setattr(
        "services.employee_eligibility_read_model_service.OperationalRegistryService",
        lambda db: MagicMock(),
    )
    result = await build_employee_eligibility_read_model(db, 1)
    assert result["status"] == "blocked_not_materialized"
    assert result["tasks"] == []
