"""APP-AUTH-05 observe-only integration tests."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from parity.enums import ComparisonResult, DiscrepancyStatus
from services.parity_observe.config import (
    get_effective_parity_flags,
    parity_observe_is_enabled,
    reset_effective_parity_flags_cache,
)
from services.parity_observe.mobile_available import observe_mobile_available_tasks
from services.parity_observe.eligibility_endpoint import observe_eligible_employees_endpoint
from services.parity_observe.sandu import build_sandu_observe_report, SANDU_EMPLOYEE_ID
from services.parity_observe.shadow_data import simulate_canonical_eligibility
from services.parity_observe.structured_log import (
    get_in_memory_observations,
    reset_in_memory_observations,
)


@pytest.fixture(autouse=True)
def _reset_parity_state(monkeypatch):
    reset_in_memory_observations()
    reset_effective_parity_flags_cache()
    monkeypatch.delenv("PARITY_OBSERVE_ENABLED", raising=False)
    monkeypatch.delenv("COMPETENCE_PARITY_ENABLED", raising=False)
    monkeypatch.delenv("ELIGIBILITY_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("EXPLICIT_MAPPING_TRACKING_ENABLED", raising=False)
    monkeypatch.delenv("PARITY_EVENT_EMISSION_ENABLED", raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    yield
    reset_effective_parity_flags_cache()
    reset_in_memory_observations()


def _enable_subset_flags(monkeypatch):
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    monkeypatch.setenv("COMPETENCE_PARITY_ENABLED", "true")
    monkeypatch.setenv("EXPLICIT_MAPPING_TRACKING_ENABLED", "true")
    monkeypatch.setenv("ELIGIBILITY_SHADOW_ENABLED", "true")
    monkeypatch.setenv("LEGACY_FALLBACK_TRACKING_ENABLED", "true")
    monkeypatch.setenv("PARITY_EVENT_EMISSION_ENABLED", "true")
    reset_effective_parity_flags_cache()


@pytest.mark.asyncio
async def test_flags_false_no_observations(monkeypatch):
    db = AsyncMock()
    rows = [{"process_type": "print", "task_id": "T1"}]
    await observe_mobile_available_tasks(db, 1, rows)
    assert get_in_memory_observations() == []
    assert parity_observe_is_enabled() is False


@pytest.mark.asyncio
async def test_registry_legacy_match_emits_match_or_no_high(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()

    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(
        return_value={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        }
    )
    registry.get_operation_employee_ids = AsyncMock(return_value=[])

    emp = MagicMock()
    emp.skills = json.dumps(["SK_PRINT_OPERATOR"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        available = [{"process_type": "print", "machine_type": ""}]
        await observe_mobile_available_tasks(db, 1, available)

    observations = get_in_memory_observations()
    assert len(observations) >= 1
    assert available[0]["process_type"] == "print"


@pytest.mark.asyncio
async def test_registry_only_observed_operational_unchanged(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(return_value=None)
    registry.get_operation_employee_ids = AsyncMock(return_value=[])

    emp = MagicMock()
    emp.skills = None
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        available = [{"process_type": "print"}]
        await observe_mobile_available_tasks(db, 2, available)

    comp_events = [o for o in get_in_memory_observations() if o["comparison_result"] == "canonical_only"]
    assert comp_events or get_in_memory_observations()


@pytest.mark.asyncio
async def test_legacy_only_transitional_only(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": [], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(return_value=None)
    registry.get_operation_employee_ids = AsyncMock(return_value=[])

    emp = MagicMock()
    emp.skills = json.dumps(["SK_ASSEMBLY"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 4, [{"process_type": "assembly"}])

    assert any(o.get("comparison_result") == "transitional_only" for o in get_in_memory_observations())


@pytest.mark.asyncio
async def test_mapping_without_competence_high_but_list_unchanged(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(
        return_value={
            "operation_code": "assembly",
            "required_skill_codes": ["SK_ASSEMBLY"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        }
    )
    registry.get_operation_employee_ids = AsyncMock(return_value=[4])

    emp = MagicMock()
    emp.skills = json.dumps(["SK_ASSEMBLY"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    available = [{"process_type": "assembly", "machine_type": ""}]
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 4, available)

    assert len(available) == 1
    high = [o for o in get_in_memory_observations() if o.get("severity") == "high"]
    assert high or any(
        o.get("comparison_result") == "operational_eligible_canonical_ineligible"
        for o in get_in_memory_observations()
    )


@pytest.mark.asyncio
async def test_eligibility_endpoint_operational_result_unchanged(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    operational = {
        "operation_code": "print",
        "resolved_operation_code": "print",
        "items": [{"id": 1, "eligibility": "authorized", "skill_match": True}],
        "authorized_employee_ids": [],
        "total": 1,
    }
    before = json.dumps(operational, sort_keys=True)

    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(
        return_value={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        }
    )

    emp = MagicMock()
    emp.skills = json.dumps(["SK_PRINT_OPERATOR"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    with patch("services.parity_observe.eligibility_endpoint.OperationalRegistryService", return_value=registry):
        await observe_eligible_employees_endpoint(db, "print", operational)

    assert json.dumps(operational, sort_keys=True) == before


def test_production_guard_forces_flags_false(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    monkeypatch.setenv("COMPETENCE_PARITY_ENABLED", "true")
    reset_effective_parity_flags_cache()
    flags = get_effective_parity_flags()
    assert flags.parity_observe_enabled is False
    assert flags.competence_parity_enabled is False


def test_master_flag_without_subflag_inactive(monkeypatch):
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    reset_effective_parity_flags_cache()
    flags = get_effective_parity_flags()
    assert flags.parity_observe_enabled is True
    assert flags.is_active() is False


def test_simulate_canonical_missing_authorization():
    snapshot = {
        "registry_skills": ["SK_PRINT_OPERATOR"],
        "registry_resources": [],
        "registry_workcenters": [],
    }
    mapping = {
        "required_skill_codes": ["SK_PRINT_OPERATOR"],
        "allowed_resource_codes": ["MCH-CNC-4020"],
        "allowed_workcenter_codes": [],
    }
    eligible, reason = simulate_canonical_eligibility(
        snapshot=snapshot,
        mapping=mapping,
        machine_type=None,
    )
    assert eligible is False
    assert reason == "missing_required_authorization"


@pytest.mark.asyncio
async def test_adapter_error_isolation(monkeypatch):
    _enable_subset_flags(monkeypatch)

    async def _boom(*_a, **_k):
        raise RuntimeError("parity internal")

    with patch(
        "services.parity_observe.mobile_available._observe_mobile_available_tasks",
        side_effect=_boom,
    ):
        await observe_mobile_available_tasks(AsyncMock(), 1, [{"process_type": "print"}])
    assert get_in_memory_observations() == []


@pytest.mark.asyncio
async def test_mobile_available_query_budget_no_per_operation_n_plus_one(monkeypatch):
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(
        return_value={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        }
    )
    registry.get_operation_employee_ids = AsyncMock(return_value=[])

    emp = MagicMock()
    emp.skills = json.dumps(["SK_PRINT_OPERATOR"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    available = [
        {"process_type": "print", "machine_type": ""},
        {"process_type": "print", "machine_type": ""},
        {"process_type": "assembly", "machine_type": ""},
    ]
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 1, available)

    assert registry.resolve_operation_mapping.await_count == 2
    assert registry.get_operation_employee_ids.await_count == 2
    _enable_subset_flags(monkeypatch)
    db = AsyncMock()
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": ["SK_PRINT_OPERATOR"], "workcenter_codes": [], "resource_codes": []}
    )
    registry.list_operation_mappings = AsyncMock(return_value=[{"operation_code": "assembly"}])
    registry.get_operation_employee_ids = AsyncMock(return_value=[SANDU_EMPLOYEE_ID])

    emp = MagicMock()
    emp.name = "Putaru Sandu"
    emp.skills = json.dumps(["SK_ASSEMBLY"])
    emp.machines = None
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=emp)))

    with patch("services.parity_observe.sandu.OperationalRegistryService", return_value=registry):
        report = await build_sandu_observe_report(db)

    assert report is not None
    assert report["mutations_performed"] is False
    assert report["sheet"]["reconciliation_status"] == DiscrepancyStatus.CONFIRMATION_REQUIRED.value
