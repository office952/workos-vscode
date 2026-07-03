"""Tests for read-only Intake V6 modular form contract (Step 5)."""

from __future__ import annotations

import pytest

from services.intake_v6_modular_form_contract_service import (
    IntakeV6ModularFormContractService,
    VOLUMETRIC_FIELD_BINDINGS,
)

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest.fixture
def form_service() -> IntakeV6ModularFormContractService:
    return IntakeV6ModularFormContractService()


def test_form_contract_exists_for_volumetric_v2(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE)
    assert contract is not None
    assert contract.summary.template_code == TEMPLATE
    assert contract.summary.active_module_count == 7


def test_all_active_modules_have_form_sections(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE)
    assert contract is not None
    codes = {m.module_code for m in contract.modules}
    for expected in (
        "geometry_svg",
        "modelare_cant",
        "structura_suport",
        "debitare_fata",
        "debitare_spate",
        "sistem_led",
        "finisaje",
    ):
        assert expected in codes


def test_mounting_system_canonical_trigger_for_structura_suport(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE)
    assert contract is not None
    structura = next(m for m in contract.modules if m.module_code == "structura_suport")
    assert "mounting_system" in structura.intake_trigger_fields
    alignment = contract.trigger_alignments[0]
    assert alignment.canonical_intake_field == "finish_setup.mounting_system"
    assert alignment.module_link_trigger_field == "metal_support_required"
    assert alignment.derived_quote_input_key == "metal_support_required"
    assert alignment.warning_code == "TRIGGER_FIELD_MISMATCH"


def test_metal_support_required_is_derived_not_form_field(form_service: IntakeV6ModularFormContractService):
    derived = next(f for f in VOLUMETRIC_FIELD_BINDINGS if f.canonical_key == "metal_support_required")
    assert derived.field_role == "derived_quote_input"
    assert derived.derived_from == "finish_setup.mounting_system"
    assert "structura_suport" in derived.module_codes


def test_geometry_svg_has_no_direct_task_fields(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE)
    assert contract is not None
    geom = next(m for m in contract.modules if m.module_code == "geometry_svg")
    assert geom.activation_kind == "always_on"
    assert any("non-priced" in w.lower() or "task" in w.lower() for w in geom.warnings)


def test_no_orphan_active_field_bindings_without_module(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE)
    assert contract is not None
    for binding in contract.field_bindings:
        if binding.field_role == "derived_quote_input":
            continue
        if binding.operational_status.startswith("FUTURE"):
            continue
        assert binding.module_codes, f"{binding.canonical_key} missing module_codes"


def test_unknown_template_returns_none(form_service: IntakeV6ModularFormContractService):
    assert form_service.get_for_template("TPL-UNKNOWN") is None


@pytest.fixture
def form_auth_client(db_fixture):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


def test_form_contract_endpoint_200(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{TEMPLATE}")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["active_module_count"] == 7
    assert len(body["field_bindings"]) >= 20


def test_form_contract_endpoint_404(form_auth_client):
    response = form_auth_client.get("/api/v1/intake-v6/form-contract/TPL-NO-CONTRACT")
    assert response.status_code == 404
