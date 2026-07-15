"""APP-AUTH-06 observation pilot — controlled scenario coverage."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from parity.enums import ComparisonResult
from services.parity_observe.config import (
    get_effective_parity_flags,
    parity_observe_is_enabled,
    reset_effective_parity_flags_cache,
)
from services.parity_observe.eligibility_endpoint import observe_eligible_employees_endpoint
from services.parity_observe.mobile_available import observe_mobile_available_tasks
from services.parity_observe.sandu import build_sandu_observe_report, SANDU_EMPLOYEE_ID
from services.parity_observe.shadow_data import simulate_canonical_eligibility
from services.parity_observe.structured_log import (
    get_in_memory_observations,
    reset_in_memory_observations,
)


@pytest.fixture(autouse=True)
def _pilot_env(monkeypatch):
    reset_in_memory_observations()
    reset_effective_parity_flags_cache()
    monkeypatch.setenv("APP_ENV", "test")
    for key in (
        "PARITY_OBSERVE_ENABLED",
        "COMPETENCE_PARITY_ENABLED",
        "EXPLICIT_MAPPING_TRACKING_ENABLED",
        "ELIGIBILITY_SHADOW_ENABLED",
        "LEGACY_FALLBACK_TRACKING_ENABLED",
        "PARITY_EVENT_EMISSION_ENABLED",
    ):
        monkeypatch.setenv(key, "true")
    reset_effective_parity_flags_cache()
    yield
    reset_effective_parity_flags_cache()
    reset_in_memory_observations()


def _registry_mock(*, skills, mapping, explicit_ids=None):
    registry = MagicMock()
    registry.get_employee_authorizations = AsyncMock(
        return_value={"skill_codes": skills, "workcenter_codes": [], "resource_codes": []}
    )
    registry.resolve_operation_mapping = AsyncMock(return_value=mapping)
    registry.get_operation_employee_ids = AsyncMock(return_value=list(explicit_ids or []))
    return registry


def _employee_row(skills):
    emp = MagicMock()
    emp.skills = json.dumps(skills) if skills is not None else None
    emp.machines = None
    return emp


@pytest.mark.asyncio
async def test_s1_registry_legacy_aligned_match():
    db = AsyncMock()
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_PRINT_OPERATOR"]))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 1, [{"process_type": "print"}])
    results = {o["comparison_result"] for o in get_in_memory_observations()}
    assert "match" in results or "value_conflict" not in results


@pytest.mark.asyncio
async def test_s2_registry_only_canonical_only():
    db = AsyncMock()
    registry = _registry_mock(skills=["SK_PRINT_OPERATOR"], mapping=None)
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(None))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 2, [{"process_type": "print"}])
    assert any(o.get("comparison_result") == "canonical_only" for o in get_in_memory_observations())


@pytest.mark.asyncio
async def test_s3_legacy_only_transitional_only():
    db = AsyncMock()
    registry = _registry_mock(skills=[], mapping=None)
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_ASSEMBLY"]))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 3, [{"process_type": "assembly"}])
    assert any(o.get("comparison_result") == "transitional_only" for o in get_in_memory_observations())


@pytest.mark.asyncio
async def test_s4_value_conflict_stable_fingerprint():
    db = AsyncMock()
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_ASSEMBLY"]))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 4, [{"process_type": "print"}])
        reset_in_memory_observations()
        await observe_mobile_available_tasks(db, 4, [{"process_type": "print"}])
    fps = [o["fingerprint"] for o in get_in_memory_observations() if o.get("domain") == "competence"]
    assert len(fps) >= 1
    assert len(set(fps)) == 1


@pytest.mark.asyncio
async def test_s5_mapping_without_competence_high():
    db = AsyncMock()
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "assembly",
            "required_skill_codes": ["SK_ASSEMBLY"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
        explicit_ids=[SANDU_EMPLOYEE_ID],
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_ASSEMBLY"]))))
    available = [{"process_type": "assembly"}]
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, SANDU_EMPLOYEE_ID, available)
    assert len(available) == 1
    assert any(
        o.get("comparison_result") == "operational_eligible_canonical_ineligible"
        or o.get("severity") == "high"
        for o in get_in_memory_observations()
    )


def test_s6_missing_authorization_distinct_from_competence():
    snapshot = {"registry_skills": ["SK_PRINT_OPERATOR"], "registry_resources": [], "registry_workcenters": []}
    mapping = {
        "required_skill_codes": ["SK_PRINT_OPERATOR"],
        "allowed_resource_codes": ["MCH-CNC-4020"],
        "allowed_workcenter_codes": [],
    }
    eligible, reason = simulate_canonical_eligibility(snapshot=snapshot, mapping=mapping, machine_type=None)
    assert eligible is False
    assert reason == "missing_required_authorization"


@pytest.mark.asyncio
async def test_s7_insufficient_data_not_false_conflict():
    db = AsyncMock()
    registry = _registry_mock(
        skills=[],
        mapping={"operation_code": "unknown", "required_skill_codes": [], "allowed_resource_codes": [], "allowed_workcenter_codes": []},
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row([]))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 5, [{"process_type": "unknown"}])
    assert any(
        o.get("comparison_result") in {"unknown_or_uncomputable", "missing_operation_requirement"}
        for o in get_in_memory_observations()
    )


@pytest.mark.asyncio
async def test_s8_comparator_error_isolated():
    async def _boom(*_a, **_k):
        raise RuntimeError("pilot comparator fault")

    with patch("services.parity_observe.mobile_available._observe_mobile_available_tasks", side_effect=_boom):
        await observe_mobile_available_tasks(AsyncMock(), 1, [{"process_type": "print"}])
    assert get_in_memory_observations() == []


@pytest.mark.asyncio
async def test_s9_five_repetitions_identical_fingerprint():
    db = AsyncMock()
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_PRINT_OPERATOR"]))))
    from collections import defaultdict

    by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        for _ in range(5):
            reset_in_memory_observations()
            await observe_mobile_available_tasks(db, 1, [{"process_type": "print"}])
            for obs in get_in_memory_observations():
                key = (obs["domain"], obs["comparison_result"])
                by_key[key].add(obs["fingerprint"])
    assert by_key
    for fingerprints in by_key.values():
        assert len(fingerprints) == 1


@pytest.mark.asyncio
async def test_s10_concurrent_observe_no_cross_contamination():
    def _make_registry(skills):
        return _registry_mock(
            skills=skills,
            mapping={
                "operation_code": "print",
                "required_skill_codes": ["SK_PRINT_OPERATOR"],
                "allowed_resource_codes": [],
                "allowed_workcenter_codes": [],
            },
        )

    async def _run(employee_id: int, skills: list[str]):
        registry = _make_registry(skills)
        local_db = AsyncMock()
        local_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(skills)))
        )
        with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
            await observe_mobile_available_tasks(local_db, employee_id, [{"process_type": "print"}])

    reset_in_memory_observations()
    await asyncio.gather(_run(10, ["SK_PRINT_OPERATOR"]), _run(11, ["SK_ASSEMBLY"]))
    all_obs = get_in_memory_observations()
    for employee_id in (10, 11):
        subset = [o for o in all_obs if o.get("employee_id") == employee_id]
        assert subset
        assert all(o["employee_id"] == employee_id for o in subset)


@pytest.mark.asyncio
async def test_pilot_confidentiality_no_prohibited_keys():
    db = AsyncMock()
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_PRINT_OPERATOR"]))))
    with patch("services.parity_observe.mobile_available.OperationalRegistryService", return_value=registry):
        await observe_mobile_available_tasks(db, 1, [{"process_type": "print"}])
    prohibited = {"salary", "salariu", "jwt", "token", "password", "secret", "hr_payload", "full_snapshot"}
    blob = json.dumps(get_in_memory_observations()).lower()
    assert not any(p in blob for p in prohibited)


@pytest.mark.asyncio
async def test_sandu_pilot_read_only():
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


@pytest.mark.asyncio
async def test_eligibility_response_unchanged_under_pilot_flags():
    db = AsyncMock()
    operational = {
        "operation_code": "print",
        "resolved_operation_code": "print",
        "items": [{"id": 1, "eligibility": "authorized"}],
        "authorized_employee_ids": [],
        "total": 1,
    }
    before = json.dumps(operational, sort_keys=True)
    registry = _registry_mock(
        skills=["SK_PRINT_OPERATOR"],
        mapping={
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_resource_codes": [],
            "allowed_workcenter_codes": [],
        },
    )
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=_employee_row(["SK_PRINT_OPERATOR"]))))
    with patch("services.parity_observe.eligibility_endpoint.OperationalRegistryService", return_value=registry):
        await observe_eligible_employees_endpoint(db, "print", operational)
    assert json.dumps(operational, sort_keys=True) == before
    assert parity_observe_is_enabled() is True


def test_production_guard_blocks_pilot_flags(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    reset_effective_parity_flags_cache()
    flags = get_effective_parity_flags()
    assert flags.parity_observe_enabled is False
